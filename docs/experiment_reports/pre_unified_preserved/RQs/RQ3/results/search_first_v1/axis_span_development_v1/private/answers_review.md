## INC-7CE00360E043 / aiops2022
RR 0.25 → 1.0; output 322; stop
Accepted (private): ['frontend']; numeric aliases: ['23887', '36845', '67607', '767']

```json
{"services": ["36845", "23887", "12867", "32225", "548"], "reason": "Pod 36845 is the leading root-cause candidate because it is the only entity with direct evidence of a failure mechanism: logs LT224 and LT223 show new errors (envoy config stream closed, failed to retrieve ads) and a significant drop in event rate (baseline 589 -> fault 182). This correlates with its trace metrics showing a massive increase in exclusive latency for operations like GetQuote (p95 2.13ms -> 826ms) and AddItem (2.26ms -> 197ms), indicating local processing delays rather than just propagation from downstream. Pod 23887 is ranked second as a caller of 36845; its metrics show increased request duration (M20, M21) which is consistent with being delayed by the faulty callee 36845. Pods 12867 and 32225 are ranked lower as other callees of 36845, potentially affected by the same load or issues but lacking specific error logs themselves. Service 548 is included as a plausible alternative given its metric anomalies (M04, M05) and grouping relationship, though the causal link to the specific pod-level faults is less direct.", "confidence": "medium"}
```

## INC-7404365412F6 / aiops2022
RR 0.0 → 0.3333333333333333; output 170; stop
Accepted (private): ['adservice2-0']; numeric aliases: ['69047']

```json
{"services": ["348", "8201", "69047", "97984", "556"], "reason": "The telemetry indicates a resource exhaustion event on service 348, evidenced by a sustained increase in committed virtual memory (M22) and peak thread counts (M15/M16). This is temporally correlated with network packet errors on node 8201 (M04/M05), suggesting an infrastructure-level bottleneck or failure. The resulting latency degradation propagates to dependent services, such as 97984, which shows increased exclusive p95 latency for the EmptyCart operation. Pod 69047 exhibits elevated request duration metrics, consistent with the service-wide impact.", "confidence": "medium"}
```

## INC-68411E6D69DA / aiops2022
RR 0.25 → 0.25; output 251; stop
Accepted (private): ['frontend']; numeric aliases: ['10441', '161', '64808', '70565']

```json
{"services": ["5367", "4251", "9163", "10441", "18725"], "reason": "Node 5367 exhibits a sustained, multi-metric resource anomaly starting before the incident window (b63), characterized by a sharp drop in disk free space (M08) and inode availability (M07) alongside a corresponding rise in usage metrics (M01-M06). This temporal precedence suggests an infrastructure-level failure. Node 4251 shows significant network segment spikes (M21/M24) that coincide with the onset of latency degradation in downstream services. The topology indicates that Service 435 (Pods 56836/93993) calls into Service 117 (Pod 18725); Pod 18725 is the earliest anomalous pod (onset 13.1 min) with increased receive traffic (M09), suggesting it is the first application-layer component to degrade, potentially due to the underlying node issues or upstream load from 56836.", "confidence": "medium"}
```

## INC-17616FF7AAD6 / aiops2022
RR 0.25 → 0.25; output 244; stop
Accepted (private): ['checkoutservice-0']; numeric aliases: ['76191']

```json
{"services": ["27832", "10085", "94717", "76191", "141"], "reason": "Pod 27832 is the leading hypothesis as it exhibits the earliest and most distinct resource anomaly in the metrics panel: a sharp, sustained spike in container_memory_failures (pgmajfault) from a baseline of 0 to a peak of 33. This memory pressure aligns temporally with latency degradation observed in its associated service operations (specifically hipstershop.195/PlaceOrder). While Service 141 shows a large z-score for java_lang_Memory_ObjectPendingFinalizationCount, the absolute change is minimal (0 to 0.167), suggesting a statistical artifact rather than exhaustion. Node 9071's disk usage increase appears to be a transient event that resolved before the incident window, making it an unlikely root cause. The latency spikes in pods 76191 and 94717 are likely downstream effects of the resource contention initiated by pod 27832.", "confidence": "medium"}
```

