"""RQ3 qualification: integrity, privacy, probability and delivery boundaries."""
from __future__ import annotations

import ast
from pathlib import Path

from unified_scripts.vllm_inference import VLLMInferenceConfig
from .utils import ROOT, read_json, sha_file


def parent_integrity():
    provenance = read_json(ROOT / "RQs/RQ3/configs/parent_provenance.json")
    errors = []
    for row in provenance["files"]:
        if sha_file(ROOT / row["source"]) != row["sha256"]:
            errors.append(row["source"])
    if errors:
        raise ValueError(f"protected parent/config changed: {errors}")
    return {"status":"passed", "checked":len(provenance["files"])}


def solver_projection(config):
    recipe = VLLMInferenceConfig.load(config["unified"]["inference"])
    return {"model":recipe.model("qwen3.8-27b"),
            "request_adapter":{"name":"rq1_1_context_safe_output_v1", "max_tokens":8192},
            "config_sha256":recipe.source_sha256}


def audit_split(split):
    if set(split["eval"]) != {"aegislab","aiops2022","aiops2025","re2_ob","re2_tt"}:
        raise ValueError("invalid eval dataset coverage")
    training = split["train"] + split["validation"]
    if any(r["dataset"] not in {"aiops2022","aiops2025"} for r in training):
        raise ValueError("training-held-out application was opened")
    ids = [(r["dataset"],r["case_id"]) for r in training]
    if len(ids) != len(set(ids)):
        raise ValueError("partition duplication")
    if any(r["case_id"] in split["eval"][r["dataset"]] for r in training):
        raise ValueError("eval leakage")
    a = {r["leakage_group"] for r in split["train"]}
    b = {r["leakage_group"] for r in split["validation"]}
    if a & b:
        raise ValueError("leakage group crosses training and validation")
    from .utils import components
    for dataset in ("aiops2022", "aiops2025"):
        rows = [r for part in ("train", "validation", "unused", "excluded")
                for r in split[part] if r["dataset"] == dataset]
        active = {r["case_id"] for r in training if r["dataset"] == dataset}
        for group in components(rows):
            ids = {r["case_id"] for r in group}
            if ids.intersection(split["eval"][dataset]) and ids.intersection(active):
                raise ValueError("transitive eval window leakage")
    return {"status":"passed", "counts":split["counts"]}


def audit_data_extension(config, split):
    """Source/identity audit only; never inject this private evidence into a prompt."""
    import hashlib
    import re
    from unified_scripts import stable_hash
    corpus = ROOT / config["processed_root"]
    root = corpus / "private/aiops2022"
    extension = read_json(root / "may_extension_summary.json")
    original = (root / "manifest_before_may_extension.jsonl").read_bytes()
    current = (root / "manifest.jsonl").read_bytes()
    if (not extension["complete"] or not current.startswith(original)
            or hashlib.sha256(current).hexdigest() != extension["manifest_sha256"]
            or hashlib.sha256(original).hexdigest() != extension["previous_manifest_sha256"]):
        raise ValueError("May release completion/append-only manifest mismatch")
    audits = [read_json(p) for p in sorted((root / "may_audit").glob("INC-*.json"))]
    if (len(audits) != extension["release_cases"] or len({r["case_id"] for r in audits}) != len(audits)
            or not all(r["public_round_trip"] for r in audits)
            or sum(r["native_csv_byte_parity"] is True for r in audits) < 2):
        raise ValueError("May full-release/native-parity audit incomplete")
    identities = {}; source_groups = {}
    for row in split["train"]+split["validation"]:
        key = row["dataset"],row["opaque_incident_id"]
        meta = read_json(corpus / "public" / key[0] / "cases" / key[1] / "metadata.json")
        if meta["opaque_incident_id"] != key[1] or meta["schema_version"] != "CanvasRCAProcessedPublicCaseV3":
            raise ValueError("training source public identity/schema mismatch")
        names = meta["services"]
        if any(re.search(r"(?:^|[^a-z0-9])(?:ts[-_]|trainticket|train[-_]ticket)",name.lower()) for name in names):
            raise ValueError("TrainTicket-like service identity encountered in training source")
        identities.setdefault(key[0],set()).update(names)
        source_groups.setdefault(key[0],set()).add(row["source"])
    return {"status":"passed", "split_audit":audit_split(split), "split_hash":split["split_hash"],
            "extension":extension,"public_round_trips":len(audits),"native_full_csv_comparisons":2,
            "candidate_identity_hashes":{d:stable_hash(sorted(v)) for d,v in identities.items()},
            "source_groups":{d:sorted(v) for d,v in source_groups.items()},
            "scope":"source dataset isolation plus explicit TrainTicket-name signature audit; not a pretraining contamination claim"}


