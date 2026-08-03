#!/usr/bin/env python
"""
End-to-end smoke test: case -> dashboard -> VLM -> parse -> score.

The M1 gate for the project. RE2-OB is the default because it has the smallest
topology (10 services), its DataCase pickles are already cached, and its faults
are metric-dominant — if the dashboard cannot express a fault there, no amount
of agentic refinement will rescue the harder datasets.

  source scripts/env.sh
  python scripts/smoke_e2e.py --model mock            # no credentials needed
  python scripts/smoke_e2e.py --model claude-opus-4-7 --n 20
"""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import math
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "RQs"))

from vlmrca.cache import load_cases  # noqa: E402
from vlmrca.eval.run_experiment import run_experiment  # noqa: E402
from vlmrca.render.presets import (  # noqa: E402
    make_dashboard_config,
    parse_set_args,
)
from vlmrca.vlm.configs import VLMConfig, get_config  # noqa: E402

# M1 pass gates, from the approved plan.
GATE_PARSE_RATE = 0.95      # <= 1 parse failure in 20
GATE_MRR = 0.35             # random top-5 over 10 services is ~0.21
GATE_RENDER_S = 5.0         # per case

RQ0_SMOKE_DATASETS = ("re2_ob", "aiops2022", "aiops2025")
RQ0_SMOKE_ARMS = {
    "visual_text_topology",
    "text_only",
    "flat_structured",
}


def _verify_rq0_smoke(run_dir: Path, model: str) -> dict:
    """Post-hoc integrity gate for the registered three-case RQ0 smoke.

    Accuracy and structured-output acceptance are deliberately absent: this is
    an infrastructure/protocol qualification, not a model-selection run.
    """
    trajectory = run_dir / "trajectories" / "episodes.jsonl"
    if not trajectory.is_file():
        raise RuntimeError(f"RQ0 smoke trajectory is absent: {trajectory}")
    records = [json.loads(line) for line in trajectory.read_text().splitlines()]
    headers = [row for row in records if row.get("record_type") == "header"]
    episodes = [row for row in records if row.get("record_type") == "episode"]
    failures: list[str] = []
    if len(headers) != 1:
        failures.append(f"expected one header, found {len(headers)}")
    if len(episodes) != 9:
        failures.append(f"expected nine case-arm episodes, found {len(episodes)}")

    datasets = {row.get("dataset") for row in episodes}
    if datasets != set(RQ0_SMOKE_DATASETS):
        failures.append(f"dataset set mismatch: {sorted(str(v) for v in datasets)}")
    for dataset in RQ0_SMOKE_DATASETS:
        rows = [row for row in episodes if row.get("dataset") == dataset]
        case_ids = {row.get("case_id") for row in rows}
        arms = {row.get("arm") for row in rows}
        if len(case_ids) != 1 or arms != RQ0_SMOKE_ARMS:
            failures.append(
                f"{dataset}: expected one case and all three arms; "
                f"cases={len(case_ids)} arms={sorted(str(v) for v in arms)}"
            )

    for row in episodes:
        label = f"{row.get('dataset')}/{row.get('opaque_incident_id')}/{row.get('arm')}"
        if row.get("status") == "infrastructure_failure":
            failures.append(f"{label}: infrastructure failure: {row.get('error')}")
        if not row.get("leakage_audit_ok"):
            failures.append(f"{label}: leakage audit was not successful")
        for key in ("mrr", "ac1", "ac3", "ac5", "avg3", "avg5", "wall_time_s"):
            value = row.get(key)
            if not isinstance(value, (int, float)):
                failures.append(f"{label}: non-numeric {key}={value!r}")
        if model != "mock":
            if not isinstance(row.get("input_tokens"), int) or row["input_tokens"] <= 0:
                failures.append(f"{label}: missing server input-token accounting")
            if row.get("preflight_input_tokens") is None:
                failures.append(f"{label}: live /tokenize preflight failed")
            if row.get("server_token_count_match") is not True:
                failures.append(f"{label}: preflight/server token count mismatch")

        opaque = row.get("opaque_incident_id")
        arm = row.get("arm")
        required = (
            run_dir / "renders" / f"{opaque}.png",
            run_dir / "renders" / f"{opaque}.manifest.json",
            run_dir / "evidence" / f"{opaque}.ceb.json",
            run_dir / "evidence" / f"{opaque}.audit.json",
            run_dir / "conversations" / f"{opaque}__{arm}.md",
        )
        for path in required:
            if not path.is_file() or path.stat().st_size == 0:
                failures.append(f"{label}: missing/empty artifact {path}")

    report = {
        "gate": "rq0_partition_aware_three_case_smoke",
        "run_dir": str(run_dir),
        "trajectory_sha256": (
            hashlib.sha256(trajectory.read_bytes()).hexdigest()
            if trajectory.is_file()
            else None
        ),
        "model": model,
        "datasets": list(RQ0_SMOKE_DATASETS),
        "episode_count": len(episodes),
        "parse_failures_observed_not_gated": sum(
            not bool(row.get("parse_ok")) for row in episodes
        ),
        "model_truncations_observed_not_gated": sum(
            bool(row.get("truncated")) for row in episodes
        ),
        "failures": failures,
        "pass": not failures,
    }
    report_path = run_dir / "smoke_qualification_report.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    return report


