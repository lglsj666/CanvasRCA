"""Read-only RQ2.1 qualification gates; never repair historical evidence."""

from __future__ import annotations

from .utils import (
    ROOT,
    RQ_ROOT,
    ProtocolError,
    artifacts_valid,
    checkpoint_identity,
    code_fingerprint,
    read_json,
    relative,
    sha_file,
    write_json,
)


def verify_parent_copy():
    manifest = read_json(RQ_ROOT / "configs/provenance/parent_renderer.json")
    adaptation = RQ_ROOT / "configs/provenance/renderer_adaptation.json"
    expected = read_json(adaptation).get("files", {}) if adaptation.is_file() else {}
    rows = []
    for row in manifest["files"]:
        source, target = ROOT / row["source"], ROOT / row["target"]
        rows.append(
            {
                "source": row["source"],
                "parent_still_matches": sha_file(source) == row["sha256"],
                "initial_copy_byte_verified": row["byte_equal_before_modification"],
                "snapshot_still_matches": sha_file(target) == expected.get(row["target"], "")
                if expected
                else target.read_bytes()
                == source.read_bytes().replace(b"RQs.RQ1_1.src.renderer", b"RQs.RQ2_1.src.renderer"),
            }
        )
    return {
        "passed": all(
            r["parent_still_matches"] and r["initial_copy_byte_verified"] and r["snapshot_still_matches"]
            for r in rows
        ),
        "files": rows,
    }


def bridge_display_audit(config):
    """Verify a selection-case bridge's recorded request and artifact identity.

    This checks provenance, not experimental qualification of every new arm.
    Parent model records are read-only; no private labels are consumed here.
    """
    roster = read_json(RQ_ROOT / "configs/rosters/public.json")["cases"]
    row = next(r for r in roster if r["dataset"] == "aiops2022" and r["role"] == "selection")
    opaque = row["opaque_incident_id"]
    prepared_root = ROOT / config["data"]["parent_prepared"]
    prepared_path = prepared_root / "prepared" / f"{opaque}.json"
    prepared = read_json(prepared_path)
    png = prepared_root / "renders" / f"{opaque}.dashboard.png"
    image_hash = sha_file(png)
    references = {}
    for model in config["models"]:
        summary = ROOT / config["data"]["parent_results"] / f"run_direct_rca_{model}_shard000-of-001.json"
        contract = read_json(summary)["run_contract"]
        if any(
            sha_file(ROOT / config["unified"][key]) != contract["unified_config_sha256"][key]
            for key in ("vllm", "scorer")
        ):
            raise ProtocolError("bridge runtime/scorer no longer matches the inherited configuration")
        for rep in ("T", "V"):
            path = (
                ROOT
                / config["data"]["parent_results"]
                / "trajectories/direct_rca"
                / model
                / f"{opaque}__{rep}.json"
            )
            record = read_json(path)
            checksum = record.pop("record_sha256")
            from unified_scripts import stable_hash

            if stable_hash(record) != checksum:
                raise ProtocolError("bridge source record checksum mismatch")
            stage = record["stages"][0]
            if stage["requested_max_tokens"] != config["request_adapter"]["max_tokens"]:
                raise ProtocolError("bridge request output adapter mismatch")
            images = [part["sha256"] for part in stage["parts"] if part["type"] == "image"]
            if images != ([image_hash] if rep == "V" else []):
                raise ProtocolError("bridge image differs from recorded request")
            references[f"{model}:{rep}"] = {
                "source": relative(path),
                "sha256": sha_file(path),
                "requested_max_tokens": stage["requested_max_tokens"],
            }
    if prepared["full_image_sha256"] != image_hash:
        raise ProtocolError("bridge prepared manifest image mismatch")
    result = {
        "schema": "RQ21BridgeReferenceCheckV1",
        "passed": True,
        "scope": "one selection case, both models, original T/V request references",
        "case": opaque,
        "original_png": relative(png),
        "original_png_sha256": image_hash,
        "bridge_references": references,
        "model_calls": 0,
    }
    write_json(RQ_ROOT / "results/registration/bridge_reference_check.json", result)
    return result


REVIEW_FOCI = (
    "logic_science",
    "logic_tools",
    "logic_representation",
    "code_data",
    "code_renderer",
    "code_recovery",
)


def protocol_fingerprint(config):
    from unified_scripts import stable_hash
    from unified_scripts.vllm_inference import VLLMInferenceConfig

    # User authorization flags may change after review; scientific controls may not.
    controls = {
        k: v for k, v in config.items() if k not in {"execution_enabled", "smoke_authorized", "status"}
    }
    runtime = VLLMInferenceConfig.load(ROOT / config["unified"]["vllm"])
    return stable_hash(
        {
            "config": controls,
            "models": {m: runtime.model(m) for m in config["models"]},
            "checkpoints": {m: checkpoint_identity(str(runtime.model_path(m))) for m in config["models"]},
            "roster": sha_file(RQ_ROOT / "configs/rosters/public.json"),
        }
    )


