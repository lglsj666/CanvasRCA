## INC-7CE00360E043 / aiops2022
RR 0.25 → 0.3333333333333333; output 249; stop
Accepted (private): ['frontend']; numeric aliases: ['23887', '36845', '67607', '767']

```json
{"services": ["235", "548", "23887", "36845", "67607"], "reason": "Service 235 is the leading root cause candidate as it exhibits the earliest anomaly onset (0.3 minutes) and a massive z-score (999) for jvm_threads_started, indicating a severe, early-occurring resource exhaustion or thread leak. This temporal precedence aligns with the topology where service 548 (which groups pods 23887, 36845, and 67607) is a downstream callee. The high latency spikes in pods 23887 and 36845 (e.g., 345k ms duration) and the error logs in 36845 are consistent with a downstream impact of the upstream failure in 235, rather than independent origin faults, although the high z-scores in 548's metrics keep it as a strong alternative if 235's issue is a symptom of a shared node failure not visible in the graph.", "confidence": "medium"}
```

## INC-7404365412F6 / aiops2022
RR 0.0 → 0.3333333333333333; output 191; stop
Accepted (private): ['adservice2-0']; numeric aliases: ['69047']

```json
{"services": ["348", "8201", "69047", "97984", "519"], "reason": "The telemetry indicates a resource exhaustion event on service 348, evidenced by a sustained increase in committed virtual memory (M22) and peak thread counts (M15/M16) that persist beyond the initial anomaly window. This correlates with a significant latency spike on pod 69047 (M02, M14) and an onset of NullPointerExceptions in service 519 (LT766). While node 8201 shows a high z-score for network errors, the absolute values are low, suggesting a secondary impact or measurement artifact rather than the primary root cause. The service-level resource degradation on 348 is the most consistent and severe deviation from baseline.", "confidence": "medium"}
```

## INC-68411E6D69DA / aiops2022
RR 0.25 → 0.3333333333333333; output 218; stop
Accepted (private): ['frontend']; numeric aliases: ['10441', '161', '64808', '70565']

```json
{"services": ["5367", "4251", "10441", "18725", "19060"], "reason": "The telemetry indicates a primary infrastructure failure on node 5367, evidenced by a simultaneous, sharp drop in free disk space (M08) and inode availability (M07) that persists through the incident window. This resource exhaustion on the node correlates temporally with a significant increase in network traffic (tcp_in/out_segs) on node 4251, suggesting a potential network-level impact or related infrastructure stress. The observed latency spikes in service 435 (pods 18725, 19060) and the reduced request counts in service 469 (pod 10441) are consistent with downstream degradation or service instability caused by the underlying node-level resource constraints, although the specific causal path from node to service is not explicitly depicted in the topology graph.", "confidence": "medium"}
```

## INC-17616FF7AAD6 / aiops2022
RR 0.25 → 0.0; output 340; stop
Accepted (private): ['checkoutservice-0']; numeric aliases: ['76191']

```json
{"services": ["27832", "27045", "27975", "94717", "141"], "reason": "The incident is initiated by a resource exhaustion fault on pod 27832, which is evidenced by the 'container_memory_failures' metric (M06/M07) spiking from a baseline of 0 to 33 during the anomalous interval. This pod is a member of service 349, which also hosts pod 27045. The traces (R) show that pod 27045 (operation PlaceOrder) and pod 94717 (operation EmptyCart) experienced significant latency increases (e.g., 59.6ms to 725ms for GetCart) and count drops, consistent with the impact of a resource-starved peer (27832) or shared infrastructure. The topology (G) confirms that 27045 and 27832 are callers to 27975 and 94717, and the logs (L) show connection errors (LT243) for pod 27975, likely resulting from the upstream instability. Service 141 is ranked lower as its metrics (M02/M03) show a concurrent step-change in JVM classes loaded, which may be a secondary effect or a separate issue, but the memory failure on 27832 is the most direct indicator of a root-cause resource fault.", "confidence": "medium"}
```

## INC-F5CD31F4DEE1 / aiops2022
RR 0.0 → 0.0; output 274; stop
Accepted (private): ['currencyservice-2']; numeric aliases: ['91905']

