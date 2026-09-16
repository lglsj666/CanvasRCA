"""Shared native May processor/cache/power-loss regression; no model calls."""
import pytest

@pytest.fixture
def may_source(tmp_path, monkeypatch):
    """Small raw-shaped CPU fixture, never an inference/smoke substitute."""
    import json
    import pandas as pd
    from unified_scripts.raw_data_processor import AIOPS2022MayDataset
    monkeypatch.delenv("EDA_CACHE_DIR", raising=False)
    monkeypatch.delenv("SCRATCH", raising=False)
    root = tmp_path / "raw"
    bed = root / "2022-05-01" / "cloudbed"
    stamp = 1651363200
    times = [stamp-1201, stamp-1200, stamp, stamp+1200, stamp+1201]
    (root / "groundtruth").mkdir(parents=True)
    (root / "groundtruth" / "groundtruth-2022-05-01.json").write_text(json.dumps({
        "timestamp": [stamp], "level": ["pod"], "cmdb_id": ["cartservice-0"],
        "failure_type": ["cpu"]}))
    tall = pd.DataFrame({"timestamp": times, "cmdb_id": ["node-1.cartservice-0"]*5,
                        "kpi_name": ["cpu"]*5, "value": [0., 1.25, 3.5, 2., 0.]})
    service = pd.DataFrame({"timestamp": times, "service": ["cartservice"]*5,
                           "rr": [1.]*5, "sr": [1.]*5, "mrt": [2.]*5, "count": [3]*5})
    logs = pd.DataFrame({"timestamp": times, "cmdb_id": ["cartservice-0"]*5,
                        "value": ["outside", "status 200", "error status 500", None, "outside"]})
    traces = pd.DataFrame({"timestamp": [t*1000 for t in times],
        "cmdb_id": ["cartservice-0"]*5, "span_id": [f"s{i}" for i in range(5)],
        "trace_id": ["tr1"]*5, "parent_span": [None, "s0", "s1", "s2", "s3"],
        "duration": [1.25]*5, "status_code": [200,200,500,200,200],
        "operation_name": ["/cart/get"]*5, "type": ["server"]*5,
        "process_metadata": ["retain-me"]*5})
    frames = {"metric/container/kpi.csv": tall, "metric/service/metric_service.csv": service,
        "log/all/log_filebeat-testbed-log-service.csv": logs,
        "trace/all/trace.csv": traces}
    for relative, frame in frames.items():
        path = bed / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        frame.to_csv(path, index=False)
    loader = AIOPS2022MayDataset(str(root))
    return root, loader, loader._build_index()[0]


def test_may_native_window_cache_and_v3_roundtrip(may_source, tmp_path):
    from unified_scripts import raw_data_processor as raw
    root, loader, entry = may_source
    raw.verify_vendored_sources()
    expected = loader.load_case(entry)
    observed = raw.load_may_window(loader, entry, tmp_path / "cache")
    assert raw.canonical_case_bytes(observed) == raw.canonical_case_bytes(expected)
    assert len(observed.traces_df) == 3 and "process_metadata" in observed.traces_df
    assert observed.metadata["node_pod_map"] == {"node-1": ["cartservice-0"]}
    assert observed.metadata["cloudbed"] == "2022-05-01-cloudbed-may"
    assert raw.canonical_case_bytes(raw.load_may_window(loader, entry, tmp_path / "cache")) == raw.canonical_case_bytes(expected)
    record = raw._process_case(observed, "aiops2022", tmp_path / "out")
    public = tmp_path / "out/public/aiops2022" / record["path"]
    assert raw.canonical_case_bytes(raw._read_public_case(entry["case_id"], "aiops2022", public)) == raw.canonical_case_bytes(raw._public_projection(observed))
    assert root != public


def test_may_epoch_predicates_keep_integer_precision(tmp_path):
    import pandas as pd
    from unified_scripts.raw_data_processor import _WindowCSVReader
    root = tmp_path / "raw"
    source = root / "metric/timestamp.csv"
    source.parent.mkdir(parents=True)
    frame = pd.DataFrame({"timestamp":[1651334400,1651334401,1651334402], "value":[1,2,3]})
    frame.to_csv(source,index=False)
    for lower, upper, expected in [(1651334400.,1651334402.,[1,2,3]),
                                    (1651334400.1,1651334401.9,[2])]:
        reader = _WindowCSVReader(root,tmp_path / "cache",lower,upper)
        observed = reader.read_csv(source,low_memory=False)
        assert observed["value"].tolist() == expected
        assert str(observed["timestamp"].dtype) == "int64"


