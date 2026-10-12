"""Thin CLI wrapper; all RQ3-specific execution logic lives in src/main.py."""
import argparse
from pathlib import Path
from RQs.RQ3.src.main import prepare_search_batch, run_search_batch, search_gallery, load_config, SEARCH_CONFIG

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("gallery", "prepare", "run"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--gallery", type=Path)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--config", type=Path, default=SEARCH_CONFIG)
    parser.add_argument("--retry-failed", action="store_true")
    args = parser.parse_args()
    if args.action == "gallery":
        search_gallery(load_config(args.config), args.source, args.output)
    elif args.action == "prepare":
        prepare_search_batch(args.gallery, args.output, args.config)
    else:
        run_search_batch(args.output, retry_failed=args.retry_failed, config_path=args.config)
