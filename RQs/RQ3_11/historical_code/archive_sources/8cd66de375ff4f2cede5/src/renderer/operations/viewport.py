"""O03: logical canvas dimensions. Can reflow all panels; not a resolution-only change."""
def apply(design, width, height):
    design["viewport"] = {"width": width, "height": height}
