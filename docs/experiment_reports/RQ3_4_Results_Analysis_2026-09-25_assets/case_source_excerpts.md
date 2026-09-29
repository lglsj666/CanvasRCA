# Named case source excerpts

Purposive illustrations; no prevalence claim.

## INC-27F3CF9F35C3

Private evaluation label: `{'ts-auth-service': '419'}`

### Qwen / TPV

MRR=0.0000. [Conversation](../../../RQs/RQ3_4/results/integrated_v1/stages/exp_integrated_locked_check/qwen3.8-27b/conversations/e0282e07966b6b56f021c7e3168e69029e0f4dc6967b0664a0f8fbc183160f2a.md)

```json
{"services": ["84519", "713", "750"], "reason": "The metrics show a abrupt drop in pod 419's memory usage and filesystem metrics to near zero around t=3m, consistent with a pod crash, and pod 77815 shows a restart, identifying an infrastructure-level fault. The log evidence attributes the new burst of 'Aborted connection' errors to pod 84519, which is the strongest local, fault-window-locked evidence. The trace evidence for service 750 shows a massive increase in exclusive latency (score 4.38), indicating a downstream stall in the 'foodsearch' domain, and the topology confirms 713 calling 892 (the caller of 750), validating the propagation path.", "confidence": "high"}
```

### Qwen / P1H1K0_G

MRR=1.0000. [Conversation](../../../RQs/RQ3_4/results/integrated_v1/stages/exp_integrated_locked_check/qwen3.8-27b/conversations/a122c3139181fdb9851e3f4c9d4faf798e35d3a8c61be434c56bbf98711d2c8d.md)

```json
{"services": ["419", "77815", "133", "985"], "reason": "Pod 77815 records a hard k8s.container.restarts onset at 3.8m (M1) with zero baseline, and node 9129 hosts it without concurrent restarts, indicating a local pod failure rather than a co-located node event. Service 419 exhibits a synchronized memory-deletion/restart dip at the same 3.8m window (M2–M7) that is causally consistent with the pod restart, while trace scores for downstream callers 133 and 985 reflect propagated latency rather than local faults.", "confidence": "medium"}
```

### Qwen / P1H1K1_G

MRR=1.0000. [Conversation](../../../RQs/RQ3_4/results/integrated_v1/stages/exp_integrated_locked_check/qwen3.8-27b/conversations/9e7b23a8cce1df51999939df9bc2eac6b3342ab00a3fbd1031aebbe7a7845790.md)

```json
{"services": ["419", "77815", "133"], "reason": "Metrics show a fault-window drop in pod 419 memory usage and pod-level metrics to ~27% baseline that self-heals, consistent with a container restart that shed state. Pod 77815 on node 9129 logs its first k8s.container.restarts from 0 to 1 during the same fault window, marking the co-located restart origin, while node 9129 is a 4-digit infrastructure node not in the candidate list. Call-edge 988 -> 892 places 892 upstream of 419, so 419 is the most plausible root-cause service among the candidates.", "confidence": "low"}
```

### Qwen / P1H1K1_T

MRR=1.0000. [Conversation](../../../RQs/RQ3_4/results/integrated_v1/stages/exp_integrated_locked_check/qwen3.8-27b/conversations/e07a3157087e76a10e915221893e40d44082ba19210a6483c877efcc18bdff04.md)

```json
{"services": ["77815", "419", "133"], "reason": "Pod 77815 is the top candidate as the root cause because it exhibits a container restart (k8s.container.restarts increasing from 0 to 1) starting around bin 32 (+4.0m), which temporally precedes or coincides with the onset of symptoms in service 419 (memory drop at +4.9m) and service 133 (onset at +4.0m). Verification confirms that 77815's restart is the earliest distinct infrastructure anomaly in the provided M evidence relative to the application-level metric drops in 419, and no upstream service (e.g., 988, 892) shows a prior trace or metric failure that would causally drive the restart.", "confidence": "medium"}
```

### Gemma / TPV

MRR=1.0000. [Conversation](../../../RQs/RQ3_4/results/integrated_v1/stages/exp_integrated_locked_check/gemma-4-26b-a4b/conversations/295c0097af626d4c5178bc1c6024504fcf38001b74bcb876f73b3f16afdbba23.md)

```json
{"services": ["77815", "419", "84519"], "reason": "Pod 77815 shows the earliest onset of restarts at 3.8m, which precedes the memory fluctuations in service 419. The error logs in 84519 regarding aborted database connections suggest service 419's instability or the pod restarts are triggering downstream communication failures. Topology shows no direct causal path from 419 to the initial restart event in 77815.", "confidence": "high"}
```

### Gemma / P1H1K0_G

MRR=1.0000. [Conversation](../../../RQs/RQ3_4/results/integrated_v1/stages/exp_integrated_locked_check/gemma-4-26b-a4b/conversations/59396f7d94a428de66db999597fab26a923ee199e57d544fc8eae0c116ca707a.md)

```json
{"services": ["77815"], "reason": "Pod 77815 shows the earliest onset of error via continuous container restarts starting at 3.8m. While service 419 exhibits significant memory drops and service 750 shows high latency, the logs from entity 84519 confirm database connection aborts that align with the timing of the system-wide instability. The trace latency in 750 and 713 are downstream symptoms of the initial infrastructure failure in pod 77815.", "confidence": "high"}
```

### Gemma / P1H1K1_G

MRR=1.0000. [Conversation](../../../RQs/RQ3_4/results/integrated_v1/stages/exp_integrated_locked_check/gemma-4-26b-a4b/conversations/5cd3c201626e24650ad68e9f5cee100c98fa7d478793623a032d5ab5acb6107a.md)

```json
{"services": ["77815"], "reason": "Pod 77815 shows container restarts starting at 3.8m, which is the earliest onset in the system. While service 419 shows significant memory drops and service 750 shows high latency, these symptoms occur after or concurrently with the pod instability. The log evidence for entity 84519 (aborted DB connections) and the timing of restarts point to infrastructure-level instability in the pod hosting the fault. ", "confidence": "high"}
```

```text
Additional observations use the same public reference/current intervals, in seconds from observation start. Medians describe measured samples; inclusive span duration includes child spans. Request counts deduplicate trace IDs and describe captured requests, not unobserved traffic. Calls and hosting are observed relations, not proof of failure propagation.
Host and instance observations:
{"entity": "45263", "region": "M", "semantic": "k8s.container.restarts", "unit": "source_unit", "values": {"current_interval_s": [225.0, 480.0], "current_median": 0.0, "current_samples": 18, "reference_interval_s": [0, 225.0], "reference_mad": 0.0, "reference_median": 0.0, "reference_samples": 15}}
{"entity": "77815", "region": "M", "semantic": "k8s.container.restarts", "unit": "source_unit", "values": {"current_interval_s": [225.0, 480.0], "current_median": 1.0, "current_samples": 18, "reference_interval_s": [0, 225.0], "reference_mad": 0.0, "reference_median": 0.0, "reference_samples": 15}}
{"from": "9129", "relation": "hosts", "to": "77815"}
{"from": "9129", "relation": "hosts", "to": "45263"}
Host and instance observations:
{"entity": "45946", "region": "M", "semantic": "k8s.container.restarts", "unit": "source_unit", "values": {"current_interval_s": [225.0, 480.0], "current_median": 0.0, "current_samples": 18, "reference_interval_s": [0, 225.0], "reference_mad": 0.0, "reference_median": 0.0, "reference_samples": 15}}
{"entity": "77815", "region": "M", "semantic": "k8s.container.restarts", "unit": "source_unit", "values": {"current_interval_s": [225.0, 480.0], "current_median": 1.0, "current_samples": 18, "reference_interval_s": [0, 225.0], "reference_mad": 0.0, "reference_median": 0.0, "reference_samples": 15}}
{"from": "9129", "relation": "hosts", "to": "77815"}
{"from": "9129", "relation": "hosts", "to": "45946"}
Host and instance observations:
{"entity": "795", "region": "M", "semantic": "jvm.system.cpu.load_1m", "unit": "source_unit", "values": {"current_interval_s": [225.0, 480.0], "current_median": 2.82, "current_samples": 18, "reference_interval_s": [0, 225.0], "reference_mad": 0.03, "reference_median": 10.86, "reference_samples": 15}}
Availability and recorded activity:
{"entity": "988", "region": "R", "semantic": "TripRepository.findAll", "unit": "ms_and_counts", "values": {"current_inclusive_median_ms": 2.24654, "current_interval_s": [225.0, 480.0], "current_observed_requests": 273, "current_span_count": 273, "current_spans_with_request_id": 273, "reference_inclusive_median_ms": 2.772372, "reference_interval_s": [0, 225.0], "reference_observed_requests": 228, "reference_span_count": 228, "reference_spans_with_request_id": 228}}
{"entity": "988", "region": "M", "semantic": "jvm.cpu.recent_utilization", "unit": "source_unit", "values": {"current_interval_s": [225.0, 480.0], "current_median": 0.0011100959, "current_samples": 18, "reference_interval_s": [0, 225.0], "reference_mad": 5.0501416e-05, "reference_median": 0.0019846199, "reference_samples": 15}}
```

