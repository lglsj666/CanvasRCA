"""Small fail-closed utilities for the RQ3.1 identity/window registration."""
from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from unified_scripts import canonical_json, stable_hash

ROOT = Path(__file__).resolve().parents[3]


def sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def implementation_hash() -> str:
    """Bind method, rendering and inherited runtime dependencies, not only the dispatcher."""
    roots = ("RQs/RQ3_1/src", "packages/rq31_sircl_native", "RQs/RQ1_1/src",
             "RQs/RQ2_1/src", "RQs/RQ2/src", "packages/rq21_native",
             "src/vlmrca", "src/unified_scripts")
    paths = {path for directory in roots for path in (ROOT / directory).rglob("*.py")
             if path.name != "tests.py" and "__pycache__" not in path.parts}
    paths.update(ROOT / name for name in ("configs/vllm_inference_local.yaml",
        "RQs/RQ1_1/configs/rq1.yaml", "RQs/RQ2_1/configs/rq2_1.yaml"))
    return stable_hash([{ "path": str(path.relative_to(ROOT)), "sha256": sha_file(path)}
                        for path in sorted(paths)])


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def exact_write(path: Path, value: Any) -> str:
    """Write once; a resume must reproduce exactly the same bytes."""
    body = value if isinstance(value, bytes) else json_bytes(value)
    if path.exists():
        if path.read_bytes() != body:
            raise ValueError(f"existing registration differs: {path}")
        return hashlib.sha256(body).hexdigest()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_bytes(body)
    temporary.replace(path)
    return hashlib.sha256(body).hexdigest()


def _skip_json_value(text: str, index: int) -> int:
    """Lexically skip one JSON value without deserializing it."""
    n = len(text)
    if index >= n:
        raise ValueError("truncated JSON value")
    if text[index] == '"':
        index += 1
        escaped = False
        while index < n:
            char = text[index]
            index += 1
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                return index
        raise ValueError("unterminated JSON string")
    if text[index] in "[{":
        stack = ["]" if text[index] == "[" else "}"]
        index += 1
        quoted = escaped = False
        while index < n and stack:
            char = text[index]
            index += 1
            if quoted:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    quoted = False
            elif char == '"':
                quoted = True
            elif char == "[":
                stack.append("]")
            elif char == "{":
                stack.append("}")
            elif char == stack[-1]:
                stack.pop()
        if stack:
            raise ValueError("unterminated JSON collection")
        return index
    while index < n and text[index] not in ",}":
        index += 1
    return index


def read_selected_top_level(path: Path, allowed: Iterable[str]) -> dict[str, Any]:
    """Decode only named top-level values; label values are lexically skipped."""
    allowed = frozenset(allowed)
    decoder = json.JSONDecoder()
    text = path.read_text(encoding="utf-8")
    index = 0

    def whitespace(position: int) -> int:
        while position < len(text) and text[position].isspace():
            position += 1
        return position

    index = whitespace(index)
    if index >= len(text) or text[index] != "{":
        raise ValueError(f"private record is not an object: {path}")
    index += 1
    output: dict[str, Any] = {}
    while True:
        index = whitespace(index)
        if index < len(text) and text[index] == "}":
            index = whitespace(index + 1)
            if index != len(text):
                raise ValueError(f"trailing private JSON content: {path}")
            if set(output) != allowed:
                raise ValueError(f"private record misses allowed fields: {sorted(allowed-set(output))}")
            return output
        key, index = decoder.raw_decode(text, index)
        if not isinstance(key, str):
            raise ValueError("non-string top-level JSON key")
        index = whitespace(index)
        if index >= len(text) or text[index] != ":":
            raise ValueError("malformed private JSON object")
        index = whitespace(index + 1)
        if key in allowed:
            if key in output:
                raise ValueError(f"duplicate allowed private field: {key}")
            output[key], index = decoder.raw_decode(text, index)
        else:
            index = _skip_json_value(text, index)
        index = whitespace(index)
        if index < len(text) and text[index] == ",":
            index += 1
            continue
        if index >= len(text) or text[index] != "}":
            raise ValueError("malformed private JSON delimiter")


