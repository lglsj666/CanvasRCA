"""O05: stable instance indices follow evidence inventory, NOT layout traversal."""
def apply(design, visible=True, start=1):
    design["indexing"] = {"visible": visible, "start": start}
