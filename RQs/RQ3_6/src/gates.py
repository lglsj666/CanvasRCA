"""Frozen cohorts, source registration and narrow execution authorization."""

import hashlib
from collections import Counter

from .utils import ROOT, digest, read_json, runtime_config, save_json


def contract(config):
    from RQs.RQ3_3.src.gates import source_contract

    files = source_contract(runtime_config(config))
    for folder in (
        "RQs/RQ3_4/src",
        "RQs/RQ3_5/src",
        "RQs/RQ3_6/src",
        "RQs/RQ3_6/configs",
        "RQs/RQ3_6/scripts",
    ):
        for path in sorted((ROOT / folder).glob("*")):
            if path.is_file():
                files[str(path.relative_to(ROOT))] = hashlib.sha256(
                    path.read_bytes()
                ).hexdigest()
    for name in (
        "RQs/RQ3_4/configs/integrated_round_v1.json",
        "scripts/vllm_vlm/serve_canvasrca_local.sh",
        "scripts/env_local.sh",
    ):
        files[name] = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
    return files


def register(config, root):
    from RQs.RQ3_3.src.gates import immutable_json

    from .utils import call_count

    parent = ROOT / config["implementation"]["roster_run"]
    if read_json(parent / "formal_queue_status.json")["state"] != "completed_screen_ab":
        raise ValueError("Predecessor discovery stage not complete")
    old = read_json(parent / "registration.json")
    rosters = {k: old["rosters"][k] for k in ("screen", "check")}
    groups = old["groups"]
    for name, count in (("screen", 20), ("check", 40)):
        if Counter(r["dataset"] for r in rosters[name]) != dict.fromkeys(
            config["qualification"]["datasets"], count
        ):
            raise ValueError("Frozen population changed")
        ids = [r["opaque_incident_id"] for r in rosters[name]]
        if len(set(ids)) != len(ids):
            raise ValueError("Duplicate incident")
    if {groups[r["opaque_incident_id"]] for r in rosters["screen"]} & {
        groups[r["opaque_incident_id"]] for r in rosters["check"]
    }:
        raise ValueError("Discovery/check overlap group")
    value = {
        "schema_version": "RQ36RegistrationV1",
        "config": config,
        "contract": contract(config),
        "rosters": rosters,
        "groups": groups,
        "source_registration": str(parent / "registration.json"),
        "exposure": "repeated_exposed",
        "stage": config.get("stage", "A") + "_only",
    }
    path = root / "registration.json"
    if path.exists() and read_json(path) != value:
        if (
            call_count(root, "rq36_smoke:" + config["experiment"])
            or list((root / "smokes").glob("*_started.json"))
            or call_count(root, "rq36_formal")
        ):
            raise ValueError(
                "Started protocol immutable; explicit version/repair required"
            )
        old = read_json(path)
        save_json(root / "preinference_revisions" / (digest(old) + ".json"), old)
        save_json(path, value)
    else:
        immutable_json(path, value)
    return value


def qualification_rows(config, registration):
    return [
        min(
            (r for r in registration["rosters"]["screen"] if r["dataset"] == d),
            key=lambda r: digest([42, "cpu", r["opaque_incident_id"]]),
        )
        for d in config["qualification"]["datasets"]
    ]


def tasks(config, registration, *, model=None, smoke=False, cpu=False):
    if model is not None and model not in config["models"]:
        raise ValueError("Unknown model")
    rows = (
        qualification_rows(config, registration)
        if smoke or cpu
        else registration["rosters"]["screen"] + registration["rosters"]["check"]
        if config.get("stage") == "B"
        else registration["rosters"]["check"]
    )
    arms = config["smoke_arms"] if smoke else config["arms"]
    stage = ("smoke_" if smoke else "cpu_" if cpu else "check_") + config["experiment"]
    out = []
    for m in config["models"]:
        if model is not None and model != m:
            continue
        for row in sorted(rows, key=lambda r: r["opaque_incident_id"]):
            for arm in arms:
                out.append(
                    {
                        "stage": stage,
                        "experiment": config["experiment"],
                        "model": m,
                        "case": row,
                        "dimensions": {
                            "arm": arm,
                            "phase": "qualification" if smoke or cpu else "check",
                        },
                        "ledger_scope": "rq36_smoke:" + config["experiment"]
                        if smoke
                        else "rq36_formal",
                        "logical_key": digest(
                            [
                                config["registration_id"],
                                stage,
                                m,
                                row["opaque_incident_id"],
                                arm,
                            ]
                        ),
                    }
                )
    if smoke and len(out) > (9 if model else 18):
        raise ValueError("Aggregate smoke limit exceeded")
    return out


def assert_current(config, registration):
    if config != registration["config"] or contract(config) != registration["contract"]:
        raise ValueError("Frozen source/config changed")


def authorize_run(config, registration, root, smoke):
    assert_current(config, registration)
    h = digest(registration["contract"])
    cpu = read_json(root / "cpu_qualification.json")
    if cpu["status"] != "passed" or cpu["contract_hash"] != h:
        raise ValueError("Current CPU qualification required")
    if smoke:
        import time

        marker = read_json(root / "smokes" / (config["experiment"] + "_started.json"))
        if marker["contract_hash"] != h or time.time() >= marker["deadline_unix"]:
            raise ValueError("No live bounded-smoke window")
    else:
        authority = read_json(root / "formal_authorization.json")
        qualification = read_json(root / "qualification.json")
        if authority != {
            "user_authorized": True,
            "stage": "B_exposed180" if config.get("stage") == "B" else "A_check120",
            "contract_hash": h,
        }:
            raise ValueError("Formal stage not authorized")
        if qualification["status"] != "passed" or qualification["contract_hash"] != h:
            raise ValueError("Current smoke qualification required")
        if not qualification.get("manual_review_passed"):
            raise ValueError("Manual input/output/image review required")
