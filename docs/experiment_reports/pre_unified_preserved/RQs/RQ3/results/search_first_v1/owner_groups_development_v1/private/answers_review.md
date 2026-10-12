## INC-9FFDC80821DC / aiops2022 / reused=False
RR 1.0 -> 1.0; joint=1
Accepted (private): ['emailservice']

```json
{"services": ["31794", "2649", "30650", "36490", "41307"], "reason": "Pod 31794 is the leading root cause candidate due to a severe local resource exhaustion signature. Metrics M07 and M08 show container CPU usage spiking from a near-zero baseline (~0.002s) to ~12.9s, a massive z-score deviation that coincides with the incident window. This is corroborated by Logs LT64 and LT308 on entity 31794, which report new errors including 'Exception while exporting Span batch' and gRPC transport dialing timeouts (io_timeout). The trace for 31794 shows its exclusive p95 latency increasing from 0.238ms to 3.29ms, indicating internal processing delay consistent with the CPU saturation. Node 2649 is ranked second as it exhibits concurrent system-level anomalies (M100 cpu.user peak 11, M73 mem.pct_usage peak 57.9), suggesting either a co-located infrastructure issue or a heavy impact from the pod's behavior. Service 30650 is a caller in the topology (calling 31794) whose latency increased significantly (14.1ms -> 606ms), likely due to propagation from the faulty callee rather than being the origin. Pods 36490 and 41307 are other members of the same service group showing similar but less extreme CPU spikes and error logs, making them plausible contributors or victims of the same underlying fault domain.", "confidence": "medium"}
```

## INC-107AD4FC7293 / aiops2022 / reused=False
RR 1.0 -> 1.0; joint=1
Accepted (private): ['checkoutservice']

```json
{"services": ["44733", "161", "5228", "7270", "7556"], "reason": "Pod 44733 is the primary root cause candidate, evidenced by a massive latency spike (exclusive p95 increasing from ~3.5-4 ms to ~9-10k ms) and high z-score (-64.9) in traces for operations like 'Convert' and 'GetCart'. This is supported by logs showing new gRPC transport errors ('Error while dialing') originating from entity 44733. Service 161 exhibits concurrent memory anomalies (high z-score on jvm_classes_loaded), but its trace evidence is less severe than 44733's explicit error/latency failures. Nodes 5228 and 7270 show resource metric spikes (memory usage and CPU load respectively) with moderate z-scores, suggesting they may be contributing factors or victims of the incident, but lack the direct application-level failure evidence seen in pod 44733.", "confidence": "medium"}
```

## INC-C46E27857BC0 / aiops2022 / reused=False
RR 0.25 -> 0.25; joint=2
Accepted (private): ['node-5']

```json
{"services": ["20192", "87592", "303", "6111", "179"], "reason": "Pod 20192 (service 163) is the leading hypothesis due to a severe, sustained drop in container_memory_cache from ~19.1M to ~9.4M (z=-325) coinciding with the fault window; this memory exhaustion likely caused the significant latency regression observed in its associated trace operation hipstershop.303/SendOrderConfirmation (p95 latency increased 3.34ms -> 28.4ms). Pod 87592 (service 649) is a secondary candidate given an extremely high z-score (999) for istio_agent_go_gc_duration_seconds_0.0, indicating potential garbage collection stalls, though the absolute value change appears small. Service 303 is implicated as the direct owner of the degraded SendOrderConfirmation operation and logs 'failed to retrieve ads' warnings. Node 6111 and Service 179 are lower-ranked alternatives showing moderate load increases (system.load.15) and memory fluctuations respectively, but lacking the specific resource-exhaustion profile or direct error correlation seen in the top candidates.", "confidence": "medium"}
```

## INC-284EAF7B78B5 / aiops2022 / reused=True
RR 0.0 -> 0.0; joint=0
Accepted (private): ['adservice']