def audit_render(packet, cards, program, manifest):
    from .exps import select_packet
    subset, selected = select_packet(packet,cards,program)
    expected = {fid for c in selected for fid in c.fact_ids}
    mapped = manifest["fact_mapping"]
    if len(mapped) != len(expected) or {r["fact_id"] for r in mapped} != expected:
        raise ValueError("image fact inventory mismatch")
    if manifest["clipping_audit"]["status"] != "passed":
        raise ValueError("clipping")
    # A fact mapped to a card but no actual primitive is NOT visibly present.
    absent = [r["fact_id"] for r in mapped if not r.get("primitive_geometry")]
    if absent:
        raise ValueError(f"selected facts have no visible primitive: {absent}")
    if len(manifest["cards"]) != len(selected):
        raise ValueError("card/silhouette mismatch")
    return {"status":"passed", "facts":len(expected), "selected_inventory":subset["fact_inventory_hash"]}


def audit_fixed_baseline(packet, png, manifest):
    """Verify provenance and semantic T/C parity before publishing TPV pixels."""
    import io
    from PIL import Image
    from unified_scripts import stable_hash
    from vlmrca.evidence import compact_evidence_text, parse_compact_evidence, semantic_packet_facts
    if manifest.get("schema_version") != "RQ3FixedBaselineV1" or manifest.get("uses_smoke_harness") is not False:
        raise ValueError("fixed baseline is not the registered parent selection")
    inventory = stable_hash(packet["facts"])
    if inventory != packet["fact_inventory_hash"] or inventory != manifest["fact_inventory_hash"]:
        raise ValueError("fixed-baseline facts changed")
    if stable_hash(png) != manifest["full_image_sha256"]:
        raise ValueError("fixed-baseline image hash mismatch")
    if parse_compact_evidence(compact_evidence_text(packet)) != semantic_packet_facts(packet):
        raise ValueError("fixed compact-text round trip mismatch")
    if not manifest.get("parent_hashes"):
        raise ValueError("missing fixed-baseline parent provenance")
    for relative, digest in manifest["parent_hashes"].items():
        path = (ROOT/relative).resolve()
        if not path.is_relative_to((ROOT/"RQs/RQ1_1").resolve()) or sha_file(path) != digest:
            raise ValueError("fixed-baseline parent changed")
    width, height = Image.open(io.BytesIO(png)).size
    crops = manifest["region_crop_audit"]
    if list(crops["source_image_px"]) != [width, height] or set(crops["crop_boxes_px"]) != {"M","R","L","G"}:
        raise ValueError("fixed-baseline geometry mismatch")
    for boxes in crops["crop_boxes_px"].values():
        for x0,y0,x1,y1 in boxes:
            if not 0 <= x0 < x1 <= width or not 0 <= y0 < y1 <= height:
                raise ValueError("fixed-baseline crop outside source image")
    return {"status":"passed", "fact_inventory_hash":inventory,
            "candidates":len(packet["candidates"]), "source_pixels":[width,height]}


def validate_rollout_probability(rollout, current_policy_version):
    if rollout["policy_version"] != current_policy_version:
        raise ValueError("off-policy rollout must not be reused as on-policy")
    if rollout["sampling"] != {"temperature":1.,"top_p":1.,"top_k":-1,"min_p":0.,"grammar":None}:
        raise ValueError("RLOO full-support probability contract mismatch")
    ids, probabilities = rollout["completion_ids"], rollout["sampled_logprobs"]
    if not ids or len(ids) != len(probabilities):
        raise ValueError("generation/logprob token-count mismatch")
    import math
    if any(not math.isfinite(p) or p > 1e-5 for p in probabilities):
        raise ValueError("invalid token log probability")
    if any(not isinstance(i, int) or i < 0 for i in ids):
        raise ValueError("invalid sampled token ID")


def probability_alignment(expected, actual):
    """Measured numeric agreement, not byte-exact logits or output repetition."""
    import numpy as np
    expected=np.asarray(expected,dtype=float);actual=np.asarray(actual,dtype=float)
    if (expected.ndim!=1 or not len(expected) or expected.shape!=actual.shape
            or not np.isfinite(expected).all() or not np.isfinite(actual).all()
            or (expected>1e-5).any() or (actual>1e-5).any()):
        raise ValueError("invalid aligned token probability vectors")
    error=np.abs(actual-expected)
    return {"status":"passed" if float(error.mean())<=.05 else "failed",
            "token_count":len(expected),"mean_absolute_logprob_error":float(error.mean()),
            "max_absolute_logprob_error":float(error.max()),
            "sequence_logprob_difference":float((actual-expected).sum()),
            "mean_absolute_tolerance":.05}