## INC-F5CD31F4DEE1 / aiops2022
RR 0.0 → 0.0; output 264; stop
Accepted (private): ['currencyservice-2']; numeric aliases: ['91905']

```json
{"services": ["918", "29295", "32588", "80139", "327"], "reason": "The telemetry indicates a latency and throughput degradation originating from the pods associated with service 918. Metrics M05 (pod 29295), M24 (pod 32588), and M12 (pod 80139) show significant spikes in `istio_request_duration` and network receive rates, aligning with the pale anomalous band. Traces confirm this with elevated exclusive p95 latencies for operations owned by these specific pods (e.g., 50845/hipstershop.185, 97947/hipstershop.182). The topology graph shows these pods as distinct endpoints in the call chain, but their simultaneous onset of high latency suggests a common underlying issue or a bottleneck at the service level. Service 327 is ranked lower as its metric (mrt) also spikes, but it appears to be a consumer or parallel component rather than the primary source of the network and request duration anomalies seen in the 918 group.", "confidence": "medium"}
```

## INC-33C7D3DB2A58 / aiops2022
RR 1.0 → 1.0; output 278; stop
Accepted (private): ['node-2']; numeric aliases: ['8144']

```json
{"services": ["8144", "26460", "97583", "22823", "11708"], "reason": "Node 8144 is the leading root-cause candidate due to severe resource exhaustion: system.io.avg_q_sz spiked from a baseline of 0.013 to a peak of 63.2 (z-score 999) and system.io.util rose from 0.647 to 50. This I/O saturation correlates temporally with a massive latency spike in pod 26460 (service 875), whose exclusive p95 latency increased by a factor of 64 (Δlog2 6.06). Pod 26460 is also identified as having the highest z-score anomaly onset (6.06) among the service pods, suggesting it is the specific instance most impacted by or responsible for the node's degradation. Pods 97583, 22823, and 11708 show minor latency increases and count drops consistent with downstream propagation from the primary fault at 8144/26460, but lack the magnitude of resource failure seen on the node itself.", "confidence": "high"}
```

## INC-CC8D92170500 / aiops2022
RR 1.0 → 1.0; output 236; stop
Accepted (private): ['node-3']; numeric aliases: ['1523']

```json
{"services": ["1523", "64649", "60245", "83855", "28327"], "reason": "Node 1523 is the leading root-cause hypothesis due to a significant and sustained CPU spike (system.cpu.pct_usage rising from ~2.7% to ~77.8%) that temporally precedes the latency degradation observed in downstream pods. The topology shows a call chain involving Pods 64649, 60245, and 83855; these pods exhibit increased exclusive p95 latency (e.g., Pod 64649 latency doubling) and are likely victims of resource contention or network delays originating from Node 1523. While Pod 28327 also shows high memory usage, its metrics do not show the same sharp temporal correlation with the onset of system-wide latency spikes as the node-level CPU anomaly does. The evidence supports a resource exhaustion scenario on the node impacting dependent services rather than an isolated application failure.", "confidence": "medium"}
```

## INC-C86F6E03B824 / aiops2022
RR 0.3333333333333333 → 0.0; output 272; stop
Accepted (private): ['productcatalogservice']; numeric aliases: ['12714', '35461', '45674', '504']

```json
{"services": ["109", "110", "342", "65159", "78926"], "reason": "Service 109 (pod 65159) is the most likely root cause because it exhibits the largest relative deviation in its own baseline: M03 shows jvm_threads_started spiking from a near-zero baseline (base 0, peak 1) to an absolute value of 1. This indicates a specific resource exhaustion or thread leak event within this pod. While Service 110 and 342 show concurrent anomalies in JVM metrics (M01/M02), their baselines are non-zero, making the relative impact less severe than 109's zero-baseline spike. The topology graph confirms that pod 65159 (service 109) is a direct upstream caller to pods 12714 and 35461 (service 504), which aligns with the trace data showing increased latency for those downstream services. The alternative hypothesis of a node-level failure (Node 4421) is less supported as its disk usage increase is a step-change rather than a continuous saturation correlated strictly with the service spikes.", "confidence": "medium"}
```

