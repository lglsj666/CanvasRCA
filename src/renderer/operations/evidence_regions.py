"""Exact source-panel placements and four native region exports."""
def apply(design, panels, boxes):
    design['evidence_regions'] = {'schema':'EqualVerticalRegionsV1','header':32,'count':4}
    design['tree'] = {'id':'regions','type':'placed','children':panels,'boxes':boxes}
