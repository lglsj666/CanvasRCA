## INC-7CE00360E043 / aiops2022
RR 0.25 → 0.0; output 273; stop
Accepted (private): ['frontend']; numeric aliases: ['23887', '36845', '67607', '767']

```json
{"services": ["235", "24865", "145", "21523", "548"], "reason": "Service 235 is the leading hypothesis as it appears first in the 'Earliest Anomaly Onset' list (onset 0.3 min, z=-1) and its metric M03 (jvm_threads_started) shows a distinct spike into the anomalous interval. This is supported by trace data for Service 767 (which includes Pod 24865), showing a massive latency increase for hipstershop.656/AddItem (exclusive p95 2.25 -> 12.8 ms). While Node 2948 (M39) shows a significant IO spike (z=488) concurrent with the incident, it is not listed in the candidate pool. The ranking prioritizes the earliest detected anomaly (235) followed by the specific pod exhibiting high-latency operations (24865) and its service group (145/21523). Uncertainty exists regarding whether the node-level IO issue is the root cause propagating to the services, but the explicit onset detection favors 235.", "confidence": "medium"}
```

## INC-7404365412F6 / aiops2022
RR 0.0 → 0.0; output 343; stop
Accepted (private): ['adservice2-0']; numeric aliases: ['69047']

```json
{"services": ["32737", "11518", "96813", "407", "348"], "reason": "Pod 32737 (service 274) is the leading root-cause candidate due to a massive latency spike in `istio_agent_go_gc_duration_seconds` (z=60.5, rising from ~9.8e-05s to 9.9e-05s), which indicates severe garbage collection pressure and CPU stalls. This aligns with the earliest onset time (0.3 min) recorded in the topology panel. Pod 11518 (service 911) is ranked second as it shows an increase in `istio_agent_go_memstats_frees` (z=10.5) at the same onset time, suggesting memory churn that may be related to or downstream of the GC issue. Pod 96813 (service 556) exhibits a high z-score for `container_memory_failures.container.pgfault` (z=95), indicating memory faults consistent with resource exhaustion. Service 407 (specifically pod 97984) shows significant exclusive latency increases in `EmptyCart` operations (p95 3.51 -> 38.3 ms), likely a consequence of the upstream slowness rather than the origin. Service 348 shows a sustained increase in thread count (z=328), which is a plausible secondary effect of request queuing caused by the primary latency issues.", "confidence": "medium"}
```

## INC-68411E6D69DA / aiops2022
RR 0.25 → 0.3333333333333333; output 265; stop
Accepted (private): ['frontend']; numeric aliases: ['10441', '161', '64808', '70565']

```json
{"services": ["33488", "10695", "10441", "79279", "13880"], "reason": "Pod 33488 is the most likely initiating fault, exhibiting a massive spike in istio_agent_go_memstats_gc_sys_bytes (M53) with a peak of 6.15M against a baseline of ~6.08M, coinciding with the earliest anomaly onset listed in G (0.3 min). This memory pressure correlates with network packet loss on Pod 10695 (M38, container_network_transmit_packets_eth0) and receive drops on Pod 10441 (M48), which are topologically downstream or related to the service groupings. The trace data for Service 297 (e.g., ShipOrder) shows increased latency (p95 2.79 -> 31.1 ms) but no error rate increase in logs, suggesting resource exhaustion rather than application logic failure. While Node 1907 shows TCP retransmissions, the specific pod-level memory spike makes 33488 the primary suspect for triggering the cascade.", "confidence": "medium"}
```

## INC-17616FF7AAD6 / aiops2022
RR 0.25 → 0.0; output 234; stop
Accepted (private): ['checkoutservice-0']; numeric aliases: ['76191']

```json
{"services": ["27975", "10085", "38553", "48361", "195"], "reason": "Pod 27975 is the leading candidate due to a direct causal link between infrastructure and application failure. Node 9071 (M12) shows free disk space dropping from ~1.49G to near zero, which correlates with Pod 27975 emitting 'StreamAggregatedResources gRPC config stream closed' errors (LT243) during the incident window. This suggests that disk exhaustion on the host node prevented the sidecar or service from maintaining its configuration stream, causing the observed latency degradation in Service 195's operations (EmptyCart/GetCart). While Pod 10085 exhibits an extreme z-score (-999) for GC duration, this is likely a secondary symptom of resource contention or a result of the broader system instability rather than the initiating fault, as it lacks the specific error logs found at 27975.", "confidence": "medium"}
```