## INC-BAC5EBEE7F18 / aiops2022
RR 0.0 → 0.0; output 343; stop
Accepted (private): ['adservice-2']; numeric aliases: ['12322']

```json
{"services": ["185", "722", "61932", "901", "908"], "reason": "Service 185 is the leading root-cause candidate because it exhibits the earliest anomaly onset (0.3 min) and a severe, sustained degradation in JVM resource metrics: M02 (memory pool allocated) peaks at 214 with z=999, and multiple garbage collection series (M16-M21) show massive spikes (z>200) during the fault window. This temporal precedence and magnitude of local resource exhaustion strongly suggest Service 185 is the origin. The trace data for 89424 (a pod of service 901) shows an exclusive p95 latency increase from 4.29 to 500 ms, which is consistent with 89424 being delayed by its callee, Service 185, rather than failing independently. Pod 61932 (service 812) is ranked third due to significant increases in request duration and HTTP 500 errors (M11-M13), but these likely represent downstream impact or concurrent stress rather than the initiating event, given that 185's anomalies began earlier. Service 901 and Node 908 are lower-ranked alternatives; 901's latency spike is explained by its dependency on 185, and Node 908's CPU iowait spike (M18) is less temporally aligned with the primary software-level failures.", "confidence": "medium"}
```

## INC-00B104A6DB74 / aiops2022
RR 1.0 → 0.5; output 269; stop
Accepted (private): ['checkoutservice-2']; numeric aliases: ['69167']

```json
{"services": ["4994", "69167", "50483", "22393", "37209"], "reason": "Node 4994 is the leading hypothesis due to a sustained, high-magnitude increase in system.cpu.iowait (M23) from a near-zero baseline to a peak of 5.66 (z=293), which strongly suggests underlying disk I/O saturation causing resource contention. This aligns temporally with the onset times for pods 69167 and 50483. Pod 69167 shows severe secondary symptoms including CPU throttling (M02/M19) and memory faults (M08-M10), while pod 50483 exhibits latency degradation in its SendOrderConfirmation operation (R). Service 22393 (alias 697) is implicated by concurrent JVM memory spikes (M13-M14) on its own timeline, though no direct hosting link to node 4994 is visible in the topology graph. The ranking prioritizes the infrastructure signal (node) that best explains the correlated container-level resource exhaustion observed in the downstream pods.", "confidence": "medium"}
```

## INC-C0F62DB233F2 / aiops2022
RR 0.0 → 0.0; output 251; stop
Accepted (private): ['node-4']; numeric aliases: ['1267']

```json
{"services": ["26757", "12532", "28246", "34973", "91735"], "reason": "The telemetry indicates a systemic resource exhaustion incident centered on Node 7425, evidenced by sustained peaks in disk usage (M18) and inode counts (M02-M05). The top-ranked candidates are the pods hosted on this node (identified via NAME GROUPS as members of services 261, 280, 685, and 747), which exhibit correlated memory cache drops and network receive spikes. Pod 26757 is ranked highest due to its explicit appearance in the 'Earliest Anomaly Onset' list (rank 2, z=8.82), suggesting it was an early driver of the node-level pressure. Pods 12532, 28246, 34973, and 91735 are ranked next as they show similar anomalous metric profiles within the same fault window, consistent with shared infrastructure degradation rather than isolated application failures.", "confidence": "medium"}
```

## INC-F9112289109A / aiops2025
RR 0.0 → 0.0; output 288; stop
Accepted (private): ['emailservice']; numeric aliases: ['12220', '387', '78549', '82541']

```json
{"services": ["331", "2195", "4808", "677", "28736"], "reason": "Service 331 is the leading hypothesis because it exhibits a sharp, isolated spike in raft_propose_wait (M02) and a sustained rise in region_pending (M22) that aligns with the estimated anomalous interval. These metrics suggest a coordination or state-management bottleneck initiating the incident. Node 2195 is ranked second due to an increase in node_disk_written_bytes_total (M07), which could be a downstream effect of Service 331's pending operations or a concurrent infrastructure issue. Node 4808 is third, showing correlated increases in disk write time (M20) and total bytes (M23), suggesting potential storage latency contributing to the system-wide impact. Service 677 is fourth based on a slight uptick in uptime (M21), which is less specific but temporally consistent. Pod 28736 is fifth; while it shows network receive/transmit anomalies (M12-M15) and CPU spikes (M01), these are likely symptoms of the upstream service delays rather than the root cause, as no direct causal edge from the pod to the service-level fault is established in the topology.", "confidence": "medium"}
```

