# 2026-07-31 causal-integration SFT v2 development plan

## Purpose

This pilot tests whether conservative case-level causal supervision can improve
the visual-text-topology input without erasing useful uncertainty already
present in the base model's top-5 ranking. It is not an RQ0 result and cannot
establish a visual increment over text-only.

## Changes from rejected v1

- Initialize a fresh rank-8 LoRA from the unmodified Qwen3.6-27B base; never
  continue from a v1 checkpoint.
- Generate base predictions only on the authorized development training pool.
- Balance `base_correct_preservation` and `base_wrong_correction` examples
  within every primary dataset.
- Supervise five candidate services. The root is first; remaining entries keep
  the base model's ranked alternatives before adding the registered hard
  symptom and other evidence-visible candidates.
- Reduce learning rate from 1e-4 to 5e-5 while keeping the adapter architecture,
  BF16 precision, and all other optimizer/runtime integrity rules unchanged.

## Frozen development split

Before base rollout, select four fresh evaluation incidents per primary dataset
from eligible development cases that were in neither v1 pilot training nor v1
pilot evaluation. Reclassify these only within v2 as
`development_heldout_v2`. They cannot enter rollout or training. The current v1
evaluation incidents remain exposed and are barred from v2 selection.

Run the unmodified base model over every remaining eligible primary-dataset
training case plus the three registered optimizer-smoke cases. Token-ineligible
cases are recorded without a model call. After rollouts are frozen, select six
base-correct and six base-wrong examples per primary dataset by deterministic
seed-42 hash, for 36 pilot training cases. If any dataset lacks six cases in
either role, stop and revise the protocol before training.

## Gate

First repeat the exact three-dataset optimizer smoke. Then train for nine
optimizer steps and evaluate base versus the final adapter on the 12 fresh v2
development-heldout incidents with hash-balanced condition order.

Promotion still requires adapter−base macro MRR at least +0.05, adapter parse
rate at least 0.95, no dataset below −0.10, and zero infrastructure failures.
Do not inspect intermediate checkpoints on the heldout cases. A failed gate
stops this direction; it does not authorize formal/reserve use or RL/GRPO.

## Relationship to the visual premise

Passing only shows that targeted SFT improves the visual-text-topology pipeline.
A later visual-benefit claim requires separately frozen, equally supervised
visual-text and text-only training arms evaluated on fresh paired incidents.
The experiment must remain capable of rejecting that claim; positive evidence
cannot be manufactured by selective case inclusion, asymmetric supervision, or
post-hoc stopping.

## Preregistered feasibility amendment: v2.1

The completed training-pool rollout contained 18 base-top-1-correct and only 3
base-top-1-wrong AegisLab cases; AIOPS-2022 contained 23/44 and AIOPS-2025
contained 7/38. Thus the planned six-per-role AegisLab cell was impossible.
This was discovered before any optimizer step and before any v2 heldout call.

Do not redefine correctness and do not duplicate the three failures. The v2.1
pilot uses all three deterministically ordered AegisLab correction cases and
three preservation cases, while retaining six per role for each AIOPS dataset:
6 + 12 + 12 = 30 training cases and eight optimizer steps. The 12-case frozen
evaluation set and every promotion threshold remain unchanged. This amendment
addresses stratum feasibility only; no heldout outcome was available when it
was made.