## INC-F5CD31F4DEE1 / aiops2022
RR 0.0 → 0.0; output 237; stop
Accepted (private): ['currencyservice-2']; numeric aliases: ['91905']

```json
{"services": ["283", "941", "327", "2042", "5737"], "reason": "Service 283 is the leading hypothesis due to a sustained increase in Java compilation time (M76, base 38.9k -> peak 40.7k) that persists through and beyond the anomalous window. This aligns with the 'earliest anomaly onset' recorded for entity 283 in the G card. The resulting CPU pressure is consistent with Service 941's increase in system CPU load (M143, z=6.91). While Node 2042 shows a memory usage spike (M58), it drops sharply at the end of the interval, suggesting a transient state or recovery rather than a persistent root cause like the compilation lag on 283. Service 327 shows a significant mrt spike (M10, z=5.59), but its temporal alignment suggests it may be a downstream effect or concurrent symptom rather than the initiating fault.", "confidence": "medium"}
```

## INC-33C7D3DB2A58 / aiops2022
RR 1.0 → 0.0; output 254; stop
Accepted (private): ['node-2']; numeric aliases: ['8144']

```json
{"services": ["49402", "59738", "875", "908", "68081"], "reason": "Pod 49402 is the leading candidate as it exhibits the earliest anomaly onset (0.3 min) and the most extreme metric deviation (z=-50.7 for M27 istio_agent_go_memstats_alloc_bytes), indicating a severe memory allocation drop that likely triggered the incident. Pod 59738 follows with an identical onset time but a much smaller z-score (-3.46). Service 875 shows a minor deviation (z=-1) at the same onset, while Service 908 also has a z=-1 deviation at the same time; both are less severe than the pod-level anomalies. Pod 68081 is ranked lower due to its moderate memory fault signal (M122 container_file_descriptors) without the extreme statistical deviation seen in 49402. The evidence strongly points to a resource exhaustion or failure event originating in Pod 49402's memory subsystem, propagating to related services and pods.", "confidence": "medium"}
```

## INC-CC8D92170500 / aiops2022
RR 1.0 → 0.0; output 246; stop
Accepted (private): ['node-3']; numeric aliases: ['1523']

```json
{"services": ["22556", "47755", "930", "129", "949"], "reason": "Pod 22556 is the leading root cause candidate, exhibiting the earliest anomaly onset (0.3 min) and the highest source-specific z-score (17.5) for istio_agent_go_memstats_gc_cpu_fraction, indicating a significant deviation in CPU/GC behavior. This is supported by its association with Service 521, which shows elevated latency in trace 47630 (p95 3.61 -> 24.3 ms). Pod 47755 follows as a secondary candidate with an early onset (0.3 min) and moderate z-score (4.31) for open file descriptors, potentially correlating with resource exhaustion or high load. The remaining candidates (Service 930, Service 129, Service 949) are ranked lower due to negative z-scores (-1), suggesting their anomalies are within normal variance or represent different types of fluctuations rather than the primary fault origin.", "confidence": "medium"}
```

## INC-C86F6E03B824 / aiops2022
RR 0.3333333333333333 → 0.0; output 204; stop
Accepted (private): ['productcatalogservice']; numeric aliases: ['12714', '35461', '45674', '504']

```json
{"services": ["27768", "110", "342", "62928", "31760"], "reason": "Pod 27768 is the central caller in the topology (G) for operations showing a consistent ~10x increase in exclusive p95 latency (R), indicating local processing delays that propagate to callees. This hypothesis is supported by metric M142 (container_sockets) on pod 27768, which shows a significant spike coinciding with the incident window. The other candidates are ranked lower: service 110 and 342 show early onset anomalies in metrics (M03, M01) but lack direct causal links or comparable magnitude of impact; pods 62928 and 31760 appear in the onset list but have less distinct supporting evidence than 27768.", "confidence": "medium"}
```