```json
{"services": ["9189", "327", "29295", "32588", "80139"], "reason": "The root cause is attributed to Node 9189 due to a synchronized, multi-dimensional resource anomaly. Metrics M01-M17 show Node 9189 experiencing a simultaneous spike in disk usage (M02), inode exhaustion (M04), and memory pressure (M14/M17) during the anomalous interval. This coincides with a massive spike in network retransmissions (M21, z=140), indicating a network-layer bottleneck or I/O stall. This node-level failure aligns with the high latency observed in the traces for Service 327 (M10) and the specific pods 29295, 32588, and 80139 (M05, M24, M12), which likely reside on or depend on this node. The logs for entities 91905 and 91905 (LT918, LT746) report transport errors and connection closures, consistent with a node-level infrastructure failure propagating to service-level timeouts.", "confidence": "medium"}
```

## INC-33C7D3DB2A58 / aiops2022
RR 1.0 → 1.0; output 325; stop
Accepted (private): ['node-2']; numeric aliases: ['8144']

```json
{"services": ["8144", "1042", "26460", "22823", "11708"], "reason": "Node 8144 is the leading root cause due to a sustained, multi-metric resource exhaustion pattern visible in the M panel: disk free space dropped sharply (M19), disk usage spiked (M03), and inode usage rose (M06), while I/O metrics (M08, M09, M10) showed a massive step-change in queue size and wait times (z-scores near 999). This infrastructure-level degradation temporally aligns with the incident window. The G panel confirms that the affected services (11708, 22823) are grouped under service 713, and their trace latencies in the R panel (e.g., 11708 PlaceOrder) increased, consistent with downstream impact from the node's I/O bottleneck. Node 1042 is a secondary candidate as its metrics (M11-M16) also show step-changes, but the I/O saturation on 8144 is more severe and directly linked to the latency spikes in the service traces. Pods 26460 and 22823 are ranked lower as they are likely victims of the node-level resource contention rather than the origin of the fault, given their log and trace anomalies align with the infrastructure metrics' onset.", "confidence": "medium"}
```

## INC-CC8D92170500 / aiops2022
RR 1.0 → 1.0; output 274; stop
Accepted (private): ['node-3']; numeric aliases: ['1523']

```json
{"services": ["1523", "65290", "33795", "50007", "7010"], "reason": "The incident is initiated by a resource exhaustion on physical node 1523, which exhibits a sharp, sustained increase in CPU usage (M16, M09) and memory usage (M23, M24) that coincides with the start of the anomalous interval. This infrastructure-level degradation is the most plausible root cause, as it can explain the downstream symptoms observed in the pods and services. Pod 65290 (M10) shows a corresponding spike in memory usage, and the logs (L) for entities 65290 and 33795 (which are grouped under service 977) report 'failed to retrieve ads' errors, consistent with resource starvation. The traces (R) show increased latency for operations associated with pods 47630, 64478, and 59934, indicating performance degradation propagating from the underlying node issue. The co-occurrence of node-level resource spikes and pod-level errors/latency strongly suggests 1523 as the initiating fault.", "confidence": "medium"}
```

## INC-C86F6E03B824 / aiops2022
RR 0.3333333333333333 → 0.2; output 335; stop
Accepted (private): ['productcatalogservice']; numeric aliases: ['12714', '35461', '45674', '504']

```json
{"services": ["4421", "342", "110", "31760", "12714"], "reason": "The leading hypothesis is that Node 4421 is the root cause due to severe filesystem exhaustion. Metrics M09 through M14 show Node 4421's disk usage and inode metrics spiking to near-capacity levels (e.g., disk.used peaking at 3.97G vs base 3.1G) within the anomaly window. This physical resource exhaustion is a plausible initiator for the observed service degradation. Service 342 (M01, M02) and Service 110 (M03) show corresponding spikes in JVM thread and class loading metrics, suggesting they are under stress, potentially due to the underlying node's resource constraints. The trace data for Pod 12714 (Service 235) shows a significant latency increase (exclusive p95 from 5.37ms to 3.52k ms), which is consistent with the timeline of the node's resource spike. While the dashboard does not explicitly depict a hosting edge between Node 4421 and these services, the temporal correlation and the nature of the node-level resource failure make it the most likely initiating factor. Pod 31760 is included as a lower-ranked alternative due to its early onset in the anomaly list, though its specific metric (GC duration) is a less direct indicator of a root cause compared to the node's disk saturation.", "confidence": "medium"}
```

## INC-BAC5EBEE7F18 / aiops2022
RR 0.0 → 0.0; output 297; stop
Accepted (private): ['adservice-2']; numeric aliases: ['12322']

