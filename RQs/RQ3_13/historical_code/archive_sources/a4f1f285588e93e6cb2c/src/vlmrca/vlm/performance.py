"""Non-invasive request and run-level performance instrumentation."""

from __future__ import annotations

import math
import os
import statistics
import subprocess
import threading
import time
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping


def _mean(values: Iterable[float]) -> float | None:
    rows = [float(value) for value in values if math.isfinite(float(value))]
    return statistics.fmean(rows) if rows else None


def _percentile(values: Iterable[float], quantile: float) -> float | None:
    rows = sorted(float(value) for value in values if math.isfinite(float(value)))
    if not rows:
        return None
    position = (len(rows) - 1) * quantile
    lower, upper = math.floor(position), math.ceil(position)
    if lower == upper:
        return rows[lower]
    return rows[lower] * (upper - position) + rows[upper] * (position - lower)


def request_timing_summary(
    *, request_elapsed_s: float, first_content_s: float | None,
    last_content_s: float | None, output_tokens: int,
    content_arrivals_s: Iterable[float], content_chunks: int,
) -> dict[str, Any]:
    """Summarize client-observed streaming timing without claiming server internals."""

    arrivals = list(content_arrivals_s)
    intervals = [right - left for left, right in zip(arrivals, arrivals[1:])]
    decode = (
        max(0.0, last_content_s - first_content_s)
        if first_content_s is not None and last_content_s is not None else None
    )
    return {
        "schema_version": "CanvasRCARequestPerformanceV1",
        "measurement_mode": "client_observed_streaming",
        "receiver_e2e_s": request_elapsed_s,
        "ttft_s": first_content_s,
        "prefill_time_s": None,
        "prefill_time_status": "not_separately_observable_from_queue_and_transport",
        "decode_time_s": decode,
        "tpot_s": decode / (output_tokens - 1) if decode is not None and output_tokens > 1 else None,
        "output_tokens_per_s": output_tokens / request_elapsed_s if request_elapsed_s > 0 else None,
        "content_chunks": content_chunks,
        "stream_chunk_interarrival_mean_s": _mean(intervals),
        "stream_chunk_interarrival_p50_s": _percentile(intervals, 0.50),
        "stream_chunk_interarrival_p95_s": _percentile(intervals, 0.95),
        "itl_status": "transport_chunk_proxy_not_guaranteed_one_chunk_per_token",
    }


def parse_prometheus_metric(text: str, metric: str) -> list[float]:
    """Read all finite samples for one Prometheus metric name."""

    values = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        name, _, value = line.partition(" ")
        if name.split("{", 1)[0] != metric:
            continue
        try:
            number = float(value.strip())
        except ValueError:
            continue
        if math.isfinite(number):
            values.append(number)
    return values


