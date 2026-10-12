# Stage B qualification review — 2026-09-27

Contract: `787a885b5c6796eedc1b6259d1e3b5c7348af09e0286bb7efd2ce7a467017e0a`.
Scope: implementation and qualification only. No formal authorization issued.

## Coverage and integrity

- CPU: 10 unit tests; 84 full requests (three development cases × fourteen arms × two models), 18.351 s, zero generation calls. Each worker pinned to a different physical core (0/2/4). Every candidate input checked with both real model processors.
- GPU: one logical smoke, 18 initiated / 18 completed, 276.903 s including both sequential model launches and persistence. Three cases × W_QUAL_T / B0_REL_S / W_SCOPE_G × Qwen/Gemma. All outputs parsed under the inherited contract; 18 raw finish reasons `stop`, no timeout or infrastructure failure.
- Cumulative calls 10,917 = inherited10,899 + smoke18. New formal calls 0. No retry/extra qualification window.
- All 18 conversation files have complete System/User/Assistant sections; every saved text input and exact assistant response is contained in the Markdown. All 12 submitted PNGs equal the CPU-qualified bytes. Saved request identities match qualification; original raw responses, projections, partial streams, cost, output and sidecar audits persist.
- Actual image tokens: Qwen 6,914 and Gemma 1,066 for both new image families; never substitute source pixels or assume equal model costs. Maximum tested input 21,468, effective output ceiling8,192 unchanged.
- All attention probes are null. Owned inference services and runners exited after review; unrelated GPU usage left alone. Source/config contract check took0.0182s, no old request or image regeneration. Formal authorization file absent.

## Visual/input review

Inspected all three scope PNGs plus screenshot control, all three added-witness texts, common prompt/candidate sections and all eighteen responses. Typed numeric entities, attached metric/operation names, deployment vs call edge direction and intact attribute ledgers are present. No root labels, dataset identity or filesystem source paths enter model-visible inputs. Screenshot uses the relational text itself, not a separately summarized packet. Values remain in the common witness text for scope arms; these are not pure-vision conditions.

The AegisLab example has only service evidence; no node/pod relation is invented. The AIOPS2022 example reuses a host anchor across several contextual packs: this is a possible concentration limitation of the inherited ranking, not a reason to tune on smoke answers. Some no-peer arms are natural no-ops and have identical input identities; reuse is permitted, not claimed as independent manipulation.

## Observable model errors are retained

Examples from saved outputs, not formal efficacy findings:

- Qwen W_QUAL_T on INC-0986D6C54EC6 asserts `212 -> 217` from onset/rank rather than a displayed edge. The supplied G does not contain that edge. This is an unsupported model inference, not an edge emitted by the renderer.
- Qwen W_SCOPE_G on INC-B8CEA35848D0 calls three-digit312 a pod, despite the fixed ID-type instructions. Types and relations in the supplied graph remain correctly bound.
- Qwen on the AegisLab case can rank the labelled root first while making an erroneous time comparison or unsupported causal relation. Correct ranking does not validate the explanation.
- Gemma returns one candidate throughout these tests; allowed by the frozen scorer and not padded or resampled.

No prompt, ranking, scorer or image was changed after seeing these answers. Smoke correctness is not an accuracy threshold and cannot establish MRR improvement or visual benefit.

## Nonfatal runtime warnings

Both servers report the optional `vllm.third_party.deep_gemm` import probe failing to find CUDA_HOME; the message includes an AssertionError traceback at WARNING level. The frozen unquantized/Triton serving path initializes and completes all calls. Inference-time Triton JIT warnings also appear. These are preserved, not suppressed or confused with EngineDead/CUDA/OOM/request failures; no inference recipe change was made.

Result: qualification passed with full planned live coverage. This does not qualify all fourteen arms live or prove full180-case capacity; untested scientific performance remains unknown. Stop here.
