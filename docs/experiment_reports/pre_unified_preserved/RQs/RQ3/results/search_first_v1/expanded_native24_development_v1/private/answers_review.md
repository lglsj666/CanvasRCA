## INC-7CE00360E043 / aiops2022
RR 0.25 → 0.25; output 231; stop
Accepted (private): ['frontend']; numeric aliases: ['23887', '36845', '67607', '767']

```json
{"services": ["235", "548", "21523", "23887", "36845"], "reason": "Service 235 is the leading root cause candidate as it exhibits the earliest anomaly onset (0.3 minutes) and a massive z-score of -1 for 'jvm_threads_started', indicating a severe deviation from its near-zero baseline that temporally precedes other faults. Service 548 follows with a high z-score (999) on 'jvm_memory_pool_Metapace' and elevated latency in downstream traces, suggesting resource exhaustion or propagation. Pod 21523 (a member of service 548) shows significant spikes in request bytes, making it a plausible specific instance of the service-level fault. Pods 23887 and 36845 are ranked lower due to concurrent duration/latency anomalies and log errors, respectively, but lack the temporal precedence or extreme statistical deviation seen in services 235 and 548.", "confidence": "medium"}
```

## INC-7404365412F6 / aiops2022
RR 0.5 → 0.0; output 274; stop
Accepted (private): ['adservice2-0']; numeric aliases: ['69047']

```json
{"services": ["348", "13083", "97984", "68527", "8201"], "reason": "Service 348 is the leading root cause candidate because its JVM metrics (M22, M15, M16, M23) show a sustained increase in committed memory and thread counts starting at bin b0 within the anomalous interval. This temporal onset aligns with the earliest anomaly listed for entity 348 in the topology panel. The concurrent rise in network errors on Node 8201 (M04, M05) suggests that the resource exhaustion or instability in Service 348 is propagating to the infrastructure layer. Pod 13083 shows significant latency increases (exclusive p95 from 5.41ms to 28.2ms), but as a downstream consumer in the call graph (callees of 13083 include 64820, 68527), it is likely experiencing degradation due to upstream issues rather than being the origin. Logs for Entity 33724 show NullPointerExceptions, which are consistent with service-level faults but do not pinpoint a specific infrastructure node.", "confidence": "medium"}
```

## INC-68411E6D69DA / aiops2022
RR 0.0 → 0.25; output 289; stop
Accepted (private): ['frontend']; numeric aliases: ['10441', '161', '64808', '70565']

```json
{"services": ["5367", "4251", "9163", "10441", "18725"], "reason": "The primary evidence points to Node 5367 as the initiating root cause. The metrics for this node (M01-M07) show a sustained, step-function degradation in disk and filesystem resources (free space, usage percentage, inode counts) that begins before the main incident window and persists throughout the recording, with high z-scores indicating significant deviation from baseline. This resource exhaustion on the infrastructure layer is a strong candidate for causing downstream application issues. Node 4251 shows network segment spikes, but these appear concurrent or slightly later than the start of the 5367 degradation. Node 9163 shows I/O spikes, which could be a symptom of the disk pressure seen on 5367 or a separate issue, but the sustained nature of 5367's disk metrics makes it the more likely origin. Pods 10441 and 18725 show network receive spikes, which are consistent with latency or retry behavior caused by upstream infrastructure faults rather than being the source themselves. No specific pod or service metric indicates an internal failure (like CPU saturation or error logs) that would precede the node-level disk issues.", "confidence": "medium"}
```

## INC-17616FF7AAD6 / aiops2022
RR 0.25 → 0.25; output 263; stop
Accepted (private): ['checkoutservice-0']; numeric aliases: ['76191']

```json
{"services": ["27832", "10085", "27975", "76191", "141"], "reason": "The incident is initiated by a resource exhaustion fault on pod 27832, which manifests as severe memory pressure (M06/M07 container_memory_failures peak at 33 from a baseline of 0) and a significant increase in exclusive latency for the hipstershop.195/PlaceOrder operation (R: 3.09ms -> 59.6ms). This local delay propagates to downstream callers, evidenced by increased exclusive latency in service 195's EmptyCart operations (R: 94717, 76191). The high z-scores observed on node 9071 (disk usage/free space) and node 1172 are likely secondary effects or unrelated noise, as the primary failure signals (memory failures and specific operation latency) are localized to the application layer pods within the 195 service group. Pod 10085 shows early anomaly onset but lacks the distinct resource failure metrics seen in 27832.", "confidence": "high"}
```

