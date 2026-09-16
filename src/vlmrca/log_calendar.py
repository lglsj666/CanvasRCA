"""Remove calendar metadata, not diagnostic numbers, from bounded log displays.

The source graph and its identifiers remain immutable. Matching uses the full
template so numeric previews cannot expose a date beyond the displayed prefix.
This utility does not infer an incident time or manufacture relative timestamps.
"""

from __future__ import annotations

import copy
import re

_NUMBER = r"(?:\{num\d+\}|\d{1,2})"
_YEAR = r"(?:\{num\d+\}|(?:19|20)\d{2})"
_MONTH = r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
_CLOCK = rf"{_NUMBER}:{_NUMBER}(?::{_NUMBER})?(?:\.(?:\{{num\d+\}}|\d+))?(?:Z|[+-]\d{{2}}:?\d{{2}})?"
_DATE = re.compile(
    rf"(?<!\w)(?:(?:(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s+)?{_MONTH}\s+{_NUMBER}\s+{_CLOCK}\s+[A-Z]{{2,5}}\s+{_YEAR}"
    rf"|{_YEAR}[-/]{_NUMBER}[-/]{_NUMBER}(?:[T ]{_CLOCK})?"
    rf"|{_NUMBER}\s+{_MONTH}\s+{_YEAR}(?:\s+{_CLOCK})?"
    rf"|{_MONTH}\s+{_NUMBER},?\s+{_YEAR}(?:\s+{_CLOCK})?"
    rf"|\[y:\s*{_YEAR}\]\[m:\s*{_NUMBER}\]\[d:\s*{_NUMBER}\])(?!\w)",
    re.IGNORECASE,
)
_VARIABLE = re.compile(r"\{num\d+\}")


def calendar_free_log_row(row, full_template):
    """Return a copy only when a visible calendar fragment/variable is present.

    Never refill a preview with previously hidden variables, alter event counts,
    relative bins, numeric precision or template IDs. Source-template checksums
    remain source identifiers, not a claim to hash the abbreviated display text.
    """
    preview_values = {k: str(v.get("first", "")) for k, v in row.get("numeric_preview", {}).items()}
    matches = []
    for match in _DATE.finditer(full_template):
        sample = _VARIABLE.sub(lambda m: preview_values.get(m.group(), "?"), match.group())
        # Do not mistake arbitrary hyphenated numeric/version triples for dates.
        if (re.search(r"\b(?:19|20)\d{2}[-/]", sample)
                or re.search(_MONTH, sample, re.IGNORECASE)
                or match.group().lower().startswith('[y:')
                or re.search(r"[T ]" + _CLOCK, match.group())):
            matches.append(match)
    if not matches:
        return row
    variables = {v for m in matches for v in _VARIABLE.findall(m.group())}
    # A variable referenced outside a calendar span is not metadata-only.
    residual = full_template
    for match in reversed(matches):
        residual = residual[:match.start()] + residual[match.end():]
    variables -= set(_VARIABLE.findall(residual))
    displayed = row["template"]
    marker = re.search(r"\s+… \[sha256=[0-9a-f]+\]$", displayed)
    prefix = displayed[:marker.start()] if marker else displayed
    suffix = displayed[marker.start():] if marker else ""
    if not full_template.startswith(prefix):
        raise ValueError("bounded log projection is not a prefix of its source template")
    for match in reversed(matches):
        if match.start() < len(prefix):
            prefix = prefix[:match.start()] + prefix[min(match.end(), len(prefix)):]
    cleaned = re.sub(r"\s{2,}", " ", prefix).strip() + (" " + suffix.lstrip() if suffix else "")
    preview = {k: v for k, v in row.get("numeric_preview", {}).items() if k not in variables}
    if cleaned == displayed and preview == row.get("numeric_preview", {}):
        return row
    result = copy.deepcopy(row)
    removed_preview = len(row.get("numeric_preview", {})) - len(preview)
    result.update(template=cleaned, numeric_preview=preview,
                  omitted_numeric_variables=max(0, row.get("omitted_numeric_variables", 0)
                                                - (len(variables) - removed_preview)))
    return result