```json
{"services": ["8448", "9357", "1712", "43483", "93900"], "reason": "Node 8448 exhibits a coherent, multi-dimensional resource exhaustion signature that aligns temporally with the incident window. Metrics M66 (CPU user), M04 (disk free), M05 (disk total), and M06 (disk used) all show sharp step-changes or spikes within the shaded anomalous interval, indicating simultaneous pressure on compute and storage resources. The topology graph shows service 705 (associated with pod 43483) calling services 137 and 690; while the dashboard does not explicitly state which node hosts these pods, the concurrent latency increases in traces for operations 84088 and 72379 suggest downstream impact from this infrastructure degradation. Node 9357 shows CPU spikes but lacks the compound disk/CPU failure profile of 8448. Node 1712 shows memory anomalies but is less comprehensive. Pod 43483 and Service 93900 are ranked lower as likely victims or partial contributors rather than the primary infrastructure origin.", "confidence": "medium"}
```

## INC-4BA2D386B400 / aiops2022 / reused=False
RR 0.3333333333333333 -> 0.25; joint=1
Accepted (private): ['node-2']

```json
{"services": ["21457", "92497", "3279", "4609", "43286"], "reason": "The incident is initiated by a traffic drop and latency spike on entity 21457, which has the earliest estimated anomaly onset (19.2 min). The topology graph shows 21457 as a caller to 92497, and 92497 exhibits significant resource anomalies (CPU z=28.9) and error logs ('FailedPrecondition') consistent with downstream failure. Node 3279 shows a concurrent memory free-space drop (z=999), suggesting potential host-level resource contention affecting services on that node, though no direct hosting relationship is visible. Pod 43286 shows high CPU usage but its trace metrics show reduced volume rather than increased latency, making it less likely to be the primary origin compared to 21457.", "confidence": "medium"}
```

## INC-0BD935F7BAAE / aiops2022 / reused=False
RR 0.5 -> 1.0; joint=1
Accepted (private): ['emailservice-1']

```json
{"services": ["68063", "1420", "3143", "25190", "177"], "reason": "Pod 68063 (service 460) is the leading root-cause candidate due to extreme resource saturation: M02 and M03 metrics show container CPU usage spiking from a near-zero baseline (base ~0.002) to a peak of 15.2, with z-scores of 999. This is corroborated by L logs showing 'ERROR' events for entity 68063 during the same interval. While Node 1420 shows memory pressure (M96 system.mem.used rising to 21.8k), it lacks the specific error evidence and magnitude of deviation seen in 68063. Service 177 (pod 88873) shows latency degradation in traces but no corresponding resource exhaustion or error logs, suggesting it may be a victim of downstream issues rather than the origin. The topology confirms 68063 is a callee in the call graph, consistent with a failure that impacts upstream services.", "confidence": "medium"}
```

## INC-2833D299D245 / aiops2022 / reused=True
RR 0.0 -> 0.0; joint=0
Accepted (private): ['recommendationservice-0']

```json
{"services": ["3419", "5355", "7150", "9104", "62419"], "reason": "Node 3419 is the leading root cause, exhibiting a sustained and severe drop in system.mem.free (M363) from ~3.58k to ~2.91k alongside a sharp increase in network traffic (M03/M04), which temporally aligns with the earliest anomaly onset. Node 5355 follows as a strong secondary candidate, showing a massive spike in memory usage (M01/M06) that correlates with increased load (M72). Nodes 7150 and 9104 display concurrent resource anomalies (CPU/memory/network) consistent with propagation or co-occurring faults. Pod 62419 is ranked lower; while it shows a network receive spike (M07), this is likely a downstream symptom of the node-level resource exhaustion affecting its service (969).", "confidence": "medium"}
```

## INC-35164E740447 / aiops2022 / reused=False
RR 1.0 -> 1.0; joint=1
Accepted (private): ['node-4']

```json
{"services": ["2078", "38624", "1550", "2209", "4666"], "reason": "Node 2078 is the leading root cause candidate because it exhibits a sharp, sustained spike in system.mem.pct_usage (M43) and an increase in system.load.1 (M450) that temporally precedes or coincides with the onset of service-level anomalies. The topology indicates that Pod 38624 (a member of Service 760) calls into downstream services; traces for 38624 show massive latency degradation (e.g., GetSupportedCurrencies p95 from 2.38ms to 56.6kms) and count drops, which are consistent with resource exhaustion on its host node. While Node 1550 also shows memory pressure, the specific correlation between the load spike on 2078 and the severe latency failures in the call chain originating from 38624 makes 2078 the most probable initiating infrastructure fault.", "confidence": "medium"}
```