## INC-B324546FFC06 / aiops2025
RR 0.5 → 0.0; output 220; stop
Accepted (private): ['node-8']; numeric aliases: ['6421']

```json
{"services": ["346", "768", "24984", "19630", "21765"], "reason": "Service 346 is the upstream caller of Service 768 (per G topology) and exhibits a significant increase in disk write time (M03, peak 0.2s vs base 0.0107s). This local resource degradation at the root of the visible call chain likely caused latency propagation to its downstream dependency, Service 768. Service 768 shows elevated error rates (M14-M17) and increased client errors on its specific pod 24984 (M10-M13), consistent with being impacted by an upstream fault or internal stress. The absence of severe baseline deviations in the other leaf services (137, 637, 639, 702, 813) suggests they are secondary victims or unaffected.", "confidence": "medium"}
```

## INC-C76C22A65921 / aiops2025
RR 0.0 → 0.0; output 185; stop
Accepted (private): ['cartservice-1', 'cartservice']; numeric aliases: ['563', '69011', '70609', '86976']

```json
{"services": ["50211", "7920", "33444", "5653", "118"], "reason": "Pod 50211 (Service 118) is the leading root cause candidate because it exhibits a simultaneous, sharp spike in client_error and error_ratio metrics that aligns with the earliest anomaly onset (onset 18.2) recorded for Pod 7920. The temporal coincidence suggests a fault originating in or affecting this specific pod instance, which then propagates to Service 118's aggregate error rates. While Node 5653 shows an early filesystem usage signal, it lacks the immediate latency/error impact seen in the pods, making it a less likely primary trigger than the direct application-layer failures observed in 50211.", "confidence": "medium"}
```

## INC-CD9AAE6C9F71 / aiops2025
RR 1.0 → 0.2; output 262; stop
Accepted (private): ['node-3']; numeric aliases: ['4359']

```json
{"services": ["36575", "17633", "82462", "39759", "4359"], "reason": "The leading hypothesis is a resource exhaustion fault on pod 36575, which hosts service 765. The metrics show node 4359 (M06) experiencing a sharp CPU spike to ~95% and memory usage increasing from ~37% to ~45%, coinciding with the incident window. Concurrently, pods associated with services running on this infrastructure (including 36575, 17633, and 82462) exhibit significant latency spikes (z-scores > 10-15). Service 765 (pod 36575) shows an rtt peak of 1.44k vs a base of 212, indicating severe degradation. While the node-level resource strain suggests an infrastructural root cause, the specific telemetry anomalies are most strongly tied to the application layer entities listed in the candidate pool, with 36575 being the primary affected pod linked to the highest-latency service group.", "confidence": "medium"}
```

## INC-CAF8151C7C9C / aiops2025
RR 0.0 → 0.0; output 223; stop
Accepted (private): ['tidb-tikv', 'tidb-tikv-0']; numeric aliases: ['399']

```json
{"services": ["207", "24729", "37980", "61721", "560"], "reason": "Service 207 is the leading root cause candidate as its memory_usage metric (M06) shows a sustained step-change increase to ~737M, representing a significant resource consumption anomaly that aligns with the incident window. The topology graph indicates Service 560 calls Service 207, suggesting that resource exhaustion in 207 could propagate latency or errors upstream to 560 and its downstream dependencies (Pods 24729, 37980, 61721). These pods exhibit elevated error ratios (M08-M16), which are consistent with being affected by the upstream degradation rather than being independent origins. While Node 8875 shows disk activity changes, the direct correlation between 207's memory spike and the service-level failures makes it the most probable initiating fault.", "confidence": "medium"}
```

