"""Explicit bounded source-caption offsets. Does not edit evidence or defaults."""
def apply(design, offsets):
    design['anchor_pack']={'schema':'AnchorPackV1','offsets':offsets}
