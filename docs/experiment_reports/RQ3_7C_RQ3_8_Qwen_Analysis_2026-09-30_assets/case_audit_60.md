# 平衡案例附录（60 例）

按 RQ×MRR 改善/退化/不变各抽十例；在 cohort×dataset 内固定 hash，再轮转抽取。不是总体频率估计。此文件逐条提供实际公开理由和源产物，不能把模型理由当成正确的因果解释。

## RQ3.7 · INC-DABDFB89960F · repair

aegislab / eval / service / ContainerKill。MRR 0.3333 → 1.0000。

评测标签（仅分析）：{"ts-travel-plan-service": "540"}

T_MATCH：["410", "830", "540"]

Service 410 is the root cause, evidenced by a decisive jump in jvm.system.cpu.load_1m (median 9.31 to 66.32, ~2.38 sigma) concurrent with the earliest fault onset at +4.0m, which contradicts the alternative hypothesis that the downstream service 540's memory crash was an independent origin. Topology and trace data confirm 410 is a callee within the call chain affected by 284's latency, and its CPU saturation temporally precedes and explains the resource contention leading to 540's crash at +4.2m.

LOCAL_LINK：["57798", "6853", "410"]

Pod 57798 (hosted on node 6853) shows a definitive k8s.container.restarts anomaly rising from a baseline of 0.0 to a current median of 1.0, starting at +6.2m which is the earliest of all propagation onsets. This local failure on pod 57798 plausibly propagates to service 410, which exhibits a severe secondary symptom of 7x CPU load increase and sustained latency degradation.

[旧输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_C_eval/qwen3.8-27b/outputs/f5cef31c7480b64611b5d2dd6bd8d0ff97f432005071854cf7db7a6938334b01.json) · [新输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_C_eval/qwen3.8-27b/outputs/57efb6a52f75924dd8b704882191abdd5321b59eaeb8ab22bf86d2f1d8b455be.json) · [新输入](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_C_eval/qwen3.8-27b/inputs/57efb6a52f75924dd8b704882191abdd5321b59eaeb8ab22bf86d2f1d8b455be.json)

[模型所见图](../pre_unified_preserved/assets/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_C_eval/qwen3.8-27b/renders/57efb6a52f75924dd8b704882191abdd5321b59eaeb8ab22bf86d2f1d8b455be_2.png)

## RQ3.7 · INC-3D79B00A900E · repair

aiops2022 / eval / pod / k8s容器内存负载。MRR 0.0000 → 1.0000。

评测标签（仅分析）：{"productcatalogservice2-0": "99916"}

T_MATCH：["41802", "6929", "16074"]

Pod 41802 exhibits a decisive root cause signal with a 999 signed-z score for container_cpu_cfs_throttled_seconds, spiking from a baseline of ~0.06 to 372.7, indicating severe CPU throttling. This is temporally aligned with the fault window (+22m to +24m) and precedes the downstream propagation of latency issues in services 724 and 474 observed in the trace evidence, while host 6929 metrics show only mild IO activity that does not independently explain the magnitude of the CPU constraint.

LOCAL_LINK：["99916", "6929", "41802"]

Metrics show Pod 99916 experiencing simultaneous and massive spikes in container_memory_failcnt, container_fs_reads, and mapped files starting around +39m. This node-level resource exhaustion is corroborated by the 'hosts' relationship indicating Pod 99916 is deployed on Node 6929, which also exhibits corresponding system-level anomalies in IO read latency and await metrics. The temporal onset and specific failure metrics identify the pod as the origin of the fault, with the host node being the co-located infrastructure impact.

[旧输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_C_eval/qwen3.8-27b/outputs/8774b1be1c6930e50e4b2d63aa411c62b2b77fb659bed5172bda6469485159c5.json) · [新输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_C_eval/qwen3.8-27b/outputs/156fd70ead9a6c548128212a961b694d1a20d0d2cbab07377cce222708299b2a.json) · [新输入](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_C_eval/qwen3.8-27b/inputs/156fd70ead9a6c548128212a961b694d1a20d0d2cbab07377cce222708299b2a.json)

[模型所见图](../pre_unified_preserved/assets/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_C_eval/qwen3.8-27b/renders/156fd70ead9a6c548128212a961b694d1a20d0d2cbab07377cce222708299b2a_2.png)

## RQ3.7 · INC-96E8C237EFAF · repair

aiops2025 / eval / service / jvm cpu。MRR 0.5000 → 1.0000。

评测标签（仅分析）：{"adservice": "240"}

T_MATCH：["7082", "240", "718"]

Service 7082 is identified as the root cause due to a decisive 12σ deviation in node_disk_written_bytes_total (rising to 486KB) that temporally precedes the latency spikes in downstream callers 240 (GetAds, 3.7x latency) and 741 (rrt_max, 4x increase), confirming a write-I/O bottleneck as the origin rather than the co-located disk read anomaly in node 2619 or the downstream latency symptoms.

LOCAL_LINK：["240", "888", "7082"]

TRC-L identifies service 240 (GetAds) as the exclusive-latency origin with a rank_score of 3.7, where the fault p95 latency (110,215 us) is entirely local time, indicating the component is not blocking on a downstream dependency. While G confirms a caller relationship where 888 invokes 240, the latency containment within 240 contradicts a 888-origin, instead identifying 240 as the active fault source; the lack of a call edge to the CPU-saturated Pod 72208 prevents a co-location attribution to Node 8830, placing 888 and the storage metric 7082 as likely secondary symptoms or independent noise.

[旧输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_A_development/qwen3.8-27b/outputs/11cfdddac01c8592e70eb42a92c7bf23ab4725992c068443c87e83060b87508a.json) · [新输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_A_development/qwen3.8-27b/outputs/92e9609b25f68a621477ddce16cb3f711ac3c539e593f579bf6c6f97dd1f25f0.json) · [新输入](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_A_development/qwen3.8-27b/inputs/92e9609b25f68a621477ddce16cb3f711ac3c539e593f579bf6c6f97dd1f25f0.json)

[模型所见图](../pre_unified_preserved/assets/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_A_development/qwen3.8-27b/renders/92e9609b25f68a621477ddce16cb3f711ac3c539e593f579bf6c6f97dd1f25f0_2.png)

## RQ3.7 · INC-851D1AAC181D · repair

aegislab / test / service / HTTPResponseDelay。MRR 0.0000 → 1.0000。

评测标签（仅分析）：{"ts-route-plan-service": "273", "ts-travel2-service": "703"}

T_MATCH：["716", "794", "103"]

Service 716 is the top-ranked TRC-L candidate (onset +5.4m, rank 2) and precedes the subsequent cascade of latency spikes in services 794 (+5.6m), 406 (+5.6m), and 103 (+5.9m). The directed call edge 771 -> 794 and the synchronized CPU load spikes in the 794/629/544/930 cluster after +5.6m confirm that the fault propagated downstream from 716, while the early, stable, and slightly decreasing memory metrics of pod 242 (onset +4.0m) indicate a concurrent benign symptom rather than the primary origin.

LOCAL_LINK：["273", "855", "614"]

Service 273 is the root origin, verified by a 9.67x exclusive latency spike on its POST operation that dominates the trace evidence and is corroborated by a direct dependency edge where 855 calls 273, indicating the failure propagates downward to callers. The secondary spike in 855's local save operations appears as a downstream consequence of the delay originating in 273 rather than an independent root cause.

[旧输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_C_test/qwen3.8-27b/outputs/50830847db3114a04e4f65f3b357ffbc4cebb558fdc9d35927a1338f3ff3f8e1.json) · [新输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_C_test/qwen3.8-27b/outputs/3bfa61c04b437ab7ef842714c05d4aca0c4a9985b6ed1a9c5368df22a3141cb1.json) · [新输入](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_C_test/qwen3.8-27b/inputs/3bfa61c04b437ab7ef842714c05d4aca0c4a9985b6ed1a9c5368df22a3141cb1.json)

[模型所见图](../pre_unified_preserved/assets/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_C_test/qwen3.8-27b/renders/3bfa61c04b437ab7ef842714c05d4aca0c4a9985b6ed1a9c5368df22a3141cb1_2.png)

## RQ3.7 · INC-0F8A700B240D · repair

aiops2022 / test / service / k8s容器进程中止。MRR 0.0000 → 0.5000。

评测标签（仅分析）：{"productcatalogservice": "721"}

T_MATCH：["47001", "356", "18553"]

Pod 47001 exhibits a decisive memory leak (working set +3.09σ, baseline 32MB to 50MB) that temporally precedes the network receive spikes in callers 18553 (5.49σ) and 356 (implied via rank/onset), while service 986's z-score is an artifact of zero baseline variance and its caller 660 shows no metric anomaly. The exclusive latency for 47001's local operation remains low (42μs), confirming the fault is resource-based (memory) rather than compute-bound, and the topology (47001 hosted on 4557) links the pod's resource exhaustion to the observed upstream network pressure.

LOCAL_LINK：["47001", "21288", "8751"]

Metrics show service 47001 has a sustained working-set jump to ~50MB (sigma 3.1) starting around +34m. This node-level memory pressure is corroborated by an elevated load (node 4557) and a CPU spike on pod 8751 (+14.2) near the incident tail, with no contradicting earlier origin.

[旧输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_C_test/qwen3.8-27b/outputs/d9f042b4eac328de38ff08ea4dc6eb2001f9e9ffc5fe974689b0c4fd87ede938.json) · [新输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_C_test/qwen3.8-27b/outputs/e2da0d08f8119c07c3122d82abebcf0e1e83d2eff85841d2ec4b8f7e03faa641.json) · [新输入](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_C_test/qwen3.8-27b/inputs/e2da0d08f8119c07c3122d82abebcf0e1e83d2eff85841d2ec4b8f7e03faa641.json)

[模型所见图](../pre_unified_preserved/assets/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_C_test/qwen3.8-27b/renders/e2da0d08f8119c07c3122d82abebcf0e1e83d2eff85841d2ec4b8f7e03faa641_2.png)

## RQ3.7 · INC-7AB932D940B7 · repair

aiops2025 / test / service / network loss。MRR 0.0000 → 1.0000。

评测标签（仅分析）：{"checkoutservice": "528", "frontend": "379"}

T_MATCH：["785", "793", "973"]

Service 785 is the root cause, evidenced by a massive drop in request volume and latency saturation to ~60ms (indicative of a client-side timeout) rather than local compute exhaustion. Service 793 is the earliest anomaly in the call chain (onset +16.0m, 528 -> 793), while 973 is a downstream victim exhibiting secondary errors and latency spikes.

LOCAL_LINK：["23927", "18792", "528"]

Pod 23927 shows a decisive root-cause signature with an exclusive p95 latency of ~60s (8.35 log2 fold change) and a server error ratio jumping to 0.40, while its host node 6321 shows normal CPU/memory and service 785's elevated client errors align with the propagation chain starting at 528. The co-located memory spike in pod 18792 lacks corresponding latency, error, or host-level resource faults to act as a causative upstream signal.

[旧输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_C_test/qwen3.8-27b/outputs/86244063b54593f37d5ea256bd0dd1deb5070ad858a8666ba08bb5d6523feee0.json) · [新输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_C_test/qwen3.8-27b/outputs/c826df1a1a1ebf7d304f5ad26adcc8876e8f34ffdc078ce5adefe6a591075c21.json) · [新输入](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_C_test/qwen3.8-27b/inputs/c826df1a1a1ebf7d304f5ad26adcc8876e8f34ffdc078ce5adefe6a591075c21.json)

[模型所见图](../pre_unified_preserved/assets/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_C_test/qwen3.8-27b/renders/c826df1a1a1ebf7d304f5ad26adcc8876e8f34ffdc078ce5adefe6a591075c21_2.png)

## RQ3.7 · INC-37ABFB78A80E · repair

aegislab / eval / service / HTTPRequestReplaceMethod。MRR 0.0000 → 0.5000。

评测标签（仅分析）：{"ts-basic-service": "495", "ts-route-service": "819"}

T_MATCH：["437", "564", "364"]

Service 437 is the root cause, verified by its exclusively elevated local operation latency (rank_score 9.9) and the topologically consistent upstream propagation to callers 364 and 287. While 364 exhibits severe inclusive latency, its dependency on 437's degradation confirms 437 as the origin rather than a co-located symptom.

LOCAL_LINK：["364", "819", "287"]

Service 364 is the root origin, with evidence verifying the top candidate and ruling out an upstream node: (1) MET-Z shows a dominant, sustained latency shift (p95 jumping from ~0.03s to 10s, ~4600σ) that begins at bin 42 and persists through the end of the window, an earlier and more continuous departure than the transient spikes seen in downstream service 437; (2) G-trace topology confirms 364 sits upstream of the other high-rank services in the fault (calling 287, 437, 564, and 784), meaning its latency propagates downstream rather than originating from them. In contrast, service 819 shows a surge in error events and call counts (302 to 4454) but only a small latency shift (~0.38 log2 fold change), which is characteristic of a loud downstream symptom of the timeout-induced failure rather than the initial latency bottleneck, and the check confirms no earlier anomaly upstream of 364 to explain its behavior.

[旧输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_A_development/qwen3.8-27b/outputs/6e8a63fef97a5eb9202c2ee003a19822eb7ae881ab9c717810b25b32f68c4036.json) · [新输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_A_development/qwen3.8-27b/outputs/b2a210ea5190fd735bbbb981fec4ed0e736474aecdf76fa2f6a7791f6f561c1b.json) · [新输入](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_A_development/qwen3.8-27b/inputs/b2a210ea5190fd735bbbb981fec4ed0e736474aecdf76fa2f6a7791f6f561c1b.json)

[模型所见图](../pre_unified_preserved/assets/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_A_development/qwen3.8-27b/renders/b2a210ea5190fd735bbbb981fec4ed0e736474aecdf76fa2f6a7791f6f561c1b_2.png)

## RQ3.7 · INC-CCCFF766DA4B · repair

aiops2022 / eval / pod / k8s容器读io负载。MRR 0.0000 → 0.5000。

评测标签（仅分析）：{"productcatalogservice-1": "57600"}

T_MATCH：["7458", "781", "889"]

The initial hypothesis that service 781 is the root cause is revised because its telemetry onset at +20.0m precedes the infrastructure anomaly on node 7458. Node 7458 exhibits decisive temporal alignment with the fault window (bins 49–62, approx. +22.5m to +37.5m), showing a simultaneous, synchronized step-change increase in disk usage, inode total/free counts, and network segments, which is characteristic of an infrastructure-level event like a volume mount or full node failure rather than a service-specific logic bug. Service 781, while having the earliest service-level rank, is likely a victim or concurrent symptom of the underlying node 7458 instability, as no other service shows comparable infrastructure-level metric divergence.

LOCAL_LINK：["7458", "57600", "4668"]

MET-Z shows node 7458 is the sole component with synchronized, massive infrastructure anomalies (disk.used +396σ, inodes +4.3kσ, tcp.out_segs +130σ) starting at bin 50, which temporally precedes and mechanistically explains the sudden local memory spike in hosted pod 57600 (+6x) at bin 33. While G shows service 781 calls 771 (suggesting an upstream application trigger), the absence of application-level CPU throttling, network errors, or log bursts in the trace evidence (R/L) confirms the root cause originated in the infrastructure layer of node 7458 rather than a specific service.

[旧输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_A_development/qwen3.8-27b/outputs/04b25774ddcd3dfa78e2bdd9d196cbd5c93d682679b6469b2baabd54949abc71.json) · [新输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_A_development/qwen3.8-27b/outputs/56f17340f4a5c43bade38d7d75a194f1a634875d7c6e01e2e53a7c9557947c56.json) · [新输入](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_A_development/qwen3.8-27b/inputs/56f17340f4a5c43bade38d7d75a194f1a634875d7c6e01e2e53a7c9557947c56.json)

[模型所见图](../pre_unified_preserved/assets/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_A_development/qwen3.8-27b/renders/56f17340f4a5c43bade38d7d75a194f1a634875d7c6e01e2e53a7c9557947c56_2.png)

## RQ3.7 · INC-B3349051A0EF · repair

aiops2025 / eval / service / jvm latency。MRR 0.0000 → 1.0000。

评测标签（仅分析）：{"adservice": "860"}

T_MATCH：["79276", "60801", "18301"]

The top candidate is pod 79276, verified by metrics showing a massive spike in network receive bytes (from ~9.7 to ~1.1k, deviation_sigma=318) concurrent with a fault window, and its topology as a co-located pod on node 3983 where pod 60801 exhibits extreme memory fluctuation (deviation_sigma=228) suggesting a resource contention origin. This aligns with the propagation onset at +28.0m for service 555 (which hosts 79276/related metrics) and the latency spikes in downstream services like 860 (GetAds) and 236 (Charge) in the trace evidence, indicating 79276 is the localized origin of the network/memory pressure.

LOCAL_LINK：["860", "822", "211"]

Service 860 is the root cause, verified by a 5.27x exclusive latency deviation on /GetAds that dominates the incident and by its elevated rank score. Its dependency on the stable caller 822 and position upstream of the massive p95 latency spike at root 211 confirm the local failure initiated the observed propagation without relying on the fluctuating but non-contributing resource saturation metrics at pod 60801.

[旧输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_A_development/qwen3.8-27b/outputs/c80272b60bd2211a71c11d0640b1d121fceb76f2a3fe83a8de9b742fb4029995.json) · [新输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_A_development/qwen3.8-27b/outputs/6205dc6d657cc6f7791daf9329637973c77b57a4b3a7238d2afe8377592156a7.json) · [新输入](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_A_development/qwen3.8-27b/inputs/6205dc6d657cc6f7791daf9329637973c77b57a4b3a7238d2afe8377592156a7.json)

[模型所见图](../pre_unified_preserved/assets/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_A_development/qwen3.8-27b/renders/6205dc6d657cc6f7791daf9329637973c77b57a4b3a7238d2afe8377592156a7_2.png)

## RQ3.7 · INC-5CBD8BBEC6FF · repair

aegislab / test / service / HTTPResponseReplaceCode。MRR 0.5000 → 1.0000。

评测标签（仅分析）：{"ts-order-service": "118", "ts-seat-service": "648"}

T_MATCH：["442", "648", "118"]

Service 442 is the root cause, evidenced by a massive exclusive latency spike (dX ~6.4) in its 'TravelController.queryInfo' operation and an early onset (+5.5m) that temporally precedes the downstream latency degradation observed in its callee 648. The alternative origin 648 is contradicted by its memory metrics, which show only a modest, non-fluctuating increase (2.32σ) insufficient to drive the 8.98σ latency explosion seen in the caller chain.

LOCAL_LINK：["648", "442", "691"]

Service 648 is the root origin, verified by a continuous memory growth and latency onset at +5.2m (rank 1) preceding other services, and confirmed by direct dependency topology where 442 calls 648, making 648 the blocking callee. The secondary check confirms 442's latency increase is a downstream symptom of calling 648, as 442's issues onset at +7.5m, later than 648's onset.

[旧输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_C_test/qwen3.8-27b/outputs/f63ae214f18dd2700be6db4e612400244ca8230e0fc962a9fd1f6d869e482696.json) · [新输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_C_test/qwen3.8-27b/outputs/98c9b5e99c796f724e15c956150b5cccaea18bf71643f18815c72e3346f85946.json) · [新输入](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_C_test/qwen3.8-27b/inputs/98c9b5e99c796f724e15c956150b5cccaea18bf71643f18815c72e3346f85946.json)

[模型所见图](../pre_unified_preserved/assets/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_C_test/qwen3.8-27b/renders/98c9b5e99c796f724e15c956150b5cccaea18bf71643f18815c72e3346f85946_2.png)

## RQ3.7 · INC-018AC5D486B5 · break

aegislab / eval / service / NetworkCorrupt。MRR 1.0000 → 0.5000。

评测标签（仅分析）：{"ts-auth-service": "702", "ts-verification-code-service": "152"}

T_MATCH：["702", "877", "510"]

Service 702 exhibits the highest trace latency anomaly (rank score 15.95) on the 'SELECT ts.auth_user' operation, which serves as a callee for the top-level entry point 510, confirming 702 as the origin of the latency propagation. The short, isolated CPU spike observed in service 877 (fluctuating 3-sigma deviation) lacks corresponding trace or log error evidence and is temporally misaligned with the sustained fault onset, ruling it out as the primary cause.

LOCAL_LINK：["877", "702", "510"]

Service 877 is the root origin, with evidence verifying the top candidate via an extreme, sustained CPU spike (MET-Z deviation > 3σ, e.g., `k8s.pod.cpu.usage` rising from ~0.006 to ~0.42 at bin 39) and the earliest propagation onset timestamp (+5.2m) prior to the main fault window. This primary resource exhaustion causes downstream latency degradation in the callee service 702 (evidenced by severe 15.95x exclusive latency increase in the `GET` operation) which in turn propagates to upstream service 510.

[旧输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_C_eval/qwen3.8-27b/outputs/560c88e3c22f867faf7a17fe5a06c71b9d6151f22e9c3c36b3d1241424b27562.json) · [新输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_C_eval/qwen3.8-27b/outputs/791db178c9c3b5781260814f641caf1bb648553ba9402f35695c658c88f0c0ef.json) · [新输入](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_C_eval/qwen3.8-27b/inputs/791db178c9c3b5781260814f641caf1bb648553ba9402f35695c658c88f0c0ef.json)

[模型所见图](../pre_unified_preserved/assets/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_C_eval/qwen3.8-27b/renders/791db178c9c3b5781260814f641caf1bb648553ba9402f35695c658c88f0c0ef_2.png)

## RQ3.7 · INC-B646C4677B96 · break

aiops2022 / eval / service / k8s容器网络丢包。MRR 1.0000 → 0.5000。

评测标签（仅分析）：{"checkoutservice": "875"}

T_MATCH：["875", "86432", "216", "22243", "68465"]

Service 875 is the root cause as it exhibits the earliest telemetry onset at +19.9m in the G graph, preceding all downstream callers. Trace evidence confirms this origin by showing a massive exclusive latency spike (12.07 log2 fold change) in the `hipstershop.216/GetCart` operation attributed to service 86432, which is a direct callee of 875, indicating the fault propagated from 875 to 86432 and then to 216.

LOCAL_LINK：["216", "86432", "22243", "68465", "362"]

Trace evidence demonstrates that hipstershop.216/GetCart is the fault origin, showing a ~4.6 ms exclusive p95 latency in baseline state versus ~20,000 ms during the incident across multiple pods (22243, 68465, 86432). This local operation latency surge preceded the ~26-minute propagation onset to downstream dependencies and manifests in 216's lack of child-span duration to subtract (inclusive == exclusive), while node 3243 co-hosting the most affected pods remains stable. Log evidence for service 95554 reveals a concurrent surge in /hipstershop.216/GetProduct API calls (POD /GetProduct 501 errors), confirming 216 as the primary failing component.

[旧输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_C_eval/qwen3.8-27b/outputs/f6d97b8bc01f2f2c3819f10428ce364899ba508a841aec781d592b24d830e012.json) · [新输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_C_eval/qwen3.8-27b/outputs/340043710fd26a158c4b04ec5eb6993c80675ddfe72647684809fc792b59eb2c.json) · [新输入](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_C_eval/qwen3.8-27b/inputs/340043710fd26a158c4b04ec5eb6993c80675ddfe72647684809fc792b59eb2c.json)

[模型所见图](../pre_unified_preserved/assets/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_C_eval/qwen3.8-27b/renders/340043710fd26a158c4b04ec5eb6993c80675ddfe72647684809fc792b59eb2c_2.png)

## RQ3.7 · INC-92A00B34EECF · break

aiops2025 / eval / service / io fault。MRR 0.5000 → 0.0000。

评测标签（仅分析）：{"tidb-tikv": "772"}

T_MATCH：["728", "772", "927"]

Service 728 is the root cause, evidenced by a decisive onset at +15.0m (preceding all other services) and a 'cold start' signature in metrics (duration_avg and raft_apply_wait shifting from zero to non-zero, indicating a crash or restart) that is not explained by the steady-state resource saturation in 772. Topology check confirms 728 is not a downstream symptom of the co-located 772 but a distinct origin, and trace analysis of its caller 927 shows the latency impact propagated upstream without originating there.

LOCAL_LINK：["927", "966", "728"]

Service 927 is the root origin, with evidence verifying the top candidate via an onset at +14.2m that predates all downstream impacts and a propagation graph showing direct causal calls from 927 to affected services 966 and 659. This is supported by the estimated fault window beginning at +14.0m, which aligns with the early latency spikes observed in the 728 and 772 storage components before propagating upstream to 927.

[旧输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_C_eval/qwen3.8-27b/outputs/7fcb4cd6fa5fd72f13ec2629641e59bd0a0b542fd511d806099945740fabd69e.json) · [新输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_C_eval/qwen3.8-27b/outputs/5ff3660dcfee577e081be3b42631a559e2ebc45ba750c5273e73b5512f9a9bf0.json) · [新输入](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_C_eval/qwen3.8-27b/inputs/5ff3660dcfee577e081be3b42631a559e2ebc45ba750c5273e73b5512f9a9bf0.json)

[模型所见图](../pre_unified_preserved/assets/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_C_eval/qwen3.8-27b/renders/5ff3660dcfee577e081be3b42631a559e2ebc45ba750c5273e73b5512f9a9bf0_2.png)

## RQ3.7 · INC-280985561CF8 · break

aegislab / test / service / HTTPRequestDelay。MRR 0.3333 → 0.0000。

评测标签（仅分析）：{"ts-order-service": "488", "ts-seat-service": "150"}

T_MATCH：["724", "726", "150", "953", "392"]

Service 724 is the root cause, evidenced by the largest exclusive latency degradation (549.7σ p50 shift, 2.36s current mean vs 0.04s baseline) and earliest metric onset at +4.0m. Verification confirms that callers 726 and 953 invoke 724 and exhibit high inclusive latency consistent with waiting on the slow 724 calls, while 724's exclusive latency proves the delay is local to 724 rather than propagated from downstream dependencies.

LOCAL_LINK：["953", "724", "726"]

Service 953 is the root origin, with evidence verifying the top candidate via an extreme exclusive latency deviation (+13.08 log2 fold change) and an exclusive-latency signature that exceeds the inclusive signature, proving the delay is local to the operation rather than inherited from downstream dependencies. The decisive topology and temporal relation is that 953's new delay onset aligns with the early latency spikes observed in its callers (724 and 726), which then propagate as inclusive duration increases to 150.

[旧输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_C_test/qwen3.8-27b/outputs/76a11513cfd28afaedd6f93eeb11adc835c86c0fa9bec19685cf934c8442cff7.json) · [新输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_C_test/qwen3.8-27b/outputs/eb91c06ce3f94ea835cfeaf64954d4c8cb8b9bf776b7614f1f64d45b0f2d6820.json) · [新输入](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_C_test/qwen3.8-27b/inputs/eb91c06ce3f94ea835cfeaf64954d4c8cb8b9bf776b7614f1f64d45b0f2d6820.json)

[模型所见图](../pre_unified_preserved/assets/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_C_test/qwen3.8-27b/renders/eb91c06ce3f94ea835cfeaf64954d4c8cb8b9bf776b7614f1f64d45b0f2d6820_2.png)

## RQ3.7 · INC-079EB921B335 · break

aiops2022 / test / service / k8s容器写io负载。MRR 1.0000 → 0.5000。

评测标签（仅分析）：{"emailservice": "352"}

T_MATCH：["77030", "3348", "392"]

The root cause is pod 77030, which exhibits the highest container_memory_failcnt increase (to 15) and a significant disk usage spike, indicating a local resource exhaustion fault. Verification confirms that the earliest anomaly onset for the calling service 392 (+20.0m) occurs after the fault window start, and the directed call edges show 392 as a caller to other services, consistent with 392 being a downstream victim of the resource failure on 77030 rather than the origin. The temporal alignment of the memory failures in 77030 with the latency and error propagation in the trace and log data supports 77030 as the primary origin.

LOCAL_LINK：["3348", "352", "587"]

Node 3348 is the origin, confirmed by the top-ranked disk free-space metric spike and mem free shift during the fault window, and by its co-location with the top trace-latency victims; alternative service-side origins are rejected because upstream calls to 352/587 precede 3348's structural anomaly.

[旧输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_C_test/qwen3.8-27b/outputs/12b84efed3dd97c93840530fc0045173748b8ef94c50c48ae865d0b6920d5d00.json) · [新输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_C_test/qwen3.8-27b/outputs/12b32d74b8922b76a03e98b0eae78d729dd80dec9de68774b0f68ded4d2bc932.json) · [新输入](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_C_test/qwen3.8-27b/inputs/12b32d74b8922b76a03e98b0eae78d729dd80dec9de68774b0f68ded4d2bc932.json)

[模型所见图](../pre_unified_preserved/assets/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_C_test/qwen3.8-27b/renders/12b32d74b8922b76a03e98b0eae78d729dd80dec9de68774b0f68ded4d2bc932_2.png)

## RQ3.7 · INC-E2F836D2BEAA · break

aiops2025 / test / pod/service / pod kill。MRR 0.2500 → 0.0000。

评测标签（仅分析）：{"shippingservice": "817", "shippingservice-1": "97312"}

T_MATCH：["4144", "1390", "2103", "97312"]

Service 4144 is the earliest onset rank-1 metric anomaly at +15.0m, preceding all downstream service symptoms, and is the deployment host for pod 97312, which exhibits a 4.7x request rate drop and log volume drop in the same window. The infrastructure nodes 1390 and 2103 show stable network and memory medians respectively, ruling out node-level resource exhaustion as the origin, leaving the host/pod pair 4144/97312 as the primary failure point propagating to services 378, 1390, and others.

LOCAL_LINK：["395", "741", "2103"]

TRC-L identifies 395 (EmptyCart) as the primary origin with the highest rank_score of 0.41, driven by a latency_lfc of 0.41 and exclusive p95 latency rising to 67856.8us. G topology confirms 361 calls 395, and while 2103 hosts an affected pod (24468) with a 176ms response metric shift, 395's trace signals originate the causal cascade without a co-located infrastructure fault.

[旧输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_C_test/qwen3.8-27b/outputs/0a3e8e8b4680cc72f53d61c63826a9c86a2bc4e09f56a98364140042f16d63cf.json) · [新输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_C_test/qwen3.8-27b/outputs/9678a2a24443061b9eb17fc458e92d7ab880c1da1890ae4220254c816cc2c410.json) · [新输入](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_C_test/qwen3.8-27b/inputs/9678a2a24443061b9eb17fc458e92d7ab880c1da1890ae4220254c816cc2c410.json)

[模型所见图](../pre_unified_preserved/assets/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_C_test/qwen3.8-27b/renders/9678a2a24443061b9eb17fc458e92d7ab880c1da1890ae4220254c816cc2c410_2.png)

## RQ3.7 · INC-B95CA78A9FA8 · break

aegislab / eval / service / JVMMemoryStress。MRR 1.0000 → 0.0000。

评测标签（仅分析）：{"ts-assurance-service": "147"}

T_MATCH：["147", "418", "126"]

Service 147 is the root cause, evidenced by the earliest trace-derived fault onset (+4.2m) and a transient unavailability (k8s.deployment.available=0, k8s.container.ready=0 for pod 62606) that temporally precedes the latency spikes in its callers. Verification confirms that caller 418's latency increase is inclusive (span time includes the slow 147 call) rather than local, and that 147's exclusive latency in traces is not the dominant anomaly compared to the hard availability drop, ruling out a primary upstream origin.

LOCAL_LINK：["418", "539", "485"]

Service 418 is the root origin, verified by a peak p50 latency of 6.875s that marks the beginning of the fault window (+4.2m) and an exclusive p95 latency fold-change of 8.25 on a local controller endpoint. The alternative origin in the local service 62606 is ruled out because it was hosted by node 9195, showing a container restart as a downstream symptom rather than a causal source in the service dependency graph.

[旧输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_A_development/qwen3.8-27b/outputs/58cfb79406265f119074ab4c110259cd9e901d08bfc7958f5cb04996805888bf.json) · [新输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_A_development/qwen3.8-27b/outputs/8b189d19b7d76b681a41c57fa971cab5f27fd070202e5d81644decb0caad0626.json) · [新输入](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_A_development/qwen3.8-27b/inputs/8b189d19b7d76b681a41c57fa971cab5f27fd070202e5d81644decb0caad0626.json)

[模型所见图](../pre_unified_preserved/assets/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_A_development/qwen3.8-27b/renders/8b189d19b7d76b681a41c57fa971cab5f27fd070202e5d81644decb0caad0626_2.png)

## RQ3.7 · INC-1FDDC9D9F646 · break

aiops2022 / eval / pod / k8s容器内存负载。MRR 0.5000 → 0.3333。

评测标签（仅分析）：{"cartservice-0": "17923"}

T_MATCH：["4238", "17923", "3816"]

Node 4238 is the root cause as its disk usage and hosted pod 17923's filesystem usage and memory cache surged from ~27% to ~33% and ~31MB to ~57MB respectively, well before the application-level latency spikes observed in service 3816. The temporal precedence of the infrastructure metrics (onset ~+20m) over the trace latency degradation (onset ~+28m) confirms the disk pressure as the originating fault.

LOCAL_LINK：["3816", "4238", "17923"]

Node 3816 exhibits correlated, sustained fluctuations across four network metrics (packets, bytes, segments) and free memory, consistent with a local resource exhaustion origin. This node-level degradation aligns temporally and causally with the massive container file-system usage increase observed in pod 17923 and the structural disk-usage shift on the co-hosted node 4238, whereas service-level trace latencies show minor secondary symptoms.

[旧输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_A_development/qwen3.8-27b/outputs/6178e11d58b2d5b39c9d798d0b0bdafa69f288fd098eac66ae287fde0e6ef03e.json) · [新输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_A_development/qwen3.8-27b/outputs/7ae45ecfaf0a96483648669cd5697c6209b481dd649a64e141b829093191a1c5.json) · [新输入](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_A_development/qwen3.8-27b/inputs/7ae45ecfaf0a96483648669cd5697c6209b481dd649a64e141b829093191a1c5.json)

[模型所见图](../pre_unified_preserved/assets/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_A_development/qwen3.8-27b/renders/7ae45ecfaf0a96483648669cd5697c6209b481dd649a64e141b829093191a1c5_2.png)

## RQ3.7 · INC-BFE7EC666320 · break

aiops2025 / eval / node / node cpu stress。MRR 0.5000 → 0.0000。

评测标签（仅分析）：{"node-3": "7373"}

T_MATCH：["456", "7373", "6980", "4252", "528"]

Service 456 is the root cause, evidenced by a 31.7σ spike in `write_wal_mbps` and 19.77σ in `snapshot_apply_count` within the fault window (+18.0m to +20.0m), which temporally precedes the disk write/read anomalies on nodes 7373, 6980, and 4252. Topology G shows no incoming causal edges to 456 from the downstream application services (526, 528, 315, 403), confirming 456 as the origin of the propagation.

LOCAL_LINK：["456", "81250", "315"]

Service 456 is the origin, confirmed by the top-ranked write_wal_mbps deviation (+18σ) and solid topology edges showing 526 calls 456 while caller 528 and callee 315 exhibit stable TRC-L ranks (0.18/0.14), ruling them out as primary drivers. The supporting temporal chain shows 456's anomaly precedes downstream 315 symptoms, which persist even as 456's other signals drop post-window. This exclusion of 81250 (fluctuating 1.29σ noise) and 315 (stable downstream rank) verifies 456 as the decisive root cause.

[旧输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_C_eval/qwen3.8-27b/outputs/7be47b1cfe9468a90f332207228225212d0f6107a53a6c9450dfd725e56fcd10.json) · [新输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_C_eval/qwen3.8-27b/outputs/5f1f7f2bb733b8ccc5bec3093095117c2878895c97e7a4ee7c9ba2504b002066.json) · [新输入](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_C_eval/qwen3.8-27b/inputs/5f1f7f2bb733b8ccc5bec3093095117c2878895c97e7a4ee7c9ba2504b002066.json)

[模型所见图](../pre_unified_preserved/assets/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_C_eval/qwen3.8-27b/renders/5f1f7f2bb733b8ccc5bec3093095117c2878895c97e7a4ee7c9ba2504b002066_2.png)

## RQ3.7 · INC-E18F78F10DB2 · break

aegislab / test / service / JVMReturn。MRR 0.3333 → 0.0000。

评测标签（仅分析）：{"ts-inside-payment-service": "147"}

T_MATCH：["977", "724", "147"]

Service 977 is the root cause, evidenced by a massive CPU spike (k8s.pod.cpu.usage to 7.462, ~1000x baseline) and the absence of any upstream callers in the G topology, indicating a local resource exhaustion (e.g., busy loop). Service 724 is ranked second as it exhibits extreme latency degradation (p95 latency lfc 11.86) and is a downstream victim, while Service 147 shows severe filesystem exhaustion (usage to 20GB) which is a distinct co-located anomaly or secondary symptom rather than the primary temporal trigger.

LOCAL_LINK：["476", "808", "637"]

Service 476 is the root origin, exhibiting the highest trace rank_score (11.86) and an exclusive p95 latency of 11.1ms (a >1000x increase over the 2.99us baseline) before the faults propagated. The causal topology in G confirms service 476 calls service 637, and temporal onset data shows 476 failing first at +6.0m, which then triggered the latency and error surges in downstream services 637 and 808.

[旧输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_C_test/qwen3.8-27b/outputs/fb9fbd9d8e82b14da763ab3c5a266d41e77a38eeb95f947e3943538869a59b5d.json) · [新输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_C_test/qwen3.8-27b/outputs/538177c08fec93d6bc703c3df1d8b8ce98252331bdd257673d5035b8889fc1c8.json) · [新输入](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_C_test/qwen3.8-27b/inputs/538177c08fec93d6bc703c3df1d8b8ce98252331bdd257673d5035b8889fc1c8.json)

[模型所见图](../pre_unified_preserved/assets/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_C_test/qwen3.8-27b/renders/538177c08fec93d6bc703c3df1d8b8ce98252331bdd257673d5035b8889fc1c8_2.png)

## RQ3.7 · INC-A1C6591B0184 · unchanged

aegislab / eval / service / HTTPRequestReplacePath。MRR 0.0000 → 0.0000。

评测标签（仅分析）：{"ts-config-service": "583", "ts-seat-service": "659"}

