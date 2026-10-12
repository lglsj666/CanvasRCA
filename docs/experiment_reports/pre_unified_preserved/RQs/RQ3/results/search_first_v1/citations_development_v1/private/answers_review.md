## INC-7CE00360E043 / aiops2022
RR 0.25 → 0.3333333333333333; output 273; stop
Accepted (private): ['frontend']; numeric aliases: ['23887', '36845', '67607', '767']

```json
{"services": ["235", "548", "23887", "36845", "67607"], "reason": "The telemetry indicates a resource exhaustion incident originating at Service 235, which propagates to downstream components. [EC01/M03] shows Service 235's jvm_threads_started metric spiking from a baseline of ~0 to a peak of 1.58k (z=999), representing a massive and anomalous increase in thread creation that is consistent with a thread leak or runaway process. This onset is the earliest recorded anomaly (onset 0.3) in [EC04]. The failure propagates via call edges to Pod 23887 and Pod 36845 (grouped under Service 548), as shown in [EC04/G]. Consequently, [EC01/M20-M23] show significant latency spikes for Pods 23887 and 36845, while [EC03/LT224] records new gRPC configuration stream errors ('transport: Error while dialing') for Entity 36845, confirming the degradation of the downstream service.", "confidence": "high"}
```

## INC-7404365412F6 / aiops2022
RR 0.0 → 0.25; output 274; stop
Accepted (private): ['adservice2-0']; numeric aliases: ['69047']

```json
{"services": ["348", "13083", "97984", "69047", "52208"], "reason": "The incident is initiated by a resource exhaustion fault in service 348. [EC01] displays synchronized, step-like increases in JVM memory (M22), peak thread counts (M15, M16), and started threads (M23) for owner SERVICE 348, with peaks reaching approximately 6.09G and 57.9 respectively against baselines of 4.79G and 39. This specific temporal pattern—memory growth preceding or coinciding with a spike in thread creation—is characteristic of a local application-level failure such as a leak or deadlock. The topology in [EC04] shows that pods associated with service 348 (e.g., 69047) are callees for upstream services like 13083 and 97984. Consequently, the latency spikes observed in [EC02] for operations on 13083 and 97984 are likely secondary effects of their dependency on the degraded service 348, rather than independent faults.", "confidence": "medium"}
```

## INC-68411E6D69DA / aiops2022
RR 0.25 → 0.25; output 284; stop
Accepted (private): ['frontend']; numeric aliases: ['10441', '161', '64808', '70565']

```json
{"services": ["5367", "4251", "9163", "10441", "18725"], "reason": "The root cause is attributed to physical node 5367 due to a sustained, multi-metric state change indicating severe resource exhaustion. In [EC01], multiple metrics for owner 5367 show simultaneous step-changes within the anomalous interval: system.disk.free drops from ~2.09G to 1.45G [EC01/M08], while system.fs.inodes.in_use increases from 1.01 to 1.17 [EC01/M04]. This coincides with network segment spikes on node 4251 (M21, M24) and I/O read spikes on node 9163 (M15), suggesting a cluster-wide infrastructure event or cascading pressure. The earliest anomaly onset in [EC04] is associated with entity 79279, but its z-score (3.13) is significantly lower than that of node 4251 (z=40.2). The magnitude and consistency of the disk/inode depletion on 5367 provide the strongest evidence for an initiating hardware-level fault.", "confidence": "medium"}
```

## INC-17616FF7AAD6 / aiops2022
RR 0.25 → 0.25; output 321; stop
Accepted (private): ['checkoutservice-0']; numeric aliases: ['76191']

```json
{"services": ["27832", "10085", "94717", "76191", "141"], "reason": "The incident is initiated by a resource exhaustion fault on Pod 27832, which then propagates latency to downstream services. [EC01/M06] shows Pod 27832's container_memory_failures spiking from a baseline of 0 to a peak of 33, and [EC01/M07] confirms this with a similar spike in hierarchy failures, indicating a local memory pressure event. This local failure correlates with a significant increase in exclusive latency for its operation 'PlaceOrder' shown in [EC02], where the p95 latency jumps from 3.09ms to 59.6ms (Δlog2 4.27). The topology [EC04] shows that 27832 calls 94717 and 76191; both of these downstream pods exhibit increased exclusive latencies ([EC02]) and their own memory failure spikes ([EC01/M04], [EC01/M05]), consistent with being impacted by the upstream stall or shared infrastructure issues. Node 9071 also shows disk usage anomalies [EC01/M12-M18], but the specific memory failure pattern on 27832 provides a more direct explanation for the service-level latency degradation.", "confidence": "medium"}
```

