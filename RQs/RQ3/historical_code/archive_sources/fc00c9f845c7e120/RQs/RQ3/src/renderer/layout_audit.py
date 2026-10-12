"""Check actual label ink on the final drawing surface, not temporary masks.

Only text/text and text/card-boundary integrity is checked. Text intentionally
annotating a curve or heatmap is not a collision with the chart itself.
"""
from PIL import Image, ImageChops, ImageDraw


class AuditedDraw:
    def __init__(self, draw):
        self.draw = draw
        self.owner = "header"
        self.bounds = (0, 0, *draw._image.size)
        self.labels = []
        self.label_count = 0

    def __getattr__(self, name):
        return getattr(self.draw, name)

    def set_owner(self, name, box):
        self.owner, self.bounds, self.labels = name, tuple(box), []

    def _check(self, box, mask):
        ink = mask.getbbox()
        if ink is None:
            return
        # Ignore surrounding whitespace; require every painted glyph pixel to
        # belong to the current card (or to the dashboard header).
        x, y = box[:2]
        actual = (x + ink[0], y + ink[1], x + ink[2], y + ink[3])
        left, top, right, bottom = self.bounds
        if actual[0] < left or actual[1] < top or actual[2] > right or actual[3] > bottom:
            raise ValueError(f"renderer text leaves card {self.owner}: {actual}")
        for previous, painted in self.labels:
            overlap = (max(box[0], previous[0]), max(box[1], previous[1]),
                       min(box[2], previous[2]), min(box[3], previous[3]))
            if overlap[0] >= overlap[2] or overlap[1] >= overlap[3]:
                continue
            a = mask.crop(tuple(v - box[i % 2] for i, v in enumerate(overlap)))
            b = painted.crop(tuple(v - previous[i % 2] for i, v in enumerate(overlap)))
            if ImageChops.darker(a, b).getbbox() is not None:
                raise ValueError(f"renderer text overlaps within card {self.owner}: {overlap}")
        self.labels.append((box, mask))
        self.label_count += 1

    def text(self, xy, text, *args, **kwargs):
        if args:
            raise TypeError("audited renderer requires named text style arguments")
        geometry = {k: v for k, v in kwargs.items() if k in {
            "font", "anchor", "spacing", "align", "direction", "features", "language", "stroke_width"}}
        box = self.draw.textbbox(xy, text, **geometry)
        # Canvas coordinates and text positions are integral in this renderer.
        # Pillow textbbox may contain floats for integral-valued coordinates.
        import math
        box = (math.floor(box[0]), math.floor(box[1]), math.ceil(box[2]), math.ceil(box[3]))
        if box[2] > box[0] and box[3] > box[1]:
            mask = Image.new("L", (box[2] - box[0], box[3] - box[1]), 0)
            ImageDraw.Draw(mask).text((xy[0] - box[0], xy[1] - box[1]), text,
                                     fill=255, stroke_fill=255, **geometry)
            self._check(box, mask)
        return self.draw.text(xy, text, **kwargs)

    def bitmap(self, xy, bitmap, *args, **kwargs):
        # Matrix labels are first drawn onto distinct offscreen masks and then
        # rotated. Their *placed* bitmap positions are the coordinates to audit.
        if any(int(v) != v for v in xy):
            raise ValueError("nonintegral label-bitmap placement")
        x, y = map(int, xy)
        self._check((x, y, x + bitmap.width, y + bitmap.height), bitmap.convert("L"))
        return self.draw.bitmap(xy, bitmap, *args, **kwargs)
