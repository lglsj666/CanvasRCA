"""CLI: python -m scorer PREDICTION.json --accepted ENTITY [...]."""
from .core import main
if __name__ == "__main__":
    raise SystemExit(main())