T_MATCH：["450", "169", "876", "422", "675"]

Service 450 is the root cause, supported by the fact that it is a callee (caller 952 -> callee 450) and exhibits a significant local filesystem pressure anomaly (filesystem.usage median ~3.77MB vs reference ~0.88MB) that is not present in the co-located metrics of service 169 (identical filesystem.available series but no usage spike in the provided host observations for 169). While services 169, 422, 876, 803, and 675 all show identical, severe drops in filesystem.available starting at +5.8m (ranked 1-3 in propagation), this uniformity across multiple independent pods/services indicates a shared infrastructure dependency or a cascading effect from a single origin, and 450's distinct storage write pressure (and its role as a callee in the call graph) identifies it as the upstream driver rather than a passive victim of the same volume issue.

LOCAL_LINK：["337", "169", "422"]

Service 337 is the root origin, verified by its earliest topological position and onset rank of 1 (at +5.8m) that precedes downstream pods. Its status is confirmed by the fact that its callers 169, 422, 450, 803, and 876 all exhibit identical, synchronized filesystem availability drops (MET-Z) and the graph shows these pods as 337's direct dependents. No contradictory exclusive latency (TRC-L) or error-burst (LOG-R) evidence was found that would implicate the downstream pods as independent origins.

[旧输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_C_eval/qwen3.8-27b/outputs/3720a9ebdccac9fdc7ee3e8266c5f6af7217558a52711c63ec9c029564d754d2.json) · [新输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_C_eval/qwen3.8-27b/outputs/847d5b2fcdce6c971cc734340aa70153fa0231012f3975e74a6af77af6349699.json) · [新输入](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_C_eval/qwen3.8-27b/inputs/847d5b2fcdce6c971cc734340aa70153fa0231012f3975e74a6af77af6349699.json)

[模型所见图](../pre_unified_preserved/assets/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_C_eval/qwen3.8-27b/renders/847d5b2fcdce6c971cc734340aa70153fa0231012f3975e74a6af77af6349699_2.png)

## RQ3.7 · INC-68BAACF4BB36 · unchanged

aiops2022 / eval / pod / k8s容器网络资源包损坏。MRR 0.0000 → 0.0000。

评测标签（仅分析）：{"emailservice-1": "51205"}

T_MATCH：["437", "27116", "148"]

Service 437 is identified as the root cause because it is the sole upstream caller in the directed graph to services 148, 320, 329, 624, and 967, all of which exhibit concurrent metric anomalies (e.g., JVM class drops in 148/153) and trace latency spikes (e.g., 329/EmptyCart) consistent with a shared dependency failure originating at 437. Topology verification confirms 437 calls the earliest-impacted downstream services, and temporal onset analysis places 437's impact prior to the downstream propagation, ruling out downstream services as the origin.

LOCAL_LINK：["27948", "27116", "252"]

Top-1 service 27948 is verified by the TRC-L analyzer showing a 7.45 log2 fold-change in exclusive p95 latency for the 'hipstershop.252/SendOrderConfirmation' operation, a metric isolated from child-span delays. The temporal onset of this local latency spike in 27948 at +29.7m precedes the onset of caller 437's symptoms at +37.0m, supporting it as the causal origin rather than a downstream propagation effect. A potential alternative in node 2790 was rejected because its system.cpu.iowait increased only marginally from 0.06 to 0.08, providing no evidence of a host-level bottleneck.

[旧输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_A_development/qwen3.8-27b/outputs/c3980f1bd38b8b0b919a381456e4afa782070f71d7fe1ef5dae7ce32e4568c2d.json) · [新输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_A_development/qwen3.8-27b/outputs/5fee3835e7840247e2e9794deade70692830fda69e4151fbe74bb7413fbe5a46.json) · [新输入](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_A_development/qwen3.8-27b/inputs/5fee3835e7840247e2e9794deade70692830fda69e4151fbe74bb7413fbe5a46.json)

[模型所见图](../pre_unified_preserved/assets/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_A_development/qwen3.8-27b/renders/5fee3835e7840247e2e9794deade70692830fda69e4151fbe74bb7413fbe5a46_2.png)

## RQ3.7 · INC-2A292B511B14 · unchanged

aiops2025 / eval / service / memory stress。MRR 0.0000 → 0.0000。

评测标签（仅分析）：{"emailservice": "446"}

T_MATCH：["245", "783", "11182"]

Service 245 is identified as the root cause because its read_mbps metric exhibits a significant deviation of 4.56σ (fluctuating_3sigma: true) with a peak of ~7M vs baseline of ~38k, representing a primary infrastructure stressor. While service 783 shows the highest exclusive latency degradation in traces (latency_lfc 0.46) and service 11182 shows elevated RRT metrics, neither exhibits the magnitude of baseline break or the independent resource anomaly seen in 245, suggesting 783 and 11182 are likely downstream symptoms or co-located effects of the I/O storm originating at 245.

LOCAL_LINK：["245", "80277", "118"]

Service 245 is the only candidate where a single root entity simultaneously exhibits fluctuating metric anomalies (read_mbps and pod_fs_writes_bytes) and an exclusive latency increase (snapshot_apply_count), with the IO spike and max write size appearing at the exact same bin (31) as the estimated fault window. This localizes the origin to the service's internal IO/latency, as the host (2738) and its other co-located pods (44907, 73569) remain near baseline, effectively ruling out a shared infrastructure fault. The top-1 candidate was verified by confirming the co-occurrence of the absolute IO spike and the latency penalty, and by confirming the absence of broader network/latency anomalies on the node and other pods.

[旧输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_A_development/qwen3.8-27b/outputs/33f3e7ec6eb3ba2ca64fef29625856cfeee87281ccc2ba1cb044cfa33ddb9765.json) · [新输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_A_development/qwen3.8-27b/outputs/b64706cee803e490d990961cad7ef0da753a07b62bb7491345f12cb0de8be755.json) · [新输入](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_A_development/qwen3.8-27b/inputs/b64706cee803e490d990961cad7ef0da753a07b62bb7491345f12cb0de8be755.json)

[模型所见图](../pre_unified_preserved/assets/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_A_development/qwen3.8-27b/renders/b64706cee803e490d990961cad7ef0da753a07b62bb7491345f12cb0de8be755_2.png)

## RQ3.7 · INC-3015F112D266 · unchanged

aegislab / test / service / HTTPResponseAbort。MRR 1.0000 → 1.0000。

评测标签（仅分析）：{"ts-route-plan-service": "358", "ts-travel-plan-service": "747"}

T_MATCH：["358", "856", "678", "387"]

The top candidate is 358, as the exclusive latency of its 'POST /api/v1/routeplanservice/routePlan/minStopStations' operation increased by 9.61 log2 fold-change, indicating a local processing bottleneck not explained by child spans. This is verified against the trace evidence where 856 calls 135 and 678 calls 387, confirming 358 is a distinct origin of high exclusive latency rather than a downstream symptom of the other failed services.

LOCAL_LINK：["358", "856", "634"]

Service 358 is the root origin, verified by a peak exclusive-latency LFC of 9.61 on 'minStopStations' in R and a decisive topological contradiction where the leading CPU consumer 908 is a child of 358 in G, preventing it from being the cause. The fault propagates from 358 to its callee 856 (LFC 7.88) and other downstream services, which then transmit the latency impact to 634, the only service in the M-panel set exhibiting a major p95 latency spike.

[旧输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_C_test/qwen3.8-27b/outputs/3dbdf3270ae86a3eabce35336ec442f39d25e7f03e02a0e3ac91246ddffbebf1.json) · [新输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_C_test/qwen3.8-27b/outputs/44c413545948ed0e57f776fdda0f86e0020a17df7d95bbc22acf93e8935cd616.json) · [新输入](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_C_test/qwen3.8-27b/inputs/44c413545948ed0e57f776fdda0f86e0020a17df7d95bbc22acf93e8935cd616.json)

[模型所见图](../pre_unified_preserved/assets/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_C_test/qwen3.8-27b/renders/44c413545948ed0e57f776fdda0f86e0020a17df7d95bbc22acf93e8935cd616_2.png)

## RQ3.7 · INC-D583BAA68A3F · unchanged

aiops2022 / test / pod / k8s容器网络资源包重复发送。MRR 0.0000 → 0.0000。

评测标签（仅分析）：{"productcatalogservice-1": "85297"}

T_MATCH：["721", "718", "833"]

Service 721 exhibits the strongest root-cause evidence with a 0.35 rank score in TRC-L due to a 0.35 log2 fold change in call count, indicating a local throughput surge rather than inherited latency. Topology confirms 252 calls 721, but 252's later onset at +38.0m compared to 721's earlier onset at +22.0m in G excludes 252 as the origin, placing the fault upstream in the 721/718 cluster before propagation to callers.

LOCAL_LINK：["3009", "67293", "68280"]

The MET-Z analyzer shows that Node 3009 is the only infrastructure node exhibiting a broad degradation across all hosted Pods (67293, 68280, 14257, etc.), characterized by simultaneously high CPU throttling (signed_z 999) and memory usage deviations. In the R and G evidence, Pods 67293 and 68280 are the top-ranked services for CPU throttling and Call-Volume increases, respectively, but because they are co-located on the same node as the other affected pods without unique trace-based latency deviations (e.g., p95 absolute values identical between baseline and fault), their telemetry confirms 3009 as the origin of the localized node-level bottleneck rather than an application-specific failure.

[旧输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_C_test/qwen3.8-27b/outputs/6658c73ec32fe65d240cf3f7e6d359d7a27ba2775d4be36972b4f8b80e26264d.json) · [新输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_C_test/qwen3.8-27b/outputs/dca3db8e5979665c009e23db7f497d1ebc6f0a17c875f344f533c4d5d474dd4a.json) · [新输入](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_C_test/qwen3.8-27b/inputs/dca3db8e5979665c009e23db7f497d1ebc6f0a17c875f344f533c4d5d474dd4a.json)

[模型所见图](../pre_unified_preserved/assets/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_C_test/qwen3.8-27b/renders/dca3db8e5979665c009e23db7f497d1ebc6f0a17c875f344f533c4d5d474dd4a_2.png)

## RQ3.7 · INC-5E10026E33A4 · unchanged

aiops2025 / test / service / jvm cpu。MRR 1.0000 → 1.0000。

评测标签（仅分析）：{"adservice": "697"}

T_MATCH：["78233", "697", "287"]

The log evidence identifies pod 78233 as the origin, showing new 'stress' thread creation logs at bin 28 (matching the fault window start) that explicitly reference service 697. While service 697 exhibits the most severe latency degradation (exclusive p95 spike) in the trace data, this is consistent with it being the callee stressed by the local resource fault on host pod 78233.

LOCAL_LINK：["697", "895", "50641"]

Service 697 is the origin, confirmed by the top-ranked exclusive latency increase (exl_p95 9.8k to 127k µs) in the TRC-L analyzer and the earliest anomaly onset (+27.2m) in the G graph. The alternate origin hypothesis is rejected because service 895 is a callee of 697, proving it is a downstream symptom, and no upstream caller exhibits a preceding latency shift. Correlated memory spikes in pods 50641 and 97603 represent concurrent resource pressure rather than the primary logic failure.

[旧输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_C_test/qwen3.8-27b/outputs/11748cf5657e8a3db1bae2fd544db70658cb8586d1fe1d300cebc104c439645b.json) · [新输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_C_test/qwen3.8-27b/outputs/5768a719fc18bc599f69e46bc1373acc1c32fcd9d610894486d79f28ec91b992.json) · [新输入](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_C_test/qwen3.8-27b/inputs/5768a719fc18bc599f69e46bc1373acc1c32fcd9d610894486d79f28ec91b992.json)

[模型所见图](../pre_unified_preserved/assets/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_C_test/qwen3.8-27b/renders/5768a719fc18bc599f69e46bc1373acc1c32fcd9d610894486d79f28ec91b992_2.png)

## RQ3.7 · INC-C7962AC24637 · unchanged

aegislab / eval / service / ContainerKill。MRR 1.0000 → 1.0000。

评测标签（仅分析）：{"ts-order-service": "412"}

T_MATCH：["412", "7852", "224", "267"]

The abrupt drop in pod 412's memory usage and filesystem metrics to near-zero (bin 32) simultaneously with new 'Aborted connection' logs indicates a sudden container crash or node failure, not a gradual leak. The crash of pod 412, which is a callee for services 267, 285, 289, 524, and 526, temporally precedes the latency and error propagation observed in these callers and other services like 224 (CPU spike).

LOCAL_LINK：["412", "53061", "162"]

Metrics and topology verify that service 412 exhibited the root fault, with its memory metrics dropping to near-zero baseline and slowly recovering while its pod 53061 showed increased k8s.container.restarts, and the 'hosts' relationship ties node 7852 to this pod 53061. This rules out infrastructure co-location symptoms on the same node by prioritizing the specific pod restart and service-level memory anomaly as the causal origin over broader node-level effects.

[旧输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_A_development/qwen3.8-27b/outputs/55421148651b692f359d5d62afa15ff03c451fcecd94f40d5404eb861a4b60f4.json) · [新输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_A_development/qwen3.8-27b/outputs/93fbd7e6c8889297babf944d090fdeaf1ca5e3cf6523bb2cbb175ceaaafe9212.json) · [新输入](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_A_development/qwen3.8-27b/inputs/93fbd7e6c8889297babf944d090fdeaf1ca5e3cf6523bb2cbb175ceaaafe9212.json)

[模型所见图](../pre_unified_preserved/assets/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_A_development/qwen3.8-27b/renders/93fbd7e6c8889297babf944d090fdeaf1ca5e3cf6523bb2cbb175ceaaafe9212_2.png)

## RQ3.7 · INC-48C127B155B6 · unchanged

aiops2022 / eval / node / node 内存消耗。MRR 0.0000 → 0.0000。

评测标签（仅分析）：{"node-2": "9050"}

T_MATCH：["751", "710", "14973"]

TRC-L identifies service 751 (SendOrderConfirmation) as the origin with the highest rank score (10.24) and dominant exclusive latency deviation (~60s), indicating local processing failure rather than downstream propagation. MET-Z confirms this origin with a >3σ fluctuation in service 710 (file descriptors) at the earliest onset (+28m), which precedes the latency spikes in dependent services and is consistent with a resource exhaustion root cause in the 751/710 cluster.

LOCAL_LINK：["39945", "45382", "8305"]

The top candidate is verified by a decisive trace topology check where pod 39945 exhibits the highest rank_score (10.24) and its local exclusive latency increases by a 10.24 log2-fold, proving it is the origin of the delay rather than a downstream symptom; this is corroborated by a temporal check where its gRPC request latency spikes from a zero baseline starting at bin 46, preceding the global 33-minute fault onset. No alternative origin is supported, as the co-located pod 45382 shows a simultaneous latency spike without a preceding error or exclusive latency deviation, and the host node 8305 shows only minor metric fluctuations.

[旧输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_C_eval/qwen3.8-27b/outputs/d8595cedd7440e86613624fb400d370f108f623d74785a297c16e8fd6c6f8066.json) · [新输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_C_eval/qwen3.8-27b/outputs/910bd6b9633963d9643763af523b8d73bbdc0ca6d7e8a4c46aed41e885550677.json) · [新输入](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_C_eval/qwen3.8-27b/inputs/910bd6b9633963d9643763af523b8d73bbdc0ca6d7e8a4c46aed41e885550677.json)

[模型所见图](../pre_unified_preserved/assets/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_C_eval/qwen3.8-27b/renders/910bd6b9633963d9643763af523b8d73bbdc0ca6d7e8a4c46aed41e885550677_2.png)

## RQ3.7 · INC-9D1784608F61 · unchanged

aiops2025 / eval / node / node disk fill。MRR 1.0000 → 1.0000。

评测标签（仅分析）：{"node-8": "1847"}

T_MATCH：["1847", "29225", "1897"]

Node 1847 is the root cause as its filesystem usage spiked from ~54% to ~81% (MET-Z z=999) starting at bin 31 (+15m), preceding the severe memory spike (z=999) and disk reads on its hosted pod 29225, which serves as the primary symptom. Verification confirms 1847 is a leaf caller with no upstream dependencies in the provided graph and its temporal onset is earliest among all anomaly sources, ruling out pod-level memory faults as the origin.

LOCAL_LINK：["1847", "66109", "29225"]

Metrics show node 1847 experienced a simultaneous and massive filesystem saturation spike (+27sigma free_bytes, +217sigma usage_rate) that temporally aligned with the fault window, predating the subsequent 'DB saved on disk' volume drop observed in pod 66109. Topology evidence confirms pod 66109 is hosted directly by node 1847, and its trace/log anomalies represent the downstream consequence of the node-level disk exhaustion rather than an independent root cause.

[旧输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_A_development/qwen3.8-27b/outputs/f99b89dca8388d145a0a45f1f0cf689ebc9cecee19a9fb69a172c6d54d5369a5.json) · [新输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_A_development/qwen3.8-27b/outputs/d642110282f11a98fe60592c18583b788c08e4f6c8e4d71e4bc40314b8b47ac8.json) · [新输入](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_A_development/qwen3.8-27b/inputs/d642110282f11a98fe60592c18583b788c08e4f6c8e4d71e4bc40314b8b47ac8.json)

[模型所见图](../pre_unified_preserved/assets/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_A_development/qwen3.8-27b/renders/d642110282f11a98fe60592c18583b788c08e4f6c8e4d71e4bc40314b8b47ac8_2.png)

## RQ3.7 · INC-3E916629F15A · unchanged

aegislab / test / service / HTTPResponseReplaceBody。MRR 1.0000 → 1.0000。

评测标签（仅分析）：{"ts-basic-service": "959", "ts-route-service": "675"}

T_MATCH：["959", "702", "185"]

Service 959 is the root cause, evidenced by a massive filesystem usage spike (3.2M to 17.9M) and queue size increase (32 to 203) that align with its onset at +5.2m, preceding the latency explosions in its callees 702 and 185. The topology confirms 959 calls 796 and 802, but 959's own resource saturation (CPU/filesystem) explains the downstream delay, whereas 696's high trace latency is a downstream symptom as a caller of 959's upstream path or co-located impact, yet 959's metric anomalies are primary and earliest.

LOCAL_LINK：["959", "217", "696"]

Service 959 is the root origin, with confirmed filesystem usage and queueSize growing linearly to ~21.4MB/203 items starting around +5.5m. Service 217 exhibits the earliest max-intensity fault onset (rank 1, peak 10s) in the cascade and receives no upstream calls from the other affected candidates, supporting it as the fault manifestation point fed by the 959 anomaly.

[旧输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_C_test/qwen3.8-27b/outputs/93a9da88a238435f5adc72456dc20a14c8d2970011983616cacac92e2568e9d1.json) · [新输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_C_test/qwen3.8-27b/outputs/755c73f04021f58c60cdee56631955f824aa83064414efb725de4e208aea554d.json) · [新输入](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_C_test/qwen3.8-27b/inputs/755c73f04021f58c60cdee56631955f824aa83064414efb725de4e208aea554d.json)

[模型所见图](../pre_unified_preserved/assets/RQs/RQ3_7/results/fusion_v2_pruned/stages/formal_C_test/qwen3.8-27b/renders/755c73f04021f58c60cdee56631955f824aa83064414efb725de4e208aea554d_2.png)

## RQ3.8 · INC-B84269FDA98E · repair

aegislab / eval / service / HTTPRequestReplaceMethod。MRR 0.5000 → 1.0000。

评测标签（仅分析）：{"ts-basic-service": "428", "ts-station-service": "570"}

TEXT：["339", "428", "570", "628"]

The top candidate 339 is the root cause because it exhibits the earliest telemetry onset (+4.0m) and highest severity z-score (50.85) among the upstream callers, with no prior anomalies observed in its dependents 428 or 570. While 428 and 570 show significant latency and queue spikes, their onsets (+5.0m) occur after 339, and 654's severe latency is consistent with propagated downstream failure rather than an independent origin.

FULL：["428", "570", "339"]

Verification confirms that 428's p95 latency remains low (0.05s) while its downstream dependency 570 experiences a massive resource fault (queue size z=58.6, page faults z=20.0). The failure propagates from 570's degradation through 428 to caller 339, whose latency then explodes (z=50.85), identifying 428 as the primary component affected by the fault originating in 570.

[旧输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s0/outputs/184b09050d06a3c1b07dbc34d7700105d361e1ff174e235acd51fec63b8ec510.json) · [新输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s0/outputs/d3856d74a32c6460303b79e3c4da969fdf053ba572140186c4831e0043f79297.json) · [新输入](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s0/inputs/d3856d74a32c6460303b79e3c4da969fdf053ba572140186c4831e0043f79297.json)

[模型所见图](../through_RQ3_15_preserved/assets/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s0/renders/d3856d74a32c6460303b79e3c4da969fdf053ba572140186c4831e0043f79297_0.png)

- M01 / 628 / container.memory.available / source_unit: {"details": [{"name": "Reference mean", "value": "3.2G"}, {"name": "Current mean", "value": "3.2G"}, {"name": "Reference SD", "value": "7.5k"}, {"name": "Current SD", "value": "59.6k"}, {"name": "Deviation (sigma)", "value": "10"}]}
- M02 / 628 / container.memory.working_set / source_unit: {"details": [{"name": "Reference mean", "value": "9.1M"}, {"name": "Current mean", "value": "9.0M"}, {"name": "Reference SD", "value": "7.5k"}, {"name": "Current SD", "value": "59.6k"}, {"name": "Deviation (sigma)", "value": "10"}]}
- M03 / 339 / hubble_http_request_duration_p50_seconds / milliseconds_or_source_unit: {"details": [{"name": "Reference mean", "value": "1.02"}, {"name": "Current mean", "value": "4.91"}, {"name": "Reference SD", "value": "2.14"}, {"name": "Current SD", "value": "2.52"}, {"name": "Deviation (sigma)", "value": "1.82"}]}
- M04 / 628 / container.memory.rss / source_unit: {"details": [{"name": "Reference mean", "value": "8.1M"}, {"name": "Current mean", "value": "8.0M"}, {"name": "Reference SD", "value": "2.9k"}, {"name": "Current SD", "value": "60.2k"}, {"name": "Deviation (sigma)", "value": "30"}]}
- M05 / 570 / queueSize / source_unit: {"details": [{"name": "Reference mean", "value": "2.74"}, {"name": "Current mean", "value": "127"}, {"name": "Reference SD", "value": "2.36"}, {"name": "Current SD", "value": "37"}, {"name": "Deviation (sigma)", "value": "53"}]}
- M06 / 453 / hubble_http_request_duration_p50_seconds / milliseconds_or_source_unit: {"details": [{"name": "Reference mean", "value": "0.35"}, {"name": "Current mean", "value": "10"}, {"name": "Reference SD", "value": "0.31"}, {"name": "Current SD", "value": "0.0e+00"}, {"name": "Deviation (sigma)", "value": "31"}]}
- M07 / 628 / container.memory.usage / source_unit: {"details": [{"name": "Reference mean", "value": "9.1M"}, {"name": "Current mean", "value": "9.0M"}, {"name": "Reference SD", "value": "7.5k"}, {"name": "Current SD", "value": "59.6k"}, {"name": "Deviation (sigma)", "value": "10"}]}
- M08 / 530 / k8s.pod.memory.page_faults / source_unit: {"details": [{"name": "Reference mean", "value": "156.2k"}, {"name": "Current mean", "value": "164.9k"}, {"name": "Reference SD", "value": "3.4k"}, {"name": "Current SD", "value": "31"}, {"name": "Deviation (sigma)", "value": "2.57"}]}
- M09 / 124 / hubble_http_request_duration_p50_seconds / milliseconds_or_source_unit: {"details": [{"name": "Reference mean", "value": "0.62"}, {"name": "Current mean", "value": "10"}, {"name": "Reference SD", "value": "0.40"}, {"name": "Current SD", "value": "0.0e+00"}, {"name": "Deviation (sigma)", "value": "24"}]}
- M10 / 570 / k8s.pod.filesystem.usage / source_unit: {"details": [{"name": "Reference mean", "value": "781.9k"}, {"name": "Current mean", "value": "1.2M"}, {"name": "Reference SD", "value": "53.2k"}, {"name": "Current SD", "value": "182.8k"}, {"name": "Deviation (sigma)", "value": "7.90"}]}
- M11 / 628 / k8s.pod.memory.rss / source_unit: {"details": [{"name": "Reference mean", "value": "8.2M"}, {"name": "Current mean", "value": "8.1M"}, {"name": "Reference SD", "value": "3.0k"}, {"name": "Current SD", "value": "60.2k"}, {"name": "Deviation (sigma)", "value": "26"}]}
- M12 / 428 / k8s.pod.filesystem.usage / source_unit: {"details": [{"name": "Reference mean", "value": "5.1M"}, {"name": "Current mean", "value": "17.9M"}, {"name": "Reference SD", "value": "1.6M"}, {"name": "Current SD", "value": "2.9M"}, {"name": "Deviation (sigma)", "value": "8.12"}]}
- R01 / 654 / POST /api/v1/travel2service/trips/left / µs: {"after": 7624393.79, "before": 17088.24, "details": [{"name": "Reference requests", "value": "76"}, {"name": "Current requests", "value": "5"}, {"name": "Current inclusive p95 (µs)", "value": "20002086.12"}, {"name": "Request log2 ratio", "value": "-3.68"}, {"name": "Latency log2 ratio", "value": "8.8"}]}
- R02 / 246 / POST / µs: {"after": 3854738.5, "before": 41444.22, "details": [{"name": "Reference requests", "value": "519"}, {"name": "Current requests", "value": "39"}, {"name": "Current inclusive p95 (µs)", "value": "4070690.47"}, {"name": "Request log2 ratio", "value": "-3.7"}, {"name": "Latency log2 ratio", "value": "6.54"}]}
- R03 / 453 / POST / µs: {"after": 15880966.63, "before": 47072.39, "details": [{"name": "Reference requests", "value": "277"}, {"name": "Current requests", "value": "23"}, {"name": "Current inclusive p95 (µs)", "value": "60004771.71"}, {"name": "Request log2 ratio", "value": "-3.53"}, {"name": "Latency log2 ratio", "value": "8.4"}]}
- R04 / 654 / POST /api/v1/travelplanservice/travelPlan/quickest / µs: {"after": 16000915.68, "before": 5222.79, "details": [{"name": "Reference requests", "value": "31"}, {"name": "Current requests", "value": "5"}, {"name": "Current inclusive p95 (µs)", "value": "20003603.34"}, {"name": "Request log2 ratio", "value": "-2.42"}, {"name": "Latency log2 ratio", "value": "11.58"}]}
- R05 / 654 / GET /api/v1/foodservice/foods/2025-08-19/shanghai/taiyuan/Z1234 / µs: {"after": 1020571.96, "before": 5021.73, "details": [{"name": "Reference requests", "value": "18"}, {"name": "Current requests", "value": "1"}, {"name": "Current inclusive p95 (µs)", "value": "1036939.48"}, {"name": "Request log2 ratio", "value": "-3.25"}, {"name": "Latency log2 ratio", "value": "7.67"}]}
- R06 / 654 / GET /api/v1/consignservice/consigns/account/4d2a46c7-71cb-4cf1-b5bb-b68406d9da6f / µs: {"after": 1025134.71, "before": 15531.88, "details": [{"name": "Reference requests", "value": "54"}, {"name": "Current requests", "value": "5"}, {"name": "Current inclusive p95 (µs)", "value": "1036850.0"}, {"name": "Request log2 ratio", "value": "-3.2"}, {"name": "Latency log2 ratio", "value": "6.04"}]}

## RQ3.8 · INC-BA41A280E858 · repair

aiops2022 / eval / pod / k8s容器读io负载。MRR 0.5000 → 1.0000。

评测标签（仅分析）：{"adservice-0": "46218"}

TEXT：["5360", "46218", "919"]

Node 5360 is the confirmed root cause as its system.io.await metric jumped 27x (0.48 to 13.18) during the fault window, triggering the disk usage spike to 626MB and memory increase observed in pod 46218. This local resource exhaustion on node 5360 explains the early latency spikes in service 411 and its callees (2660, 621) starting at +20.0m, preceding the secondary propagation to downstream services like 833 and 919.

FULL：["46218", "5360", "919"]

The metrics show a sudden disk usage spike (bin 32) and working-set jump on pod 46218 that occurred before the Tenured-Gen step changes in service 919, satisfying the earliest-onset check; this origin is supported by the trace evidence, as the 7.1x exclusive p95 degradation in hipstershop.234/EmptyCart is centered on node 5360 (where 46218 runs) with no higher-latency anomaly on the 919 instance in the same window, ruling 919 out as a co-located symptom rather than the origin.

[旧输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s2/outputs/947ec64d841aeeebad88d982b1f301f262cee530ce9719a92e5d3715f34148da.json) · [新输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s2/outputs/de8be0c12c1f22714bd39668fdb0e3a516f25cecf4debd2dd8291509983733f4.json) · [新输入](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s2/inputs/de8be0c12c1f22714bd39668fdb0e3a516f25cecf4debd2dd8291509983733f4.json)

[模型所见图](../through_RQ3_15_preserved/assets/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s2/renders/de8be0c12c1f22714bd39668fdb0e3a516f25cecf4debd2dd8291509983733f4_0.png)

- M01 / 919 / jvm_memory_pool_allocated_MB_total.Tenured_Gen / source_unit: {"details": [{"name": "Reference mean", "value": "134"}, {"name": "Current mean", "value": "134"}, {"name": "Reference SD", "value": "1.0e-04"}, {"name": "Current SD", "value": "0.09"}, {"name": "Deviation (sigma)", "value": "540"}]}
- M02 / 77551 / container_network_receive_MB.eth0 / source_unit: {"details": [{"name": "Reference mean", "value": "0.02"}, {"name": "Current mean", "value": "0.05"}, {"name": "Reference SD", "value": "2.9e-03"}, {"name": "Current SD", "value": "0.12"}, {"name": "Deviation (sigma)", "value": "9.03"}]}
- M03 / 46218 / container_fs_inodes./dev/vda1 / source_unit: {"details": [{"name": "Reference mean", "value": "0.0e+00"}, {"name": "Current mean", "value": "0.14"}, {"name": "Reference SD", "value": "0.0e+00"}, {"name": "Current SD", "value": "0.64"}]}
- M04 / 25634 / container_network_receive_MB.eth0 / source_unit: {"details": [{"name": "Reference mean", "value": "0.02"}, {"name": "Current mean", "value": "0.05"}, {"name": "Reference SD", "value": "2.9e-03"}, {"name": "Current SD", "value": "0.11"}, {"name": "Deviation (sigma)", "value": "8.76"}]}
- M05 / 919 / jvm_memory_pool_MB_used.Tenured_Gen / source_unit: {"details": [{"name": "Reference mean", "value": "53"}, {"name": "Current mean", "value": "53"}, {"name": "Reference SD", "value": "1.0e-04"}, {"name": "Current SD", "value": "0.09"}, {"name": "Deviation (sigma)", "value": "549"}]}
- M06 / 46519 / container_network_receive_MB.eth0 / source_unit: {"details": [{"name": "Reference mean", "value": "0.02"}, {"name": "Current mean", "value": "0.04"}, {"name": "Reference SD", "value": "1.6e-03"}, {"name": "Current SD", "value": "0.11"}, {"name": "Deviation (sigma)", "value": "15"}]}
- M07 / 919 / java_lang_GarbageCollector_LastGcInfo_memoryUsageAfterGc_used.Tenured_Gen.Copy / source_unit: {"details": [{"name": "Reference mean", "value": "56.0M"}, {"name": "Current mean", "value": "56.0M"}, {"name": "Reference SD", "value": "106"}, {"name": "Current SD", "value": "90.1k"}, {"name": "Deviation (sigma)", "value": "540"}]}
- M08 / 919 / java_lang_MemoryPool_Usage_used.Tenured_Gen / source_unit: {"details": [{"name": "Reference mean", "value": "56.0M"}, {"name": "Current mean", "value": "56.0M"}, {"name": "Reference SD", "value": "106"}, {"name": "Current SD", "value": "90.1k"}, {"name": "Deviation (sigma)", "value": "540"}]}
- M09 / 70692 / container_cpu_cfs_throttled_seconds / source_unit: {"details": [{"name": "Reference mean", "value": "9.6e-14"}, {"name": "Current mean", "value": "1.4e-04"}, {"name": "Reference SD", "value": "2.8e-13"}, {"name": "Current SD", "value": "4.3e-04"}, {"name": "Deviation (sigma)", "value": "497.7M"}]}
- M10 / 2660 / system.net.bytes_rcvd / source_unit: {"details": [{"name": "Reference mean", "value": "96.5k"}, {"name": "Current mean", "value": "146.5k"}, {"name": "Reference SD", "value": "3.5k"}, {"name": "Current SD", "value": "112.8k"}, {"name": "Deviation (sigma)", "value": "14"}]}
- M11 / 919 / java_lang_GarbageCollector_LastGcInfo_memoryUsageBeforeGc_used.Tenured_Gen.Copy / source_unit: {"details": [{"name": "Reference mean", "value": "56.0M"}, {"name": "Current mean", "value": "56.0M"}, {"name": "Reference SD", "value": "109"}, {"name": "Current SD", "value": "86.6k"}, {"name": "Deviation (sigma)", "value": "499"}]}
- M12 / 46218 / container_fs_usage_MB./dev/vda1 / source_unit: {"details": [{"name": "Reference mean", "value": "23"}, {"name": "Current mean", "value": "197"}, {"name": "Reference SD", "value": "0.0e+00"}, {"name": "Current SD", "value": "271"}]}
- R01 / 41677 / hipstershop.234/EmptyCart / µs: {"after": 28953.0, "before": 4062.4, "details": [{"name": "Reference requests", "value": "29"}, {"name": "Current requests", "value": "30"}, {"name": "Current inclusive p95 (µs)", "value": "28953.0"}, {"name": "Request log2 ratio", "value": "0.05"}, {"name": "Latency log2 ratio", "value": "2.83"}]}
- R02 / 26128 / hipstershop.848/GetQuote / µs: {"after": 104.5, "before": 79.9, "details": [{"name": "Reference requests", "value": "142"}, {"name": "Current requests", "value": "150"}, {"name": "Current inclusive p95 (µs)", "value": "104.5"}, {"name": "Request log2 ratio", "value": "0.08"}, {"name": "Latency log2 ratio", "value": "0.38"}]}
- R03 / 71446 / hipstershop.234/EmptyCart / µs: {"after": 4517.4, "before": 3650.25, "details": [{"name": "Reference requests", "value": "24"}, {"name": "Current requests", "value": "25"}, {"name": "Current inclusive p95 (µs)", "value": "4517.4"}, {"name": "Request log2 ratio", "value": "0.06"}, {"name": "Latency log2 ratio", "value": "0.31"}]}
- R04 / 32534 / hipstershop.579/SendOrderConfirmation / µs: {"after": 46195.0, "before": 16778.35, "details": [{"name": "Reference requests", "value": "24"}, {"name": "Current requests", "value": "25"}, {"name": "Current inclusive p95 (µs)", "value": "46432.4"}, {"name": "Request log2 ratio", "value": "0.06"}, {"name": "Latency log2 ratio", "value": "1.46"}]}
- R05 / 93550 / /hipstershop.234/AddItem / µs: {"after": 1000.0, "before": 1000.0, "details": [{"name": "Reference requests", "value": "34"}, {"name": "Current requests", "value": "48"}, {"name": "Current inclusive p95 (µs)", "value": "1000.0"}, {"name": "Request log2 ratio", "value": "0.49"}, {"name": "Latency log2 ratio", "value": "0.0"}]}
- R06 / 32534 / hipstershop.862/Charge / µs: {"after": 4868.8, "before": 3274.55, "details": [{"name": "Reference requests", "value": "24"}, {"name": "Current requests", "value": "25"}, {"name": "Current inclusive p95 (µs)", "value": "5003.0"}, {"name": "Request log2 ratio", "value": "0.06"}, {"name": "Latency log2 ratio", "value": "0.57"}]}

## RQ3.8 · INC-D02CFDF1A4AE · repair

aiops2025 / eval / service / network loss。MRR 0.3333 → 0.5000。

评测标签（仅分析）：{"checkoutservice": "980", "frontend": "211"}

TEXT：["3473", "622", "19602"]

Node 3473 is the root cause as its memory usage and disk write metrics exhibit a sustained deviation starting at +32m that temporally aligns with the onset of the incident; the topology confirms that the affected services, such as 622, are hosted on this node, making the infrastructure failure the origin of the downstream symptom in 622 and its callers.

FULL：["791", "211", "980"]

Top-1 791 survives two checks: (1) the top callers' PlaceOrder span to 980 holds a 60s timeout ceiling with an exclusive-latency log2 ratio of 0.0, and 791 is the parent of every degraded trace, excluding 980/211 as local origins; (2) 791's rrt_max median jumps ~200× (305k→60.0M) with onset at +28.0m and a low client_error_ratio (~0.05), the latency-stall signature of a root, so the co-occurring 980 error-ratio spike and downstream 544/364/691 count drops are consistent consequences rather than an alternate origin.

[旧输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s0/outputs/7af2f270643ee61ec171c2345399270644e09d2ccfa85843c2af8c0b80114646.json) · [新输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s0/outputs/527a9cb8f9e59bf882de443528f1891cb4701ba55b9a7650cf6a3304aa6f73f2.json) · [新输入](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s0/inputs/527a9cb8f9e59bf882de443528f1891cb4701ba55b9a7650cf6a3304aa6f73f2.json)

[模型所见图](../through_RQ3_15_preserved/assets/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s0/renders/527a9cb8f9e59bf882de443528f1891cb4701ba55b9a7650cf6a3304aa6f73f2_0.png)