## INC-C88979DF4D19 / aiops2022 / reused=False
RR 1.0 -> 1.0; joint=2
Accepted (private): ['checkoutservice']

```json
{"services": ["37956", "38128", "73449", "236", "39565"], "reason": "Pods 37956, 38128, and 73449 exhibit the most significant temporal anomalies, with metrics (M05-M08) showing sharp spikes in request duration and traces indicating a massive increase in exclusive p95 latency (approx. 8.6x) during the incident window. The topology places these pods downstream of service 51750; while 51750 is not a public candidate, its associated pod 51750 is also absent from the candidate list, leaving the observed latency degradation on the 858-group pods as the primary visible fault. Service 236 is ranked lower due to a minor thread spike (M01) that appears concurrent with, rather than preceding, the latency explosion in the other pods.", "confidence": "medium"}
```

## INC-E1E599C9691A / aiops2022 / reused=False
RR 0.0 -> 0.0; joint=2
Accepted (private): ['recommendationservice']

```json
{"services": ["363", "761", "2144", "8386", "22728"], "reason": "Service 363 is the leading hypothesis because it exhibits a sustained, high-magnitude deviation in JVM classes loaded (M04) from a near-zero baseline, with an onset at +0.3 minutes that precedes other major anomalies. This specific resource exhaustion pattern correlates temporally with elevated memory usage on Node 2144 (M295/M796), suggesting a causal link between service behavior and node load. Service 761 shows concurrent memory pressure (M01/M02/M03) but lacks the distinct 'class loading' spike seen in 363, making it a plausible secondary contributor or co-affected component rather than the primary initiator. Node 2144 and Node 8386 are ranked as physical infrastructure candidates due to significant CPU and memory metric spikes, though their correlation with Service 363 suggests they may be victims of the service-level fault rather than independent root causes. Pod 22728 is included as a lower-ranked alternative given its presence in the topology and potential association with Service 363's pods, although direct evidence linking its specific pod-level metrics to the incident is less definitive than the service-wide JVM data.", "confidence": "medium"}
```

## INC-AEB63063B99C / aiops2022 / reused=False
RR 1.0 -> 0.25; joint=1
Accepted (private): ['frontend']

```json
{"services": ["8377", "4046", "50743", "25855", "98023"], "reason": "Node 8377 is the leading root cause due to a synchronized, step-change degradation in multiple distinct I/O metrics (system.io.avg_dq_sz, system.io.await, system.io.r_await, system.io.r_s, system.io.rkb_s) and memory pressure (system.mem.real.pct_usage), all showing large z-scores and coinciding with the incident window. This infrastructure-level resource exhaustion explains the downstream latency increases observed in pods hosted on or affected by this node (e.g., Pod 50743 shows network receive spikes; Pods 13347 and 98023 show increased exclusive latency for SendOrderConfirmation). Node 4046 is ranked second due to concurrent CPU and memory usage anomalies that may contribute to cluster-wide instability or represent a correlated secondary failure. The other candidates are lower-ranked alternatives where symptoms (latency/errors) are present but lack the primary resource saturation evidence seen on 8377.", "confidence": "high"}
```

## INC-877AD157CB24 / aiops2022 / reused=False
RR 0.0 -> 0.0; joint=2
Accepted (private): ['node-5']

```json
{"services": ["64331", "73701", "81028", "68380", "191"], "reason": "The incident is initiated by a network failure in pod 64331, evidenced by logs LT254 and LT253 reporting gRPC 'no such host' and 'i/o timeout' errors during the earliest anomaly window (onset 0.3 min). This local fault propagates to caller service 73701, which exhibits a significant drop in request count (42 -> 11) and increased exclusive latency (4.56 ms -> 26.5 ms), indicating it is being delayed or failing due to the unavailable callee. The topology graph confirms a direct call edge from 73701 to 64331. Pod 81028 also shows a network receive spike and latency increase, likely as a secondary effect of the same network instability or shared infrastructure issue affecting the 191 service group.", "confidence": "medium"}
```