## INC-F5CD31F4DEE1 / aiops2022
RR 0.0 → 0.0; output 213; stop
Accepted (private): ['currencyservice-2']; numeric aliases: ['91905']

```json
{"services": ["9189", "327", "29295", "32588", "80139"], "reason": "The root cause is attributed to Node 9189 due to a synchronized, multi-dimensional resource anomaly. Metrics M01-M17 show that disk (total/used/free), filesystem inodes (free/in-use/total/used), and memory (pct_usage/real_pct_used/used) all deviate from baseline simultaneously within the same temporal window. This pattern of concurrent pressure across storage and memory subsystems on a single node indicates a host-level infrastructure failure or exhaustion event. The resulting impact propagates to Service 327 (M10 mrt latency spike) and Pods 29295, 32588, and 80139, which exhibit increased request duration and network receive activity consistent with processing delays or retries caused by the underlying node instability.", "confidence": "high"}
```

## INC-33C7D3DB2A58 / aiops2022
RR 1.0 → 1.0; output 297; stop
Accepted (private): ['node-2']; numeric aliases: ['8144']

```json
{"services": ["8144", "97583", "26460", "875", "908"], "reason": "The root cause is attributed to node 8144, which exhibits a clear temporal and causal anomaly in its metrics. The 'Earliest Anomaly Onset' list identifies node 8144 as the first component to deviate from baseline (onset at 15 min), while other anomalies occur later. Specifically, M08 (system.io.avg_q_sz) shows a massive spike (z=999) starting at bin b16, coinciding with the onset of service-level latency issues. This is supported by M09 (io.await) and M22 (io.util) also spiking on node 8144 during the same window. Service 875 (and its pods 97583, 26460) shows increased exclusive latency in traces (R section) and elevated error rates in logs (L section), consistent with being downstream victims of the I/O saturation on node 8144. While the dashboard does not explicitly draw a hosting edge between node 8144 and these services, the temporal precedence of the node's I/O failure over the service degradation strongly implies a dependency relationship where the infrastructure fault initiates the incident.", "confidence": "medium"}
```

## INC-CC8D92170500 / aiops2022
RR 0.25 → 1.0; output 225; stop
Accepted (private): ['node-3']; numeric aliases: ['1523']

```json
{"services": ["1523", "60245", "64649", "83855", "7010"], "reason": "The incident is initiated by a resource exhaustion on physical node 1523, which exhibits a sharp increase in system CPU usage (M16) and user CPU time (M09) peaking at z=310. This local resource contention propagates to the application layer, causing a significant latency spike in service 727's 'SendOrderConfirmation' operation (exclusive p95 latency increases from 3.61ms to 24.3ms). The topology graph confirms that pods 60245, 64649, and 83855 are downstream of this path, making them likely secondary contributors or victims of the delay rather than independent root causes. Node 7010 shows memory pressure but lacks the direct causal link to the primary latency event seen in 1523.", "confidence": "medium"}
```

## INC-C86F6E03B824 / aiops2022
RR 0.0 → 0.3333333333333333; output 226; stop
Accepted (private): ['productcatalogservice']; numeric aliases: ['12714', '35461', '45674', '504']

```json
{"services": ["109", "14904", "12714", "35461", "45674"], "reason": "Service 109 (pod 10122) is the leading root cause, evidenced by a sharp spike in jvm_threads_started to a peak of 1 with a high z-score (z=999), indicating severe resource exhaustion or thrashing. This anomaly aligns temporally with latency spikes observed across its downstream dependencies (pods 14904, 12714, 35461, and 45674). The topology confirms these pods are called by upstream services (79234, 80028) and likely depend on Service 109's resources; their increased request duration metrics (e.g., M16, M18, M17) reflect the propagated impact of the initial fault in Service 109 rather than independent failures.", "confidence": "medium"}
```

## INC-BAC5EBEE7F18 / aiops2022
RR 0.0 → 0.0; output 287; stop
Accepted (private): ['adservice-2']; numeric aliases: ['12322']

