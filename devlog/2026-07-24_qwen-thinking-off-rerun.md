# 2026-07-24 — Qwen bake-off rerun with thinking disabled

*Term definitions (MRR, parse rate, chain-of-thought, DNF, and so on) are in the
2026-07-23 devlog's "Terms" block. SIRCL is the sibling text-only project
(`RL-SLM-RCA`) whose settings we mirror. "Design decision (DD)" = a numbered,
recorded choice in `plans/design_decisions.md`.*

## What happened

Reran the three Qwen models on the same 20 AegisLab cases, now telling each model to
skip its written-out reasoning and answer directly — the same recipe the sibling
project SIRCL uses. The three settings are now in
[vlmrca/vlm/configs.py](../vlmrca/vlm/configs.py):
`extra_body={"chat_template_kwargs": {"enable_thinking": False}}` (turn reasoning
off), `presence_penalty=1.5` (discourage repetitive rambling), and `temperature=0.0`
(make output deterministic — the code path to our self-hosted models was not passing
this before). Ran as job array 18482149, with results saved under
`RQs/RQ3/results/bakeoff_nothink_qwen*`; the earlier thinking-mode results
(`RQs/RQ3/results/bakeoff_qwen*`) were kept so the two can be compared. Same cached dashboards.

| model | MRR | Top1 | parse | out-tok median | s/case |
|---|---|---|---|---|---|
| **thinking (default, first run)** | | | | | |
| qwen3.5-9b | 0.417 | 0.400 | 0.60 | 15113 | 223.7 |
| qwen3.5-4b | 0.485 | 0.450 | 0.95 | 10024 | 133.2 |
| qwen3.6-27b | 0.050 | 0.050 | 0.10 | 0 (18/20 conn-err) | 82.5 |
| **no-thinking (enable_thinking=False, pp=1.5)** | | | | | |
| qwen3.5-9b | 0.350 | 0.250 | **1.00** | 775 | 33.4 |
| qwen3.5-4b | 0.287 | 0.200 | **1.00** | 460 | 8.9 |
| qwen3.6-27b | **0.658** | **0.600** | **1.00** | 695 | 51.8 |

Reference (thinking-free already): gemma-4-e4b 0.508 / gemma-4-12b 0.467 · Sonnet-5 0.797.
Input is ~9.4k tokens/case (dashboard image + hybrid text) for all — that fixed cost,
not output, now dominates the token count.

## Key findings

- **Thinking-off fixes parse and speed for all three: parse 0.60/0.95/0.10 → 1.00,
  output medians ~15k/10k → 460–775 tokens, 4–15× faster.** The template's pre-closed
  empty `<think></think>` makes the model answer directly; responses are clean (no
  stray think tags), all 20/20 parse.

- **qwen3.6-27b is transformed: MRR 0.050 → 0.658** — now the **best open model**,
  above gemma-4-e4b (0.508) and within reach of Sonnet-5 (0.797). Its thinking-mode
  0.050 was never a real score: the server dropped connections on 18/20 cases under
  the long generations. Short generations removed that stress, so 0.658 is its true
  number.

- **But thinking-off HURT the small Qwen models: qwen3.5-9b 0.417 → 0.350,
  qwen3.5-4b 0.485 → 0.287.** For these, the (slow, often-truncated) reasoning was
  genuinely contributing accuracy. Caveat sharpening this: the thinking-mode MRR
  counted truncated cases as 0 (40% of 9b, 5% of 4b), so their *per-completed-case*
  accuracy with thinking on was even higher than 0.417/0.485. The small Qwens really
  do reason their way to better answers — at 15–25× the tokens and a large parse hit.
  The 27B does not need the extended CoT to be accurate; the small ones lean on it.

## Revised screening-model picture (each model at its appropriate config)

| model | MRR | parse | s/case | note |
|---|---|---|---|---|
| qwen3.6-27b (nothink) | **0.658** | 1.00 | 51.8 | best accuracy; ~9× slower than gemma-e4b |
| gemma-4-e4b | 0.508 | 1.00 | 5.7 | best speed/accuracy balance |
| gemma-4-12b | 0.467 | 1.00 | 8.6 | fast, solid |
| qwen3.5-9b (nothink) | 0.350 | 1.00 | 33.4 | reasoning helped it; nothink loses that |
| qwen3.5-4b (nothink) | 0.287 | 1.00 | 8.9 | weakest |
| claude-sonnet-5 (ref) | 0.797 | — | — | frontier reference |

This is now an **accuracy-vs-speed decision**, not a clear single winner as before:
- **qwen3.6-27b** scores furthest above the "random floor" (~0.21 MRR — roughly what
  you would get by guessing five services at random), so it has the most room to show
  differences between dashboard settings — the property that matters most for a model
  used to screen many settings — but running the full grid with it costs about 9× the
  GPU time of a Gemma. Since we host it ourselves and can run cases in parallel, that
  may be acceptable.
- **gemma-4-e4b** remains the cheapest reliable option for fast iteration.
- Plausible split: gemma-4-e4b for rapid within-axis iteration, qwen3.6-27b for the
  confirmation passes and as the headline open-model comparator. Not yet promoted to
  a DD — pending the user's call on the tradeoff.

## Blockers

- None new. gemma-4-26b-a4b still did not finish (its mixture-of-experts kernels take
  longer than the 1800-second startup limit to compile) from the first run, and it
  was not part of this Qwen-only rerun.

## Next steps

1. Decide the screening model on the accuracy/speed tradeoff above; record as a DD.
2. If qwen3.6-27b is chosen, note its 51.8 s/case when sizing the RQ1 grid GPU budget.
3. Start the RQ1 grid ([docs/rq1_design.md](../docs/rq1_design.md)) with the chosen model.