## INC-BAC5EBEE7F18 / aiops2022
RR 0.0 → 1.0; output 307; stop
Accepted (private): ['adservice-2']; numeric aliases: ['12322']

```json
{"services": ["12322", "185", "14226", "79898", "1104"], "reason": "The leading hypothesis is that pod 12322 (member of service 185) is the root cause due to a specific, high-magnitude resource fault: container file descriptors dropped from a baseline of 24 to 21 (M45), while simultaneously exhibiting a massive spike in istio_request_duration (M82, base 187 -> peak 12k ms). This local latency explosion is corroborated by trace data for pod 14226 (a caller in the topology) showing exclusive p95 latency increasing from 4.29ms to 500ms, and log LT17 for pod 12322 reporting 'max duration timeout' errors with an error rate jumping from 0 to 7.55. Service 185 is ranked second as the logical owner of the faulty pod 12322. Pod 14226 is ranked third as it shows severe downstream latency degradation consistent with being blocked by the faulty callee. Pod 79898 and Node 1104 are lower-ranked alternatives; Node 1104 shows CPU spikes but lacks the specific application-layer error signatures seen in 12322.", "confidence": "medium"}
```

## INC-819F72DDB48B / aiops2022
RR 1.0 → 1.0; output 248; stop
Accepted (private): ['checkoutservice']; numeric aliases: ['36644', '39185', '47933', '493']

```json
{"services": ["36644", "75248", "29079", "89168", "13140"], "reason": "Pod 36644 is the most likely initiating fault. The topology graph (G) shows 36644 as a caller to all other anomalous pods (75248, 29079, 89168), while no reverse edges are depicted. Log evidence (L) for 36644 explicitly reports 'dial tcp: i/o timeout' when calling the Jaeger collector, indicating a network or connectivity failure that would delay its operations. This local latency and error generation align with the increased exclusive p95 latencies observed in the traces (R) for its downstream targets (e.g., 75248 and 89168 show significant Δlog2 increases). The anomaly onset for 36644 is early in the recording window (onset 0.3 min), supporting its role as the origin of the incident's propagation through the call chain.", "confidence": "medium"}
```

## INC-00B104A6DB74 / aiops2022
RR 1.0 → 0.0; output 231; stop
Accepted (private): ['checkoutservice-2']; numeric aliases: ['69167']

```json
{"services": ["350", "474", "61506", "29341", "85031"], "reason": "The telemetry indicates a latency and resource degradation incident centered on the service 350 cluster. Metrics for pods 59463, 34048, and 50483 (all mapped to service 350 via NAME GROUPS) show synchronized anomalies during the fault window: significant spikes in container memory faults (pgfaults) and CPU throttling (cfs_throttled_seconds), alongside elevated network retransmissions on node 4994. Trace data confirms high exclusive latency increases for operations within this cluster (e.g., hipstershop.693/SendOrderConfirmation). While pod 61506 (service 675) shows 'failed to retrieve ads' logs, its metric baselines are stable, suggesting it is a downstream victim of the latency propagation from the 350 cluster rather than the initiating root cause.", "confidence": "medium"}
```

## INC-C0F62DB233F2 / aiops2022
RR 0.0 → 1.0; output 195; stop
Accepted (private): ['node-4']; numeric aliases: ['1267']

```json
{"services": ["1267", "4821", "14604", "29214", "34973"], "reason": "Node 1267 exhibits the most significant resource exhaustion, with system.cpu.user spiking to 35.4% (z=58.7) and a sharp drop in free memory (M02). This temporal alignment with the incident window strongly suggests a hardware-level bottleneck. Pod 14604 is ranked second as it hosts Service 280, which shows elevated request latency (M67) consistent with the node's CPU pressure. Pods 29214 and 34973 are included as lower-ranked alternatives due to their high event counts in logs (L), though they lack the primary resource-exhaustion signals seen on Node 1267.", "confidence": "medium"}
```

## INC-F9112289109A / aiops2025
RR 0.0 → 0.0; output 222; stop
Accepted (private): ['emailservice']; numeric aliases: ['12220', '387', '78549', '82541']