```json
{"services": ["185", "163", "212", "417", "722"], "reason": "Service 185 is the primary root cause, evidenced by a persistent, step-function increase in JVM memory metrics (M16, M20, M21, M01) starting at b32, indicating a memory leak or exhaustion. This correlates with a significant latency spike in the 'GetAds' operation (89424, 87361, 15520) where exclusive p95 latency increased by a factor of ~6.8 (Δlog2 6.86-6.89). Log LT2412 for entity 89424 (a pod of service 185) confirms 'failed to retrieve ads' with a 1.42x error rate increase. Service 163 (pod 50373) shows a secondary latency increase (Δlog2 1.51) in 'SendOrderConfirmation' and is a downstream dependency of 185 (edge 87361->50373), suggesting propagation or a correlated issue. Services 212 and 417 show no direct evidence of fault in the provided telemetry, ranking lower due to lack of anomaly.", "confidence": "medium"}
```

## INC-819F72DDB48B / aiops2022
RR 1.0 → 1.0; output 235; stop
Accepted (private): ['checkoutservice']; numeric aliases: ['36644', '39185', '47933', '493']

```json
{"services": ["36644", "39185", "47933", "85810", "493"], "reason": "Pod 36644 is the leading candidate as it exhibits the earliest anomaly onset (22.2) among the observed pods, accompanied by a log event (LT224) indicating a dial tcp i/o timeout to a collector. This suggests a local network or resource fault. Pods 39185, 47933, and 85810 show concurrent latency spikes (M10-M21) and elevated error rates (LT72), but their onset times are identical or later, and their exclusive latency increases in the trace panel (R) are consistent with downstream propagation from the initial 36644 fault rather than independent origin. The topology (G) confirms 36644 is a callee for 25103 and 86248, but the local log evidence makes it the most probable initiating source.", "confidence": "medium"}
```

## INC-00B104A6DB74 / aiops2022
RR 1.0 → 1.0; output 351; stop
Accepted (private): ['checkoutservice-2']; numeric aliases: ['69167']

```json
{"services": ["69167", "4994", "697", "50483", "37209"], "reason": "Pod 69167 is the leading root cause due to severe resource exhaustion and error generation. Metrics M02-M09 show significant spikes in CPU throttling and memory failures (pgfaults), with M15 indicating a massive jump in memory faults (base 660k -> peak 4.39M). Logs LT851 from entity 59463 (a member of service 350, which groups pod 59463, though 69167 is in service 474) show NullPointerExceptions, but the specific resource pressure on 69167 is the strongest signal. Traces R for 69167 show increased latency (3.15 -> 56.6 ms) and count. Node 4994 shows high iowait (M23, peak 5.66), which may be a contributing factor or a downstream effect of the I/O heavy pod. Service 697 shows memory pressure (M13-M14) but lacks the specific error logs and fault counters seen in the pod metrics. Pod 50483 and Service 37209 are ranked lower as they show latency increases and are upstream callers in the topology (G), suggesting they may be experiencing propagated delays rather than being the origin of the resource fault, although 50483 has its own latency anomalies in R.", "confidence": "medium"}
```

## INC-C0F62DB233F2 / aiops2022
RR 0.0 → 0.0; output 286; stop
Accepted (private): ['node-4']; numeric aliases: ['1267']

```json
{"services": ["7425", "685", "26067", "71003", "34973"], "reason": "The root cause is hypothesized to be Node 7425, which exhibits a sharp, sustained increase in system.net.bytes_sent (M10) and system.net.tcp.out_segs (M07) starting at the onset of the incident. This network saturation correlates temporally with a significant drop in container_memory_cache across multiple pods (12532, 26067, 26757, 28246, 34973, 52718, 66938, 71003), suggesting a system-wide resource contention or I/O bottleneck. The topology (G) indicates that Pod 96887 (Service 685) is a primary caller to these affected pods, and its traces (R) show increased latency and request counts, likely as a consequence of the downstream degradation caused by the node-level network issue. While Pod 71003 shows an early onset in the anomaly list, the broad impact on unrelated pods points to a shared infrastructure dependency (Node 7425) rather than a single pod failure.", "confidence": "medium"}
```

## INC-F9112289109A / aiops2025
RR 0.0 → 0.0; output 309; stop
Accepted (private): ['emailservice']; numeric aliases: ['12220', '387', '78549', '82541']