```text
Computed relations between displayed observations:
77815 k8s.container.restarts (source_unit): current_median is greater than reference_median.
77815 is a pod.
77815 k8s.container.restarts (source_unit): current_median is greater than reference_median.
795 jvm.system.cpu.load_1m (source_unit): current_median is less than reference_median.
795 is a service.
988 TripRepository.findAll (milliseconds): current_inclusive_median_ms is less than reference_inclusive_median_ms.
988 is a service.
988 jvm.cpu.recent_utilization (source_unit): current_median is less than reference_median.
Displayed G onset of 133 is earlier than 142; this is temporal order, not fault causation.
Displayed G onset of 161 is earlier than 142; this is temporal order, not fault causation.
Displayed G onset of 375 is earlier than 419; this is temporal order, not fault causation.
Displayed G onset of 620 is earlier than 419; this is temporal order, not fault causation.
Displayed G onset of 699 is earlier than 817; this is temporal order, not fault causation.
Displayed G onset of 892 is earlier than 817; this is temporal order, not fault causation.
```

### Gemma / P1H1K1_T

MRR=1.0000. [Conversation](../../../RQs/RQ3_4/results/integrated_v1/stages/exp_integrated_locked_check/gemma-4-26b-a4b/conversations/02a5e1974f9c3c6b030690908a742980db787aaf9aa8242f79220bf5c9758819.md)

```json
{"services": ["77815"], "reason": "Pod 77815 shows a definitive container restart anomaly (M1) starting at the onset of the incident window. While service 419 exhibits extreme memory metric shifts and service 892 shows high error propagation, they are downstream or co-located symptoms of the instability introduced by the pod restart. The metric and host evidence confirm 77815 is a pod under node 9129 experiencing a restart event.", "confidence": "high"}
```

## INC-9D1784608F61

Private evaluation label: `{'node-8': '1847'}`

### Qwen / TPV

MRR=0.0000. [Conversation](../../../RQs/RQ3_4/results/integrated_v1/stages/exp_integrated_locked_check/qwen3.8-27b/conversations/2beb36e30fc3a022b353de9fc3cb733333e0153a1ad4057734b5a64edd9680b0.md)

```json
{"services": ["365", "217", "610"], "reason": "Service 365 is the root origin, verified by its earliest anomaly onset at 15m predating all other entities and by its trace evidence showing a large exclusive-latency increase. This topology is supported by the directed edges where 217 calls 365, and by 610's subsequent late-onset filesystem metric degradation, which is consistent with 365 being the upstream trigger for the incident.", "confidence": "high"}
```

### Qwen / P1H1K0_G

MRR=1.0000. [Conversation](../../../RQs/RQ3_4/results/integrated_v1/stages/exp_integrated_locked_check/qwen3.8-27b/conversations/874effc197947489b8d160b4adb568c68c34a28eaa5768f79381ac93ba2ec4d7.md)

```json
{"services": ["1847", "66109", "29225"], "reason": "The top candidate is the node 1847, which exhibits an extreme node_filesystem_usage_rate shift from ~54% to ~81% (MET-Z deviation_sigma of 2.17σ) starting at bin 31 (relative time ~18m). The temporal ordering and topology evidence confirm this origin, as the fault window begins at +18.0m and node 1847 hosts the affected pods 66109 and 29225, which both show corresponding memory and response-time anomalies within the same interval.", "confidence": "high"}
```

### Qwen / P1H1K1_G

MRR=1.0000. [Conversation](../../../RQs/RQ3_4/results/integrated_v1/stages/exp_integrated_locked_check/qwen3.8-27b/conversations/c79b5411da9a98760943577ccb63dd7afdb9d5b2e733aeb10cefb7c7b6805ac9.md)

```json
{"services": ["1847", "66109", "29225"], "reason": "Metrics show node 1847 experienced a simultaneous and massive filesystem saturation to ~81%, a large 902MB disk read burst, and sustained pod memory spikes on hosted pods 66109 and 29225, which correlates with the observed 66109 response-time degradation. Corroborating topology evidence confirms 1847 physically hosts both problematic pods, and G-diagnostic onset timing for 1847 at 21m precedes the 217->192 application-level propagation failures, pointing to the co-located node as the initial origin.", "confidence": "high"}
```

### Qwen / P1H1K1_T

MRR=1.0000. [Conversation](../../../RQs/RQ3_4/results/integrated_v1/stages/exp_integrated_locked_check/qwen3.8-27b/conversations/7e19e65580465a1556d67c52595ce2eb58b1536bd591dba61af86daff22fea7b.md)

```json
{"services": ["1847", "29225", "1897"], "reason": "Node 1847 is the root cause as its filesystem usage surged from ~54% to ~81% (M5) starting around +18m, preceding the memory spike in co-located pod 29225 (M6) at +20m and its subsequent latency errors. This local resource exhaustion aligns with the propagation onset of 1847 at +21m, distinguishing it from upstream network blips on 9798 which showed negligible deviation.", "confidence": "high"}
```

### Gemma / TPV

MRR=1.0000. [Conversation](../../../RQs/RQ3_4/results/integrated_v1/stages/exp_integrated_locked_check/gemma-4-26b-a4b/conversations/1c6c1ae0dab4f1cbb56d832dad037fd70746990de16604c7302d968688a37fc7.md)

```json
{"services": ["1847"], "reason": "Node 1847 shows a massive disk read spike (z=315) and filesystem usage increase (z=2.17) starting around 27m, which correlates with the onset of downstream pod anomalies. Verification confirmed the disk IO spike precedes the latency increases in service 365 and the memory pressure in pod 64408. Although service 365 shows higher inclusive latency, its exclusive latency remains relatively stable, pointing to the infrastructure node as the origin.", "confidence": "high"}
```

### Gemma / P1H1K0_G

MRR=1.0000. [Conversation](../../../RQs/RQ3_4/results/integrated_v1/stages/exp_integrated_locked_check/gemma-4-26b-a4b/conversations/91c15f0740bc8f2303709d4bbf887fab2d39acf5f2ec517c383e7359921b90a3.md)

```json
{"services": ["1847"], "reason": "Node 1847 shows a massive filesystem usage increase (from 53% to 81%) and disk read spikes (z=315), preceding the onset of downstream service anomalies. Metric and trace data confirm that while downstream pods like 62540 and 64408 show memory pressure, the foundational filesystem pressure on node 1847 is the earliest structural change.", "confidence": "high"}
```

### Gemma / P1H1K1_G

MRR=1.0000. [Conversation](../../../RQs/RQ3_4/results/integrated_v1/stages/exp_integrated_locked_check/gemma-4-26b-a4b/conversations/2b300762df31fe69f85f6e6e04e14fc2b8145ddfd75a1998a6eb8ce9579746ce.md)

