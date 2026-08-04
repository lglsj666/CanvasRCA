"""In-memory and on-disk preparation of paired RCA-VisOps artifacts."""

from __future__ import annotations

import json
import os
import tempfile
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .contracts import ContractError, canonical_json, sha256_bytes
from .evidence import CanonicalEvidenceStore
from .prompts import PromptBundle, audit_paired_views, build_prompt_bundle
from .views import ViewArtifact, compile_text_view, compile_visual_view
from .visops import (
    VisOpsTask,
    build_compositional_visops_tasks,
    build_two_stage_onset_tasks,
    build_two_stage_onset_tasks_v2,
    build_visops_tasks,
)


@dataclass(frozen=True)
class PreparedVisOpsTask:
    task: VisOpsTask
    text_view: ViewArtifact
    visual_view: ViewArtifact
    prompts: PromptBundle
    paired_audit: dict[str, Any]
    visual_sham_view: ViewArtifact | None = None
    sham_prompts: PromptBundle | None = None
    sham_paired_audit: dict[str, Any] | None = None

    @property
    def artifact_id(self) -> str:
        return self.task.query.query_id


def prepare_store(
    store: CanonicalEvidenceStore,
    *,
    private_markers: Iterable[Any] = (),
    task_profile: str = "legacy_visops_v2",
) -> tuple[PreparedVisOpsTask, ...]:
    prepared: list[PreparedVisOpsTask] = []
    builders = {
        "legacy_visops_v2": build_visops_tasks,
        "answer_hidden_compositional_v1": build_compositional_visops_tasks,
        "two_stage_onset_ledger_v1": build_two_stage_onset_tasks,
        "two_stage_onset_ledger_v2": build_two_stage_onset_tasks_v2,
    }
    try:
        tasks = builders[task_profile](store)
    except KeyError as exc:
        raise ContractError(f"unknown VisOps task profile {task_profile!r}") from exc
    for task in tasks:
        text_view = compile_text_view(task)
        visual_view = compile_visual_view(task)
        prompts = build_prompt_bundle(
            task,
            text_view=text_view,
            visual_view=visual_view,
        )
        audit = audit_paired_views(
            task,
            text_view=text_view,
            visual_view=visual_view,
            prompts=prompts,
            private_markers=private_markers,
        )
        visual_sham_view = None
        sham_prompts = None
        sham_audit = None
        if task_profile in {"two_stage_onset_ledger_v1", "two_stage_onset_ledger_v2"}:
            visual_sham_view = compile_visual_view(
                task, row_order_condition="deterministic_sham"
            )
            sham_prompts = build_prompt_bundle(
                task,
                text_view=text_view,
                visual_view=visual_sham_view,
            )
            sham_audit = audit_paired_views(
                task,
                text_view=text_view,
                visual_view=visual_sham_view,
                prompts=sham_prompts,
                private_markers=private_markers,
            )
        prepared.append(
            PreparedVisOpsTask(
                task=task,
                text_view=text_view,
                visual_view=visual_view,
                prompts=prompts,
                paired_audit=audit,
                visual_sham_view=visual_sham_view,
                sham_prompts=sham_prompts,
                sham_paired_audit=sham_audit,
            )
        )
    if not prepared:
        raise ContractError("evidence store did not support any VisOps task")
    return tuple(prepared)