```json
{"services": ["331", "1358", "2195", "28736", "609"], "reason": "Service 331 is the leading hypothesis because it exhibits the earliest anomaly onset (27.3 min) and a significant increase in the 'region_pending' metric (M22), which is a strong indicator of a resource or queueing bottleneck. This service-level degradation temporally precedes or coincides with the onset of latency spikes in downstream pods (28736, 46669, 47382) and services (609), suggesting 331 is the origin of the propagation. Node 1358 is ranked second due to its early onset (27.3 min) and high z-score (5.01) on disk write metrics, which could be a co-occurring infrastructure stressor or a secondary effect of the service-level issue, but the direct correlation with the 'pending' queue in 331 makes 331 the more likely initiating fault. Node 2195 is a lower-ranked alternative due to a later onset (35.2 min). Pod 28736 and Service 609 are included as plausible contributors or early affected components given their latency deviations and grouping relationships, though their onsets are concurrent with the broader incident window rather than strictly preceding it.", "confidence": "medium"}
```

## INC-B324546FFC06 / aiops2025
RR 0.5 → 0.5; output 223; stop
Accepted (private): ['node-8']; numeric aliases: ['6421']

```json
{"services": ["3184", "6421", "4648", "768", "24984"], "reason": "The incident is initiated by physical infrastructure degradation on Node 3184, evidenced by a sustained spike in filesystem usage rate (M01) and disk write time (M03) within the anomalous interval. This local resource contention correlates temporally with a sharp increase in working set memory for Pod 24984 (M20), which is a member of Service 768. The resource pressure propagates to the application layer, causing a significant drop in request counts and a rise in client errors for Service 768 (M14-M17) and its downstream dependencies (Service 498, M04-M07). Node 6421 and 4648 are ranked lower as secondary infrastructure anomalies with similar but less severe filesystem and disk write time spikes that may contribute to the overall cluster instability.", "confidence": "medium"}
```

## INC-C76C22A65921 / aiops2025
RR 0.0 → 0.0; output 304; stop
Accepted (private): ['cartservice-1', 'cartservice']; numeric aliases: ['563', '69011', '70609', '86976']

```json
{"services": ["54912", "7920", "5653", "118", "50211"], "reason": "Pod 54912 (service 641) is the leading root-cause candidate because its exclusive latency (M16) shows a sharp, sustained increase from a 1.72k baseline to a 4.78k peak (z=9.12) precisely within the estimated anomalous interval, and it is listed as the earliest onset in the topology (18.2). This local latency spike likely propagated to the caller, Service 118, which exhibits a simultaneous, massive spike in client errors (M22, M23, M19) from a near-zero baseline. Node 5653 (ranked 3rd in onset) shows a sharp spike in filesystem usage (M01) to 68.2 (z=999), which could be a contributing infrastructure factor or a correlated symptom, but the direct service-level latency-to-error chain points to Pod 54912 as the initiating fault. Pod 7920 (service 306) is a lower-ranked alternative as it also shows significant latency increases (M15, M07) during the same window, potentially indicating a shared upstream issue or a secondary fault.", "confidence": "medium"}
```

## INC-CD9AAE6C9F71 / aiops2025
RR 1.0 → 1.0; output 411; stop
Accepted (private): ['node-3']; numeric aliases: ['4359']

```json
{"services": ["4359", "4070", "17633", "286", "507"], "reason": "The leading hypothesis is that physical infrastructure node 4359 is the root cause. This is supported by metrics M06 (node_cpu_usage_rate) showing a sharp increase from a baseline of 29.6 to a peak of 95, and M23 (node_memory_usage_rate) rising from 37.7 to 43.6 during the incident window. Concurrently, M14 (pod 17633 rrt) shows a latency spike (base 1.87k, peak 4.46k), and the topology graph (G) indicates that service 753 (which hosts pod 17633) is a downstream dependency of services 767 and 930, suggesting that resource exhaustion on node 4359 propagated latency to the application layer. Node 4070 is ranked second due to network packet drops (M03, M04) that coincide with the incident window, potentially contributing to the observed latency. Service 286 and 507 are lower-ranked alternatives based on their own latency and throughput metrics (M17, M18, M07) which show significant deviations, but lack the clear resource-exhaustion signal seen in node 4359. The logs (L) show a drop in event rate for entity 36575, which is a pod of service 765, but this is likely a symptom of the upstream latency rather than the cause. The uncertainty lies in the exact propagation path, as the topology graph does not explicitly show node-hosting relationships, but the temporal correlation of node 4359's resource spikes with the service latency spikes strongly suggests a causal link.", "confidence": "medium"}
```

## INC-CAF8151C7C9C / aiops2025
RR 0.0 → 0.0; output 296; stop
Accepted (private): ['tidb-tikv', 'tidb-tikv-0']; numeric aliases: ['399']