```json
{"services": ["1847"], "reason": "Node 1847 shows a massive deviation in disk read bytes and a significant increase in filesystem usage rate. This node hosts pods 29225 and 66109, and the disk pressure on 1847 aligns with the onset of subsequent anomalies across the service graph. Verified that node 1847's disk metric shift precedes the trace latency increases and log volume drops observed in downstream entities. ", "confidence": "high"}
```

```text
Additional observations use the same public reference/current intervals, in seconds from observation start. Medians describe measured samples; inclusive span duration includes child spans. Request counts deduplicate trace IDs and describe captured requests, not unobserved traffic. Calls and hosting are observed relations, not proof of failure propagation.
Host and instance observations:
{"entity": "66109", "region": "M", "semantic": "response", "unit": "source_unit", "values": {"current_interval_s": [1080.0, 1800.0], "current_median": 646.0, "current_samples": 13, "reference_interval_s": [0, 1080.0], "reference_mad": 26.5, "reference_median": 564.5, "reference_samples": 18}}
{"entity": "1847", "region": "M", "semantic": "node_filesystem_usage_rate", "unit": "source_unit", "values": {"current_interval_s": [1080.0, 1800.0], "current_median": 80.845, "current_samples": 13, "reference_interval_s": [0, 1080.0], "reference_mad": 0.015, "reference_median": 53.685, "reference_samples": 18}}
{"entity": "29225", "region": "M", "semantic": "response", "unit": "source_unit", "values": {"current_interval_s": [1080.0, 1800.0], "current_median": 8.0, "current_samples": 13, "reference_interval_s": [0, 1080.0], "reference_mad": 0.5, "reference_median": 6.0, "reference_samples": 18}}
{"from": "1847", "relation": "hosts", "to": "29225"}
{"from": "1847", "relation": "hosts", "to": "66109"}
Host and instance observations:
{"entity": "66109", "region": "M", "semantic": "pod_memory_working_set_bytes", "unit": "source_unit", "values": {"current_interval_s": [1080.0, 1800.0], "current_median": 1949937.6, "current_samples": 13, "reference_interval_s": [0, 1080.0], "reference_mad": 1000359.2, "reference_median": 1000359.2, "reference_samples": 18}}
{"entity": "1847", "region": "M", "semantic": "node_filesystem_usage_rate", "unit": "source_unit", "values": {"current_interval_s": [1080.0, 1800.0], "current_median": 80.845, "current_samples": 13, "reference_interval_s": [0, 1080.0], "reference_mad": 0.015, "reference_median": 53.685, "reference_samples": 18}}
{"entity": "66932", "region": "M", "semantic": "pod_memory_working_set_bytes", "unit": "source_unit", "values": {"current_interval_s": [1080.0, 1800.0], "current_median": 1242606.7, "current_samples": 13, "reference_interval_s": [0, 1080.0], "reference_mad": 162724.02, "reference_median": 1313613.9, "reference_samples": 18}}
{"from": "1847", "relation": "hosts", "to": "66932"}
{"from": "1847", "relation": "hosts", "to": "66109"}
Host and instance observations:
{"entity": "1897", "region": "M", "semantic": "node_memory_usage_rate", "unit": "source_unit", "values": {"current_interval_s": [1080.0, 1800.0], "current_median": 31.89, "current_samples": 13, "reference_interval_s": [0, 1080.0], "reference_mad": 0.36, "reference_median": 29.075, "reference_samples": 18}}
Host and instance observations:
{"entity": "1755", "region": "M", "semantic": "node_network_receive_packets_total", "unit": "source_unit", "values": {"current_interval_s": [1080.0, 1800.0], "current_median": 1.0, "current_samples": 13, "reference_interval_s": [0, 1080.0], "reference_mad": 0.0, "reference_median": 0.93, "reference_samples": 18}}
```

```text
Computed relations between displayed observations:
66109 response (source_unit): current_median is greater than reference_median.
66109 is a pod.
1847 node_filesystem_usage_rate (source_unit): current_median is greater than reference_median.
1847 is a node.
29225 response (source_unit): current_median is greater than reference_median.
29225 is a pod.
66109 pod_memory_working_set_bytes (source_unit): current_median is greater than reference_median.
1847 node_filesystem_usage_rate (source_unit): current_median is greater than reference_median.
66932 pod_memory_working_set_bytes (source_unit): current_median is less than reference_median.
66932 is a pod.
1897 node_memory_usage_rate (source_unit): current_median is greater than reference_median.
1897 is a node.
1755 node_network_receive_packets_total (source_unit): current_median is greater than reference_median.
1755 is a node.
Displayed G onset of 1897 is earlier than 192; this is temporal order, not fault causation.
Displayed G onset of 192 is earlier than 217; this is temporal order, not fault causation.
Observed relation: 217 calls 192.
```

### Gemma / P1H1K1_T

MRR=1.0000. [Conversation](../../../RQs/RQ3_4/results/integrated_v1/stages/exp_integrated_locked_check/gemma-4-26b-a4b/conversations/a7e1cb16c6acaeec578a841ad244bda2e27ed954901dc306c83101f858f9cac1.md)

```json
{"services": ["1847"], "reason": "Node 1847 shows a significant increase in filesystem usage rate and disk read activity starting around the onset window. These infrastructure anomalies precede the propagation of errors and latency seen in hosted pods like 29225 and 66109, confirming it as the origin.", "confidence": "high"}
```

## INC-6D1C8225111D

Private evaluation label: `{'ts-route-plan-service': '386', 'ts-travel-service': '860'}`

### Qwen / TPV

MRR=1.0000. [Conversation](../../../RQs/RQ3_4/results/integrated_v1/stages/exp_integrated_locked_check/qwen3.8-27b/conversations/346a5fabb4e54b1267b91ef4fe11f1e87d57e9202ec16878595ccb16ffd36f2f.md)

```json
{"services": ["386", "851", "163"], "reason": "Service 386 is the root origin, with evidence verifying the top candidate and ruling out an upstream node cause: it shows a dominant exclusive-latency explosion in the local POST operation (p95 ~3.67M ms, log2 fold +9.89) at the earliest trace onset (~4.5m), consistent with an origin rather than a callee symptom. While node 851 also shows an early, severe CPU burst (JVM/pod CPU spiking >20x baseline) at ~4.5m, it lacks a causally upstream caller/callee edge and no trace or log error evidence implicates it as the propagator, making 386 the decisive origin and 851 a co-located/resource symptom; service 163 is a primary downstream caller with a large (but subordinate) latency impact.", "confidence": "medium"}
```

### Qwen / P1H1K0_G

MRR=1.0000. [Conversation](../../../RQs/RQ3_4/results/integrated_v1/stages/exp_integrated_locked_check/qwen3.8-27b/conversations/da21658424a9129251326bf3d82f8f85588027ee3b2a13f576cc519c6d599dab.md)

```json
{"services": ["386", "851", "163"], "reason": "Service 386 is the root origin, with evidence verifying the top candidate and ruling out an upstream node cause: it shows a dominant exclusive-latency explosion in the local POST operation (p95 ~3.67M ms, log2 fold-change ~9.89), and its anomaly onset (~4.5m) precedes the edge-adjacent symptoms of 318, 851, and 928 (4.5–4.8m). Node 4562 was checked as an alternative co-located origin but rejected, as its hosted instances 41659 and 72072 show no deviation in memory_request (current and reference medians identical).", "confidence": "high"}
```

### Qwen / P1H1K1_G

MRR=0.0000. [Conversation](../../../RQs/RQ3_4/results/integrated_v1/stages/exp_integrated_locked_check/qwen3.8-27b/conversations/bbda59f6ded062644b26784f24675b0d8cdef537a7d308a34ef62fd111a77196.md)

```json
{"services": ["318", "133", "364"], "reason": "Service 318 is the root origin, with evidence verifying the top candidate and eliminating downstream alternatives. TRC-L traces show that 318's fault signals align temporally and topologically with the caller edges (318 calls 133, 184, and 159), indicating a propagation from 318 to its callees. Metric data further supports this as 318 is the only caller with an associated performance deviation (page faults current > reference), whereas 176's opposing deviation is a co-located distractor.", "confidence": "high"}
```

