"""Unified, configurable RCA ranking scorer used by the pipeline and all RQs."""

from __future__ import annotations

import argparse
import json
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import ConfigError, FrozenConfig

HitFunction = Callable[[str, str], bool]


@dataclass(frozen=True)
class CaseScore:
    rank: int | None
    mrr: float
    ac_at: Mapping[int, float]
    avg_at: Mapping[int, float]

    def as_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"rank": self.rank, "mrr": self.mrr}
        result.update({f"ac@{k}": v for k, v in self.ac_at.items()})
        result.update({f"avg@{k}": v for k, v in self.avg_at.items()})
        return result


class RCAScorerConfig(FrozenConfig):
    DEFAULT_PATH = "configs/rca_scorer.yaml"
    SCHEMA_VERSION = "CanvasRCAScorerConfigV1"

    def validate(self) -> None:
        if self.data.get("prediction_limit") != 5:
            raise ConfigError("RCA output contract requires ranked top-5 predictions")
        ks = tuple(self.data.get("cutoffs") or ())
        if ks != (1, 3, 5):
            raise ConfigError("canonical RCA cutoffs must be [1, 3, 5]")
        if self.data.get("confidence_intervals_reported") is not False:
            raise ConfigError("CanvasRCA does not report confidence intervals")


class RCAScorer:
    """Base scorer; subclasses may override matching but not metric definitions."""

    def __init__(self, config: RCAScorerConfig, hit: HitFunction | None = None):
        self.config = config
        self.hit = hit or self._default_hit

    @staticmethod
    def _default_hit(predicted: str, accepted: str) -> bool:
        from vlmrca.eval.scoring import is_granularity_aware_hit

        return is_granularity_aware_hit(predicted, accepted)

    def rank(self, predictions: Sequence[str], accepted: Sequence[str]) -> int | None:
        labels = tuple(map(str, accepted))
        for index, prediction in enumerate(map(str, predictions[:5]), start=1):
            if any(self.hit(prediction, label) for label in labels):
                return index
        return None

    def score(self, predictions: Sequence[str], accepted: Sequence[str]) -> CaseScore:
        rank = self.rank(predictions, accepted)
        mrr = 0.0 if rank is None else 1.0 / rank
        cutoffs = tuple(map(int, self.config.data["cutoffs"]))
        ac = {k: float(rank is not None and rank <= k) for k in cutoffs}
        # AVG@K is the mean of cumulative AC@1 ... AC@K.  It is deliberately
        # distinct from both MRR and AC@K and matches the upstream RCA report.
        avg = {
            k: sum(float(rank is not None and rank <= cutoff) for cutoff in range(1, k + 1)) / k
            for k in (3, 5)
        }
        return CaseScore(rank=rank, mrr=mrr, ac_at=ac, avg_at=avg)

    def score_json(self, prediction: Mapping[str, Any], accepted: Sequence[str]) -> dict[str, Any]:
        services = prediction.get("services")
        if not isinstance(services, list):
            raise ConfigError("prediction must contain a services list")
        return self.score([str(value) for value in services], accepted).as_dict()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("prediction", type=Path)
    parser.add_argument("--accepted", nargs="+", required=True)
    parser.add_argument("--config", default=RCAScorerConfig.DEFAULT_PATH)
    args = parser.parse_args(argv)
    scorer = RCAScorer(RCAScorerConfig.load(args.config))
    prediction = json.loads(args.prediction.read_text())
    print(json.dumps(scorer.score_json(prediction, args.accepted), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