- M01 / 19602 / error_ratio / ratio_or_percent: {"details": [{"name": "Reference mean", "value": "0.12"}, {"name": "Current mean", "value": "12"}, {"name": "Reference SD", "value": "0.49"}, {"name": "Current SD", "value": "6.93"}, {"name": "Deviation (sigma)", "value": "24"}]}
- M02 / 791 / client_error_ratio / ratio_or_percent: {"details": [{"name": "Reference mean", "value": "0.04"}, {"name": "Current mean", "value": "0.12"}, {"name": "Reference SD", "value": "0.07"}, {"name": "Current SD", "value": "0.29"}, {"name": "Deviation (sigma)", "value": "1.12"}]}
- M03 / 980 / client_error_ratio / ratio_or_percent: {"details": [{"name": "Reference mean", "value": "0.12"}, {"name": "Current mean", "value": "11"}, {"name": "Reference SD", "value": "0.49"}, {"name": "Current SD", "value": "6.98"}, {"name": "Deviation (sigma)", "value": "22"}]}
- M04 / 34190 / pod_processes / source_unit: {"details": [{"name": "Reference mean", "value": "1.00"}, {"name": "Current mean", "value": "1.06"}, {"name": "Reference SD", "value": "0.0e+00"}, {"name": "Current SD", "value": "0.24"}]}
- M05 / 76273 / client_error_ratio / ratio_or_percent: {"details": [{"name": "Reference mean", "value": "0.0e+00"}, {"name": "Current mean", "value": "45"}, {"name": "Reference SD", "value": "0.0e+00"}, {"name": "Current SD", "value": "24"}]}
- M06 / 3473 / node_memory_usage_rate / ratio_or_percent: {"details": [{"name": "Reference mean", "value": "68"}, {"name": "Current mean", "value": "66"}, {"name": "Reference SD", "value": "0.43"}, {"name": "Current SD", "value": "4.52"}, {"name": "Deviation (sigma)", "value": "4.01"}]}
- M07 / 3473 / node_memory_MemAvailable_bytes / source_unit: {"details": [{"name": "Reference mean", "value": "10.1G"}, {"name": "Current mean", "value": "10.7G"}, {"name": "Reference SD", "value": "145.7M"}, {"name": "Current SD", "value": "1.5G"}, {"name": "Deviation (sigma)", "value": "4.01"}]}
- M08 / 980 / error_ratio / ratio_or_percent: {"details": [{"name": "Reference mean", "value": "0.12"}, {"name": "Current mean", "value": "11"}, {"name": "Reference SD", "value": "0.49"}, {"name": "Current SD", "value": "6.98"}, {"name": "Deviation (sigma)", "value": "22"}]}
- M09 / 19602 / client_error_ratio / ratio_or_percent: {"details": [{"name": "Reference mean", "value": "0.12"}, {"name": "Current mean", "value": "12"}, {"name": "Reference SD", "value": "0.49"}, {"name": "Current SD", "value": "6.93"}, {"name": "Deviation (sigma)", "value": "24"}]}
- M10 / 49082 / client_error_ratio / ratio_or_percent: {"details": [{"name": "Reference mean", "value": "0.0e+00"}, {"name": "Current mean", "value": "45"}, {"name": "Reference SD", "value": "0.0e+00"}, {"name": "Current SD", "value": "25"}]}
- M11 / 791 / error_ratio / ratio_or_percent: {"details": [{"name": "Reference mean", "value": "0.06"}, {"name": "Current mean", "value": "0.23"}, {"name": "Reference SD", "value": "0.07"}, {"name": "Current SD", "value": "0.31"}, {"name": "Deviation (sigma)", "value": "2.22"}]}
- M12 / 3473 / node_disk_written_bytes_total / source_unit: {"details": [{"name": "Reference mean", "value": "26.7k"}, {"name": "Current mean", "value": "58.6k"}, {"name": "Reference SD", "value": "5.2k"}, {"name": "Current SD", "value": "69.4k"}, {"name": "Deviation (sigma)", "value": "6.13"}]}
- R01 / 364 / 791.364/GetAds / µs: {"after": 7754.5, "before": 7647.2, "details": [{"name": "Reference requests", "value": "1437"}, {"name": "Current requests", "value": "791"}, {"name": "Current inclusive p95 (µs)", "value": "7754.5"}, {"name": "Request log2 ratio", "value": "-0.86"}, {"name": "Latency log2 ratio", "value": "0.02"}]}
- R02 / 544 / 791.544/ListProducts / µs: {"after": 2013.8, "before": 1903.0, "details": [{"name": "Reference requests", "value": "2283"}, {"name": "Current requests", "value": "1205"}, {"name": "Current inclusive p95 (µs)", "value": "2101.4"}, {"name": "Request log2 ratio", "value": "-0.92"}, {"name": "Latency log2 ratio", "value": "0.08"}]}
- R03 / 347 / /791.347/ListRecommendations / µs: {"after": 1503.85, "before": 1473.85, "details": [{"name": "Reference requests", "value": "1704"}, {"name": "Current requests", "value": "888"}, {"name": "Current inclusive p95 (µs)", "value": "5070.0"}, {"name": "Request log2 ratio", "value": "-0.94"}, {"name": "Latency log2 ratio", "value": "0.03"}]}
- R04 / 980 / 791.980/PlaceOrder / µs: {"after": 60000689.4, "before": 59854496.0, "details": [{"name": "Reference requests", "value": "177"}, {"name": "Current requests", "value": "62"}, {"name": "Current inclusive p95 (µs)", "value": "60000689.4"}, {"name": "Request log2 ratio", "value": "-1.5"}, {"name": "Latency log2 ratio", "value": "0.0"}]}
- R05 / 544 / 791.544/GetProduct / µs: {"after": 12962.55, "before": 12671.6, "details": [{"name": "Reference requests", "value": "21698"}, {"name": "Current requests", "value": "11230"}, {"name": "Current inclusive p95 (µs)", "value": "15789.65"}, {"name": "Request log2 ratio", "value": "-0.95"}, {"name": "Latency log2 ratio", "value": "0.03"}]}
- R06 / 691 / 791.691/AddItem / µs: {"after": 2326.75, "before": 2231.9, "details": [{"name": "Reference requests", "value": "194"}, {"name": "Current requests", "value": "102"}, {"name": "Current inclusive p95 (µs)", "value": "5742.0"}, {"name": "Request log2 ratio", "value": "-0.92"}, {"name": "Latency log2 ratio", "value": "0.06"}]}

## RQ3.8 · INC-840F977CC454 · repair

aegislab / test / service / HTTPRequestReplaceMethod。MRR 0.0000 → 0.5000。

评测标签（仅分析）：{"ts-food-service": "626", "ts-train-food-service": "277"}

TEXT：["330", "415", "235"]

Service 330 exhibits a dominant, isolated resource exhaustion (CPU spike >46σ) in the metrics (M) that is temporally distinct and uncorrelated with the downstream latency propagation. The proposed alternative origin, service 415, is contradicted by topology (G), as 330 is a leaf node with no outgoing call edges to the affected cluster containing 415. The delay in 415's latency onset (+4.2m) relative to 330's resource anomaly (+4.5m) and the lack of a causal link in the call graph support 330 as the independent root cause of the resource fault.

FULL：["722", "277", "626"]

Top-1 722 survives two checks: (1) the top-ranked exclusive-latency jump is local to 722 (e.g., GET consigns 3.1 ms→1.03 s, log2 +8.37), and its fan-out callers/callees (415, 512, 644, 235, 626) show co-occurring R/M anomalies consistent with 722 being the origin rather than a downstream; (2) the alternative earliest onset 968 has only a weak z-score (143.5, rank 1 but moderate) and no local exclusive-latency explosion in R (only 722/626 ops appear), so 968 is an early symptom, not the source. Decisive relation: 722's local-time blowup precedes and precedes-in-time its outbound edges to 415/512/235, which then surface downstream, while 330's metric spike is a co-located infra symptom not linked by a call path.

[旧输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s1/outputs/b15a690740e76711d6799b24fba36380549d8188496d7b2a94f4cec2278bc404.json) · [新输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s1/outputs/32d0db64668fb035eeda50b1d591a10870741b9dab1953a4a6279ad9fbeb681a.json) · [新输入](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s1/inputs/32d0db64668fb035eeda50b1d591a10870741b9dab1953a4a6279ad9fbeb681a.json)

[模型所见图](../through_RQ3_15_preserved/assets/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s1/renders/32d0db64668fb035eeda50b1d591a10870741b9dab1953a4a6279ad9fbeb681a_0.png)

- M01 / 330 / k8s.pod.cpu.node.utilization / ratio_or_percent: {"details": [{"name": "Reference mean", "value": "4.0e-05"}, {"name": "Current mean", "value": "2.6e-04"}, {"name": "Reference SD", "value": "4.8e-06"}, {"name": "Current SD", "value": "6.5e-04"}, {"name": "Deviation (sigma)", "value": "46"}]}
- M02 / 330 / container.cpu.usage / source_unit: {"details": [{"name": "Reference mean", "value": "5.2e-03"}, {"name": "Current mean", "value": "0.03"}, {"name": "Reference SD", "value": "5.9e-04"}, {"name": "Current SD", "value": "0.06"}, {"name": "Deviation (sigma)", "value": "39"}]}
- M03 / 330 / container.memory.rss / source_unit: {"details": [{"name": "Reference mean", "value": "692.5M"}, {"name": "Current mean", "value": "696.9M"}, {"name": "Reference SD", "value": "45.4k"}, {"name": "Current SD", "value": "379.3k"}, {"name": "Deviation (sigma)", "value": "97"}]}
- M04 / 330 / jvm.cpu.recent_utilization / ratio_or_percent: {"details": [{"name": "Reference mean", "value": "4.1e-05"}, {"name": "Current mean", "value": "1.8e-04"}, {"name": "Reference SD", "value": "3.9e-06"}, {"name": "Current SD", "value": "2.3e-04"}, {"name": "Deviation (sigma)", "value": "34"}]}
- M05 / 330 / k8s.pod.memory.rss / source_unit: {"details": [{"name": "Reference mean", "value": "692.5M"}, {"name": "Current mean", "value": "697.0M"}, {"name": "Reference SD", "value": "49.7k"}, {"name": "Current SD", "value": "16.0k"}, {"name": "Deviation (sigma)", "value": "91"}]}
- M06 / 330 / container.memory.working_set / source_unit: {"details": [{"name": "Reference mean", "value": "702.7M"}, {"name": "Current mean", "value": "707.2M"}, {"name": "Reference SD", "value": "71.5k"}, {"name": "Current SD", "value": "378.6k"}, {"name": "Deviation (sigma)", "value": "62"}]}
- M07 / 330 / k8s.pod.cpu_limit_utilization / ratio_or_percent: {"details": [{"name": "Reference mean", "value": "1.0e-03"}, {"name": "Current mean", "value": "6.7e-03"}, {"name": "Reference SD", "value": "1.2e-04"}, {"name": "Current SD", "value": "0.02"}, {"name": "Deviation (sigma)", "value": "46"}]}
- M08 / 415 / hubble_http_request_duration_p95_seconds / milliseconds_or_source_unit: {"details": [{"name": "Reference mean", "value": "0.12"}, {"name": "Current mean", "value": "0.57"}, {"name": "Reference SD", "value": "0.38"}, {"name": "Current SD", "value": "0.78"}, {"name": "Deviation (sigma)", "value": "1.20"}]}
- M09 / 330 / container.memory.available / source_unit: {"details": [{"name": "Reference mean", "value": "2.5G"}, {"name": "Current mean", "value": "2.5G"}, {"name": "Reference SD", "value": "71.5k"}, {"name": "Current SD", "value": "378.6k"}, {"name": "Deviation (sigma)", "value": "62"}]}
- M10 / 330 / k8s.pod.cpu.usage / source_unit: {"details": [{"name": "Reference mean", "value": "5.2e-03"}, {"name": "Current mean", "value": "0.03"}, {"name": "Reference SD", "value": "6.2e-04"}, {"name": "Current SD", "value": "0.08"}, {"name": "Deviation (sigma)", "value": "46"}]}
- M11 / 330 / container.memory.usage / source_unit: {"details": [{"name": "Reference mean", "value": "703.1M"}, {"name": "Current mean", "value": "707.5M"}, {"name": "Reference SD", "value": "71.5k"}, {"name": "Current SD", "value": "378.6k"}, {"name": "Deviation (sigma)", "value": "62"}]}
- M12 / 330 / k8s.pod.memory_limit_utilization / ratio_or_percent: {"details": [{"name": "Reference mean", "value": "0.22"}, {"name": "Current mean", "value": "0.22"}, {"name": "Reference SD", "value": "2.4e-05"}, {"name": "Current SD", "value": "4.0e-06"}, {"name": "Deviation (sigma)", "value": "57"}]}
- R01 / 722 / GET /api/v1/consignservice/consigns/account/4d2a46c7-71cb-4cf1-b5bb-b68406d9da6f / µs: {"after": 1031970.37, "before": 3125.83, "details": [{"name": "Reference requests", "value": "74"}, {"name": "Current requests", "value": "3"}, {"name": "Current inclusive p95 (µs)", "value": "1038832.68"}, {"name": "Request log2 ratio", "value": "-4.23"}, {"name": "Latency log2 ratio", "value": "8.37"}]}
- R02 / 626 / GET /api/v1/foodservice/foods/{date}/{startStation}/{endStation}/{tripId} / µs: {"after": 37000.89, "before": 2815.77, "details": [{"name": "Reference requests", "value": "355"}, {"name": "Current requests", "value": "19"}, {"name": "Current inclusive p95 (µs)", "value": "193566085.71"}, {"name": "Request log2 ratio", "value": "-4.15"}, {"name": "Latency log2 ratio", "value": "3.72"}]}
- R03 / 626 / FoodController.getAllFood / µs: {"after": 193522231.42, "before": 6246.21, "details": [{"name": "Reference requests", "value": "355"}, {"name": "Current requests", "value": "19"}, {"name": "Current inclusive p95 (µs)", "value": "193536413.31"}, {"name": "Request log2 ratio", "value": "-4.15"}, {"name": "Latency log2 ratio", "value": "14.92"}]}
- R04 / 722 / POST /api/v1/travelservice/trips/left / µs: {"after": 762542.61, "before": 8944.97, "details": [{"name": "Reference requests", "value": "143"}, {"name": "Current requests", "value": "6"}, {"name": "Current inclusive p95 (µs)", "value": "875329.11"}, {"name": "Request log2 ratio", "value": "-4.36"}, {"name": "Latency log2 ratio", "value": "6.41"}]}
- R05 / 722 / GET /api/v1/foodservice/foods/2025-07-24/nanjing/shanghai/G1234 / µs: {"after": 15797786.54, "before": 2649.29, "details": [{"name": "Reference requests", "value": "30"}, {"name": "Current requests", "value": "1"}, {"name": "Current inclusive p95 (µs)", "value": "20000007.45"}, {"name": "Request log2 ratio", "value": "-3.95"}, {"name": "Latency log2 ratio", "value": "12.54"}]}
- R06 / 722 / POST /api/v1/orderOtherService/orderOther/refresh / µs: {"after": 153091.75, "before": 4570.93, "details": [{"name": "Reference requests", "value": "430"}, {"name": "Current requests", "value": "18"}, {"name": "Current inclusive p95 (µs)", "value": "158509.14"}, {"name": "Request log2 ratio", "value": "-4.5"}, {"name": "Latency log2 ratio", "value": "5.07"}]}

## RQ3.8 · INC-4628F1A41C33 · repair

aiops2022 / test / service / k8s容器内存负载。MRR 0.0000 → 0.5000。

评测标签（仅分析）：{"recommendationservice": "564"}

TEXT：["4043", "377", "138"]

Node 4043 is the origin, confirmed by the collapse of its free memory to 6.14% and the consequent 61x spike in container memory_cache on hosted pods, which contradicts the hypothesis of a pure software fault. The temporal onset at +19.1m in service 138 precedes the infrastructure degradation, aligning with a memory leak in 138's instance (pod 33547) that exhausted node 4043's resources, causing downstream latency in 377.

FULL：["4043", "564", "37514", "97858"]

Verified (1) the top candidate 4043 shows a decisive node-level memory divergence (system.mem.free spiking ~3.1k→4.8k while real.pct_useage drops ~80→55) at +22m, and (2) via G02 it hosts the affected pods 37514 (FS jumps ~41→65 MB) and 97858 (mapped-file 0→135k), confirming a co-located infrastructure fault upstream of the 584 Tenured-Gen saturation (and contradicting a 377-origin hypothesis, since 377 is late at +38m and only calls into the faulty pods).

[旧输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s1/outputs/974b0a9676f27e1992b361aa07e9145dbd19523c42658d8ca3f1d587908e8845.json) · [新输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s1/outputs/bdebe4f8383bad7921363f5d683615006322d99b341e972dc02cf6ffac6d0cf4.json) · [新输入](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s1/inputs/bdebe4f8383bad7921363f5d683615006322d99b341e972dc02cf6ffac6d0cf4.json)

[模型所见图](../through_RQ3_15_preserved/assets/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s1/renders/bdebe4f8383bad7921363f5d683615006322d99b341e972dc02cf6ffac6d0cf4_0.png)

- M01 / 42903 / container_network_receive_MB.eth0 / source_unit: {"details": [{"name": "Reference mean", "value": "0.02"}, {"name": "Current mean", "value": "0.05"}, {"name": "Reference SD", "value": "1.6e-03"}, {"name": "Current SD", "value": "0.13"}, {"name": "Deviation (sigma)", "value": "17"}]}
- M02 / 584 / jvm_memory_pool_allocated_MB_total.Tenured_Gen / source_unit: {"details": [{"name": "Reference mean", "value": "28"}, {"name": "Current mean", "value": "28"}, {"name": "Reference SD", "value": "2.8e-04"}, {"name": "Current SD", "value": "0.04"}, {"name": "Deviation (sigma)", "value": "646"}]}
- M03 / 584 / java_lang_GarbageCollector_LastGcInfo_memoryUsageAfterGc_used.Tenured_Gen.Copy / source_unit: {"details": [{"name": "Reference mean", "value": "22.7M"}, {"name": "Current mean", "value": "22.9M"}, {"name": "Reference SD", "value": "295"}, {"name": "Current SD", "value": "46.0k"}, {"name": "Deviation (sigma)", "value": "646"}]}
- M04 / 4428 / system.mem.real.pct_useage / source_unit: {"details": [{"name": "Reference mean", "value": "80"}, {"name": "Current mean", "value": "55"}, {"name": "Reference SD", "value": "0.31"}, {"name": "Current SD", "value": "15"}, {"name": "Deviation (sigma)", "value": "83"}]}
- M05 / 584 / jvm_memory_pool_MB_used.Tenured_Gen / source_unit: {"details": [{"name": "Reference mean", "value": "22"}, {"name": "Current mean", "value": "22"}, {"name": "Reference SD", "value": "2.8e-04"}, {"name": "Current SD", "value": "0.04"}, {"name": "Deviation (sigma)", "value": "642"}]}
- M06 / 9639 / system.net.tcp.retrans_segs / source_unit: {"details": [{"name": "Reference mean", "value": "0.03"}, {"name": "Current mean", "value": "0.34"}, {"name": "Reference SD", "value": "0.03"}, {"name": "Current SD", "value": "1.46"}, {"name": "Deviation (sigma)", "value": "12"}]}
- M07 / 4428 / system.mem.free / source_unit: {"details": [{"name": "Reference mean", "value": "3.1k"}, {"name": "Current mean", "value": "4.8k"}, {"name": "Reference SD", "value": "31"}, {"name": "Current SD", "value": "5.1k"}, {"name": "Deviation (sigma)", "value": "54"}]}
- M08 / 54840 / container_cpu_system_seconds / source_unit: {"details": [{"name": "Reference mean", "value": "1.2e-17"}, {"name": "Current mean", "value": "4.8e-04"}, {"name": "Reference SD", "value": "5.0e-17"}, {"name": "Current SD", "value": "1.5e-03"}, {"name": "Deviation (sigma)", "value": "9604.1G"}]}
- M09 / 37514 / container_fs_usage_MB./dev/vda1 / source_unit: {"details": [{"name": "Reference mean", "value": "41"}, {"name": "Current mean", "value": "64"}, {"name": "Reference SD", "value": "0.03"}, {"name": "Current SD", "value": "5.04"}, {"name": "Deviation (sigma)", "value": "748"}]}
- M10 / 584 / java_lang_MemoryPool_PeakUsage_used.Tenured_Gen / source_unit: {"details": [{"name": "Reference mean", "value": "22.7M"}, {"name": "Current mean", "value": "22.9M"}, {"name": "Reference SD", "value": "294"}, {"name": "Current SD", "value": "46.0k"}, {"name": "Deviation (sigma)", "value": "648"}]}
- M11 / 584 / java_lang_MemoryPool_Usage_used.Tenured_Gen / source_unit: {"details": [{"name": "Reference mean", "value": "22.7M"}, {"name": "Current mean", "value": "22.9M"}, {"name": "Reference SD", "value": "294"}, {"name": "Current SD", "value": "46.0k"}, {"name": "Deviation (sigma)", "value": "648"}]}
- M12 / 584 / java_lang_GarbageCollector_LastGcInfo_memoryUsageBeforeGc_used.Tenured_Gen.Copy / source_unit: {"details": [{"name": "Reference mean", "value": "22.7M"}, {"name": "Current mean", "value": "22.9M"}, {"name": "Reference SD", "value": "288"}, {"name": "Current SD", "value": "47.4k"}, {"name": "Deviation (sigma)", "value": "658"}]}
- R01 / 15775 / hipstershop.872/EmptyCart / µs: {"after": 6976.2, "before": 3804.0, "details": [{"name": "Reference requests", "value": "22"}, {"name": "Current requests", "value": "20"}, {"name": "Current inclusive p95 (µs)", "value": "6976.2"}, {"name": "Request log2 ratio", "value": "-0.13"}, {"name": "Latency log2 ratio", "value": "0.87"}]}
- R02 / 88225 / hipstershop.720/ShipOrder / µs: {"after": 229.5, "before": 81.85, "details": [{"name": "Reference requests", "value": "22"}, {"name": "Current requests", "value": "18"}, {"name": "Current inclusive p95 (µs)", "value": "229.5"}, {"name": "Request log2 ratio", "value": "-0.28"}, {"name": "Latency log2 ratio", "value": "1.48"}]}
- R03 / 32113 / hipstershop.630/SendOrderConfirmation / µs: {"after": 45219.1, "before": 38806.75, "details": [{"name": "Reference requests", "value": "40"}, {"name": "Current requests", "value": "42"}, {"name": "Current inclusive p95 (µs)", "value": "45462.1"}, {"name": "Request log2 ratio", "value": "0.07"}, {"name": "Latency log2 ratio", "value": "0.22"}]}
- R04 / 15775 / hipstershop.720/ShipOrder / µs: {"after": 37340.2, "before": 3039.4, "details": [{"name": "Reference requests", "value": "22"}, {"name": "Current requests", "value": "20"}, {"name": "Current inclusive p95 (µs)", "value": "37533.55"}, {"name": "Request log2 ratio", "value": "-0.13"}, {"name": "Latency log2 ratio", "value": "3.62"}]}
- R05 / 92680 / hipstershop.630/SendOrderConfirmation / µs: {"after": 11371.05, "before": 4207.6, "details": [{"name": "Reference requests", "value": "22"}, {"name": "Current requests", "value": "20"}, {"name": "Current inclusive p95 (µs)", "value": "11621.65"}, {"name": "Request log2 ratio", "value": "-0.13"}, {"name": "Latency log2 ratio", "value": "1.43"}]}
- R06 / 94812 / /hipstershop.872/AddItem / µs: {"after": 1000.0, "before": 1000.0, "details": [{"name": "Reference requests", "value": "38"}, {"name": "Current requests", "value": "52"}, {"name": "Current inclusive p95 (µs)", "value": "1000.0"}, {"name": "Request log2 ratio", "value": "0.44"}, {"name": "Latency log2 ratio", "value": "0.0"}]}

## RQ3.8 · INC-12D81A21098E · repair

aiops2025 / test / service / network corrupt。MRR 0.5000 → 1.0000。

评测标签（仅分析）：{"checkoutservice": "876", "shippingservice": "111"}

TEXT：["364", "111", "20972"]

Service 364 is the root cause as it is the earliest-affected upstream caller in the topology (onset +18m) that owns pod 11935, which exhibits a massive request-response time anomaly (median ~64s vs ~13s) and error log burst. Verification confirms that the extreme latency in downstream service 111 (exclusive p95 ~20s) and its caller 876 are consistent with 364's failure, while host node 9484 shows stable filesystem usage, ruling out infrastructure as the primary origin.

FULL：["111", "785", "130"]

Top-1 service 111 is confirmed by TRC-L: its GetQuote operation shows an exclusive-latency p95 that explodes from ~5.6e3 µs to ~2.0e7 µs (latency_lfc=11.79, rank_score 11.79) with a count drop, far above every other traced operation, so the latency fault is local to 111 rather than inherited from callers. The same magnitude (rrt_max current_median 20,099,476) is visible on its hosted pod 11935, and 111's anomaly onset (~+18m) predates downstream 130 (+23.3m) and matches the earlier 276/364/242 onsets, so the topology/temporal order (364→111, 876→111 callers) is consistent with 111 as origin, not a downstream artifact.

[旧输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s0/outputs/02423d66886031207d545cf62d13b8eb0b8743cc1f83699badcd8c6276ac5d73.json) · [新输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s0/outputs/d0dfc7f01430befde7e76c6f57643edad49ff3697979bfee1ffe1100b36acd73.json) · [新输入](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s0/inputs/d0dfc7f01430befde7e76c6f57643edad49ff3697979bfee1ffe1100b36acd73.json)

[模型所见图](../through_RQ3_15_preserved/assets/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s0/renders/d0dfc7f01430befde7e76c6f57643edad49ff3697979bfee1ffe1100b36acd73_0.png)

- M01 / 84834 / client_error_ratio / ratio_or_percent: {"details": [{"name": "Reference mean", "value": "0.0e+00"}, {"name": "Current mean", "value": "0.85"}, {"name": "Reference SD", "value": "0.0e+00"}, {"name": "Current SD", "value": "2.42"}]}
- M02 / 58906 / client_error / source_unit: {"details": [{"name": "Reference mean", "value": "0.0e+00"}, {"name": "Current mean", "value": "0.44"}, {"name": "Reference SD", "value": "0.0e+00"}, {"name": "Current SD", "value": "1.26"}]}
- M03 / 84834 / error / source_unit: {"details": [{"name": "Reference mean", "value": "0.0e+00"}, {"name": "Current mean", "value": "0.44"}, {"name": "Reference SD", "value": "0.0e+00"}, {"name": "Current SD", "value": "1.26"}]}
- M04 / 73342 / client_error_ratio / ratio_or_percent: {"details": [{"name": "Reference mean", "value": "0.0e+00"}, {"name": "Current mean", "value": "0.07"}, {"name": "Reference SD", "value": "0.0e+00"}, {"name": "Current SD", "value": "0.19"}]}
- M05 / 84834 / error_ratio / ratio_or_percent: {"details": [{"name": "Reference mean", "value": "0.0e+00"}, {"name": "Current mean", "value": "0.85"}, {"name": "Reference SD", "value": "0.0e+00"}, {"name": "Current SD", "value": "2.42"}]}
- M06 / 73342 / client_error / source_unit: {"details": [{"name": "Reference mean", "value": "0.0e+00"}, {"name": "Current mean", "value": "0.44"}, {"name": "Reference SD", "value": "0.0e+00"}, {"name": "Current SD", "value": "1.26"}]}
- M07 / 73342 / error_ratio / ratio_or_percent: {"details": [{"name": "Reference mean", "value": "0.0e+00"}, {"name": "Current mean", "value": "0.07"}, {"name": "Reference SD", "value": "0.0e+00"}, {"name": "Current SD", "value": "0.19"}]}
- M08 / 58906 / error_ratio / ratio_or_percent: {"details": [{"name": "Reference mean", "value": "0.0e+00"}, {"name": "Current mean", "value": "0.85"}, {"name": "Reference SD", "value": "0.0e+00"}, {"name": "Current SD", "value": "2.42"}]}
- M09 / 73342 / error / source_unit: {"details": [{"name": "Reference mean", "value": "0.0e+00"}, {"name": "Current mean", "value": "0.44"}, {"name": "Reference SD", "value": "0.0e+00"}, {"name": "Current SD", "value": "1.26"}]}
- M10 / 58906 / error / source_unit: {"details": [{"name": "Reference mean", "value": "0.0e+00"}, {"name": "Current mean", "value": "0.44"}, {"name": "Reference SD", "value": "0.0e+00"}, {"name": "Current SD", "value": "1.26"}]}
- M11 / 58906 / client_error_ratio / ratio_or_percent: {"details": [{"name": "Reference mean", "value": "0.0e+00"}, {"name": "Current mean", "value": "0.85"}, {"name": "Reference SD", "value": "0.0e+00"}, {"name": "Current SD", "value": "2.42"}]}
- M12 / 84834 / client_error / source_unit: {"details": [{"name": "Reference mean", "value": "0.0e+00"}, {"name": "Current mean", "value": "0.44"}, {"name": "Reference SD", "value": "0.0e+00"}, {"name": "Current SD", "value": "1.26"}]}
- R01 / 785 / 276.785/ListProducts / µs: {"after": 1994.75, "before": 1918.0, "details": [{"name": "Reference requests", "value": "4829"}, {"name": "Current requests", "value": "1746"}, {"name": "Current inclusive p95 (µs)", "value": "2068.5"}, {"name": "Request log2 ratio", "value": "-1.47"}, {"name": "Latency log2 ratio", "value": "0.06"}]}
- R02 / 111 / 276.111/GetQuote / µs: {"after": 20000595.8, "before": 5655.4, "details": [{"name": "Reference requests", "value": "2429"}, {"name": "Current requests", "value": "812"}, {"name": "Current inclusive p95 (µs)", "value": "20000595.8"}, {"name": "Request log2 ratio", "value": "-1.58"}, {"name": "Latency log2 ratio", "value": "11.79"}]}
- R03 / 712 / 276.712/EmptyCart / µs: {"after": 76233.6, "before": 69418.55, "details": [{"name": "Reference requests", "value": "150"}, {"name": "Current requests", "value": "15"}, {"name": "Current inclusive p95 (µs)", "value": "78406.4"}, {"name": "Request log2 ratio", "value": "-3.24"}, {"name": "Latency log2 ratio", "value": "0.14"}]}
- R04 / 111 / 276.111/ShipOrder / µs: {"after": 518774.0, "before": 68671.6, "details": [{"name": "Reference requests", "value": "305"}, {"name": "Current requests", "value": "31"}, {"name": "Current inclusive p95 (µs)", "value": "518946.0"}, {"name": "Request log2 ratio", "value": "-3.26"}, {"name": "Latency log2 ratio", "value": "2.92"}]}
- R05 / 785 / /276.785/ListProducts / µs: {"after": 4195.95, "before": 4007.3, "details": [{"name": "Reference requests", "value": "3647"}, {"name": "Current requests", "value": "1264"}, {"name": "Current inclusive p95 (µs)", "value": "4277.45"}, {"name": "Request log2 ratio", "value": "-1.53"}, {"name": "Latency log2 ratio", "value": "0.07"}]}
- R06 / 242 / 276.242/Charge / µs: {"after": 86263.25, "before": 47239.7, "details": [{"name": "Reference requests", "value": "155"}, {"name": "Current requests", "value": "16"}, {"name": "Current inclusive p95 (µs)", "value": "86263.25"}, {"name": "Request log2 ratio", "value": "-3.2"}, {"name": "Latency log2 ratio", "value": "0.87"}]}

## RQ3.8 · INC-01BF937825D4 · repair

aegislab / eval / service / HTTPRequestAbort。MRR 0.0000 → 1.0000。

评测标签（仅分析）：{"ts-preserve-service": "732", "ts-ui-dashboard": "927"}

TEXT：["836", "864", "563"]

Service 836 is the root cause, evidenced by a 42x spike in exclusive latency for its 'POST /api/v1/travelservice/trip_detail' operation (exl_p95 2214us -> 94248us) and a 10x CPU utilization jump. This local degradation in 836 explains the high inclusive latency in its upstream callers (732, 689) and the subsequent CPU/latency spikes in downstream services like 864 and 563 (which 864 calls), fitting the call graph propagation from 836.

FULL：["732", "763", "165"]

Top-1 732 is verified: (1) its CPU mean shift is 13σ over baseline (MET-Z) while its log rates are absent from L, ruling out a pure noise/erroneous-entity reading and confirming a real fault window; and (2) graph G shows 732 as a caller that invokes 109, 482, and 836, all of which onset immediately after 732 (7.2m vs 7.0–7.2m), establishing a plausible upstream origin rather than a downstream victim. No contradictory alternative origin is supported, so 732 is retained.

[旧输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s2/outputs/ef2fb6941d84c83bf3c459ae0402a12d5bdd20ca2e180954abba5e7546cf4cfe.json) · [新输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s2/outputs/57cac362648ac9a57c8b5fb59cf641e41f6db1d76dca8a34284c40b9858e9e91.json) · [新输入](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s2/inputs/57cac362648ac9a57c8b5fb59cf641e41f6db1d76dca8a34284c40b9858e9e91.json)

[模型所见图](../through_RQ3_15_preserved/assets/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s2/renders/57cac362648ac9a57c8b5fb59cf641e41f6db1d76dca8a34284c40b9858e9e91_0.png)

- M01 / 836 / jvm.system.cpu.utilization / ratio_or_percent: {"details": [{"name": "Reference mean", "value": "0.02"}, {"name": "Current mean", "value": "0.15"}, {"name": "Reference SD", "value": "0.01"}, {"name": "Current SD", "value": "0.06"}, {"name": "Deviation (sigma)", "value": "12"}]}
- M02 / 109 / hubble_http_request_duration_p90_seconds / milliseconds_or_source_unit: {"details": [{"name": "Reference mean", "value": "6.5e-03"}, {"name": "Current mean", "value": "0.28"}, {"name": "Reference SD", "value": "1.3e-03"}, {"name": "Current SD", "value": "0.32"}, {"name": "Deviation (sigma)", "value": "220"}]}
- M03 / 762 / jvm.system.cpu.utilization / ratio_or_percent: {"details": [{"name": "Reference mean", "value": "0.05"}, {"name": "Current mean", "value": "0.25"}, {"name": "Reference SD", "value": "0.01"}, {"name": "Current SD", "value": "0.10"}, {"name": "Deviation (sigma)", "value": "13"}]}
- M04 / 564 / jvm.system.cpu.utilization / ratio_or_percent: {"details": [{"name": "Reference mean", "value": "0.02"}, {"name": "Current mean", "value": "0.15"}, {"name": "Reference SD", "value": "0.01"}, {"name": "Current SD", "value": "0.06"}, {"name": "Deviation (sigma)", "value": "11"}]}
- M05 / 779 / hubble_http_request_duration_p99_seconds / milliseconds_or_source_unit: {"details": [{"name": "Reference mean", "value": "9.9e-03"}, {"name": "Current mean", "value": "0.70"}, {"name": "Reference SD", "value": "1.0e-04"}, {"name": "Current SD", "value": "1.07"}, {"name": "Deviation (sigma)", "value": "6.8k"}]}
- M06 / 932 / jvm.system.cpu.utilization / ratio_or_percent: {"details": [{"name": "Reference mean", "value": "0.02"}, {"name": "Current mean", "value": "0.15"}, {"name": "Reference SD", "value": "1.0e-02"}, {"name": "Current SD", "value": "0.06"}, {"name": "Deviation (sigma)", "value": "13"}]}
- M07 / 826 / jvm.cpu.recent_utilization / ratio_or_percent: {"details": [{"name": "Reference mean", "value": "3.2e-05"}, {"name": "Current mean", "value": "3.9e-05"}, {"name": "Reference SD", "value": "1.2e-06"}, {"name": "Current SD", "value": "2.0e-06"}, {"name": "Deviation (sigma)", "value": "4.87"}]}
- M08 / 719 / jvm.cpu.recent_utilization / ratio_or_percent: {"details": [{"name": "Reference mean", "value": "3.1e-05"}, {"name": "Current mean", "value": "3.7e-05"}, {"name": "Reference SD", "value": "7.8e-07"}, {"name": "Current SD", "value": "3.5e-06"}, {"name": "Deviation (sigma)", "value": "7.08"}]}
- M09 / 165 / hubble_http_request_duration_p95_seconds / milliseconds_or_source_unit: {"details": [{"name": "Reference mean", "value": "4.7e-03"}, {"name": "Current mean", "value": "5.6e-03"}, {"name": "Reference SD", "value": "2.9e-19"}, {"name": "Current SD", "value": "1.2e-03"}, {"name": "Deviation (sigma)", "value": "3035303.2G"}]}
- M10 / 732 / jvm.system.cpu.utilization / ratio_or_percent: {"details": [{"name": "Reference mean", "value": "0.02"}, {"name": "Current mean", "value": "0.14"}, {"name": "Reference SD", "value": "9.8e-03"}, {"name": "Current SD", "value": "0.07"}, {"name": "Deviation (sigma)", "value": "13"}]}
- M11 / 109 / jvm.system.cpu.utilization / ratio_or_percent: {"details": [{"name": "Reference mean", "value": "0.02"}, {"name": "Current mean", "value": "0.17"}, {"name": "Reference SD", "value": "0.02"}, {"name": "Current SD", "value": "0.07"}, {"name": "Deviation (sigma)", "value": "9.73"}]}
- M12 / 763 / jvm.system.cpu.utilization / ratio_or_percent: {"details": [{"name": "Reference mean", "value": "0.02"}, {"name": "Current mean", "value": "0.14"}, {"name": "Reference SD", "value": "7.6e-03"}, {"name": "Current SD", "value": "0.06"}, {"name": "Deviation (sigma)", "value": "16"}]}
- R01 / 836 / POST /api/v1/travelservice/trip_detail / µs: {"after": 94248.28, "before": 2214.84, "details": [{"name": "Reference requests", "value": "139"}, {"name": "Current requests", "value": "13"}, {"name": "Current inclusive p95 (µs)", "value": "203485.0"}, {"name": "Request log2 ratio", "value": "-3.32"}, {"name": "Latency log2 ratio", "value": "5.41"}]}
- R02 / 927 / POST /api/v1/travelplanservice/travelPlan/minStation / µs: {"after": 36429.4, "before": 3350.8, "details": [{"name": "Reference requests", "value": "47"}, {"name": "Current requests", "value": "12"}, {"name": "Current inclusive p95 (µs)", "value": "1111978.54"}, {"name": "Request log2 ratio", "value": "-1.88"}, {"name": "Latency log2 ratio", "value": "3.44"}]}
- R03 / 927 / POST /api/v1/orderOtherService/orderOther/refresh / µs: {"after": 20756.84, "before": 2987.78, "details": [{"name": "Reference requests", "value": "356"}, {"name": "Current requests", "value": "54"}, {"name": "Current inclusive p95 (µs)", "value": "30917.32"}, {"name": "Request log2 ratio", "value": "-2.7"}, {"name": "Latency log2 ratio", "value": "2.8"}]}
- R04 / 960 / TravelPlanController.getByMinStation / µs: {"after": 471962.29, "before": 17252.56, "details": [{"name": "Reference requests", "value": "47"}, {"name": "Current requests", "value": "12"}, {"name": "Current inclusive p95 (µs)", "value": "1078198.78"}, {"name": "Request log2 ratio", "value": "-1.88"}, {"name": "Latency log2 ratio", "value": "4.77"}]}
- R05 / 519 / HTTP POST / µs: {"after": 346036.49, "before": 2503.15, "details": [{"name": "Reference requests", "value": "1973"}, {"name": "Current requests", "value": "336"}, {"name": "Current inclusive p95 (µs)", "value": "547798.39"}, {"name": "Request log2 ratio", "value": "-2.55"}, {"name": "Latency log2 ratio", "value": "7.11"}]}
- R06 / 689 / RoutePlanController.getQuickestRoutes / µs: {"after": 137025.12, "before": 10783.12, "details": [{"name": "Reference requests", "value": "37"}, {"name": "Current requests", "value": "13"}, {"name": "Current inclusive p95 (µs)", "value": "810718.47"}, {"name": "Request log2 ratio", "value": "-1.44"}, {"name": "Latency log2 ratio", "value": "3.67"}]}