```json
{"services": ["185", "722", "61932", "901", "908"], "reason": "Service 185 is the leading root-cause candidate because it exhibits the earliest anomaly onset (0.3 min) and a sustained, multi-dimensional resource exhaustion pattern in the metrics: JVM compilation time (M22), GC memory usage (M16/M20/M21), and Metaspace allocation (M01) all show step-change increases that persist through the observation window. This local degradation correlates with massive latency spikes in its downstream operations (hipstershop.185/GetAds on pods 89424, 87361, and 15520), where exclusive p95 latency jumps from ~4ms to ~500ms (Δlog2 ≈ +6.8). The logs for pod 89424 confirm this impact with a 'failed to retrieve ads' error rate increase. While Pod 61932 (service 812) shows high request duration, its topology position as a callee of 185 suggests it may be experiencing secondary effects or shared infrastructure issues, but 185's internal resource saturation is the more direct initiator of the observed service-level failure.", "confidence": "high"}
```

## INC-819F72DDB48B / aiops2022
RR 0.5 → 1.0; output 208; stop
Accepted (private): ['checkoutservice']; numeric aliases: ['36644', '39185', '47933', '493']

```json
{"services": ["36644", "86248", "39185", "47933", "85810"], "reason": "Pod 36644 is the leading hypothesis as it hosts the earliest logged anomaly (LT224, bin 34) indicating a dial tcp i/o timeout to the jaeger-collector, which correlates with a significant increase in exclusive p95 latency for its operation (2.94 -> 11.4k ms). This local resource or network failure likely propagates to callers like pod 86248 and 39185, which also exhibit elevated latency and error rates within the same temporal window. While the topology shows these pods are interconnected, the specific 'i/o timeout' log on 36644 provides a distinct causal mechanism compared to the other pods where only generic request errors or latency spikes are observed.", "confidence": "medium"}
```

## INC-00B104A6DB74 / aiops2022
RR 0.5 → 1.0; output 262; stop
Accepted (private): ['checkoutservice-2']; numeric aliases: ['69167']

```json
{"services": ["69167", "4994", "50483", "22393", "37209"], "reason": "Pod 69167 is the leading root cause, evidenced by severe resource exhaustion (CPU throttling and memory failures) with a massive z-score of 999 on container_memory_usage_MB. This local degradation correlates with a significant increase in exclusive latency for its service's operations (SendOrderConfirmation, GetQuote). Node 4994 is ranked second due to a concurrent CPU iowait spike (z=293), suggesting a potential underlying infrastructure pressure or co-located load, though the specific pod-level faults in 69167 are more distinct. Pod 50483 is ranked third as a downstream caller showing elevated latency, likely propagating the delay from 69167 rather than originating it. Service 22393 (associated with 69167) and Pod 37209 are included as lower-ranked alternatives given the topology connections and lack of unique primary fault indicators compared to the direct resource saturation observed in 69167.", "confidence": "medium"}
```

## INC-C0F62DB233F2 / aiops2022
RR 1.0 → 0.0; output 250; stop
Accepted (private): ['node-4']; numeric aliases: ['1267']

```json
{"services": ["7425", "34973", "66938", "26757", "12532"], "reason": "The leading hypothesis is a resource exhaustion fault on node 7425, which exhibits the earliest and most severe metric anomalies (onset 0.3 min). Specifically, system.fs.inodes_free drops significantly while system.disk.used increases sharply, indicating filesystem pressure. This temporal precedence aligns with the subsequent latency degradation observed in the call graph, where pod 34973 (service 280) shows the largest exclusive latency increase (p95 33.2 -> 48.8 ms) as a direct callee of service 828. The memory cache drops across multiple pods (e.g., 34973, 66938) are consistent consequences of this underlying infrastructure stress rather than independent origins. Uncertainty remains regarding whether the specific filesystem type or workload distribution on 7425 triggered the inode exhaustion versus general disk saturation, but the node-level metrics provide the strongest causal evidence for the incident's initiation.", "confidence": "medium"}
```

## INC-F9112289109A / aiops2025
RR 0.0 → 0.0; output 202; stop
Accepted (private): ['emailservice']; numeric aliases: ['12220', '387', '78549', '82541']