def read_selected_object_field(path: Path, field: str, allowed_nested: Iterable[str]) -> dict[str, Any]:
    """Decode allowlisted members of one top-level object and skip all others."""
    allowed_nested = frozenset(allowed_nested)
    decoder = json.JSONDecoder()
    text = path.read_text(encoding="utf-8")

    def whitespace(position: int) -> int:
        while position < len(text) and text[position].isspace():
            position += 1
        return position

    def selected_object(position: int) -> tuple[dict[str, Any], int]:
        position = whitespace(position)
        if position >= len(text) or text[position] != "{":
            raise ValueError(f"selected private field is not an object: {field}")
        position += 1
        output: dict[str, Any] = {}
        while True:
            position = whitespace(position)
            if position < len(text) and text[position] == "}":
                return output, position + 1
            key, position = decoder.raw_decode(text, position)
            position = whitespace(position)
            if position >= len(text) or text[position] != ":":
                raise ValueError("malformed selected private object")
            position = whitespace(position + 1)
            if key in allowed_nested:
                if key in output:
                    raise ValueError(f"duplicate selected private member: {key}")
                output[key], position = decoder.raw_decode(text, position)
            else:
                position = _skip_json_value(text, position)
            position = whitespace(position)
            if position < len(text) and text[position] == ",":
                position += 1
                continue
            if position >= len(text) or text[position] != "}":
                raise ValueError("malformed selected private object delimiter")

    position = whitespace(0)
    if position >= len(text) or text[position] != "{":
        raise ValueError(f"private record is not an object: {path}")
    position += 1
    found = None
    while True:
        position = whitespace(position)
        if position < len(text) and text[position] == "}":
            if found is None:
                raise ValueError(f"private record misses selected object: {field}")
            return found
        key, position = decoder.raw_decode(text, position)
        position = whitespace(position)
        if position >= len(text) or text[position] != ":":
            raise ValueError("malformed private JSON object")
        position = whitespace(position + 1)
        if key == field:
            if found is not None:
                raise ValueError(f"duplicate selected private object: {field}")
            found, position = selected_object(position)
        else:
            position = _skip_json_value(text, position)
        position = whitespace(position)
        if position < len(text) and text[position] == ",":
            position += 1
            continue
        if position >= len(text) or text[position] != "}":
            raise ValueError("malformed private JSON delimiter")


def epoch(value: Any) -> float:
    if isinstance(value, bool):
        raise ValueError("boolean is not a timestamp")
    if isinstance(value, (int, float)):
        result = float(value)
    else:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        result = (parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)).timestamp()
    if not math.isfinite(result):
        raise ValueError("non-finite timestamp")
    return result


def related(left: dict[str, Any], right: dict[str, Any]) -> bool:
    same_event = bool(left.get("event")) and left["event"] == right.get("event")
    overlap = (
        left["source"] == right["source"]
        and max(float(left["start"]), float(right["start"]))
        <= min(float(left["end"]), float(right["end"]))
    )
    return same_event or overlap


def source_hashes(config: dict[str, Any]) -> dict[str, str]:
    references = dict(config["sources"])
    return {name: sha_file(ROOT / spec["path"]) for name, spec in sorted(references.items())}


def verify_source_hashes(config: dict[str, Any]) -> dict[str, str]:
    observed = source_hashes(config)
    expected = {name: spec["sha256"] for name, spec in sorted(config["sources"].items())}
    if observed != expected:
        changed = sorted(name for name in expected if observed.get(name) != expected[name])
        raise ValueError(f"protected data-registration source changed: {changed}")
    return observed


def record_hash(value: Any) -> str:
    return stable_hash(value)


def compact_status(value: Any) -> str:
    return canonical_json(value)


# ---------------------------------------------------------------------------
# RQ3.1 same-fact representation twins
# ---------------------------------------------------------------------------

SOLVER_EVIDENCE_SCHEMA = "ContrastSolverEvidenceV1"
REPRESENTATION_SCHEMA = "RepresentationTwinV1"
FACT_KEYS = frozenset({"fact_id", "region", "field", "entity_ids", "relative_bins", "unit", "payload"})
BUNDLE_KEYS = frozenset({
    "bundle_id", "mechanism", "comparison_key", "side_a", "side_b", "relation_fact_ids", "fact_ids",
})
RELATION_KEYS = frozenset({"relation_id", "type", "subject", "object", "fact_id"})
FORBIDDEN_VISIBLE_KEYS = frozenset({
    "ground_truth", "label", "labels", "accepted_labels", "dataset", "dataset_name", "case_id",
    "fault_type", "fault_description", "absolute_time", "absolute_timestamp", "timestamp",
    "injection_time", "injection_timestamp", "injection_ground_truth", "source_path", "file_path",
    "source_ids", "source_bindings", "selection_score", "relevance", "contrast_strength", "coverage_q",
    "semantic_cost", "selection_hash", "pool_hash", "bundle_hash", "fact_inventory_hash",
    "template_full_sha256",
})
VISIBLE_LEAK_TOKENS = ("aiops2022", "aiops2025", "aegislab", "re2_ob", "re2_tt", "/home/", "dataset/")
VISIBLE_IPV4 = re.compile(r"(?<![\w.])(?:\d{1,3}\.){3}\d{1,3}(?![\w.])")
VISIBLE_UUID = re.compile(r"(?i)(?<![0-9a-f])[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}(?![0-9a-f])")
VISIBLE_K8S_HOST = re.compile(
    r"(?i)\b[a-z0-9][a-z0-9-]*(?:\.[a-z0-9][a-z0-9-]*)*\.svc(?:\.cluster\.local)?\b"
)

