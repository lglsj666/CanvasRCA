"""Targeted CPU qualification of the actual failed case, both processors."""

import json
import pickle
import time
from copy import deepcopy

from RQs.RQ3_3.src.utils import OfflineTokens
from RQs.RQ3_4.src.exps import assert_no_absolute_clock, pareto_priorities
from RQs.RQ3_4.src.utils import metric_selection_metadata
from RQs.RQ3_6.src.exps import qualify_witnesses
from RQs.RQ3_7.scripts.stage_c.clock_projection import project_log_clocks
from RQs.RQ3_7.scripts.stage_c.operations import compile_prepared, scope
from RQs.RQ3_7.src import gates
from RQs.RQ3_7.src.tests import persist_cpu_input
from RQs.RQ3_7.src.utils import ROOT, call_count, read_json, runtime_config, save_json

if __name__ == "__main__":
    started = time.monotonic()
    config, registration, root = scope()
    tasks = [t for t in gates.tasks(config, registration, "C")
             if t["case"]["opaque_incident_id"] == "INC-12D885A5B485"]
    before_calls = call_count(root)
    tokens = OfflineTokens(runtime_config(config))
    context = pickle.loads((root / "diagnostics/clock_work/public.pkl").read_bytes())
    parent = read_json(ROOT / "RQs/RQ3_4/configs/integrated_round_v1.json")
    context["selection_metadata"] = metric_selection_metadata(context, tasks[0]["case"], parent)
    context["integrated"] = {"priority_audit": pareto_priorities(context["observations"], context["selection_metadata"])}
    fixed = deepcopy(context)
    fixed["observations"], audit = project_log_clocks(context["observations"])
    p = read_json(ROOT / config["implementation"]["parent_config"])
    old_choice = qualify_witnesses(context, p, tokens)
    new_choice = qualify_witnesses(fixed, p, tokens)
    # Exact original public statistics still drive the same priorities.
    assert pareto_priorities(fixed["observations"], fixed["selection_metadata"]) == context["integrated"]["priority_audit"]
    selected = lambda choice: [[row["id"], row["members"]] for row in choice["packs"]]
    same_selection = selected(old_choice) == selected(new_choice)
    print("Changed log observations", len(audit["observations"]), "same selected packs", same_selection, flush=True)
    compiled = compile_prepared((config, registration, tasks))
    result = {"case": "INC-12D885A5B485", "status": "passed", "new_calls": 0,
              "clock_rows": len(audit["observations"]), "same_selected_packs": same_selection,
              "old_selected": selected(old_choice), "new_selected": selected(new_choice), "requests": []}
    for task, request in compiled:
        if "parts" not in request:
            raise ValueError(f"Unqualified actual request: {request}")
        assert_no_absolute_clock(request["parts"])
        joined = "\n".join(part.get("text", "") for part in request["parts"])
        assert audit["origin"] not in joined
        persist_cpu_input(root, task, request)
        result["requests"].append({"model": task["model"], "arm": task["dimensions"]["arm"],
                                   "input_identity": request["input_identity"],
                                   "clock_projected_in_input": "microseconds_component" in joined})
    assert call_count(root) == before_calls
    result["elapsed_s"] = time.monotonic() - started
    save_json(root / "diagnostics/clock_repair_cpu.json", result)
    print(json.dumps(result, indent=2), flush=True)