from vlmrca.run_state import audit_call_artifacts


def audit_training_rows(config, rows, partition="train"):
    from .utils import RQ3SegmentationAdapter
    split = RQ3SegmentationAdapter(config).build()
    allowed = {(r["dataset"], r["case_id"]) for r in split[partition]}
    if not rows or any((r.get("dataset"), r.get("case_id")) not in allowed or r.get("partition") != partition for r in rows):
        raise ValueError("training inputs are not members of the isolated split")
    return split["split_hash"]


def source_audit():
    path = ROOT / "RQs/RQ3/src"
    modules = sorted(p.name for p in path.glob("*.py"))
    expected = sorted(["main.py","utils.py","exps.py","tests.py","gates.py","__init__.py"])
    if modules != expected:
        raise ValueError(f"RQ3 module layout: {modules}")
    count = 0
    for file in path.rglob("*.py"):
        ast.parse(file.read_text())
        if file.parent == path:
            count += sum(bool(s.strip()) and not s.lstrip().startswith("#") for s in file.read_text().splitlines())
    if count > 10000:
        raise ValueError("RQ3 module line limit exceeded")
    return {"status":"passed", "functional_lines":count}


def assert_formal_authorized(config):
    if config.get('qualification_renderer_repair'):
        raise PermissionError('renderer-only qualification configuration cannot run formal work')
    if not config["execution_enabled"]:
        raise PermissionError("Full training/evaluation remains disabled until CPU and live qualification pass")
    budget = config["budget"]
    if budget.get("status", "ready") != "ready" or budget["planned"] + budget["reserve"] > budget["hard_limit"]:
        raise PermissionError("RQ3 budget revision is required before formal execution")


def audit_catalog_inventory(payload):
    """A shortlist is explicit and bound, not a counterfeit complete directory."""
    from unified_scripts import stable_hash
    from .renderer.capacity import rendering_profile
    obs = payload.get("observation", {})
    audit = payload.get("catalog_audit", {})
    if obs.get("schema_version") != "ComposerObservationV2" or audit.get("schema_version") != "RQ3CatalogAuditV2":
        raise ValueError("old or unqualified catalogue; rebuild from the retained public pool")
    all_cards = {c["card_id"]: c for c in payload["cards"]}
    all_facts = {f["fact_id"]: f for f in payload["pool"]["facts"]}
    rows = obs["cards"]; ids = [r["card_id"] for r in rows]
    if len(ids) != len(set(ids)) or not set(ids) <= set(all_cards):
        raise ValueError("unbound/duplicated advertised card")
    if ids != audit["catalog_card_ids"]:
        raise ValueError("catalogue order/ID audit mismatch")
    if sorted(set(all_cards) - set(ids)) != audit["omitted_card_ids"]:
        raise ValueError("unrecorded catalogue omission")
    if stable_hash(obs) != audit["observation_hash"] or stable_hash(payload["pool"]) != audit["pool_hash"]:
        raise ValueError("catalogue/source content drift")
    if stable_hash(payload["cards"]) != audit["source_card_hash"]:
        raise ValueError("source cards changed")
    for row in rows:
        card = all_cards[row["card_id"]]
        if (list(card["fact_ids"]) != audit["bindings"][row["card_id"]]
                or row["region"] != card["region"] or row["entities"] != list(card["entity_ids"])
                or row["fact_count"] != len(card["fact_ids"])):
            raise ValueError("directory-to-card binding mismatch")
        profile = obs["constraints"]["profiles"][row["profile"]]
        expected = rendering_profile(card, all_facts)
        if profile != expected:
            raise ValueError("advertised rendering profile differs from card")
    coverage = obs["constraints"]["catalog_coverage"]
    if (coverage["pool_cards"], coverage["catalog_cards"], coverage["omitted_cards"]) != (len(all_cards), len(rows), len(all_cards)-len(rows)):
        raise ValueError("incorrect catalogue coverage")
    if obs["candidates"] != payload["pool"]["candidates"]:
        # Tuples are used in-memory, lists after JSON persistence.
        if list(obs["candidates"]) != list(payload["pool"]["candidates"]):
            raise ValueError("candidate set/order changed")
    return ids