RQ31_SOLVER_SYSTEM_PROMPT = (
    "You are an expert Site Reliability Engineer performing Root Cause Analysis (RCA) "
    "for a microservice application deployed on a Kubernetes cluster."
)
_RQ31_TEXT_ARMS = frozenset({"T", "T_COMPACT", "P0_T_CAL", "X_T", "X_C", "X_C_TABLE", "SIRCL_TEXT"})
_RQ31_SCREENSHOT_ARMS = frozenset({"X_S", "X_C_TABLE_S"})
_RQ31_VISUAL_ARMS = frozenset({"V", "P0_V_STANDARD", "P0_V_CONTRAST", "X_V_STANDARD", "X_V_CONTRAST"})
_RQ31_MIXED_ARMS = frozenset({"TPV", "X_MTEXT"})


def rq31_solver_system_prompt() -> str:
    """One system role for inherited P0 and counterfactual X anchors."""
    return RQ31_SOLVER_SYSTEM_PROMPT


def rq31_solver_read_guide(arm: str) -> str:
    """Return the minimal common RCA discipline plus carrier-accurate grammar."""
    known = _RQ31_TEXT_ARMS | _RQ31_SCREENSHOT_ARMS | _RQ31_VISUAL_ARMS | _RQ31_MIXED_ARMS
    if arm not in known:
        raise ValueError(f"no RQ3.1 read guide for arm {arm!r}")
    common = """A fault has occurred. Identify where it originated, not merely the loudest downstream or co-located symptom. Root causes may be services, pods, or nodes. Three digits identify a service, four a node, and five a pod; return only IDs from the exhaustive candidate list.

M supplies metric series with relative coordinates, numeric samples, source units and diagnostics. R supplies operation or service counts and duration summaries. L supplies observed messages or templates, occurrence counts and relative-bin information. Use only the fields actually supplied. G supplies concrete caller→callee, pod→node hosting, and pod→service membership relations. Direction or co-location alone does not prove causality. Oxx denotes one unique observation. Cxx compares two sides by O-reference, and REL lists relation O-references; a later Cxx may reuse an earlier Oxx without repeating its values. A REPEATED WHOLE BUNDLE section redraws or restates the same referenced observations for display load only; it adds no new event or count.

Use the inherited SIRCL* discipline in M→R→L→G order: assess metric changes and supplied sample counts; compare supplied parent wall-duration and non-child wall-time proxy observations without subtracting aggregates or interpreting either as CPU execution or measured waiting; compare adjacent caller/callee observations only when a concrete relation supports that adjacency; inspect log rate/template diagnostics; then use concrete relations and relative timing to test origin versus propagation. Form a preliminary ranking, verify top-1 with two supplied-evidence checks including one contradiction or alternative, and revise if contradicted. Do this internally and do not emit hidden reasoning labels.

Return exactly one JSON object: {"services":["candidate-id"],"reason":"compact evidence-grounded verification summary","confidence":"high|medium|low"}. Rank at most five candidate IDs. The reason is at most three sentences and states the two checks and any decisive relation."""
    if arm == "X_C_TABLE":
        carrier = """Read the direct comparison table literally. Each C block places the actual supplied observations for its named A and B sides locally; CONTEXT and REL rows retain selected supporting observations. The same O-reference can appear in more than one C block without becoming a new event or count. A labelled REPEAT block is a registered display-load repeat only."""
    elif arm in _RQ31_TEXT_ARMS:
        carrier = """Read the supplied natural or compact text literally. In a clean carrier observation values occur once in the catalogue and comparisons contain references. A labelled REPEATED WHOLE BUNDLE section restates the same observations only for a registered display-load condition. Relative coordinates remain explicit in each metric/log observation."""
    elif arm == "X_C_TABLE_S":
        carrier = """The image is a lossless screenshot of the direct comparison table, not a chart. Read wrapped table lines literally; wrapping adds no field or value, and repeated O-references remain the same observations."""
    elif arm in _RQ31_SCREENSHOT_ARMS:
        carrier = """The image is a lossless screenshot of the natural-text evidence, not a chart. Read wrapped lines literally; wrapping adds no field or value."""
    elif arm in _RQ31_VISUAL_ARMS:
        carrier = """Read the telemetry dashboard as graphics. Metric titles state entity type/ID, metric and y-unit; numeric x/y axes state either the shared relative axis or a panel-local relative axis. Curves connect successive supplied numeric samples at their true displayed x. Trace bars encode supplied numeric values. Relation overviews combine a graph with an authoritative O-indexed ledger. Standard groups overview regions; Contrast places short comparison references near relevant primitives. A reference may point to a shared primitive elsewhere on the same image; a labelled Repeated whole bundle block restates every observation from that bundle in fixed-size readable rows while reusing its clean graphical primitive."""
    else:
        carrier = """The mixed carrier places metric observations in compact text and R/L/G observations in one dashboard image. O-references and any labelled repeated-bundle load are shared across the two parts."""
    if arm.startswith("P0_"):
        semantics = ("Metrics retain their supplied baseline/MET-Z fields. MET-Z compares early and later "
                     "means in baseline standard deviations. TRC-L counts and ExL summaries use the inherited "
                     "span-ID child-duration subtraction proxy, not measured CPU execution or waiting. "
                     "LOG-R fields are error-keyword and log-volume summaries; Denum template numeric previews "
                     "belong to the supplied log groups.")
    else:
        semantics = ("The reference interval is the first half of the observed time range; current is its "
                     "second half, not a supplied failure injection boundary. Metric baseline/current values "
                     "are medians. signed robust change is the largest signed deviation from the reference "
                     "median divided by 1.4826 times its median absolute deviation, floored at 0.001 of the "
                     "series' largest absolute value and 1e-12, and capped at ±999. Each time bin shows its "
                     "largest absolute excursion from that reference, with its observed sample count; min/max "
                     "summaries retain full-series extrema. The non-child wall-time proxy subtracts the union "
                     "of observed direct-child intervals within the same trace. It is not measured CPU execution "
                     "or waiting. log counts are observed message occurrences, not LOG-R scores. Repeated "
                     "identical messages are grouped without removing diagnostic numbers.")
    return common + "\n\n" + semantics + "\n\n" + carrier


