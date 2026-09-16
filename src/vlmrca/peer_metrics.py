"""Label-free peer-relative metric summaries; no RQ, renderer or scorer imports."""
import math
import re
from collections import defaultdict
from statistics import median


def display_number(value, default=0.):
    """Parse the existing k/M/G display alphabet without guessing other units."""
    try:
        match = re.fullmatch(r'([+-]?[\d.]+(?:[eE][+-]?\d+)?)([kMG]?)', str(value))
        number = float(match[1]) * {'': 1, 'k': 1e3, 'M': 1e6, 'G': 1e9}[match[2]] if match else default
        return number if number is not None and math.isfinite(number) else default
    except (ValueError, TypeError):
        return default


def peer_shift_residuals(rows, min_other_owners=2):
    """Compare bounded own-baseline shifts, leaving the current owner out.

    rows contain key (caller-defined semantic group), owner, before, after,
    spread. Duplicate observations of one owner count once through their median.
    Invalid summaries are unscored, not zero-filled. No healthy-peer assumption
    is asserted by this descriptive operation; residuals are not RCA scores.
    """
    if type(min_other_owners) is not int or min_other_owners < 2:
        raise ValueError('peer comparison requires at least two other owners')
    groups = defaultdict(lambda: defaultdict(list))
    normalized = []
    for row in rows:
        before, after, spread = (display_number(row[k], None) for k in ('before', 'after', 'spread'))
        shift = None
        if None not in (before, after, spread) and spread >= 0:
            magnitude = max(abs(before), abs(after), spread)
            if magnitude == 0:
                shift = 0.
            else:
                a, b, d = before / magnitude, after / magnitude, spread / magnitude
                shift = (b - a) / max(abs(a) + abs(b), 2 * d)
            groups[row['key']][row['owner']].append(shift)
        normalized.append(shift)
    medians = {key: {owner: median(values) for owner, values in owners.items()}
               for key, owners in groups.items()}
    output = []
    for row, shift in zip(rows, normalized):
        peers = [v for owner, v in medians.get(row['key'], {}).items() if owner != row['owner']]
        eligible = shift is not None and len(peers) >= min_other_owners
        center = median(peers) if eligible else None
        output.append({'shift': shift, 'peer_count': len(peers), 'peer_center': center,
                       'residual': abs(shift - center) / 2 if eligible else None})
    return output
