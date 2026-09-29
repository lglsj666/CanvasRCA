"""Public contracts, exact encodings, small-file persistence and lifecycle."""

import hashlib
import json
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, localcontext
from pathlib import Path

from RQs.RQ3_4.src.utils import digest, read_json, runtime_config
from RQs.RQ3_6.src.utils import call_count, endpoint_vacant, model_probe, stop_owned

__all__ = [
    "call_count",
    "digest",
    "endpoint_vacant",
    "model_probe",
    "read_json",
    "runtime_config",
    "save_json",
    "stop_owned",
]

ROOT = Path(__file__).resolve().parents[3]
CONFIG = ROOT / "RQs/RQ3_7/configs/fusion_v1.json"
VERSION = "rq37_numeric_relation_fusion_v2_pruned"
MODULE = "RQs.RQ3_7.src.main"
PRIMARY = ("aiops2022", "aiops2025", "aegislab")
VISUAL = ("REMOTE_ID", "REMOTE_LINK", "LOCAL_ID", "LOCAL_LINK")
METRICS = ("mrr", "ac@1", "ac@3", "ac@5", "avg@3", "avg@5")
ZERO = dict.fromkeys(METRICS, 0.0)


def save_json(path, obj):
    """Shared progress files need unique atomic temps under concurrent writers."""
    from vlmrca.run_state import atomic_write

    atomic_write(path, (json.dumps(obj, indent=2, ensure_ascii=False,
                                  allow_nan=False) + "\n").encode("utf-8"))


def reference_only(task, config):
    """Read-only historical comparisons must never fall back to generation."""
    return bool(task.get("reference_only")) or task["dimensions"].get("arm") in (
        config.get("experiments", {})
        .get(task["experiment_id"], {})
        .get("reference_only_arms", ())
    )


@dataclass(frozen=True)
class NumericPanelV1:
    entity: str
    observations: tuple


@dataclass(frozen=True)
class FrozenEvidenceViewV1:
    """Only already-public input; no dataset, source path, time origin or label."""

    parts: tuple
    metric_facts: tuple
    panels: tuple
    entities: tuple
    relations: tuple
    ledger: str
    candidates: tuple
    system: str


@dataclass(frozen=True)
class FusionSceneV1:
    width: int
    height: int
    nodes: dict
    local_slots: dict
    remote_slots: dict
    panel_sizes: dict
    reading_lines: dict
    ledger_lines: tuple
    ledger_y: int


@dataclass(frozen=True)
class EquivalentEncodingV1:
    mode: str
    changes: tuple
    applicable: bool


@dataclass(frozen=True)
class InterventionAuditV1:
    fact_hash: str
    panel_hash: str
    geometry_hash: str
    mode: str
    arm: str
    image_hash: str | None
    encoding: dict
    primitives: tuple


class DesignInfeasible(ValueError):
    """Only registered pixel/context bounds, never a catch-all renderer error."""


def decimal(value):
    if isinstance(value, bool):
        raise TypeError("Boolean is not a quantity")
    # Parent _fmt uses decimal (not binary) k/M/G display suffixes. Expand
    # exactly the displayed value; never infer extra precision or physical units.
    text = str(value).strip()
    match = re.fullmatch(r"([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)([kMG])", text)
    try:
        number = Decimal(match[1] if match else text)
    except InvalidOperation as exc:
        raise ValueError("Invalid numeric observation") from exc
    if not number.is_finite():
        raise ValueError("Non-finite observation")
    if match:
        with localcontext() as ctx:
            ctx.prec = max(80, len(number.as_tuple().digits) + 20)
            number = number.scaleb({"k": 3, "M": 6, "G": 9}[match[2]])
    return number


def measurement_definitions(config):
    inherited = read_json(ROOT / config["implementation"]["semantics"])["definitions"]
    overlay = read_json(ROOT / config["implementation"]["semantics_overlay"])
    additions = overlay["definitions"]
    if set(inherited) & set(additions):
        raise ValueError("RQ37 metric definitions cannot override inherited definitions")
    if any(not d.get("source") for d in additions.values()):
        raise ValueError("Every added exact metric definition needs a primary source")
    return inherited | additions


