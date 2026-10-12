"""Source-faithful SIRCL Drain frequency component with positional bindings."""
from pathlib import Path
from types import SimpleNamespace
import warnings
import numpy as np
from .sircl_adapted.extractors.log_template_freq import build_torai_template_freq


def rank_log_templates(frame, time_seconds, window):
    if frame is None or frame.empty or window is None:
        return {'rows': [], 'status': 'no_public_log_window', 'excluded_rows': 0}
    if (len(window) != 2 or any(isinstance(x, bool) or not np.isfinite(float(x)) for x in window)
            or window[1] < window[0]):
        raise ValueError('invalid public log window')
    clock = np.asarray(time_seconds, dtype=float)
    if clock.ndim != 1 or len(frame) != len(clock) or not {'container_name', 'message'} <= set(frame):
        raise ValueError('invalid log table/clock alignment')
    if Path('drain3.ini').exists():
        raise ValueError('unregistered cwd Drain configuration')
    work = frame.copy(deep=True)
    work['_source_row'] = np.arange(len(work))
    work['_rq21_time_s'] = clock
    valid = (np.isfinite(work['_rq21_time_s']) & (work['_rq21_time_s'] <= window[1])
             & work['container_name'].notna() & work['message'].notna())
    excluded = int((~valid).sum()); work = work.loc[valid].copy()
    work['container_name'] = work['container_name'].astype(str)
    # The copied parser suppresses warnings. Contain that side effect locally.
    with warnings.catch_warnings():
        rows = build_torai_template_freq(SimpleNamespace(logs_df=work, analysis_start_s=float(window[0])), structured=True)
    seen = set()
    for row in rows:
        indices = row['source_rows']
        if len(indices) != row['count'] or len(set(indices)) != len(indices) or seen.intersection(indices):
            raise ValueError('native log source multiplicity mismatch')
        seen.update(indices)
    return {'rows': rows, 'status': 'ranked' if rows else 'no_native_rank', 'excluded_rows': excluded}
