"""Explicit large-canvas capability. Historical viewport limits stay unchanged."""
def apply(design, width, height):
    if type(width) is not int or type(height) is not int or not 800 <= width <= 8192 or not 600 <= height <= 8192:
        raise ValueError('Large canvas sides must be within the registered 8192px limit')
    design['canvas_extent'] = 'wide_8192_v1'
    design['viewport'] = {'width': width, 'height': height}