```json
{"services": ["207", "20843", "24729", "177", "560"], "reason": "Service 207 is the leading hypothesis because it is the only candidate showing a resource exhaustion signature (memory_usage dropping from a 1.44G baseline to 737M, z=-28.9) that temporally precedes the error spikes in the topology's downstream services. The topology (G) shows 560 calling 207; the failure of 207 likely propagates as latency/errors to 560 and its other callees (238, 684, 146). Pod 20843 (a member of service 684) and Pod 24729 (a member of service 284) are ranked next due to high error rates and log volume drops (new_errors +100) observed during the incident window. Service 177 is included due to a high z-score (999) on store_unhealth_count, though the absolute change (0 to 1) is minimal, suggesting a potential health-check flake or secondary effect rather than the primary resource fault. Service 560 is a likely propagation point as the caller of the failing 207.", "confidence": "medium"}
```

## INC-ECD8A1AFD496 / aiops2025
RR 1.0 → 1.0; output 289; stop
Accepted (private): ['adservice']; numeric aliases: ['122', '14187', '28199', '53466']

```json
{"services": ["14187", "122", "1322", "92965", "855"], "reason": "Pod 14187 is the primary root cause candidate, evidenced by explicit log entries (LT03, LT08) reporting 'Agent failed to start' and 'InvocationTargetException' with a non-zero error rate (0.4) and event rate (2) compared to a zero baseline. This local failure propagates to its parent service 122, which exhibits a sharp, synchronized spike in read (574k) and write (667) I/O metrics (M02, M03) during the same interval, suggesting a retry or crash-loop behavior. Node 1322 is a lower-ranked alternative or contributing factor, showing concurrent disk read/write spikes (M11, M14) and a decrease in available memory (M08), but its z-scores are lower and the specific error logs are localized to pod 14187. Pod 92965 and service 855 are ranked lower as they show client error spikes (M17-M20) that are temporally coincident with the 14187 failure, likely representing downstream impact rather than the initiating fault.", "confidence": "medium"}
```

## INC-17BB91ED69B2 / aiops2025
RR 0.0 → 0.0; output 367; stop
Accepted (private): ['node-7']; numeric aliases: ['9569']

```json
{"services": ["151", "1818", "202", "3863", "27699"], "reason": "Service 151 is the leading hypothesis because it is a source node in the topology (called by 510) and exhibits the earliest listed anomaly onset (31.2 min) with a high z-score (3.49) on its rtt_max metric (M21), which spikes sharply within the anomalous window. Node 1818 is a strong alternative root cause, showing a significant increase in memory usage (M19, z 9.72) and a corresponding drop in available memory (M18, z 9.72) at the same onset time; if Node 1818 hosts Service 151, this resource exhaustion would explain the latency. Service 202 shows a large z-score (67.6) for memory usage, but the absolute change is small (1.04G to 1.05G), suggesting it is likely a sensitive metric rather than a primary fault. Node 3863 shows filesystem anomalies (M07, M08) but with lower z-scores (4.07). Pod 27699 (member of Service 785) shows latency spikes, but Service 785 is a downstream callee of 510, making it less likely to be the origin than the upstream 151 or the infrastructure node 1818. The logs (L) show routine conversion requests for entity 85664, providing no error evidence to contradict the latency/resource hypothesis.", "confidence": "medium"}
```

## INC-BF5E3D25D876 / aiops2025
RR 0.3333333333333333 → 0.3333333333333333; output 276; stop
Accepted (private): ['checkoutservice-1', 'checkoutservice']; numeric aliases: ['342', '46678', '53569', '87970']

```json
{"services": ["351", "858", "53569", "93444", "85333"], "reason": "Service 351 is the leading root cause candidate because its metrics (M13 snapshot_apply_count, M09 write_wal_mbps) show the earliest and most significant anomalous deviations (z-scores 16.2 and 20.4) within the fault window, indicating a write-path or storage bottleneck. Service 858 is a strong alternative or downstream impact candidate, exhibiting a massive spike in rtt_max (z=14.4) and elevated CPU/network usage in its associated pods (53569, 93444, 85333). The topology shows 858 calling 511, but the metrics for 511 are stable, suggesting the delay originates in 858 or its upstream dependencies (351). The specific pods 53569, 93444, and 85333 are ranked lower as they are likely the specific instances experiencing the resource exhaustion or latency spikes caused by the service-level fault in 351 or 858.", "confidence": "medium"}
```