```json
{"services": ["331", "28736", "14805", "2195", "609"], "reason": "Service 331 is the leading candidate as it exhibits the earliest anomaly onset (27.3) and a significant increase in 'region_pending' (M22), indicating resource saturation or queue buildup that likely initiated the incident. Pod 28736 is ranked second due to a sharp spike in 'pod_memory_working_set_bytes' (M16) coinciding with the fault window, suggesting a memory leak or exhaustion event. Node 2195 shows a sustained rise in 'node_disk_written_bytes_total' (M07), representing a plausible infrastructure-level I/O bottleneck. Service 609 and Pod 14805 are lower-ranked alternatives showing elevated latency (rrt_max) consistent with downstream impact from the primary faults.", "confidence": "medium"}
```

## INC-B324546FFC06 / aiops2025
RR 0.0 → 0.5; output 226; stop
Accepted (private): ['node-8']; numeric aliases: ['6421']

```json
{"services": ["3184", "6421", "768", "24984", "56747"], "reason": "Node 3184 exhibits a distinct resource exhaustion pattern: node_filesystem_usage_rate (M01) rises from a baseline of 47.3 to a peak of 47.3 with a z-score of 999, and node_disk_write_time_seconds_total (M03) spikes significantly. This physical infrastructure failure is the most plausible root cause for the observed service degradation. Service 768 (and its pod 24984) shows elevated client_error metrics (M14-M17) and trace latency increases, consistent with being impacted by the underlying node fault. Node 6421 also shows filesystem usage changes but lacks the extreme z-score magnitude seen in 3184. The remaining candidates are ranked lower due to weaker or indirect evidence links compared to the clear resource saturation on 3184.", "confidence": "medium"}
```

## INC-C76C22A65921 / aiops2025
RR 0.0 → 0.0; output 282; stop
Accepted (private): ['cartservice-1', 'cartservice']; numeric aliases: ['563', '69011', '70609', '86976']

```json
{"services": ["54912", "7920", "306", "118", "105"], "reason": "The top-ranked hypothesis is that Pod 54912 (Service 641) is the initiating root cause. This is supported by its metric M16 (rtr) showing a sharp, high-amplitude spike (z=9.12) that aligns temporally with the shaded anomaly interval and precedes or coincides with the latency spikes in downstream services. While Service 306 (M07/M15) shows massive rtr_max spikes (z=20.7), these are likely secondary effects of the delay originating upstream from 54912, as suggested by the topology flow. Service 118 exhibits client errors (M22/M23) consistent with being a victim of the latency propagation rather than the source, given the lack of resource exhaustion signals on its own metrics. The evidence for 54912 is strong but not absolute due to the limited visibility of direct call edges, leaving some uncertainty regarding whether an intermediate node (like 7920) might be the true origin, though 54912's specific metric deviation makes it the most plausible primary suspect.", "confidence": "medium"}
```

## INC-CD9AAE6C9F71 / aiops2025
RR 0.0 → 1.0; output 210; stop
Accepted (private): ['node-3']; numeric aliases: ['4359']

```json
{"services": ["4359", "17633", "36575", "82462", "753"], "reason": "The primary evidence points to Node 4359 as the initiating root cause. The metrics for Node 4359 (M06, M22) show a sharp increase in CPU usage and network transmission during the anomalous window (shaded area), which aligns temporally with the latency spikes observed in Pods 17633, 36575, and 82462. These pods exhibit increased RRT/latency that coincides with the node-level resource contention. Service 753 is ranked lower as it appears in the topology as a downstream dependency of the affected services, suggesting its latency increase may be propagated rather than originating from the node fault itself. No other nodes or services show comparable magnitude of baseline deviation in their own telemetry.", "confidence": "medium"}
```

## INC-CAF8151C7C9C / aiops2025
RR 0.0 → 0.0; output 271; stop
Accepted (private): ['tidb-tikv', 'tidb-tikv-0']; numeric aliases: ['399']

