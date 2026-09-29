"""Small IO and process lifecycle helpers; no scientific input transformations."""

import json
import os
import signal
import sqlite3
from pathlib import Path

from RQs.RQ3_4.src.utils import digest, read_json, runtime_config, save_json

ROOT = Path(__file__).resolve().parents[3]
CONFIG = ROOT / os.environ.get(
    "CANVASRCA_RQ36_CONFIG", "RQs/RQ3_6/configs/replication_v1.json"
)
VERSION = read_json(CONFIG)["registration_id"]
MODULE = "RQs.RQ3_6.src.main"
__all__ = ["digest", "read_json", "runtime_config", "save_json"]


def load_config():
    config = read_json(CONFIG)
    if config.get("status") == "draft_history_audit_required":
        raise ValueError("Draft under historical-overlap revision; not executable")
    q = config["qualification"]
    if q["max_calls"] != 18 or q["max_seconds"] != 600:
        raise ValueError("Logical smoke capacity changed")
    if config["budget"]["hard_limit"] != 40000:
        raise ValueError("Cumulative major-RQ budget changed")
    expected = (
        10
        if config.get("family") == "scope_competition"
        else 12
        if config.get("family")
        else 14
        if config.get("stage") == "B"
        else 11
    )
    if len(config["arms"]) != expected or len(set(config["arms"])) != expected:
        raise ValueError("Registered unique arm count changed")
    if not set(config["smoke_arms"]) <= set(config["arms"]):
        raise ValueError("Smoke arm not registered")
    return config


def ensure_shared_ledger(config, root):
    """Three experiments, one cumulative budget; never copy a stale counter."""
    name = config["implementation"].get("shared_ledger")
    if not name:
        return
    shared = ROOT / name
    shared.parent.mkdir(parents=True, exist_ok=True)
    target = root / "calls.sqlite"
    if target.is_symlink():
        if target.resolve() != shared.resolve():
            raise ValueError("Unexpected shared budget destination")
    elif target.exists():
        raise ValueError("Refuse to replace an existing private call ledger")
    else:
        target.symlink_to(shared)


def model_probe(spec):
    """Authenticated readiness; False only for transient startup states."""
    import urllib.error
    import urllib.request

    request = urllib.request.Request(
        spec["base_url"].rstrip("/") + "/models",
        headers={"Authorization": "Bearer " + os.environ.get("VLLM_API_KEY", "EMPTY")},
    )
    try:
        with urllib.request.urlopen(request, timeout=3) as response:
            names = [row["id"] for row in json.load(response)["data"]]
    except urllib.error.HTTPError as exc:
        if exc.code == 503:
            return False
        raise RuntimeError(
            f"Model readiness HTTP {exc.code}; authentication/configuration failure"
        ) from None
    except urllib.error.URLError as exc:
        if isinstance(exc.reason, ConnectionRefusedError):
            return False
        raise RuntimeError("Model readiness connection failed") from exc
    if names != [spec["served_model_name"]]:
        raise RuntimeError("Unexpected served model identity")
    return True


def endpoint_vacant(spec):
    """Only TCP refusal establishes vacancy, never an HTTP authentication error."""
    import socket
    from urllib.parse import urlparse

    url = urlparse(spec["base_url"])
    try:
        with socket.create_connection((url.hostname, url.port or 80), timeout=2):
            pass
    except ConnectionRefusedError:
        return True
    return False


def terminal_flag(root, task):
    """Only tiny flags on resume, before loading context or tokenizers."""
    path = root / "flags" / (task["logical_key"] + ".json")
    if not path.exists():
        return None
    flag = read_json(path)
    if flag.get("logical_key") != task["logical_key"]:
        raise ValueError("Wrong terminal flag identity")
    if flag["status"] not in {"done", "fail"}:
        raise ValueError("Unknown terminal status")
    if flag["status"] == "fail" and flag.get("failure_class") != "request_timeout":
        raise ValueError("Infrastructure failure needs diagnosis; no automatic retry")
    return flag


def stop_owned(process):
    """Kill only a session we created, including children of an exited leader."""
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    process.wait(timeout=5)


def call_count(root, scope=None):
    path = root / "calls.sqlite"
    if not path.exists():
        return 0
    with sqlite3.connect(f"file:{path}?mode=ro", uri=True) as db:
        if scope is None:
            return db.execute("SELECT count(*) FROM calls").fetchone()[0]
        prefix = scope + "/"
        return db.execute(
            "SELECT count(*) FROM calls WHERE substr(call_key,1,?)=?",
            (len(prefix), prefix),
        ).fetchone()[0]


def interrupted_calls(root, scope):
    """Keep attempts counted; allow only uncommitted work to be resumed."""
    from vlmrca.run_state import DurableCallRegister

    ledger = DurableCallRegister(root / "calls.sqlite", limit=40000, scope=scope)
    prefix = scope + "/"
    with ledger.connect() as db:
        db.execute(
            "UPDATE calls SET state='interrupted',result=? WHERE state='started' AND substr(call_key,1,?)=?",
            (
                json.dumps({"reason": "previous owner exited without commit"}),
                len(prefix),
                prefix,
            ),
        )
