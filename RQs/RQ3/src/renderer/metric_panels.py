"""Source-independent metric facet arrangement; no evidence selection or rescaling."""
import math


def lane_box(box, count, index, columns):
    if type(columns) is not int or columns not in (1, 2):
        raise ValueError('metric panel columns must be integer1 or2')
    if type(count) is not int or type(index) is not int or not 0 <= index < count:
        raise ValueError('invalid metric panel index/count')
    x0, y0, x1, y1 = box
    if not all(math.isfinite(v) for v in box) or x1 <= x0 or y1 <= y0:
        raise ValueError('invalid metric panel bounds')
    effective = min(columns, count)
    nrows = math.ceil(count / effective)
    column, row = divmod(index, nrows)
    gap = 18 if effective > 1 else 0
    width = (x1-x0-gap*(effective-1)) / effective
    top, bottom = y0+68, y1-31
    if bottom-top < nrows*72-6:
        raise ValueError('insufficient metric panel height')
    lane_height = max(72, (bottom-top)//nrows)
    left = x0 + column*(width+gap)
    right = left+width
    lane_top = top+row*lane_height
    lane_bottom = min(bottom, lane_top+lane_height-6)
    if width < 320 or lane_bottom-lane_top < 66:
        raise ValueError('insufficient metric panel width/height')
    return left, lane_top, right, lane_bottom