def _mapping(value: Any, label: str) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    converter = getattr(value, "to_dict", None)
    if callable(converter):
        result = converter()
        if isinstance(result, Mapping):
            return dict(result)
    raise ValueError(f"{label} must be a mapping or expose to_dict()")


def _audit_visible_keys(value: Any, path: str = "visible") -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            normalized = str(key).strip().lower()
            if normalized in FORBIDDEN_VISIBLE_KEYS or normalized.endswith("_sha256"):
                raise ValueError(f"forbidden model-visible key at {path}.{key}")
            _audit_visible_keys(nested, f"{path}.{key}")
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, nested in enumerate(value):
            _audit_visible_keys(nested, f"{path}[{index}]")


def _validate_entity_id(value: Any) -> str:
    entity = str(value)
    if not entity.isdigit() or len(entity) not in (3, 4, 5):
        raise ValueError(f"entity is not a case-local 3/4/5-digit numeric ID: {entity!r}")
    return entity


def _validate_solver_evidence(materialized: Any) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    public = _mapping(materialized, "materialized solver evidence")
    if set(public) != {"schema_version", "facts", "bundles", "relations"}:
        raise ValueError(f"solver evidence root is not the exact public allowlist: {sorted(public)}")
    if public["schema_version"] != SOLVER_EVIDENCE_SCHEMA:
        raise ValueError(f"unexpected solver evidence schema: {public['schema_version']!r}")
    facts = [_mapping(value, "fact") for value in public["facts"]]
    bundles = [_mapping(value, "bundle") for value in public["bundles"]]
    relations = [_mapping(value, "relation") for value in public["relations"]]
    if not facts:
        raise ValueError("solver evidence contains no selected facts")
    ids: set[str] = set()
    for fact in facts:
        if set(fact) != FACT_KEYS:
            raise ValueError(f"fact is not the exact public allowlist: {sorted(fact)}")
        fact_id = str(fact["fact_id"])
        if not fact_id or fact_id in ids:
            raise ValueError("fact IDs must be nonempty and unique")
        ids.add(fact_id)
        fact["fact_id"] = fact_id
        if fact["region"] not in ("M", "R", "L", "G"):
            raise ValueError(f"invalid fact region: {fact['region']!r}")
        if not isinstance(fact["field"], str) or not fact["field"]:
            raise ValueError("fact field must be nonempty text")
        if not isinstance(fact["entity_ids"], (list, tuple)):
            raise ValueError("fact entity_ids must be a sequence")
        fact["entity_ids"] = [_validate_entity_id(value) for value in fact["entity_ids"]]
        if not isinstance(fact["relative_bins"], (list, tuple)):
            raise ValueError("fact relative_bins must be a sequence")
        if not isinstance(fact["payload"], Mapping):
            raise ValueError("fact payload must be an object")
        _audit_visible_keys(fact["payload"], f"fact[{fact_id}].payload")
    referenced: set[str] = set()
    bundle_ids: set[str] = set()
    for bundle in bundles:
        if set(bundle) != BUNDLE_KEYS:
            raise ValueError(f"bundle is not the exact public allowlist: {sorted(bundle)}")
        bundle_id = str(bundle["bundle_id"])
        if not bundle_id or bundle_id in bundle_ids:
            raise ValueError("bundle IDs must be nonempty and unique")
        bundle_ids.add(bundle_id)
        bundle["bundle_id"] = bundle_id
        for side_name in ("side_a", "side_b"):
            side = _mapping(bundle[side_name], side_name)
            required = {"label", "role", "fact_ids", "entity_ids"}
            optional = {"observed_subtypes"}
            if not required <= set(side) or set(side) - required - optional:
                raise ValueError(f"{side_name} is not the exact public allowlist: {sorted(side)}")
            side["fact_ids"] = [str(value) for value in side["fact_ids"]]
            side["entity_ids"] = [_validate_entity_id(value) for value in side["entity_ids"]]
            if "observed_subtypes" in side:
                if not isinstance(side["observed_subtypes"], (list, tuple)) or not all(
                    isinstance(value, str) and value for value in side["observed_subtypes"]
                ):
                    raise ValueError(f"{side_name} observed_subtypes must be nonempty strings")
                side["observed_subtypes"] = list(side["observed_subtypes"])
            bundle[side_name] = side
        bundle["fact_ids"] = [str(value) for value in bundle["fact_ids"]]
        bundle["relation_fact_ids"] = [str(value) for value in bundle["relation_fact_ids"]]
        if len(bundle["fact_ids"]) != len(set(bundle["fact_ids"])):
            raise ValueError(f"bundle {bundle_id} duplicates a fact")
        missing = set(bundle["fact_ids"]) - ids
        if missing:
            raise ValueError(f"bundle {bundle_id} references unknown facts: {sorted(missing)}")
        for side_name in ("side_a", "side_b"):
            if not set(bundle[side_name]["fact_ids"]) <= set(bundle["fact_ids"]):
                raise ValueError(f"bundle {bundle_id} {side_name} is not fact-closed")
            if not bundle[side_name]["fact_ids"]:
                raise ValueError(f"bundle {bundle_id} lacks complete bilateral evidence")
        if not set(bundle["relation_fact_ids"]) <= set(bundle["fact_ids"]):
            raise ValueError(f"bundle {bundle_id} relation facts are not closed")
        referenced.update(bundle["fact_ids"])
    # P0 calibration packets legitimately carry context facts which are not
    # members of a bilateral ContrastBundle.  They remain first-class facts in
    # every representation; the renderer places them in an explicit context
    # block.  X selections enforce bundle closure in the selector/materializer,
    # not by deleting otherwise valid public facts at this projection boundary.
    if not referenced <= ids:
        raise ValueError("materialized bundles reference facts outside the selected inventory")
    relation_ids: set[str] = set()
    for relation in relations:
        if set(relation) != RELATION_KEYS:
            raise ValueError(f"relation is not the exact public allowlist: {sorted(relation)}")
        relation_id = str(relation["relation_id"])
        if not relation_id or relation_id in relation_ids:
            raise ValueError("relation IDs must be nonempty and unique")
        relation_ids.add(relation_id)
        relation["relation_id"] = relation_id
        relation["subject"] = _validate_entity_id(relation["subject"])
        relation["object"] = _validate_entity_id(relation["object"])
        relation["fact_id"] = str(relation["fact_id"])
        if relation["fact_id"] not in ids:
            raise ValueError(f"relation {relation_id} references an unknown fact")
    return facts, bundles, relations