def _atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def write_prepared_artifacts(
    prepared: Iterable[PreparedVisOpsTask],
    *,
    output_dir: Path,
    store: CanonicalEvidenceStore,
    status: str = "qualification_artifacts_not_experiment_results",
) -> dict[str, Any]:
    """Persist qualification artifacts without leaking private answer keys public."""

    output_dir = Path(output_dir)
    if output_dir.exists() and any(output_dir.iterdir()):
        raise ContractError(f"refusing to mix artifacts into non-empty {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, Any]] = []
    private_records: list[dict[str, Any]] = []
    for item in prepared:
        query_id = item.artifact_id
        public_dir = output_dir / "public" / query_id
        private_dir = output_dir / "private" / query_id
        public_files = {
            "task": public_dir / "task.json",
            "text": public_dir / "text_view.txt",
            "visual": public_dir / "visual_view.png",
            "visual_manifest": public_dir / "visual_view.manifest.json",
            "prompt_contract": public_dir / "prompt_contract.json",
            "paired_audit": public_dir / "paired_view_audit.json",
        }
        if item.visual_sham_view is not None:
            if item.sham_prompts is None or item.sham_paired_audit is None:
                raise ContractError("row-sham view lacks prompt or parity audit")
            public_files.update(
                {
                    "visual_sham": public_dir / "visual_view.row_sham.png",
                    "visual_sham_manifest": public_dir
                    / "visual_view.row_sham.manifest.json",
                    "prompt_contract_sham": public_dir
                    / "prompt_contract.row_sham.json",
                    "paired_audit_sham": public_dir / "paired_view_audit.row_sham.json",
                }
            )
        _atomic_write(
            public_files["task"],
            (canonical_json(item.task.public_contract()) + "\n").encode("utf-8"),
        )
        _atomic_write(public_files["text"], item.text_view.artifact_bytes)
        _atomic_write(public_files["visual"], item.visual_view.artifact_bytes)
        _atomic_write(
            public_files["visual_manifest"],
            (canonical_json(item.visual_view.public_metadata()) + "\n").encode("utf-8"),
        )
        _atomic_write(
            public_files["prompt_contract"],
            (canonical_json(item.prompts.public_contract()) + "\n").encode("utf-8"),
        )
        _atomic_write(
            public_files["paired_audit"],
            (canonical_json(item.paired_audit) + "\n").encode("utf-8"),
        )
        if item.visual_sham_view is not None:
            _atomic_write(
                public_files["visual_sham"], item.visual_sham_view.artifact_bytes
            )
            _atomic_write(
                public_files["visual_sham_manifest"],
                (canonical_json(item.visual_sham_view.public_metadata()) + "\n").encode(
                    "utf-8"
                ),
            )
            _atomic_write(
                public_files["prompt_contract_sham"],
                (canonical_json(item.sham_prompts.public_contract()) + "\n").encode(
                    "utf-8"
                ),
            )
            _atomic_write(
                public_files["paired_audit_sham"],
                (canonical_json(item.sham_paired_audit) + "\n").encode("utf-8"),
            )
        answer_path = private_dir / "answer_key.json"
        _atomic_write(
            answer_path,
            (canonical_json(item.task.private_answer_key.private_dict()) + "\n").encode(
                "utf-8"
            ),
        )
        records.append(
            {
                "query_id": query_id,
                "query_hash": item.task.query.query_hash,
                "operation": item.task.query.operation,
                "family": item.task.query.family,
                "fact_inventory_hash": item.task.query.fact_inventory_hash,
                "public_files": {
                    name: str(path.relative_to(output_dir))
                    for name, path in public_files.items()
                },
                "public_hashes": {
                    name: sha256_bytes(path.read_bytes())
                    for name, path in public_files.items()
                },
            }
        )
        private_records.append(
            {
                "query_id": query_id,
                "query_hash": item.task.query.query_hash,
                "answer_key": str(answer_path.relative_to(output_dir)),
                "answer_key_sha256": sha256_bytes(answer_path.read_bytes()),
            }
        )
    if status not in {
        "qualification_artifacts_not_experiment_results",
        "registered_experiment_inputs",
    }:
        raise ContractError(f"unsupported prepared-artifact status {status!r}")
    manifest = {
        "schema_version": "RQ1PreparedVisOpsManifestV1",
        "opaque_incident_id": store.opaque_incident_id,
        "evidence_store": store.public_contract(),
        "task_count": len(records),
        "tasks": records,
        "status": status,
    }
    _atomic_write(
        output_dir / "manifest.json",
        (
            json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
        ).encode("utf-8"),
    )
    _atomic_write(
        output_dir / "private/index.json",
        (
            json.dumps(
                {
                    "schema_version": "RQ1PrivateAnswerIndexV1",
                    "records": private_records,
                },
                ensure_ascii=False,
                sort_keys=True,
                indent=2,
            )
            + "\n"
        ).encode("utf-8"),
    )
    return manifest