```json
{"services": ["207", "20843", "14984", "260", "560"], "reason": "Service 207 is the leading hypothesis because it exhibits a sustained, high-magnitude memory_usage drop (from ~1.45G to ~737M) with a massive z-score (-28.9), which is consistent with resource exhaustion or a crash initiating the incident. This aligns with the 'earliest anomaly onset' list in G, where 207 appears first (onset 16.2). Pod 20843 is ranked second due to correlated error spikes (client_error_ratio and error_ratio) that temporally follow the initial signal from 207; however, as a pod-level entity, it may be a victim of the service-level fault rather than the origin. Node 14984 is included as a lower-ranked alternative infrastructure candidate, though its specific telemetry is not explicitly detailed in the visible lanes, representing uncertainty regarding physical root causes. Service 260 and 560 are listed as plausible alternatives given their presence in the topology and concurrent metric anomalies, but lack the distinct magnitude of change seen in 207.", "confidence": "medium"}
```

## INC-ECD8A1AFD496 / aiops2025
RR 1.0 → 1.0; output 296; stop
Accepted (private): ['adservice']; numeric aliases: ['122', '14187', '28199', '53466']

```json
{"services": ["14187", "92965", "855", "1322", "50767"], "reason": "The primary evidence points to Pod 14187 as the initiating fault. The Logs (L) panel explicitly identifies entity 14187 with a 'level unknown' status and messages indicating an agent failure ('Agent failed to start!') and a reflection exception, accompanied by a significant increase in error rates (0 -> 0.4). This is temporally consistent with the Metrics (M) panel, which shows sharp spikes in read/write throughput for Service 490 (likely the host or dependent service of 14187) during the same anomalous interval. While Service 855 and Pod 92965 also show increased client errors, these are likely downstream effects of the primary failure in 14187. Node 1322 shows disk I/O anomalies but lacks the specific application-level error logs found in 14187, making it a secondary suspect rather than the root cause. The topology (G) links 14187 to Service 122, providing context for its role in the system, though no direct call edges to other failing services are shown to definitively prove propagation paths beyond the temporal correlation.", "confidence": "medium"}
```

## INC-17BB91ED69B2 / aiops2025
RR 0.0 → 0.0; output 280; stop
Accepted (private): ['node-7']; numeric aliases: ['9569']

```json
{"services": ["158", "238", "7014", "191", "21659"], "reason": "Service 158 is the leading hypothesis due to a high-magnitude latency regression in operation 'AddItem' (exclusive p95 increased from 2.43 ms to 2.77 ms, Δlog2 0.19), which exceeds the minor fluctuations seen in other services like 785 or 776. This local performance degradation is supported by an earliest anomaly onset for Service 151 at t=31.2 minutes; given that Service 151 calls Service 158, the timing suggests 158's delay may have propagated upstream. Alternative explanations such as resource exhaustion are less likely: Node 1818 shows only a small absolute increase in memory usage (11.2G to 14.7G) and Node 7014 shows a drop in usage rate despite a high z-score, which does not indicate failure. Pod 21659 is ranked lower because its filesystem read spike (base 0 -> peak 17.8k) appears to be a transient event rather than a sustained root cause affecting service-level latency.", "confidence": "medium"}
```

## INC-BF5E3D25D876 / aiops2025
RR 0.0 → 0.3333333333333333; output 293; stop
Accepted (private): ['checkoutservice-1', 'checkoutservice']; numeric aliases: ['342', '46678', '53569', '87970']

```json
{"services": ["351", "858", "53569", "2450", "1609"], "reason": "Service 351 is the leading hypothesis because it exhibits a high z-score (z=16.2) for snapshot_apply_count, with a peak of 0.71 against a very low baseline of 0.064, indicating a significant deviation from its own operational norm within the fault window. Service 858 and pod 53569 are plausible secondary candidates due to concurrent resource spikes; specifically, service 858 shows an rtt_max increase (base 31.2k -> peak 507k) and pod 53569 shows network receive/transmit increases (e.g., receive_bytes base 0 -> peak 6.49k). Node 2450 and node 1609 are ranked lower as infrastructure alternatives given their memory and filesystem metric fluctuations (node_memory_MemAvailable_bytes and node_filesystem_free_bytes), but lack the specific application-level anomaly magnitude seen in service 351. The topology suggests propagation from upstream services like 342/399 to 858, but the distinct spike in 351's metrics makes it a strong independent candidate for the initiating fault.", "confidence": "medium"}
```