def _candidate_text(candidates: Sequence[Any]) -> str:
    values = [_validate_entity_id(value) for value in candidates]
    if not values or len(values) != len(set(values)):
        raise ValueError("candidate IDs must be nonempty and unique")
    return "Candidate IDs (complete ordered set): " + ", ".join(values) + "\n"


def _fact_inventory(facts: Sequence[Mapping[str, Any]]) -> tuple[str, ...]:
    return tuple(sorted(str(fact["fact_id"]) for fact in facts))


def _audit_visible_text(*values: str) -> None:
    text = "\n".join(values).lower()
    leaked = [token for token in VISIBLE_LEAK_TOKENS if token in text]
    if "inc-" in text:
        leaked.append("opaque incident ID")
    if VISIBLE_IPV4.search(text):
        leaked.append("raw IPv4 address")
    if VISIBLE_UUID.search(text):
        leaked.append("raw UUID")
    if VISIBLE_K8S_HOST.search(text):
        leaked.append("raw Kubernetes service hostname")
    if leaked:
        raise ValueError(f"model-visible representation contains forbidden identity/path token: {leaked}")


def _attach_screenshot_fact_bindings(
    screenshot: dict[str, Any], natural: Mapping[str, Any],
) -> dict[str, Any]:
    rows: dict[int, list[dict[str, Any]]] = {}
    for binding in screenshot["line_bindings"]:
        rows.setdefault(int(binding["source_line"]), []).append(binding)
    output = dict(screenshot)
    output["fact_primitive_bindings"] = {
        fact_id: [item for line in lines for item in rows.get(int(line), [])]
        for fact_id, lines in natural["fact_line_bindings"].items()
    }
    missing = sorted(fact_id for fact_id, items in output["fact_primitive_bindings"].items() if not items)
    if missing:
        raise ValueError(f"screenshot facts lack visible line bindings: {missing}")
    return output


