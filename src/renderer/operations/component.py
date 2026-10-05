"""O08: substitute one compatible dashboard component at a fixed instance slot."""
def apply(design, card, component, node_layout=None, dashed_width_scale=None):
    def visit(node):
        if node["type"] == "panel":
            if node["card"] == card:
                node["component"] = component
                node.pop('node_layout', None)
                node.pop('dashed_width_scale', None)
                if node_layout is not None:
                    node['node_layout'] = node_layout
                if dashed_width_scale is not None:
                    node['dashed_width_scale'] = dashed_width_scale
                return 1
            return 0
        return sum(visit(child) for child in node.get("children", []))
    if visit(design["tree"]) != 1:
        raise ValueError("Expected exactly one component instance")
