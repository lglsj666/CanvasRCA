"""Small fail-closed utilities for the RQ3.1 identity/window registration."""
from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from unified_scripts import canonical_json, stable_hash

ROOT = Path(__file__).resolve().parents[3]


def sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def exact_write(path: Path, value: Any) -> str:
    """Write once; a resume must reproduce exactly the same bytes."""
    body = json_bytes(value)
    if path.exists():
        if path.read_bytes() != body:
            raise ValueError(f"existing registration differs: {path}")
        return hashlib.sha256(body).hexdigest()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_bytes(body)
    temporary.replace(path)
    return hashlib.sha256(body).hexdigest()


def _skip_json_value(text: str, index: int) -> int:
    """Lexically skip one JSON value without deserializing it."""
    n = len(text)
    if index >= n:
        raise ValueError("truncated JSON value")
    if text[index] == '"':
        index += 1
        escaped = False
        while index < n:
            char = text[index]
            index += 1
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                return index
        raise ValueError("unterminated JSON string")
    if text[index] in "[{":
        stack = ["]" if text[index] == "[" else "}"]
        index += 1
        quoted = escaped = False
        while index < n and stack:
            char = text[index]
            index += 1
            if quoted:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    quoted = False
            elif char == '"':
                quoted = True
            elif char == "[":
                stack.append("]")
            elif char == "{":
                stack.append("}")
            elif char == stack[-1]:
                stack.pop()
        if stack:
            raise ValueError("unterminated JSON collection")
        return index
    while index < n and text[index] not in ",}":
        index += 1
    return index


def read_selected_top_level(path: Path, allowed: Iterable[str]) -> dict[str, Any]:
    """Decode only named top-level values; label values are lexically skipped."""
    allowed = frozenset(allowed)
    decoder = json.JSONDecoder()
    text = path.read_text(encoding="utf-8")
    index = 0

    def whitespace(position: int) -> int:
        while position < len(text) and text[position].isspace():
            position += 1
        return position

    index = whitespace(index)
    if index >= len(text) or text[index] != "{":
        raise ValueError(f"private record is not an object: {path}")
    index += 1
    output: dict[str, Any] = {}
    while True:
        index = whitespace(index)
        if index < len(text) and text[index] == "}":
            index = whitespace(index + 1)
            if index != len(text):
                raise ValueError(f"trailing private JSON content: {path}")
            if set(output) != allowed:
                raise ValueError(f"private record misses allowed fields: {sorted(allowed-set(output))}")
            return output
        key, index = decoder.raw_decode(text, index)
        if not isinstance(key, str):
            raise ValueError("non-string top-level JSON key")
        index = whitespace(index)
        if index >= len(text) or text[index] != ":":
            raise ValueError("malformed private JSON object")
        index = whitespace(index + 1)
        if key in allowed:
            if key in output:
                raise ValueError(f"duplicate allowed private field: {key}")
            output[key], index = decoder.raw_decode(text, index)
        else:
            index = _skip_json_value(text, index)
        index = whitespace(index)
        if index < len(text) and text[index] == ",":
            index += 1
            continue
        if index >= len(text) or text[index] != "}":
            raise ValueError("malformed private JSON delimiter")


def read_selected_object_field(path: Path, field: str, allowed_nested: Iterable[str]) -> dict[str, Any]:
    """Decode allowlisted members of one top-level object and skip all others."""
    allowed_nested = frozenset(allowed_nested)
    decoder = json.JSONDecoder()
    text = path.read_text(encoding="utf-8")

    def whitespace(position: int) -> int:
        while position < len(text) and text[position].isspace():
            position += 1
        return position

    def selected_object(position: int) -> tuple[dict[str, Any], int]:
        position = whitespace(position)
        if position >= len(text) or text[position] != "{":
            raise ValueError(f"selected private field is not an object: {field}")
        position += 1
        output: dict[str, Any] = {}
        while True:
            position = whitespace(position)
            if position < len(text) and text[position] == "}":
                return output, position + 1
            key, position = decoder.raw_decode(text, position)
            position = whitespace(position)
            if position >= len(text) or text[position] != ":":
                raise ValueError("malformed selected private object")
            position = whitespace(position + 1)
            if key in allowed_nested:
                if key in output:
                    raise ValueError(f"duplicate selected private member: {key}")
                output[key], position = decoder.raw_decode(text, position)
            else:
                position = _skip_json_value(text, position)
            position = whitespace(position)
            if position < len(text) and text[position] == ",":
                position += 1
                continue
            if position >= len(text) or text[position] != "}":
                raise ValueError("malformed selected private object delimiter")

    position = whitespace(0)
    if position >= len(text) or text[position] != "{":
        raise ValueError(f"private record is not an object: {path}")
    position += 1
    found = None
    while True:
        position = whitespace(position)
        if position < len(text) and text[position] == "}":
            if found is None:
                raise ValueError(f"private record misses selected object: {field}")
            return found
        key, position = decoder.raw_decode(text, position)
        position = whitespace(position)
        if position >= len(text) or text[position] != ":":
            raise ValueError("malformed private JSON object")
        position = whitespace(position + 1)
        if key == field:
            if found is not None:
                raise ValueError(f"duplicate selected private object: {field}")
            found, position = selected_object(position)
        else:
            position = _skip_json_value(text, position)
        position = whitespace(position)
        if position < len(text) and text[position] == ",":
            position += 1
            continue
        if position >= len(text) or text[position] != "}":
            raise ValueError("malformed private JSON delimiter")


def epoch(value: Any) -> float:
    if isinstance(value, bool):
        raise ValueError("boolean is not a timestamp")
    if isinstance(value, (int, float)):
        result = float(value)
    else:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        result = (parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)).timestamp()
    if not math.isfinite(result):
        raise ValueError("non-finite timestamp")
    return result


def related(left: dict[str, Any], right: dict[str, Any]) -> bool:
    same_event = bool(left.get("event")) and left["event"] == right.get("event")
    overlap = (
        left["source"] == right["source"]
        and max(float(left["start"]), float(right["start"]))
        <= min(float(left["end"]), float(right["end"]))
    )
    return same_event or overlap


def source_hashes(config: dict[str, Any]) -> dict[str, str]:
    references = dict(config["sources"])
    return {name: sha_file(ROOT / spec["path"]) for name, spec in sorted(references.items())}


def verify_source_hashes(config: dict[str, Any]) -> dict[str, str]:
    observed = source_hashes(config)
    expected = {name: spec["sha256"] for name, spec in sorted(config["sources"].items())}
    if observed != expected:
        changed = sorted(name for name in expected if observed.get(name) != expected[name])
        raise ValueError(f"protected data-registration source changed: {changed}")
    return observed


def record_hash(value: Any) -> str:
    return stable_hash(value)


def compact_status(value: Any) -> str:
    return canonical_json(value)
