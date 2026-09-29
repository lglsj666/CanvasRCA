"""Offline inspection of C's actual anchor, excluding unused predecessor arms."""

import pickle

from RQs.RQ3_3.src.utils import OfflineTokens, prepare_public_context
from RQs.RQ3_4.src.exps import assert_no_absolute_clock, pareto_priorities
from RQs.RQ3_4.src.utils import metric_selection_metadata
from RQs.RQ3_7.scripts.stage_c.operations import scope
from RQs.RQ3_7.src import exps, gates
from RQs.RQ3_7.src.utils import (
    ROOT,
    measurement_definitions,
    read_json,
    runtime_config,
    save_json,
)
from vlmrca.run_state import atomic_write

if __name__ == "__main__":
    config, registration, root = scope()
    oid = "INC-12D885A5B485"
    row = next(t["case"] for t in gates.tasks(config, registration, "C")
               if t["case"]["opaque_incident_id"] == oid)
    base = runtime_config(config)
    tokens = OfflineTokens(base)
    context, private = prepare_public_context(row, base)
    # Diagnostic-only checkpoint, never a committed production cache.
    atomic_write(root / "diagnostics/clock_work/public.pkl", pickle.dumps(context, protocol=5))
    save_json(root / "private/clock_diagnostic" / (oid + ".json"), private)
    parent = read_json(ROOT / "RQs/RQ3_4/configs/integrated_round_v1.json")
    context["selection_metadata"] = metric_selection_metadata(context, row, parent)
    context["integrated"] = {"priority_audit": pareto_priorities(context["observations"], context["selection_metadata"]),
                             "clock_projection_version": "relative_clock_v1"}
    context["rq36_parent_trace_unit"] = "us"
    # RE2 has microsecond trace provenance in the registered duration adapter.
    from RQs.RQ3_1.src.exps import _registered_trace_duration_projection
    factor, _ = _registered_trace_duration_projection(row["dataset"])
    context["rq36_parent_trace_unit"] = "us" if factor == 0.001 else "ms"
    view = exps.make_view(context, read_json(ROOT / config["implementation"]["parent_config"]),
                          tokens, measurement_definitions(config))
    texts = [p["text"] for p in view.parts]
    hits = [line for text in texts for line in text.splitlines() if "WiredTiger" in line]
    result = {"case": oid, "wiredtiger_actual_lines": hits}
    try:
        assert_no_absolute_clock(list(view.parts))
        result["actual_clock_check"] = "passed"
    except ValueError as exc:
        result["actual_clock_check"] = str(exc)
    save_json(root / "diagnostics/clock_actual_input.json", result)
    print(result, flush=True)