def _run_rq0_smoke(model: str, replicate: str) -> int:
    run_name = f"{model}__validation__{replicate}"
    run_dir = (
        REPO
        / "RQs/RQ0/results"
        / "rq0_equal_information_equal_compute_v1"
        / run_name
    )
    command = [
        sys.executable,
        str(REPO / "RQs/RQ0/scripts/run_rq0.py"),
        "--model",
        model,
        "--partition",
        "validation",
        "--datasets",
        *RQ0_SMOKE_DATASETS,
        "--replicate",
        replicate,
    ]
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join((str(REPO / "RQs"), str(REPO)))
    completed = subprocess.run(command, cwd=REPO, env=env, check=False)
    if completed.returncode:
        return completed.returncode
    report = _verify_rq0_smoke(run_dir, model)
    print("\n=== RQ0 smoke qualification ===")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["pass"] else 1


def _verify_training_smoke(run_dir: Path) -> dict:
    """Verify optimizer/infrastructure integrity without accuracy or loss floors."""
    summary_path = run_dir / "summary.json"
    contract_path = run_dir / "run_contract.json"
    trajectory_path = run_dir / "trajectories/episodes.jsonl"
    failures: list[str] = []
    if not summary_path.is_file():
        failures.append("summary.json is absent")
        summary = {}
    else:
        summary = json.loads(summary_path.read_text())
    if not contract_path.is_file():
        failures.append("run_contract.json is absent")
        contract = {}
    else:
        contract = json.loads(contract_path.read_text())
    if not trajectory_path.is_file():
        failures.append("training trajectory is absent")
        episodes = []
    else:
        rows = [json.loads(line) for line in trajectory_path.read_text().splitlines()]
        episodes = [row for row in rows if row.get("record_type") == "episode"]

    expected = set(RQ0_SMOKE_DATASETS)
    if len(episodes) != 3:
        failures.append(f"expected three training episodes, found {len(episodes)}")
    if {row.get("dataset") for row in episodes} != expected:
        failures.append("training smoke dataset set mismatch")
    if any(row.get("stage_partition") != "train" for row in episodes):
        failures.append("a training smoke case is not in the train subpartition")
    for row in episodes:
        if row.get("status") != "ok" or row.get("unexpected_issue"):
            failures.append(f"{row.get('opaque_incident_id')}: training status is not clean")
        loss = row.get("loss")
        if not isinstance(loss, (int, float)) or not math.isfinite(loss):
            failures.append(f"{row.get('opaque_incident_id')}: loss is not finite")
        conversation = run_dir / "conversations" / f"{row.get('opaque_incident_id')}.md"
        if not conversation.is_file() or conversation.stat().st_size == 0:
            failures.append(f"{row.get('opaque_incident_id')}: conversation is absent")

    if summary.get("optimizer_steps") != 1:
        failures.append(f"expected one optimizer step, found {summary.get('optimizer_steps')}")
    if summary.get("accuracy_used_as_smoke_gate") is not False:
        failures.append("accuracy was not explicitly excluded from smoke passage")
    if summary.get("loss_magnitude_used_as_smoke_gate") is not False:
        failures.append("loss magnitude was not explicitly excluded from smoke passage")
    if contract.get("created_before_optimizer_step") is not True:
        failures.append("optimizer contract was not frozen before the step")
    if contract.get("source_partition") != "development":
        failures.append("training smoke source partition is not development")
    checkpoints = summary.get("checkpoints") or []
    if len(checkpoints) != 1:
        failures.append(f"expected one smoke checkpoint, found {len(checkpoints)}")
    for relative in checkpoints:
        checkpoint = REPO / relative
        for name in ("adapter_config.json", "adapter_model.safetensors", "trainer_state.pt"):
            if not (checkpoint / name).is_file():
                failures.append(f"checkpoint artifact is absent: {relative}/{name}")

    report = {
        "gate": "causal_integration_sft_partition_aware_three_case_smoke",
        "run_dir": str(run_dir),
        "datasets": sorted(expected),
        "episode_count": len(episodes),
        "optimizer_steps": summary.get("optimizer_steps"),
        "mean_loss_observed_not_thresholded": summary.get("mean_teacher_forced_loss"),
        "accuracy_observed_not_gated": None,
        "failures": failures,
        "pass": not failures,
    }
    (run_dir / "smoke_qualification_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    )
    return report


def _run_training_smoke(run_name: str) -> int:
    run_dir = REPO / "RQs/RQ0/results/causal_integration_sft_smoke_v1" / run_name
    command = [
        str(REPO / "venvs/train/bin/python"),
        "-m",
        "vlmrca.training.train",
        "--config",
        str(REPO / "RQs/RQ0/configs/training/causal_integration_sft_v1.yaml"),
        "--mode",
        "smoke",
        "--run-name",
        run_name,
    ]
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join((str(REPO / "RQs"), str(REPO)))
    completed = subprocess.run(command, cwd=REPO, env=env, check=False)
    if completed.returncode:
        return completed.returncode
    report = _verify_training_smoke(run_dir)
    print("\n=== causal-integration SFT smoke qualification ===")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["pass"] else 1


def _typed_model_overrides(pairs: list[str]) -> dict:
    """Coerce `--model-set field=value` strings to their VLMConfig field types."""
    declared = {f.name: str(f.type) for f in dataclasses.fields(VLMConfig)}
    out = {}
    for key, raw in parse_set_args(pairs).items():
        if key not in declared:
            raise KeyError(
                f"Unknown VLMConfig field {key!r}. Known: {sorted(declared)}"
            )
        text = declared[key]
        if "bool" in text:
            low = raw.lower()
            if low not in {"true", "false", "1", "0", "yes", "no", "on", "off"}:
                raise ValueError(f"--model-set {key}={raw!r} is not a boolean")
            out[key] = low in {"true", "1", "yes", "on"}
        elif "int" in text:
            out[key] = int(raw)
        elif "float" in text:
            out[key] = float(raw)
        else:
            out[key] = raw
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", default="mock")
    ap.add_argument(
        "--rq0",
        action="store_true",
        help="run the registered RQ0 three-case/three-arm validation smoke "
        "through RQs/RQ0/scripts/run_rq0.py and its post-hoc integrity verifier",
    )
    ap.add_argument(
        "--training",
        action="store_true",
        help="run the registered causal-integration SFT three-case optimizer smoke",
    )
    ap.add_argument(
        "--replicate",
        default="smoke",
        help="diagnostic run label (used with --rq0 or --training)",
    )
    ap.add_argument("--dataset", default="re2_ob")
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--modality", default="hybrid", choices=["hybrid", "image_only", "text_only"])
    ap.add_argument(
        "--config",
        default="v0",
        help="dashboard preset name (RQs/vlmrca/render/presets.py); unknown names raise",
    )
    ap.add_argument(
        "--set",
        dest="set_fields",
        action="append",
        default=[],
        metavar="FIELD=VALUE",
        help="override one DashboardConfig field, repeatable "
        "(e.g. --set panel_budget=6 --set show_logs=false)",
    )
    ap.add_argument(
        "--model-set",
        dest="model_set_fields",
        action="append",
        default=[],
        metavar="FIELD=VALUE",
        help="override one VLMConfig field, repeatable "
        "(e.g. --model-set thinking=true --model-set max_tokens=32768)",
    )
    ap.add_argument("--experiment", default=None)
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--no-renders", action="store_true")
    ap.add_argument(
        "--render-cache",
        dest="render_cache",
        action="store_true",
        default=True,
        help="reuse byte-identical renders across runs (default on); "
        "shared at results/render_cache, keyed by case + config fingerprint",
    )
    ap.add_argument("--no-render-cache", dest="render_cache", action="store_false")
    ap.add_argument(
        "--no-gates",
        action="store_true",
        help="skip the M1 smoke gates. Use for production arms: the MRR floor "
             "fails control arms (text_only) for confirming the hypothesis.",
    )
    args = ap.parse_args()

    if args.rq0 and args.training:
        ap.error("--rq0 and --training are mutually exclusive")
    if args.training:
        return _run_training_smoke(args.replicate)
    if args.rq0:
        return _run_rq0_smoke(args.model, args.replicate)

    exp = args.experiment or f"smoke_{args.dataset}_{args.config}"
    out_dir = args.out or (REPO / "results" / exp)

    print(f"loading {args.n} {args.dataset} cases from the frozen manifest ...", flush=True)
    cases = load_cases(args.dataset, limit=args.n)
    print(f"loaded {len(cases)} cases", flush=True)

    cfg = make_dashboard_config(args.config, parse_set_args(args.set_fields))
    model_cfg = get_config(args.model, **_typed_model_overrides(args.model_set_fields))
    print(
        f"dashboard: preset={args.config} name={cfg.name} fingerprint={cfg.fingerprint()}\n"
        f"model:     {model_cfg.tag} temp={model_cfg.temperature} top_p={model_cfg.top_p} "
        f"seed={model_cfg.seed} thinking={model_cfg.thinking} max_tokens={model_cfg.max_tokens}",
        flush=True,
    )
    render_cache_dir = (REPO / "results" / "render_cache") if args.render_cache else None
    summary = run_experiment(
        cases,
        model=args.model,
        model_cfg=model_cfg,
        dashboard_cfg=cfg,
        modality=args.modality,
        experiment=exp,
        out_dir=out_dir,
        save_renders=not args.no_renders,
        render_cache_dir=render_cache_dir,
    )

    print("\n=== summary ===")
    print(json.dumps({k: v for k, v in summary.items() if k != "dashboard_config"}, indent=2, default=str))

    # An accuracy floor is a smoke-test idea and a measurement bug. `text_only`
    # is the CONTROL arm of the modality comparison -- the hypothesis is that it
    # scores lower than hybrid -- so gating on `mrr >= 0.35` fails the run
    # precisely when the experiment is working. gemma-4-26b-a4b's text_only arm
    # scored 0.333 and exited 1 with 100 clean episodes and parse rate 1.000.
    # An exit code that fires on a real result trains everyone to ignore exit
    # codes, so production arms pass --no-gates and are judged on their summary.
    if getattr(args, "no_gates", False):
        # ...but parse rate is NOT an outcome gate, it is a validity gate, and
        # dropping it with the others was a regression. qwen3.5-9b returned
        # parse_rate 0.740 here -- 26 of 100 cases ran to the 16384-token
        # ceiling and scored 0 -- which is a broken arm, not a low score. An arm
        # that cannot answer is excluded from analysis either way, so it should
        # still exit non-zero. Only the MRR floor and the wall-clock ceiling are
        # skipped: the first fails control arms for confirming the hypothesis,
        # the second fails every model slower than the smoke test's subject.
        pr = summary.get("parse_rate", 0.0)
        print("\n=== M1 gates: accuracy and wall-clock skipped (--no-gates) ===")
        print(f"  {'PASS' if pr >= GATE_PARSE_RATE else 'FAIL'}  "
              f"parse_rate={pr:.3f} >= {GATE_PARSE_RATE}  (validity, still enforced)")
        if pr < GATE_PARSE_RATE:
            print("  This arm did not produce usable answers on "
                  f"{(1 - pr) * 100:.0f}% of cases. Check stop_reason=length "
                  "before treating its MRR as a measurement.")
            return 1
        return 0

    checks = {
        "parse_rate": (summary.get("parse_rate", 0.0), GATE_PARSE_RATE, ">="),
        "mrr": (summary.get("mrr", 0.0), GATE_MRR, ">="),
        "wall_clock_s_per_case": (summary.get("avg_wall_clock_s", 0.0), GATE_RENDER_S * 6, "<="),
    }
    print("\n=== M1 gates ===")
    failed = []
    for name, (val, thresh, op) in checks.items():
        ok = val >= thresh if op == ">=" else val <= thresh
        print(f"  {'PASS' if ok else 'FAIL'}  {name}={val:.3f} {op} {thresh}")
        if not ok:
            failed.append(name)

    if args.model == "mock":
        print("\nNote: mock backend exercises render/prompt/parse/score only; "
              "the MRR gate is meaningful only with a real model.")
        return 0
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