## INC-987C8AAB3A59 / aiops2025
RR 0.0 → 0.0; output 292; stop
Accepted (private): ['tidb-tidb', 'tidb-tidb-0']; numeric aliases: ['759']

```json
{"services": ["33118", "70044", "988", "292", "655"], "reason": "The leading hypothesis is that pod 33118 (and its sibling 70044) initiated the incident. The Logs section explicitly attributes error templates LT859 to entities 33118 and 70044, showing a jump from baseline 0 to fault rates of 46 and 29 respectively, with messages indicating 'connection refused' during product queries. This represents a hard failure signal. In contrast, the Metrics for service 988 (which calls 33118's service group via pod 17854) show increased RRT (M17) and client errors (M09/M10), but these are consistent with downstream propagation from the connection failures rather than an independent root cause. Traces for services 292, 359, 594, and 655 show negligible latency changes (Δlog2 < 0.1), suggesting they are not the source of the degradation. The specific 'connection refused' logs on pods 33118/70044 provide the strongest causal evidence for the origin of the connectivity issues affecting the upstream callers.", "confidence": "medium"}
```

## INC-2522930091BF / aiops2025
RR 1.0 → 0.5; output 302; stop
Accepted (private): ['checkoutservice', 'paymentservice']; numeric aliases: ['19026', '22521', '33849', '39530', '60978', '80520', '844', '921']

```json
{"services": ["45473", "22521", "80520", "236", "921"], "reason": "Pod 45473 (service 614) is the leading root-cause candidate because it exhibits the earliest and most severe resource anomalies: M20 shows a massive spike in pod_memory_working_set_bytes (base 1.36k to peak 1.65M, z 999), and M12/M13 show corresponding server_error spikes (z 999). The temporal pattern of these metrics aligns with the incident window. While service-level traces for 614 show increased latency (R: p95 31.9 -> 60.8ms), the specific magnitude of the memory error on pod 45473 suggests a local failure propagating to the service level. Other pods like 22521 (service 844) and 80520 (service 921) also show high-z-score memory and RRT anomalies, but the severity and combination of metrics on 45473 make it the primary suspect. Service 236 and 921 are ranked lower as they primarily show downstream effects or less distinct primary signals compared to the explicit resource exhaustion on 45473.", "confidence": "medium"}
```

## INC-209913B37F61 / aiops2025
RR 0.3333333333333333 → 0.25; output 218; stop
Accepted (private): ['node-6']; numeric aliases: ['5669']

```json
{"services": ["9564", "10719", "12813", "5669", "945"], "reason": "Node 9564 is the leading root cause, exhibiting the earliest anomaly onset (19.3) and a high z-score (14.1) for node_memory_usage_rate in the M metrics. This temporal lead suggests an infrastructure-level resource constraint that precedes the observed service-level symptoms. Service 945 shows concurrent anomalies in raft_apply_wait and snapshot_apply_count, consistent with a storage or memory bottleneck propagating to dependent services. Pods 10719 and 12813 exhibit latency spikes (rtr_max) during the incident window, likely as secondary effects of the underlying node pressure or service delays. Node 5669 also shows disk write time anomalies but with a later onset (28.2), making it less likely to be the primary initiator compared to 9564.", "confidence": "medium"}
```

## INC-09ED18E6FF30 / aiops2025
RR 0.0 → 0.0; output 262; stop
Accepted (private): ['emailservice']; numeric aliases: ['58504', '71843', '74209', '885']

```json
{"services": ["138", "66971", "242", "30100", "55357"], "reason": "The telemetry indicates a storage subsystem failure on Node 2134 (M06, M09), evidenced by a massive spike in disk read bytes (z=321) and network transmit bytes (z=32.1). This correlates with a significant drop in filesystem free bytes on Node 5414 (M08, z=78.2), suggesting the nodes are co-located or sharing a volume that has exhausted capacity. The impact propagates to Service 138, whose member Pod 66971 shows an error log pattern (LT1375) indicating 'volume_drop' (L panel). While Pods 30100 (Service 242) and 55357 (Service 986) exhibit high CPU/process metrics, these appear as secondary symptoms of resource contention or retry loops triggered by the underlying storage issue rather than the primary fault origin. No evidence supports a root cause within the application logic of the other services shown in the topology.", "confidence": "medium"}
```