## INC-492AFB4CE9D6 / aiops2025 / reused=False
RR 0.2 -> 0.3333333333333333; joint=1
Accepted (private): ['checkoutservice', 'cartservice']

```json
{"services": ["4441", "233", "751", "868", "545"], "reason": "Node 4441 is the leading hypothesis due to the earliest anomaly onset (22.3 min) and a high z-score of 17.5 for node_cpu_usage_rate, indicating a significant deviation from its baseline. This resource pressure likely propagated through the service topology; Service 233 shows a massive z-score of 153 on block_cache_size, and its trace metrics show increased latency in operations like GetCart (owner 751) and Convert (owner 868). The co-occurrence of node-level CPU spikes with service-level cache and latency anomalies suggests an infrastructure-originated incident affecting dependent services.", "confidence": "medium"}
```

## INC-C6AD1614BF41 / aiops2025 / reused=False
RR 0.3333333333333333 -> 0.25; joint=1
Accepted (private): ['checkoutservice', 'paymentservice']

```json
{"services": ["15391", "84506", "14361", "767", "3809"], "reason": "Pod 15391 is the leading root cause candidate due to extreme metric anomalies: M07 (rtr) shows a massive spike from a base of ~8.04k to a peak of 429k (z=608), and M03 (rtr_max) spikes from ~132k to 20M (z=999). These are supported by log evidence for entity 84506 (LT736), which shows an error rate increase from 0.82 to 2.34, and entity 14361 (LT736) with an error rate increase from 1.05 to 2.34. The topology groups service 852 with pods 14361, 15391, and 84506, linking these entities. Service 767 is ranked lower as its trace data shows a latency increase (121ms to 4.08k ms) but a significant drop in request count (198 to 17), suggesting it may be a victim or secondary effect rather than the primary origin, although it is the caller in the graph. Node 3809 is included as a lower-ranked alternative due to memory usage anomalies (M21 z=-11.4) coinciding with the incident window, though the specific causal link to the pod failures is not explicitly defined in the visible topology.", "confidence": "medium"}
```

## INC-56FC27993C6C / aiops2025 / reused=False
RR 1.0 -> 0.0; joint=1
Accepted (private): ['node-6']

```json
{"services": ["409", "86389", "135", "711", "212"], "reason": "The leading hypothesis is that service 409 is the root cause. This is supported by a massive spike in rtt_max for pod 86389 (a member of service 409) reaching ~76.3k from a baseline of ~7.5k, which is the most significant metric anomaly on the dashboard. The logs for entity 77833 (also a member of service 409) show an event rate drop and volume drop during the incident window, further implicating this service. While other services like 135 and 711 show increased latency in traces, the magnitude of the resource exhaustion (RTT) and log anomalies in service 409 makes it the most likely origin. The ranking includes members of service 409 and downstream/upstream services involved in the topology to account for propagation effects or alternative local faults not fully captured by the top-level metrics.", "confidence": "medium"}
```

## INC-D142F47FE539 / aiops2025 / reused=False
RR 1.0 -> 0.0; joint=1
Accepted (private): ['tidb-tikv', 'tidb-tikv-0']

```json
{"services": ["17272", "756", "18625", "956", "50064"], "reason": "Pod 17272 (a member of service 756) exhibits a severe, sustained spike in the rtt_max metric during the fault window, with values peaking at 28.7k against a baseline of 2.51k (z-score ~40). This is the most extreme resource anomaly visible on the dashboard and temporally aligns with the incident interval. Service 756 shows elevated trace counts and latency for the ShipOrder operation, consistent with degradation from its faulty pod. Pod 18625 (member of service 956) also displays a significant memory working-set increase (peak 536k vs base 4.29k), suggesting a secondary resource exhaustion event or correlated failure. The remaining candidates are ranked lower due to lack of comparable magnitude anomalies in their specific telemetry lanes.", "confidence": "medium"}
```