## INC-F5CD31F4DEE1 / aiops2022
RR 0.0 → 0.0; output 296; stop
Accepted (private): ['currencyservice-2']; numeric aliases: ['91905']

```json
{"services": ["9189", "327", "29295", "32588", "80139"], "reason": "The telemetry indicates a resource exhaustion event on physical infrastructure node 9189. [EC01] displays synchronized, high-magnitude anomalies across multiple storage and memory metrics for NODE 9189 during the incident window: system.disk.pct_usage [EC01/M07] rises from a base of 42.2 to a peak of 46.1 (z=568), while system.mem.used [EC01/M14] increases from 10.1k to 12.8k (z=327). These baseline deviations suggest a local hardware or kernel-level fault on the node rather than an application-specific issue. This is supported by trace data in [EC02], where hipstershop.185/PlaceOrder shows a significant increase in exclusive p95 latency (9.65 -> 974 ms), consistent with the performance degradation expected from disk I/O saturation on the underlying host. While the onset list identifies pod 29295 as having the earliest anomaly, its metric change (istio_request_duration) is more likely a downstream consequence of the node-level resource pressure observed on 9189.", "confidence": "medium"}
```

## INC-33C7D3DB2A58 / aiops2022
RR 1.0 → 1.0; output 338; stop
Accepted (private): ['node-2']; numeric aliases: ['8144']

```json
{"services": ["8144", "26460", "97583", "22823", "11708"], "reason": "The leading hypothesis is a physical infrastructure fault on node 8144, supported by sustained resource exhaustion and I/O degradation observed in [EC01]. Specifically, metrics M08 (system.io.avg_q_sz) and M09 (system.io.await) for NODE 8144 show significant spikes from near-zero baselines to peaks of 63.2 and 120 respectively during the anomalous interval, indicating severe disk contention or failure. This aligns with the topology in [EC04], where node 8144 is an underlying host for pods exhibiting high latency (e.g., 26460, 97583). The trace data in [EC02] confirms this impact: pod 26460 shows a massive increase in exclusive p95 latency (0.018ms -> 0.02ms is a small absolute change but a large relative one; however, 97583 shows 4.14 -> 27.8ms), which is consistent with I/O-bound delays propagating to service-level operations like 'getads' and 'SendOrderConfirmation'. While log errors appear in [EC03] for entities 48029 and 22823, these are likely downstream consequences of the resource starvation at the node level rather than independent software failures.", "confidence": "medium"}
```

## INC-CC8D92170500 / aiops2022
RR 1.0 → 1.0; output 237; stop
Accepted (private): ['node-3']; numeric aliases: ['1523']

```json
{"services": ["1523", "60245", "64649", "83855", "7010"], "reason": "The incident is initiated by a resource exhaustion on physical node 1523, which drives downstream latency. In [EC01], NODE 1523 shows a sharp increase in system.cpu.pct_usage (M16) and system.cpu.user (M09), peaking at 77.8% and 76.4% respectively within the fault window. This high CPU utilization correlates with the elevated exclusive p95 latencies observed in [EC02] for services hosted on or associated with this node, specifically POD 60245 (service 870) and POD 64649 (service 237). The topology in [EC04] indicates that these pods are part of the call graph where the latency spikes occur (SendOrderConfirmation), supporting the hypothesis that the node-level resource contention is the root cause propagating to service-level delays.", "confidence": "medium"}
```

## INC-C86F6E03B824 / aiops2022
RR 0.3333333333333333 → 0.25; output 224; stop
Accepted (private): ['productcatalogservice']; numeric aliases: ['12714', '35461', '45674', '504']

