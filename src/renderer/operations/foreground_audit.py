"""Audit-only foreground registration; never modifies model-visible data."""
def apply(design, roles):
    design['provenance']={'schema':'CanonicalForegroundV1','roles':roles}