### Qwen / P1H1K1_T

MRR=0.0000. [Conversation](../../../RQs/RQ3_4/results/integrated_v1/stages/exp_integrated_locked_check/qwen3.8-27b/conversations/72fc2527f639e46fe32549a3bba4de1c8043be259b5115134074ee2e5b7e813c.md)

```json
{"services": ["318", "184", "133"], "reason": "Service 318 is the topologically upstream caller with the earliest onset (+4.5m) and highest severity (z=20.35), preceding the propagation to callee 184 (+4.5m, z=14.42). The trace evidence confirms high latency impact in 184 (rank_score 9.89) and 133, consistent with a failure originating in 318 and propagating downstream, while metric anomalies in 851 (z=257.5) appear slightly later (+4.8m) and lack direct trace causality to the primary call chain.", "confidence": "medium"}
```

### Gemma / TPV

MRR=0.0000. [Conversation](../../../RQs/RQ3_4/results/integrated_v1/stages/exp_integrated_locked_check/gemma-4-26b-a4b/conversations/a665851a6f2c0279847b221fc0fc467add019c8968db1151171568a1115d2461.md)

```json
{"services": ["851"], "reason": "Service 851 shows severe CPU and memory spikes (signed-z up to 257) starting at t=4.5m, which precedes all trace-derived latency increases in downstream callers 163 and 386. The onset of resource exhaustion in 851 aligns perfectly with the observed service-wide slowdown, confirming it as the origin rather than a symptom of the high latency in 386.", "confidence": "high"}
```

### Gemma / P1H1K0_G

MRR=0.0000. [Conversation](../../../RQs/RQ3_4/results/integrated_v1/stages/exp_integrated_locked_check/gemma-4-26b-a4b/conversations/e57a281fe010cc74f6476e8e9722613c380dfed6b7287aeed9fdab7041abbc55.md)

```json
{"services": ["851"], "reason": "Service 851 shows a massive spike in JVM CPU utilization (z=257.5) and memory usage starting at the beginning of the fault window, which precedes the latency spikes in downstream services 163 and 386. While 163 and 386 show high inclusive latency, their exclusive latencies do not explain the system-wide onset, and 851 is a clear resource-exhaustion origin. The temporal onset in G for 851 is consistent with the massive resource deviation in M.", "confidence": "high"}
```

### Gemma / P1H1K1_G

MRR=0.0000. [Conversation](../../../RQs/RQ3_4/results/integrated_v1/stages/exp_integrated_locked_check/gemma-4-26b-a4b/conversations/075acb8faf0d31d4f4df15499c1d9216d7db00ce1cef0ecb72dadce16e366d72.md)

```json
{"services": ["851"], "reason": "Service 851 shows severe CPU and memory spikes (signed-z up to 257) starting at t=4.5m, which precedes all other anomaly onsets. Trace and topology data show downstream latency in services like 386 and 163, but service 851 is the earliest metric-derived anomaly and lacks any upstream callers in the provided subgraph. Verification confirmed that 851's local CPU spike and memory pressure are the earliest observed symptoms.", "confidence": "high"}
```

```text
Additional observations use the same public reference/current intervals, in seconds from observation start. Medians describe measured samples; inclusive span duration includes child spans. Request counts deduplicate trace IDs and describe captured requests, not unobserved traffic. Calls and hosting are observed relations, not proof of failure propagation.
Host and instance observations:
{"entity": "41659", "region": "M", "semantic": "k8s.container.memory_request", "unit": "source_unit", "values": {"current_interval_s": [270.0, 480.0], "current_median": 1073741800.0, "current_samples": 15, "reference_interval_s": [0, 270.0], "reference_mad": 0.0, "reference_median": 1073741800.0, "reference_samples": 18}}
{"entity": "72072", "region": "M", "semantic": "k8s.container.memory_request", "unit": "source_unit", "values": {"current_interval_s": [270.0, 480.0], "current_median": 1073741800.0, "current_samples": 15, "reference_interval_s": [0, 270.0], "reference_mad": 0.0, "reference_median": 1073741800.0, "reference_samples": 18}}
{"from": "4562", "relation": "hosts", "to": "41659"}
{"from": "4562", "relation": "hosts", "to": "72072"}
Host and instance observations:
{"entity": "80382", "region": "M", "semantic": "k8s.container.ready", "unit": "source_unit", "values": {"current_interval_s": [270.0, 480.0], "current_median": 1.0, "current_samples": 15, "reference_interval_s": [0, 270.0], "reference_mad": 0.0, "reference_median": 1.0, "reference_samples": 18}}
{"entity": "25149", "region": "M", "semantic": "k8s.container.ready", "unit": "source_unit", "values": {"current_interval_s": [270.0, 480.0], "current_median": 1.0, "current_samples": 15, "reference_interval_s": [0, 270.0], "reference_mad": 0.0, "reference_median": 1.0, "reference_samples": 18}}
{"from": "2663", "relation": "hosts", "to": "80382"}
{"from": "2663", "relation": "hosts", "to": "25149"}
Host and instance observations:
{"entity": "318", "region": "M", "semantic": "container.memory.page_faults", "unit": "source_unit", "values": {"current_interval_s": [270.0, 480.0], "current_median": 151363.0, "current_samples": 15, "reference_interval_s": [0, 270.0], "reference_mad": 671.16667, "reference_median": 140431.83, "reference_samples": 18}}
Host and instance observations:
{"entity": "176", "region": "M", "semantic": "jvm.cpu.recent_utilization", "unit": "source_unit", "values": {"current_interval_s": [270.0, 480.0], "current_median": 0.0018960558, "current_samples": 15, "reference_interval_s": [0, 270.0], "reference_mad": 0.00023608614, "reference_median": 0.0038814604, "reference_samples": 18}}
```

```text
Computed relations between displayed observations:
318 container.memory.page_faults (source_unit): current_median is greater than reference_median.
318 is a service.
176 jvm.cpu.recent_utilization (source_unit): current_median is less than reference_median.
176 is a service.
Displayed G onset of 184 is earlier than 179; this is temporal order, not fault causation.
Displayed G onset of 318 is earlier than 364; this is temporal order, not fault causation.
Displayed G onset of 661 is earlier than 785; this is temporal order, not fault causation.
Displayed G onset of 851 is earlier than 785; this is temporal order, not fault causation.
Displayed G onset of 851 is earlier than 852; this is temporal order, not fault causation.
Displayed G onset of 852 is earlier than 928; this is temporal order, not fault causation.
Displayed G onset of 941 is earlier than 928; this is temporal order, not fault causation.
Observed relation: 133 calls 364.
Observed relation: 184 calls 928.
Observed relation: 318 calls 133.
Observed relation: 318 calls 159.
Observed relation: 318 calls 184.
```

### Gemma / P1H1K1_T

MRR=0.0000. [Conversation](../../../RQs/RQ3_4/results/integrated_v1/stages/exp_integrated_locked_check/gemma-4-26b-a4b/conversations/fd860612cda1dc7caf8451da3dee757c7f507dacf0c8d145e688f2b3dcbc2dc4.md)

```json
{"services": ["851"], "reason": "Service 851 shows the earliest onset of severe metric anomalies, specifically a massive spike in JVM CPU utilization (z=257.5) and memory working set (z=26.98). While service 318 has the highest rank score, its onset occurs later than 851, and 851's resource saturation independently explains the observed system instability. No other component shows a simultaneous or preceding resource-driven fault profile.", "confidence": "high"}
```

## INC-CCCFF766DA4B

Private evaluation label: `{'productcatalogservice-1': '57600'}`

### Qwen / TPV

MRR=0.0000. [Conversation](../../../RQs/RQ3_4/results/integrated_v1/stages/exp_integrated_locked_check/qwen3.8-27b/conversations/c4b5a85760e613ad7af1c9de00ce77a35eaa4d75d379909da03dc1df0f39d872.md)

