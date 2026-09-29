"""O08: substitute one compatible dashboard component at a fixed instance slot."""
def apply(design, card, component):
    def visit(node):
        if node["type"] == "panel":
            if node["card"] == card:
                node["component"] = component
                return 1
            return 0
        return sum(visit(child) for child in node["children"])
    if visit(design["tree"]) != 1:
        raise ValueError("Expected exactly one component instance")
