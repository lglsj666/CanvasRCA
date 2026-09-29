"""Reproduce only the interrupted CPU frontier; never launch a model."""

import concurrent.futures as cf

from RQs.RQ3_3.src.main import interleaved_sources
from RQs.RQ3_6.src.main import close_pool, cpu_pool
from RQs.RQ3_7.scripts.stage_c.operations import compile_prepared, scope
from RQs.RQ3_7.src import gates
from RQs.RQ3_7.src.utils import read_json, save_json, terminal_flag


def main():
    config, registration, root = scope()
    tasks = [t for t in gates.tasks(config, registration, "C")
             if terminal_flag(root, t) is None and t["dimensions"]["arm"] == "T_MATCH"]
    by_case = {t["case"]["opaque_incident_id"]: t for t in tasks}
    checks = {r["case"] for r in read_json(root / "stage_c_boundary_check.json")["completed"]}
    completed = {r["case"] for r in read_json(root / "stage_c_preparation.json")["completed"]}
    ordered = interleaved_sources([t["case"] for oid, t in by_case.items() if oid not in checks])
    frontier = [r for r in ordered[:len(completed) + 8] if r["opaque_incident_id"] not in completed]
    print("Diagnostic frontier:", [r["opaque_incident_id"] for r in frontier], flush=True)
    pool, queue, _ = cpu_pool(min(8, len(frontier)))
    results = []
    try:
        futures = {pool.submit(compile_prepared, (config, registration,
                   [by_case[r["opaque_incident_id"]]])): r for r in frontier}
        for future in cf.as_completed(futures):
            row = futures[future]
            try:
                future.result()
                result = {"case": row["opaque_incident_id"], "status": "passed"}
            except ValueError as exc:
                result = {"case": row["opaque_incident_id"], "status": "failed", "error": str(exc)}
            results.append(result)
            print(result, flush=True)
            save_json(root / "diagnostics/clock_frontier.json", results)
    finally:
        close_pool(pool, queue, abort=False)


if __name__ == "__main__":
    main()