```json
{"services": ["4421", "342", "110", "12714", "80028"], "reason": "The initiating root cause is identified as Node 4421 based on a distinct, sustained resource anomaly that temporally precedes the service-level latency degradation. In [EC01], metrics M09 (system.disk.used) and M10 (system.fs.inodes.free) for NODE 4421 show significant deviations from baseline during the incident window, with disk usage rising toward capacity limits and free inodes dropping sharply. These infrastructure-level changes begin before the onset of high-latency traces observed in [EC02] for downstream services like Service 342 (Pod 12714), suggesting a propagation from the physical node to its hosted workloads. While Service 342 shows clear performance impact (increased p95 latency), its behavior is consistent with being a victim of the underlying node-level resource exhaustion rather than the primary origin.", "confidence": "medium"}
```

## INC-BAC5EBEE7F18 / aiops2022
RR 0.0 → 0.0; output 247; stop
Accepted (private): ['adservice-2']; numeric aliases: ['12322']

```json
{"services": ["185", "722", "61932", "901", "908"], "reason": "The leading hypothesis is that Service 185 is the root cause due to a distinct resource exhaustion pattern. [EC01] displays multiple memory metrics for owner SERVICE 185, specifically M01 (jvm_memory_pool_allocated) and M16 (java_lang_GarbageCollector_LastGcInfo), which show sustained, step-function increases from a stable baseline, unlike the transient spikes seen in other components. This persistent state change suggests a leak or capacity limit rather than a transient load event. While Pod 61932 (Service 812) shows elevated latency and error rates in traces and logs [EC03/LT2412], it appears downstream in the call graph relative to Service 185's operational scope, making it a likely victim of the upstream degradation rather than the origin. The distinction between the sustained resource growth of 185 and the reactive latency of 61932 supports 185 as the initiating fault.", "confidence": "medium"}
```

## INC-819F72DDB48B / aiops2022
RR 1.0 → 1.0; output 216; stop
Accepted (private): ['checkoutservice']; numeric aliases: ['36644', '39185', '47933', '493']

```json
{"services": ["36644", "86248", "25103", "39185", "47933"], "reason": "Pod 36644 is the most likely initiating fault, indicated by a 'dial tcp: i/o timeout' log event [EC03/LT224] and a sharp latency spike in its gRPC request duration metric [EC01/M07]. This local failure propagates to upstream callers, evidenced by increased exclusive p95 latency for pod 86248 calling service 493 (which includes 36644) [EC02/86248], and an increase in error rates for entity 86248 [EC03/LT72]. The topology [EC04] confirms that 86248 and 25103 are direct callers of 36644.", "confidence": "medium"}
```

## INC-00B104A6DB74 / aiops2022
RR 1.0 → 1.0; output 267; stop
Accepted (private): ['checkoutservice-2']; numeric aliases: ['69167']

```json
{"services": ["69167", "50483", "22393", "4994", "37209"], "reason": "Pod 69167 is the leading root cause, supported by [EC01] metrics showing a massive increase in container_memory_failcnt (M15) and memory_usage_MB (M20), which indicates severe local resource exhaustion. This is corroborated by [EC02] traces for 69167, where exclusive p95 latency for SendOrderConfirmation increased significantly (Δlog2 4.17), consistent with a process struggling under memory pressure. Pod 50483 is ranked second as it shows high z-scores for network receive metrics in [EC01] and elevated trace latency in [EC02], suggesting it may be affected by or contributing to the same incident. Node 4994 is included due to an iowait spike in [EC01/M23], though its absolute value remains low. Service 22393 and pod 37209 are lower-ranked alternatives based on their presence in the topology [EC04] and minor metric deviations.", "confidence": "medium"}
```

## INC-C0F62DB233F2 / aiops2022
RR 0.0 → 0.0; output 256; stop
Accepted (private): ['node-4']; numeric aliases: ['1267']

