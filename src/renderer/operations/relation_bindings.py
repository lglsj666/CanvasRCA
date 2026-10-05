"""Connect a two-endpoint observation to its exact public directed edge."""
def apply(design, links, style=None):
    design['relation_bindings'] = links
    if style is not None:
        design['relation_binding_style'] = style
