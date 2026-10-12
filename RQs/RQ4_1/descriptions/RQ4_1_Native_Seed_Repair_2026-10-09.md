# RQ4.1 native request seed contract repair — 2026-10-09

The user explicitly authorizes fixing the stopped native phase and resuming the
experiment. This is an execution repair of the registered T_NATIVE requests,
not a new scientific condition or a new set of answers for completed calls.

## Failure and scope

The HF phase committed all 5,880 positions (5,862 generated answers and 18
registered inapplicable positions). T_NATIVE then reserved 36 attempts, but the
shared client rejected their registered per-unit seeds against its default seed
42 before sending any inference HTTP request. These infrastructure failures and
the earlier single shutdown interruption remain in the original call ledger.
All 220 T_NATIVE positions remain pending. The native smoke used seed 42 and
therefore did not exercise this integration defect.

The common client now accepts an explicit `registered_seed` contract, passed
from the frozen unit by the RQ native worker. It must equal the actual request
seed. Temperature and top-p still match the canonical defaults, and requests
without this explicit contract still require the default seed 42. No global
configuration or environment seed is mutated, so concurrent requests cannot
change one another's expected seed. The model payload receives its original
seed; the extra validation argument is not transmitted to the model.

Prompts, evidence, schema, candidates, scorer, model weights, processor, native
profile, ranking-prefix decoder, generation parameters, 36-way concurrency,
0.75 GPU fraction, call keys and request fingerprints stay unchanged. The
T_NATIVE seeds are not replaced with 42. Completed HF work is skipped using its
existing phase marker before loading a model or materializing requests.

## Qualification and frozen successor

The version-29 execution configuration retains the version-28 output directory,
ledger scope, request index and budgets. It points only to a new source freeze
and authorization receipt. Version-28 configuration, freeze, qualification,
completed artifacts and failed attempts remain unchanged. The four pre-repair
source files are archived under `deployment_v29/before_source/` for resolving
their historical frozen hashes.

Targeted offline checks cover default and registered seed validation, invalid
seed types/ranges, unchanged temperature/top-p enforcement, all 220 registered
native seeds concurrently through the real client with a transport substitute,
the real native worker/client connection, shared streaming-client regressions,
atomic commits and fast resume. A read-only pending-request check verifies all
220 logical request fingerprints match version 28 and that the only pending
positions are native. Existing full CPU and GPU qualification is inherited;
no fresh GPU smoke or new scientific qualification is claimed.

After these checks, resume the authorized formal native queue. Inspect actual
committed payload seeds, tokenizer counts, decoder audit records and ledger
progress during at least two minutes of healthy operation. These are the
registered formal requests, not additional qualification calls. Preserve any
model failures as outcomes; retry only permitted uncommitted infrastructure
failures. Monitor startup without changing the queue based on answers. The
runner shuts down its owned server after completion or failure.

With 5,899 historical formal attempts and 220 pending positions, the expected
total is 6,119 formal attempts if no additional interruption occurs, below the
existing 6,470 formal cap. The project-wide 12,000 cap is unchanged. No new
smoke allowance is spent. Codex.md is unchanged by this repair.