def summarize_call_performance(calls: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    rows = [dict(call.get("performance") or {}) for call in calls]
    names = ("receiver_e2e_s", "ttft_s", "decode_time_s", "tpot_s", "output_tokens_per_s")
    return {
        f"avg_{name}": _mean(row[name] for row in rows if row.get(name) is not None)
        for name in names
    } | {"request_performance_coverage": sum(bool(row) for row in rows) / len(rows) if rows else None}


@dataclass
class RuntimePerformanceMonitor:
    """Sample one local vLLM/GPU process and return run-level operational cost."""

    base_url: str
    interval_s: float = 1.0
    enabled: bool = True
    _samples: list[dict[str, float]] = field(default_factory=list, init=False)
    _errors: set[str] = field(default_factory=set, init=False)
    _stop: threading.Event = field(default_factory=threading.Event, init=False)
    _thread: threading.Thread | None = field(default=None, init=False)
    _started: float = field(default=0.0, init=False)

    def start(self) -> "RuntimePerformanceMonitor":
        self._started = time.perf_counter()
        if self.enabled:
            self._thread = threading.Thread(target=self._loop, name="runtime-performance", daemon=True)
            self._thread.start()
        return self

    def _gpu(self) -> dict[str, float]:
        command = [
            "nvidia-smi", "--query-gpu=utilization.gpu,memory.used,memory.total,power.draw",
            "--format=csv,noheader,nounits",
        ]
        visible = os.environ.get("CUDA_VISIBLE_DEVICES", "").strip()
        if visible and visible.split(",")[0].isdigit():
            command[1:1] = ["--id", visible.split(",")[0]]
        output = subprocess.run(command, check=True, capture_output=True, text=True, timeout=2).stdout
        rows = [[float(value.strip()) for value in line.split(",")] for line in output.splitlines() if line.strip()]
        if not rows:
            return {}
        util, used, total, power = zip(*rows)
        return {
            "gpu_utilization_fraction": statistics.fmean(util) / 100.0,
            "vram_used_bytes": sum(used) * 1024 * 1024,
            "vram_total_bytes": sum(total) * 1024 * 1024,
            "power_watts": sum(power),
        }

    def _vllm(self) -> dict[str, float]:
        endpoint = self.base_url.rstrip("/").removesuffix("/v1") + "/metrics"
        with urllib.request.urlopen(endpoint, timeout=2) as response:
            body = response.read().decode("utf-8", errors="replace")
        values = parse_prometheus_metric(body, "vllm:gpu_cache_usage_perc")
        return {"kv_cache_usage_fraction": max(values)} if values else {}

    def _loop(self) -> None:
        while not self._stop.is_set():
            sample = {"offset_s": time.perf_counter() - self._started}
            for name, reader in (("nvidia_smi", self._gpu), ("vllm_metrics", self._vllm)):
                try:
                    sample.update(reader())
                except Exception as error:  # operational telemetry must never stop inference
                    self._errors.add(f"{name}:{type(error).__name__}")
            self._samples.append(sample)
            self._stop.wait(max(0.1, self.interval_s))

    def stop(self, *, attempted_requests: int, good_requests: int) -> dict[str, Any]:
        elapsed = max(0.0, time.perf_counter() - self._started)
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=max(2.0, self.interval_s + 1.0))
        sample_duration = min(elapsed, self.interval_s * max(1, len(self._samples)))
        util = [row["gpu_utilization_fraction"] for row in self._samples if "gpu_utilization_fraction" in row]
        power = [row["power_watts"] for row in self._samples if "power_watts" in row]
        used = [row["vram_used_bytes"] for row in self._samples if "vram_used_bytes" in row]
        total = [row["vram_total_bytes"] for row in self._samples if "vram_total_bytes" in row]
        cache = [row["kv_cache_usage_fraction"] for row in self._samples if "kv_cache_usage_fraction" in row]
        mean_util, mean_power = _mean(util), _mean(power)
        return {
            "schema_version": "CanvasRCARunPerformanceV1",
            "status": "sampled" if self._samples else "disabled",
            "monitor_elapsed_s": elapsed,
            "sample_count": len(self._samples), "sample_interval_s": self.interval_s,
            "attempted_requests_per_s": attempted_requests / elapsed if elapsed else None,
            "goodput_requests_per_s": good_requests / elapsed if elapsed else None,
            "mean_gpu_utilization_fraction": mean_util,
            "peak_gpu_utilization_fraction": max(util) if util else None,
            "gpu_utilization_weighted_seconds": mean_util * sample_duration if mean_util is not None else None,
            "gpu_active_seconds": min(
                elapsed, sum(value > 0 for value in util) * self.interval_s,
            ) if util else None,
            "peak_vram_used_bytes": max(used) if used else None,
            "peak_vram_fraction": max((a / b for a, b in zip(used, total) if b > 0), default=None),
            "peak_kv_cache_usage_fraction": max(cache) if cache else None,
            "estimated_energy_joules": mean_power * sample_duration if mean_power is not None else None,
            "measurement_scope": "run_level_operational_not_per_case_causal_cost",
            "errors": sorted(self._errors),
        }