```json
{"services": ["7458", "652", "112"], "reason": "TRC-L identifies service 652 (EmptyCart/AddItem) with the highest rank scores and largest exclusive latency degradation, while LOG-R confirms a fault-window volume drop on its pod 47174. G-topology confirms 652 is a downstream callee called by 112/218/161, making 652 the root origin.", "confidence": "high"}
```

### Qwen / P1H1K0_G

MRR=0.0000. [Conversation](../../../RQs/RQ3_4/results/integrated_v1/stages/exp_integrated_locked_check/qwen3.8-27b/conversations/eefb74d5163294316119e19df4fd3dd16e00bfecb92fe6733de4c94dcef95cf2.md)

```json
{"services": ["7458", "652", "112"], "reason": "Node 7458 is the origin, confirmed by the top-ranked exclusive-latency burst on node-local operations and the earliest (31m) fault-window onset driven by sustained node-level filesystem and disk-inode anomalies. Check 1 confirms the temporal origin, as 7458's onset precedes all downstream service symptoms; check 2 confirms the causal topology, as 7458 hosts the affected pods and terminates the caller->callee dependency chain (652 -> 112).", "confidence": "high"}
```

### Qwen / P1H1K1_G

MRR=0.0000. [Conversation](../../../RQs/RQ3_4/results/integrated_v1/stages/exp_integrated_locked_check/qwen3.8-27b/conversations/4adfc9eaa6390a45bb745024ae3d24b7659f6fabe03079164bbd427d0efd2d89.md)

```json
{"services": ["7458", "652", "112"], "reason": "Node 7458 is the only candidate showing a large, simultaneous disk and filesystem jump to ~4GB usage during the estimated fault window, and pod 57600 running on 7458 exhibits the matching elevated memory working set. Verified checks confirm no trace evidence points to 7458 as a local latency origin (its delay is an infrastructure footprint, not a service-compute delay) and the G topology places 7458 before its downstream callers, establishing it as the earliest plausible root.", "confidence": "medium"}
```

### Qwen / P1H1K1_T

MRR=0.0000. [Conversation](../../../RQs/RQ3_4/results/integrated_v1/stages/exp_integrated_locked_check/qwen3.8-27b/conversations/42c072b761419620d33d153ef487a26188d3a68486cd8d4b36e2ceda6d07afd7.md)

```json
{"services": ["7458", "781", "349"], "reason": "The node 7458 exhibits decisive, synchronized local resource saturation starting at bin 51 (~+27.7m), characterized by a step-change in disk/inode usage and a 20x spike in TCP out segments, preceding the estimated fault window start at +33.0m. Topological verification confirms that service 781, which has the earliest propagation onset (+20.0m) and significant exclusive latency increase in traces, is hosted on 7458, identifying the node's resource exhaustion as the upstream origin of the service-level symptoms.", "confidence": "high"}
```

### Gemma / TPV

MRR=0.0000. [Conversation](../../../RQs/RQ3_4/results/integrated_v1/stages/exp_integrated_locked_check/gemma-4-26b-a4b/conversations/6c49e2858fadc18b922ec2da90abf170e3dd478b6e87dff0dcd0ea4b70df0cdc.md)

```json
{"services": ["7458"], "reason": "Node 7458 exhibits a massive, simultaneous surge in disk usage, inode usage, and network output segments starting at the beginning of the fault window. Traces for downstream services show latency increases, but node 7458's resource exhaustion is the earliest and most severe anomaly. The spike in disk and inode metrics identifies the node as the primary origin rather than a service-level software fault.", "confidence": "high"}
```

### Gemma / P1H1K0_G

MRR=0.0000. [Conversation](../../../RQs/RQ3_4/results/integrated_v1/stages/exp_integrated_locked_check/gemma-4-26b-a4b/conversations/78894f5cbc3ce7eaf37b3b1a2ea9c8b8d683db45e6006a79503251109bd96dc1.md)

```json
{"services": ["7458"], "reason": "Node 7458 exhibits a massive spike in disk usage and inode utilization starting at $t=33$m, which precedes the propagation of symptoms across the cluster. Metric analysis confirms the disk and inode surges are highly significant, and they occur before the onset of errors in downstream services. While service 77548 shows CPU throttling, this is a symptom of resource contention rather than the origin.", "confidence": "high"}
```

### Gemma / P1H1K1_G

MRR=1.0000. [Conversation](../../../RQs/RQ3_4/results/integrated_v1/stages/exp_integrated_locked_check/gemma-4-26b-a4b/conversations/3026af2770a2b178263bc645720a41ff69c346cae7d98b6336c1690de88f09db.md)

```json
{"services": ["57600"], "reason": "Pod 57600 on node 7458 exhibits a massive increase in memory failcnt and disk usage, which preceded the network and inode anomalies on the same node. Traces and logs show downstream symptoms, but the infrastructure-level resource exhaustion at the pod/node level is the primary driver. The temporal onset of node-level metrics correlates with the cascading failure of service-level operations.", "confidence": "high"}
```

```text
Additional observations use the same public reference/current intervals, in seconds from observation start. Medians describe measured samples; inclusive span duration includes child spans. Request counts deduplicate trace IDs and describe captured requests, not unobserved traffic. Calls and hosting are observed relations, not proof of failure propagation.
Host and instance observations:
{"entity": "14560", "region": "M", "semantic": "container_memory_mapped_file", "unit": "source_unit", "values": {"current_interval_s": [1200.0, 2340.0], "current_median": 8192.0, "current_samples": 20, "reference_interval_s": [0, 1200.0], "reference_mad": 0.0, "reference_median": 8192.0, "reference_samples": 20}}
{"entity": "4668", "region": "M", "semantic": "system.load.5", "unit": "source_unit", "values": {"current_interval_s": [1200.0, 2340.0], "current_median": 1.485, "current_samples": 20, "reference_interval_s": [0, 1200.0], "reference_mad": 0.03, "reference_median": 1.24, "reference_samples": 20}}
{"entity": "51863", "region": "M", "semantic": "container_memory_mapped_file", "unit": "source_unit", "values": {"current_interval_s": [1200.0, 2340.0], "current_median": 745472.0, "current_samples": 20, "reference_interval_s": [0, 1200.0], "reference_mad": 0.0, "reference_median": 741376.0, "reference_samples": 20}}
{"from": "4668", "relation": "hosts", "to": "14560"}
{"from": "4668", "relation": "hosts", "to": "51863"}
Host and instance observations:
{"entity": "15658", "region": "M", "semantic": "container_fs_inodes./dev/vda1", "unit": "source_unit", "values": {"current_interval_s": [1200.0, 2340.0], "current_median": 0.0, "current_samples": 20, "reference_interval_s": [0, 1200.0], "reference_mad": 0.0, "reference_median": 0.0, "reference_samples": 20}}
{"entity": "4668", "region": "M", "semantic": "system.load.5", "unit": "source_unit", "values": {"current_interval_s": [1200.0, 2340.0], "current_median": 1.485, "current_samples": 20, "reference_interval_s": [0, 1200.0], "reference_mad": 0.03, "reference_median": 1.24, "reference_samples": 20}}
{"entity": "14560", "region": "M", "semantic": "container_fs_inodes./dev/vda1", "unit": "source_unit", "values": {"current_interval_s": [1200.0, 2340.0], "current_median": 0.0, "current_samples": 20, "reference_interval_s": [0, 1200.0], "reference_mad": 0.0, "reference_median": 0.0, "reference_samples": 20}}
{"from": "4668", "relation": "hosts", "to": "15658"}
{"from": "4668", "relation": "hosts", "to": "14560"}
Host and instance observations:
{"entity": "57600", "region": "M", "semantic": "container_memory_working_set_MB", "unit": "source_unit", "values": {"current_interval_s": [1200.0, 2340.0], "current_median": 46.467773, "current_samples": 20, "reference_interval_s": [0, 1200.0], "reference_mad": 0.16341146, "reference_median": 31.616862, "reference_samples": 20}}
{"entity": "18219", "region": "M", "semantic": "container_memory_working_set_MB", "unit": "source_unit", "values": {"current_interval_s": [1200.0, 2340.0], "current_median": 79.324219, "current_samples": 20, "reference_interval_s": [0, 1200.0], "reference_mad": 0.0, "reference_median": 79.371094, "reference_samples": 20}}
{"from": "7458", "relation": "hosts", "to": "57600"}
{"from": "7458", "relation": "hosts", "to": "18219"}
Host and instance observations:
{"entity": "57600", "region": "M", "semantic": "container_memory_failcnt", "unit": "source_unit", "values": {"current_interval_s": [1200.0, 2340.0], "current_median": 8467334.0, "current_samples": 20, "reference_interval_s": [0, 1200.0], "reference_mad": 0.0, "reference_median": 3222490.0, "reference_samples": 20}}
{"entity": "24397", "region": "M", "semantic": "container_memory_failcnt", "unit": "source_unit", "values": {"current_interval_s": [1200.0, 2340.0], "current_median": 538398.0, "current_samples": 20, "reference_interval_s": [0, 1200.0], "reference_mad": 0.0, "reference_median": 538398.0, "reference_samples": 20}}
{"from": "7458", "relation": "hosts", "to": "57600"}
{"from": "7458", "relation": "hosts", "to": "24397"}
```