## RQ3.8 · INC-1FDDC9D9F646 · repair

aiops2022 / eval / pod / k8s容器内存负载。MRR 0.0000 → 0.5000。

评测标签（仅分析）：{"cartservice-0": "17923"}

TEXT：["311", "44667", "474", "6707", "623"]

Service 311 exhibits the earliest telemetry onset (+20.0m, preceding the fault window start) and its pod instance 53161 shows a decisive 11σ fluctuation in network receive metrics, identifying it as the temporal origin. Topology verification confirms 6707 (also early onset) calls 623, which calls 311, establishing a propagation path where 311's anomaly precedes downstream symptoms in 623 and 6707, while 44667 (pod of 474) shows a high-rank local anomaly as a secondary affected component.

FULL：["4238", "17923", "10033", "10369", "32198"]

Node 4238 is verified as the origin because its system disk usage climbed from a ~26.9% reference median to ~33.5% during the fault window, coinciding with a >1.5x local jump in container filesystem usage on hosted pod 17923, while the node also hosts the co-located pods 10033 and 10369. An alternative root-cause service or pod is contradicted by the lack of other independent node-level or service-level failures preceding these localized storage increases.

[旧输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s0/outputs/e9baab9f2247c676d30ebad55774c0af90b6e4c848b19a8194b996476012bcba.json) · [新输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s0/outputs/5e6ce7c8e93d2720ec18ef64408c9624e2c6f0e1ac8ce417a1b0bc51775ba489.json) · [新输入](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s0/inputs/5e6ce7c8e93d2720ec18ef64408c9624e2c6f0e1ac8ce417a1b0bc51775ba489.json)

[模型所见图](../through_RQ3_15_preserved/assets/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s0/renders/5e6ce7c8e93d2720ec18ef64408c9624e2c6f0e1ac8ce417a1b0bc51775ba489_0.png)

- M01 / 324 / jvm_memory_pool_allocated_MB_total.Metaspace / source_unit: {"details": [{"name": "Reference mean", "value": "30"}, {"name": "Current mean", "value": "30"}, {"name": "Reference SD", "value": "0.0e+00"}, {"name": "Current SD", "value": "9.8e-05"}]}
- M02 / 53161 / container_network_receive_MB.eth0 / source_unit: {"details": [{"name": "Reference mean", "value": "0.02"}, {"name": "Current mean", "value": "0.05"}, {"name": "Reference SD", "value": "2.9e-03"}, {"name": "Current SD", "value": "0.09"}, {"name": "Deviation (sigma)", "value": "11"}]}
- M03 / 344 / java_lang_GarbageCollector_LastGcInfo_memoryUsageBeforeGc_used.Eden_Space.Copy / source_unit: {"details": [{"name": "Reference mean", "value": "26.8M"}, {"name": "Current mean", "value": "26.8M"}, {"name": "Reference SD", "value": "28"}, {"name": "Current SD", "value": "1.4k"}, {"name": "Deviation (sigma)", "value": "14"}]}
- M04 / 5407 / system.disk.pct_usage / source_unit: {"details": [{"name": "Reference mean", "value": "43"}, {"name": "Current mean", "value": "43"}, {"name": "Reference SD", "value": "0.0e+00"}, {"name": "Current SD", "value": "2.7e-03"}]}
- M05 / 3816 / system.mem.free / source_unit: {"details": [{"name": "Reference mean", "value": "9.7k"}, {"name": "Current mean", "value": "10.0k"}, {"name": "Reference SD", "value": "9.04"}, {"name": "Current SD", "value": "539"}, {"name": "Deviation (sigma)", "value": "36"}]}
- M06 / 3816 / system.net.bytes_rcvd / source_unit: {"details": [{"name": "Reference mean", "value": "673.6k"}, {"name": "Current mean", "value": "1.3M"}, {"name": "Reference SD", "value": "126.7k"}, {"name": "Current SD", "value": "490.6k"}, {"name": "Deviation (sigma)", "value": "4.64"}]}
- M07 / 3816 / system.net.tcp.in_segs / source_unit: {"details": [{"name": "Reference mean", "value": "1.0k"}, {"name": "Current mean", "value": "1.2k"}, {"name": "Reference SD", "value": "34"}, {"name": "Current SD", "value": "346"}, {"name": "Deviation (sigma)", "value": "4.42"}]}
- M08 / 68587 / container_network_receive_MB.eth0 / source_unit: {"details": [{"name": "Reference mean", "value": "0.05"}, {"name": "Current mean", "value": "0.02"}, {"name": "Reference SD", "value": "0.08"}, {"name": "Current SD", "value": "1.7e-03"}, {"name": "Deviation (sigma)", "value": "0.32"}]}
- M09 / 44667 / container_network_receive_MB.eth0 / source_unit: {"details": [{"name": "Reference mean", "value": "0.02"}, {"name": "Current mean", "value": "0.05"}, {"name": "Reference SD", "value": "2.6e-03"}, {"name": "Current SD", "value": "0.13"}, {"name": "Deviation (sigma)", "value": "12"}]}
- M10 / 3816 / system.net.packets_in.count / source_unit: {"details": [{"name": "Reference mean", "value": "431"}, {"name": "Current mean", "value": "621"}, {"name": "Reference SD", "value": "31"}, {"name": "Current SD", "value": "336"}, {"name": "Deviation (sigma)", "value": "6.16"}]}
- M11 / 11738 / istio_agent_go_gc_duration_seconds.1.0 / milliseconds_or_source_unit: {"details": [{"name": "Reference mean", "value": "1.9e-04"}, {"name": "Current mean", "value": "1.8e-04"}, {"name": "Reference SD", "value": "0.0e+00"}, {"name": "Current SD", "value": "1.5e-05"}]}
- M12 / 28852 / container_memory_usage_MB / source_unit: {"details": [{"name": "Reference mean", "value": "256"}, {"name": "Current mean", "value": "256"}, {"name": "Reference SD", "value": "0.02"}, {"name": "Current SD", "value": "1.03"}, {"name": "Deviation (sigma)", "value": "15"}]}
- R01 / 25301 / hipstershop.421/ShipOrder / µs: {"after": 114.4, "before": 103.75, "details": [{"name": "Reference requests", "value": "52"}, {"name": "Current requests", "value": "37"}, {"name": "Current inclusive p95 (µs)", "value": "114.4"}, {"name": "Request log2 ratio", "value": "-0.48"}, {"name": "Latency log2 ratio", "value": "0.14"}]}
- R02 / 28316 / hipstershop.286/ListProducts / µs: {"after": 2823.35, "before": 2530.0, "details": [{"name": "Reference requests", "value": "139"}, {"name": "Current requests", "value": "122"}, {"name": "Current inclusive p95 (µs)", "value": "2852.25"}, {"name": "Request log2 ratio", "value": "-0.19"}, {"name": "Latency log2 ratio", "value": "0.16"}]}
- R03 / 97679 / hipstershop.413/EmptyCart / µs: {"after": 5317.4, "before": 4292.45, "details": [{"name": "Reference requests", "value": "50"}, {"name": "Current requests", "value": "33"}, {"name": "Current inclusive p95 (µs)", "value": "5317.4"}, {"name": "Request log2 ratio", "value": "-0.58"}, {"name": "Latency log2 ratio", "value": "0.31"}]}
- R04 / 24801 / hipstershop.413/EmptyCart / µs: {"after": 51471.5, "before": 17171.8, "details": [{"name": "Reference requests", "value": "105"}, {"name": "Current requests", "value": "31"}, {"name": "Current inclusive p95 (µs)", "value": "51971.5"}, {"name": "Request log2 ratio", "value": "-1.73"}, {"name": "Latency log2 ratio", "value": "1.58"}]}
- R05 / 26918 / hipstershop.413/EmptyCart / µs: {"after": 15646.8, "before": 14192.8, "details": [{"name": "Reference requests", "value": "48"}, {"name": "Current requests", "value": "35"}, {"name": "Current inclusive p95 (µs)", "value": "15646.8"}, {"name": "Request log2 ratio", "value": "-0.44"}, {"name": "Latency log2 ratio", "value": "0.14"}]}
- R06 / 86273 / grpc.hipstershop.474/Charge / µs: {"after": 193.8, "before": 177.4, "details": [{"name": "Reference requests", "value": "49"}, {"name": "Current requests", "value": "33"}, {"name": "Current inclusive p95 (µs)", "value": "193.8"}, {"name": "Request log2 ratio", "value": "-0.56"}, {"name": "Latency log2 ratio", "value": "0.13"}]}

## RQ3.8 · INC-9DDF62CAF256 · repair

aiops2025 / eval / pod/service / memory stress。MRR 0.0000 → 0.3333。

评测标签（仅分析）：{"productcatalogservice": "167", "productcatalogservice-2": "96150"}

TEXT：["553", "298", "772"]

Service 553 exhibits the earliest and most severe metric anomaly (onset +16.0m, z-score 129.3) in storage I/O metrics (read_mbps, write_wal_mbps), consistent with a database fault origin. The topology confirms 553 is not a direct callee in the provided call graph, while 298 and 772 are upstream callers experiencing downstream latency and count drops, validating 553 as the root cause over downstream services 490, 611, or 772.

FULL：["772", "298", "167"]

Top-1 service 772 has the earliest tied onset (+15.0m, rank 1) and a high MET-Z severity (14.28) that is not suppressed by any caller edges in G, and TRC-L/LOG-R show no louder local trace or log anomaly that would implicate a callee. The decisive temporal/topology relation is that 772 precedes or is simultaneous with its downstream callees 298 (+15.0m), 167 (+24.0m), 611 (+25.0m), and 662 (+24.0m), so the anomaly propagates outward from 772 rather than from a callee.

[旧输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s1/outputs/13fd1ca1e3c4b5650f6b7f1cf2118ec12a5cb76e16504ccf99175df13605c893.json) · [新输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s1/outputs/70e802b9a2b9abbad302a7a641829bdd24150cc67c2fb15f4fdd51fb733b8228.json) · [新输入](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s1/inputs/70e802b9a2b9abbad302a7a641829bdd24150cc67c2fb15f4fdd51fb733b8228.json)

[模型所见图](../through_RQ3_15_preserved/assets/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s1/renders/70e802b9a2b9abbad302a7a641829bdd24150cc67c2fb15f4fdd51fb733b8228_0.png)

- M01 / 654 / memory_usage / source_unit: {"details": [{"name": "Reference mean", "value": "864.7M"}, {"name": "Current mean", "value": "872.4M"}, {"name": "Reference SD", "value": "526.7k"}, {"name": "Current SD", "value": "5.8M"}, {"name": "Deviation (sigma)", "value": "15"}]}
- M02 / 66229 / rrt_max / source_unit: {"details": [{"name": "Reference mean", "value": "7.5k"}, {"name": "Current mean", "value": "4.7k"}, {"name": "Reference SD", "value": "13.3k"}, {"name": "Current SD", "value": "2.5k"}, {"name": "Deviation (sigma)", "value": "0.21"}]}
- M03 / 553 / read_mbps / source_unit: {"details": [{"name": "Reference mean", "value": "38.6k"}, {"name": "Current mean", "value": "29.1k"}, {"name": "Reference SD", "value": "88.6k"}, {"name": "Current SD", "value": "21.5k"}, {"name": "Deviation (sigma)", "value": "0.11"}]}
- M04 / 553 / snapshot_apply_count / source_unit: {"details": [{"name": "Reference mean", "value": "0.10"}, {"name": "Current mean", "value": "0.10"}, {"name": "Reference SD", "value": "0.18"}, {"name": "Current SD", "value": "0.12"}, {"name": "Deviation (sigma)", "value": "0.01"}]}
- M05 / 9674 / node_memory_MemAvailable_bytes / source_unit: {"details": [{"name": "Reference mean", "value": "8.6G"}, {"name": "Current mean", "value": "9.2G"}, {"name": "Reference SD", "value": "108.4M"}, {"name": "Current SD", "value": "1.3G"}, {"name": "Deviation (sigma)", "value": "6.03"}]}
- M06 / 21246 / pod_memory_working_set_bytes / source_unit: {"details": [{"name": "Reference mean", "value": "1.2k"}, {"name": "Current mean", "value": "70.3k"}, {"name": "Reference SD", "value": "437"}, {"name": "Current SD", "value": "171.7k"}, {"name": "Deviation (sigma)", "value": "158"}]}
- M07 / 2020 / node_memory_usage_rate / ratio_or_percent: {"details": [{"name": "Reference mean", "value": "42"}, {"name": "Current mean", "value": "28"}, {"name": "Reference SD", "value": "11"}, {"name": "Current SD", "value": "0.51"}, {"name": "Deviation (sigma)", "value": "1.34"}]}
- M08 / 32621 / pod_memory_working_set_bytes / source_unit: {"details": [{"name": "Reference mean", "value": "2.8k"}, {"name": "Current mean", "value": "204.7k"}, {"name": "Reference SD", "value": "1.4k"}, {"name": "Current SD", "value": "497.2k"}, {"name": "Deviation (sigma)", "value": "147"}]}
- M09 / 553 / write_wal_mbps / source_unit: {"details": [{"name": "Reference mean", "value": "39"}, {"name": "Current mean", "value": "47"}, {"name": "Reference SD", "value": "113"}, {"name": "Current SD", "value": "56"}, {"name": "Deviation (sigma)", "value": "0.08"}]}
- M10 / 9674 / node_memory_usage_rate / ratio_or_percent: {"details": [{"name": "Reference mean", "value": "51"}, {"name": "Current mean", "value": "47"}, {"name": "Reference SD", "value": "0.65"}, {"name": "Current SD", "value": "7.64"}, {"name": "Deviation (sigma)", "value": "6.03"}]}
- M11 / 2020 / node_memory_MemAvailable_bytes / source_unit: {"details": [{"name": "Reference mean", "value": "9.3G"}, {"name": "Current mean", "value": "11.7G"}, {"name": "Reference SD", "value": "1.8G"}, {"name": "Current SD", "value": "85.1M"}, {"name": "Deviation (sigma)", "value": "1.34"}]}
- M12 / 24902 / rrt_max / source_unit: {"details": [{"name": "Reference mean", "value": "43.2k"}, {"name": "Current mean", "value": "45.8k"}, {"name": "Reference SD", "value": "3.0k"}, {"name": "Current SD", "value": "9.0k"}, {"name": "Deviation (sigma)", "value": "0.85"}]}
- R01 / 960 / POST /912.960/AddItem / µs: {"after": 1580.75, "before": 1567.85, "details": [{"name": "Reference requests", "value": "508"}, {"name": "Current requests", "value": "146"}, {"name": "Current inclusive p95 (µs)", "value": "6458.75"}, {"name": "Request log2 ratio", "value": "-1.79"}, {"name": "Latency log2 ratio", "value": "0.01"}]}
- R02 / 960 / POST /912.960/EmptyCart / µs: {"after": 1973.2, "before": 1556.5, "details": [{"name": "Reference requests", "value": "251"}, {"name": "Current requests", "value": "73"}, {"name": "Current inclusive p95 (µs)", "value": "5260.0"}, {"name": "Request log2 ratio", "value": "-1.77"}, {"name": "Latency log2 ratio", "value": "0.34"}]}
- R03 / 490 / /912.490/SendOrderConfirmation / µs: {"after": 1071.6, "before": 996.0, "details": [{"name": "Reference requests", "value": "251"}, {"name": "Current requests", "value": "73"}, {"name": "Current inclusive p95 (µs)", "value": "1071.6"}, {"name": "Request log2 ratio", "value": "-1.77"}, {"name": "Latency log2 ratio", "value": "0.11"}]}
- R04 / 167 / /912.167/ListProducts / µs: {"after": 4010.25, "before": 3978.75, "details": [{"name": "Reference requests", "value": "4556"}, {"name": "Current requests", "value": "1308"}, {"name": "Current inclusive p95 (µs)", "value": "4106.6"}, {"name": "Request log2 ratio", "value": "-1.8"}, {"name": "Latency log2 ratio", "value": "0.01"}]}
- R05 / 490 / 912.490/SendOrderConfirmation / µs: {"after": 80815.2, "before": 77995.0, "details": [{"name": "Reference requests", "value": "251"}, {"name": "Current requests", "value": "73"}, {"name": "Current inclusive p95 (µs)", "value": "81426.6"}, {"name": "Request log2 ratio", "value": "-1.77"}, {"name": "Latency log2 ratio", "value": "0.05"}]}
- R06 / 918 / 918 / µs: {"after": 3553.0, "before": 3458.9, "details": [{"name": "Reference requests", "value": "759"}, {"name": "Current requests", "value": "219"}, {"name": "Current inclusive p95 (µs)", "value": "3553.0"}, {"name": "Request log2 ratio", "value": "-1.79"}, {"name": "Latency log2 ratio", "value": "0.04"}]}

## RQ3.8 · INC-93E715B82D2A · repair

aegislab / test / service / HTTPResponseReplaceBody。MRR 0.0000 → 0.5000。

评测标签（仅分析）：{"ts-basic-service": "837", "ts-station-service": "757"}

TEXT：["679", "752", "608"]

Service 679 is the root cause, evidenced by the earliest propagation onset (+4.8m) and a distinct degradation in its specific operation 'ConsignController.findByAccountId' (reference median 5.28ms vs current 4.40ms, indicating a shift in behavior or error rate not seen in other services which showed latency improvements). In contrast, service 752, despite having the highest metric severity (z-score 66.95 for memory), exhibits a later onset (+6.2m) and a coherent pattern of memory growth (increasing RSS, working set, and page faults, with decreasing available memory) that is characteristic of a downstream resource exhaustion or leak triggered by the upstream fault in 679.

FULL：["752", "757", "129"]

Verification Check 1 (M): Service 752 exhibits a runaway memory leak with an extreme +66.95σ deviation (RSS approaching limit), starting around +6.2m. Verification Check 2 (G): Service 752 is a leaf dependency called only by 129 and 686, with no outgoing calls, placing it at the bottom of the suspect fault hierarchy. The decisive temporal relation shows 757 (called by 837, a callee of 424) appearing anomalously near the window's start (~+4.8m), indicating it is the initial victim of the latency propagation.

[旧输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s2/outputs/d31fdafd4ab5932205a33f7ca67aa27ec13be1f4f7e62647ccce7b076fbe2e59.json) · [新输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s2/outputs/8a867981453a1265e5b0852deea1cea7ead9057c824e73b46ff8659ec1292806.json) · [新输入](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s2/inputs/8a867981453a1265e5b0852deea1cea7ead9057c824e73b46ff8659ec1292806.json)

[模型所见图](../through_RQ3_15_preserved/assets/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s2/renders/8a867981453a1265e5b0852deea1cea7ead9057c824e73b46ff8659ec1292806_0.png)

- M01 / 752 / container.memory.page_faults / source_unit: {"details": [{"name": "Reference mean", "value": "158.8k"}, {"name": "Current mean", "value": "162.4k"}, {"name": "Reference SD", "value": "110"}, {"name": "Current SD", "value": "812"}, {"name": "Deviation (sigma)", "value": "33"}]}
- M02 / 752 / k8s.pod.memory.node.utilization / ratio_or_percent: {"details": [{"name": "Reference mean", "value": "5.5e-03"}, {"name": "Current mean", "value": "5.6e-03"}, {"name": "Reference SD", "value": "2.6e-06"}, {"name": "Current SD", "value": "3.8e-05"}, {"name": "Deviation (sigma)", "value": "33"}]}
- M03 / 752 / container.memory.rss / source_unit: {"details": [{"name": "Reference mean", "value": "728.2M"}, {"name": "Current mean", "value": "739.8M"}, {"name": "Reference SD", "value": "292.5k"}, {"name": "Current SD", "value": "4.3M"}, {"name": "Deviation (sigma)", "value": "40"}]}
- M04 / 752 / container.memory.working_set / source_unit: {"details": [{"name": "Reference mean", "value": "739.0M"}, {"name": "Current mean", "value": "750.6M"}, {"name": "Reference SD", "value": "446.1k"}, {"name": "Current SD", "value": "4.2M"}, {"name": "Deviation (sigma)", "value": "26"}]}
- M05 / 752 / k8s.pod.memory_limit_utilization / ratio_or_percent: {"details": [{"name": "Reference mean", "value": "0.23"}, {"name": "Current mean", "value": "0.23"}, {"name": "Reference SD", "value": "1.1e-04"}, {"name": "Current SD", "value": "1.6e-03"}, {"name": "Deviation (sigma)", "value": "33"}]}
- M06 / 752 / k8s.pod.memory.page_faults / source_unit: {"details": [{"name": "Reference mean", "value": "159.5k"}, {"name": "Current mean", "value": "163.0k"}, {"name": "Reference SD", "value": "111"}, {"name": "Current SD", "value": "1.0k"}, {"name": "Deviation (sigma)", "value": "32"}]}
- M07 / 752 / k8s.pod.memory.usage / source_unit: {"details": [{"name": "Reference mean", "value": "740.0M"}, {"name": "Current mean", "value": "751.3M"}, {"name": "Reference SD", "value": "346.2k"}, {"name": "Current SD", "value": "5.1M"}, {"name": "Deviation (sigma)", "value": "33"}]}
- M08 / 752 / k8s.pod.memory.available / source_unit: {"details": [{"name": "Reference mean", "value": "2.5G"}, {"name": "Current mean", "value": "2.5G"}, {"name": "Reference SD", "value": "346.2k"}, {"name": "Current SD", "value": "5.1M"}, {"name": "Deviation (sigma)", "value": "33"}]}
- M09 / 752 / k8s.pod.memory.rss / source_unit: {"details": [{"name": "Reference mean", "value": "728.2M"}, {"name": "Current mean", "value": "739.4M"}, {"name": "Reference SD", "value": "296.8k"}, {"name": "Current SD", "value": "5.2M"}, {"name": "Deviation (sigma)", "value": "38"}]}
- M10 / 752 / k8s.pod.memory.working_set / source_unit: {"details": [{"name": "Reference mean", "value": "739.7M"}, {"name": "Current mean", "value": "750.9M"}, {"name": "Reference SD", "value": "346.2k"}, {"name": "Current SD", "value": "5.1M"}, {"name": "Deviation (sigma)", "value": "33"}]}
- M11 / 752 / container.memory.usage / source_unit: {"details": [{"name": "Reference mean", "value": "739.4M"}, {"name": "Current mean", "value": "751.0M"}, {"name": "Reference SD", "value": "446.1k"}, {"name": "Current SD", "value": "4.2M"}, {"name": "Deviation (sigma)", "value": "26"}]}
- M12 / 752 / container.memory.available / source_unit: {"details": [{"name": "Reference mean", "value": "2.5G"}, {"name": "Current mean", "value": "2.5G"}, {"name": "Reference SD", "value": "446.1k"}, {"name": "Current SD", "value": "4.2M"}, {"name": "Deviation (sigma)", "value": "26"}]}
- R01 / 424 / BasicErrorController.error / µs: {"after": 832.0, "before": 1037.57, "details": [{"name": "Reference requests", "value": "34"}, {"name": "Current requests", "value": "133"}, {"name": "Current inclusive p95 (µs)", "value": "832.0"}, {"name": "Request log2 ratio", "value": "1.94"}, {"name": "Latency log2 ratio", "value": "-0.32"}]}
- R02 / 924 / BasicErrorController.error / µs: {"after": 667.0, "before": 896.89, "details": [{"name": "Reference requests", "value": "44"}, {"name": "Current requests", "value": "148"}, {"name": "Current inclusive p95 (µs)", "value": "667.0"}, {"name": "Request log2 ratio", "value": "1.73"}, {"name": "Latency log2 ratio", "value": "-0.43"}]}
- R03 / 377 / BasicErrorController.error / µs: {"after": 820.3, "before": 1140.59, "details": [{"name": "Reference requests", "value": "25"}, {"name": "Current requests", "value": "77"}, {"name": "Current inclusive p95 (µs)", "value": "820.3"}, {"name": "Request log2 ratio", "value": "1.58"}, {"name": "Latency log2 ratio", "value": "-0.48"}]}
- R04 / 837 / BasicErrorController.error / µs: {"after": 509.32, "before": 959.61, "details": [{"name": "Reference requests", "value": "58"}, {"name": "Current requests", "value": "211"}, {"name": "Current inclusive p95 (µs)", "value": "509.32"}, {"name": "Request log2 ratio", "value": "1.85"}, {"name": "Latency log2 ratio", "value": "-0.91"}]}
- R05 / 817 / BasicErrorController.error / µs: {"after": 826.42, "before": 1088.11, "details": [{"name": "Reference requests", "value": "16"}, {"name": "Current requests", "value": "63"}, {"name": "Current inclusive p95 (µs)", "value": "826.42"}, {"name": "Request log2 ratio", "value": "1.91"}, {"name": "Latency log2 ratio", "value": "-0.4"}]}
- R06 / 608 / BasicErrorController.error / µs: {"after": 726.89, "before": 1172.97, "details": [{"name": "Reference requests", "value": "24"}, {"name": "Current requests", "value": "78"}, {"name": "Current inclusive p95 (µs)", "value": "726.89"}, {"name": "Request log2 ratio", "value": "1.66"}, {"name": "Latency log2 ratio", "value": "-0.69"}]}

## RQ3.8 · INC-37ABFB78A80E · break

aegislab / eval / service / HTTPRequestReplaceMethod。MRR 1.0000 → 0.0000。

评测标签（仅分析）：{"ts-basic-service": "495", "ts-route-service": "819"}

TEXT：["495", "803", "171"]

Service 495 is the topologically upstream origin, as it is called by 364, 437, and 564 but does not call any of the other high-severity candidates, and its latency deviation (z=872.6) aligns with the earliest observed onset (+4.2m). Verification confirms that 495's exclusive latency is elevated, indicating local processing failure rather than just downstream wait, and its lack of outgoing calls to other faulted services rules out it being a victim of their faults.

FULL：["364", "803", "248"]

MET-Z records service 364's latency degradation at bin 40 (~5.0m), the earliest onset among the high-severity (999σ) cluster, and G shows 803 is an isolated leaf with no calls to other services, disqualifying it as the source of the cascading propagation. This localizes the origin to 364, whose latency spikes align temporally and topologically with its caller 189 and affected callees (437, 495, 564).

[旧输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s1/outputs/fb0add616be7f249c557c81326e8f38c6324dda14e7b84c5dda2762324d4bbd9.json) · [新输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s1/outputs/8dfb07e256f22f756a3b63a02d31cc26f9d92e8524fae9c430408475e8a4e2a5.json) · [新输入](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s1/inputs/8dfb07e256f22f756a3b63a02d31cc26f9d92e8524fae9c430408475e8a4e2a5.json)

[模型所见图](../through_RQ3_15_preserved/assets/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s1/renders/8dfb07e256f22f756a3b63a02d31cc26f9d92e8524fae9c430408475e8a4e2a5_0.png)

- M01 / 564 / hubble_http_request_duration_p95_seconds / milliseconds_or_source_unit: {"details": [{"name": "Reference mean", "value": "0.13"}, {"name": "Current mean", "value": "5.05"}, {"name": "Reference SD", "value": "0.01"}, {"name": "Current SD", "value": "2.50"}, {"name": "Deviation (sigma)", "value": "342"}]}
- M02 / 394 / hubble_http_request_duration_p95_seconds / milliseconds_or_source_unit: {"details": [{"name": "Reference mean", "value": "0.61"}, {"name": "Current mean", "value": "5.73"}, {"name": "Reference SD", "value": "0.02"}, {"name": "Current SD", "value": "3.17"}, {"name": "Deviation (sigma)", "value": "236"}]}
- M03 / 495 / hubble_http_request_duration_p90_seconds / milliseconds_or_source_unit: {"details": [{"name": "Reference mean", "value": "0.03"}, {"name": "Current mean", "value": "0.13"}, {"name": "Reference SD", "value": "1.7e-04"}, {"name": "Current SD", "value": "0.03"}, {"name": "Deviation (sigma)", "value": "585"}]}
- M04 / 437 / hubble_http_request_duration_p50_seconds / milliseconds_or_source_unit: {"details": [{"name": "Reference mean", "value": "0.03"}, {"name": "Current mean", "value": "1.96"}, {"name": "Reference SD", "value": "4.0e-03"}, {"name": "Current SD", "value": "2.70"}, {"name": "Deviation (sigma)", "value": "479"}]}
- M05 / 437 / hubble_http_request_duration_p90_seconds / milliseconds_or_source_unit: {"details": [{"name": "Reference mean", "value": "0.09"}, {"name": "Current mean", "value": "5.70"}, {"name": "Reference SD", "value": "0.03"}, {"name": "Current SD", "value": "2.18"}, {"name": "Deviation (sigma)", "value": "217"}]}
- M06 / 564 / hubble_http_request_duration_p50_seconds / milliseconds_or_source_unit: {"details": [{"name": "Reference mean", "value": "0.04"}, {"name": "Current mean", "value": "0.84"}, {"name": "Reference SD", "value": "4.7e-03"}, {"name": "Current SD", "value": "2.20"}, {"name": "Deviation (sigma)", "value": "171"}]}
- M07 / 364 / hubble_http_request_duration_p90_seconds / milliseconds_or_source_unit: {"details": [{"name": "Reference mean", "value": "0.03"}, {"name": "Current mean", "value": "4.72"}, {"name": "Reference SD", "value": "2.6e-03"}, {"name": "Current SD", "value": "4.98"}, {"name": "Deviation (sigma)", "value": "1.8k"}]}
- M08 / 394 / hubble_http_request_duration_p50_seconds / milliseconds_or_source_unit: {"details": [{"name": "Reference mean", "value": "0.16"}, {"name": "Current mean", "value": "2.67"}, {"name": "Reference SD", "value": "0.02"}, {"name": "Current SD", "value": "4.07"}, {"name": "Deviation (sigma)", "value": "111"}]}
- M09 / 564 / hubble_http_request_duration_p90_seconds / milliseconds_or_source_unit: {"details": [{"name": "Reference mean", "value": "0.09"}, {"name": "Current mean", "value": "5.93"}, {"name": "Reference SD", "value": "0.02"}, {"name": "Current SD", "value": "2.34"}, {"name": "Deviation (sigma)", "value": "248"}]}
- M10 / 437 / hubble_http_request_duration_p95_seconds / milliseconds_or_source_unit: {"details": [{"name": "Reference mean", "value": "0.14"}, {"name": "Current mean", "value": "5.43"}, {"name": "Reference SD", "value": "0.03"}, {"name": "Current SD", "value": "2.15"}, {"name": "Deviation (sigma)", "value": "210"}]}
- M11 / 364 / hubble_http_request_duration_p50_seconds / milliseconds_or_source_unit: {"details": [{"name": "Reference mean", "value": "7.8e-03"}, {"name": "Current mean", "value": "3.54"}, {"name": "Reference SD", "value": "5.8e-04"}, {"name": "Current SD", "value": "4.77"}, {"name": "Deviation (sigma)", "value": "6.1k"}]}
- M12 / 364 / hubble_http_request_duration_p95_seconds / milliseconds_or_source_unit: {"details": [{"name": "Reference mean", "value": "0.03"}, {"name": "Current mean", "value": "7.65"}, {"name": "Reference SD", "value": "1.7e-03"}, {"name": "Current SD", "value": "4.23"}, {"name": "Deviation (sigma)", "value": "4.6k"}]}
- R01 / 819 / OnCommittedResponseWrapper.sendError / µs: {"after": 35.38, "before": 18.86, "details": [{"name": "Reference requests", "value": "302"}, {"name": "Current requests", "value": "4454"}, {"name": "Current inclusive p95 (µs)", "value": "35.38"}, {"name": "Request log2 ratio", "value": "3.88"}, {"name": "Latency log2 ratio", "value": "0.87"}]}
- R02 / 364 / POST / µs: {"after": 2149479.97, "before": 3701.69, "details": [{"name": "Reference requests", "value": "678"}, {"name": "Current requests", "value": "60"}, {"name": "Current inclusive p95 (µs)", "value": "60002987.04"}, {"name": "Request log2 ratio", "value": "-3.48"}, {"name": "Latency log2 ratio", "value": "9.18"}]}
- R03 / 287 / POST / µs: {"after": 1002916.13, "before": 3743.0, "details": [{"name": "Reference requests", "value": "676"}, {"name": "Current requests", "value": "115"}, {"name": "Current inclusive p95 (µs)", "value": "60000371.43"}, {"name": "Request log2 ratio", "value": "-2.55"}, {"name": "Latency log2 ratio", "value": "8.07"}]}
- R04 / 819 / PUT /error / µs: {"after": 1675.49, "before": 1287.54, "details": [{"name": "Reference requests", "value": "302"}, {"name": "Current requests", "value": "4454"}, {"name": "Current inclusive p95 (µs)", "value": "2113.46"}, {"name": "Request log2 ratio", "value": "3.88"}, {"name": "Latency log2 ratio", "value": "0.38"}]}
- R05 / 437 / POST / µs: {"after": 3657672.77, "before": 3822.01, "details": [{"name": "Reference requests", "value": "1996"}, {"name": "Current requests", "value": "482"}, {"name": "Current inclusive p95 (µs)", "value": "4130151.62"}, {"name": "Request log2 ratio", "value": "-2.05"}, {"name": "Latency log2 ratio", "value": "9.9"}]}
- R06 / 564 / POST / µs: {"after": 3618519.68, "before": 3974.24, "details": [{"name": "Reference requests", "value": "1218"}, {"name": "Current requests", "value": "252"}, {"name": "Current inclusive p95 (µs)", "value": "4038237.22"}, {"name": "Request log2 ratio", "value": "-2.27"}, {"name": "Latency log2 ratio", "value": "9.83"}]}

## RQ3.8 · INC-03C364835E1A · break

aiops2022 / eval / service / k8s容器网络资源包重复发送。MRR 1.0000 → 0.0000。

评测标签（仅分析）：{"emailservice": "299"}

TEXT：["299", "487", "212"]

Service 299 is the root cause, evidenced by the highest MET-Z severity (rank 1, z=186) and the dominant TRC-L exclusive latency degradation (rank_score 1.9) for the SendOrderConfirmation operation, indicating local processing failure. Topology verification confirms 299 is a callee of 501, which aligns with the propagation chain, and 487 is the next most severe anomaly (z=343.8) acting as a downstream symptom or co-located factor rather than the origin.

FULL：["487", "777", "132"]

Top-1 pod 49410 is rejected by a direct topological contradiction: its network spike is narrow to a single bin (0.55 MB versus ~0.02 MB baseline) while its owner service 487's calls appear nowhere in the R trace set, whereas the alternative 50658 sustains three edge spikes that flow through its callee 85031 (Convert) inside the +24–26 min window. This sustains 487 as the loudest-metric origin, with 777 (sustained 4-bin receive spike, +24 m onset) and 132 (trailing +27 m, downstream of 212) as secondary candidates.

[旧输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s2/outputs/efcb2bead7c2076748a40f1b496fd874224178dfb6387ac1943c89f634185c49.json) · [新输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s2/outputs/3d9f61bb80803d8b2f1cb11f2d6c6003b9367ad08cdc6cabdf1631196a4587a3.json) · [新输入](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s2/inputs/3d9f61bb80803d8b2f1cb11f2d6c6003b9367ad08cdc6cabdf1631196a4587a3.json)

[模型所见图](../through_RQ3_15_preserved/assets/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s2/renders/3d9f61bb80803d8b2f1cb11f2d6c6003b9367ad08cdc6cabdf1631196a4587a3_0.png)