def number(value, mode="NATIVE", exponent=0):
    """Power-of-ten conversion, exact even beyond Decimal's default precision."""
    original = decimal(value)
    with localcontext() as ctx:
        ctx.prec = max(80, len(original.as_tuple().digits) + abs(exponent) + 20)
        converted = original.scaleb(exponent)
        if converted.scaleb(-exponent) != original:
            raise ValueError("Unit conversion is not reversible")
        shown = format(converted, "E" if mode == "SCIENTIFIC" else "f")
        if Decimal(shown) != converted:
            raise ValueError("Display changed numeric value")
        return shown


def exact_json(value, *, spaced=False):
    """JSON numeric literals (not quoted pseudo-numbers), stable key order."""
    if isinstance(value, NumericLiteral):
        return str(value)
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, dict):
        separator, colon = (", ", ": ") if spaced else (",", ":")
        return (
            "{"
            + separator.join(
                json.dumps(k, ensure_ascii=False) + colon + exact_json(v, spaced=spaced)
                for k, v in sorted(value.items())
            )
            + "}"
        )
    if isinstance(value, (list, tuple)):
        return (
            "["
            + (", " if spaced else ",").join(
                exact_json(v, spaced=spaced) for v in value
            )
            + "]"
        )
    return json.dumps(value, ensure_ascii=False, allow_nan=False)


class NumericLiteral(str):
    """Validated JSON number whose lexical spelling must be retained."""

    def __new__(cls, value):
        if not re.fullmatch(r"-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?", str(value)):
            raise ValueError("Not a JSON numeric literal")
        decimal(value)
        return super().__new__(cls, value)


def visible_id(value):
    if not isinstance(value, str) or not re.fullmatch(r"\d{3,5}", value):
        raise ValueError("Expected case-local numeric entity ID")
    return value


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def saved_prompt_path(base, key):
    """Retries preserve attempt files; the commit names the actual saved prompt."""
    commit = read_json(base / "completed" / (key + ".json"))
    paths = [
        base / p
        for p in (commit.get("response_artifact_hashes") or {})
        if p.startswith("prompts/") and p.endswith(".json")
    ]
    if len(paths) != 1:
        raise ValueError("Completion does not name exactly one persisted prompt")
    if not paths[0].resolve().is_relative_to(base.resolve()):
        raise ValueError("Prompt artifact escapes result root")
    return paths[0]


def terminal_flag(root, task):
    """All terminal failures are skipped, not retried. No artifact rebuild."""
    path = root / "flags" / (task["logical_key"] + ".json")
    if not path.exists():
        return None
    flag = read_json(path)
    if flag.get("logical_key") != task["logical_key"] or flag.get("status") not in {
        "done",
        "fail",
    }:
        raise ValueError("Malformed terminal flag")
    return flag


def load_config():
    c = read_json(CONFIG)
    if c["registration_id"] != VERSION or c["budget"]["hard_limit"] != 40000:
        raise ValueError("Unknown protocol or reset budget")
    if (
        c["qualification"]["max_calls"] != 18
        or c["qualification"]["max_seconds"] != 600
    ):
        raise ValueError("Logical smoke bounds changed")
    if c["execution"]["attention"] or c["execution"]["training"]:
        raise ValueError("Attention/training not registered")
    for spec in c["experiments"].values():
        arms = spec["arms"] + spec.get("reference_only_arms", [])
        if len(arms) != len(set(arms)):
            raise ValueError("Duplicate arm")
        if not set(spec["smoke_arms"]) <= set(spec["arms"]):
            raise ValueError("Smoke must qualify active conditions")
    if c["experiments"]["A"]["arms"] != ["T_MATCH", *VISUAL] or set(
        c["experiments"]["A"].get("reference_only_arms", [])
    ) != {"TPV_REF", "B3_G_REF"}:
        raise ValueError(
            "Pruned A must keep five active arms and two read-only references"
        )
    if (
        c["budget"]["planned_new_upper"]
        != sum(spec["calls_upper"] for spec in c["experiments"].values())
        + len(c["experiments"]) * c["qualification"]["max_calls"]
    ):
        raise ValueError("Call-budget arithmetic mismatch")
    return c
