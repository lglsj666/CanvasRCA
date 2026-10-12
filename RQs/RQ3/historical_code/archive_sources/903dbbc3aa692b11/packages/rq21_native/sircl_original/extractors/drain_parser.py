"""
Vendored Drain log parser — shared primitive used by L1 (LT) and L4 (LB).

Citation:
  He, P., Zhu, J., Zheng, Z., Lyu, M.R. (2017).
  "Drain: An Online Log Parsing Approach with Fixed Depth Tree."
  In Proc. IEEE ICWS 2017.

In-repo code reference for parsing integration pattern:
  src/baselines/original_implementations/non_llm/rca_algo_contrib/nezha/log_parsing.py:14
  (Nezha's Drain3 integration. We use the same drain3 library here.)
"""

from __future__ import annotations

from typing import List, Tuple

import pandas as pd


_LOG_FORMAT_PLACEHOLDER = "<*>"


def parse_drain_templates(messages: List[str]) -> Tuple[List[str], List[int]]:
    """
    Parse a list of raw log messages into Drain templates.

    Returns:
        (template_texts, message_template_ids)
        template_texts[i] is the canonical template string for cluster i
        (cluster_id is 1-indexed in drain3 — we re-index to 0-based).
        message_template_ids[k] is the 0-based cluster index assigned to messages[k].
    """
    if not messages:
        return [], []

    # Drain3 emits warnings to stderr if config file not found; suppress them.
    import warnings as _warnings
    _warnings.filterwarnings("ignore")

    from drain3 import TemplateMiner

    tm = TemplateMiner()
    raw_assignments: List[int] = []
    for msg in messages:
        result = tm.add_log_message(str(msg))
        # drain3 returns cluster_id (int >= 1)
        raw_assignments.append(int(result["cluster_id"]))

    # drain3 cluster_ids are 1-based; re-index to dense 0-based
    sorted_clusters = sorted(tm.drain.clusters, key=lambda c: c.cluster_id)
    template_texts = [c.get_template() for c in sorted_clusters]
    cid_to_idx = {c.cluster_id: idx for idx, c in enumerate(sorted_clusters)}
    message_template_ids = [cid_to_idx[cid] for cid in raw_assignments]

    return template_texts, message_template_ids


def bin_template_counts(
    df_logs: pd.DataFrame,
    *,
    bin_seconds: int = 60,
    service_col: str = "container_name",
    message_col: str = "message",
    timestamp_col: str = "timestamp",
) -> pd.DataFrame:
    """
    Aggregate Drain-parsed logs into per-service per-template per-time-bin counts.

    Returns a long DataFrame with columns:
        service, template_id, template_text, time_bin, count

    If `df_logs` lacks a timestamp column, all messages are placed in time_bin=0
    (the per-template per-service total over the whole window).
    """
    if df_logs.empty or service_col not in df_logs.columns or message_col not in df_logs.columns:
        return pd.DataFrame(
            columns=["service", "template_id", "template_text", "time_bin", "count"]
        )

    messages = df_logs[message_col].astype(str).tolist()
    template_texts, msg_tids = parse_drain_templates(messages)

    work = df_logs[[service_col, message_col]].copy()
    work["template_id"] = msg_tids
    work["template_text"] = [template_texts[t] for t in msg_tids]

    if timestamp_col in df_logs.columns:
        ts = pd.to_numeric(df_logs[timestamp_col], errors="coerce")
        work["time_bin"] = (ts // bin_seconds).astype("Int64")
    else:
        work["time_bin"] = 0

    grouped = (
        work.groupby([service_col, "template_id", "template_text", "time_bin"], dropna=False)
            .size()
            .reset_index(name="count")
            .rename(columns={service_col: "service"})
    )
    return grouped
