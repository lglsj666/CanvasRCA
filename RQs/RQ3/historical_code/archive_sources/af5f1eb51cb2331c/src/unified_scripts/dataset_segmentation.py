"""Unified deterministic dataset segmentation for every CanvasRCA RQ."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import ConfigError, FrozenConfig, canonical_json, project_path, stable_hash


@dataclass(frozen=True)
class CaseRecord:
    dataset: str
    case_id: str
    metadata_path: Path
    strata: tuple[str, ...] = ()


class CaseIndexProvider:
    """Extension point for alternate processed-data layouts."""

    def records(self, processed_root: Path, datasets: Sequence[str]) -> list[CaseRecord]:
        raise NotImplementedError


class ProcessedDirectoryIndex(CaseIndexProvider):
    """Index the sole V3 corpus through its evaluator-private identity manifest."""

    def records(self, processed_root: Path, datasets: Sequence[str]) -> list[CaseRecord]:
        records: list[CaseRecord] = []
        for dataset in datasets:
            manifest = processed_root / "private" / dataset / "manifest.jsonl"
            if not manifest.is_file():
                raise ConfigError(f"V3 processed manifest is missing: {manifest}")
            seen: set[str] = set()
            for line in manifest.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                row = json.loads(line)
                case_id = str(row["case_id"])
                opaque = str(row["opaque_incident_id"])
                if case_id in seen:
                    raise ConfigError(f"duplicate V3 source case ID: {dataset}/{case_id}")
                seen.add(case_id)
                case_dir = processed_root / "public" / dataset / "cases" / opaque
                metadata = case_dir / "metadata.json"
                if not metadata.is_file() or not (case_dir / "_SUCCESS").is_file():
                    raise ConfigError(f"incomplete V3 processed case: {dataset}/{opaque}")
                records.append(CaseRecord(dataset, case_id, metadata))
        return records


@dataclass(frozen=True)
class FrozenManifestAdapter:
    """Hash-locked adapter for an established case manifest plus exclusions."""

    source: Path
    data: Mapping[str, Any]

    SCHEMA_VERSION = "CanvasRCAFrozenManifestAdapterV1"

    @classmethod
    def load(cls, path: str | Path) -> "FrozenManifestAdapter":
        source = project_path(path).resolve()
        payload = json.loads(source.read_text())
        if payload.get("schema_version") != cls.SCHEMA_VERSION:
            raise ConfigError(f"unsupported frozen-manifest adapter: {source}")
        return cls(source=source, data=payload)

    @staticmethod
    def _locked_json(reference: Mapping[str, Any]) -> Mapping[str, Any]:
        path = project_path(reference["path"]).resolve()
        raw = path.read_bytes()
        observed = hashlib.sha256(raw).hexdigest()
        if observed != reference["sha256"]:
            raise ConfigError(f"frozen source hash mismatch: {path}")
        payload = json.loads(raw)
        if not isinstance(payload, Mapping):
            raise ConfigError(f"frozen source is not a mapping: {path}")
        return payload

    def roster(
        self,
        config: "DatasetSegmentationConfig",
        *,
        include_private: bool = False,
    ) -> dict[str, Any]:
        """Materialize the frozen roster without consulting labels or replacing cases."""

        manifest = self._locked_json(self.data["manifest"])
        excluded = frozenset(self.data.get("excluded_case_ids", ()))
        if len(excluded) != int(self.data["expected_excluded"]):
            raise ConfigError("frozen exclusion count does not match the adapter contract")
        source_ids = {
            case_id
            for case_ids in manifest["datasets"].values()
            for case_id in case_ids
        }
        if not excluded <= source_ids:
            raise ConfigError("frozen exclusions contain IDs outside the source manifest")

        datasets: dict[str, list[dict[str, str]]] = {}
        counts: dict[str, int] = {}
        for dataset, case_ids in manifest["datasets"].items():
            values = []
            for case_id in case_ids:
                if case_id in excluded:
                    continue
                record = CaseRecord(dataset, case_id, Path())
                item = {
                    "dataset": dataset,
                    "opaque_incident_id": config.opaque_id(record),
                }
                if include_private:
                    item["case_id"] = case_id
                values.append(item)
            datasets[dataset] = values
            counts[dataset] = len(values)

        expected = {key: int(value) for key, value in self.data["expected_counts"].items()}
        if counts != expected or sum(counts.values()) != int(self.data["expected_total"]):
            raise ConfigError(f"frozen roster count mismatch: observed={counts}, expected={expected}")
        payload = {
            "schema_version": "CanvasRCAFrozenRosterV1",
            "status": "frozen",
            "visibility": "evaluator_private" if include_private else "model_safe_public",
            "seed": int(manifest["seed"]),
            "adapter": {
                "path": str(self.source.relative_to(project_path("."))),
                "sha256": hashlib.sha256(self.source.read_bytes()).hexdigest(),
                "source_manifest_sha256": self.data["manifest"]["sha256"],
                "exclusion_ledger_sha256": self.data["exclusion_ledger_sha256"],
                "no_replacement": True,
            },
            "counts": counts,
            "total": sum(counts.values()),
            "datasets": datasets,
        }
        payload["roster_sha256"] = stable_hash(payload)
        return payload


class DatasetSegmentationConfig(FrozenConfig):
    DEFAULT_PATH = "configs/dataset_segmentation.yaml"
    SCHEMA_VERSION = "CanvasRCADatasetSegmentationConfigV1"

    def validate(self) -> None:
        if int(self.data.get("seed", -1)) < 0:
            raise ConfigError("dataset seed must be non-negative")
        datasets = self.data.get("datasets")
        partitions = self.data.get("partitions")
        if not isinstance(datasets, Mapping) or not isinstance(partitions, Mapping):
            raise ConfigError("dataset segmentation requires datasets and partitions")
        if abs(sum(float(v) for v in partitions.values()) - 1.0) > 1e-9:
            raise ConfigError("partition fractions must sum to 1")

    @property
    def processed_root(self) -> Path:
        configured = os.environ.get("CANVASRCA_PROCESSED_ROOT")
        return project_path(configured or self.data["paths"]["processed"])

    def opaque_id(self, record: CaseRecord) -> str:
        key = f"{self.data['seed']}:{record.dataset}:{record.case_id}"
        return "INC-" + hashlib.sha256(key.encode()).hexdigest()[:12].upper()

    def split(
        self,
        records: Iterable[CaseRecord],
        *,
        strata: Mapping[str, Sequence[str]] | None = None,
        include_private: bool = False,
    ) -> dict[str, list[dict[str, str]]]:
        """Deterministically assign label-blind records within optional strata."""

        groups: dict[tuple[str, ...], list[CaseRecord]] = defaultdict(list)
        for record in records:
            group = (record.dataset, *tuple((strata or {}).get(record.case_id, ())))
            groups[group].append(record)
        output = {name: [] for name in self.data["partitions"]}
        fractions = list(self.data["partitions"].items())
        for group in sorted(groups):
            ordered = sorted(
                groups[group],
                key=lambda item: hashlib.sha256(
                    f"{self.data['seed']}:{item.dataset}:{item.case_id}".encode()
                ).digest(),
            )
            raw = [len(ordered) * float(value) for _, value in fractions]
            counts = [int(value) for value in raw]
            for index in sorted(range(len(raw)), key=lambda i: raw[i] - counts[i], reverse=True)[: len(ordered) - sum(counts)]:
                counts[index] += 1
            cursor = 0
            for (name, _), count in zip(fractions, counts, strict=True):
                for record in ordered[cursor : cursor + count]:
                    item = {"dataset": record.dataset, "opaque_incident_id": self.opaque_id(record)}
                    if include_private:
                        item["case_id"] = record.case_id
                    output[name].append(item)
                cursor += count
        for values in output.values():
            values.sort(key=lambda item: (item["dataset"], item["opaque_incident_id"]))
        return output

    def manifest(
        self,
        provider: CaseIndexProvider | None = None,
        *,
        include_private: bool = False,
    ) -> dict[str, Any]:
        datasets = tuple(self.data["datasets"])
        records = (provider or ProcessedDirectoryIndex()).records(self.processed_root, datasets)
        splits = self.split(records, include_private=include_private)
        payload = {
            "schema_version": "CanvasRCADatasetManifestV1",
            "config": self.audit_record(),
            "visibility": "evaluator_private" if include_private else "model_safe_public",
            "counts": {key: len(value) for key, value in splits.items()},
            "partitions": splits,
        }
        payload["manifest_sha256"] = stable_hash(payload)
        return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=DatasetSegmentationConfig.DEFAULT_PATH)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--private", action="store_true", help="include source case IDs in an evaluator-private manifest")
    parser.add_argument(
        "--frozen-adapter",
        type=Path,
        help="materialize a hash-locked established manifest instead of creating a new split",
    )
    args = parser.parse_args(argv)
    config = DatasetSegmentationConfig.load(args.config)
    payload = (
        FrozenManifestAdapter.load(args.frozen_adapter).roster(config, include_private=args.private)
        if args.frozen_adapter
        else config.manifest(include_private=args.private)
    )
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.out is None:
        print(text, end="")
        return 0
    target = project_path(args.out)
    if args.check:
        return 0 if target.is_file() and target.read_text() == text else 1
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text)
    print(canonical_json({"written": str(target), "sha256": stable_hash(payload)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
