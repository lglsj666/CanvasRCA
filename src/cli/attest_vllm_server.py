"""Record a lightweight live-server attestation against the global contract."""

from __future__ import annotations

import argparse
import json
import os
import urllib.request
from pathlib import Path

from unified_scripts import PROJECT_ROOT, stable_hash
from unified_scripts.vllm_inference import VLLMInferenceConfig


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model", choices=("qwen3.8-27b", "gemma-4-26b-a4b"))
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    config = VLLMInferenceConfig.load()
    runtime = config.model(args.model)
    api_key = os.environ.get("VLLM_API_KEY", "EMPTY")
    request = urllib.request.Request(
        runtime["base_url"].rstrip("/") + "/models",
        headers={"Authorization": f"Bearer {api_key}"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        models = json.loads(response.read())
    served = {str(item.get("id")) for item in models.get("data", ())}
    payload = {
        "schema_version": "CanvasRCAVLLMAttestationV3",
        "model": args.model,
        "served_model_name": runtime["served_model_name"],
        "models_endpoint_match": runtime["served_model_name"] in served,
        "config": config.audit_record(),
    }
    payload["attestation_sha256"] = stable_hash(payload)
    if not payload["models_endpoint_match"]:
        raise RuntimeError(f"served model mismatch: {sorted(served)}")
    output = args.out or PROJECT_ROOT / f"artifacts/contracts/{args.model}.server.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
