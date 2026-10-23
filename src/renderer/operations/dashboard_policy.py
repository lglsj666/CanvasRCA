"""Persistent canvas/card contract; legacy designs and components are unchanged.

Viewport/resolution operations cannot enforce a card cap or stop a subsequent
operation from changing the PNG size. This adds the missing validation contract.
"""
POLICY = "fixed_4096_28_v1"
SIDE = 4096
MAX_CARDS = 28


def apply(design):
    design["dashboard_policy"] = POLICY
    design["viewport"] = {"width": SIDE, "height": SIDE}
    design["scale"] = 1


def validate(evidence, design):
    if "dashboard_policy" not in design:
        return  # Preserve frozen historical geometry.
    if design["dashboard_policy"] != POLICY:
        raise ValueError("Unknown dashboard policy")
    if design["viewport"] != {"width": SIDE, "height": SIDE} or design["scale"] != 1:
        raise ValueError("New dashboard requires a 4096x4096 PNG at scale 1")
    if len(evidence["cards"]) > MAX_CARDS:
        raise ValueError("Dashboard exceeds 28 cards; select evidence explicitly before rendering")