@dataclass(frozen=True)
class RepresentationTwinV1:
    """All same-selection projections; bytes remain separate from audit metadata."""

    candidate_text: str
    natural_text: str
    compact_compare_text: str
    direct_compare_table_text: str
    screenshot_png: bytes | None
    direct_compare_table_screenshot_png: bytes | None
    standard_png: bytes | None
    contrast_png: bytes | None
    mtext_text: str
    mtext_png: bytes | None
    fact_inventory: tuple[str, ...]
    manifests: Mapping[str, Any] = field(repr=False)
    schema_version: str = REPRESENTATION_SCHEMA

    def validate(self) -> None:
        if self.schema_version != REPRESENTATION_SCHEMA:
            raise ValueError("representation schema drift")
        statuses = self.manifests.get("carrier_status")
        if not isinstance(statuses, Mapping):
            raise ValueError("representation twin lacks per-carrier status")
        images = {
            "screenshot": self.screenshot_png,
            "direct_compare_table_screenshot": self.direct_compare_table_screenshot_png,
            "standard": self.standard_png,
            "contrast": self.contrast_png,
        }
        for name, value in images.items():
            available = statuses.get(name, {}).get("status") == "available"
            if available != (value is not None):
                raise ValueError(f"{name} carrier status/bytes disagree")
            if value is not None and not value.startswith(b"\x89PNG"):
                raise ValueError(f"{name} carrier is not PNG")
        if self.mtext_png is not None and not self.mtext_png.startswith(b"\x89PNG"):
            raise ValueError("mixed visual carrier is not PNG")
        expected = set(self.fact_inventory)
        for name in ("natural_text", "compact_compare_text", "direct_compare_table_text",
                     "screenshot", "direct_compare_table_screenshot", "standard", "contrast"):
            if statuses.get(name, {}).get("status") != "available":
                continue
            manifest = self.manifests[name]
            bindings = set(manifest.get("fact_line_bindings", manifest.get("fact_primitive_bindings", {})))
            if bindings != expected:
                raise ValueError(f"{name} fact inventory differs: {sorted(expected ^ bindings)}")
        if statuses.get("mtext", {}).get("status") == "available":
            mixed = set(self.manifests["mtext"]["text_fact_line_bindings"]) | set(
                self.manifests["mtext"]["image_fact_primitive_bindings"]
            )
            if mixed != expected:
                raise ValueError(f"M-text mixed fact inventory differs: {sorted(expected ^ mixed)}")
            if set(self.manifests["mtext"]["text_fact_line_bindings"]) & set(
                self.manifests["mtext"]["image_fact_primitive_bindings"]
            ):
                raise ValueError("M-text mixed duplicated a fact across carriers")

    def require_image(self, carrier: str) -> bytes:
        """Return one available image or raise a typed per-carrier capacity error."""
        from .renderer.contrast import RepresentationCapacityError

        fields = {
            "screenshot": self.screenshot_png,
            "direct_compare_table_screenshot": self.direct_compare_table_screenshot_png,
            "standard": self.standard_png,
            "contrast": self.contrast_png,
            "mtext": self.mtext_png,
        }
        if carrier not in fields:
            raise ValueError(f"unknown image carrier {carrier!r}")
        value = fields[carrier]
        status = self.manifests.get("carrier_status", {}).get(carrier, {})
        # M-text legitimately has no PNG when every selected fact is metric.
        if carrier == "mtext" and value is None and status.get("status") == "available":
            raise ValueError("available M-text carrier has no image component")
        if value is None:
            raise RepresentationCapacityError(
                f"{carrier} carrier unavailable: {status.get('reason', 'capacity unavailable')}"
            )
        return value

    def to_manifest(self) -> dict[str, Any]:
        self.validate()
        return {
            "schema_version": self.schema_version,
            "fact_inventory": list(self.fact_inventory),
            "candidate_text_sha256": hashlib.sha256(self.candidate_text.encode("utf-8")).hexdigest(),
            "natural_text_sha256": hashlib.sha256(self.natural_text.encode("utf-8")).hexdigest(),
            "compact_compare_text_sha256": hashlib.sha256(self.compact_compare_text.encode("utf-8")).hexdigest(),
            "direct_compare_table_text_sha256": hashlib.sha256(
                self.direct_compare_table_text.encode("utf-8")
            ).hexdigest(),
            "mtext_text_sha256": hashlib.sha256(self.mtext_text.encode("utf-8")).hexdigest(),
            "images": {
                "screenshot": hashlib.sha256(self.screenshot_png).hexdigest() if self.screenshot_png else None,
                "direct_compare_table_screenshot": hashlib.sha256(
                    self.direct_compare_table_screenshot_png
                ).hexdigest() if self.direct_compare_table_screenshot_png else None,
                "standard": hashlib.sha256(self.standard_png).hexdigest() if self.standard_png else None,
                "contrast": hashlib.sha256(self.contrast_png).hexdigest() if self.contrast_png else None,
                "mtext": hashlib.sha256(self.mtext_png).hexdigest() if self.mtext_png is not None else None,
            },
            "projection_manifests": dict(self.manifests),
            "max_pngs_per_arm": 1,
            "model_visible_opaque_identity": False,
            "model_visible_selector_statistics": False,
        }