## INC-ECD8A1AFD496 / aiops2025
RR 1.0 → 1.0; output 278; stop
Accepted (private): ['adservice']; numeric aliases: ['122', '14187', '28199', '53466']

```json
{"services": ["14187", "92965", "855", "1322", "50767"], "reason": "The primary evidence points to Pod 14187 as the initiating fault. The Logs (L) panel explicitly identifies entity 14187 with a 'level unknown' status and messages indicating an agent failure ('Agent failed to start!') and a reflection exception, accompanied by a significant increase in error rates (0 -> 0.4). This is corroborated by Metrics (M), which show a sharp spike in disk I/O for Node 1322 (node_disk_read_bytes_total) coinciding with the incident window, suggesting resource contention or heavy load on the host. Service 855 exhibits elevated client_error metrics (M21, M22, M18) during the same interval, and Pod 92965 (a member of Service 855 per Topology G) shows corresponding spikes in client errors and latency (M19-M24). The causal chain likely begins with the failure or resource exhaustion at Pod 14187, propagating to its co-located resources or downstream services like 855/92965.", "confidence": "medium"}
```

## INC-17BB91ED69B2 / aiops2025
RR 0.0 → 0.0; output 242; stop
Accepted (private): ['node-7']; numeric aliases: ['9569']

```json
{"services": ["158", "238", "7014", "3863", "923"], "reason": "Service 158 is the leading hypothesis due to a distinct degradation in its operations (AddItem, EmptyCart) where exclusive p95 latency increased by ~15-8% while request counts rose, indicating local processing slowdown. This aligns with Service 238 (hosting Pod 85664), which shows a massive spike in rrt_max (z=10.8) and corresponding log activity for conversion requests, suggesting resource contention or heavy load. Node 7014 is ranked third as a plausible infrastructure contributor, exhibiting a sustained step-change increase in memory usage rate (from ~50% to higher levels) that could impact host performance. Node 3863 is included as an alternative due to disk read spikes, though less temporally correlated than 7014. Service 923 is lower-ranked; its trace latency increases are likely propagated from its dependency on Service 158 rather than originating locally.", "confidence": "medium"}
```

## INC-BF5E3D25D876 / aiops2025
RR 0.3333333333333333 → 0.25; output 280; stop
Accepted (private): ['checkoutservice-1', 'checkoutservice']; numeric aliases: ['342', '46678', '53569', '87970']

```json
{"services": ["351", "858", "411", "53569", "2450"], "reason": "Service 351 exhibits the strongest and most consistent deviation from baseline, with a z-score of 16.2 for snapshot_apply_count (M13) and 20.4 for write_wal_mbps (M09), both peaking sharply within the shaded anomaly interval. This suggests an internal processing or I/O bottleneck as the initiating root cause. Service 858 shows elevated rt_max (z=14.4) and trace latency increases (p95 1.46 -> 1.64ms), but these are likely secondary effects given its position in the call graph downstream of 351's potential impact on shared resources or upstream callers. Pod 53569 (part of service 342) shows high CPU usage (z=12.2) and network spikes, which could be a contributing factor or a separate concurrent issue, but lacks the direct correlation to the primary service-level anomalies seen in 351. Node 2450 shows stable filesystem metrics despite some memory fluctuations, making it less likely to be the primary source compared to the service-level behavioral changes.", "confidence": "medium"}
```

## INC-2522930091BF / aiops2025
RR 0.5 → 0.5; output 230; stop
Accepted (private): ['checkoutservice', 'paymentservice']; numeric aliases: ['19026', '22521', '33849', '39530', '60978', '80520', '844', '921']

```json
{"services": ["45473", "22521", "80520", "236", "921"], "reason": "Pod 45473 (service 614) is the leading root-cause candidate, showing a massive latency spike in M11 (rpt_max rising from ~101k to 60M) and new server errors (M12/M13) during the incident window. This aligns with the topology where service 614 calls service 844; consequently, service 844 exhibits elevated latency (M03/M04) and pod 22521 (service 844) shows high rpt_max (M01), suggesting downstream propagation of delay. Service 921 also shows increased latency (M23) as a downstream caller of 844. The evidence strongly supports a fault originating at or near pod 45473 causing cascading latency and errors through the call chain.", "confidence": "medium"}
```

