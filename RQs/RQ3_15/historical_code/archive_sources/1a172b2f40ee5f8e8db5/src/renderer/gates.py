"""Small post-render diagnostics; no model/tokenizer imports or server checks."""
from pathlib import Path
import hashlib
import os

from .utils import RENDERER, digest, read


def source_fingerprint():
    files = {}
    for directory, dirs, names in os.walk(RENDERER):
        dirs[:] = sorted(d for d in dirs if d not in {"node_modules", "dist", "assets", "__pycache__"})
        for name in sorted(names):
            path = Path(directory)/name
            if path.suffix in {".py", ".ts", ".tsx", ".json", ".css", ".sh"}:
                files[str(path.relative_to(RENDERER))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return {"files": files, "sha256": digest(files)}


def compare(a, b):
    """Explain actual manipulations; a config field is not a causal guarantee."""
    left, right = read(Path(a)/"manifest.json"), read(Path(b)/"manifest.json")
    if left["status"] != "passed" or right["status"] != "passed":
        raise ValueError("Cannot compare failed renders")
    lrect = {r["card"]: r for r in left["rectangles"]}
    rrect = {r["card"]: r for r in right["rectangles"]}
    return {
        "same_projected_evidence": left["evidence_hash"] == right["evidence_hash"],
        "same_card_inventory": set(lrect) == set(rrect),
        "same_field_bindings": left["expected_bindings"] == right["expected_bindings"],
        "same_source_canvas": (left["width"], left["height"]) == (right["width"], right["height"]),
        "changed_geometry": [c for c in sorted(lrect.keys() & rrect.keys()) if any(lrect[c][k] != rrect[c][k]
                              for k in ("x", "y", "width", "height"))],
        "changed_component": [c for c in sorted(lrect.keys() & rrect.keys()) if lrect[c]["component"] != rrect[c]["component"]],
        "same_pixels": left["png_sha256"] == right["png_sha256"],
        "scope": "These checks cover projected DTO, not missing legacy fields or VLM interpretability",
    }
