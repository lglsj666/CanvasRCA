"""Pinned, resumable RCA model acquisition; never deletes or searches model trees."""
import argparse
import json
from pathlib import Path

from huggingface_hub import snapshot_download

MODELS = {
    "qwen": ("Qwen/Qwen3.8-27B", "1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0"),
    "gemma": ("google/gemma-4-31B-it", "842da3794eaa0b77d5f08bae87a17459d91ff475"),
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("model", choices=MODELS)
    parser.add_argument("--directory", type=Path, required=True)
    args = parser.parse_args()
    repo, revision = MODELS[args.model]
    print(json.dumps({"status": "starting", "repo": repo, "revision": revision,
                      "directory": str(args.directory)}), flush=True)
    snapshot_download(repo_id=repo, revision=revision, local_dir=args.directory,
                      max_workers=4)
    index = json.loads((args.directory / "model.safetensors.index.json").read_text())
    for name in set(index["weight_map"].values()):
        path = args.directory / name
        if not path.is_file() or path.stat().st_size == 0:
            raise RuntimeError(f"Missing model shard: {name}")
    # Receipt is operational metadata, not a model configuration modification.
    (args.directory / "canvasrca_download_receipt.json").write_text(
        json.dumps({"repo": repo, "revision": revision, "status": "complete"}, indent=2)
    )
    print("DOWNLOAD_COMPLETE", repo, revision, flush=True)


if __name__ == "__main__":
    main()