```json
{"services": ["331", "677", "423", "478", "669"], "reason": "Service 331 is the leading hypothesis due to the earliest listed anomaly onset (t=27.3) with a high z-score of 5.01 for raft_propose_wait, indicating a fundamental coordination failure that aligns temporally with the incident window. Service 677 follows closely in time (onset t=27.3) with a significant timeout spike (z=5.3), suggesting it may be a primary victim or co-fault within the same cluster as 331. Services 423 (CPU usage) and 478 (error_ratio) show anomalies at the same timestamp but lack the specific operational indicators (like timeouts or consensus waits) that point to an initiating root cause. Service 669 shows a client_error_ratio spike, which is typically a downstream symptom of the latency or errors originating from the upstream services.", "confidence": "medium"}
```

## INC-B324546FFC06 / aiops2025
RR 0.5 → 0.0; output 257; stop
Accepted (private): ['node-8']; numeric aliases: ['6421']

```json
{"services": ["3184", "3220", "56747", "274", "969"], "reason": "The leading hypothesis is that Node 3184 is the initiating root cause due to a sustained, step-like increase in node_filesystem_usage_rate from a baseline of 47.3% to a peak of 47.3% (likely a display truncation or near-ceiling value) during the incident window. This resource exhaustion on the physical infrastructure is consistent with the observed drop in event rates for Pod 56747 (associated with Service 566), which experienced a volume_drop_x30:0.58 and reduced event rate (0.961 -> 0.556). The temporal alignment between the filesystem spike on Node 3184 and the service degradation suggests a causal link where storage pressure led to logging or operational failures. While Node 3220 also shows an increase in memory usage, it lacks the direct evidence of failure seen in the logs associated with the other cluster. Other candidates are ranked lower based on weaker or absent direct correlation with the primary telemetry anomalies.", "confidence": "medium"}
```

## INC-C76C22A65921 / aiops2025
RR 0.0 → 0.0; output 232; stop
Accepted (private): ['cartservice-1', 'cartservice']; numeric aliases: ['563', '69011', '70609', '86976']

```json
{"services": ["7920", "5653", "118", "4074", "812"], "reason": "The top-ranked hypothesis is that Node 7920 is the initiating root cause due to a sustained, monotonic increase in node_disk_written_bytes_total (M31) with a high z-score of 6.51. This storage activity correlates temporally with an earlier anomaly onset (t=18.2 min) compared to other components. The leading alternative explanation is Node 5653, which shows a sharp spike in filesystem usage (M01, z=9.99) but lacks the sustained directional trend seen on 7920. Service 118 and Pod 50211 exhibit client_error_ratio spikes, likely representing downstream symptoms of the infrastructure-level disk pressure rather than independent faults. Node 4074 and Service 812 are lower-ranked alternatives showing resource shifts (filesystem free bytes drop, region_pending rise) that coincide with the incident window.", "confidence": "medium"}
```

## INC-CD9AAE6C9F71 / aiops2025
RR 1.0 → 0.0; output 291; stop
Accepted (private): ['node-3']; numeric aliases: ['4359']

```json
{"services": ["36575", "17633", "46630", "72423", "132"], "reason": "The incident is initiated by a resource exhaustion fault in Pod 36575, which manifests as a massive latency spike (M12: rrt baseline ~212ms to peak 1.44k ms) and a corresponding drop in event volume (L: volume_drop x30). This local failure propagates through the call graph; Service 753 (the owner of operations involving Pod 36575's service group) shows increased exclusive latency for 'AddItem' (R: 1.97 -> 2.18 ms), suggesting it is being delayed by its downstream dependency. Pods 17633, 46630, and 72423 are ranked lower as they share the same service alias (753) and exhibit concurrent network timeouts (M132: timeout peak 2) or network transmission anomalies (M55), but lack the specific high-magnitude RRT spike seen in 36575. The topology confirms that these pods belong to Service 753, which is called by upstream services like 930 and 175.", "confidence": "medium"}
```

## INC-CAF8151C7C9C / aiops2025
RR 0.0 → 0.0; output 268; stop
Accepted (private): ['tidb-tikv', 'tidb-tikv-0']; numeric aliases: ['399']