- M01 / 97820 / container_memory_max_usage_MB / source_unit: {"details": [{"name": "Reference mean", "value": "138"}, {"name": "Current mean", "value": "138"}, {"name": "Reference SD", "value": "5.5e-03"}, {"name": "Current SD", "value": "0.11"}, {"name": "Deviation (sigma)", "value": "40"}]}
- M02 / 73227 / container_network_receive_MB.eth0 / source_unit: {"details": [{"name": "Reference mean", "value": "0.08"}, {"name": "Current mean", "value": "0.12"}, {"name": "Reference SD", "value": "7.1e-03"}, {"name": "Current SD", "value": "0.13"}, {"name": "Deviation (sigma)", "value": "4.98"}]}
- M03 / 378 / java_lang_MemoryPool_Usage_used.Tenured_Gen / source_unit: {"details": [{"name": "Reference mean", "value": "16.3M"}, {"name": "Current mean", "value": "16.3M"}, {"name": "Reference SD", "value": "195"}, {"name": "Current SD", "value": "2.8k"}, {"name": "Deviation (sigma)", "value": "14"}]}
- M04 / 3419 / system.io.avg_q_sz / source_unit: {"details": [{"name": "Reference mean", "value": "0.02"}, {"name": "Current mean", "value": "0.02"}, {"name": "Reference SD", "value": "0.08"}, {"name": "Current SD", "value": "0.04"}, {"name": "Deviation (sigma)", "value": "0.02"}]}
- M05 / 50658 / container_network_receive_MB.eth0 / source_unit: {"details": [{"name": "Reference mean", "value": "0.04"}, {"name": "Current mean", "value": "0.07"}, {"name": "Reference SD", "value": "5.0e-03"}, {"name": "Current SD", "value": "0.13"}, {"name": "Deviation (sigma)", "value": "6.58"}]}
- M06 / 378 / jvm_memory_pool_MB_used.Tenured_Gen / source_unit: {"details": [{"name": "Reference mean", "value": "16"}, {"name": "Current mean", "value": "16"}, {"name": "Reference SD", "value": "1.8e-04"}, {"name": "Current SD", "value": "2.7e-03"}, {"name": "Deviation (sigma)", "value": "14"}]}
- M07 / 74447 / container_network_receive_MB.eth0 / source_unit: {"details": [{"name": "Reference mean", "value": "0.04"}, {"name": "Current mean", "value": "0.07"}, {"name": "Reference SD", "value": "3.8e-03"}, {"name": "Current SD", "value": "0.09"}, {"name": "Deviation (sigma)", "value": "8.63"}]}
- M08 / 49410 / container_network_receive_MB.eth0 / source_unit: {"details": [{"name": "Reference mean", "value": "0.02"}, {"name": "Current mean", "value": "0.06"}, {"name": "Reference SD", "value": "2.6e-03"}, {"name": "Current SD", "value": "0.13"}, {"name": "Deviation (sigma)", "value": "13"}]}
- M09 / 77198 / container_network_receive_MB.eth0 / source_unit: {"details": [{"name": "Reference mean", "value": "0.05"}, {"name": "Current mean", "value": "0.03"}, {"name": "Reference SD", "value": "0.11"}, {"name": "Current SD", "value": "1.6e-03"}, {"name": "Deviation (sigma)", "value": "0.21"}]}
- M10 / 378 / java_lang_GarbageCollector_LastGcInfo_memoryUsageAfterGc_used.Tenured_Gen.Copy / source_unit: {"details": [{"name": "Reference mean", "value": "16.3M"}, {"name": "Current mean", "value": "16.3M"}, {"name": "Reference SD", "value": "195"}, {"name": "Current SD", "value": "2.8k"}, {"name": "Deviation (sigma)", "value": "14"}]}
- M11 / 378 / java_lang_MemoryPool_PeakUsage_used.Tenured_Gen / source_unit: {"details": [{"name": "Reference mean", "value": "16.3M"}, {"name": "Current mean", "value": "16.3M"}, {"name": "Reference SD", "value": "195"}, {"name": "Current SD", "value": "2.8k"}, {"name": "Deviation (sigma)", "value": "14"}]}
- M12 / 52535 / container_cpu_cfs_throttled_seconds / source_unit: {"details": [{"name": "Reference mean", "value": "2.2e-04"}, {"name": "Current mean", "value": "4.2e-03"}, {"name": "Reference SD", "value": "1.1e-03"}, {"name": "Current SD", "value": "0.02"}, {"name": "Deviation (sigma)", "value": "3.71"}]}
- R01 / 96498 / hipstershop.886/ListProducts / µs: {"after": 41.1, "before": 36.35, "details": [{"name": "Reference requests", "value": "194"}, {"name": "Current requests", "value": "120"}, {"name": "Current inclusive p95 (µs)", "value": "41.1"}, {"name": "Request log2 ratio", "value": "-0.69"}, {"name": "Latency log2 ratio", "value": "0.17"}]}
- R02 / 97820 / hipstershop.378/getads / µs: {"after": 20.0, "before": 18.0, "details": [{"name": "Reference requests", "value": "1595"}, {"name": "Current requests", "value": "986"}, {"name": "Current inclusive p95 (µs)", "value": "20.0"}, {"name": "Request log2 ratio", "value": "-0.69"}, {"name": "Latency log2 ratio", "value": "0.14"}]}
- R03 / 85031 / grpc.hipstershop.609/Convert / µs: {"after": 642.35, "before": 582.0, "details": [{"name": "Reference requests", "value": "3601"}, {"name": "Current requests", "value": "2202"}, {"name": "Current inclusive p95 (µs)", "value": "642.35"}, {"name": "Request log2 ratio", "value": "-0.71"}, {"name": "Latency log2 ratio", "value": "0.14"}]}
- R04 / 50658 / hipstershop.299/SendOrderConfirmation / µs: {"after": 14602.4, "before": 3911.25, "details": [{"name": "Reference requests", "value": "66"}, {"name": "Current requests", "value": "39"}, {"name": "Current inclusive p95 (µs)", "value": "14837.1"}, {"name": "Request log2 ratio", "value": "-0.74"}, {"name": "Latency log2 ratio", "value": "1.9"}]}
- R05 / 50658 / hipstershop.746/GetQuote / µs: {"after": 2909.5, "before": 2728.75, "details": [{"name": "Reference requests", "value": "66"}, {"name": "Current requests", "value": "39"}, {"name": "Current inclusive p95 (µs)", "value": "2974.1"}, {"name": "Request log2 ratio", "value": "-0.74"}, {"name": "Latency log2 ratio", "value": "0.09"}]}
- R06 / 39718 / hipstershop.886/ListProducts / µs: {"after": 2118.5, "before": 1936.5, "details": [{"name": "Reference requests", "value": "282"}, {"name": "Current requests", "value": "163"}, {"name": "Current inclusive p95 (µs)", "value": "2141.6"}, {"name": "Request log2 ratio", "value": "-0.79"}, {"name": "Latency log2 ratio", "value": "0.13"}]}

## RQ3.8 · INC-ABA10DF868CA · break

aiops2025 / eval / service / network corrupt。MRR 1.0000 → 0.3333。

评测标签（仅分析）：{"cartservice": "838", "frontend": "251"}

TEXT：["44866", "68078", "84187"]

The top candidate is pod 44866, which exhibits a significant deviation in CPU usage (median 0.0 vs reference 0.02) and the earliest server error onset (+18.0m) among the measured pods, coinciding with the incident's estimated fault window start. Verification confirms that pod 68078, while showing extreme memory working set spikes, is co-located or downstream as its network/pod metrics align with 44866's anomaly pattern, and service 84187's latency spikes are secondary symptoms of the resource exhaustion initiated by 44866.

FULL：["471", "584", "20263", "251"]

MET-Z shows service 471 is the earliest onset (relative ~15.0 m, before the +16.0–18.0 m fault window) with a significant 3σ mean shift, while downstream pods 20263/251/44866/55661/84187 and the other services only begin their shifts from ~16–26 m onward; no R (trace) or L (log) series exist to contradict this (explicit missing), and empty G call/hosting graphs leave no evidence placing the origin on a callee or co-located node, so the earliest-shifting upstream service 471 is the supported origin.

[旧输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s0/outputs/7829678e9bdfceb9944297f00f9534a5153500e2b012de952550a1b6f2450f0b.json) · [新输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s0/outputs/367ced8defeff7293cd5967f03033071646145c7c790e6e1fd4ce729f67399ff.json) · [新输入](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s0/inputs/367ced8defeff7293cd5967f03033071646145c7c790e6e1fd4ce729f67399ff.json)

[模型所见图](../through_RQ3_15_preserved/assets/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s0/renders/367ced8defeff7293cd5967f03033071646145c7c790e6e1fd4ce729f67399ff_0.png)

- M01 / 55661 / server_error / source_unit: {"details": [{"name": "Reference mean", "value": "0.25"}, {"name": "Current mean", "value": "4.14"}, {"name": "Reference SD", "value": "0.97"}, {"name": "Current SD", "value": "3.74"}, {"name": "Deviation (sigma)", "value": "4.02"}]}
- M02 / 84187 / rrt_max / source_unit: {"details": [{"name": "Reference mean", "value": "23.5k"}, {"name": "Current mean", "value": "19.9M"}, {"name": "Reference SD", "value": "55.2k"}, {"name": "Current SD", "value": "52.9M"}, {"name": "Deviation (sigma)", "value": "360"}]}
- M03 / 44866 / server_error_ratio / ratio_or_percent: {"details": [{"name": "Reference mean", "value": "2.43"}, {"name": "Current mean", "value": "13"}, {"name": "Reference SD", "value": "9.41"}, {"name": "Current SD", "value": "10"}, {"name": "Deviation (sigma)", "value": "1.12"}]}
- M04 / 251 / server_error / source_unit: {"details": [{"name": "Reference mean", "value": "1.25"}, {"name": "Current mean", "value": "13"}, {"name": "Reference SD", "value": "4.84"}, {"name": "Current SD", "value": "9.37"}, {"name": "Deviation (sigma)", "value": "2.43"}]}
- M05 / 838 / rrt / source_unit: {"details": [{"name": "Reference mean", "value": "1.8k"}, {"name": "Current mean", "value": "249.6k"}, {"name": "Reference SD", "value": "1.3k"}, {"name": "Current SD", "value": "825.9k"}, {"name": "Deviation (sigma)", "value": "185"}]}
- M06 / 20263 / server_error / source_unit: {"details": [{"name": "Reference mean", "value": "0.12"}, {"name": "Current mean", "value": "4.86"}, {"name": "Reference SD", "value": "0.48"}, {"name": "Current SD", "value": "4.64"}, {"name": "Deviation (sigma)", "value": "9.77"}]}
- M07 / 68078 / pod_memory_working_set_bytes / source_unit: {"details": [{"name": "Reference mean", "value": "1.1k"}, {"name": "Current mean", "value": "1.1M"}, {"name": "Reference SD", "value": "1.6k"}, {"name": "Current SD", "value": "3.8M"}, {"name": "Deviation (sigma)", "value": "664"}]}
- M08 / 98070 / pod_fs_reads_bytes / source_unit: {"details": [{"name": "Reference mean", "value": "40"}, {"name": "Current mean", "value": "0.0e+00"}, {"name": "Reference SD", "value": "154"}, {"name": "Current SD", "value": "0.0e+00"}, {"name": "Deviation (sigma)", "value": "0.26"}]}
- M09 / 84187 / rrt / source_unit: {"details": [{"name": "Reference mean", "value": "1.7k"}, {"name": "Current mean", "value": "509.7k"}, {"name": "Reference SD", "value": "810"}, {"name": "Current SD", "value": "1.7M"}, {"name": "Deviation (sigma)", "value": "627"}]}
- M10 / 55661 / server_error_ratio / ratio_or_percent: {"details": [{"name": "Reference mean", "value": "1.04"}, {"name": "Current mean", "value": "11"}, {"name": "Reference SD", "value": "4.04"}, {"name": "Current SD", "value": "11"}, {"name": "Deviation (sigma)", "value": "2.52"}]}
- M11 / 20263 / server_error_ratio / ratio_or_percent: {"details": [{"name": "Reference mean", "value": "0.69"}, {"name": "Current mean", "value": "14"}, {"name": "Reference SD", "value": "2.69"}, {"name": "Current SD", "value": "11"}, {"name": "Deviation (sigma)", "value": "4.89"}]}
- M12 / 44866 / server_error / source_unit: {"details": [{"name": "Reference mean", "value": "0.88"}, {"name": "Current mean", "value": "4.00"}, {"name": "Reference SD", "value": "3.39"}, {"name": "Current SD", "value": "2.73"}, {"name": "Deviation (sigma)", "value": "0.92"}]}

## RQ3.8 · INC-BDFA6FFC3C13 · break

aegislab / test / service / JVMMemoryStress。MRR 1.0000 → 0.5000。

评测标签（仅分析）：{"ts-order-service": "897"}

TEXT：["897", "11028", "199", "255", "327"]

Service 897 is the root cause, evidenced by a container restart (MET-Z deviation_sigma=4.36, fluctuating_3sigma=true) for pod 11028 (which 897 has_instance of) and severe local latency degradation in operations like 'Session.merge order.entity.Order' (latency_lfc=6.52, rank_score=6.52) within service 897 itself. While services 199, 255, and 327 show high MET-Z severity (ranks 2, 3, 6), their trace evidence indicates reduced latency (e.g., 255 'BasicErrorController.error' latency_lfc=-1.64) and they are downstream callees or peers of 897's failure propagation, confirming 897 as the origin rather than a downstream symptom.

FULL：["493", "897", "11028"]

Service 493 shows the earliest measured anomaly onset (+4.0 min) and hosts no recorded downstream dependencies, establishing it as the temporal origin that precedes the faults in its caller. Service 897 exhibits the strongest consequence with a hard memory crash and restarts (triggering pod 11028) that propagate upstream into 789. The supporting topology confirms the fault path from the originating node into the heavily connected 789/897 cluster.

[旧输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s2/outputs/52fa6d90d5521d49b9670e47b0ae7d66df4424454c4790012f65c9998efd1db7.json) · [新输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s2/outputs/1e66e9f23bc541b2896ba1f7162c2051f38eefa4f345789eeddedcf79f3f26f2.json) · [新输入](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s2/inputs/1e66e9f23bc541b2896ba1f7162c2051f38eefa4f345789eeddedcf79f3f26f2.json)

[模型所见图](../through_RQ3_15_preserved/assets/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s2/renders/1e66e9f23bc541b2896ba1f7162c2051f38eefa4f345789eeddedcf79f3f26f2_0.png)

- M01 / 897 / container.memory.available / source_unit: {"details": [{"name": "Reference mean", "value": "3.3G"}, {"name": "Current mean", "value": "3.6G"}, {"name": "Reference SD", "value": "598.0M"}, {"name": "Current SD", "value": "179.0M"}, {"name": "Deviation (sigma)", "value": "0.42"}]}
- M02 / 897 / hubble_http_request_duration_p50_seconds / milliseconds_or_source_unit: {"details": [{"name": "Reference mean", "value": "1.02"}, {"name": "Current mean", "value": "0.05"}, {"name": "Reference SD", "value": "3.00"}, {"name": "Current SD", "value": "0.05"}, {"name": "Deviation (sigma)", "value": "0.32"}]}
- M03 / 897 / k8s.pod.memory.usage / source_unit: {"details": [{"name": "Reference mean", "value": "887.7M"}, {"name": "Current mean", "value": "694.5M"}, {"name": "Reference SD", "value": "426.6M"}, {"name": "Current SD", "value": "183.6M"}, {"name": "Deviation (sigma)", "value": "0.45"}]}
- M04 / 897 / k8s.pod.memory.node.utilization / ratio_or_percent: {"details": [{"name": "Reference mean", "value": "6.6e-03"}, {"name": "Current mean", "value": "5.1e-03"}, {"name": "Reference SD", "value": "3.2e-03"}, {"name": "Current SD", "value": "1.4e-03"}, {"name": "Deviation (sigma)", "value": "0.45"}]}
- M05 / 897 / k8s.pod.memory.working_set / source_unit: {"details": [{"name": "Reference mean", "value": "887.4M"}, {"name": "Current mean", "value": "694.1M"}, {"name": "Reference SD", "value": "426.6M"}, {"name": "Current SD", "value": "183.6M"}, {"name": "Deviation (sigma)", "value": "0.45"}]}
- M06 / 897 / k8s.pod.memory_limit_utilization / ratio_or_percent: {"details": [{"name": "Reference mean", "value": "0.21"}, {"name": "Current mean", "value": "0.16"}, {"name": "Reference SD", "value": "0.10"}, {"name": "Current SD", "value": "0.04"}, {"name": "Deviation (sigma)", "value": "0.45"}]}
- M07 / 897 / container.memory.rss / source_unit: {"details": [{"name": "Reference mean", "value": "935.7M"}, {"name": "Current mean", "value": "686.3M"}, {"name": "Reference SD", "value": "596.0M"}, {"name": "Current SD", "value": "178.9M"}, {"name": "Deviation (sigma)", "value": "0.42"}]}
- M08 / 897 / container.memory.usage / source_unit: {"details": [{"name": "Reference mean", "value": "947.5M"}, {"name": "Current mean", "value": "698.9M"}, {"name": "Reference SD", "value": "598.0M"}, {"name": "Current SD", "value": "179.1M"}, {"name": "Deviation (sigma)", "value": "0.42"}]}
- M09 / 11028 / k8s.container.restarts / source_unit: {"details": [{"name": "Reference mean", "value": "0.05"}, {"name": "Current mean", "value": "1.00"}, {"name": "Reference SD", "value": "0.22"}, {"name": "Current SD", "value": "0.0e+00"}, {"name": "Deviation (sigma)", "value": "4.36"}]}
- M10 / 897 / k8s.pod.memory.rss / source_unit: {"details": [{"name": "Reference mean", "value": "875.5M"}, {"name": "Current mean", "value": "682.1M"}, {"name": "Reference SD", "value": "425.8M"}, {"name": "Current SD", "value": "183.5M"}, {"name": "Deviation (sigma)", "value": "0.45"}]}
- M11 / 897 / container.filesystem.usage / source_unit: {"details": [{"name": "Reference mean", "value": "701.8k"}, {"name": "Current mean", "value": "439.0k"}, {"name": "Reference SD", "value": "679.5k"}, {"name": "Current SD", "value": "71.5k"}, {"name": "Deviation (sigma)", "value": "0.39"}]}
- M12 / 897 / k8s.pod.memory.available / source_unit: {"details": [{"name": "Reference mean", "value": "3.4G"}, {"name": "Current mean", "value": "3.6G"}, {"name": "Reference SD", "value": "426.6M"}, {"name": "Current SD", "value": "183.6M"}, {"name": "Deviation (sigma)", "value": "0.45"}]}
- R01 / 897 / Session.merge order.entity.Order / µs: {"after": 67816.85, "before": 738.14, "details": [{"name": "Reference requests", "value": "85"}, {"name": "Current requests", "value": "28"}, {"name": "Current inclusive p95 (µs)", "value": "68676.5"}, {"name": "Request log2 ratio", "value": "-1.57"}, {"name": "Latency log2 ratio", "value": "6.52"}]}
- R02 / 789 / GET /api/v1/foodservice/foods/2025-07-21/taiyuan/shanghai/Z1236 / µs: {"after": 55280.0, "before": 4090.67, "details": [{"name": "Reference requests", "value": "23"}, {"name": "Current requests", "value": "16"}, {"name": "Current inclusive p95 (µs)", "value": "75263.37"}, {"name": "Request log2 ratio", "value": "-0.5"}, {"name": "Latency log2 ratio", "value": "3.76"}]}
- R03 / 789 / GET /api/v1/foodservice/foods/2025-07-21/shanghai/taiyuan/T1235 / µs: {"after": 18548.45, "before": 5667.54, "details": [{"name": "Reference requests", "value": "21"}, {"name": "Current requests", "value": "10"}, {"name": "Current inclusive p95 (µs)", "value": "34517.76"}, {"name": "Request log2 ratio", "value": "-1.0"}, {"name": "Latency log2 ratio", "value": "1.71"}]}
- R04 / 897 / INSERT ts.orders / µs: {"after": 23985.68, "before": 4578.83, "details": [{"name": "Reference requests", "value": "42"}, {"name": "Current requests", "value": "14"}, {"name": "Current inclusive p95 (µs)", "value": "23985.68"}, {"name": "Request log2 ratio", "value": "-1.52"}, {"name": "Latency log2 ratio", "value": "2.39"}]}
- R05 / 255 / BasicErrorController.error / µs: {"after": 1758.07, "before": 5471.32, "details": [{"name": "Reference requests", "value": "6"}, {"name": "Current requests", "value": "25"}, {"name": "Current inclusive p95 (µs)", "value": "1758.07"}, {"name": "Request log2 ratio", "value": "1.89"}, {"name": "Latency log2 ratio", "value": "-1.64"}]}
- R06 / 789 / POST /api/v1/orderservice/order/refresh / µs: {"after": 3588152.42, "before": 87301.72, "details": [{"name": "Reference requests", "value": "295"}, {"name": "Current requests", "value": "193"}, {"name": "Current inclusive p95 (µs)", "value": "3680030.53"}, {"name": "Request log2 ratio", "value": "-0.61"}, {"name": "Latency log2 ratio", "value": "5.36"}]}

## RQ3.8 · INC-C07AC67CFD5C · break

aiops2022 / test / pod / k8s容器写io负载。MRR 0.5000 → 0.0000。

评测标签（仅分析）：{"frontend-0": "51011"}

TEXT：["8138", "51011", "91043"]

The fault originates on node 8138, where system-level metrics show a synchronized onset of extreme I/O queue saturation (avg_q_sz ~36, 493σ shift) and significant memory pressure (pgmajfaults, working_set spikes) starting at bin 32 (+20.0m). This infrastructure degradation precedes the service-level symptoms, as the host contains pods 51011 (service 513) and 91043 (service 728), which exhibit the highest trace latency rank scores and MET-Z severity shifts immediately following the node's resource exhaustion.

FULL：["728", "8138", "513"]

MET-Z shows Pod 91043 (Service 728) and its host Node 8138 both hitting the z=999 cap simultaneously—the only node in the graph with a saturating signal—while no upstream calls 728 (its trace signature is empty, so its symptom is local/host-level, not propagated) and the 8138 → 91043 co-location is consistent with an infrastructure fault. 8138's elevated io.avg_q_sz, pgfaults, and udp.in_errors (fault window +19–+29m, co-occurring with the bin-32 spikes) plausibly drive Service 513's 100ms inclusive-latency jump as a secondary effect.

[旧输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s1/outputs/b9d7c4ac2908a882a3317d5f54499fec6cf16ebd8851bc39f5e4afdc07bf8045.json) · [新输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s1/outputs/868e6d3a9458917653af673716ef3e7947aed22f9318e586341c148ac1d0d7f5.json) · [新输入](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s1/inputs/868e6d3a9458917653af673716ef3e7947aed22f9318e586341c148ac1d0d7f5.json)

[模型所见图](../through_RQ3_15_preserved/assets/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s1/renders/868e6d3a9458917653af673716ef3e7947aed22f9318e586341c148ac1d0d7f5_0.png)

- M01 / 51011 / container_fs_inodes./dev/vda1 / source_unit: {"details": [{"name": "Reference mean", "value": "0.0e+00"}, {"name": "Current mean", "value": "0.19"}, {"name": "Reference SD", "value": "0.0e+00"}, {"name": "Current SD", "value": "0.85"}]}
- M02 / 91043 / container_memory_failures.container.pgmajfault / source_unit: {"details": [{"name": "Reference mean", "value": "0.0e+00"}, {"name": "Current mean", "value": "1.57"}, {"name": "Reference SD", "value": "0.0e+00"}, {"name": "Current SD", "value": "7.03"}]}
- M03 / 51011 / container_cpu_system_seconds / source_unit: {"details": [{"name": "Reference mean", "value": "0.19"}, {"name": "Current mean", "value": "7.99"}, {"name": "Reference SD", "value": "0.02"}, {"name": "Current SD", "value": "9.47"}, {"name": "Deviation (sigma)", "value": "380"}]}
- M04 / 51011 / container_fs_usage_MB./dev/vda1 / source_unit: {"details": [{"name": "Reference mean", "value": "35"}, {"name": "Current mean", "value": "2.0k"}, {"name": "Reference SD", "value": "0.58"}, {"name": "Current SD", "value": "3.2k"}, {"name": "Deviation (sigma)", "value": "3.4k"}]}
- M05 / 8138 / system.net.udp.in_errors / source_unit: {"details": [{"name": "Reference mean", "value": "0.0e+00"}, {"name": "Current mean", "value": "1.4e-03"}, {"name": "Reference SD", "value": "0.0e+00"}, {"name": "Current SD", "value": "6.4e-03"}]}
- M06 / 91043 / container_memory_usage_MB / source_unit: {"details": [{"name": "Reference mean", "value": "35"}, {"name": "Current mean", "value": "39"}, {"name": "Reference SD", "value": "2.2e-03"}, {"name": "Current SD", "value": "0.0e+00"}, {"name": "Deviation (sigma)", "value": "2.2k"}]}
- M07 / 51011 / container_memory_working_set_MB / source_unit: {"details": [{"name": "Reference mean", "value": "29"}, {"name": "Current mean", "value": "106"}, {"name": "Reference SD", "value": "0.0e+00"}, {"name": "Current SD", "value": "82"}]}
- M08 / 8138 / system.io.avg_q_sz / source_unit: {"details": [{"name": "Reference mean", "value": "0.01"}, {"name": "Current mean", "value": "13"}, {"name": "Reference SD", "value": "0.03"}, {"name": "Current SD", "value": "16"}, {"name": "Deviation (sigma)", "value": "493"}]}
- M09 / 91043 / container_memory_working_set_MB / source_unit: {"details": [{"name": "Reference mean", "value": "27"}, {"name": "Current mean", "value": "29"}, {"name": "Reference SD", "value": "2.2e-03"}, {"name": "Current SD", "value": "0.0e+00"}, {"name": "Deviation (sigma)", "value": "1000"}]}
- M10 / 91043 / container_memory_failures.hierarchy.pgmajfault / source_unit: {"details": [{"name": "Reference mean", "value": "0.0e+00"}, {"name": "Current mean", "value": "1.57"}, {"name": "Reference SD", "value": "0.0e+00"}, {"name": "Current SD", "value": "7.03"}]}
- M11 / 51011 / container_memory_failures.container.pgmajfault / source_unit: {"details": [{"name": "Reference mean", "value": "0.0e+00"}, {"name": "Current mean", "value": "14"}, {"name": "Reference SD", "value": "0.0e+00"}, {"name": "Current SD", "value": "49"}]}
- M12 / 51011 / container_memory_failures.hierarchy.pgmajfault / source_unit: {"details": [{"name": "Reference mean", "value": "0.0e+00"}, {"name": "Current mean", "value": "14"}, {"name": "Reference SD", "value": "0.0e+00"}, {"name": "Current SD", "value": "49"}]}
- R01 / 64395 / hipstershop.955/EmptyCart / µs: {"after": 45375.45, "before": 34833.25, "details": [{"name": "Reference requests", "value": "74"}, {"name": "Current requests", "value": "70"}, {"name": "Current inclusive p95 (µs)", "value": "45375.45"}, {"name": "Request log2 ratio", "value": "-0.08"}, {"name": "Latency log2 ratio", "value": "0.38"}]}
- R02 / 93918 / hipstershop.447/ShipOrder / µs: {"after": 93.65, "before": 81.65, "details": [{"name": "Reference requests", "value": "68"}, {"name": "Current requests", "value": "70"}, {"name": "Current inclusive p95 (µs)", "value": "93.65"}, {"name": "Request log2 ratio", "value": "0.04"}, {"name": "Latency log2 ratio", "value": "0.2"}]}
- R03 / 51011 / hipstershop.513/Recv. / µs: {"after": 1213.4, "before": 971.3, "details": [{"name": "Reference requests", "value": "1795"}, {"name": "Current requests", "value": "1784"}, {"name": "Current inclusive p95 (µs)", "value": "109646.65"}, {"name": "Request log2 ratio", "value": "-0.01"}, {"name": "Latency log2 ratio", "value": "0.32"}]}
- R04 / 64395 / hipstershop.648/SendOrderConfirmation / µs: {"after": 29042.4, "before": 23854.2, "details": [{"name": "Reference requests", "value": "74"}, {"name": "Current requests", "value": "70"}, {"name": "Current inclusive p95 (µs)", "value": "29301.55"}, {"name": "Request log2 ratio", "value": "-0.08"}, {"name": "Latency log2 ratio", "value": "0.28"}]}
- R05 / 51011 / hipstershop.423/PlaceOrder / µs: {"after": 6516.5, "before": 2826.9, "details": [{"name": "Reference requests", "value": "72"}, {"name": "Current requests", "value": "70"}, {"name": "Current inclusive p95 (µs)", "value": "100689.65"}, {"name": "Request log2 ratio", "value": "-0.04"}, {"name": "Latency log2 ratio", "value": "1.2"}]}
- R06 / 99012 / hipstershop.648/SendOrderConfirmation / µs: {"after": 48585.5, "before": 37754.2, "details": [{"name": "Reference requests", "value": "72"}, {"name": "Current requests", "value": "71"}, {"name": "Current inclusive p95 (µs)", "value": "48850.0"}, {"name": "Request log2 ratio", "value": "-0.02"}, {"name": "Latency log2 ratio", "value": "0.36"}]}

## RQ3.8 · INC-93D9EA50D239 · break

aiops2025 / test / service / code error。MRR 1.0000 → 0.0000。

评测标签（仅分析）：{"productcatalogservice": "633"}

TEXT：["633", "14233", "105", "292"]

Service 633 is the root cause, evidenced by the earliest and strongest exclusive latency degradation (TRC-L rank 1, +17.1m) and massive RRT anomalies (MET-Z signed_z ~999) in its pods (14233, 91708, 97816), which precedes the downstream propagation to its callers (105, 292) and co-located services. Verification confirms that the latency increase is local to 633 (exclusive p95 latency_lfc > 0) and not inherited from child spans, and that no upstream caller (292) or sibling service exhibited concurrent infrastructure failure or earlier onset that could account for 633's primary latency spike.

FULL：["105", "292", "1728"]

Service 105 is the root origin, with confirmed caller→callee edges 105→633 and 292→105 and an exclusive-latency onset of 18.0 min sitting between the 17.1 min upstream R-event at 292 and the 24.0 min downstream M-event at 1728. The fault-window metrics (56σ deviation) and the LT02 'new_errors:+100' burst at bin 30 on instance 50868 are consistent with 105 as the internal bottleneck behind the latency, rather than a mere downstream symptom.

[旧输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s1/outputs/25cefd40196437d7251b3452dfbca819c96d0d02037e9acf44d59fd05a361ec9.json) · [新输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s1/outputs/16f3b80d536191199aac3c9c9254be3c3e478c9bbca433f5e83595f79afccb94.json) · [新输入](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s1/inputs/16f3b80d536191199aac3c9c9254be3c3e478c9bbca433f5e83595f79afccb94.json)

[模型所见图](../through_RQ3_15_preserved/assets/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s1/renders/16f3b80d536191199aac3c9c9254be3c3e478c9bbca433f5e83595f79afccb94_0.png)

- M01 / 50868 / rrt / source_unit: {"details": [{"name": "Reference mean", "value": "3.8k"}, {"name": "Current mean", "value": "9.6k"}, {"name": "Reference SD", "value": "105"}, {"name": "Current SD", "value": "19.9k"}, {"name": "Deviation (sigma)", "value": "56"}]}
- M02 / 633 / rrt_max / source_unit: {"details": [{"name": "Reference mean", "value": "31.8k"}, {"name": "Current mean", "value": "2.0M"}, {"name": "Reference SD", "value": "5.3k"}, {"name": "Current SD", "value": "1.6M"}, {"name": "Deviation (sigma)", "value": "377"}]}
- M03 / 105 / rrt / source_unit: {"details": [{"name": "Reference mean", "value": "3.8k"}, {"name": "Current mean", "value": "9.6k"}, {"name": "Reference SD", "value": "105"}, {"name": "Current SD", "value": "19.9k"}, {"name": "Deviation (sigma)", "value": "56"}]}
- M04 / 932 / duration_99th / milliseconds_or_source_unit: {"details": [{"name": "Reference mean", "value": "1.0e-02"}, {"name": "Current mean", "value": "0.01"}, {"name": "Reference SD", "value": "1.7e-18"}, {"name": "Current SD", "value": "4.3e-03"}, {"name": "Deviation (sigma)", "value": "549010.2G"}]}
- M05 / 932 / connection_count / source_unit: {"details": [{"name": "Reference mean", "value": "2.00"}, {"name": "Current mean", "value": "2.43"}, {"name": "Reference SD", "value": "0.0e+00"}, {"name": "Current SD", "value": "0.79"}]}
- M06 / 41228 / error_ratio / ratio_or_percent: {"details": [{"name": "Reference mean", "value": "0.0e+00"}, {"name": "Current mean", "value": "24"}, {"name": "Reference SD", "value": "0.0e+00"}, {"name": "Current SD", "value": "20"}]}
- M07 / 41228 / server_error_ratio / ratio_or_percent: {"details": [{"name": "Reference mean", "value": "0.0e+00"}, {"name": "Current mean", "value": "24"}, {"name": "Reference SD", "value": "0.0e+00"}, {"name": "Current SD", "value": "20"}]}
- M08 / 97816 / rrt / source_unit: {"details": [{"name": "Reference mean", "value": "7.0k"}, {"name": "Current mean", "value": "10.4k"}, {"name": "Reference SD", "value": "1.4k"}, {"name": "Current SD", "value": "16.2k"}, {"name": "Deviation (sigma)", "value": "2.51"}]}
- M09 / 14233 / rrt / source_unit: {"details": [{"name": "Reference mean", "value": "7.4k"}, {"name": "Current mean", "value": "668.3k"}, {"name": "Reference SD", "value": "97"}, {"name": "Current SD", "value": "495.0k"}, {"name": "Deviation (sigma)", "value": "6.8k"}]}
- M10 / 633 / rrt / source_unit: {"details": [{"name": "Reference mean", "value": "7.4k"}, {"name": "Current mean", "value": "532.8k"}, {"name": "Reference SD", "value": "94"}, {"name": "Current SD", "value": "425.1k"}, {"name": "Deviation (sigma)", "value": "5.6k"}]}
- M11 / 14233 / rrt_max / source_unit: {"details": [{"name": "Reference mean", "value": "31.8k"}, {"name": "Current mean", "value": "2.0M"}, {"name": "Reference SD", "value": "5.3k"}, {"name": "Current SD", "value": "1.6M"}, {"name": "Deviation (sigma)", "value": "376"}]}
- M12 / 91708 / rrt / source_unit: {"details": [{"name": "Reference mean", "value": "7.4k"}, {"name": "Current mean", "value": "7.7k"}, {"name": "Reference SD", "value": "566"}, {"name": "Current SD", "value": "8.3k"}, {"name": "Deviation (sigma)", "value": "0.58"}]}
- R01 / 633 / 624.633/GetProduct / µs: {"after": 15702.2, "before": 13484.2, "details": [{"name": "Reference requests", "value": "14025"}, {"name": "Current requests", "value": "4473"}, {"name": "Current inclusive p95 (µs)", "value": "19062.8"}, {"name": "Request log2 ratio", "value": "-1.65"}, {"name": "Latency log2 ratio", "value": "0.22"}]}
- R02 / 340 / 624.340/GetCart / µs: {"after": 4935.8, "before": 4306.35, "details": [{"name": "Reference requests", "value": "1284"}, {"name": "Current requests", "value": "457"}, {"name": "Current inclusive p95 (µs)", "value": "8508.2"}, {"name": "Request log2 ratio", "value": "-1.49"}, {"name": "Latency log2 ratio", "value": "0.2"}]}
- R03 / 928 / 928 / µs: {"after": 3561.2, "before": 2323.95, "details": [{"name": "Reference requests", "value": "1410"}, {"name": "Current requests", "value": "495"}, {"name": "Current inclusive p95 (µs)", "value": "3561.2"}, {"name": "Request log2 ratio", "value": "-1.51"}, {"name": "Latency log2 ratio", "value": "0.62"}]}
- R04 / 633 / 624.633/ListProducts / µs: {"after": 3011.5, "before": 1949.95, "details": [{"name": "Reference requests", "value": "1462"}, {"name": "Current requests", "value": "531"}, {"name": "Current inclusive p95 (µs)", "value": "3168.5"}, {"name": "Request log2 ratio", "value": "-1.46"}, {"name": "Latency log2 ratio", "value": "0.63"}]}
- R05 / 340 / 624.340/AddItem / µs: {"after": 3248.6, "before": 2952.75, "details": [{"name": "Reference requests", "value": "126"}, {"name": "Current requests", "value": "38"}, {"name": "Current inclusive p95 (µs)", "value": "8598.0"}, {"name": "Request log2 ratio", "value": "-1.7"}, {"name": "Latency log2 ratio", "value": "0.14"}]}
- R06 / 105 / 624.105/ListRecommendations / µs: {"after": 4917.5, "before": 4517.2, "details": [{"name": "Reference requests", "value": "1105"}, {"name": "Current requests", "value": "366"}, {"name": "Current inclusive p95 (µs)", "value": "10547.25"}, {"name": "Request log2 ratio", "value": "-1.59"}, {"name": "Latency log2 ratio", "value": "0.12"}]}

## RQ3.8 · INC-FBCBAA98002C · break

aegislab / eval / service / HTTPRequestReplaceMethod。MRR 0.3333 → 0.0000。

评测标签（仅分析）：{"ts-basic-service": "370", "ts-price-service": "305"}

TEXT：["750", "714", "370"]

Service 750, identified as the database role, is the unobserved origin of the saturation affecting the downstream trace anomalies in 714 and 370, which exhibit the highest latency rank scores. The temporal onset of the CPU load spike in 219 at +4.8m precedes the latency propagation to 370, confirming the fault originated in the infrastructure/data layer before manifesting in the application services.

FULL：["712", "750", "26419"]

The log evidence from pod 26419 shows the root cause with the template "Attempting to connect to: [ts-{num1}:{num2}]" where num1=712 and num2=5672, indicating connection failures to service 712. The timing correlates with the CPU and load spikes observed across multiple services starting around bin 32 (the fault window). Service 712 is identified as a queue in the instance roles, and database 750 is part of the same infrastructure layer that would be affected by queue processing failures.

[旧输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s0/outputs/8828ae93b59480b2317bdc223d00e38a0bcba61586e085e786a7a6a6a1d8bb34.json) · [新输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s0/outputs/54e169120ed826f34ff89e7b2613f53606fb2849ce95af0e10ac6dff826109f4.json) · [新输入](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s0/inputs/54e169120ed826f34ff89e7b2613f53606fb2849ce95af0e10ac6dff826109f4.json)

[模型所见图](../through_RQ3_15_preserved/assets/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s0/renders/54e169120ed826f34ff89e7b2613f53606fb2849ce95af0e10ac6dff826109f4_0.png)