## INC-209913B37F61 / aiops2025
RR 0.25 → 0.0; output 234; stop
Accepted (private): ['node-6']; numeric aliases: ['5669']

```json
{"services": ["9564", "34875", "47180", "49764", "945"], "reason": "The primary evidence points to Node 9564 as the initiating root cause. The 'Earliest Anomaly Onset' list in the topology card identifies 9564 with an onset at 19.3 minutes, which is earlier than other entities (e.g., Service 945 at 25.2 min). Correspondingly, metric M21 for NODE 9564 shows a significant spike in `node_disk_write_time_seconds_total` (z=6.52) within the anomalous window. This node-level storage latency likely propagated to Service 945, which exhibits concurrent anomalies in `raft_apply_wait`, `snapshot_apply_count`, and `write_wal_mbps`. While Service 945 shows high z-scores, its later onset suggests it is reacting to the underlying infrastructure issue on Node 9564 rather than originating the fault itself.", "confidence": "medium"}
```

## INC-09ED18E6FF30 / aiops2025
RR 0.0 → 1.0; output 251; stop
Accepted (private): ['emailservice']; numeric aliases: ['58504', '71843', '74209', '885']

```json
{"services": ["58504", "71843", "74209", "885", "138"], "reason": "Pod 58504 (a member of service 885) exhibits the most distinct and severe resource anomaly, with pod_cpu_usage spiking to a peak of 0.4 (z-score 14.2) and pod_processes increasing from a baseline of 1 to a peak of 12 (z-score 14.7) during the incident window. This is supported by trace data for service 885, which shows a significant increase in exclusive p95 latency for SendOrderConfirmation operations (from 1.15ms to 8.07ms). Pods 71843 and 74209 also show identical CPU/process spikes but are ranked lower due to their similar, non-differentiating telemetry profiles within the same service group. Service 138 is included as an alternative hypothesis because its associated logs (entity 66971) indicate a volume drop and background saving activity that could contribute to system load.", "confidence": "medium"}
```

## INC-819F72DDB48B / aiops2022
RR 1.0 → 1.0; output 208; stop
Accepted (private): ['checkoutservice']; numeric aliases: ['36644', '39185', '47933', '493']

```json
{"services": ["36644", "86248", "39185", "47933", "85810"], "reason": "Pod 36644 is the leading hypothesis as it hosts the earliest logged anomaly (LT224, bin 34) indicating a dial tcp i/o timeout to the jaeger-collector, which correlates with a significant increase in exclusive p95 latency for its operation (2.94 -> 11.4k ms). This local resource or network failure likely propagates to callers like pod 86248 and 39185, which also exhibit elevated latency and error rates within the same temporal window. While the topology shows these pods are interconnected, the specific 'i/o timeout' log on 36644 provides a distinct causal mechanism compared to the other pods where only generic request errors or latency spikes are observed.", "confidence": "medium"}
```

## INC-987C8AAB3A59 / aiops2025
RR 0.0 → 0.0; output 292; stop
Accepted (private): ['tidb-tidb', 'tidb-tidb-0']; numeric aliases: ['759']

```json
{"services": ["33118", "70044", "988", "292", "655"], "reason": "The leading hypothesis is that pod 33118 (and its sibling 70044) initiated the incident. The Logs section explicitly attributes error templates LT859 to entities 33118 and 70044, showing a jump from baseline 0 to fault rates of 46 and 29 respectively, with messages indicating 'connection refused' during product queries. This represents a hard failure signal. In contrast, the Metrics for service 988 (which calls 33118's service group via pod 17854) show increased RRT (M17) and client errors (M09/M10), but these are consistent with downstream propagation from the connection failures rather than an independent root cause. Traces for services 292, 359, 594, and 655 show negligible latency changes (Δlog2 < 0.1), suggesting they are not the source of the degradation. The specific 'connection refused' logs on pods 33118/70044 provide the strongest causal evidence for the origin of the connectivity issues affecting the upstream callers.", "confidence": "medium"}
```