```json
{"services": ["207", "284", "238", "61501", "91936"], "reason": "Service 207 is the leading hypothesis as it exhibits a sustained, high-magnitude memory_usage drop (from ~1.45G to ~737M) starting at b63, which aligns with the incident window and precedes or coincides with latency increases in downstream services like 284 and 238. The topology shows 284 calling 238, which then calls 774; however, the exclusive latency for 774 increased significantly (3.72ms to 19.6ms), suggesting local degradation rather than purely propagated delay from upstream. Logs from Pod 61501 (associated with Service 161) show new errors (+100) and volume drops, but its metrics are not explicitly shown as anomalous in the M section, making it a plausible secondary impact or alternative root if 207's memory issue was transient. Node 5413 shows a disk read spike, but without explicit hosting relationships in the graph, it remains a lower-ranked infrastructure candidate.", "confidence": "medium"}
```

## INC-ECD8A1AFD496 / aiops2025
RR 1.0 → 1.0; output 216; stop
Accepted (private): ['adservice']; numeric aliases: ['122', '14187', '28199', '53466']

```json
{"services": ["14187", "28199", "56548", "78255", "122"], "reason": "The telemetry identifies Pod 14187 as the initiating root cause. The Logs (L) panel explicitly attributes error events ('Agent failed to start', 'InvocationTargetException') and a shift in error rate (0 -> 0.4) to entity 14187. In the Metrics (M) panel, the lane for POD 14187 shows a distinct spike in CPU usage that aligns with the incident window, while other pods show normal variance or unrelated spikes. The Topology (G) panel confirms that 14187 is a member of Service 122. Other candidates like 28199 (same service group) are ranked lower as potential secondary impacts due to co-location within the same service alias, though no direct causal edge is depicted between them.", "confidence": "medium"}
```

## INC-17BB91ED69B2 / aiops2025
RR 0.0 → 0.0; output 245; stop
Accepted (private): ['node-7']; numeric aliases: ['9569']

```json
{"services": ["1818", "202", "3863", "923", "785"], "reason": "The telemetry indicates a resource exhaustion incident on Node 1818. The metric M18 (node_memory_MemAvailable_bytes) shows a sharp, sustained drop from a baseline of 11.2G to a peak deviation state of 14.7G (likely representing bytes used or low available), with the highest z-score (9.72) and earliest onset (31.2 min) among all candidates. This memory pressure correlates temporally with the anomaly window in Service 202 (memory_usage) and Service 3863 (disk_write_time). While Service 202 exhibits a high z-score (67.6), its absolute change is small relative to its baseline, suggesting it may be a secondary effect of the node-level resource constraint rather than the primary origin. No explicit hosting edge is visible linking Node 1818 to these services, so the causal link is inferred from temporal correlation and the nature of the node-level failure.", "confidence": "medium"}
```

## INC-BF5E3D25D876 / aiops2025
RR 0.3333333333333333 → 1.0; output 221; stop
Accepted (private): ['checkoutservice-1', 'checkoutservice']; numeric aliases: ['342', '46678', '53569', '87970']

```json
{"services": ["342", "858", "69219", "92994", "460"], "reason": "Service 342 is the leading hypothesis as it is the upstream caller in the topology (edges to 411, 645, 858, 966) and exhibits a significant spike in client_error_ratio (M284) during the fault window. This aligns with Service 858 showing increased exclusive latency (R panel), suggesting that 342's errors may be due to downstream slowness or its own instability propagating through the call chain. Pod 69219 (a member of service 375) shows a high z-score for response metrics (M36), but lacks direct evidence of being the primary origin compared to the broader impact seen at the service level. The remaining candidates are ranked lower due to weaker temporal alignment or lack of clear causal links in the visible topology.", "confidence": "medium"}
```

## INC-987C8AAB3A59 / aiops2025
RR 0.0 → 0.0; output 313; stop
Accepted (private): ['tidb-tidb', 'tidb-tidb-0']; numeric aliases: ['759']