- M01 / 461 / jvm.system.cpu.utilization / ratio_or_percent: {"details": [{"name": "Reference mean", "value": "0.05"}, {"name": "Current mean", "value": "0.50"}, {"name": "Reference SD", "value": "0.02"}, {"name": "Current SD", "value": "0.36"}, {"name": "Deviation (sigma)", "value": "22"}]}
- M02 / 478 / jvm.system.cpu.utilization / ratio_or_percent: {"details": [{"name": "Reference mean", "value": "0.11"}, {"name": "Current mean", "value": "0.32"}, {"name": "Reference SD", "value": "0.01"}, {"name": "Current SD", "value": "0.17"}, {"name": "Deviation (sigma)", "value": "19"}]}
- M03 / 491 / jvm.system.cpu.utilization / ratio_or_percent: {"details": [{"name": "Reference mean", "value": "0.11"}, {"name": "Current mean", "value": "0.32"}, {"name": "Reference SD", "value": "0.01"}, {"name": "Current SD", "value": "0.17"}, {"name": "Deviation (sigma)", "value": "18"}]}
- M04 / 370 / jvm.system.cpu.utilization / ratio_or_percent: {"details": [{"name": "Reference mean", "value": "0.04"}, {"name": "Current mean", "value": "0.51"}, {"name": "Reference SD", "value": "0.01"}, {"name": "Current SD", "value": "0.36"}, {"name": "Deviation (sigma)", "value": "46"}]}
- M05 / 845 / jvm.system.cpu.utilization / ratio_or_percent: {"details": [{"name": "Reference mean", "value": "0.04"}, {"name": "Current mean", "value": "0.51"}, {"name": "Reference SD", "value": "7.6e-03"}, {"name": "Current SD", "value": "0.36"}, {"name": "Deviation (sigma)", "value": "62"}]}
- M06 / 461 / jvm.system.cpu.load_1m / source_unit: {"details": [{"name": "Reference mean", "value": "4.74"}, {"name": "Current mean", "value": "449"}, {"name": "Reference SD", "value": "2.03"}, {"name": "Current SD", "value": "185"}, {"name": "Deviation (sigma)", "value": "219"}]}
- M07 / 897 / jvm.system.cpu.load_1m / source_unit: {"details": [{"name": "Reference mean", "value": "4.74"}, {"name": "Current mean", "value": "449"}, {"name": "Reference SD", "value": "2.03"}, {"name": "Current SD", "value": "185"}, {"name": "Deviation (sigma)", "value": "219"}]}
- M08 / 219 / jvm.system.cpu.load_1m / source_unit: {"details": [{"name": "Reference mean", "value": "34"}, {"name": "Current mean", "value": "431"}, {"name": "Reference SD", "value": "125"}, {"name": "Current SD", "value": "182"}, {"name": "Deviation (sigma)", "value": "3.17"}]}
- M09 / 897 / jvm.system.cpu.utilization / ratio_or_percent: {"details": [{"name": "Reference mean", "value": "0.05"}, {"name": "Current mean", "value": "0.51"}, {"name": "Reference SD", "value": "0.02"}, {"name": "Current SD", "value": "0.36"}, {"name": "Deviation (sigma)", "value": "25"}]}
- M10 / 219 / jvm.system.cpu.utilization / ratio_or_percent: {"details": [{"name": "Reference mean", "value": "0.08"}, {"name": "Current mean", "value": "0.46"}, {"name": "Reference SD", "value": "0.16"}, {"name": "Current SD", "value": "0.37"}, {"name": "Deviation (sigma)", "value": "2.39"}]}
- M11 / 370 / jvm.system.cpu.load_1m / source_unit: {"details": [{"name": "Reference mean", "value": "4.58"}, {"name": "Current mean", "value": "458"}, {"name": "Reference SD", "value": "1.67"}, {"name": "Current SD", "value": "176"}, {"name": "Deviation (sigma)", "value": "272"}]}
- M12 / 845 / jvm.system.cpu.load_1m / source_unit: {"details": [{"name": "Reference mean", "value": "4.62"}, {"name": "Current mean", "value": "458"}, {"name": "Reference SD", "value": "1.61"}, {"name": "Current SD", "value": "176"}, {"name": "Deviation (sigma)", "value": "281"}]}
- R01 / 546 / GET /api/v1/foodservice/foods/2025-07-27/shanghai/suzhou/D1345 / µs: {"after": 15161.79, "before": 921.76, "details": [{"name": "Reference requests", "value": "49"}, {"name": "Current requests", "value": "18"}, {"name": "Current inclusive p95 (µs)", "value": "51136.02"}, {"name": "Request log2 ratio", "value": "-1.4"}, {"name": "Latency log2 ratio", "value": "4.04"}]}
- R02 / 714 / POST / µs: {"after": 37600.53, "before": 2560.88, "details": [{"name": "Reference requests", "value": "2707"}, {"name": "Current requests", "value": "803"}, {"name": "Current inclusive p95 (µs)", "value": "278258.52"}, {"name": "Request log2 ratio", "value": "-1.75"}, {"name": "Latency log2 ratio", "value": "3.88"}]}
- R03 / 546 / POST /api/v1/travelplanservice/travelPlan/minStation / µs: {"after": 20000475.14, "before": 1064.85, "details": [{"name": "Reference requests", "value": "104"}, {"name": "Current requests", "value": "33"}, {"name": "Current inclusive p95 (µs)", "value": "20000475.14"}, {"name": "Request log2 ratio", "value": "-1.63"}, {"name": "Latency log2 ratio", "value": "14.2"}]}
- R04 / 370 / GET / µs: {"after": 83753.61, "before": 1539.44, "details": [{"name": "Reference requests", "value": "3363"}, {"name": "Current requests", "value": "985"}, {"name": "Current inclusive p95 (µs)", "value": "90079.17"}, {"name": "Request log2 ratio", "value": "-1.77"}, {"name": "Latency log2 ratio", "value": "5.76"}]}
- R05 / 845 / ConsignController.updateConsign / µs: {"after": 563788.16, "before": 7046.2, "details": [{"name": "Reference requests", "value": "17"}, {"name": "Current requests", "value": "2"}, {"name": "Current inclusive p95 (µs)", "value": "584410.31"}, {"name": "Request log2 ratio", "value": "-2.58"}, {"name": "Latency log2 ratio", "value": "6.32"}]}
- R06 / 370 / POST / µs: {"after": 81415.8, "before": 2704.96, "details": [{"name": "Reference requests", "value": "3184"}, {"name": "Current requests", "value": "1049"}, {"name": "Current inclusive p95 (µs)", "value": "88271.96"}, {"name": "Request log2 ratio", "value": "-1.6"}, {"name": "Latency log2 ratio", "value": "4.91"}]}

## RQ3.8 · INC-540349CB2170 · break

aiops2022 / eval / pod / k8s容器进程中止。MRR 1.0000 → 0.0000。

评测标签（仅分析）：{"checkoutservice-1": "45905"}

TEXT：["45905", "7361", "920"]

Pod 45905 exhibits a decisive local root cause with an extreme burst in CFS CPU throttling (peak 61s) and page faults that temporally precedes the latency degradation observed in callers 920 and 849. Topology verification confirms 45905 is an instance of service 920, which is a direct caller of the degraded service 849, consistent with the propagation onset order where 45905's internal resource exhaustion triggers the downstream service faults.

FULL：["7361", "447", "321"]

MET-Z records a system.inode anomaly on node 7361 at +38.0 min that lacks an upstream caller (no A->7361 edges), while node-local logs from pod 45905 show a /dev/vda1 filesystem-event at +20.0 min plus a volume-drop consistent with local disk exhaustion rather than an application-code defect. Temporal G-onset shows node 7361 as the latest/potentially most-severe node signature (severity z=999), and pod 45905 hosts the inodes/tmpfs pressure while co-located pods 36937/99137/82495 remain flat, placing the fault at the node/storage layer rather than the downstream caller pods (18949/99137).

[旧输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s0/outputs/d8818cf3138d99dd712d4b4f90fc437b8826ad68fc46404ff740aa8d2f8c95cb.json) · [新输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s0/outputs/c0c826788a180266d8d1eea3d4c6eddb5284883f61fb3deb6752903baaeebe99.json) · [新输入](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s0/inputs/c0c826788a180266d8d1eea3d4c6eddb5284883f61fb3deb6752903baaeebe99.json)

[模型所见图](../through_RQ3_15_preserved/assets/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s0/renders/c0c826788a180266d8d1eea3d4c6eddb5284883f61fb3deb6752903baaeebe99_0.png)

- M01 / 7361 / system.fs.inodes.used / source_unit: {"details": [{"name": "Reference mean", "value": "1.4M"}, {"name": "Current mean", "value": "1.5M"}, {"name": "Reference SD", "value": "12"}, {"name": "Current SD", "value": "86.2k"}, {"name": "Deviation (sigma)", "value": "2.5k"}]}
- M02 / 7361 / system.fs.inodes.total / source_unit: {"details": [{"name": "Reference mean", "value": "2.9G"}, {"name": "Current mean", "value": "3.0G"}, {"name": "Reference SD", "value": "335.0k"}, {"name": "Current SD", "value": "275.5M"}, {"name": "Deviation (sigma)", "value": "279"}]}
- M03 / 7361 / system.fs.inodes.in_use / source_unit: {"details": [{"name": "Reference mean", "value": "0.98"}, {"name": "Current mean", "value": "0.97"}, {"name": "Reference SD", "value": "1.1e-16"}, {"name": "Current SD", "value": "0.04"}, {"name": "Deviation (sigma)", "value": "113775.1G"}]}
- M04 / 7361 / system.disk.total / source_unit: {"details": [{"name": "Reference mean", "value": "3.8G"}, {"name": "Current mean", "value": "3.9G"}, {"name": "Reference SD", "value": "9.5e-07"}, {"name": "Current SD", "value": "302.0M"}, {"name": "Deviation (sigma)", "value": "108602.8G"}]}
- M05 / 7361 / system.disk.used / source_unit: {"details": [{"name": "Reference mean", "value": "2.8G"}, {"name": "Current mean", "value": "2.9G"}, {"name": "Reference SD", "value": "470.7k"}, {"name": "Current SD", "value": "241.3M"}, {"name": "Deviation (sigma)", "value": "176"}]}
- M06 / 45905 / container_fs_inodes./dev/vda1 / source_unit: {"details": [{"name": "Reference mean", "value": "0.0e+00"}, {"name": "Current mean", "value": "0.05"}, {"name": "Reference SD", "value": "0.0e+00"}, {"name": "Current SD", "value": "0.22"}]}
- M07 / 45905 / container_cpu_cfs_throttled_seconds / source_unit: {"details": [{"name": "Reference mean", "value": "0.30"}, {"name": "Current mean", "value": "3.74"}, {"name": "Reference SD", "value": "1.19"}, {"name": "Current SD", "value": "14"}, {"name": "Deviation (sigma)", "value": "2.90"}]}
- M08 / 45905 / container_memory_failures.container.pgfault / source_unit: {"details": [{"name": "Reference mean", "value": "2.0k"}, {"name": "Current mean", "value": "16.2k"}, {"name": "Reference SD", "value": "8.0k"}, {"name": "Current SD", "value": "59.5k"}, {"name": "Deviation (sigma)", "value": "1.78"}]}
- M09 / 45905 / container_memory_failures.hierarchy.pgfault / source_unit: {"details": [{"name": "Reference mean", "value": "2.0k"}, {"name": "Current mean", "value": "16.2k"}, {"name": "Reference SD", "value": "8.0k"}, {"name": "Current SD", "value": "59.5k"}, {"name": "Deviation (sigma)", "value": "1.78"}]}
- M10 / 79846 / container_cpu_cfs_throttled_seconds / source_unit: {"details": [{"name": "Reference mean", "value": "1.3e-16"}, {"name": "Current mean", "value": "6.5e-03"}, {"name": "Reference SD", "value": "2.0e-16"}, {"name": "Current SD", "value": "0.03"}, {"name": "Deviation (sigma)", "value": "32461.6G"}]}
- M11 / 6040 / system.disk.pct_usage / source_unit: {"details": [{"name": "Reference mean", "value": "40"}, {"name": "Current mean", "value": "40"}, {"name": "Reference SD", "value": "1.4e-14"}, {"name": "Current SD", "value": "4.1e-03"}, {"name": "Deviation (sigma)", "value": "148.1G"}]}
- M12 / 7361 / system.fs.inodes.free / source_unit: {"details": [{"name": "Reference mean", "value": "2.9G"}, {"name": "Current mean", "value": "3.0G"}, {"name": "Reference SD", "value": "335.1k"}, {"name": "Current SD", "value": "275.4M"}, {"name": "Deviation (sigma)", "value": "279"}]}
- R01 / 18949 / hipstershop.818/SendOrderConfirmation / µs: {"after": 61495.25, "before": 33588.5, "details": [{"name": "Reference requests", "value": "31"}, {"name": "Current requests", "value": "24"}, {"name": "Current inclusive p95 (µs)", "value": "61782.15"}, {"name": "Request log2 ratio", "value": "-0.36"}, {"name": "Latency log2 ratio", "value": "0.87"}]}
- R02 / 99137 / hipstershop.818/SendOrderConfirmation / µs: {"after": 25133.65, "before": 4322.0, "details": [{"name": "Reference requests", "value": "21"}, {"name": "Current requests", "value": "20"}, {"name": "Current inclusive p95 (µs)", "value": "25386.15"}, {"name": "Request log2 ratio", "value": "-0.07"}, {"name": "Latency log2 ratio", "value": "2.54"}]}
- R03 / 99137 / hipstershop.920/PlaceOrder / µs: {"after": 11518.05, "before": 10081.0, "details": [{"name": "Reference requests", "value": "21"}, {"name": "Current requests", "value": "20"}, {"name": "Current inclusive p95 (µs)", "value": "66185.45"}, {"name": "Request log2 ratio", "value": "-0.07"}, {"name": "Latency log2 ratio", "value": "0.19"}]}
- R04 / 36596 / hipstershop.920/PlaceOrder / µs: {"after": 2996.7, "before": 2679.0, "details": [{"name": "Reference requests", "value": "21"}, {"name": "Current requests", "value": "20"}, {"name": "Current inclusive p95 (µs)", "value": "69118.25"}, {"name": "Request log2 ratio", "value": "-0.07"}, {"name": "Latency log2 ratio", "value": "0.16"}]}
- R05 / 18949 / hipstershop.700/EmptyCart / µs: {"after": 4977.1, "before": 4156.0, "details": [{"name": "Reference requests", "value": "31"}, {"name": "Current requests", "value": "24"}, {"name": "Current inclusive p95 (µs)", "value": "4977.1"}, {"name": "Request log2 ratio", "value": "-0.36"}, {"name": "Latency log2 ratio", "value": "0.26"}]}
- R06 / 45905 / hipstershop.818/SendOrderConfirmation / µs: {"after": 35585.75, "before": 12643.15, "details": [{"name": "Reference requests", "value": "32"}, {"name": "Current requests", "value": "24"}, {"name": "Current inclusive p95 (µs)", "value": "35812.3"}, {"name": "Request log2 ratio", "value": "-0.4"}, {"name": "Latency log2 ratio", "value": "1.49"}]}

## RQ3.8 · INC-8E1DFDBC7F96 · break

aiops2025 / eval / pod/service / network corrupt。MRR 0.3333 → 0.0000。

评测标签（仅分析）：{"cartservice": "891", "redis-cart": "569", "redis-cart-0": "53329"}

TEXT：["287", "279", "891"]

Service 287 is the root cause, evidenced by a massive exclusive latency spike (11.59 log2 fold change) and a sharp drop in request counts, indicating a local processing bottleneck. Topologically, service 891 calls both 287 and 279, and the 5.9M microsecond inclusive latency in 891's traces matches the latency spikes in its downstream dependencies (287 and 279), confirming that 891's symptoms are downstream consequences rather than the origin.

FULL：["78992", "3477", "817"]

The decisive MET-Z/LOG-R evidence localizes the failure to pod 78992, which logged 285 new 'request complete' errors and a ~30× log-volume drop in bin 2 with no upstream calls to other component pods (only service-level edges). The alternate-origin check is contradicted by healthy co-located resources: node 3477's memory-usage rate actually decreased and its paired pods show no MET-Z anomalies, ruling out a node-level fault, while host-only candidate 62858's CPU/memory lack a supporting upstream latency trigger.

[旧输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s0/outputs/5d2897b770896e94734cff645db727c8577a639623c2f306fbe7e0a2a4c290f9.json) · [新输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s0/outputs/5127ca0e8ec431f334ed1509f2db22f85a33c3c27d9ffa77b61d883ac99dfffa.json) · [新输入](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s0/inputs/5127ca0e8ec431f334ed1509f2db22f85a33c3c27d9ffa77b61d883ac99dfffa.json)

[模型所见图](../through_RQ3_15_preserved/assets/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s0/renders/5127ca0e8ec431f334ed1509f2db22f85a33c3c27d9ffa77b61d883ac99dfffa_0.png)

- M01 / 53329 / rrt_max / source_unit: {"details": [{"name": "Reference mean", "value": "11.7k"}, {"name": "Current mean", "value": "15.6M"}, {"name": "Reference SD", "value": "20.1k"}, {"name": "Current SD", "value": "58.8M"}, {"name": "Deviation (sigma)", "value": "780"}]}
- M02 / 71167 / rrt / source_unit: {"details": [{"name": "Reference mean", "value": "1.4k"}, {"name": "Current mean", "value": "974.7k"}, {"name": "Reference SD", "value": "176"}, {"name": "Current SD", "value": "2.6M"}, {"name": "Deviation (sigma)", "value": "5.5k"}]}
- M03 / 569 / rrt / source_unit: {"details": [{"name": "Reference mean", "value": "209"}, {"name": "Current mean", "value": "749.3k"}, {"name": "Reference SD", "value": "136"}, {"name": "Current SD", "value": "2.8M"}, {"name": "Deviation (sigma)", "value": "5.5k"}]}
- M04 / 62858 / rrt_max / source_unit: {"details": [{"name": "Reference mean", "value": "3.5k"}, {"name": "Current mean", "value": "81.6M"}, {"name": "Reference SD", "value": "1.7k"}, {"name": "Current SD", "value": "185.1M"}, {"name": "Deviation (sigma)", "value": "48.8k"}]}
- M05 / 98098 / pod_memory_working_set_bytes / source_unit: {"details": [{"name": "Reference mean", "value": "26"}, {"name": "Current mean", "value": "15.7k"}, {"name": "Reference SD", "value": "64"}, {"name": "Current SD", "value": "42.0k"}, {"name": "Deviation (sigma)", "value": "246"}]}
- M06 / 569 / rrt_max / source_unit: {"details": [{"name": "Reference mean", "value": "11.7k"}, {"name": "Current mean", "value": "15.6M"}, {"name": "Reference SD", "value": "20.1k"}, {"name": "Current SD", "value": "58.8M"}, {"name": "Deviation (sigma)", "value": "780"}]}
- M07 / 15014 / pod_memory_working_set_bytes / source_unit: {"details": [{"name": "Reference mean", "value": "6.69"}, {"name": "Current mean", "value": "42.7k"}, {"name": "Reference SD", "value": "24"}, {"name": "Current SD", "value": "89.4k"}, {"name": "Deviation (sigma)", "value": "1.8k"}]}
- M08 / 216 / node_filesystem_usage_rate / ratio_or_percent: {"details": [{"name": "Reference mean", "value": "36"}, {"name": "Current mean", "value": "36"}, {"name": "Reference SD", "value": "7.1e-15"}, {"name": "Current SD", "value": "2.5e-03"}, {"name": "Deviation (sigma)", "value": "307.9G"}]}
- M09 / 62858 / rrt / source_unit: {"details": [{"name": "Reference mean", "value": "1.5k"}, {"name": "Current mean", "value": "5.9M"}, {"name": "Reference SD", "value": "254"}, {"name": "Current SD", "value": "8.1M"}, {"name": "Deviation (sigma)", "value": "23.1k"}]}
- M10 / 71167 / rrt_max / source_unit: {"details": [{"name": "Reference mean", "value": "8.2k"}, {"name": "Current mean", "value": "51.0M"}, {"name": "Reference SD", "value": "7.3k"}, {"name": "Current SD", "value": "130.8M"}, {"name": "Deviation (sigma)", "value": "7.0k"}]}
- M11 / 53329 / rrt / source_unit: {"details": [{"name": "Reference mean", "value": "209"}, {"name": "Current mean", "value": "749.3k"}, {"name": "Reference SD", "value": "136"}, {"name": "Current SD", "value": "2.8M"}, {"name": "Deviation (sigma)", "value": "5.5k"}]}
- M12 / 8201 / node_network_receive_bytes_total / source_unit: {"details": [{"name": "Reference mean", "value": "164"}, {"name": "Current mean", "value": "164"}, {"name": "Reference SD", "value": "0.0e+00"}, {"name": "Current SD", "value": "4.8e-03"}]}
- R01 / 891 / 215.891/AddItem / µs: {"after": 2506.0, "before": 2219.0, "details": [{"name": "Reference requests", "value": "147"}, {"name": "Current requests", "value": "80"}, {"name": "Current inclusive p95 (µs)", "value": "5988145.1"}, {"name": "Request log2 ratio", "value": "-0.87"}, {"name": "Latency log2 ratio", "value": "0.18"}]}
- R02 / 759 / /215.759/ListProducts / µs: {"after": 4005.35, "before": 3556.7, "details": [{"name": "Reference requests", "value": "1315"}, {"name": "Current requests", "value": "120"}, {"name": "Current inclusive p95 (µs)", "value": "4091.65"}, {"name": "Request log2 ratio", "value": "-3.44"}, {"name": "Latency log2 ratio", "value": "0.17"}]}
- R03 / 891 / POST /215.891/AddItem / µs: {"after": 2727.9, "before": 1600.0, "details": [{"name": "Reference requests", "value": "147"}, {"name": "Current requests", "value": "80"}, {"name": "Current inclusive p95 (µs)", "value": "5985973.0"}, {"name": "Request log2 ratio", "value": "-0.87"}, {"name": "Latency log2 ratio", "value": "0.77"}]}
- R04 / 279 / 279 / µs: {"after": 2550771.65, "before": 1575.05, "details": [{"name": "Reference requests", "value": "218"}, {"name": "Current requests", "value": "14"}, {"name": "Current inclusive p95 (µs)", "value": "2550771.65"}, {"name": "Request log2 ratio", "value": "-3.87"}, {"name": "Latency log2 ratio", "value": "10.66"}]}
- R05 / 891 / POST /215.891/GetCart / µs: {"after": 2969.1, "before": 1564.0, "details": [{"name": "Reference requests", "value": "1533"}, {"name": "Current requests", "value": "772"}, {"name": "Current inclusive p95 (µs)", "value": "5992122.9"}, {"name": "Request log2 ratio", "value": "-0.99"}, {"name": "Latency log2 ratio", "value": "0.92"}]}
- R06 / 287 / 287 / µs: {"after": 5989888.7, "before": 1948.3, "details": [{"name": "Reference requests", "value": "1680"}, {"name": "Current requests", "value": "852"}, {"name": "Current inclusive p95 (µs)", "value": "5989888.7"}, {"name": "Request log2 ratio", "value": "-0.98"}, {"name": "Latency log2 ratio", "value": "11.59"}]}

## RQ3.8 · INC-0176E922439E · break

aegislab / test / service / HTTPResponseReplaceCode。MRR 1.0000 → 0.0000。

评测标签（仅分析）：{"ts-order-service": "368", "ts-seat-service": "609"}

TEXT：["368", "579", "609"]

Service 368 exhibits the earliest and most severe local performance degradation (MET-Z signed_z 999, onset +4.2m) without any upstream caller edges in the dependency graph, isolating it as the origin rather than a downstream victim like 579 or 609. Verification confirms 368 has no incoming calls, ruling out an upstream trigger, and its latency spike precedes the onset of symptoms in 579 (+4.8m) and 609 (+6.9m), establishing a causal temporal and topological relationship where 579 and 609 are affected callers of the root cause.

FULL：["769", "792", "163"]

Verification confirms that service 769's absolute latency degradation (TRC-L dX=8.48, onset +4.8m) originates locally in service 792 (onset +4.4m, earliest anomaly), whereas the massive p50 spike observed at 769 is a downstream reflection of that local delay. Furthermore, service 163's early latency fault (+4.4m, onset +6.9m) is shown via 609 -> 163 call paths to be a separate co-located CPU/saturation symptom independent from the 792-driven propagation.

[旧输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s1/outputs/7977de50391b0a8e32730be306dc081f0b5a9b0b1a41caba83d34f0bca2183a2.json) · [新输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s1/outputs/c275bd69122bce722fd8b8bae13e1909e1a8156aa3acf59469b62df5a7a9f4d2.json) · [新输入](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s1/inputs/c275bd69122bce722fd8b8bae13e1909e1a8156aa3acf59469b62df5a7a9f4d2.json)

[模型所见图](../through_RQ3_15_preserved/assets/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s1/renders/c275bd69122bce722fd8b8bae13e1909e1a8156aa3acf59469b62df5a7a9f4d2_0.png)

- M01 / 609 / hubble_http_request_duration_p90_seconds / milliseconds_or_source_unit: {"details": [{"name": "Reference mean", "value": "0.03"}, {"name": "Current mean", "value": "0.82"}, {"name": "Reference SD", "value": "0.03"}, {"name": "Current SD", "value": "0.89"}, {"name": "Deviation (sigma)", "value": "24"}]}
- M02 / 769 / hubble_http_request_duration_p50_seconds / milliseconds_or_source_unit: {"details": [{"name": "Reference mean", "value": "0.15"}, {"name": "Current mean", "value": "4.27"}, {"name": "Reference SD", "value": "0.04"}, {"name": "Current SD", "value": "2.98"}, {"name": "Deviation (sigma)", "value": "112"}]}
- M03 / 609 / hubble_http_request_duration_p50_seconds / milliseconds_or_source_unit: {"details": [{"name": "Reference mean", "value": "0.01"}, {"name": "Current mean", "value": "0.07"}, {"name": "Reference SD", "value": "8.2e-03"}, {"name": "Current SD", "value": "0.02"}, {"name": "Deviation (sigma)", "value": "7.54"}]}
- M04 / 792 / hubble_http_request_duration_p95_seconds / milliseconds_or_source_unit: {"details": [{"name": "Reference mean", "value": "0.02"}, {"name": "Current mean", "value": "0.03"}, {"name": "Reference SD", "value": "2.1e-03"}, {"name": "Current SD", "value": "0.03"}, {"name": "Deviation (sigma)", "value": "7.56"}]}
- M05 / 579 / hubble_http_request_duration_p50_seconds / milliseconds_or_source_unit: {"details": [{"name": "Reference mean", "value": "0.03"}, {"name": "Current mean", "value": "3.82"}, {"name": "Reference SD", "value": "6.8e-03"}, {"name": "Current SD", "value": "1.43"}, {"name": "Deviation (sigma)", "value": "554"}]}
- M06 / 579 / hubble_http_request_duration_p90_seconds / milliseconds_or_source_unit: {"details": [{"name": "Reference mean", "value": "0.24"}, {"name": "Current mean", "value": "7.09"}, {"name": "Reference SD", "value": "0.49"}, {"name": "Current SD", "value": "1.96"}, {"name": "Deviation (sigma)", "value": "14"}]}
- M07 / 114 / jvm.system.cpu.load_1m / source_unit: {"details": [{"name": "Reference mean", "value": "3.00"}, {"name": "Current mean", "value": "102"}, {"name": "Reference SD", "value": "1.12"}, {"name": "Current SD", "value": "141"}, {"name": "Deviation (sigma)", "value": "89"}]}
- M08 / 163 / hubble_http_request_duration_p50_seconds / milliseconds_or_source_unit: {"details": [{"name": "Reference mean", "value": "2.6e-03"}, {"name": "Current mean", "value": "6.6e-03"}, {"name": "Reference SD", "value": "6.1e-05"}, {"name": "Current SD", "value": "7.3e-03"}, {"name": "Deviation (sigma)", "value": "66"}]}
- M09 / 224 / hubble_http_request_duration_p90_seconds / milliseconds_or_source_unit: {"details": [{"name": "Reference mean", "value": "0.02"}, {"name": "Current mean", "value": "0.05"}, {"name": "Reference SD", "value": "3.7e-04"}, {"name": "Current SD", "value": "0.05"}, {"name": "Deviation (sigma)", "value": "92"}]}
- M10 / 368 / hubble_http_request_duration_p95_seconds / milliseconds_or_source_unit: {"details": [{"name": "Reference mean", "value": "8.4e-03"}, {"name": "Current mean", "value": "0.25"}, {"name": "Reference SD", "value": "7.9e-04"}, {"name": "Current SD", "value": "0.48"}, {"name": "Deviation (sigma)", "value": "300"}]}
- M11 / 477 / hubble_http_request_duration_p90_seconds / milliseconds_or_source_unit: {"details": [{"name": "Reference mean", "value": "4.5e-03"}, {"name": "Current mean", "value": "6.9e-03"}, {"name": "Reference SD", "value": "2.1e-05"}, {"name": "Current SD", "value": "3.3e-03"}, {"name": "Deviation (sigma)", "value": "112"}]}
- M12 / 631 / jvm.system.cpu.load_1m / source_unit: {"details": [{"name": "Reference mean", "value": "2.84"}, {"name": "Current mean", "value": "122"}, {"name": "Reference SD", "value": "1.06"}, {"name": "Current SD", "value": "147"}, {"name": "Deviation (sigma)", "value": "112"}]}
- R01 / 579 / POST / µs: {"after": 5874263.66, "before": 4326.36, "details": [{"name": "Reference requests", "value": "1977"}, {"name": "Current requests", "value": "359"}, {"name": "Current inclusive p95 (µs)", "value": "7876121.88"}, {"name": "Request log2 ratio", "value": "-2.46"}, {"name": "Latency log2 ratio", "value": "10.41"}]}
- R02 / 769 / POST / µs: {"after": 1593827.06, "before": 4477.0, "details": [{"name": "Reference requests", "value": "623"}, {"name": "Current requests", "value": "26"}, {"name": "Current inclusive p95 (µs)", "value": "60006121.98"}, {"name": "Request log2 ratio", "value": "-4.53"}, {"name": "Latency log2 ratio", "value": "8.48"}]}
- R03 / 199 / POST /api/v1/travelservice/trips/left / µs: {"after": 1019087.73, "before": 2548.39, "details": [{"name": "Reference requests", "value": "159"}, {"name": "Current requests", "value": "12"}, {"name": "Current inclusive p95 (µs)", "value": "20003424.38"}, {"name": "Request log2 ratio", "value": "-3.62"}, {"name": "Latency log2 ratio", "value": "8.64"}]}
- R04 / 199 / GET /api/v1/consignservice/consigns/account/4d2a46c7-71cb-4cf1-b5bb-b68406d9da6f / µs: {"after": 559492.81, "before": 2682.82, "details": [{"name": "Reference requests", "value": "74"}, {"name": "Current requests", "value": "10"}, {"name": "Current inclusive p95 (µs)", "value": "572722.5"}, {"name": "Request log2 ratio", "value": "-2.77"}, {"name": "Latency log2 ratio", "value": "7.7"}]}
- R05 / 579 / TravelController.getTripAllDetailInfo / µs: {"after": 720829.16, "before": 8889.16, "details": [{"name": "Reference requests", "value": "253"}, {"name": "Current requests", "value": "17"}, {"name": "Current inclusive p95 (µs)", "value": "9576584.97"}, {"name": "Request log2 ratio", "value": "-3.82"}, {"name": "Latency log2 ratio", "value": "6.34"}]}
- R06 / 333 / POST /api/v1/travelplanservice/travelPlan/quickest / µs: {"after": 1577255.2, "before": 3947.23, "details": [{"name": "Reference requests", "value": "84"}, {"name": "Current requests", "value": "8"}, {"name": "Current inclusive p95 (µs)", "value": "61583873.82"}, {"name": "Request log2 ratio", "value": "-3.24"}, {"name": "Latency log2 ratio", "value": "8.64"}]}

## RQ3.8 · INC-6BD7198BE675 · unchanged

aegislab / eval / service / NetworkLoss。MRR 0.0000 → 0.0000。

评测标签（仅分析）：{"ts-order-other-service": "774", "ts-security-service": "692"}

TEXT：["946", "605", "152"]

Service 946 is the root cause, evidenced by the highest trace anomaly rank_score (14.3) and a 20-second exclusive latency spike in the 'preserve' operation. This is supported by the topology, where 946 calls 605 (the second-earliest onset) and 152 (the highest severity in R), and the temporal order where 946's high-severity trace onset precedes the secondary symptoms in 152 and 605.

FULL：["706", "758", "822"]

Verification confirms that pod 706 (the 'queue') exhibited the earliest propagated anomaly onset at +5.5m, strictly preceding all other candidate services (the next earliest being +5.8m), establishing it as the temporal origin rather than a downstream symptom. Second check identifies pod 758 (callee of 385) as showing a distinct, isolated mid-series CPU spike at ~bin 30, cleanly distinguishing a root-cause signature from the global, step-wise CPU/memory jumps observed in 706, 822, and the CPU/SVC hosts (509, 605, 765, 866).

[旧输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s0/outputs/8116e986c6354d4f66238a2e49608fab17ccf7169f365926bf54568d4efbda80.json) · [新输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s0/outputs/3ea616aa49f4b9d26ede19a649aecf19cc63844cd9bca47a259e10aee80a703b.json) · [新输入](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s0/inputs/3ea616aa49f4b9d26ede19a649aecf19cc63844cd9bca47a259e10aee80a703b.json)

[模型所见图](../through_RQ3_15_preserved/assets/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s0/renders/3ea616aa49f4b9d26ede19a649aecf19cc63844cd9bca47a259e10aee80a703b_0.png)

- M01 / 765 / jvm.system.cpu.load_1m / source_unit: {"details": [{"name": "Reference mean", "value": "39"}, {"name": "Current mean", "value": "321"}, {"name": "Reference SD", "value": "86"}, {"name": "Current SD", "value": "86"}, {"name": "Deviation (sigma)", "value": "3.26"}]}
- M02 / 866 / container.memory.rss / source_unit: {"details": [{"name": "Reference mean", "value": "9.6M"}, {"name": "Current mean", "value": "10.3M"}, {"name": "Reference SD", "value": "32.7k"}, {"name": "Current SD", "value": "72.1k"}, {"name": "Deviation (sigma)", "value": "22"}]}
- M03 / 677 / jvm.system.cpu.load_1m / source_unit: {"details": [{"name": "Reference mean", "value": "39"}, {"name": "Current mean", "value": "321"}, {"name": "Reference SD", "value": "86"}, {"name": "Current SD", "value": "86"}, {"name": "Deviation (sigma)", "value": "3.26"}]}
- M04 / 519 / jvm.system.cpu.load_1m / source_unit: {"details": [{"name": "Reference mean", "value": "37"}, {"name": "Current mean", "value": "323"}, {"name": "Reference SD", "value": "79"}, {"name": "Current SD", "value": "58"}, {"name": "Deviation (sigma)", "value": "3.62"}]}
- M05 / 509 / jvm.system.cpu.load_1m / source_unit: {"details": [{"name": "Reference mean", "value": "39"}, {"name": "Current mean", "value": "318"}, {"name": "Reference SD", "value": "93"}, {"name": "Current SD", "value": "112"}, {"name": "Deviation (sigma)", "value": "3.00"}]}
- M06 / 822 / k8s.pod.memory.usage / source_unit: {"details": [{"name": "Reference mean", "value": "791.8M"}, {"name": "Current mean", "value": "797.5M"}, {"name": "Reference SD", "value": "4.4M"}, {"name": "Current SD", "value": "152.1k"}, {"name": "Deviation (sigma)", "value": "1.30"}]}
- M07 / 866 / k8s.pod.memory.rss / source_unit: {"details": [{"name": "Reference mean", "value": "9.7M"}, {"name": "Current mean", "value": "10.4M"}, {"name": "Reference SD", "value": "33.6k"}, {"name": "Current SD", "value": "0.0e+00"}, {"name": "Deviation (sigma)", "value": "22"}]}
- M08 / 758 / container.cpu.usage / source_unit: {"details": [{"name": "Reference mean", "value": "0.02"}, {"name": "Current mean", "value": "7.0e-03"}, {"name": "Reference SD", "value": "0.03"}, {"name": "Current SD", "value": "1.4e-03"}, {"name": "Deviation (sigma)", "value": "0.54"}]}
- M09 / 822 / k8s.pod.memory.working_set / source_unit: {"details": [{"name": "Reference mean", "value": "791.4M"}, {"name": "Current mean", "value": "797.2M"}, {"name": "Reference SD", "value": "4.4M"}, {"name": "Current SD", "value": "152.1k"}, {"name": "Deviation (sigma)", "value": "1.30"}]}
- M10 / 385 / jvm.system.cpu.load_1m / source_unit: {"details": [{"name": "Reference mean", "value": "39"}, {"name": "Current mean", "value": "318"}, {"name": "Reference SD", "value": "93"}, {"name": "Current SD", "value": "112"}, {"name": "Deviation (sigma)", "value": "3.00"}]}
- M11 / 706 / k8s.pod.memory.rss / source_unit: {"details": [{"name": "Reference mean", "value": "153.3M"}, {"name": "Current mean", "value": "153.3M"}, {"name": "Reference SD", "value": "4.1k"}, {"name": "Current SD", "value": "17.3k"}, {"name": "Deviation (sigma)", "value": "3.71"}]}
- M12 / 822 / k8s.pod.memory.node.utilization / ratio_or_percent: {"details": [{"name": "Reference mean", "value": "5.9e-03"}, {"name": "Current mean", "value": "5.9e-03"}, {"name": "Reference SD", "value": "3.3e-05"}, {"name": "Current SD", "value": "1.1e-06"}, {"name": "Deviation (sigma)", "value": "1.30"}]}
- R01 / 153 / POST /api/v1/routeplanservice/routePlan/minStopStations / µs: {"after": 1602401.09, "before": 4167.17, "details": [{"name": "Reference requests", "value": "62"}, {"name": "Current requests", "value": "3"}, {"name": "Current inclusive p95 (µs)", "value": "5122633.35"}, {"name": "Request log2 ratio", "value": "-3.98"}, {"name": "Latency log2 ratio", "value": "8.59"}]}
- R02 / 946 / GET /api/v1/foodservice/foods/2025-08-09/shanghai/suzhou/D1345 / µs: {"after": 706972.21, "before": 1731.83, "details": [{"name": "Reference requests", "value": "34"}, {"name": "Current requests", "value": "5"}, {"name": "Current inclusive p95 (µs)", "value": "774639.46"}, {"name": "Request log2 ratio", "value": "-2.54"}, {"name": "Latency log2 ratio", "value": "8.67"}]}
- R03 / 218 / SELECT PriceConfig / µs: {"after": 112991.86, "before": 1114.99, "details": [{"name": "Reference requests", "value": "408"}, {"name": "Current requests", "value": "11"}, {"name": "Current inclusive p95 (µs)", "value": "114780.88"}, {"name": "Request log2 ratio", "value": "-5.09"}, {"name": "Latency log2 ratio", "value": "6.66"}]}
- R04 / 946 / POST /api/v1/preserveservice/preserve / µs: {"after": 20003086.63, "before": 988.17, "details": [{"name": "Reference requests", "value": "142"}, {"name": "Current requests", "value": "10"}, {"name": "Current inclusive p95 (µs)", "value": "20003086.63"}, {"name": "Request log2 ratio", "value": "-3.7"}, {"name": "Latency log2 ratio", "value": "14.3"}]}
- R05 / 692 / GET / µs: {"after": 32550368.89, "before": 2737.65, "details": [{"name": "Reference requests", "value": "283"}, {"name": "Current requests", "value": "11"}, {"name": "Current inclusive p95 (µs)", "value": "32563619.6"}, {"name": "Request log2 ratio", "value": "-4.56"}, {"name": "Latency log2 ratio", "value": "13.54"}]}
- R06 / 946 / GET /api/v1/userservice/users/id/4d2a46c7-71cb-4cf1-b5bb-b68406d9da6f / µs: {"after": 101797.8, "before": 1685.4, "details": [{"name": "Reference requests", "value": "1083"}, {"name": "Current requests", "value": "73"}, {"name": "Current inclusive p95 (µs)", "value": "106232.21"}, {"name": "Request log2 ratio", "value": "-3.87"}, {"name": "Latency log2 ratio", "value": "5.92"}]}

