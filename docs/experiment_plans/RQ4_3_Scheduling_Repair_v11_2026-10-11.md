# RQ4.3 v11: isolate sustained CPU preparation from GPU dispatch

The user requests stopping the slow resumed formal run, repairing scheduling,
checking static consistency, and then resuming the full queue without another
GPU smoke. This is an explicit operational smoke waiver, not a new smoke pass.
The 314 committed positions, 2,632-position queue, call ceilings, all evidence,
prompts, model weights, BF16, fused kernels, token operations, decoding and
scoring remain unchanged. The eight cancelled-arm repairs stay isolated.

## Evidence and scope

The resumed v9 run committed 33 new answers. At eight in-flight requests,
GPU utilization averaged 69.68% (240 samples), versus smoke08's 87.67%
(84 samples). The formal run had hundreds of inputs ready in RAM. After the
pause stopped replenishing CPU tasks, utilization averaged 86.36% over 11
samples while eight GPU requests were still in flight. This supports a host
contention diagnosis but is not a randomized throughput comparison.

The old smoke's finite preparation queue emptied early; it did not qualify
sustained eight-worker preparation alongside eight GPU requests. Formal and
smoke launchers also differed in OMP/MKL defaults (8 versus 1). A CPU probe
shows torch.set_num_threads(1) propagates to the eight Python request threads,
so the environment difference alone is not an established cause.

## Repair

1. Reserve eight distinct physical cores for the eight preparation processes;
   exclude both SMT siblings of those cores from the GPU host process and all
   its threads. The current machine exposes 16 physical cores. Fail before
   model loading when disjoint capacity is unavailable.
2. Keep eight GPU request slots, the existing forward-dispatch and prefill
   locks, eight CPU workers, continuous byte-bounded RAM lookahead and the
   existing memory reserve. CPU workers and their renderer descendants run
   at a lower scheduler priority; do not add a disk preparation buffer.
3. Give formal and smoke the same one-thread BLAS/OpenMP environment. Record
   actual affinity, priority, thread settings, preparation activity, ready
   backlog and per-slot decode progress alongside GPU samples.
4. Add an immediate stop command which kills only the verified owned formal
   process group. Keep atomic commits and interruption recovery unchanged.
5. Static qualification binds the new source fingerprint and byte-identical
   queue; verify protected renderer, Codex and committed-result hashes. Record
   the user's explicit smoke waiver separately from historical GPU evidence.

After these checks, resume the unchanged formal queue under the user's latest
authorization and inspect startup and sustained preparation/decode overlap.
Do not claim a measured throughput repair from static checks alone; report
the actual formal observations. No additional smoke calls are authorized or
spent. No prompts, scientific gates or renderer components change here.