```json
{"services": ["7425", "685", "12532", "96887", "54323"], "reason": "The root cause is attributed to Node 7425 due to a synchronized, step-function degradation in core filesystem and network metrics. [EC01/M02] shows NODE 7425's system.fs.inodes.free dropping from a baseline of 3.01G to 3.00G (z -999), while [EC01/M01] shows system.disk.used increasing from 3.1G to 3.97G (z 119). These shifts occur simultaneously with network throughput spikes in [EC01/M10] (system.net.bytes_sent) and [EC01/M07] (system.net.tcp.out_segs). This physical infrastructure anomaly precedes the onset of latency increases observed in service 685 (pods 96887 and 54323) within [EC02], suggesting the node-level resource exhaustion or I/O bottleneck is the initiating fault propagating to dependent workloads.", "confidence": "medium"}
```

## INC-F9112289109A / aiops2025
RR 0.0 → 0.0; output 255; stop
Accepted (private): ['emailservice']; numeric aliases: ['12220', '387', '78549', '82541']

```json
{"services": ["331", "2089", "2195", "4808", "677"], "reason": "The telemetry indicates a systemic latency incident affecting multiple services (331, 609) and pods across the topology. Service 331 is identified as the leading candidate because its 'region_pending' metric [EC01/M22] shows a sustained upward trend from ~20k to ~27k, representing a significant departure from baseline that coincides with the global onset of RRT spikes in other components. This suggests a potential resource or queueing bottleneck within service 331 that may be propagating delays. The physical nodes 2089, 2195, and 4808 are ranked lower but remain plausible root causes due to concurrent increases in disk write metrics [EC01/M14, M07, M20], which could contribute to system-wide I/O contention. Service 677 is included as an alternative given its uptime metric anomaly [EC01/M21], though the specific causal link is less direct than the storage-related node metrics.", "confidence": "low"}
```

## INC-B324546FFC06 / aiops2025
RR 0.5 → 0.5; output 232; stop
Accepted (private): ['node-8']; numeric aliases: ['6421']

```json
{"services": ["3184", "6421", "768", "24984", "56747"], "reason": "The telemetry indicates a storage subsystem failure on physical node 3184 as the initiating root cause. [EC01/M01] shows NODE 3184's filesystem_usage_rate jumping from a stable baseline of 47.3 to a peak of 77.1, while [EC01/M03] shows its disk_write_time increasing from a near-zero baseline (0.0107) to a peak of 0.2 seconds. These resource exhaustion and I/O latency signals on the infrastructure layer precede or coincide with service-level symptoms in the topology. Service 768 and its associated pod 24984 show increased error rates [EC01/M14], which is consistent with downstream degradation caused by the underlying node fault, although no explicit hosting edge between 3184 and 768 is depicted in the provided graph.", "confidence": "medium"}
```

## INC-C76C22A65921 / aiops2025
RR 0.0 → 0.0; output 287; stop
Accepted (private): ['cartservice-1', 'cartservice']; numeric aliases: ['563', '69011', '70609', '86976']

```json
{"services": ["50211", "7920", "33444", "5653", "118"], "reason": "The telemetry indicates a latency and error spike centered on the fault window. The leading hypothesis is that Pod 50211 is the initiating root cause due to its direct manifestation of client errors (M20, M21) and elevated latency (M13). This is supported by [EC01/M20] showing a sharp increase in 'client_error' for owner POD 50211 from a baseline of 0 to a peak of 12 during the anomalous interval. Additionally, [EC01/M13] shows 'client_error_ratio' for POD 50211 rising significantly from a baseline of 0 to 2.49. While Service 118 also exhibits similar error patterns (M22, M23), the pod-level granularity of 50211 suggests it is the specific failing instance within that service group. Node 5653 is ranked lower as a potential infrastructure contributor given the filesystem usage anomaly observed in [EC01/M01], but the direct application-layer errors in 50211 provide stronger evidence of an originating software or resource exhaustion fault.", "confidence": "medium"}
```

## INC-CD9AAE6C9F71 / aiops2025
RR 1.0 → 1.0; output 209; stop
Accepted (private): ['node-3']; numeric aliases: ['4359']