```text
Computed relations between displayed observations:
4668 system.load.5 (source_unit): current_median is greater than reference_median.
4668 is a node.
51863 container_memory_mapped_file (source_unit): current_median is greater than reference_median.
51863 is a pod.
4668 system.load.5 (source_unit): current_median is greater than reference_median.
57600 container_memory_working_set_MB (source_unit): current_median is greater than reference_median.
57600 is a pod.
18219 container_memory_working_set_MB (source_unit): current_median is less than reference_median.
18219 is a pod.
57600 container_memory_failcnt (source_unit): current_median is greater than reference_median.
Displayed G onset of 112 is earlier than 161; this is temporal order, not fault causation.
Displayed G onset of 349 is earlier than 218; this is temporal order, not fault causation.
Displayed G onset of 349 is earlier than 448; this is temporal order, not fault causation.
Displayed G onset of 652 is earlier than 448; this is temporal order, not fault causation.
```

### Gemma / P1H1K1_T

MRR=0.0000. [Conversation](../../../RQs/RQ3_4/results/integrated_v1/stages/exp_integrated_locked_check/gemma-4-26b-a4b/conversations/193817d3ff0c31743c5864dc1bd256f05a5267d3e87856fbfa68744a54a4f7d9.md)

```json
{"services": ["781"], "reason": "Service 781 shows the earliest onset of severity (+20.0m) among all services. Verification confirmed that while service 349 and node 7458 exhibit significant metric shifts, service 781 precedes them temporally and acts as a central caller in the topology, making it the plausible origin. The metric shifts in node 7458 and its hosted pods occur significantly later (+31.0m onwards).", "confidence": "high"}
```

## INC-B63AC53AB86F

Private evaluation label: `{'productcatalogservice-2': '92244'}`

### Qwen / TPV

MRR=0.0000. [Conversation](../../../RQs/RQ3_4/results/integrated_v1/stages/exp_integrated_locked_check/qwen3.8-27b/conversations/eb44ed404f136d7460fd94d6b9426743d444b2a8b2879363c83eaa8c44bd206d.md)

```json
{"services": ["200", "106", "224"], "reason": "MET-Z shows service 200 spiked first (bin 32) with an extreme 822σ deviation, while 106 and 224 showed strong local spikes at the same bin 32 onset. Topology verifies this origin by showing 106 and 128 as direct callers of 200, which explains their co-occurring latency spikes as downstream propagation rather than independent faults.", "confidence": "high"}
```

### Qwen / P1H1K0_G

MRR=0.0000. [Conversation](../../../RQs/RQ3_4/results/integrated_v1/stages/exp_integrated_locked_check/qwen3.8-27b/conversations/ad837dd2a5c28e696887200d4237d92511eb0ee623334a6250a77f00de7f6166.md)

```json
{"services": ["200", "106", "224"], "reason": "MET-Z shows service 200 spiked first (bin 32) with an extreme mean shift over 3sigma, while R confirms service 106 exhibits a massive exclusive-latency burst (8.4k log2 fold) starting at bin 34, indicating local processing failure. G topology shows 246->224, supporting 106 (the latency origin) and 200 (the earliest metric origin) as the root cause cluster rather than the downstream 224 callers.", "confidence": "medium"}
```

### Qwen / P1H1K1_G

MRR=0.0000. [Conversation](../../../RQs/RQ3_4/results/integrated_v1/stages/exp_integrated_locked_check/qwen3.8-27b/conversations/f7b4c63f9f0a82fc60b004ba95215bd8772fd85ae53ebec5957aaf2a8004bd2e.md)

```json
{"services": ["224", "246", "200"], "reason": "Service 224 is the root origin, with confirmed caller→callee edges 323→224 and 421→224 from an earlier onset (19.1m) that temporally precedes 246 (19.9m), 200 (20m), and 106 (20m). While alternative origin 246→224 is contradicted by this causal topology, metric 200/mrt (z=59.6) and 106/mrt (z=264) co-location with 224 is consistent with 224 as a shared downstream dependency.", "confidence": "high"}
```

### Qwen / P1H1K1_T

MRR=1.0000. [Conversation](../../../RQs/RQ3_4/results/integrated_v1/stages/exp_integrated_locked_check/qwen3.8-27b/conversations/b641173f2463011ed9b43a17ebff7a9a20f2d0c94f763867f1f729c77d251a63.md)

```json
{"services": ["92244", "323", "224"], "reason": "TRC-L identifies pod 92244 as the root cause with an exclusive latency p95 spike to 2.86s (rank score 9.31), indicating local processing failure rather than downstream delay. Topology verifies this origin by showing 92244 is not a caller in the propagation graph, whereas it is a callee of 224, and G confirms the earliest R-derived onset is at the upstream caller 323 which invokes 224, consistent with the fault originating in 92244 and propagating to 224's callers.", "confidence": "high"}
```

### Gemma / TPV

MRR=1.0000. [Conversation](../../../RQs/RQ3_4/results/integrated_v1/stages/exp_integrated_locked_check/gemma-4-26b-a4b/conversations/7d5917ce03793cd21784e78a21ce98eb4904dd59ceab674150ca05a2ac6dc185.md)

```json
{"services": ["92244"], "reason": "Service 92244 exhibits the highest TRC-L rank score due to an extreme p95 latency spike (9.31 LFC), which precedes the onset of latency in 27456 and 72218. Although 128 and 106 show significant metric deviations, they are downstream or co-located symptoms of the resource/latency pressure initiated by 92244. The temporal propagation from 92244 through the call graph confirms its role as the origin.", "confidence": "high"}
```

### Gemma / P1H1K0_G

MRR=1.0000. [Conversation](../../../RQs/RQ3_4/results/integrated_v1/stages/exp_integrated_locked_check/gemma-4-26b-a4b/conversations/3c5d2a29080ab32d13d46ee2e581137062bd8f54847a37dab798d43516fee6a2.md)

```json
{"services": ["92244"], "reason": "Service 92244 exhibits the highest TRC-L rank score due to an extreme p95 latency jump from 4.5s to 2866s. Verification against M and G confirms that while other services like 27456 and 128 show significant latency shifts, 92244's latency is not explained by downstream child span delays. The onset of latency in downstream callers follows the massive latency increase in 92244.", "confidence": "high"}
```

### Gemma / P1H1K1_G

MRR=0.0000. [Conversation](../../../RQs/RQ3_4/results/integrated_v1/stages/exp_integrated_locked_check/gemma-4-26b-a4b/conversations/0a1099cb1dfea2ae50573affca576ad216d938aa7991bd4ce102b8d0af59b254.md)

```json
{"services": ["128"], "reason": "Service 128 shows the earliest onset of extreme latency and metric deviation, with a huge increase in MRT. While service 224 and 92244 also show high latency, their inclusive latency spikes are consistent with downstream propagation from the root 128. Verification confirms 128's error-free status and local latency spike before downstream services 224 and 337 exhibited symptoms. ", "confidence": "high"}
```