def compile_representation_twin(
    materialized: Any, *, candidates: Sequence[Any],
    renderer_parameters: Mapping[str, Any] | None = None,
    display_reference_schedule: Sequence[Mapping[str, Any]] | None = None,
) -> RepresentationTwinV1:
    """Compile all registered carriers from one complete materialized selection."""
    from .renderer.contrast import (
        RepresentationCapacityError,
        project_compact_comparative_text,
        project_direct_comparison_table,
        project_natural_text,
        render_contrast_dashboard,
        render_standard_dashboard,
        render_text_screenshot,
    )

    parameters = dict(renderer_parameters or {
        "comparison_grouping": "contrast",
        "shared_time_alignment": True,
        "preserve_relative_bins": True,
    })
    if set(parameters) != {
        "comparison_grouping", "shared_time_alignment", "preserve_relative_bins",
    }:
        raise ValueError("renderer_parameters must use the exact registered fields")
    if parameters["comparison_grouping"] not in {"contrast", "disabled"}:
        raise ValueError("comparison_grouping must be contrast or disabled")
    if not isinstance(parameters["shared_time_alignment"], bool):
        raise ValueError("shared_time_alignment must be boolean")
    if parameters["preserve_relative_bins"] is not True:
        raise ValueError("relative bins must remain unchanged by renderer interventions")
    schedule = [dict(row) for row in (display_reference_schedule or ())]
    facts, bundles, relations = _validate_solver_evidence(materialized)
    # Relation rows are validated as a public typed view. Their underlying fact
    # is already present in each projection; serializing relation IDs would add
    # an audit-only identifier and duplicate the observed relation.
    del relations
    candidates_visible = _candidate_text(candidates)
    natural_text, natural_manifest = project_natural_text(
        facts, bundles, display_reference_schedule=schedule,
    )
    compact_text, compact_manifest = project_compact_comparative_text(
        facts, bundles, display_reference_schedule=schedule,
    )
    direct_table_text, direct_table_manifest = project_direct_comparison_table(
        facts, bundles, display_reference_schedule=schedule,
    )
    carrier_status: dict[str, dict[str, Any]] = {
        "natural_text": {"status": "available"},
        "compact_compare_text": {"status": "available"},
        "direct_compare_table_text": {"status": "available"},
    }

    def unavailable(name: str, exc: RepresentationCapacityError) -> dict[str, Any]:
        carrier_status[name] = {"status": "unavailable", "reason": str(exc)}
        return {"status": "unavailable", "reason": str(exc), "fact_inventory": list(_fact_inventory(facts))}

    try:
        screenshot_png, screenshot_manifest = render_text_screenshot(natural_text)
        screenshot_manifest = _attach_screenshot_fact_bindings(screenshot_manifest, natural_manifest)
        carrier_status["screenshot"] = {"status": "available"}
    except RepresentationCapacityError as exc:
        screenshot_png, screenshot_manifest = None, unavailable("screenshot", exc)
    try:
        direct_table_screenshot_png, direct_table_screenshot_manifest = render_text_screenshot(
            direct_table_text
        )
        direct_table_screenshot_manifest = _attach_screenshot_fact_bindings(
            direct_table_screenshot_manifest, direct_table_manifest,
        )
        carrier_status["direct_compare_table_screenshot"] = {"status": "available"}
    except RepresentationCapacityError as exc:
        direct_table_screenshot_png, direct_table_screenshot_manifest = (
            None, unavailable("direct_compare_table_screenshot", exc)
        )
    try:
        standard_png, standard_manifest = render_standard_dashboard(
            facts, bundles, shared_time=parameters["shared_time_alignment"],
            display_reference_schedule=schedule,
        )
        carrier_status["standard"] = {"status": "available"}
    except RepresentationCapacityError as exc:
        standard_png, standard_manifest = None, unavailable("standard", exc)
    try:
        contrast_png, contrast_manifest = render_contrast_dashboard(
            facts, bundles,
            grouping=parameters["comparison_grouping"] == "contrast",
            shared_time=parameters["shared_time_alignment"],
            display_reference_schedule=schedule,
        )
        carrier_status["contrast"] = {"status": "available"}
    except RepresentationCapacityError as exc:
        contrast_png, contrast_manifest = None, unavailable("contrast", exc)
    metric_facts = [fact for fact in facts if fact["region"] == "M"]
    nonmetric_facts = [fact for fact in facts if fact["region"] != "M"]
    metric_ids = {str(fact["fact_id"]) for fact in metric_facts}
    bundles_by_id = {str(bundle["bundle_id"]): bundle for bundle in bundles}
    mtext_text_schedule = [
        row for row in schedule
        if metric_ids & set(map(str, bundles_by_id.get(str(row.get("bundle_id")), {}).get("fact_ids", ())))
    ]
    nonmetric_ids = {str(fact["fact_id"]) for fact in nonmetric_facts}
    mtext_image_schedule = [
        row for row in schedule
        if nonmetric_ids & set(map(str, bundles_by_id.get(str(row.get("bundle_id")), {}).get("fact_ids", ())))
    ]
    mtext_text, mtext_text_manifest = project_compact_comparative_text(
        facts, bundles, regions=("M",), display_reference_schedule=mtext_text_schedule,
    )
    if nonmetric_facts:
        try:
            mtext_png, mtext_image_manifest = render_contrast_dashboard(
                facts, bundles, regions=("R", "L", "G"),
                grouping=parameters["comparison_grouping"] == "contrast",
                shared_time=parameters["shared_time_alignment"],
                display_reference_schedule=mtext_image_schedule,
            )
            image_bindings = mtext_image_manifest["fact_primitive_bindings"]
            carrier_status["mtext"] = {"status": "available"}
        except RepresentationCapacityError as exc:
            mtext_png, image_bindings = None, {}
            mtext_image_manifest = unavailable("mtext", exc)
    else:
        mtext_png, mtext_image_manifest, image_bindings = None, None, {}
        carrier_status["mtext"] = {"status": "available", "image_component": "not_required"}
    _audit_visible_text(candidates_visible, natural_text, compact_text, direct_table_text, mtext_text)
    inventory = _fact_inventory(facts)
    twin = RepresentationTwinV1(
        candidate_text=candidates_visible,
        natural_text=natural_text,
        compact_compare_text=compact_text,
        direct_compare_table_text=direct_table_text,
        screenshot_png=screenshot_png,
        direct_compare_table_screenshot_png=direct_table_screenshot_png,
        standard_png=standard_png,
        contrast_png=contrast_png,
        mtext_text=mtext_text,
        mtext_png=mtext_png,
        fact_inventory=inventory,
        manifests={
            "carrier_status": carrier_status,
            "public_allowlist": {
                "root": ["schema_version", "facts", "bundles", "relations"],
                "fact": sorted(FACT_KEYS), "bundle": sorted(BUNDLE_KEYS), "relation": sorted(RELATION_KEYS),
            },
            "renderer_parameters": parameters,
            "display_reference_schedule": schedule,
            "natural_text": natural_manifest,
            "compact_compare_text": compact_manifest,
            "direct_compare_table_text": direct_table_manifest,
            "screenshot": screenshot_manifest,
            "direct_compare_table_screenshot": direct_table_screenshot_manifest,
            "standard": standard_manifest,
            "contrast": contrast_manifest,
            "mtext": {
                "schema_version": "RQ31MTextMixedV1",
                "text_regions": ["M"], "image_regions": ["R", "L", "G"],
                "text_fact_line_bindings": mtext_text_manifest["fact_line_bindings"],
                "text_display_reference_schedule": mtext_text_schedule,
                "image_fact_primitive_bindings": image_bindings,
                "image_display_reference_schedule": mtext_image_schedule,
                "image_manifest": mtext_image_manifest,
                "metric_fact_count": len(metric_facts),
            },
        },
    )
    twin.validate()
    return twin