@pytest.mark.parametrize("failure_point", ["private_publish", "public_publish"])
def test_may_power_loss_recovers_verified_staging(may_source, tmp_path, monkeypatch, failure_point):
    from unified_scripts import raw_data_processor as raw
    _, loader, entry = may_source
    case = loader.load_case(entry)
    output = tmp_path / "out"
    opaque = raw._opaque(entry["case_id"], "aiops2022")
    target = output / (f"private/aiops2022/cases/{opaque}.json" if failure_point == "private_publish" else f"public/aiops2022/cases/{opaque}")
    original = raw.os.replace
    def interrupted(source, dest):
        if dest == target:
            raise OSError("simulated power interruption at publication")
        return original(source, dest)
    with monkeypatch.context() as patch:
        patch.setattr(raw.os, "replace", interrupted)
        with pytest.raises(OSError, match="power interruption"):
            raw._process_case(case, "aiops2022", output)
    label = raw._recover_may_commit(entry["case_id"], output)
    assert label["sircl_datacase_sha256"] == raw.canonical_case_sha256(case)
    assert raw._existing_processed_record(entry["case_id"], "aiops2022", output)
    public = output / f"public/aiops2022/cases/{opaque}"
    (public / "graph.json").write_text('{"nodes":[],"edges":[]}')
    with pytest.raises(ValueError, match="checksum mismatch"):
        raw._recover_may_commit(entry["case_id"], output)


def test_may_invalid_labels_and_cache_failure_are_not_missing(may_source, tmp_path):
    import json
    from unified_scripts import raw_data_processor as raw
    root, loader, entry = may_source
    raw.load_may_window(loader, entry, tmp_path / "cache")
    target = sorted((tmp_path / "cache").glob("*.parquet"))[0]
    target.write_bytes(b"broken source cache")
    with pytest.raises(RuntimeError, match="source-read failures"):
        raw.load_may_window(loader, entry, tmp_path / "cache")
    labels = root / "groundtruth/groundtruth-2022-05-01.json"
    payload = json.loads(labels.read_text())
    payload["cmdb_id"] = [None]
    labels.write_text(json.dumps(payload))
    with pytest.raises(ValueError, match="empty"):
        raw.AIOPS2022MayDataset(str(root))._build_index()


def test_may_append_preserves_old_corpus_and_reuses(may_source, tmp_path, monkeypatch):
    import json
    from concurrent.futures import Future
    from unified_scripts import raw_data_processor as raw
    root, _, entry = may_source
    class InlinePool:
        def __init__(self, **kwargs):
            pass
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
        def submit(self, function, *args):
            future = Future()
            try:
                future.set_result(function(*args))
            except Exception as exc:
                future.set_exception(exc)
            return future
    import concurrent.futures
    monkeypatch.setattr(concurrent.futures, "ProcessPoolExecutor", InlinePool)
    monkeypatch.setattr(raw.os, "sched_setaffinity", lambda *args: None)
    output = tmp_path / "out"
    manifest = output / "private/aiops2022/manifest.jsonl"
    manifest.parent.mkdir(parents=True)
    old = b'{"case_id":"preserved-prior-case","opaque_incident_id":"INC-PRIOR","path":"cases/INC-PRIOR"}\n'
    manifest.write_bytes(old)
    result = raw.process_may_dataset(root, output, tmp_path / "cache", workers=1)
    assert result["added_cases"] == 1 and result["total_manifest_cases"] == 2
    complete = manifest.read_bytes()
    assert complete.startswith(old)
    assert (manifest.parent / "manifest_before_may_extension.jsonl").read_bytes() == old
    monkeypatch.setattr(raw, "load_may_window", lambda *a: pytest.fail("completed case reprocessed"))
    assert raw.process_may_dataset(root, output, tmp_path / "cache", workers=1)["added_cases"] == 0
    assert manifest.read_bytes() == complete
    audit = json.loads(next((manifest.parent / "may_audit").glob("*.json")).read_text())
    assert audit["native_csv_byte_parity"] and audit["case_id"] == entry["case_id"]
