"""O10: graph-only visibility; never alters edges, observations or candidates."""
def apply(design, show_isolates):
    design["graph"] = {"show_isolates": show_isolates}
