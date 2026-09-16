"""Generic clock projection with explicit synthetic column identities."""
import pytest
from vlmrca.metric_calendar import relative_clock_gauges


def project(frame, _entities):
    identity={c:tuple(c.split('_',1)) for c in frame if c!='timestamp'}
    return relative_clock_gauges(frame,identity)

def test_clock_metric_projection_preserves_offsets_zero_and_source():
    import pandas as pd
    import numpy as np
    data = pd.DataFrame({"timestamp":[0.,1.,2.],
        "svc_container_last_seen":[1_600_000_010.,1_600_000_011.,np.nan],
        "pod_process_start_time_seconds":[1_600_000_000.,1_600_000_000.,0.],
        "svc_process_start_time_ms":[1_600_000_005_000.]*3,
        "svc_disk_write_time_seconds_total":[1_600_000_001.,2.,3.],
        "svc_bytes_total":[1_600_000_003.,4.,5.]})
    original=data.copy(deep=True)
    converted,audit=project(data,["svc","pod"])
    pd.testing.assert_frame_equal(data,original)
    assert converted["svc_container_last_seen_relative_s"].iloc[:2].tolist()==[11.,12.]
    assert converted["pod_process_start_time_seconds_relative_s"].tolist()==[1.,1.,0.]
    assert converted["svc_process_start_time_ms_relative_s"].tolist()==[6.,6.,6.]
    assert np.isnan(converted["svc_container_last_seen_relative_s"].iloc[2])
    assert audit["converted_columns"]==3 and "origin" not in audit
    pd.testing.assert_frame_equal(converted[["timestamp","svc_bytes_total","svc_disk_write_time_seconds_total"]],
                                  original[["timestamp","svc_bytes_total","svc_disk_write_time_seconds_total"]])


def test_clock_projection_is_calendar_translation_invariant():
    import pandas as pd
    data=pd.DataFrame({"timestamp":[0.,1.,2.],"svc_container_last_seen":[1_600_000_010.,0.,1_600_000_015.],
                       "svc_process_start_time_seconds":[1_600_000_000.]*3})
    shifted=data.copy(deep=True)
    for col in list(shifted)[1:]:
        shifted[col]=shifted[col].where(shifted[col]==0,shifted[col]+987654.)
    first,a=project(data,["svc"]);second,b=project(shifted,["svc"])
    pd.testing.assert_frame_equal(first,second)
    assert a==b


def test_clock_metric_units_and_bad_source_fail_closed():
    import pandas as pd
    import numpy as np
    data=pd.DataFrame({"timestamp":[0.,1.],"svc_boot_time_ns":[1_600_000_000_000_000_000,1_600_000_010_000_000_000],
                       "svc_timestamp_us":[1_600_000_005_000_000,1_600_000_005_000_000]})
    converted,_=project(data,["svc"])
    assert converted["svc_boot_time_ns_relative_s"].tolist()==[1.,11.]
    assert converted["svc_timestamp_us_relative_s"].tolist()==[6.,6.]
    for value in [-1.,42.,1.6e12]:
        with pytest.raises(ValueError,match="clock gauge"):
            project(pd.DataFrame({"svc_last_seen":[value]}),["svc"])
    converted,_=project(pd.DataFrame({"svc_last_seen":[0.,np.nan]}),["svc"])
    assert converted.iloc[0,0]==0 and np.isnan(converted.iloc[1,0])
