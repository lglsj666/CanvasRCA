# RQ4.1 host RAM and speed amendment — 2026-10-07

**Status: adopted by explicit user instruction; prospective.**

The user's subsequent instruction leaves `Codex.md` unchanged. The temporary
new host-memory paragraph was removed; its pre-existing rules are preserved.
This amendment and RQ4.1 code/configuration carry the execution-policy change.

The user removes fixed host-memory thresholds, including the 2 GiB selector
limit, and instructs that full experiments must not sacrifice speed to save
RAM. This supersedes the host-memory portions of §16.D and the prior-completion
v13/v14 resource contracts. The old 24 GiB aggregate termination threshold is
also removed. Both per-selector and aggregate host-RAM limits are now **none**.
Continue measuring RSS; do not use it as an eligibility or termination gate.
No replacement numerical host-memory threshold is introduced.

Current code removes memory-estimate rejection from the matched selectors,
SCOPE and G-Prune, measured-RSS rejection from CPU audits, and the aggregate-RSS
SIGTERM trigger. Active policy is `configs/resource_policy_active_v16.json`.
Earlier config fields and archived snapshots describe historical runs and do
not override this policy. They remain intact to explain past decisions.

Other constraints retain their separate meaning: at most eight physical-core
CPU workers, original CPU time accounting, selector time bounds, context/call
budgets, attention storage cap, and GPU VRAM utilization 0.75. This host-RAM
change does not authorize GPU inference or a full experiment.

## Speed evidence

The previous parallel resource fixtures cannot establish a fair before/after
speed comparison. An additional sequential AB/BA comparison uses three fixed
actual request sizes, two repetitions each, fresh processes pinned to CPU 0,
one Torch/BLAS thread, identical seeded FP32 hidden/key tensors, and identical
selected indices. No model forward or LLM call is involved.

| Dataset | Unchunked median | 512-row CPU chunks median | Speed ratio |
|---|---:|---:|---:|
| AIOPS-2022 | 3.016 s | 1.918 s | 1.57× |
| AIOPS-2025 | 2.863 s | 1.957 s | 1.46× |
| AegisLab | 2.795 s | 1.939 s | 1.44× |

Keep DART's CPU chunking because it is faster on these matched fixtures, not
because it fits the removed cap. GPU uses full vectorized operations until
real GPU timing supports a different choice. CPU measurements are not GPU or
end-to-end latency claims. Raw timing and reproducible worker source are in
`results/comparison_coding_v1/prior_speed_v15/`.

The machine owner reports 96 GB installed RAM. The current WSL environment
exposes approximately 45 GiB, with approximately 41 GiB available when checked.
This is an environment observation, not a new RAM cap. No Windows/WSL settings
were changed. The former 2.43 GiB DART peak is comfortably below available RAM.

Historical failed memory checks remain failures under their original contract;
do not rewrite them as passes. Completed CPU checks remain usable because no
facts, selection objective, source image or model result changed. Targeted
static review verifies removal of host-memory rejection paths. No broad CPU
replay, feature extraction, renderer run, GPU smoke or formal launch is needed
for this policy amendment.
