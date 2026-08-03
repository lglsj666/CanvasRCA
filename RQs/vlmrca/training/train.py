"""Unified unquantized BF16 LoRA entry point for CanvasRCA causal SFT.

Run through the project training environment:

    venvs/train/bin/python -m vlmrca.training.train \
        --config RQs/RQ0/configs/training/causal_integration_sft_v1.yaml --mode smoke
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import importlib.util
import json
import math
import os
import queue
import random
import subprocess
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import torch
import yaml
from PIL import Image
from peft import LoraConfig, get_peft_model
from torch.optim import AdamW
from torch.optim.lr_scheduler import LambdaLR
from transformers import AutoModelForImageTextToText, AutoProcessor

from vlmrca.config_paths import resolve_project_path
from vlmrca.training.causal_sft import canonical_json, sha256_json

ROOT = Path(__file__).resolve().parents[3]
LANGUAGE_LINEAR_SUFFIXES = {
    "q_proj",
    "k_proj",
    "v_proj",
    "o_proj",
    "in_proj_qkv",
    "in_proj_z",
    "in_proj_b",
    "in_proj_a",
    "out_proj",
    "gate_proj",
    "up_proj",
    "down_proj",
}


def _sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha_file(path: Path) -> str:
    return _sha_bytes(path.read_bytes())


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, default=str) + "\n")


def _git(args: List[str]) -> str:
    completed = subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, text=True, check=False
    )
    return completed.stdout.strip()


class AsyncArtifactWriter:
    """Single ordered writer; training never waits on each small artifact write."""

    def __init__(self) -> None:
        self._queue: queue.Queue[Any] = queue.Queue()
        self._error: Optional[BaseException] = None
        self._thread = threading.Thread(target=self._run, name="sft-artifact-writer", daemon=True)
        self._thread.start()

    def _run(self) -> None:
        try:
            while True:
                item = self._queue.get()
                try:
                    if item is None:
                        return
                    operation, path, payload = item
                    path.parent.mkdir(parents=True, exist_ok=True)
                    if operation == "append":
                        with path.open("a", encoding="utf-8") as handle:
                            handle.write(payload)
                    elif operation == "text":
                        path.write_text(payload, encoding="utf-8")
                    else:
                        raise ValueError(operation)
                finally:
                    self._queue.task_done()
        except BaseException as exc:  # noqa: BLE001
            self._error = exc

    def append_jsonl(self, path: Path, value: Dict[str, Any]) -> None:
        self._queue.put(("append", path, json.dumps(value, ensure_ascii=False, default=str) + "\n"))

    def append_text(self, path: Path, value: str) -> None:
        self._queue.put(("append", path, value))

    def write_text(self, path: Path, value: str) -> None:
        self._queue.put(("text", path, value))

    def drain(self) -> None:
        self._queue.join()
        if self._error is not None:
            raise RuntimeError("asynchronous artifact writer failed") from self._error

    def close(self) -> None:
        self.drain()
        self._queue.put(None)
        self._thread.join()
        if self._error is not None:
            raise RuntimeError("asynchronous artifact writer failed") from self._error


class PhysicalGPUMonitor:
    """Sample device-resident memory separately from CUDA allocator bookkeeping."""

    def __init__(self, interval_s: float = 0.5) -> None:
        self.interval_s = interval_s
        self.samples: List[Dict[str, float]] = []
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        def sample() -> None:
            while not self._stop.is_set():
                try:
                    completed = subprocess.run(
                        [
                            "nvidia-smi",
                            "--query-gpu=memory.used,utilization.gpu",
                            "--format=csv,noheader,nounits",
                        ],
                        capture_output=True,
                        text=True,
                        timeout=3,
                        check=False,
                    )
                    memory, utilization = completed.stdout.strip().splitlines()[0].split(",")[:2]
                    self.samples.append(
                        {
                            "time": time.time(),
                            "memory_used_mib": float(memory),
                            "utilization_pct": float(utilization),
                        }
                    )
                except Exception:
                    pass
                self._stop.wait(self.interval_s)

        self._thread = threading.Thread(target=sample, name="sft-gpu-monitor", daemon=True)
        self._thread.start()

    def stop(self) -> Dict[str, Any]:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=5)
        return self.summary()

    def summary(self) -> Dict[str, Any]:
        return {
            "peak_gpu_physical_used_mib_sampled": max(
                (sample["memory_used_mib"] for sample in self.samples), default=None
            ),
            "gpu_physical_samples": len(self.samples),
            "gpu_physical_sampling_interval_s": self.interval_s,
            "physical_measurement_includes_display_processes": True,
        }


@dataclass
class EncodedExample:
    record: Dict[str, Any]
    prompt_tokens: int
    total_tokens: int
    target_tokens: int


class MultimodalExampleEncoder:
    def __init__(self, model_path: Path, max_sequence_length: int) -> None:
        self.processor = AutoProcessor.from_pretrained(
            model_path, local_files_only=True, trust_remote_code=True
        )
        self.max_sequence_length = max_sequence_length

    @staticmethod
    def _messages(system: str, user: str, image_path: Path) -> List[Dict[str, Any]]:
        return [
            {"role": "system", "content": [{"type": "text", "text": system}]},
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": str(image_path)},
                    {"type": "text", "text": user},
                ],
            },
        ]

    def encode(self, record: Dict[str, Any], tensors: bool = True) -> EncodedExample | Dict[str, Any]:
        input_path = ROOT / record["files"]["input"]
        image_path = ROOT / record["files"]["image"]
        supervision_path = ROOT / record["files"]["supervision"]
        model_input = json.loads(input_path.read_text())
        supervision = json.loads(supervision_path.read_text())
        target = supervision.get("target_text")
        if not supervision.get("eligible") or not target:
            raise RuntimeError(f"selected example is not eligible: {record['opaque_incident_id']}")
        base = self._messages(model_input["system"], model_input["user_text"], image_path)
        full = base + [
            {"role": "assistant", "content": [{"type": "text", "text": target}]}
        ]
        prompt_text = self.processor.apply_chat_template(
            base, tokenize=False, add_generation_prompt=True, enable_thinking=False
        )
        full_text = self.processor.apply_chat_template(
            full, tokenize=False, add_generation_prompt=False, enable_thinking=False
        )
        with Image.open(image_path) as source:
            image = source.convert("RGB")
            prompt = self.processor(
                text=[prompt_text], images=[image], return_tensors="pt"
            )
            encoded = self.processor(text=[full_text], images=[image], return_tensors="pt")
        prompt_tokens = int(prompt["input_ids"].shape[1])
        total_tokens = int(encoded["input_ids"].shape[1])
        if total_tokens > self.max_sequence_length:
            raise RuntimeError(
                f"{record['opaque_incident_id']} has {total_tokens} tokens, exceeds "
                f"frozen max_sequence_length={self.max_sequence_length}"
            )
        if not torch.equal(
            encoded["input_ids"][0, :prompt_tokens], prompt["input_ids"][0]
        ):
            raise RuntimeError(
                f"assistant-mask prefix mismatch for {record['opaque_incident_id']}"
            )
        target_tokens = total_tokens - prompt_tokens
        if target_tokens <= 0:
            raise RuntimeError(f"empty assistant target for {record['opaque_incident_id']}")
        if not tensors:
            return EncodedExample(record, prompt_tokens, total_tokens, target_tokens)
        labels = encoded["input_ids"].clone()
        labels[:, :prompt_tokens] = -100
        return {
            **dict(encoded),
            "labels": labels,
            "prompt_tokens": prompt_tokens,
            "total_tokens": total_tokens,
            "target_tokens": target_tokens,
            "target_text": target,
        }


def _verify_selected_files(records: Iterable[Dict[str, Any]]) -> None:
    for record in records:
        for name, relative in record["files"].items():
            path = ROOT / relative
            if not path.is_file():
                raise RuntimeError(f"missing frozen {name}: {path}")
            if _sha_file(path) != record["file_sha256"][name]:
                raise RuntimeError(f"frozen artifact drift: {path}")


def _model_lock(config: Dict[str, Any]) -> Dict[str, Any]:
    lock_path = resolve_project_path(ROOT, config["model"]["checkpoint_lock"])
    lock = json.loads(lock_path.read_text())["models"]["qwen3.6-27b"]
    model_path = ROOT / config["model"]["path"]
    if _sha_file(model_path / "config.json") != lock["config_sha256"]:
        raise RuntimeError("Qwen config drifted from checkpoint lock")
    if _sha_file(model_path / "model.safetensors.index.json") != lock["index_sha256"]:
        raise RuntimeError("Qwen weight index drifted from checkpoint lock")
    if config["model"].get("quantization") is not None:
        raise RuntimeError("training quantization is prohibited")
    return lock


def _run_contract(
    config_path: Path,
    config: Dict[str, Any],
    roster_path: Path,
    roster: Dict[str, Any],
    records: List[Dict[str, Any]],
    mode: str,
    token_inventory: List[EncodedExample],
) -> Dict[str, Any]:
    lock = _model_lock(config)
    git_diff = subprocess.run(
        ["git", "diff", "--binary", "--", "."], cwd=ROOT, capture_output=True, check=False
    ).stdout
    packages = {}
    for package in (
        "torch",
        "transformers",
        "peft",
        "accelerate",
        "flash_attn",
        "flash-linear-attention",
    ):
        try:
            packages[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            packages[package] = None
    return {
        "schema_version": "CausalIntegrationSFTOptimizerContractV1",
        "created_before_optimizer_step": True,
        "mode": mode,
        "config_path": str(config_path.relative_to(ROOT)),
        "config_sha256": _sha_file(config_path),
        "roster_path": str(roster_path.relative_to(ROOT)),
        "roster_file_sha256": _sha_file(roster_path),
        "roster_declared_sha256": roster["roster_sha256"],
        "source_partition": roster["source_partition"],
        "split_assignment_sha256": roster["split_assignment_sha256"],
        "selected_records_sha256": sha256_json(records),
        "selected_cases": [
            {
                "dataset": row["dataset"],
                "opaque_incident_id": row["opaque_incident_id"],
                "private_case_id_sha256": _sha_bytes(row["private_case_id"].encode()),
                "stage_partition": row["stage_partition"],
                "ceb_hash": row["ceb_hash"],
                "fact_inventory_hash": row["fact_inventory_hash"],
                "input_sha256": row["input_sha256"],
                "target_sha256": row["target_sha256"],
            }
            for row in records
        ],
        "token_inventory": [
            {
                "opaque_incident_id": item.record["opaque_incident_id"],
                "prompt_tokens": item.prompt_tokens,
                "target_tokens": item.target_tokens,
                "total_tokens": item.total_tokens,
            }
            for item in token_inventory
        ],
        "model_lock": lock,
        "canvasrca_git_head": _git(["rev-parse", "HEAD"]),
        "working_tree_diff_sha256": _sha_bytes(git_diff),
        "implementation_files": {
            str(path.relative_to(ROOT)): _sha_file(path)
            for path in (
                ROOT / "RQs/vlmrca/training/train.py",
                ROOT / "RQs/vlmrca/training/causal_sft.py",
                ROOT / "RQs/vlmrca/rq0/evidence.py",
            )
        },
        "environment": {
            "python": os.sys.version,
            "packages": packages,
            "torch_cuda": torch.version.cuda,
            "gpu": torch.cuda.get_device_name(0),
            "gpu_total_memory_bytes": torch.cuda.get_device_properties(0).total_memory,
            "flash_linear_attention_available": bool(importlib.util.find_spec("fla")),
            "causal_conv1d_available": bool(importlib.util.find_spec("causal_conv1d")),
            "process_co_residency": "no_project_vllm_server; display_processes_only",
        },
        "effective_training_config": {
            "dtype": config["model"]["dtype"],
            "quantization": config["model"]["quantization"],
            "attention_implementation": config["model"]["attention_implementation"],
            "gdn_backend": config["model"]["gdn_backend"],
            "causal_conv1d_backend": config["model"]["causal_conv1d_backend"],
            "max_sequence_length": config["training"]["max_sequence_length"],
            "lora": config["lora"],
            "training": config["training"],
            "mode_overrides": config[mode],
        },
    }


def _target_modules(model: torch.nn.Module) -> List[str]:
    modules = [
        name
        for name, module in model.named_modules()
        if name.startswith("model.language_model.layers.")
        and name.rsplit(".", 1)[-1] in LANGUAGE_LINEAR_SUFFIXES
        and isinstance(module, torch.nn.Linear)
    ]
    if len(modules) != 496:
        raise RuntimeError(f"expected 496 Qwen language linear modules, found {len(modules)}")
    return modules


def _save_checkpoint(
    model: torch.nn.Module,
    processor: Any,
    optimizer: torch.optim.Optimizer,
    scheduler: LambdaLR,
    checkpoint_root: Path,
    step: int,
    state: Dict[str, Any],
) -> Path:
    path = checkpoint_root / f"step-{step:04d}"
    path.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(path, safe_serialization=True)
    processor.save_pretrained(path)
    torch.save(
        {
            "optimizer": optimizer.state_dict(),
            "scheduler": scheduler.state_dict(),
            "step": step,
            "state": state,
            "torch_rng_state": torch.get_rng_state(),
            "cuda_rng_state": torch.cuda.get_rng_state(),
        },
        path / "trainer_state.pt",
    )
    _write_json(path / "checkpoint_manifest.json", state)
    return path


def _move_batch(batch: Dict[str, Any], device: torch.device) -> Dict[str, Any]:
    return {
        key: value.to(device, non_blocking=True)
        for key, value in batch.items()
        if isinstance(value, torch.Tensor)
    }


def run(config_path: Path, mode: str, run_name: Optional[str]) -> Dict[str, Any]:
    config_path = config_path.resolve()
    config = yaml.safe_load(config_path.read_text())
    roster_path = resolve_project_path(ROOT, config["derived_roster"]).resolve()
    roster = json.loads(roster_path.read_text())
    selection_name = "smoke_train" if mode == "smoke" else "pilot_train"
    records = list(roster["selections"][selection_name])
    if mode == "smoke":
        expected = set(config["smoke_datasets"])
        observed = {row["dataset"] for row in records}
        if len(records) != 3 or observed != expected:
            raise RuntimeError(f"training smoke must contain exactly {sorted(expected)}")
        if any(row["stage_partition"] != "train" for row in records):
            raise RuntimeError("training smoke selected a non-train case")
    _verify_selected_files(records)

    model_path = ROOT / config["model"]["path"]
    encoder = MultimodalExampleEncoder(
        model_path, int(config["training"]["max_sequence_length"])
    )
    token_inventory = [encoder.encode(record, tensors=False) for record in records]
    assert all(isinstance(item, EncodedExample) for item in token_inventory)

    stamp = run_name or time.strftime("%Y%m%dT%H%M%S")
    result_root = ROOT / config[mode]["result_root"] / stamp
    checkpoint_root = ROOT / config[mode]["checkpoint_root"] / stamp
    result_root.mkdir(parents=True, exist_ok=False)
    contract = _run_contract(
        config_path,
        config,
        roster_path,
        roster,
        records,
        mode,
        token_inventory,  # type: ignore[arg-type]
    )
    _write_json(result_root / "run_contract.json", contract)

    detailed_path = result_root / "logs/detailed.jsonl"
    brief_path = result_root / "logs/brief.log"
    trajectory_path = result_root / "trajectories/episodes.jsonl"
    writer = AsyncArtifactWriter()
    writer.append_jsonl(
        trajectory_path,
        {
            "record_type": "header",
            "experiment": config["experiment"],
            "mode": mode,
            "contract_sha256": _sha_file(result_root / "run_contract.json"),
        },
    )
    writer.append_text(
        brief_path,
        f"Causal-integration SFT {mode}: {len(records)} frozen train cases\n",
    )
    started = time.time()
    torch.manual_seed(int(config["training"]["seed"]))
    torch.cuda.manual_seed_all(int(config["training"]["seed"]))
    random.seed(int(config["training"]["seed"]))
    torch.backends.cuda.matmul.allow_tf32 = True
    torch.cuda.reset_peak_memory_stats()
    physical_gpu = PhysicalGPUMonitor(interval_s=0.5)
    physical_gpu.start()

    writer.append_jsonl(detailed_path, {"event": "model_load_start", "time": time.time()})
    model = AutoModelForImageTextToText.from_pretrained(
        model_path,
        local_files_only=True,
        trust_remote_code=True,
        dtype=torch.bfloat16,
        attn_implementation=config["model"]["attention_implementation"],
        low_cpu_mem_usage=True,
        device_map={"": 0},
    )
    model.config.use_cache = False
    if config["training"]["gradient_checkpointing"]:
        model.gradient_checkpointing_enable(
            gradient_checkpointing_kwargs={"use_reentrant": False}
        )
        model.enable_input_require_grads()
    targets = _target_modules(model)
    lora = config["lora"]
    model = get_peft_model(
        model,
        LoraConfig(
            r=int(lora["rank"]),
            lora_alpha=int(lora["alpha"]),
            lora_dropout=float(lora["dropout"]),
            bias=str(lora["bias"]),
            target_modules=targets,
            task_type="CAUSAL_LM",
        ),
    )
    model.train()
    trainable = [parameter for parameter in model.parameters() if parameter.requires_grad]
    trainable_count = sum(parameter.numel() for parameter in trainable)
    total_count = sum(parameter.numel() for parameter in model.parameters())
    if trainable_count != 58_363_904:
        raise RuntimeError(f"unexpected LoRA trainable parameter count {trainable_count}")
    writer.append_jsonl(
        detailed_path,
        {
            "event": "model_load_complete",
            "time": time.time(),
            "target_module_count": len(targets),
            "trainable_parameters": trainable_count,
            "total_parameters": total_count,
            "gpu_allocated_bytes": torch.cuda.memory_allocated(),
            "gpu_reserved_bytes": torch.cuda.memory_reserved(),
        },
    )

    training = config["training"]
    grad_accum = int(
        config[mode].get(
            "gradient_accumulation_steps", training["gradient_accumulation_steps"]
        )
    )
    max_steps = int(
        config[mode].get("max_optimizer_steps", training["pilot_max_optimizer_steps"])
    )
    required_microsteps = min(len(records), max_steps * grad_accum)
    records = records[:required_microsteps]
    max_steps = math.ceil(len(records) / grad_accum)
    optimizer = AdamW(
        trainable,
        lr=float(training["learning_rate"]),
        weight_decay=float(training["weight_decay"]),
        fused=True,
    )
    warmup_steps = max(1, int(round(max_steps * float(training["warmup_ratio"]))))

    def lr_scale(step: int) -> float:
        if step < warmup_steps:
            return float(step + 1) / warmup_steps
        denominator = max(1, max_steps - warmup_steps)
        return max(0.0, float(max_steps - step) / denominator)

    scheduler = LambdaLR(optimizer, lr_lambda=lr_scale)
    optimizer.zero_grad(set_to_none=True)
    losses: List[float] = []
    optimizer_step = 0
    checkpoint_paths: List[str] = []
    next_report = 0.05

    try:
        for microstep, record in enumerate(records, start=1):
            case_started = time.time()
            encoded = encoder.encode(record, tensors=True)
            metadata = {
                key: encoded.pop(key)
                for key in ("prompt_tokens", "total_tokens", "target_tokens", "target_text")
            }
            batch = _move_batch(encoded, torch.device("cuda:0"))
            with torch.autocast(device_type="cuda", dtype=torch.bfloat16):
                output = model(**batch, use_cache=False)
                raw_loss = output.loss
                loss = raw_loss / grad_accum
            if not torch.isfinite(raw_loss):
                raise FloatingPointError(
                    f"non-finite training loss at {record['opaque_incident_id']}"
                )
            loss.backward()
            raw_value = float(raw_loss.detach().cpu())
            losses.append(raw_value)
            boundary = microstep % grad_accum == 0 or microstep == len(records)
            grad_norm = None
            if boundary:
                grad_norm = float(
                    torch.nn.utils.clip_grad_norm_(
                        trainable, float(training["max_grad_norm"])
                    ).detach().cpu()
                )
                optimizer.step()
                scheduler.step()
                optimizer.zero_grad(set_to_none=True)
                optimizer_step += 1

            conversation_source = ROOT / record["files"]["conversation"]
            writer.write_text(
                result_root / "conversations" / f"{record['opaque_incident_id']}.md",
                conversation_source.read_text(),
            )
            episode = {
                "record_type": "episode",
                "mode": mode,
                "dataset": record["dataset"],
                "opaque_incident_id": record["opaque_incident_id"],
                "stage_partition": record["stage_partition"],
                "status": "ok",
                "unexpected_issue": False,
                "input_tokens": metadata["prompt_tokens"],
                "output_tokens": metadata["target_tokens"],
                "total_tokens": metadata["total_tokens"],
                "wall_time_s": time.time() - case_started,
                "loss": raw_value,
                "reward": None,
                "ac1": None,
                "ac3": None,
                "ac5": None,
                "avg3": None,
                "avg5": None,
                "mrr": None,
                "metrics_status": "teacher_forcing_only; independent_generation_eval_required",
                "microstep": microstep,
                "optimizer_step": optimizer_step,
                "learning_rate": optimizer.param_groups[0]["lr"],
                "gradient_norm": grad_norm,
                "gpu_allocated_bytes": torch.cuda.memory_allocated(),
                "gpu_reserved_bytes": torch.cuda.memory_reserved(),
                "gpu_physical_so_far": physical_gpu.summary(),
            }
            writer.append_jsonl(trajectory_path, episode)
            writer.append_jsonl(detailed_path, {"event": "training_case", **episode})
            progress = microstep / len(records)
            if progress + 1e-12 >= next_report or microstep == len(records):
                line = (
                    f"{microstep}/{len(records)} ({progress:.1%}) "
                    f"loss={sum(losses)/len(losses):.6f} reward=NA "
                    f"lr={optimizer.param_groups[0]['lr']:.3e} "
                    "AC@1/3/5=NA AVG@3/5=NA MRR=NA "
                    f"optimizer_step={optimizer_step}\n"
                )
                writer.append_text(brief_path, line)
                print(line, end="", flush=True)
                while next_report <= progress + 1e-12:
                    next_report += 0.05

            checkpoint_due = boundary and (
                optimizer_step % int(training["checkpoint_every_steps"]) == 0
                or optimizer_step == max_steps
            )
            if checkpoint_due:
                writer.drain()
                state = {
                    "mode": mode,
                    "optimizer_step": optimizer_step,
                    "microstep": microstep,
                    "mean_loss": sum(losses) / len(losses),
                    "contract_sha256": _sha_file(result_root / "run_contract.json"),
                    "trainable_parameters": trainable_count,
                    "target_module_count": len(targets),
                }
                checkpoint = _save_checkpoint(
                    model,
                    encoder.processor,
                    optimizer,
                    scheduler,
                    checkpoint_root,
                    optimizer_step,
                    state,
                )
                checkpoint_paths.append(str(checkpoint.relative_to(ROOT)))
                writer.append_jsonl(
                    detailed_path,
                    {"event": "checkpoint_saved", "path": checkpoint_paths[-1], **state},
                )
    finally:
        writer.drain()

    physical_summary = physical_gpu.stop()
    summary = {
        "schema_version": "CausalIntegrationSFTTrainingSummaryV1",
        "experiment": config["experiment"],
        "mode": mode,
        "status": "complete",
        "protocol_pass": True,
        "n_cases": len(records),
        "datasets": sorted({row["dataset"] for row in records}),
        "optimizer_steps": optimizer_step,
        "gradient_accumulation_steps": grad_accum,
        "mean_teacher_forced_loss": sum(losses) / len(losses),
        "loss_magnitude_used_as_smoke_gate": False,
        "accuracy_used_as_smoke_gate": False,
        "independent_generation_metrics": None,
        "trainable_parameters": trainable_count,
        "total_parameters": total_count,
        "peak_gpu_allocator_allocated_bytes": torch.cuda.max_memory_allocated(),
        "peak_gpu_allocator_reserved_bytes": torch.cuda.max_memory_reserved(),
        "allocator_measurement_semantics": (
            "CUDA allocator logical bytes; may exceed physical residency with virtual-memory allocation"
        ),
        **physical_summary,
        "wall_time_s": time.time() - started,
        "checkpoints": checkpoint_paths,
        "best_model_status": "pending_independent_generation_evaluation",
        "contract_sha256": _sha_file(result_root / "run_contract.json"),
    }
    _write_json(result_root / "summary.json", summary)
    writer.append_jsonl(detailed_path, {"event": "training_complete", **summary})
    writer.append_text(
        brief_path,
        f"complete optimizer_steps={optimizer_step} "
        f"peak_physical_gpu_MiB={summary['peak_gpu_physical_used_mib_sampled']}\n",
    )
    writer.close()
    return {**summary, "result_root": str(result_root.relative_to(ROOT))}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "RQs/RQ0/configs/training/causal_integration_sft_v1.yaml",
    )
    parser.add_argument("--mode", choices=("smoke", "pilot"), required=True)
    parser.add_argument("--run-name")
    args = parser.parse_args()
    result = run(args.config, args.mode, args.run_name)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