## RQ3.8 · INC-A630AAF01518 · unchanged

aiops2022 / eval / pod / k8s容器cpu负载。MRR 0.0000 → 0.0000。

评测标签（仅分析）：{"productcatalogservice-0": "64716"}

TEXT：["729", "750", "661"]

Service 729 is the top-ranked origin candidate, supported by the top-ranked exclusive latency degradation in its instance 40392 (TRC-L rank_score 6.64) and the earliest onset in its callers 551/952 (M rank 1/2 at +20.0m), preceding downstream degradation in 661/395. Verification confirms the latency anomaly is local to 729's instance (exclusive > baseline, not just inclusive) and that the co-located infrastructure node 6653 shows a contemporaneous disk/inode spike (M +25.0m) that temporally aligns with the fault window, making 729 the most plausible root cause over co-located noise.

FULL：["729", "6653", "692"]

MET-Z shows service 729 (pod 40392) network traffic jump to 25x baseline during the fault window, and pod 64716 has the largest exclusive latency increase (100x, rank_score 6.64) with inclusive=exclusive indicating local processing time; since no upstream service edge exists for 692 in the provided data and node 6653 is healthy, the fault originates in 729's behavior which propagates downstream.

[旧输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s0/outputs/50a1af717c913d7a5d7fa6f918d9b5aaf9eb90bf5eb18f22bb915183cdadbffc.json) · [新输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s0/outputs/21bdf5a74dbb81a65b22412a0a7e04a0780c5a3706239fd8c02f886e327206e3.json) · [新输入](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s0/inputs/21bdf5a74dbb81a65b22412a0a7e04a0780c5a3706239fd8c02f886e327206e3.json)

[模型所见图](../through_RQ3_15_preserved/assets/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s0/renders/21bdf5a74dbb81a65b22412a0a7e04a0780c5a3706239fd8c02f886e327206e3_0.png)

- M01 / 6653 / system.disk.used / source_unit: {"details": [{"name": "Reference mean", "value": "3.7G"}, {"name": "Current mean", "value": "3.8G"}, {"name": "Reference SD", "value": "310.4k"}, {"name": "Current SD", "value": "551.9M"}, {"name": "Deviation (sigma)", "value": "396"}]}
- M02 / 6653 / system.fs.inodes.total / source_unit: {"details": [{"name": "Reference mean", "value": "3.8G"}, {"name": "Current mean", "value": "4.0G"}, {"name": "Reference SD", "value": "233.5k"}, {"name": "Current SD", "value": "578.2M"}, {"name": "Deviation (sigma)", "value": "557"}]}
- M03 / 6194 / system.disk.pct_usage / source_unit: {"details": [{"name": "Reference mean", "value": "41"}, {"name": "Current mean", "value": "41"}, {"name": "Reference SD", "value": "7.1e-15"}, {"name": "Current SD", "value": "3.5e-03"}, {"name": "Deviation (sigma)", "value": "201.1G"}]}
- M04 / 6653 / system.fs.inodes.in_use / source_unit: {"details": [{"name": "Reference mean", "value": "1.17"}, {"name": "Current mean", "value": "1.16"}, {"name": "Reference SD", "value": "2.2e-16"}, {"name": "Current SD", "value": "0.03"}, {"name": "Deviation (sigma)", "value": "34313.1G"}]}
- M05 / 952 / mrt / source_unit: {"details": [{"name": "Reference mean", "value": "1.05"}, {"name": "Current mean", "value": "1.07"}, {"name": "Reference SD", "value": "2.1e-12"}, {"name": "Current SD", "value": "0.15"}, {"name": "Deviation (sigma)", "value": "9.4G"}]}
- M06 / 6653 / system.fs.inodes.free / source_unit: {"details": [{"name": "Reference mean", "value": "3.8G"}, {"name": "Current mean", "value": "4.0G"}, {"name": "Reference SD", "value": "233.5k"}, {"name": "Current SD", "value": "578.0M"}, {"name": "Deviation (sigma)", "value": "557"}]}
- M07 / 6653 / system.disk.total / source_unit: {"details": [{"name": "Reference mean", "value": "5.1G"}, {"name": "Current mean", "value": "5.3G"}, {"name": "Reference SD", "value": "0.0e+00"}, {"name": "Current SD", "value": "681.9M"}]}
- M08 / 6653 / system.fs.inodes.used / source_unit: {"details": [{"name": "Reference mean", "value": "1.6M"}, {"name": "Current mean", "value": "1.6M"}, {"name": "Reference SD", "value": "4.24"}, {"name": "Current SD", "value": "155.4k"}, {"name": "Deviation (sigma)", "value": "8.2k"}]}
- M09 / 551 / jvm_threads_started / source_unit: {"details": [{"name": "Reference mean", "value": "0.0e+00"}, {"name": "Current mean", "value": "0.10"}, {"name": "Reference SD", "value": "0.0e+00"}, {"name": "Current SD", "value": "0.20"}]}
- M10 / 6653 / system.disk.free / source_unit: {"details": [{"name": "Reference mean", "value": "1.4G"}, {"name": "Current mean", "value": "1.4G"}, {"name": "Reference SD", "value": "310.4k"}, {"name": "Current SD", "value": "130.6M"}, {"name": "Deviation (sigma)", "value": "95"}]}
- M11 / 661 / mrt / source_unit: {"details": [{"name": "Reference mean", "value": "50"}, {"name": "Current mean", "value": "221"}, {"name": "Reference SD", "value": "2.02"}, {"name": "Current SD", "value": "312"}, {"name": "Deviation (sigma)", "value": "85"}]}
- M12 / 40392 / container_network_receive_MB.eth0 / source_unit: {"details": [{"name": "Reference mean", "value": "0.03"}, {"name": "Current mean", "value": "0.08"}, {"name": "Reference SD", "value": "1.7e-03"}, {"name": "Current SD", "value": "0.18"}, {"name": "Deviation (sigma)", "value": "34"}]}
- R01 / 83464 / hipstershop.692/GetProduct / µs: {"after": 83515.9, "before": 2468.85, "details": [{"name": "Reference requests", "value": "4684"}, {"name": "Current requests", "value": "4343"}, {"name": "Current inclusive p95 (µs)", "value": "395928.8"}, {"name": "Request log2 ratio", "value": "-0.11"}, {"name": "Latency log2 ratio", "value": "5.08"}]}
- R02 / 88157 / hipstershop.692/GetProduct / µs: {"after": 82289.0, "before": 2590.4, "details": [{"name": "Reference requests", "value": "2287"}, {"name": "Current requests", "value": "2192"}, {"name": "Current inclusive p95 (µs)", "value": "328674.3"}, {"name": "Request log2 ratio", "value": "-0.06"}, {"name": "Latency log2 ratio", "value": "4.99"}]}
- R03 / 55242 / hipstershop.692/GetProduct / µs: {"after": 81352.0, "before": 2584.0, "details": [{"name": "Reference requests", "value": "4701"}, {"name": "Current requests", "value": "4469"}, {"name": "Current inclusive p95 (µs)", "value": "293458.4"}, {"name": "Request log2 ratio", "value": "-0.07"}, {"name": "Latency log2 ratio", "value": "4.98"}]}
- R04 / 88157 / hipstershop.692/ListProducts / µs: {"after": 70021.2, "before": 2608.8, "details": [{"name": "Reference requests", "value": "63"}, {"name": "Current requests", "value": "57"}, {"name": "Current inclusive p95 (µs)", "value": "70047.2"}, {"name": "Request log2 ratio", "value": "-0.14"}, {"name": "Latency log2 ratio", "value": "4.75"}]}
- R05 / 64716 / hipstershop.692/GetProduct / µs: {"after": 599898.8, "before": 6033.1, "details": [{"name": "Reference requests", "value": "3950"}, {"name": "Current requests", "value": "3733"}, {"name": "Current inclusive p95 (µs)", "value": "599898.8"}, {"name": "Request log2 ratio", "value": "-0.08"}, {"name": "Latency log2 ratio", "value": "6.64"}]}
- R06 / 57968 / /hipstershop.692/ListProducts / µs: {"after": 75303.25, "before": 2701.95, "details": [{"name": "Reference requests", "value": "622"}, {"name": "Current requests", "value": "586"}, {"name": "Current inclusive p95 (µs)", "value": "75887.25"}, {"name": "Request log2 ratio", "value": "-0.09"}, {"name": "Latency log2 ratio", "value": "4.8"}]}

## RQ3.8 · INC-EDDC755A08F5 · unchanged

aiops2025 / eval / service / pod failure。MRR 0.0000 → 0.0000。

评测标签（仅分析）：{"tidb-tikv": "955"}

TEXT：["207", "243", "207"]

Service 207 is the root cause, evidenced by a drop in memory usage and a burst of failed_query_ops occurring during the estimated fault window, which precedes the latency spikes in downstream services. The topology confirms 207 is a downstream dependency of the failing services (334, 903), ruling out 207's symptoms as merely co-located noise. The fault originates in the query operation of service 207, causing the observed latency and error propagation in the calling services.

FULL：["207", "243", "130"]

Top-1 207 is verified: (1) its failure indicators are among the earliest in the recorded telemetry (anomaly onset +16.0 min, with duration/failed-query jumps at ~relative bin 35 and an estimated fault window +14.0 to +18.0 min), and (2) no upstream caller edge in G invokes 207, so no demonstrated upstream service origin exists to contradict its candidacy. The decisive relation is that 207's onset immediately precedes the widespread caller-side latency onset cluster (e.g., 531 at +14.2 min trace evidence, 334 at +15.0 min, 903 at +14.2 min) and that 207 has no upstream caller in the observed call graph.

[旧输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s1/outputs/cc2467e3980f8469da124aade02c241e074ab025c9dc1a76817d72c416eedf0f.json) · [新输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s1/outputs/f449d941072884ef1da314e0fbec0f29afcd70978caf97029de6669b92e429c7.json) · [新输入](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s1/inputs/f449d941072884ef1da314e0fbec0f29afcd70978caf97029de6669b92e429c7.json)

[模型所见图](../through_RQ3_15_preserved/assets/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s1/renders/f449d941072884ef1da314e0fbec0f29afcd70978caf97029de6669b92e429c7_0.png)

- M01 / 334 / rrt / source_unit: {"details": [{"name": "Reference mean", "value": "7.3k"}, {"name": "Current mean", "value": "5.2M"}, {"name": "Reference SD", "value": "693"}, {"name": "Current SD", "value": "9.6M"}, {"name": "Deviation (sigma)", "value": "7.4k"}]}
- M02 / 207 / duration_avg / milliseconds_or_source_unit: {"details": [{"name": "Reference mean", "value": "0.0e+00"}, {"name": "Current mean", "value": "15"}, {"name": "Reference SD", "value": "0.0e+00"}, {"name": "Current SD", "value": "8.18"}]}
- M03 / 73637 / rrt / source_unit: {"details": [{"name": "Reference mean", "value": "7.1k"}, {"name": "Current mean", "value": "2.7M"}, {"name": "Reference SD", "value": "905"}, {"name": "Current SD", "value": "1.9M"}, {"name": "Deviation (sigma)", "value": "3.0k"}]}
- M04 / 207 / duration_99th / milliseconds_or_source_unit: {"details": [{"name": "Reference mean", "value": "1.0e-02"}, {"name": "Current mean", "value": "54"}, {"name": "Reference SD", "value": "1.7e-18"}, {"name": "Current SD", "value": "23"}, {"name": "Deviation (sigma)", "value": "31303980577.9G"}]}
- M05 / 243 / store_unhealth_count / source_unit: {"details": [{"name": "Reference mean", "value": "0.0e+00"}, {"name": "Current mean", "value": "0.25"}, {"name": "Reference SD", "value": "0.0e+00"}, {"name": "Current SD", "value": "0.43"}]}
- M06 / 207 / memory_usage / source_unit: {"details": [{"name": "Reference mean", "value": "1.1G"}, {"name": "Current mean", "value": "680.4M"}, {"name": "Reference SD", "value": "0.0e+00"}, {"name": "Current SD", "value": "193.2M"}]}
- M07 / 96154 / rrt / source_unit: {"details": [{"name": "Reference mean", "value": "7.3k"}, {"name": "Current mean", "value": "5.2M"}, {"name": "Reference SD", "value": "693"}, {"name": "Current SD", "value": "9.6M"}, {"name": "Deviation (sigma)", "value": "7.4k"}]}
- M08 / 48810 / pod_memory_working_set_bytes / source_unit: {"details": [{"name": "Reference mean", "value": "12"}, {"name": "Current mean", "value": "475.0k"}, {"name": "Reference SD", "value": "43"}, {"name": "Current SD", "value": "1.8M"}, {"name": "Deviation (sigma)", "value": "11.1k"}]}
- M09 / 73637 / rrt_max / source_unit: {"details": [{"name": "Reference mean", "value": "13.5k"}, {"name": "Current mean", "value": "26.9M"}, {"name": "Reference SD", "value": "2.6k"}, {"name": "Current SD", "value": "19.0M"}, {"name": "Deviation (sigma)", "value": "10.3k"}]}
- M10 / 207 / failed_query_ops / source_unit: {"details": [{"name": "Reference mean", "value": "0.0e+00"}, {"name": "Current mean", "value": "3.58"}, {"name": "Reference SD", "value": "0.0e+00"}, {"name": "Current SD", "value": "1.64"}]}
- M11 / 243 / store_up_count / source_unit: {"details": [{"name": "Reference mean", "value": "1.00"}, {"name": "Current mean", "value": "0.12"}, {"name": "Reference SD", "value": "0.0e+00"}, {"name": "Current SD", "value": "0.33"}]}
- M12 / 207 / duration_95th / milliseconds_or_source_unit: {"details": [{"name": "Reference mean", "value": "1.0e-02"}, {"name": "Current mean", "value": "51"}, {"name": "Reference SD", "value": "1.7e-18"}, {"name": "Current SD", "value": "24"}, {"name": "Deviation (sigma)", "value": "29156303987.6G"}]}
- R01 / 531 / 130.531/GetProduct / µs: {"after": 40280141.0, "before": 13248.0, "details": [{"name": "Reference requests", "value": "16101"}, {"name": "Current requests", "value": "1451"}, {"name": "Current inclusive p95 (µs)", "value": "40290533.0"}, {"name": "Request log2 ratio", "value": "-3.47"}, {"name": "Latency log2 ratio", "value": "11.57"}]}
- R02 / 959 / 130.959/GetCart / µs: {"after": 6255.8, "before": 4737.4, "details": [{"name": "Reference requests", "value": "1489"}, {"name": "Current requests", "value": "165"}, {"name": "Current inclusive p95 (µs)", "value": "8478.2"}, {"name": "Request log2 ratio", "value": "-3.17"}, {"name": "Latency log2 ratio", "value": "0.4"}]}
- R03 / 531 / 130.531/ListProducts / µs: {"after": 2034.0, "before": 1702.75, "details": [{"name": "Reference requests", "value": "1714"}, {"name": "Current requests", "value": "201"}, {"name": "Current inclusive p95 (µs)", "value": "2093.0"}, {"name": "Request log2 ratio", "value": "-3.09"}, {"name": "Latency log2 ratio", "value": "0.26"}]}
- R04 / 867 / /130.867/SendOrderConfirmation / µs: {"after": 1063.1, "before": 979.5, "details": [{"name": "Reference requests", "value": "74"}, {"name": "Current requests", "value": "12"}, {"name": "Current inclusive p95 (µs)", "value": "1063.1"}, {"name": "Request log2 ratio", "value": "-2.53"}, {"name": "Latency log2 ratio", "value": "0.12"}]}
- R05 / 852 / 130.852/ShipOrder / µs: {"after": 31694.7, "before": 7665.7, "details": [{"name": "Reference requests", "value": "148"}, {"name": "Current requests", "value": "24"}, {"name": "Current inclusive p95 (µs)", "value": "31948.6"}, {"name": "Request log2 ratio", "value": "-2.58"}, {"name": "Latency log2 ratio", "value": "2.05"}]}
- R06 / 193 / 193 / µs: {"after": 4383.95, "before": 2885.0, "details": [{"name": "Reference requests", "value": "212"}, {"name": "Current requests", "value": "24"}, {"name": "Current inclusive p95 (µs)", "value": "4383.95"}, {"name": "Request log2 ratio", "value": "-3.09"}, {"name": "Latency log2 ratio", "value": "0.6"}]}

## RQ3.8 · INC-E5AC8B5D69F1 · unchanged

aegislab / test / service / JVMMemoryStress。MRR 1.0000 → 1.0000。

评测标签（仅分析）：{"ts-order-service": "117"}

TEXT：["117", "273", "58787"]

Service 117 is the origin, confirmed by the top-ranked propagation onset at +4.2m and exclusive latency p95 shifts (e.g., OrderRepository.findByAccountIdAndTrainNumberAndTravelDate rank_score 2.11) that are not explained by upstream callers. The alternative origin of a node failure is contradicted by the absence of restarts on the host node 4432 and its co-located pods 77924 and 64178, while the restart of pod 58787 (instance of 117) is a co-located symptom of the memory spike.

FULL：["117", "273", "128"]

Verification confirms that pod 58787 (the sole instance of service 117) is the origin: it is the only instance to show a container restart (k8s.container.restarts from 0 to 1), concurrent with severe, >3σ memory spikes (working set utilization hitting 0.63) that explain the sustained degradation in service 117's local latency (TRC-L exclusive latency p95 jumped from ~214µs to ~928µs). An alternative database-origin hypothesis is ruled out because the database service (128) and its queried pod (82932) show no anomalies—log errors on 82932 (aborted connection) are entirely consistent with a crash/restart of its caller (pod 58787) rather than a database fault, and the temporal onset of the restart and memory spikes in service 117 precedes the anomaly manifestations in its callers like 273.

[旧输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s0/outputs/7b9180918de4ade3c6c802c887ef6378f27a26ab7f60f54e73944976e23fa1a6.json) · [新输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s0/outputs/f39eb8274265ea0b63826da4acfca465a578252336c40bdded0b6cb30bda0d4e.json) · [新输入](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s0/inputs/f39eb8274265ea0b63826da4acfca465a578252336c40bdded0b6cb30bda0d4e.json)

[模型所见图](../through_RQ3_15_preserved/assets/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s0/renders/f39eb8274265ea0b63826da4acfca465a578252336c40bdded0b6cb30bda0d4e_0.png)

- M01 / 117 / container.memory.working_set / source_unit: {"details": [{"name": "Reference mean", "value": "836.2M"}, {"name": "Current mean", "value": "801.1M"}, {"name": "Reference SD", "value": "2.7M"}, {"name": "Current SD", "value": "325.9M"}, {"name": "Deviation (sigma)", "value": "13"}]}
- M02 / 117 / k8s.pod.memory_limit_utilization / ratio_or_percent: {"details": [{"name": "Reference mean", "value": "0.19"}, {"name": "Current mean", "value": "0.21"}, {"name": "Reference SD", "value": "6.1e-04"}, {"name": "Current SD", "value": "0.12"}, {"name": "Deviation (sigma)", "value": "31"}]}
- M03 / 117 / k8s.pod.memory.available / source_unit: {"details": [{"name": "Reference mean", "value": "3.5G"}, {"name": "Current mean", "value": "3.4G"}, {"name": "Reference SD", "value": "2.6M"}, {"name": "Current SD", "value": "507.5M"}, {"name": "Deviation (sigma)", "value": "31"}]}
- M04 / 117 / k8s.pod.memory.rss / source_unit: {"details": [{"name": "Reference mean", "value": "825.4M"}, {"name": "Current mean", "value": "905.2M"}, {"name": "Reference SD", "value": "2.6M"}, {"name": "Current SD", "value": "506.5M"}, {"name": "Deviation (sigma)", "value": "30"}]}
- M05 / 117 / container.memory.available / source_unit: {"details": [{"name": "Reference mean", "value": "3.5G"}, {"name": "Current mean", "value": "3.5G"}, {"name": "Reference SD", "value": "2.7M"}, {"name": "Current SD", "value": "317.3M"}, {"name": "Deviation (sigma)", "value": "11"}]}
- M06 / 58787 / k8s.container.restarts / source_unit: {"details": [{"name": "Reference mean", "value": "0.0e+00"}, {"name": "Current mean", "value": "0.79"}, {"name": "Reference SD", "value": "0.0e+00"}, {"name": "Current SD", "value": "0.41"}]}
- M07 / 117 / k8s.pod.memory.node.utilization / ratio_or_percent: {"details": [{"name": "Reference mean", "value": "6.2e-03"}, {"name": "Current mean", "value": "6.8e-03"}, {"name": "Reference SD", "value": "1.9e-05"}, {"name": "Current SD", "value": "3.8e-03"}, {"name": "Deviation (sigma)", "value": "31"}]}
- M08 / 117 / container.memory.rss / source_unit: {"details": [{"name": "Reference mean", "value": "825.1M"}, {"name": "Current mean", "value": "794.9M"}, {"name": "Reference SD", "value": "2.8M"}, {"name": "Current SD", "value": "317.0M"}, {"name": "Deviation (sigma)", "value": "11"}]}
- M09 / 117 / k8s.pod.memory.working_set / source_unit: {"details": [{"name": "Reference mean", "value": "837.0M"}, {"name": "Current mean", "value": "917.4M"}, {"name": "Reference SD", "value": "2.6M"}, {"name": "Current SD", "value": "507.5M"}, {"name": "Deviation (sigma)", "value": "31"}]}
- M10 / 117 / container.filesystem.usage / source_unit: {"details": [{"name": "Reference mean", "value": "466.9k"}, {"name": "Current mean", "value": "620.7k"}, {"name": "Reference SD", "value": "0.0e+00"}, {"name": "Current SD", "value": "620.6k"}]}
- M11 / 117 / container.memory.usage / source_unit: {"details": [{"name": "Reference mean", "value": "836.6M"}, {"name": "Current mean", "value": "807.1M"}, {"name": "Reference SD", "value": "2.7M"}, {"name": "Current SD", "value": "317.3M"}, {"name": "Deviation (sigma)", "value": "11"}]}
- M12 / 117 / k8s.pod.memory.usage / source_unit: {"details": [{"name": "Reference mean", "value": "837.4M"}, {"name": "Current mean", "value": "917.7M"}, {"name": "Reference SD", "value": "2.6M"}, {"name": "Current SD", "value": "507.5M"}, {"name": "Deviation (sigma)", "value": "31"}]}
- R01 / 759 / POST /api/v1/travelplanservice/travelPlan/minStation / µs: {"after": 2575.0, "before": 1308.56, "details": [{"name": "Reference requests", "value": "48"}, {"name": "Current requests", "value": "100"}, {"name": "Current inclusive p95 (µs)", "value": "1448819.11"}, {"name": "Request log2 ratio", "value": "1.04"}, {"name": "Latency log2 ratio", "value": "0.98"}]}
- R02 / 117 / OrderRepository.findByAccountIdAndTrainNumberAndTravelDate / µs: {"after": 928.25, "before": 214.92, "details": [{"name": "Reference requests", "value": "114"}, {"name": "Current requests", "value": "105"}, {"name": "Current inclusive p95 (µs)", "value": "8060.59"}, {"name": "Request log2 ratio", "value": "-0.12"}, {"name": "Latency log2 ratio", "value": "2.11"}]}
- R03 / 117 / Session.find order.entity.Order / µs: {"after": 2398.49, "before": 615.39, "details": [{"name": "Reference requests", "value": "84"}, {"name": "Current requests", "value": "54"}, {"name": "Current inclusive p95 (µs)", "value": "3670.29"}, {"name": "Request log2 ratio", "value": "-0.63"}, {"name": "Latency log2 ratio", "value": "1.96"}]}
- R04 / 562 / HTTP GET http://759:8080/api/v1/cancelservice/cancel/{orderId}/{loginId} / µs: {"after": 4784.51, "before": 794.23, "details": [{"name": "Reference requests", "value": "7"}, {"name": "Current requests", "value": "5"}, {"name": "Current inclusive p95 (µs)", "value": "101294.42"}, {"name": "Request log2 ratio", "value": "-0.42"}, {"name": "Latency log2 ratio", "value": "2.59"}]}
- R05 / 180 / FoodOrderRepository.findByOrderId / µs: {"after": 3575.06, "before": 818.83, "details": [{"name": "Reference requests", "value": "38"}, {"name": "Current requests", "value": "20"}, {"name": "Current inclusive p95 (µs)", "value": "8449.11"}, {"name": "Request log2 ratio", "value": "-0.89"}, {"name": "Latency log2 ratio", "value": "2.12"}]}
- R06 / 117 / Session.merge order.entity.Order / µs: {"after": 2083.97, "before": 551.14, "details": [{"name": "Reference requests", "value": "76"}, {"name": "Current requests", "value": "46"}, {"name": "Current inclusive p95 (µs)", "value": "2690.76"}, {"name": "Request log2 ratio", "value": "-0.71"}, {"name": "Latency log2 ratio", "value": "1.92"}]}

## RQ3.8 · INC-D6CF4BA65A45 · unchanged

aiops2022 / test / service / k8s容器网络丢包。MRR 0.0000 → 0.0000。

评测标签（仅分析）：{"productcatalogservice": "826"}

TEXT：["895", "743", "61445"]

Service 895 is the only candidate with a direct MET-Z 3-sigma metric deviation showing a distinct tenured heap usage shift from 22.9M to 23.1M, whereas other ranked candidates like 743 and 61445 exhibit normal metric baselines or minor fluctuation. Topology confirms 895 is a plausible origin as it is not a callee of the downstream order-flow services (695, 655) that display the primary trace latency and log errors.

FULL：["743", "895", "125"]

Top-1 candidate 743 is confirmed by (1) the earliest propagated anomaly onset at +21.0m (rank 1), preceding other services, and (2) node 7328 — its host and the host of pods 46049/53257 — carrying a decisive log burst (LT48 new_errors +100, error rate 0.45, volume drop) from within 743's own instances; no upstream calls 743, eliminating an alternative origin. 895 follows due to a correlated MET-Z Tenured_Gen memory shift, and 125 due to downstream propagation order.

[旧输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s0/outputs/1b3b18cb6c2c2c933ff5debb85a2b3050098e45129e79b1701b8ae58d9d61602.json) · [新输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s0/outputs/98dd1b130ca00ae4547afbda94f0b56c71dff4dd42697e3e6d3e3f043f59ff82.json) · [新输入](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s0/inputs/98dd1b130ca00ae4547afbda94f0b56c71dff4dd42697e3e6d3e3f043f59ff82.json)

[模型所见图](../through_RQ3_15_preserved/assets/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s0/renders/98dd1b130ca00ae4547afbda94f0b56c71dff4dd42697e3e6d3e3f043f59ff82_0.png)

- M01 / 895 / java_lang_MemoryPool_Usage_used.Tenured_Gen / source_unit: {"details": [{"name": "Reference mean", "value": "22.9M"}, {"name": "Current mean", "value": "23.1M"}, {"name": "Reference SD", "value": "134"}, {"name": "Current SD", "value": "97.5k"}, {"name": "Deviation (sigma)", "value": "1.1k"}]}
- M02 / 895 / java_lang_MemoryPool_PeakUsage_used.Tenured_Gen / source_unit: {"details": [{"name": "Reference mean", "value": "22.9M"}, {"name": "Current mean", "value": "23.1M"}, {"name": "Reference SD", "value": "134"}, {"name": "Current SD", "value": "97.5k"}, {"name": "Deviation (sigma)", "value": "1.1k"}]}
- M03 / 895 / java_lang_GarbageCollector_LastGcInfo_memoryUsageAfterGc_used.Tenured_Gen.Copy / source_unit: {"details": [{"name": "Reference mean", "value": "22.9M"}, {"name": "Current mean", "value": "23.1M"}, {"name": "Reference SD", "value": "134"}, {"name": "Current SD", "value": "97.5k"}, {"name": "Deviation (sigma)", "value": "1.1k"}]}
- M04 / 14748 / istio_requests.http.0. / source_unit: {"details": [{"name": "Reference mean", "value": "0.0e+00"}, {"name": "Current mean", "value": "0.33"}, {"name": "Reference SD", "value": "0.0e+00"}, {"name": "Current SD", "value": "0.66"}]}
- M05 / 678 / jvm_threads_started / source_unit: {"details": [{"name": "Reference mean", "value": "0.0e+00"}, {"name": "Current mean", "value": "0.10"}, {"name": "Reference SD", "value": "0.0e+00"}, {"name": "Current SD", "value": "0.33"}]}
- M06 / 14748 / istio_request_duration_milliseconds.http.0. / milliseconds_or_source_unit: {"details": [{"name": "Reference mean", "value": "0.0e+00"}, {"name": "Current mean", "value": "19.9k"}, {"name": "Reference SD", "value": "0.0e+00"}, {"name": "Current SD", "value": "39.4k"}]}
- M07 / 895 / java_lang_GarbageCollector_LastGcInfo_memoryUsageBeforeGc_used.Tenured_Gen.Copy / source_unit: {"details": [{"name": "Reference mean", "value": "22.9M"}, {"name": "Current mean", "value": "23.1M"}, {"name": "Reference SD", "value": "134"}, {"name": "Current SD", "value": "98.4k"}, {"name": "Deviation (sigma)", "value": "1.1k"}]}
- M08 / 678 / jvm_memory_MB_used.nonheap / source_unit: {"details": [{"name": "Reference mean", "value": "55"}, {"name": "Current mean", "value": "55"}, {"name": "Reference SD", "value": "7.1e-15"}, {"name": "Current SD", "value": "0.03"}, {"name": "Deviation (sigma)", "value": "6019.9G"}]}
- M09 / 895 / jvm_memory_pool_allocated_MB_total.Tenured_Gen / source_unit: {"details": [{"name": "Reference mean", "value": "28"}, {"name": "Current mean", "value": "28"}, {"name": "Reference SD", "value": "1.3e-04"}, {"name": "Current SD", "value": "0.09"}, {"name": "Deviation (sigma)", "value": "1.1k"}]}
- M10 / 895 / jvm_threads_started / source_unit: {"details": [{"name": "Reference mean", "value": "0.0e+00"}, {"name": "Current mean", "value": "0.10"}, {"name": "Reference SD", "value": "0.0e+00"}, {"name": "Current SD", "value": "0.31"}]}
- M11 / 14748 / istio_request_bytes.http.0. / source_unit: {"details": [{"name": "Reference mean", "value": "0.0e+00"}, {"name": "Current mean", "value": "119"}, {"name": "Reference SD", "value": "0.0e+00"}, {"name": "Current SD", "value": "236"}]}
- M12 / 895 / jvm_memory_pool_MB_used.Tenured_Gen / source_unit: {"details": [{"name": "Reference mean", "value": "22"}, {"name": "Current mean", "value": "22"}, {"name": "Reference SD", "value": "1.3e-04"}, {"name": "Current SD", "value": "0.09"}, {"name": "Deviation (sigma)", "value": "1.1k"}]}
- R01 / 53257 / hipstershop.655/AddItem / µs: {"after": 2486.5, "before": 2289.0, "details": [{"name": "Reference requests", "value": "20"}, {"name": "Current requests", "value": "51"}, {"name": "Current inclusive p95 (µs)", "value": "3486.5"}, {"name": "Request log2 ratio", "value": "1.31"}, {"name": "Latency log2 ratio", "value": "0.12"}]}
- R02 / 61445 / hipstershop.221/SendOrderConfirmation / µs: {"after": 41942.2, "before": 4908.15, "details": [{"name": "Reference requests", "value": "22"}, {"name": "Current requests", "value": "19"}, {"name": "Current inclusive p95 (µs)", "value": "42188.6"}, {"name": "Request log2 ratio", "value": "-0.2"}, {"name": "Latency log2 ratio", "value": "3.09"}]}
- R03 / 61445 / hipstershop.655/EmptyCart / µs: {"after": 34190.6, "before": 4114.45, "details": [{"name": "Reference requests", "value": "22"}, {"name": "Current requests", "value": "19"}, {"name": "Current inclusive p95 (µs)", "value": "34190.6"}, {"name": "Request log2 ratio", "value": "-0.2"}, {"name": "Latency log2 ratio", "value": "3.05"}]}
- R04 / 35572 / hipstershop.695/PlaceOrder / µs: {"after": 43725.2, "before": 10075.85, "details": [{"name": "Reference requests", "value": "42"}, {"name": "Current requests", "value": "25"}, {"name": "Current inclusive p95 (µs)", "value": "85312.6"}, {"name": "Request log2 ratio", "value": "-0.73"}, {"name": "Latency log2 ratio", "value": "2.12"}]}
- R05 / 86706 / hipstershop.221/SendOrderConfirmation / µs: {"after": 44082.9, "before": 7879.0, "details": [{"name": "Reference requests", "value": "21"}, {"name": "Current requests", "value": "18"}, {"name": "Current inclusive p95 (µs)", "value": "44342.0"}, {"name": "Request log2 ratio", "value": "-0.21"}, {"name": "Latency log2 ratio", "value": "2.48"}]}
- R06 / 53257 / hipstershop.655/GetCart / µs: {"after": 3034.0, "before": 2832.0, "details": [{"name": "Reference requests", "value": "201"}, {"name": "Current requests", "value": "504"}, {"name": "Current inclusive p95 (µs)", "value": "3034.0"}, {"name": "Request log2 ratio", "value": "1.32"}, {"name": "Latency log2 ratio", "value": "0.1"}]}

## RQ3.8 · INC-88391D803008 · unchanged

aiops2025 / test / service / io fault。MRR 0.0000 → 0.0000。

评测标签（仅分析）：{"tidb-tikv": "627"}

TEXT：["619", "21780", "22676"]

Service 619 is the root cause as it is the earliest onset anomaly at +14.2m (Rank 1) in the propagation graph and acts as the caller to downstream services 588, 445, and 456 which show subsequent degradation. The specific failure mechanism is a memory leak in pod 21780 (instance of 619), evidenced by a 30,000x spike in working set memory (M1) at the start of the fault window, which is not contradicted by the stable metrics of upstream or unrelated co-located nodes.

FULL：["619", "886", "128"]