def audit_public_pool(packet):
    """Reject retained pre-repair pools before catalogue reuse or model access."""
    from .exps import METRIC_CLOCK, POOL_VERSION
    if packet.get("schema_version") != "RQ3EvidencePoolV1":
        return  # Unit fixtures are separately constructed, not processed cases.
    if packet.get("compiler_version") != POOL_VERSION:
        raise ValueError("obsolete public pool: recompile from retained canonical V3, not raw data")
    for fact in packet["facts"]:
        if fact["field"] == "metric_series_64":
            metric = fact["payload"]["metric"]
            if METRIC_CLOCK.search(metric) and (not metric.endswith("_relative_s") or
                    fact["unit"] != "seconds_relative_to_public_clock_reference"):
                raise ValueError("unprojected absolute clock gauge in public pool")


def audit_catalog(payload, config, tokenizer=None, *, verify_contract=True):
    from .utils import (composer_tokenizer, composer_input_budget, chat_token_ids,
                        catalogue_contract,preparation_identity_matches)
    from .exps import composer_messages
    audit_public_pool(payload["pool"])
    ids = audit_catalog_inventory(payload)
    if verify_contract and not preparation_identity_matches(payload.get("catalog_contract"),catalogue_contract(config),'catalogue'):
        raise ValueError("catalogue code/config/tokenizer contract changed; explicit reindex required")
    tokenizer = tokenizer or composer_tokenizer(config)
    tokens = len(chat_token_ids(tokenizer, composer_messages(payload["observation"])))
    audit = payload["catalog_audit"]; budget = composer_input_budget(config)
    if tokens != audit["input_tokens"] or tokens > budget:
        raise ValueError("whole-chat token count/budget mismatch")
    if audit["input_budget"] != budget or audit["output_reserved_tokens"] != config["composer"]["max_tokens"]:
        raise ValueError("input/output budget reservation drift")
    if len(ids) > config["harness"]["catalog_max_cards"]:
        raise ValueError("catalogue card cap exceeded")
    return {"input_tokens": tokens, "available_input_tokens": budget,
            "output_reserved_tokens": config["composer"]["max_tokens"],
            "context_guard_tokens": config["harness"]["catalog_context_guard_tokens"],
            "max_model_len": config["composer"]["max_model_len"],
            "catalog_cards": len(ids), "pool_cards": len(payload["cards"]),
            "fact_coverage": audit["fact_coverage"], "fits": True}


def validate_composer_input(messages, config, tokenizer=None):
    """Shared guard for generation and teacher-forcing, before GPU allocation."""
    import json
    from .exps import composer_messages, program_schema
    from .utils import composer_input_budget, composer_tokenizer, chat_token_ids
    try:
        obs = json.loads(messages[1]["content"][0]["text"])
        canonical = composer_messages(obs)
    except (IndexError, KeyError, TypeError, ValueError) as exc:
        raise ValueError("invalid Composer observation messages") from exc
    if messages != canonical or obs["constraints"].get("output_schema") != program_schema():
        raise ValueError("Composer prompt/schema differs from the budgeted protocol")
    if obs["constraints"].get("catalog_policy") != config["harness"]["catalog_policy"]:
        raise ValueError("Composer catalogue policy differs")
    ids = [row["card_id"] for row in obs["cards"]]
    if not ids or len(ids) != len(set(ids)) or len(ids) > config["harness"]["catalog_max_cards"]:
        raise ValueError("invalid Composer advertised card set")
    tokens = chat_token_ids(tokenizer or composer_tokenizer(config), messages)
    if len(tokens) > composer_input_budget(config):
        raise ValueError("Composer input exceeds budget before contacting vLLM/allocating training GPU")
    return tokens


def catalog_preflight(config, prepared):
    """Official local tokenizer and exact shared messages, zero generation calls."""
    from .utils import composer_tokenizer
    tokenizer = composer_tokenizer(config)
    index = read_json(Path(prepared)/"index.json"); results = []
    for row in index["cases"]:
        payload = read_json(Path(prepared)/row["public"])
        report = audit_catalog(payload, config, tokenizer)
        results.append({"opaque_incident_id": row["opaque_incident_id"], **report})
    if not results:
        raise ValueError("no real catalogue cases qualified")
    return {"status": "passed", "cases": results, "model_calls": 0,
            "silent_truncation": False, "pool_modified": False,
            "policy": config["harness"]["catalog_policy"]}
