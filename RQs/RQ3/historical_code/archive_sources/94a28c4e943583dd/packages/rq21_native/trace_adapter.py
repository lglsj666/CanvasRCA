"""Public-table adapter for the vendored SIRCL operation support/confidence tool.

The original score is a harmonic mean, despite its historical `jaccard` key.
No trace-set mining or complete TraceRCA reproduction is claimed here.
"""
from types import SimpleNamespace
import numpy as np
import pandas as pd
from .sircl_adapted.extractors.tracerca_scorer import score_operations_jaccard


def rank_trace_operations(frame, time_seconds, window):
    if frame is None or frame.empty or window is None:
        return {'rows': [], 'status': 'no_public_trace_window', 'excluded_rows': 0}
    if len(window) != 2 or any(isinstance(x,bool) or not np.isfinite(float(x)) for x in window) or window[1] < window[0]:
        raise ValueError('invalid public trace window')
    if len(frame) != len(time_seconds) or not {'service_name','duration_ms'} <= set(frame):
        raise ValueError('invalid trace table/clock alignment')
    work = frame.copy(deep=True)
    work['_rq21_time_s'] = np.asarray(time_seconds, dtype=float)
    if 'operation_name' not in work: work['operation_name'] = 'default'
    work['operation_name'] = work['operation_name'].fillna('default').astype(str)
    valid = np.isfinite(work['_rq21_time_s']) & (work['_rq21_time_s'] <= window[1]) & work['service_name'].notna()
    excluded = int((~valid).sum()); work = work.loc[valid].copy()
    work['service_name'] = work['service_name'].astype(str)
    pairs = work[['service_name','operation_name']].drop_duplicates()
    binding = {}
    for service, operation in pairs.itertuples(index=False, name=None):
        key = service + '_' + operation
        if key in binding and binding[key] != (service, operation):
            raise ValueError('native compound operation identity collision')
        binding[key] = (service, operation)
    rows = score_operations_jaccard(SimpleNamespace(traces_df=work, analysis_start_s=float(window[0])), structured=True)
    result = []
    for row in rows:
        service, operation = binding[row['operation']]
        result.append({**row, 'service': service, 'operation_name': operation})
    return {'rows':result,'status':'ranked' if result else 'no_native_rank', 'excluded_rows':excluded}