```json
{"services": ["4359", "765", "17633", "82462", "36575"], "reason": "The telemetry indicates a resource exhaustion event on physical infrastructure node 4359. [EC01/M06] shows the node's CPU usage rate (node_cpu_usage_rate) spiking to a peak of 95, representing a significant deviation from its baseline of 29.6. Concurrently, [EC01/M24] records a drop in available memory (node_memory_MemAvailable_bytes) for the same node, with values falling below the 10G baseline. These host-level anomalies temporally align with latency spikes observed in service 765 [EC01/M13] and pod 17633 [EC01/M14], suggesting that the root cause is the underlying hardware capacity constraint rather than a specific application fault.", "confidence": "medium"}
```

## INC-CAF8151C7C9C / aiops2025
RR 0.0 → 0.0; output 252; stop
Accepted (private): ['tidb-tikv', 'tidb-tikv-0']; numeric aliases: ['399']

```json
{"services": ["20843", "61721", "24729", "560", "177"], "reason": "The telemetry indicates a localized resource exhaustion event on pod 20843. In [EC01], metric M19 (client_error_ratio) and M20 (error_ratio) for POD 20843 show a sharp, sustained increase to approximately 63.2% during the anomalous interval, a massive deviation from its baseline of 0. This is corroborated by [EC02] traces, where operation 684/GetProduct shows a significant drop in request count (15488 -> 552) and a large increase in exclusive p95 latency (14.7ms -> 40.4k ms), suggesting the service was overwhelmed or failing locally. While other pods like 61721 and 24729 also show error spikes in [EC01], the specific combination of high error ratio and extreme latency/count degradation in 20843 makes it the most likely initiating fault.", "confidence": "medium"}
```

## INC-ECD8A1AFD496 / aiops2025
RR 1.0 → 1.0; output 236; stop
Accepted (private): ['adservice']; numeric aliases: ['122', '14187', '28199', '53466']

```json
{"services": ["14187", "92965", "855", "28199", "30505"], "reason": "The telemetry identifies Pod 14187 as the initiating root cause. Logs [EC02/LT03] show Pod 14187 emitting 'Agent failed to start' and [EC02/LT08] showing an InvocationTargetException, representing a hard failure with a new error rate (baseline 0 -> fault 0.4). This local failure is supported by metrics in [EC01], where Service 855 (to which Pod 14187 belongs per G) exhibits client_error spikes [EC01/M21] and error_ratio increases [EC01/M18]. The co-occurring disk read/write anomalies on Node 1322 [EC01/M14, EC01/M11] are likely secondary symptoms or concurrent noise rather than the primary origin of the specific application-level exceptions observed at the pod level.", "confidence": "medium"}
```

## INC-17BB91ED69B2 / aiops2025
RR 0.0 → 0.0; output 275; stop
Accepted (private): ['node-7']; numeric aliases: ['9569']

```json
{"services": ["158", "202", "785", "923", "776"], "reason": "The telemetry indicates a resource exhaustion event on Service 202 (pod 21979) that propagated to downstream latency. [EC01/M09] shows SERVICE 202 memory_usage increasing from a baseline of ~1.04G to a peak of 1.05G, a significant departure from its stable baseline. This coincides with [EC01/M20] showing POD 21979 rrt_max spiking sharply during the anomalous interval. The topology in [EC04/G] identifies SERVICE 202 as an upstream caller to SERVICE 158 and SERVICE 785. Consistent with this propagation, [EC02/R] shows SERVICE 158 experiencing increased exclusive p95 latency (e.g., ShipOrder 49.8ms -> 61.7ms), while [EC01/M14] confirms SERVICE 785 rrt also spiked. The lack of corresponding node-level failures or error logs suggests the root cause is the memory/latency degradation within Service 202's specific pod instance.", "confidence": "medium"}
```

## INC-BF5E3D25D876 / aiops2025
RR 0.3333333333333333 → 0.0; output 239; stop
Accepted (private): ['checkoutservice-1', 'checkoutservice']; numeric aliases: ['342', '46678', '53569', '87970']

```json
{"services": ["351", "858", "2450", "4206", "9437"], "reason": "The telemetry indicates a resource exhaustion incident on Service 351. Metrics [EC01/M13] and [EC01/M09] show significant spikes in 'snapshot_apply_count' and 'write_wal_mbps' for Service 351, with the write rate peaking at 213 MB/s against a baseline of ~12.8 MB/s (z=20.4). These service-level I/O anomalies are temporally coincident with a sharp drop in available memory for Node 1609 [EC01/M11], which is not listed as a candidate but provides infrastructure context. While Service 858 shows elevated p95 latency [EC02] and Pod 53569 shows increased CPU usage [EC01/M23], these appear to be secondary effects or concurrent activity rather than the primary initiator given the specific write-heavy metrics on 351.", "confidence": "medium"}
```