```text
Additional observations use the same public reference/current intervals, in seconds from observation start. Medians describe measured samples; inclusive span duration includes child spans. Request counts deduplicate trace IDs and describe captured requests, not unobserved traffic. Calls and hosting are observed relations, not proof of failure propagation.
Host and instance observations:
{"entity": "67859", "region": "M", "semantic": "container_sockets", "unit": "source_unit", "values": {"current_interval_s": [1140.0, 2340.0], "current_median": 8.0, "current_samples": 21, "reference_interval_s": [0, 1140.0], "reference_mad": 0.0, "reference_median": 8.0, "reference_samples": 19}}
{"entity": "5150", "region": "M", "semantic": "system.net.packets_in.count", "unit": "source_unit", "values": {"current_interval_s": [1140.0, 2340.0], "current_median": 89.15, "current_samples": 21, "reference_interval_s": [0, 1140.0], "reference_mad": 0.96, "reference_median": 87.09, "reference_samples": 19}}
{"entity": "72218", "region": "M", "semantic": "container_sockets", "unit": "source_unit", "values": {"current_interval_s": [1140.0, 2340.0], "current_median": 17.0, "current_samples": 21, "reference_interval_s": [0, 1140.0], "reference_mad": 0.0, "reference_median": 15.0, "reference_samples": 19}}
{"from": "5150", "relation": "hosts", "to": "67859"}
{"from": "5150", "relation": "hosts", "to": "72218"}
Host and instance observations:
{"entity": "87167", "region": "M", "semantic": "container_memory_max_usage_MB", "unit": "source_unit", "values": {"current_interval_s": [1140.0, 2340.0], "current_median": 252.61328, "current_samples": 21, "reference_interval_s": [0, 1140.0], "reference_mad": 0.0, "reference_median": 252.61328, "reference_samples": 19}}
{"entity": "9624", "region": "M", "semantic": "system.net.bytes_sent", "unit": "source_unit", "values": {"current_interval_s": [1140.0, 2340.0], "current_median": 96786.13, "current_samples": 21, "reference_interval_s": [0, 1140.0], "reference_mad": 635.65, "reference_median": 95272.55, "reference_samples": 19}}
{"entity": "78915", "region": "M", "semantic": "container_memory_max_usage_MB", "unit": "source_unit", "values": {"current_interval_s": [1140.0, 2340.0], "current_median": 90.308594, "current_samples": 21, "reference_interval_s": [0, 1140.0], "reference_mad": 0.72265625, "reference_median": 84.798828, "reference_samples": 19}}
{"from": "9624", "relation": "hosts", "to": "78915"}
{"from": "9624", "relation": "hosts", "to": "87167"}
Host and instance observations:
{"entity": "78915", "region": "M", "semantic": "container_file_descriptors", "unit": "source_unit", "values": {"current_interval_s": [1140.0, 2340.0], "current_median": 163.0, "current_samples": 21, "reference_interval_s": [0, 1140.0], "reference_mad": 0.0, "reference_median": 163.0, "reference_samples": 19}}
{"entity": "15075", "region": "M", "semantic": "container_file_descriptors", "unit": "source_unit", "values": {"current_interval_s": [1140.0, 2340.0], "current_median": 25.0, "current_samples": 21, "reference_interval_s": [0, 1140.0], "reference_mad": 0.0, "reference_median": 23.0, "reference_samples": 19}}
{"from": "9624", "relation": "hosts", "to": "78915"}
{"from": "9624", "relation": "hosts", "to": "15075"}
Host and instance observations:
{"entity": "78095", "region": "M", "semantic": "istio_agent_go_memstats_stack_inuse_bytes", "unit": "source_unit", "values": {"current_interval_s": [1140.0, 2340.0], "current_median": 1933312.0, "current_samples": 21, "reference_interval_s": [0, 1140.0], "reference_mad": 0.0, "reference_median": 2031616.0, "reference_samples": 19}}
```

```text
Computed relations between displayed observations:
5150 system.net.packets_in.count (source_unit): current_median is greater than reference_median.
5150 is a node.
72218 container_sockets (source_unit): current_median is greater than reference_median.
72218 is a pod.
9624 system.net.bytes_sent (source_unit): current_median is greater than reference_median.
9624 is a node.
78915 container_memory_max_usage_MB (source_unit): current_median is greater than reference_median.
78915 is a pod.
15075 container_file_descriptors (source_unit): current_median is greater than reference_median.
15075 is a pod.
78095 istio_agent_go_memstats_stack_inuse_bytes (source_unit): current_median is less than reference_median.
78095 is a pod.
Displayed G onset of 106 is earlier than 111; this is temporal order, not fault causation.
Displayed G onset of 128 is earlier than 111; this is temporal order, not fault causation.
Displayed G onset of 224 is earlier than 128; this is temporal order, not fault causation.
Observed relation: 246 calls 224.
Observed relation: 246 calls 337.
```

### Gemma / P1H1K1_T

MRR=0.0000. [Conversation](../../../RQs/RQ3_4/results/integrated_v1/stages/exp_integrated_locked_check/gemma-4-26b-a4b/conversations/8bc03b15b684d35b9f1494ca3600dcae98eef75d79aa2c106795bc929b035451.md)

```json
{"services": ["323"], "reason": "Service 323 shows the earliest onset of severe latency and error signals in R, predating the 19.1m onset seen in downstream services like 421 and 224. While 224 exhibits massive latency in R, it is a callee of 323, and the temporal order of onset in G confirms 323 as the lead indicator. Verification confirmed that 323's onset occurs before the propagation to 224 and 421.", "confidence": "high"}
```

## INC-E196793B7152

Private evaluation label: `{'ts-station-food-service': '451'}`

### Qwen / TPV

MRR=0.0000. [Conversation](../../../RQs/RQ3_4/results/integrated_v1/stages/exp_integrated_locked_check/qwen3.8-27b/conversations/8234b6fb47ef9afd17dec06129c0899f8145986b66fb7cdced141fb67f041e2f.md)

```json
{"services": ["446", "755", "512"], "reason": "Service 446 is the root origin, with evidence verifying the top candidate and ruling out an upstream node cause: it is a callee (caller 755 -> callee 446) and its TRC-L exclusive p95 for the 'SELECT ts.consign_price' operation spiked from 1355ms to 18690ms (score 4.07) while its call count was nearly stable, proving local database latency rather than inherited downstream delay; concurrently, its G-onset at 3.8m predates the 4m onsets of callers 755, 845, and 112, and the correlated new 'Aborted connection' logs in 94450 are a consequence of those 18-second DB queries timing out, not an independent or earlier origin.", "confidence": "high"}
```

### Qwen / P1H1K0_G

MRR=0.0000. [Conversation](../../../RQs/RQ3_4/results/integrated_v1/stages/exp_integrated_locked_check/qwen3.8-27b/conversations/0fd0798c5b05d9120acb1d1fc9596cff9278209605f79c894ceb6a50e5e088b6.md)

```json
{"services": ["446", "755", "512"], "reason": "Service 446 is the root origin, with evidence verifying the top candidate and ruling out an upstream node cause: it is a callee (G edges 112->451, 773->845 list no upstream calls to 446) and its TRC-L shows the highest local service change (exclusive-latency log2-fold 3.78, rank 4.07, SELECT ts.consign_price) consistent with the metric onset window; the alternate origin 451 is contradicted because its flat memory baseline (reference median 0.0, MAD 0.0) shows no real deviation, and the co-located container restart on pod 47022/node 4537 is an independent failure not on the call path.", "confidence": "medium"}
```

### Qwen / P1H1K1_G

MRR=0.0000. [Conversation](../../../RQs/RQ3_4/results/integrated_v1/stages/exp_integrated_locked_check/qwen3.8-27b/conversations/ab1218295853bdbd37c2faaafcdc496de8958c7c827ce375637fbf483b00f801.md)

