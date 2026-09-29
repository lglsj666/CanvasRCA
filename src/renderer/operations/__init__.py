"""Explicit operation registry. Operators transform design, never evidence."""
from copy import deepcopy
from . import appearance, bindings, component, indexing, layout, reorder, resolution, spacing, viewport, graph_visibility
from ..utils import compile_design, digest

REGISTRY = {
    "spacing": spacing.apply, "resolution": resolution.apply, "viewport": viewport.apply,
    "appearance": appearance.apply, "indexing": indexing.apply, "layout": layout.apply,
    "bindings": bindings.apply, "component": component.apply, "reorder": reorder.apply,
    "graph_visibility": graph_visibility.apply,
}


def apply_operations(evidence, design, operations):
    result, audit = deepcopy(design), []
    initial_evidence = digest(evidence)
    before = compile_design(evidence, result)
    for operation in operations:
        if set(operation) != {"op", "args"} or operation["op"] not in REGISTRY:
            raise ValueError("Unknown dashboard operation")
        old = deepcopy(before)
        REGISTRY[operation["op"]](result, **deepcopy(operation["args"]))
        before = compile_design(evidence, result)
        old_rects = {r["card"]: r for r in old["rectangles"]}
        changes = {r["card"]: sorted(k for k in r.keys() | old_rects[r["card"]].keys()
                                     if r.get(k) != old_rects[r["card"]].get(k))
                   for r in before["rectangles"] if r != old_rects[r["card"]]}
        audit.append({"operation": operation, "changed_rectangles": changes,
                      "before_hidden_isolates": old["hidden_graph_isolates"],
                      "after_hidden_isolates": before["hidden_graph_isolates"],
                      "before_design_hash": old["design_hash"], "after_design_hash": before["design_hash"]})
    if digest(evidence) != initial_evidence:
        raise ValueError("Operator changed evidence")
    return result, audit
