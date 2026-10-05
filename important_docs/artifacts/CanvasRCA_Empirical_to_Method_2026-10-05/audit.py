"""Read-only historical aggregation; writes only this proposal's derived files."""
import csv
import hashlib
import json
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
SOURCE = ROOT / "RQs/RQ3_16/results/marginal_coverage_v1/analysis_detailed_v1/case_metrics.csv"


def main():
    with SOURCE.open() as handle:
        rows = list(csv.DictReader(handle))
    keyed = {(r["case"], r["arm"]): r for r in rows}
    assert len(keyed) == len(rows), "Duplicate logical score positions"
    comparisons = []
    for baseline in ("PAIR_FIVE", "BASE_FLEX"):
        for dataset in ("all", "aiops2022", "aiops2025", "aegislab"):
            pairs = []
            for (case, arm), right in keyed.items():
                if arm != "MARGINAL_FIVE":
                    continue
                if dataset != "all" and right["dataset"] != dataset:
                    continue
                left = keyed.get((case, baseline))
                fields = ("mrr", "input_tokens", "output_tokens", "total_tokens")
                if left and all(r.get(k) not in (None, "") for r in (left, right) for k in fields):
                    pairs.append((left, right))
            assert pairs, (baseline, dataset)
            for pair in pairs:
                for r in pair:
                    assert int(r["input_tokens"]) + int(r["output_tokens"]) == int(r["total_tokens"])
            item = {"baseline": baseline, "method": "MARGINAL_FIVE", "dataset": dataset, "paired_n": len(pairs)}
            for side, index in (("baseline", 0), ("method", 1)):
                for field in fields:
                    item[f"{side}_{field}"] = mean(float(p[index][field]) for p in pairs)
            item["delta_mrr"] = mean(float(r["mrr"]) - float(l["mrr"]) for l, r in pairs)
            item["total_token_ratio"] = item["method_total_tokens"] / item["baseline_total_tokens"]
            comparisons.append(item)
    report = {
        "source": str(SOURCE.relative_to(ROOT)),
        "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "scope": "Historical complete paired logical positions; no new model calls; no revised significance/adoption claim",
        "comparisons": comparisons,
    }
    (OUT / "cost_audit.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(comparisons, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