```json
{"services": ["446", "755", "512"], "reason": "TRC-L shows a decisive local root-cause signature at 446 with an exclusive-latency p95 surge of 3.78 log2 fold change driven by the local 'SELECT ts.consign_price' operation, rather than slow child spans. Verified checks confirm that callers 755 and 512 exhibit extremely high inclusive latency (up to ~4.7M ms) while their exclusive latency remains comparatively modest, proving they are victims waiting on 446; the 370->112->451 memory/crash branch lacks a supporting upstream latency trigger, leaving 446 as the independent origin.", "confidence": "high"}
```

### Qwen / P1H1K1_T

MRR=0.0000. [Conversation](../../../RQs/RQ3_4/results/integrated_v1/stages/exp_integrated_locked_check/qwen3.8-27b/conversations/d6f103924878e7b3f94a8bea39f705bfc995148d7f3c21e8b0577a203fb19f6a.md)

```json
{"services": ["446", "755", "512"], "reason": "Service 446 is the root cause because it exhibits the highest trace anomaly rank score (4.07) driven by a massive 3.78 log2 fold change in exclusive latency for the 'SELECT ts.consign_price' operation, while the only other component with a high trace score, 755, is a downstream caller of 512 whose symptoms are consistent with propagation. This is corroborated by node 94450 logs showing 'Aborted connection' errors to the database, which aligns with the database latency spike in 446, and the topology confirms no upstream caller of 446 is exhibiting earlier or more severe primary faults.", "confidence": "high"}
```

### Gemma / TPV

MRR=0.0000. [Conversation](../../../RQs/RQ3_4/results/integrated_v1/stages/exp_integrated_locked_check/gemma-4-26b-a4b/conversations/1cdaaca7348cf9a8d7f54da4e411182963fe992d0243bd334a45ae41475daa43.md)

```json
{"services": ["94450"], "reason": "Pod 94450 is the root cause because it exhibits a burst of database connection error logs (LT7496) stating 'Aborted connection to db: ts'. This error precedes the latency spikes in services 755 and 512 and corresponds to the earliest temporal onset of failure observed in the system logs.", "confidence": "high"}
```

### Gemma / P1H1K0_G

MRR=0.0000. [Conversation](../../../RQs/RQ3_4/results/integrated_v1/stages/exp_integrated_locked_check/gemma-4-26b-a4b/conversations/4e2a72a4c79ddbf6ec5c0ad923c134b8ee37f9be4193766295c39341eaafcfdf.md)

```json
{"services": ["94450"], "reason": "Pod 94450 is the root cause because it exhibits a burst of database connection error logs (LT7496) which directly precedes the latency spikes in services 512 and 755. While pod 47022 shows restarts, the error logs in 94450 provide the specific connectivity failure mechanism that matches the observed trace latency increases. The topology shows 755 calling 512, but the log-based error onset in 94450 is the most granular and earliest evidence of the database-related fault.", "confidence": "high"}
```

### Gemma / P1H1K1_G

MRR=1.0000. [Conversation](../../../RQs/RQ3_4/results/integrated_v1/stages/exp_integrated_locked_check/gemma-4-26b-a4b/conversations/b3fe39cf33f16959f10f5cd573892422b7727b4d9aa2ec79fb3244e4141af862.md)

```json
{"services": ["47022"], "reason": "Pod 47022 shows a massive increase in container restarts starting at the onset of the window. While service 451 exhibits significant memory fluctuations and service 755 shows high inclusive latency, 47022 is the earliest distinct fault onset and lacks the downstream dependency symptoms seen in the service traces. Verification confirmed that the 47022 restart onset precedes the widespread latency spikes in the caller services.", "confidence": "high"}
```

```text
Additional observations use the same public reference/current intervals, in seconds from observation start. Medians describe measured samples; inclusive span duration includes child spans. Request counts deduplicate trace IDs and describe captured requests, not unobserved traffic. Calls and hosting are observed relations, not proof of failure propagation.
Host and instance observations:
{"entity": "61833", "region": "M", "semantic": "k8s.container.restarts", "unit": "source_unit", "values": {"current_interval_s": [225.0, 465.0], "current_median": 0.0, "current_samples": 17, "reference_interval_s": [0, 225.0], "reference_mad": 0.0, "reference_median": 0.0, "reference_samples": 15}}
{"entity": "47022", "region": "M", "semantic": "k8s.container.restarts", "unit": "source_unit", "values": {"current_interval_s": [225.0, 465.0], "current_median": 1.0, "current_samples": 17, "reference_interval_s": [0, 225.0], "reference_mad": 0.0, "reference_median": 0.0, "reference_samples": 15}}
{"from": "4537", "relation": "hosts", "to": "61833"}
{"from": "4537", "relation": "hosts", "to": "47022"}
Host and instance observations:
{"entity": "50636", "region": "M", "semantic": "k8s.container.restarts", "unit": "source_unit", "values": {"current_interval_s": [225.0, 465.0], "current_median": 0.0, "current_samples": 17, "reference_interval_s": [0, 225.0], "reference_mad": 0.0, "reference_median": 0.0, "reference_samples": 15}}
{"entity": "47022", "region": "M", "semantic": "k8s.container.restarts", "unit": "source_unit", "values": {"current_interval_s": [225.0, 465.0], "current_median": 1.0, "current_samples": 17, "reference_interval_s": [0, 225.0], "reference_mad": 0.0, "reference_median": 0.0, "reference_samples": 15}}
{"from": "4537", "relation": "hosts", "to": "50636"}
{"from": "4537", "relation": "hosts", "to": "47022"}
Host and instance observations:
{"entity": "755", "region": "M", "semantic": "container.memory.usage", "unit": "source_unit", "values": {"current_interval_s": [225.0, 465.0], "current_median": 65152341.0, "current_samples": 17, "reference_interval_s": [0, 225.0], "reference_mad": 2194090.7, "reference_median": 34699947.0, "reference_samples": 15}}
Host and instance observations:
{"entity": "701", "region": "M", "semantic": "queueSize", "unit": "source_unit", "values": {"current_interval_s": [225.0, 465.0], "current_median": 44.5, "current_samples": 17, "reference_interval_s": [0, 225.0], "reference_mad": 1.0, "reference_median": 3.5, "reference_samples": 15}}
```

```text
Computed relations between displayed observations:
47022 k8s.container.restarts (source_unit): current_median is greater than reference_median.
47022 is a pod.
47022 k8s.container.restarts (source_unit): current_median is greater than reference_median.
755 container.memory.usage (source_unit): current_median is greater than reference_median.
755 is a service.
701 queueSize (source_unit): current_median is greater than reference_median.
701 is a service.
Displayed G onset of 370 is earlier than 112; this is temporal order, not fault causation.
Displayed G onset of 678 is earlier than 681; this is temporal order, not fault causation.
Displayed G onset of 681 is earlier than 717; this is temporal order, not fault causation.
Displayed G onset of 755 is earlier than 717; this is temporal order, not fault causation.
Displayed G onset of 773 is earlier than 755; this is temporal order, not fault causation.
Displayed G onset of 773 is earlier than 845; this is temporal order, not fault causation.
Displayed G onset of 845 is earlier than 871; this is temporal order, not fault causation.
Observed relation: 112 calls 451.
Observed relation: 773 calls 845.
```

### Gemma / P1H1K1_T

MRR=1.0000. [Conversation](../../../RQs/RQ3_4/results/integrated_v1/stages/exp_integrated_locked_check/gemma-4-26b-a4b/conversations/ffd4410f20cb8f46bbd52eb58636c934161c3e2c77ab4858a50c827acccb39e9.md)

```json
{"services": ["47022"], "reason": "Pod 47022 shows a restart event with a significant Z-score in k8s.container.restarts (M1), which precedes the latency and error propagation seen in other services. While service 451 exhibits extreme memory metric fluctuations, the topology and temporal onset of the container restarts in 47022 align with the start of the fault window. The restart event is a discrete infrastructure failure that explains the subsequent service instability. ", "confidence": "high"}
```