## INC-987C8AAB3A59 / aiops2025
RR 0.0 → 0.0; output 209; stop
Accepted (private): ['tidb-tidb', 'tidb-tidb-0']; numeric aliases: ['759']

```json
{"services": ["33118", "70044", "988", "292", "655"], "reason": "The leading hypothesis is that Pod 33118 is the initiating root cause. This is supported by [EC03/LT859] which shows entity 33118 with a high error rate (baseline 0 -> fault 46) and 'connection refused' logs, indicating an active failure state. Additionally, [EC01/M15] shows Pod 34258 (a peer in service 988) experiencing latency spikes, suggesting a potential cluster-wide or network-level impact originating from the faulty pod's environment. While [EC01/M11] shows Pod 17854 also with elevated RRT, the specific error logs for 33118 provide more direct evidence of a fault than the latency metrics alone.", "confidence": "medium"}
```

## INC-2522930091BF / aiops2025
RR 0.5 → 0.3333333333333333; output 247; stop
Accepted (private): ['checkoutservice', 'paymentservice']; numeric aliases: ['19026', '22521', '33849', '39530', '60978', '80520', '844', '921']

```json
{"services": ["45473", "74974", "22521", "614", "844"], "reason": "The telemetry indicates a localized resource or processing fault on pod 45473. [EC01/M11] shows pod 45473's rrt_max metric spiking to a peak of 60M (base 180k), representing a massive deviation from its baseline compared to other pods like 74974 or 22521 which show smaller absolute increases. This local latency spike is supported by [EC03/LT1451], where entity 45473 reports an error rate increase from 0 to 1.93 and a volume drop, suggesting the pod was failing requests or throttling under stress. While service-level metrics for 614 and 844 also show anomalies in [EC01], the specific high-magnitude latency and error logs for 45473 make it the most likely initiating root cause within the 614 service group.", "confidence": "medium"}
```

## INC-209913B37F61 / aiops2025
RR 0.25 → 0.0; output 273; stop
Accepted (private): ['node-6']; numeric aliases: ['5669']

```json
{"services": ["9564", "10719", "34875", "47180", "51512"], "reason": "The leading hypothesis identifies Node 9564 as the initiating root cause due to a sustained, directional resource degradation pattern. [EC01/M13] shows node_memory_usage_rate for owner 9564 rising from a baseline of ~66.4% to a peak of 68.5% (z=14.1), while [EC01/M14] shows node_memory_MemAvailable_bytes for the same owner dropping from ~10.3G to 9.56G (z=-14). This concurrent increase in usage and decrease in free memory indicates genuine resource exhaustion on the host rather than a statistical artifact. The temporal onset at 19.3 minutes (per [EC04]) is earlier than the service-level anomalies (e.g., Service 945 at 25.2 min), supporting a bottom-up propagation model where the node's state impacts hosted services like 945 and their associated pods (34875, 47180, 51512).", "confidence": "medium"}
```

## INC-09ED18E6FF30 / aiops2025
RR 0.0 → 0.0; output 195; stop
Accepted (private): ['emailservice']; numeric aliases: ['58504', '71843', '74209', '885']

```json
{"services": ["9780", "66971", "30100", "5414", "2134"], "reason": "The leading hypothesis is that Node 9780 experienced a network resource fault. [EC01/M01] shows node_network_receive_bytes_total for owner NODE 9780 dropping from a baseline of 164 to a peak deviation of 160 (z -999), indicating a severe reduction in incoming traffic capacity or throughput. This aligns with [EC01/M02], which shows node_network_receive_packets_total for the same node dropping from 1.6 to 1.53 (z -999). The massive negative z-scores suggest a near-total loss of normal network behavior on this physical infrastructure node, likely causing downstream service degradation observed in other metrics.", "confidence": "high"}
```