## INC-987C8AAB3A59 / aiops2025
RR 0.0 → 0.0; output 356; stop
Accepted (private): ['tidb-tidb', 'tidb-tidb-0']; numeric aliases: ['759']

```json
{"services": ["33118", "70044", "104", "988", "477"], "reason": "The leading hypothesis is that pod 33118 is the initiating root cause. This is supported by the logs (L), which show a new error pattern (LT859) for entity 33118 with a message 'failed to query product by id... connection refused' and a significant increase in error rate (0 to 46). The topology (G) shows that service 104 (which includes pods 33118 and 70044) is a downstream dependency of service 988. The traces (R) show increased latency and error counts for service 988, which is consistent with it being affected by a failure in its downstream dependency (service 104/pod 33118). The metrics (M) for pod 34258 (also in service 988) show increased RRT, further supporting the hypothesis that service 988 is experiencing issues due to downstream failures. The alternative explanation that service 988 is the root cause is less likely because the specific 'connection refused' error in the logs of pod 33118 points to a failure in that pod's ability to connect to a resource, rather than a general failure of service 988. The uncertainty lies in the exact resource that pod 33118 is failing to connect to, but the evidence strongly points to pod 33118 as the origin of the incident.", "confidence": "medium"}
```

## INC-2522930091BF / aiops2025
RR 0.5 → 0.2; output 234; stop
Accepted (private): ['checkoutservice', 'paymentservice']; numeric aliases: ['19026', '22521', '33849', '39530', '60978', '80520', '844', '921']

```json
{"services": ["45473", "74974", "77465", "614", "844"], "reason": "Pod 45473 (a member of service 614) is the leading candidate as it exhibits the strongest local resource anomaly: M20 shows a significant increase in pod_memory_working_set_bytes (peak 1.65M) and M11 shows elevated rtt_max. This local resource pressure is temporally aligned with the incident window. Service 614 (M14-M16) and downstream services 844 and 921 show correlated latency increases (M03, M23) and error spikes, consistent with a propagation from the 614 layer. The topology (614 -> 844) supports this causal direction. While the exact internal failure mechanism (e.g., memory leak vs. GC pause) is not explicitly logged, the resource metric deviation on 45473 provides the strongest initiating evidence among the candidates.", "confidence": "medium"}
```

## INC-209913B37F61 / aiops2025
RR 0.25 → 0.0; output 340; stop
Accepted (private): ['node-6']; numeric aliases: ['5669']

```json
{"services": ["9564", "945", "10719", "12813", "51512"], "reason": "The primary evidence points to Node 9564 as the initiating root cause. The 'Earliest Anomaly Onset' list in the topology card identifies 9564 with the earliest onset (19.3) and highest z-score (14.1) among the listed anomalies. Metrics M13 (node_memory_usage_rate) and M14 (node_memory_MemAvailable_bytes) for Node 9564 show a significant deviation in the anomalous interval (pale band), with M13 rising from a baseline of 66.4 to a peak of 68.5 and M14 dropping from 10.3G to 9.56G. This memory pressure on the node likely propagates to the services running on it. Service 945 (onset 25.2) shows corresponding anomalies in memory usage (M15) and raft/snapshot operations (M03, M05), which are often sensitive to underlying resource contention. The latency spikes in Pods 10719 (M18), 12813 (M10, M06), and 51512 (M11, M08) align temporally with the node anomaly and the service-level degradation, suggesting they are downstream effects of the resource exhaustion on Node 9564 rather than independent faults.", "confidence": "medium"}
```

## INC-09ED18E6FF30 / aiops2025
RR 0.0 → 0.2; output 230; stop
Accepted (private): ['emailservice']; numeric aliases: ['58504', '71843', '74209', '885']

```json
{"services": ["138", "66971", "1586", "754", "885"], "reason": "Service 138 (and its associated pod 66971) is the leading root-cause candidate because its logs (LT1375, LT1374) explicitly record a 'volume_drop' and 'Fork CoW' failure signals during the anomalous window, which aligns with the temporal onset of the incident. The topology shows service 138 calling 939, and the traces for 939 show a slight latency increase, consistent with a downstream impact from 138's resource issues. Other candidates like 1586 and 754 show metric anomalies (rt_max, write_wal) but lack the explicit error evidence found in 138's logs, making them secondary suspects or potential co-affected components. The evidence for 138 is strongest due to the direct correlation between log errors and the incident window.", "confidence": "medium"}
```
