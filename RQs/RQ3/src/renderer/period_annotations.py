"""Display already selected MET-Z comparisons without altering statistics."""
import math
import re

FIELDS = ('regular_mean', 'current_mean', 'regular_std_dev', 'current_std_dev')
NUMBER = re.compile(r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?[kMG]?')


def comparison_text(payload):
    values = payload.get('sircl_met_z') or {}
    if any(values.get(k) is None for k in FIELDS):
        return None
    labels = [str(values[k]) for k in FIELDS]
    for key, value in zip(FIELDS, labels):
        if not NUMBER.fullmatch(value):
            raise ValueError('invalid metric period numeric label')
        number = float(value[:-1] if value[-1:] in ('k', 'M', 'G') else value)
        if not math.isfinite(number) or ('std_dev' in key and number < 0):
            raise ValueError('invalid metric period numeric value')
    a, b, c, d = labels
    return f'MET-Z regular → current | mean {a} → {b} | std {c} → {d}'


def period_context(geometry):
    from .human_dashboard import _fmt
    window = geometry.get('analysis_window') if geometry else None
    if window is None:
        return None
    if len(window) != 2 or any(isinstance(v, bool) or not isinstance(v, (int, float))
                             or not math.isfinite(v) or abs(v) >= 1e7 for v in window):
        raise ValueError('invalid relative metric comparison interval')
    start, end = window
    if end <= start:
        raise ValueError('invalid metric comparison interval order')
    return f'MET-Z regular t<{_fmt(start)}s; current {_fmt(start)}…{_fmt(end)}s'


def paint_comparison(draw, payload, box, color):
    from .human_dashboard import _font
    text = comparison_text(payload)
    if text is None:
        return []
    left, top, right, bottom = box
    font = _font(11, True)
    # Anchor the actual glyph top rather than treating baseline offsets as zero.
    offset = draw.textbbox((0, 0), text, font=font)[1]
    origin = (left, top - offset)
    bounds = draw.textbbox(origin, text, font=font)
    if bounds[0] < left or bounds[1] < top or bounds[2] > right or bounds[3] > bottom:
        raise ValueError('metric period annotation cannot fit without clipping')
    draw.text(origin, text, font=font, fill=color)
    return [{'kind': 'metric_period_annotation', 'text': text, 'bbox': list(bounds),
             'font_size_px': font.size, 'fields': {k: payload['sircl_met_z'][k] for k in FIELDS}}]