## INC-0917F17160F5 / aiops2025 / reused=True
RR 0.0 -> 0.0; joint=0
Accepted (private): ['tidb-tikv', 'tidb-tikv-0']

```json
{"services": ["3699", "1010", "1412", "52111", "66241"], "reason": "Node 3699 exhibits a distinct, multi-dimensional anomaly pattern that is absent in other nodes: node_disk_read_bytes_total spikes from a baseline of 0 to a peak of 352k (z=999), and node_disk_read_time_seconds_total spikes from 0 to 0.01s (z=999). These metrics indicate a sudden onset of I/O activity on a previously idle disk. While CPU and memory metrics for Node 3699 show minor fluctuations consistent with the global noise band, the zero-to-non-zero transition in disk metrics represents a unique deviation from its own baseline. This suggests a local infrastructure fault or an unmanaged process initiating heavy disk reads. Pods 52111 and 66241 show concurrent resource spikes (fs_reads and working_set) which are likely symptoms of the underlying node-level I/O pressure rather than independent root causes. Other nodes like 1010 and 1412 show only minor deviations within the general telemetry noise.", "confidence": "medium"}
```

## INC-2B399A2FAEB2 / aiops2025 / reused=False
RR 0.0 -> 0.0; joint=2
Accepted (private): ['tidb-tidb', 'tidb-tidb-0']

```json
{"services": ["23106", "851", "1836", "961", "458"], "reason": "The leading hypothesis is a fault in pod 23106 (service 851). The log evidence (LT991) explicitly identifies entity 23106 as the owner of a 'request error' pattern with a significant volume drop and an increase in error rate. This aligns with the topology, where service 851 is a downstream callee for services 405 and 961; latency increases observed in callers like 458 (exclusive p95 13.2ms -> 129k ms) are consistent with delays propagated from this failing downstream component. Node 1836 is ranked third due to a high z-score (56.5) on disk write time, which may indicate infrastructure stress or be a secondary effect, but lacks direct error logs. Services 961 and 458 are lower-ranked alternatives as they exhibit client errors and latency spikes, respectively, but their behavior is more plausibly explained by the failure of their dependency (851/23106) rather than being the initiating root cause themselves.", "confidence": "medium"}
```

## INC-CDE4651C6884 / aiops2025 / reused=False
RR 0.5 -> 0.5; joint=2
Accepted (private): ['frontend', 'adservice']

```json
{"services": ["1533", "49677", "82517", "8091", "83675"], "reason": "Node 1533 is the leading hypothesis as it presents the earliest estimated anomaly onset (18.3) with a significant negative z-score (-3.94) for CPU usage, indicating a deviation from its baseline prior to other components. This timing suggests it may be the initiating fault that propagates to downstream services like 330 and 619 shown in the topology. Pod 49677 is ranked second due to a high-magnitude z-score (-9.96) for filesystem reads, though its later onset (22.2) makes it less likely than 1533 to be the primary origin. Other candidates are included based on concurrent anomalies or trace latency increases but lack the temporal precedence of Node 1533.", "confidence": "medium"}
```

## INC-7BABC3F333B2 / aiops2025 / reused=True
RR 0.0 -> 0.0; joint=0
Accepted (private): ['tidb-tikv', 'tidb-tikv-0']

```json
{"services": ["293", "57503", "149", "244", "174"], "reason": "Service 293 and its member pod 57503 (linked via the NAME GROUPS strip) exhibit the strongest temporal correlation with the incident window, showing sharp spikes in client_error, error, and error_ratio metrics that align with the shaded anomalous interval. While node 149 displays a significant z-score for CPU usage, this is likely a result of a low baseline rather than an absolute failure state, making it a less probable root cause than the direct error signals from service 293. Service 244 shows increased latency but lacks the explicit error spikes seen in 293, suggesting it may be a downstream impact or concurrent symptom rather than the initiating fault. Service 174 shows minor trace changes and remains a plausible alternative due to its position in the call graph, though evidence for it as the primary origin is weaker.", "confidence": "medium"}
```

