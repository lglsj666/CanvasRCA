"""O09: permute a container's children; slot sizes/weights stay unchanged."""
def apply(design, container, order):
    def find(node):
        if node["id"] == container:
            return node
        for child in node.get("children", []):
            hit = find(child)
            if hit is not None:
                return hit
        return None
    node = find(design["tree"])
    if node is None or node["type"] == "panel":
        raise ValueError("Reorder target must be a layout container")
    children = {c["id"]: c for c in node["children"]}
    if len(order) != len(children) or set(order) != set(children):
        raise ValueError("Reorder must be a complete permutation; no hidden removal")
    node["children"] = [children[cid] for cid in order]