Top-1 619 is verified: (1) it is the earliest and only rank-1 TRC-L onset at +14.2m, preceding all other metric onsets by at least ~0.8m and consistent with the fault window opening at +14.0m, and (2) in G it is a pure caller (edges to 128, 194, 445, 456, 588, 604, 886) with no observed upstream caller in the same window, supporting origin rather than downstream amplification. No evidence contradicts 619 (its own R rank is far stronger than downstream 886's +24.5m z=4.28, and no edge shows an earlier source invoking 619).

[旧输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s1/outputs/78940c7697b866909522c04d1bd920d21e13a72b144d167069f1d7fc6a5127e9.json) · [新输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s1/outputs/98dd177f7a1745e4da2a7cff8773a84b18c57e0cdc9259e59c636682195391b2.json) · [新输入](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s1/inputs/98dd177f7a1745e4da2a7cff8773a84b18c57e0cdc9259e59c636682195391b2.json)

[模型所见图](../through_RQ3_15_preserved/assets/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s1/renders/98dd177f7a1745e4da2a7cff8773a84b18c57e0cdc9259e59c636682195391b2_0.png)

- M01 / 652 / duration_avg / milliseconds_or_source_unit: {"details": [{"name": "Reference mean", "value": "0.0e+00"}, {"name": "Current mean", "value": "4.4e-03"}, {"name": "Reference SD", "value": "0.0e+00"}, {"name": "Current SD", "value": "0.01"}]}
- M02 / 6357 / node_network_transmit_packets_total / source_unit: {"details": [{"name": "Reference mean", "value": "1.20"}, {"name": "Current mean", "value": "1.22"}, {"name": "Reference SD", "value": "2.2e-16"}, {"name": "Current SD", "value": "0.03"}, {"name": "Deviation (sigma)", "value": "87570.0G"}]}
- M03 / 6357 / node_network_receive_packets_total / source_unit: {"details": [{"name": "Reference mean", "value": "1.20"}, {"name": "Current mean", "value": "1.22"}, {"name": "Reference SD", "value": "2.2e-16"}, {"name": "Current SD", "value": "0.03"}, {"name": "Deviation (sigma)", "value": "87570.0G"}]}
- M04 / 627 / raft_apply_wait / source_unit: {"details": [{"name": "Reference mean", "value": "0.0e+00"}, {"name": "Current mean", "value": "4.4e-03"}, {"name": "Reference SD", "value": "0.0e+00"}, {"name": "Current SD", "value": "0.02"}]}
- M05 / 301 / node_filesystem_usage_rate / ratio_or_percent: {"details": [{"name": "Reference mean", "value": "48"}, {"name": "Current mean", "value": "48"}, {"name": "Reference SD", "value": "7.1e-15"}, {"name": "Current SD", "value": "4.1e-03"}, {"name": "Deviation (sigma)", "value": "469.1G"}]}
- M06 / 9702 / node_network_receive_bytes_total / source_unit: {"details": [{"name": "Reference mean", "value": "164"}, {"name": "Current mean", "value": "164"}, {"name": "Reference SD", "value": "2.8e-14"}, {"name": "Current SD", "value": "6.9e-03"}, {"name": "Deviation (sigma)", "value": "58.6G"}]}
- M07 / 6357 / node_network_receive_bytes_total / source_unit: {"details": [{"name": "Reference mean", "value": "118"}, {"name": "Current mean", "value": "119"}, {"name": "Reference SD", "value": "2.8e-14"}, {"name": "Current SD", "value": "1.25"}, {"name": "Deviation (sigma)", "value": "27365.6G"}]}
- M08 / 22676 / pod_memory_working_set_bytes / source_unit: {"details": [{"name": "Reference mean", "value": "1.5k"}, {"name": "Current mean", "value": "36.5k"}, {"name": "Reference SD", "value": "715"}, {"name": "Current SD", "value": "144.4k"}, {"name": "Deviation (sigma)", "value": "49"}]}
- M09 / 652 / duration_99th / milliseconds_or_source_unit: {"details": [{"name": "Reference mean", "value": "1.0e-02"}, {"name": "Current mean", "value": "0.03"}, {"name": "Reference SD", "value": "1.7e-18"}, {"name": "Current SD", "value": "0.07"}, {"name": "Deviation (sigma)", "value": "10248191.2G"}]}
- M10 / 21780 / pod_memory_working_set_bytes / source_unit: {"details": [{"name": "Reference mean", "value": "327"}, {"name": "Current mean", "value": "552.8k"}, {"name": "Reference SD", "value": "52"}, {"name": "Current SD", "value": "2.3M"}, {"name": "Deviation (sigma)", "value": "10.6k"}]}
- M11 / 483 / node_filesystem_usage_rate / ratio_or_percent: {"details": [{"name": "Reference mean", "value": "36"}, {"name": "Current mean", "value": "36"}, {"name": "Reference SD", "value": "0.0e+00"}, {"name": "Current SD", "value": "1.9e-03"}]}
- M12 / 991 / region_health / source_unit: {"details": [{"name": "Reference mean", "value": "61"}, {"name": "Current mean", "value": "61"}, {"name": "Reference SD", "value": "0.0e+00"}, {"name": "Current SD", "value": "0.05"}]}
- R01 / 445 / 940.445/GetCart / µs: {"after": 4348.6, "before": 4182.1, "details": [{"name": "Reference requests", "value": "1303"}, {"name": "Current requests", "value": "1840"}, {"name": "Current inclusive p95 (µs)", "value": "7361.8"}, {"name": "Request log2 ratio", "value": "0.5"}, {"name": "Latency log2 ratio", "value": "0.06"}]}
- R02 / 102 / /940.102/SendOrderConfirmation / µs: {"after": 1176.5, "before": 986.4, "details": [{"name": "Reference requests", "value": "64"}, {"name": "Current requests", "value": "88"}, {"name": "Current inclusive p95 (µs)", "value": "1176.5"}, {"name": "Request log2 ratio", "value": "0.45"}, {"name": "Latency log2 ratio", "value": "0.25"}]}
- R03 / 961 / 961 / µs: {"after": 2275.0, "before": 2109.25, "details": [{"name": "Reference requests", "value": "186"}, {"name": "Current requests", "value": "261"}, {"name": "Current inclusive p95 (µs)", "value": "2275.0"}, {"name": "Request log2 ratio", "value": "0.49"}, {"name": "Latency log2 ratio", "value": "0.11"}]}
- R04 / 445 / POST /940.445/AddItem / µs: {"after": 1656.6, "before": 1589.6, "details": [{"name": "Reference requests", "value": "122"}, {"name": "Current requests", "value": "173"}, {"name": "Current inclusive p95 (µs)", "value": "5443.6"}, {"name": "Request log2 ratio", "value": "0.5"}, {"name": "Latency log2 ratio", "value": "0.06"}]}
- R05 / 588 / 940.588/PlaceOrder / µs: {"after": 72664.25, "before": 66041.3, "details": [{"name": "Reference requests", "value": "128"}, {"name": "Current requests", "value": "176"}, {"name": "Current inclusive p95 (µs)", "value": "223835.75"}, {"name": "Request log2 ratio", "value": "0.46"}, {"name": "Latency log2 ratio", "value": "0.14"}]}
- R06 / 128 / /940.128/ListProducts / µs: {"after": 3456.75, "before": 3282.1, "details": [{"name": "Reference requests", "value": "1104"}, {"name": "Current requests", "value": "1576"}, {"name": "Current inclusive p95 (µs)", "value": "3532.75"}, {"name": "Request log2 ratio", "value": "0.51"}, {"name": "Latency log2 ratio", "value": "0.07"}]}

## RQ3.8 · INC-5DDDA62386B6 · unchanged

aegislab / eval / service / HTTPRequestReplaceMethod。MRR 1.0000 → 1.0000。

评测标签（仅分析）：{"ts-assurance-service": "847", "ts-ui-dashboard": "310"}

TEXT：["847", "271", "310"]

Service 847 is the root cause, evidenced by a massive memory spike (signed_z -69.83) and a burst of new 'HttpRequestMethodNotSupportedException' logs that coincide with the earliest observed anomaly onset at +5.0m. Service 847 is a callee of 271 and 310, placing it upstream of the latency symptoms observed in 310 (rank_score 7.41) and other downstream services, which confirms 847 as the origin of the fault.

FULL：["847", "573", "310"]

Top-1 847 is verified by the co-located diagnostic log LT10 ("Request method 'DELETE' not supported") that emerged from pod 93921 (its instance) at the +5m onset with 0→160 errors, matching its high MET-Z (signed z 63.84–72.77 class) and TRC-L DELETE/error count surge (9→160); this confirms a local application-level fault rather than downstream noise. An alternative origin was checked against 573 (z 72.77), but 573's p99 latency spike has no error-log support and it sits downstream of the 310→573 caller edge, so it is classified as a symptom, not an origin. Topologically, 310 calls 847 (310→847) and precedes 847's +5.2m onset, consistent with 847 as the true fault origin, while 310's elevated exclusive latency (GET foodservice, POST travelPlan/cheapest, DELETE assurances/types) reflects it absorbing the failure.

[旧输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s2/outputs/17f354bdb3b3bb4567fc59f68c531909b1033848966427d2d6ca8c8048e0b5d5.json) · [新输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s2/outputs/1e945f4d2461a4b536f9328d0abdc30966b4d2d6d7bbb77638fea2eff9dc7eab.json) · [新输入](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s2/inputs/1e945f4d2461a4b536f9328d0abdc30966b4d2d6d7bbb77638fea2eff9dc7eab.json)

[模型所见图](../through_RQ3_15_preserved/assets/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s2/renders/1e945f4d2461a4b536f9328d0abdc30966b4d2d6d7bbb77638fea2eff9dc7eab_0.png)

- M01 / 847 / container.memory.available / source_unit: {"details": [{"name": "Reference mean", "value": "2.4G"}, {"name": "Current mean", "value": "2.4G"}, {"name": "Reference SD", "value": "461.3k"}, {"name": "Current SD", "value": "15.7M"}, {"name": "Deviation (sigma)", "value": "39"}]}
- M02 / 847 / k8s.pod.memory.node.utilization / ratio_or_percent: {"details": [{"name": "Reference mean", "value": "5.8e-03"}, {"name": "Current mean", "value": "5.9e-03"}, {"name": "Reference SD", "value": "3.3e-06"}, {"name": "Current SD", "value": "1.2e-04"}, {"name": "Deviation (sigma)", "value": "41"}]}
- M03 / 847 / k8s.pod.memory.working_set / source_unit: {"details": [{"name": "Reference mean", "value": "782.0M"}, {"name": "Current mean", "value": "800.1M"}, {"name": "Reference SD", "value": "440.4k"}, {"name": "Current SD", "value": "15.6M"}, {"name": "Deviation (sigma)", "value": "41"}]}
- M04 / 847 / k8s.pod.memory_limit_utilization / ratio_or_percent: {"details": [{"name": "Reference mean", "value": "0.24"}, {"name": "Current mean", "value": "0.25"}, {"name": "Reference SD", "value": "1.4e-04"}, {"name": "Current SD", "value": "4.8e-03"}, {"name": "Deviation (sigma)", "value": "41"}]}
- M05 / 847 / container.memory.working_set / source_unit: {"details": [{"name": "Reference mean", "value": "781.8M"}, {"name": "Current mean", "value": "799.7M"}, {"name": "Reference SD", "value": "461.3k"}, {"name": "Current SD", "value": "15.7M"}, {"name": "Deviation (sigma)", "value": "39"}]}
- M06 / 847 / container.memory.rss / source_unit: {"details": [{"name": "Reference mean", "value": "770.7M"}, {"name": "Current mean", "value": "788.8M"}, {"name": "Reference SD", "value": "411.3k"}, {"name": "Current SD", "value": "15.7M"}, {"name": "Deviation (sigma)", "value": "44"}]}
- M07 / 239 / k8s.pod.memory.rss / source_unit: {"details": [{"name": "Reference mean", "value": "152.2M"}, {"name": "Current mean", "value": "152.2M"}, {"name": "Reference SD", "value": "410"}, {"name": "Current SD", "value": "12.3k"}, {"name": "Deviation (sigma)", "value": "23"}]}
- M08 / 847 / k8s.pod.memory.usage / source_unit: {"details": [{"name": "Reference mean", "value": "782.4M"}, {"name": "Current mean", "value": "800.4M"}, {"name": "Reference SD", "value": "440.4k"}, {"name": "Current SD", "value": "15.6M"}, {"name": "Deviation (sigma)", "value": "41"}]}
- M09 / 847 / container.memory.usage / source_unit: {"details": [{"name": "Reference mean", "value": "782.2M"}, {"name": "Current mean", "value": "800.1M"}, {"name": "Reference SD", "value": "461.3k"}, {"name": "Current SD", "value": "15.7M"}, {"name": "Deviation (sigma)", "value": "39"}]}
- M10 / 847 / k8s.pod.memory.rss / source_unit: {"details": [{"name": "Reference mean", "value": "770.6M"}, {"name": "Current mean", "value": "788.6M"}, {"name": "Reference SD", "value": "409.1k"}, {"name": "Current SD", "value": "15.6M"}, {"name": "Deviation (sigma)", "value": "44"}]}
- M11 / 573 / hubble_http_request_duration_p99_seconds / milliseconds_or_source_unit: {"details": [{"name": "Reference mean", "value": "0.01"}, {"name": "Current mean", "value": "0.06"}, {"name": "Reference SD", "value": "2.4e-03"}, {"name": "Current SD", "value": "0.13"}, {"name": "Deviation (sigma)", "value": "19"}]}
- M12 / 847 / k8s.pod.memory.available / source_unit: {"details": [{"name": "Reference mean", "value": "2.4G"}, {"name": "Current mean", "value": "2.4G"}, {"name": "Reference SD", "value": "440.4k"}, {"name": "Current SD", "value": "15.6M"}, {"name": "Deviation (sigma)", "value": "41"}]}
- R01 / 847 / DELETE /error / µs: {"after": 4190.89, "before": 3482.95, "details": [{"name": "Reference requests", "value": "9"}, {"name": "Current requests", "value": "160"}, {"name": "Current inclusive p95 (µs)", "value": "5475.09"}, {"name": "Request log2 ratio", "value": "4.01"}, {"name": "Latency log2 ratio", "value": "0.27"}]}
- R02 / 310 / GET /api/v1/foodservice/foods/2025-08-05/suzhou/shanghai/G1236 / µs: {"after": 104363.23, "before": 2458.89, "details": [{"name": "Reference requests", "value": "4"}, {"name": "Current requests", "value": "19"}, {"name": "Current inclusive p95 (µs)", "value": "152694.44"}, {"name": "Request log2 ratio", "value": "2.0"}, {"name": "Latency log2 ratio", "value": "5.41"}]}
- R03 / 310 / DELETE /api/v1/assuranceservice/assurances/types / µs: {"after": 3855.66, "before": 3363.05, "details": [{"name": "Reference requests", "value": "9"}, {"name": "Current requests", "value": "161"}, {"name": "Current inclusive p95 (µs)", "value": "8437.61"}, {"name": "Request log2 ratio", "value": "4.02"}, {"name": "Latency log2 ratio", "value": "0.2"}]}
- R04 / 847 / OnCommittedResponseWrapper.sendError / µs: {"after": 86.85, "before": 74.93, "details": [{"name": "Reference requests", "value": "9"}, {"name": "Current requests", "value": "160"}, {"name": "Current inclusive p95 (µs)", "value": "86.85"}, {"name": "Request log2 ratio", "value": "4.01"}, {"name": "Latency log2 ratio", "value": "0.21"}]}
- R05 / 310 / POST /api/v1/travelplanservice/travelPlan/cheapest / µs: {"after": 17750.9, "before": 3761.7, "details": [{"name": "Reference requests", "value": "24"}, {"name": "Current requests", "value": "102"}, {"name": "Current inclusive p95 (µs)", "value": "2526062.55"}, {"name": "Request log2 ratio", "value": "2.04"}, {"name": "Latency log2 ratio", "value": "2.24"}]}
- R06 / 511 / OrderRepository.findById / µs: {"after": 121222.5, "before": 2259.99, "details": [{"name": "Reference requests", "value": "63"}, {"name": "Current requests", "value": "18"}, {"name": "Current inclusive p95 (µs)", "value": "126137.38"}, {"name": "Request log2 ratio", "value": "-1.75"}, {"name": "Latency log2 ratio", "value": "5.74"}]}

## RQ3.8 · INC-B63F1516296F · unchanged

aiops2022 / eval / service / k8s容器进程中止。MRR 0.0000 → 0.0000。

评测标签（仅分析）：{"recommendationservice": "506"}

TEXT：["4390", "336", "167"]

Service 4390 is the only candidate with a direct MET-Z anomaly (tcp_retrans_segs spike to 22.02, z=604.5) at the fault onset (+22m), indicating a network transmission failure. The topology confirms 4390 is a lower-tier service called by upstream pods (e.g., 27391, 80525) with no outgoing calls in the observed graph, making it a plausible origin for the downstream latency increases seen in 336 and 167.

FULL：["4390", "167", "273"]

MET-Z shows node 4390's TCP retransmissions spiking 604.5σ to a peak of 22.02 from a near-zero baseline. This node-level network degradation is temporally and causally upstream of the p95 latency explosions at pod 11553 (host 9861) for the callee service 449, proving node-level network interference as the root origin.

[旧输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s0/outputs/fa75341822ee7b529bce6bb1d7886d567f3d729958d2665afc02554fc12464fd.json) · [新输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s0/outputs/3858bf15281cdc2467daabe407500cf2c41606d9617f914813d79c660f9b96d0.json) · [新输入](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s0/inputs/3858bf15281cdc2467daabe407500cf2c41606d9617f914813d79c660f9b96d0.json)

[模型所见图](../through_RQ3_15_preserved/assets/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s0/renders/3858bf15281cdc2467daabe407500cf2c41606d9617f914813d79c660f9b96d0_0.png)

- M01 / 61093 / container_cpu_usage_seconds / source_unit: {"details": [{"name": "Reference mean", "value": "0.12"}, {"name": "Current mean", "value": "0.24"}, {"name": "Reference SD", "value": "0.13"}, {"name": "Current SD", "value": "0.54"}, {"name": "Deviation (sigma)", "value": "0.93"}]}
- M02 / 63102 / container_network_receive_MB.eth0 / source_unit: {"details": [{"name": "Reference mean", "value": "0.07"}, {"name": "Current mean", "value": "0.04"}, {"name": "Reference SD", "value": "0.11"}, {"name": "Current SD", "value": "3.5e-03"}, {"name": "Deviation (sigma)", "value": "0.21"}]}
- M03 / 73995 / container_fs_usage_MB./dev/vda1 / source_unit: {"details": [{"name": "Reference mean", "value": "47"}, {"name": "Current mean", "value": "44"}, {"name": "Reference SD", "value": "0.29"}, {"name": "Current SD", "value": "12"}, {"name": "Deviation (sigma)", "value": "8.97"}]}
- M04 / 4390 / system.net.tcp.retrans_segs / source_unit: {"details": [{"name": "Reference mean", "value": "0.02"}, {"name": "Current mean", "value": "1.59"}, {"name": "Reference SD", "value": "0.03"}, {"name": "Current SD", "value": "5.67"}, {"name": "Deviation (sigma)", "value": "48"}]}
- M05 / 162 / jvm_threads_started / source_unit: {"details": [{"name": "Reference mean", "value": "0.0e+00"}, {"name": "Current mean", "value": "0.07"}, {"name": "Reference SD", "value": "0.0e+00"}, {"name": "Current SD", "value": "0.22"}]}
- M06 / 18633 / container_cpu_cfs_throttled_seconds / source_unit: {"details": [{"name": "Reference mean", "value": "0.15"}, {"name": "Current mean", "value": "0.49"}, {"name": "Reference SD", "value": "0.51"}, {"name": "Current SD", "value": "1.77"}, {"name": "Deviation (sigma)", "value": "0.67"}]}
- M07 / 71334 / container_network_receive_MB.eth0 / source_unit: {"details": [{"name": "Reference mean", "value": "0.02"}, {"name": "Current mean", "value": "0.06"}, {"name": "Reference SD", "value": "1.9e-03"}, {"name": "Current SD", "value": "0.15"}, {"name": "Deviation (sigma)", "value": "21"}]}
- M08 / 84252 / container_network_receive_MB.eth0 / source_unit: {"details": [{"name": "Reference mean", "value": "0.02"}, {"name": "Current mean", "value": "0.07"}, {"name": "Reference SD", "value": "1.8e-03"}, {"name": "Current SD", "value": "0.12"}, {"name": "Deviation (sigma)", "value": "27"}]}
- M09 / 42913 / container_network_receive_MB.eth0 / source_unit: {"details": [{"name": "Reference mean", "value": "0.05"}, {"name": "Current mean", "value": "0.03"}, {"name": "Reference SD", "value": "0.11"}, {"name": "Current SD", "value": "4.4e-03"}, {"name": "Deviation (sigma)", "value": "0.19"}]}
- M10 / 18633 / container_cpu_cfs_throttled_periods / source_unit: {"details": [{"name": "Reference mean", "value": "1.10"}, {"name": "Current mean", "value": "2.61"}, {"name": "Reference SD", "value": "3.73"}, {"name": "Current SD", "value": "9.40"}, {"name": "Deviation (sigma)", "value": "0.41"}]}
- M11 / 36629 / container_network_receive_MB.eth0 / source_unit: {"details": [{"name": "Reference mean", "value": "0.05"}, {"name": "Current mean", "value": "0.02"}, {"name": "Reference SD", "value": "0.11"}, {"name": "Current SD", "value": "1.6e-03"}, {"name": "Deviation (sigma)", "value": "0.20"}]}
- M12 / 61093 / container_cpu_user_seconds / source_unit: {"details": [{"name": "Reference mean", "value": "0.09"}, {"name": "Current mean", "value": "0.21"}, {"name": "Reference SD", "value": "0.11"}, {"name": "Current SD", "value": "0.50"}, {"name": "Deviation (sigma)", "value": "1.07"}]}
- R01 / 94249 / hipstershop.167/GetQuote / µs: {"after": 11690.1, "before": 3272.0, "details": [{"name": "Reference requests", "value": "31"}, {"name": "Current requests", "value": "18"}, {"name": "Current inclusive p95 (µs)", "value": "11764.3"}, {"name": "Request log2 ratio", "value": "-0.75"}, {"name": "Latency log2 ratio", "value": "1.84"}]}
- R02 / 15155 / hipstershop.449/SendOrderConfirmation / µs: {"after": 33152.0, "before": 4169.3, "details": [{"name": "Reference requests", "value": "39"}, {"name": "Current requests", "value": "21"}, {"name": "Current inclusive p95 (µs)", "value": "33393.0"}, {"name": "Request log2 ratio", "value": "-0.86"}, {"name": "Latency log2 ratio", "value": "2.99"}]}
- R03 / 80525 / hipstershop.954/GetProduct / µs: {"after": 3864.45, "before": 3489.9, "details": [{"name": "Reference requests", "value": "58"}, {"name": "Current requests", "value": "30"}, {"name": "Current inclusive p95 (µs)", "value": "9270.05"}, {"name": "Request log2 ratio", "value": "-0.93"}, {"name": "Latency log2 ratio", "value": "0.15"}]}
- R04 / 68549 / hipstershop.167/ShipOrder / µs: {"after": 108.0, "before": 77.2, "details": [{"name": "Reference requests", "value": "33"}, {"name": "Current requests", "value": "19"}, {"name": "Current inclusive p95 (µs)", "value": "108.0"}, {"name": "Request log2 ratio", "value": "-0.77"}, {"name": "Latency log2 ratio", "value": "0.48"}]}
- R05 / 80525 / hipstershop.336/PlaceOrder / µs: {"after": 23849.75, "before": 11516.9, "details": [{"name": "Reference requests", "value": "32"}, {"name": "Current requests", "value": "16"}, {"name": "Current inclusive p95 (µs)", "value": "98673.0"}, {"name": "Request log2 ratio", "value": "-0.96"}, {"name": "Latency log2 ratio", "value": "1.05"}]}
- R06 / 27391 / hipstershop.476/Charge / µs: {"after": 3973.0, "before": 3253.0, "details": [{"name": "Reference requests", "value": "33"}, {"name": "Current requests", "value": "16"}, {"name": "Current inclusive p95 (µs)", "value": "4132.0"}, {"name": "Request log2 ratio", "value": "-1.0"}, {"name": "Latency log2 ratio", "value": "0.29"}]}

## RQ3.8 · INC-6FDD214ABC63 · unchanged

aiops2025 / eval / service / jvm gc。MRR 0.0000 → 0.0000。

评测标签（仅分析）：{"adservice": "764"}

TEXT：["8130", "438", "1438", "269", "93651"]

Node 8130 is the verified root cause, as its memory usage deviation (13.97 sigma) is the earliest anomaly at +19m, preceding all downstream service onsets. Topology confirms 8130 hosts the affected pods (including 88409), and the temporal sequence validates resource exhaustion on the node as the origin before trace/log symptoms in services like 438 and 1438.

FULL：["438", "8130", "269"]

MET-Z records service 438 (raft_apply_wait) as the earliest and largest onset at +20.0m with severity 999, and no candidate that 438 calls or that calls 438 shows an earlier onset, so it cannot be a downstream symptom of the other candidates. No service that hosts a pod on node 8130 (the earlier +19.0m infrastructure onset) or is related to node 269 exhibits a corresponding signature, leaving 438 as the origin.

[旧输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s0/outputs/a702f9d53827bef223e86230f0b29a56c24efd0f5f5f9b9650dc4ac0ed19d1a6.json) · [新输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s0/outputs/9b851014048bb9bf347f3eed39958e414527ee52e2d89a5720092938ca772134.json) · [新输入](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s0/inputs/9b851014048bb9bf347f3eed39958e414527ee52e2d89a5720092938ca772134.json)

[模型所见图](../through_RQ3_15_preserved/assets/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s0/renders/9b851014048bb9bf347f3eed39958e414527ee52e2d89a5720092938ca772134_0.png)

- M01 / 468 / rrt / source_unit: {"details": [{"name": "Reference mean", "value": "1.6k"}, {"name": "Current mean", "value": "1.8k"}, {"name": "Reference SD", "value": "95"}, {"name": "Current SD", "value": "852"}, {"name": "Deviation (sigma)", "value": "2.10"}]}
- M02 / 68577 / rrt_max / source_unit: {"details": [{"name": "Reference mean", "value": "3.9k"}, {"name": "Current mean", "value": "9.5k"}, {"name": "Reference SD", "value": "1.3k"}, {"name": "Current SD", "value": "19.4k"}, {"name": "Deviation (sigma)", "value": "4.38"}]}
- M03 / 468 / rrt_max / source_unit: {"details": [{"name": "Reference mean", "value": "3.6k"}, {"name": "Current mean", "value": "7.1k"}, {"name": "Reference SD", "value": "1.0k"}, {"name": "Current SD", "value": "13.4k"}, {"name": "Deviation (sigma)", "value": "3.48"}]}
- M04 / 3670 / node_disk_read_bytes_total / source_unit: {"details": [{"name": "Reference mean", "value": "0.0e+00"}, {"name": "Current mean", "value": "78"}, {"name": "Reference SD", "value": "0.0e+00"}, {"name": "Current SD", "value": "281"}]}
- M05 / 53337 / rrt_max / source_unit: {"details": [{"name": "Reference mean", "value": "4.7k"}, {"name": "Current mean", "value": "14.1k"}, {"name": "Reference SD", "value": "2.0k"}, {"name": "Current SD", "value": "19.9k"}, {"name": "Deviation (sigma)", "value": "4.66"}]}
- M06 / 93651 / rrt / source_unit: {"details": [{"name": "Reference mean", "value": "1.5k"}, {"name": "Current mean", "value": "2.1k"}, {"name": "Reference SD", "value": "156"}, {"name": "Current SD", "value": "2.3k"}, {"name": "Deviation (sigma)", "value": "3.70"}]}
- M07 / 93651 / pod_memory_working_set_bytes / source_unit: {"details": [{"name": "Reference mean", "value": "1.5k"}, {"name": "Current mean", "value": "33.0k"}, {"name": "Reference SD", "value": "409"}, {"name": "Current SD", "value": "114.6k"}, {"name": "Deviation (sigma)", "value": "77"}]}
- M08 / 57449 / pod_processes / source_unit: {"details": [{"name": "Reference mean", "value": "1.00"}, {"name": "Current mean", "value": "1.14"}, {"name": "Reference SD", "value": "0.0e+00"}, {"name": "Current SD", "value": "0.35"}]}
- M09 / 93651 / pod_cpu_usage / source_unit: {"details": [{"name": "Reference mean", "value": "0.0e+00"}, {"name": "Current mean", "value": "7.1e-04"}, {"name": "Reference SD", "value": "0.0e+00"}, {"name": "Current SD", "value": "2.6e-03"}]}
- M10 / 438 / raft_apply_wait / source_unit: {"details": [{"name": "Reference mean", "value": "0.0e+00"}, {"name": "Current mean", "value": "1.4e-03"}, {"name": "Reference SD", "value": "0.0e+00"}, {"name": "Current SD", "value": "3.5e-03"}]}
- M11 / 93651 / rrt_max / source_unit: {"details": [{"name": "Reference mean", "value": "2.4k"}, {"name": "Current mean", "value": "5.9k"}, {"name": "Reference SD", "value": "841"}, {"name": "Current SD", "value": "13.8k"}, {"name": "Deviation (sigma)", "value": "4.18"}]}
- M12 / 269 / node_disk_write_time_seconds_total / source_unit: {"details": [{"name": "Reference mean", "value": "0.02"}, {"name": "Current mean", "value": "0.13"}, {"name": "Reference SD", "value": "0.02"}, {"name": "Current SD", "value": "0.16"}, {"name": "Deviation (sigma)", "value": "7.12"}]}
- R01 / 468 / 715.468/Charge / µs: {"after": 74035.0, "before": 70288.4, "details": [{"name": "Reference requests", "value": "392"}, {"name": "Current requests", "value": "247"}, {"name": "Current inclusive p95 (µs)", "value": "74035.0"}, {"name": "Request log2 ratio", "value": "-0.66"}, {"name": "Latency log2 ratio", "value": "0.07"}]}
- R02 / 445 / 715.445/ShipOrder / µs: {"after": 67515.0, "before": 65035.35, "details": [{"name": "Reference requests", "value": "784"}, {"name": "Current requests", "value": "494"}, {"name": "Current inclusive p95 (µs)", "value": "67703.85"}, {"name": "Request log2 ratio", "value": "-0.67"}, {"name": "Latency log2 ratio", "value": "0.05"}]}
- R03 / 879 / /715.879/ListProducts / µs: {"after": 4077.0, "before": 4004.95, "details": [{"name": "Reference requests", "value": "7002"}, {"name": "Current requests", "value": "4476"}, {"name": "Current inclusive p95 (µs)", "value": "4178.25"}, {"name": "Request log2 ratio", "value": "-0.65"}, {"name": "Latency log2 ratio", "value": "0.03"}]}
- R04 / 488 / 715.488/Recv. / µs: {"after": 3835.0, "before": 3744.8, "details": [{"name": "Reference requests", "value": "9769"}, {"name": "Current requests", "value": "6201"}, {"name": "Current inclusive p95 (µs)", "value": "130821.0"}, {"name": "Request log2 ratio", "value": "-0.66"}, {"name": "Latency log2 ratio", "value": "0.03"}]}
- R05 / 924 / 715.924/EmptyCart / µs: {"after": 79496.5, "before": 76293.05, "details": [{"name": "Reference requests", "value": "392"}, {"name": "Current requests", "value": "247"}, {"name": "Current inclusive p95 (µs)", "value": "81043.6"}, {"name": "Request log2 ratio", "value": "-0.66"}, {"name": "Latency log2 ratio", "value": "0.06"}]}
- R06 / 960 / 715.960/SendOrderConfirmation / µs: {"after": 84009.9, "before": 83096.75, "details": [{"name": "Reference requests", "value": "392"}, {"name": "Current requests", "value": "247"}, {"name": "Current inclusive p95 (µs)", "value": "84746.6"}, {"name": "Request log2 ratio", "value": "-0.66"}, {"name": "Latency log2 ratio", "value": "0.02"}]}

## RQ3.8 · INC-3BD85268FC32 · unchanged

aegislab / test / service / NetworkPartition。MRR 0.0000 → 0.0000。

评测标签（仅分析）：{"ts-food-service": "508", "ts-train-food-service": "798"}

TEXT：["684", "541", "243"]

Service 684 (database) is the top candidate as it has the earliest telemetry onset (+4.2m) and highest severity rank (1), preceding the +4.5m onset of the other anomalous cluster (including 541, a queue) and the +6.2m onset of the downstream service cluster (243, 440). While 541 and 243 show severe filesystem exhaustion (identical Z-scores), the temporal precedence of 684 and its role as a database dependency makes it the most plausible origin for the latency and volume drops observed in the call graph.

FULL：["440", "243", "117"]

Top-1 440 is verified: (1) its TRC-L exclusive-latency p95 exploded to ~20s (rank_score 13.25–14.28) with its callers 508/795 simultaneously degenerating at +6.2m, indicating a caller-side local stall rather than a child-span effect; (2) the fault-window metrics (5.8m–7.8m) show 440's exclusive latency onset precedes the widespread container/filesystem available-space collapse seen in 243/552/899/954 (and co-hosted 382/541) at +6.2m, making 440 the origin of the cascade rather than a downstream victim.

[旧输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s1/outputs/59cc6d512742e9dc34b37769e223a2213d21ce405d4d55d0d0549571d6fcead2.json) · [新输出](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s1/outputs/0dc01c2dee0466434f1151934bf9b10aaa6592462e687f3bd430d835ad1dde02.json) · [新输入](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s1/inputs/0dc01c2dee0466434f1151934bf9b10aaa6592462e687f3bd430d835ad1dde02.json)

[模型所见图](../through_RQ3_15_preserved/assets/RQs/RQ3_8/results/ops_components_v7/qwen3.8-27b_s1/renders/0dc01c2dee0466434f1151934bf9b10aaa6592462e687f3bd430d835ad1dde02_0.png)

- M01 / 243 / container.filesystem.available / source_unit: {"details": [{"name": "Reference mean", "value": "35.0G"}, {"name": "Current mean", "value": "25.7G"}, {"name": "Reference SD", "value": "88.0M"}, {"name": "Current SD", "value": "6.5G"}, {"name": "Deviation (sigma)", "value": "106"}]}
- M02 / 954 / k8s.pod.filesystem.available / source_unit: {"details": [{"name": "Reference mean", "value": "35.0G"}, {"name": "Current mean", "value": "25.7G"}, {"name": "Reference SD", "value": "88.0M"}, {"name": "Current SD", "value": "6.5G"}, {"name": "Deviation (sigma)", "value": "106"}]}
- M03 / 552 / container.filesystem.available / source_unit: {"details": [{"name": "Reference mean", "value": "35.0G"}, {"name": "Current mean", "value": "25.7G"}, {"name": "Reference SD", "value": "88.0M"}, {"name": "Current SD", "value": "6.5G"}, {"name": "Deviation (sigma)", "value": "106"}]}
- M04 / 899 / k8s.pod.filesystem.available / source_unit: {"details": [{"name": "Reference mean", "value": "35.0G"}, {"name": "Current mean", "value": "25.7G"}, {"name": "Reference SD", "value": "88.0M"}, {"name": "Current SD", "value": "6.5G"}, {"name": "Deviation (sigma)", "value": "106"}]}
- M05 / 954 / container.filesystem.available / source_unit: {"details": [{"name": "Reference mean", "value": "35.0G"}, {"name": "Current mean", "value": "25.7G"}, {"name": "Reference SD", "value": "88.0M"}, {"name": "Current SD", "value": "6.5G"}, {"name": "Deviation (sigma)", "value": "106"}]}
- M06 / 846 / container.filesystem.available / source_unit: {"details": [{"name": "Reference mean", "value": "35.0G"}, {"name": "Current mean", "value": "25.7G"}, {"name": "Reference SD", "value": "88.0M"}, {"name": "Current SD", "value": "6.5G"}, {"name": "Deviation (sigma)", "value": "106"}]}
- M07 / 675 / container.filesystem.available / source_unit: {"details": [{"name": "Reference mean", "value": "35.0G"}, {"name": "Current mean", "value": "25.7G"}, {"name": "Reference SD", "value": "88.0M"}, {"name": "Current SD", "value": "6.5G"}, {"name": "Deviation (sigma)", "value": "106"}]}
- M08 / 899 / container.filesystem.available / source_unit: {"details": [{"name": "Reference mean", "value": "35.0G"}, {"name": "Current mean", "value": "25.7G"}, {"name": "Reference SD", "value": "88.0M"}, {"name": "Current SD", "value": "6.5G"}, {"name": "Deviation (sigma)", "value": "106"}]}
- M09 / 675 / k8s.pod.filesystem.available / source_unit: {"details": [{"name": "Reference mean", "value": "35.0G"}, {"name": "Current mean", "value": "25.7G"}, {"name": "Reference SD", "value": "88.0M"}, {"name": "Current SD", "value": "6.5G"}, {"name": "Deviation (sigma)", "value": "106"}]}
- M10 / 846 / k8s.pod.filesystem.available / source_unit: {"details": [{"name": "Reference mean", "value": "35.0G"}, {"name": "Current mean", "value": "25.7G"}, {"name": "Reference SD", "value": "88.0M"}, {"name": "Current SD", "value": "6.5G"}, {"name": "Deviation (sigma)", "value": "106"}]}
- M11 / 552 / k8s.pod.filesystem.available / source_unit: {"details": [{"name": "Reference mean", "value": "35.0G"}, {"name": "Current mean", "value": "25.7G"}, {"name": "Reference SD", "value": "88.0M"}, {"name": "Current SD", "value": "6.5G"}, {"name": "Deviation (sigma)", "value": "106"}]}
- M12 / 243 / k8s.pod.filesystem.available / source_unit: {"details": [{"name": "Reference mean", "value": "35.0G"}, {"name": "Current mean", "value": "25.7G"}, {"name": "Reference SD", "value": "88.0M"}, {"name": "Current SD", "value": "6.5G"}, {"name": "Deviation (sigma)", "value": "106"}]}
- R01 / 508 / GET / µs: {"after": 130866535.78, "before": 2974.9, "details": [{"name": "Reference requests", "value": "166"}, {"name": "Current requests", "value": "5"}, {"name": "Current inclusive p95 (µs)", "value": "130866535.78"}, {"name": "Request log2 ratio", "value": "-4.8"}, {"name": "Latency log2 ratio", "value": "15.42"}]}
- R02 / 795 / GET / µs: {"after": 1646602.52, "before": 3323.7, "details": [{"name": "Reference requests", "value": "181"}, {"name": "Current requests", "value": "9"}, {"name": "Current inclusive p95 (µs)", "value": "1666530.59"}, {"name": "Request log2 ratio", "value": "-4.19"}, {"name": "Latency log2 ratio", "value": "8.95"}]}
- R03 / 170 / RoutePlanController.getQuickestRoutes / µs: {"after": 287716.74, "before": 59188.98, "details": [{"name": "Reference requests", "value": "20"}, {"name": "Current requests", "value": "3"}, {"name": "Current inclusive p95 (µs)", "value": "597930.68"}, {"name": "Request log2 ratio", "value": "-2.39"}, {"name": "Latency log2 ratio", "value": "2.28"}]}
- R04 / 440 / GET /api/v1/foodservice/foods/2025-07-21/taiyuan/shanghai/Z1236 / µs: {"after": 20003943.37, "before": 2047.32, "details": [{"name": "Reference requests", "value": "11"}, {"name": "Current requests", "value": "2"}, {"name": "Current inclusive p95 (µs)", "value": "20003943.37"}, {"name": "Request log2 ratio", "value": "-2.0"}, {"name": "Latency log2 ratio", "value": "13.25"}]}
- R05 / 440 / GET /api/v1/foodservice/foods/2025-07-21/nanjing/shanghai/Z1236 / µs: {"after": 20001242.26, "before": 1003.97, "details": [{"name": "Reference requests", "value": "17"}, {"name": "Current requests", "value": "1"}, {"name": "Current inclusive p95 (µs)", "value": "20001242.26"}, {"name": "Request log2 ratio", "value": "-3.17"}, {"name": "Latency log2 ratio", "value": "14.28"}]}
- R06 / 570 / GET /api/v1/trainservice/trains/byName/{name} / µs: {"after": 1682348.82, "before": 2674.63, "details": [{"name": "Reference requests", "value": "318"}, {"name": "Current requests", "value": "9"}, {"name": "Current inclusive p95 (µs)", "value": "1700977.42"}, {"name": "Request log2 ratio", "value": "-5.0"}, {"name": "Latency log2 ratio", "value": "9.3"}]}