```json
{"services": ["34258", "988", "17854", "292", "655"], "reason": "The leading hypothesis is that Pod 34258 is the initiating root cause. This is supported by a direct causal chain visible in the telemetry: Pod 34258 (M40) shows a significant increase in `server_error_ratio` (base 0.139 to peak 33.3, z=63.7). Topologically, Service 988 calls Service 292, which in turn calls Service 655. The NAME GROUPS strip links Service 988 to Pod 34258 and Service 655 to Pod 48731 (among others). Consequently, an error spike in Pod 34258 (Service 988) would propagate downstream to its caller's callee, Service 655. Indeed, Service 655 (R panel) shows an increased count (92 -> 134), while other downstream services like 594 show similar count increases but lower latency impact. Service 988 itself shows a timeout spike (M134). The temporal alignment of the error ratio spike on 34258 with the downstream traffic/latency shifts makes it the most plausible origin compared to generic node metrics or upstream callers.", "confidence": "medium"}
```

## INC-2522930091BF / aiops2025
RR 0.5 → 0.5; output 229; stop
Accepted (private): ['checkoutservice', 'paymentservice']; numeric aliases: ['19026', '22521', '33849', '39530', '60978', '80520', '844', '921']

```json
{"services": ["236", "844", "921", "614", "866"], "reason": "The incident is characterized by a massive latency spike in Service 236 (M42 response z-score -20, M43 error ratio rising to 0.09) and its associated trace operations (R: 921/Charge exclusive p95 increased from 34.4ms to 60k ms). This aligns with the topology where Service 236 acts as a caller to Service 844 (PlaceOrder), which also exhibits extreme latency degradation (p95 69.7ms to 20k ms) and reduced throughput. The simultaneous increase in error rates for Pods 45473 and 77465 (associated with Service 614) suggests widespread impact or shared dependency failure, but the magnitude of the latency shift in 236 and 844 identifies them as the primary points of failure.", "confidence": "medium"}
```

## INC-209913B37F61 / aiops2025
RR 0.25 → 0.2; output 273; stop
Accepted (private): ['node-6']; numeric aliases: ['5669']

```json
{"services": ["9564", "1265", "30155", "784", "5669"], "reason": "The leading hypothesis is that Node 9564 (node_memory_usage_rate) is the initiating root cause. The telemetry shows a sustained increase in memory usage on this node starting at onset 19.3 minutes, which precedes the onset of other anomalies. This memory pressure correlates temporally with an increase in 'client_error_ratio' for Service 524 and a spike in 'pod_fs_writes_bytes' for Pod 30155, suggesting resource exhaustion or thrashing propagated to dependent services. Node 1265 (node_filesystem_free_bytes) is ranked second due to a sharp drop in free space (onset 25.2), but its timing is later than the memory anomaly. Pod 30155 is a likely downstream victim given its I/O spike. While the topology graph does not explicitly link these nodes/pods, the temporal ordering of the metric anomalies supports the infrastructure-first hypothesis over a pure application-layer failure. Confidence is medium because the specific causal path from node memory to service errors is inferred from correlation rather than explicit dependency edges in the provided view.", "confidence": "medium"}
```

## INC-09ED18E6FF30 / aiops2025
RR 0.0 → 0.0; output 270; stop
Accepted (private): ['emailservice']; numeric aliases: ['58504', '71843', '74209', '885']

```json
{"services": ["10517", "769", "138", "66971", "40405"], "reason": "Pod 10517 (Service 769) exhibits a sharp, sustained drop in the 'response' metric from a baseline of ~48 to a low of ~44 during the anomalous interval, indicating a significant performance degradation. This local fault is consistent with the elevated exclusive latency observed for Service 769's operations. The co-located Pod 40405 (Service 754) shows an increase in round-trip time (rtr), and Node 2880 (Node ID 2880) displays increased CPU usage, suggesting resource contention or network propagation issues affecting the cluster. Logs for Pod 66971 indicate a volume drop but no error rate change, which may be a secondary effect of the reduced response throughput from 10517. While the exact causal chain between the node-level metrics and pod-level faults is not fully explicit in the graph, the temporal correlation and specific anomaly in 10517 make it the primary suspect for the initiating root cause of the service-level latency increase.", "confidence": "medium"}
```
