"""Explicit operation registry. Operators transform design, never evidence."""
from copy import deepcopy
from . import raster_translation, readability_audit, factual_qa, anchor_pack, question_colors, evidence_regions, readable_cards, qa_badges, foreground_audit, canvas_extent, appearance, bindings, component, indexing, layout, reorder, resolution, spacing, viewport, graph_visibility, relation_bindings
from ..utils import compile_design, digest

# Export operations consume frozen source DOM, rather than rewriting its design.
# Ordinary design operations and existing renderer paths are unchanged.
from .source_views import SourceViewRenderer
EXPORT_REGISTRY = {"source_views": SourceViewRenderer}

REGISTRY = {
    "raster_translation": raster_translation.apply,
    "readability_audit": readability_audit.apply,
    "factual_qa": factual_qa.apply,
    "anchor_pack": anchor_pack.apply,
    "question_colors": question_colors.apply,
    "evidence_regions": evidence_regions.apply,
    "readable_cards": readable_cards.apply,
    "qa_badges": qa_badges.apply,
    "control_glyph": lambda design, binding, part: design.update(control_glyph={"binding":binding,"part":part}),
    "foreground_audit": foreground_audit.apply,
    "canvas_extent": canvas_extent.apply,
    "spacing": spacing.apply, "resolution": resolution.apply, "viewport": viewport.apply,
    "appearance": appearance.apply, "indexing": indexing.apply, "layout": layout.apply,
    "bindings": bindings.apply, "component": component.apply, "reorder": reorder.apply,
    "graph_visibility": graph_visibility.apply, "relation_bindings": relation_bindings.apply,
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
        changes = {r["card"]: sorted(k for k in r.keys() | old_rects.get(r["card"], {}).keys()
                                     if r.get(k) != old_rects.get(r["card"], {}).get(k))
                   for r in before["rectangles"] if r != old_rects.get(r["card"])}
        audit.append({"operation": operation, "changed_rectangles": changes,
                      "before_hidden_isolates": old["hidden_graph_isolates"],
                      "after_hidden_isolates": before["hidden_graph_isolates"],
                      "before_design_hash": old["design_hash"], "after_design_hash": before["design_hash"]})
    if digest(evidence) != initial_evidence:
        raise ValueError("Operator changed evidence")
    return result, audit