## INC-4DBB272354A5 / aiops2025 / reused=False
RR 1.0 -> 1.0; joint=1
Accepted (private): ['recommendationservice', 'productcatalogservice']

```json
{"services": ["337", "28096", "14520", "228", "334"], "reason": "Service 337 (ListRecommendations) exhibits the most severe latency degradation, with exclusive p95 latency increasing by a factor of ~9000 (Δlog2 13.2) to 60k ms and request volume dropping significantly. This extreme local delay is consistent with a resource exhaustion or blocking issue within the service. The incident appears to propagate upstream to Service 228 (ListProducts), which calls 337; Service 228 shows increased error rates (0 -> 2) and reduced throughput, likely due to timeouts from the slow dependency. Pod 28096 (a member of Service 455, not 337, but listed as a candidate) shows high rtt_max and server_error spikes in metrics, suggesting it may be experiencing similar stress or is part of a broader cluster-wide issue affecting multiple services. Node 14520 is included as a lower-ranked alternative because physical infrastructure issues can sometimes manifest as widespread latency, though specific node telemetry for this ID is not explicitly detailed in the provided view compared to the clear service-level anomalies.", "confidence": "medium"}
```

## INC-6CB61FBD3E4F / aiops2025 / reused=False
RR 1.0 -> 1.0; joint=1
Accepted (private): ['currencyservice']

```json
{"services": ["12223", "88974", "243", "2304", "59565"], "reason": "The primary evidence points to Pod 12223 (M05) exhibiting a massive, sustained spike in 'rtr' metrics (base ~1.2k, peak 3.86k, z=17.8) during the anomalous window. This aligns with Service 243's trace data (R), which shows a significant latency degradation for operations like Convert and GetSupportedCurrencies (e.g., p95 latency increasing from 5.38ms to 59.9ms). While Node 2304 (M165/M503) shows memory anomalies (z~3.65/1.83), these are less severe than the pod-level metric spikes. The topology indicates Service 243 is part of the affected cluster, but the specific telemetry owner 12223 provides the most direct correlation to the observed performance failure.", "confidence": "medium"}
```

## INC-CB91FA13504C / aiops2025 / reused=False
RR 0.25 -> 0.25; joint=1
Accepted (private): ['shippingservice']

```json
{"services": ["9135", "9384", "18962", "59167", "115"], "reason": "Node 9135 is the leading root cause candidate because it exhibits the earliest estimated anomaly onset (19.3 min) with a high z-score of 5.54, indicating a significant deviation from its baseline CPU usage prior to other components. This temporal precedence suggests that resource exhaustion or high load on Node 9135 initiated the incident, potentially propagating delays to dependent services like Service 115 (whose pod 18962 shows a later onset at 28.2 min). The alternative hypothesis that Pod 18962 or Service 115 is the origin is weaker due to their later onset times relative to Node 9135. While Node 9384 and Pod 59167 also show anomalies, their later onset (25.2 and 28.2 min respectively) places them downstream in the causal chain.", "confidence": "medium"}
```

## INC-6678662095B6 / aiops2025 / reused=False
RR 0.0 -> 0.0; joint=1
Accepted (private): ['node-6']

```json
{"services": ["235", "100", "245", "894", "737"], "reason": "The telemetry indicates a primary fault in service 235, evidenced by the 'SendOrderConfirmation' operation showing a significant drop in request count (85 to 35) and an increase in exclusive p95 latency (72.6 ms to 81.6 ms). This is temporally correlated with a high z-score anomaly in node 5437's disk write time metric (M04), which aligns with the estimated incident window. Service 100 is ranked second as a likely downstream impact, showing reduced traffic and slight latency increases in 'EmptyCart' and 'GetCart', consistent with being a caller of the impaired service 235. Service 245 is ranked third due to minor latency fluctuations in its own operations, while services 894 and 737 are included as lower-ranked alternatives given their position in the topology and lack of severe independent anomalies.", "confidence": "medium"}
```