def execution_gate(config, *, formal=True, smoke=False):
    blockers = []
    if not config["smoke_authorized" if smoke else "execution_enabled"]:
        blockers.append("execution_disabled")
    if not verify_parent_copy()["passed"]:
        blockers.append("parent_or_initial_snapshot_changed_without_adaptation_provenance")
    path = RQ_ROOT / "results/registration/bridge_reference_check.json"
    if not path.is_file() or not read_json(path)["passed"]:
        blockers.append("bridge_reference_unverified")
    # These attestations are produced only by the actual completed reviews;
    # absence is not a timeout-only passage or an implementation success.
    code, protocol = code_fingerprint(), protocol_fingerprint(config)
    if config.get("fixed_anchor") and formal and not smoke:
        # Explicit user waiver: retain the actual old smokes as historical
        # qualification, do not forge refreshed live-smoke attestations.
        path = RQ_ROOT / "results/qualification/fixed_anchor_v2/proof.json"
        proof = read_json(path) if path.is_file() else {}
        if (
            proof.get("status") != "passed_static_user_smoke_waiver"
            or proof.get("code") != code
            or proof.get("protocol") != protocol
            or not artifacts_valid(proof)
        ):
            blockers.append("fixed_anchor_migration_not_verified")
        return {
            "passed": not blockers,
            "blockers": blockers,
            "model_calls": 0,
            "qualification": "inherited_smokes_plus_static_anchor_migration_user_waiver",
        }
    for name in REVIEW_FOCI:
        path = RQ_ROOT / "results/qualification" / f"{name}.json"
        row = read_json(path) if path.is_file() else {}
        if row.get("status") != "passed" or row.get("code") != code or row.get("protocol") != protocol:
            blockers.append(f"review_pending:{name}")
    for name in ("visual_review", "token_preflight"):
        path = RQ_ROOT / "results/qualification" / f"{name}.json"
        row = read_json(path) if path.is_file() else {}
        if row.get("status") != "passed" or row.get("protocol") != protocol or not artifacts_valid(row):
            blockers.append(f"qualification_pending:{name}")
    if formal and not smoke:
        for experiment in config["experiments"]:
            root = RQ_ROOT / "results" / f"{experiment}_smoke_v1"
            suffix = "_current" if (root / "qualification_current.json").is_file() else ""
            proof, review = root / f"qualification{suffix}.json", root / f"human_review{suffix}.json"
            report = read_json(proof) if proof.is_file() else {}
            manual = read_json(review) if review.is_file() else {}
            if (
                report.get("passed") is not True
                or report.get("code") != code
                or report.get("protocol") != protocol
                or not artifacts_valid(report)
            ):
                blockers.append(f"smoke_pending:{experiment}")
            if manual.get("passed") is not True or manual.get("qualification_sha256") != (
                sha_file(proof) if report else None
            ):
                blockers.append(f"conversation_review_pending:{experiment}")
    return {"passed": not blockers, "blockers": blockers, "model_calls": 0}


def offline_token_preflight(config, samples):
    """Native processor/tokenizer only; no model weights, CUDA, or generation."""
    import io

    from PIL import Image
    from transformers import AutoProcessor

    from unified_scripts.vllm_inference import VLLMInferenceConfig
    from vlmrca.vlm.attention_probe import processor_patch_geometry

    from .exps import RCA_SYSTEM_ROLE

    runtime = VLLMInferenceConfig.load(ROOT / config["unified"]["vllm"])
    rows = []
    for model in config["models"]:
        spec = runtime.model(model)
        model_config = read_json(runtime.model_path(model) / "config.json")
        processor = AutoProcessor.from_pretrained(
            runtime.model_path(model),
            local_files_only=True,
            trust_remote_code=spec.get("trust_remote_code", True),
            **(spec.get("mm_processor_kwargs") or {}),
        )
        for sample in samples:
            content = [
                {"type": "text", "text": p["text"]}
                if p["type"] == "text"
                else {
                    "type": "image",
                    "image": Image.open(io.BytesIO(p["png"])).convert("RGB"),
                }
                for p in sample["parts"]
            ]
            kwargs = dict(spec.get("default_chat_template_kwargs", {}))
            if model.startswith("qwen") and kwargs.get("enable_thinking") is False:
                kwargs["preserve_thinking"] = False
            batch = processor.apply_chat_template(
                [
                    {
                        "role": "system",
                        "content": [{"type": "text", "text": RCA_SYSTEM_ROLE}],
                    },
                    {"role": "user", "content": content},
                ],
                tokenize=True,
                add_generation_prompt=True,
                return_dict=True,
                return_tensors="pt",
                **kwargs,
            )
            count = int(batch["input_ids"].shape[-1])
            image_parts = [p for p in sample["parts"] if p["type"] == "image"]
            patch_geometry = None
            if image_parts:
                image_id = model_config["image_token_id"]
                visual_tokens = int((batch["input_ids"] == image_id).sum())
                image_size = Image.open(io.BytesIO(image_parts[0]["png"])).size
                patch_geometry = processor_patch_geometry(
                    model=model,
                    model_path=runtime.model_path(model),
                    image_size=image_size,
                    expected_tokens=visual_tokens,
                    mm_processor_kwargs=spec.get("mm_processor_kwargs"),
                )
                patch_geometry = {k: v for k, v in patch_geometry.items() if k != "source_token_boxes_px"}
            geometry = {
                k: {
                    "shape": list(v.shape),
                    "values": v.tolist() if v.numel() < 500 else None,
                }
                for k, v in batch.items()
                if k in {"image_grid_thw", "image_position_ids", "num_soft_tokens_per_image"}
            }
            rows.append(
                {
                    "case": sample["case"],
                    "arm": sample["arm"],
                    "model": model,
                    "tokens": count,
                    "geometry": geometry,
                    "verified_patch_geometry": patch_geometry,
                    "fits": count <= config["request_adapter"]["input_limit"]
                    and count + config["request_adapter"]["max_tokens"] <= spec["max_model_len"],
                }
            )
        del processor
    return {
        "status": "failed" if any(not r["fits"] for r in rows) else "passed",
        "rows": rows,
        "scope": "sample CPU preflight; every actual request also uses live preflight",
        "over_budget_designs": [r for r in rows if not r["fits"]],
        "model_calls": 0,
        "protocol": protocol_fingerprint(config),
    }
