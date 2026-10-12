## INC-7CE00360E043 / aiops2022
RR 0.25 → 1.0; output 315; stop
Accepted (private): ['frontend']; numeric aliases: ['23887', '36845', '67607', '767']

```json
{"services": ["36845", "20950", "32225", "66822", "19612"], "reason": "Pod 36845 is the most likely initiating fault. The topology graph (G) shows 36845 as a caller to pods 19612, 20950, 32225, 66822, and 69300. Telemetry in M indicates significant latency spikes for 36845 across multiple protocols (M06-M11), with request durations increasing by orders of magnitude (e.g., M09: base 0 -> peak 252). Logs (L) for 36845 show new error patterns ('failed to retrieve ads') during the incident window. Traces (R) confirm that 36845's exclusive p95 latency increased significantly (e.g., 2.13 -> 826 ms for GetQuote), suggesting the delay originated locally within 36845 rather than being purely propagated from callees. The other candidates (20950, 32225, 66822, 19612) are downstream dependencies or peers showing correlated metrics, but the evidence points to 36845 as the source of the degradation.", "confidence": "medium"}
```

## INC-7404365412F6 / aiops2022
RR 0.0 → 0.3333333333333333; output 262; stop
Accepted (private): ['adservice2-0']; numeric aliases: ['69047']

```json
{"services": ["90566", "8201", "69047", "33724", "13083"], "reason": "Pod 90566 is the leading root cause candidate due to severe resource exhaustion: metrics M09/M10 show container memory faults (pgfault) spiking from a baseline of ~898 to a peak of 79.3k, and M08 shows mapped file memory dropping from 53.2k to 0. This correlates temporally with latency degradation in Pod 69047 (M02-M07) and service-level errors logged by entity 33724 (LT766/LT734). The topology indicates 90566 is called by upstream services (13083/97984), consistent with a downstream failure propagating up. Node 8201 exhibits network packet errors (M04/M05) which may be a contributing infrastructure factor or a secondary symptom, but the specific application-layer memory faults on 90566 provide a more direct explanation for the service degradation.", "confidence": "medium"}
```

## INC-68411E6D69DA / aiops2022
RR 0.25 → 0.0; output 199; stop
Accepted (private): ['frontend']; numeric aliases: ['10441', '161', '64808', '70565']

```json
{"services": ["5367", "45736", "18725", "54946", "79279"], "reason": "Node 5367 is the leading root cause, exhibiting a sustained and severe degradation in filesystem health (disk free space, inode usage, and I/O) that coincides with the incident window. The topology graph shows Node 5367 as the central caller for multiple downstream pods (including 45736 and 18725), which display correlated anomalies in memory faults (pgfaults) and network throughput. This suggests a cascading failure where resource exhaustion on the node propagates to its hosted or dependent workloads. While pod-level metrics show significant z-scores, they are temporally aligned with and structurally dependent on the node-level infrastructure failure, making the node the most likely initiating fault.", "confidence": "medium"}
```

## INC-17616FF7AAD6 / aiops2022
RR 0.25 → 0.5; output 280; stop
Accepted (private): ['checkoutservice-0']; numeric aliases: ['76191']

```json
{"services": ["10382", "76191", "48361", "69626", "141"], "reason": "Pod 10382 is the leading hypothesis as it exhibits the earliest and most severe metric anomalies, specifically a massive spike in container_memory_failures (pgfault/pgmajfault) with a peak of 148 against a baseline of 0. This memory exhaustion directly correlates with the significant latency degradation observed in its service-level traces (Service 195), where exclusive p95 latency for operations like PlaceOrder increased from ~3ms to ~60ms. The topology confirms that Pod 10382 is a caller to Pods 76191 and 48361; however, since 10382's local metrics indicate resource failure prior to or concurrent with the latency spikes, the downstream pods are likely experiencing propagated delays rather than being the primary origin. Service 141 is ranked lower as an alternative because its 'jvm_classes_loaded' metric shows a step change, but without corresponding error logs or immediate trace failures on its specific pod members, it is less likely to be the initiating fault compared to the hard resource limit breach seen in 10382.", "confidence": "medium"}
```

## INC-F5CD31F4DEE1 / aiops2022
RR 0.0 → 0.0; output 236; stop
Accepted (private): ['currencyservice-2']; numeric aliases: ['91905']

```json
{"services": ["4956", "327", "185", "182", "865"], "reason": "Node 4956 is the leading root-cause candidate because its metrics (M1070, M851, M850) show simultaneous, sustained spikes in I/O wait, read latency, and read bytes that align with the estimated anomalous interval. This physical resource contention correlates temporally with the service-level degradation seen in Service 327 (mrt) and the increased exclusive p95 latencies for operations owned by Pods 50845 and 97947 (mapped to Services 185 and 182). While the logs for Pod 91905 (Service 930) indicate transport errors, these are likely downstream symptoms of the network or I/O instability originating from Node 4956. The co-occurrence of high z-scores on node-level infrastructure metrics provides a stronger causal basis than the isolated latency increases at the service level.", "confidence": "medium"}
```

## INC-33C7D3DB2A58 / aiops2022
RR 1.0 → 0.5; output 316; stop
Accepted (private): ['node-2']; numeric aliases: ['8144']

```json
{"services": ["49402", "8144", "69710", "875", "908"], "reason": "Pod 49402 is the leading root cause candidate, exhibiting a severe memory allocation anomaly (M27: istio_agent_go_memstats_alloc_bytes) with a z-score of -205 and a massive absolute drop from ~8.09M to ~961k during the incident window. This resource exhaustion likely caused the earliest observed latency degradation in its associated service 635 (M118). Node 8144 is a strong alternative hypothesis due to a cluster of highly correlated disk and I/O anomalies (M03-M08, M52, M59) including significant drops in total/used disk space and spikes in I/O wait, which could independently trigger system-wide latency issues. Pod 69710 shows concurrent page fault spikes (M97, M98), suggesting potential memory pressure as a secondary or parallel factor. Service 875 and 908 are lower-ranked alternatives; while they show elevated JVM class loading metrics (M02, M01) and increased request duration for 875, these appear more consistent with downstream symptoms of the underlying infrastructure or pod-level resource failures rather than the initiating fault, given the magnitude of the deviations seen in 49402 and 8144.", "confidence": "medium"}
```

## INC-CC8D92170500 / aiops2022
RR 1.0 → 1.0; output 256; stop
Accepted (private): ['node-3']; numeric aliases: ['1523']

```json
{"services": ["1523", "6771", "11227", "90768", "33795"], "reason": "The incident is initiated by a resource exhaustion on physical node 1523, evidenced by M09 (system.cpu.user) spiking to 76.4 (z=310), which is the earliest and most severe anomaly in the metrics stream. This high CPU load on the host propagates to the co-located pod 11227, causing visible throttling (M113 container_cpu_cfs_throttled_periods) and subsequent memory pressure (M66/M67 pgfault spikes). The latency degradation observed in traces for operations hosted on this infrastructure (e.g., 47630 hipstershop.870/SendOrderConfirmation) aligns with this root cause. While logs show error rate increases for services 977 (pods 33795/65290) and 870 (pod 90768), these are downstream symptoms of the upstream resource contention rather than independent initiating faults.", "confidence": "medium"}
```

## INC-C86F6E03B824 / aiops2022
RR 0.3333333333333333 → 0.0; output 230; stop
Accepted (private): ['productcatalogservice']; numeric aliases: ['12714', '35461', '45674', '504']

```json
{"services": ["342", "110", "65159", "78926", "92441"], "reason": "Service 342 is the leading root cause due to a massive, sustained increase in JVM classes loaded (M01) from a baseline of ~0.00 to a peak of 0.833, indicating a severe resource exhaustion or classloader leak that likely triggered cascading failures. Service 110 shows concurrent anomalies in jvm_threads_started (M03), and the topology (G) confirms that service 342 calls service 110, suggesting 110 is a downstream victim of the degradation originating at 342. Pods 65159, 78926, and 92441 are ranked lower as specific members of service 110 which may be exhibiting the observed thread spikes, but the systemic nature of the 342 metric points to the service level as the primary fault origin.", "confidence": "medium"}
```

## INC-BAC5EBEE7F18 / aiops2022
RR 0.0 → 0.0; output 393; stop
Accepted (private): ['adservice-2']; numeric aliases: ['12322']

```json
{"services": ["185", "75385", "163", "901", "212"], "reason": "Service 185 is the leading root-cause candidate because it exhibits the earliest anomaly onset (0.3 min) and a sustained, high-magnitude increase in JVM memory pool allocation (M01, peak 30.1 vs base 30.1, z 999), which aligns with a resource exhaustion hypothesis. This service also shows significant latency degradation in its GetAds operation (R89424, R87361, R15520; p95 ~500ms). The topology indicates that Service 185's pods (e.g., 15520, 89424) call downstream to Pods 12322 and 50373, suggesting that 185's internal slowness may be propagating or affecting these callees. Pod 75385 is ranked second due to concurrent, severe spikes in request duration (M05, M06) and I/O reads (M473, M474) during the incident window, indicating potential local resource contention or disk pressure. Service 163 is ranked third based on increased latency in SendOrderConfirmation (R50373), which may be a downstream effect of the broader system stress or a related fault. Services 901 and 212 are included as lower-ranked alternatives because they represent the service-level abstractions for the affected pods (15520/89424 and 50373 respectively), serving as plausible owners if the fault is distributed across their respective pod groups rather than isolated to a single instance.", "confidence": "medium"}
```

## INC-819F72DDB48B / aiops2022
RR 1.0 → 0.5; output 205; stop
Accepted (private): ['checkoutservice']; numeric aliases: ['36644', '39185', '47933', '493']

```json
{"services": ["4750", "36644", "39185", "29079", "29398"], "reason": "Node 4750 is the leading hypothesis due to having the earliest anomaly onset (t=19.2) with a significant z-score of 119, indicating a substantial deviation from its baseline system.io.avg_q_sz metric. This temporal precedence suggests an infrastructure-level fault that likely propagated to dependent components. Pod 36644 and 39185 are ranked next as they show concurrent latency spikes in trace data (PlaceOrder/GetCart) and are direct callers to Pods 29079 and 29398 per the topology ledger; however, their latency increases may be downstream effects of the node issue or independent pod faults, which cannot be fully distinguished without more granular resource metrics for the pods themselves.", "confidence": "medium"}
```

## INC-00B104A6DB74 / aiops2022
RR 1.0 → 0.5; output 270; stop
Accepted (private): ['checkoutservice-2']; numeric aliases: ['69167']

```json
{"services": ["4994", "69167", "350", "93074", "50483"], "reason": "The root cause is attributed to Node 4994 due to a sustained, multi-metric resource exhaustion pattern. Metrics M23 (cpu.iowait), M58 (io.avg_q_sz), and M29 (io.rkb_s) all show simultaneous spikes that persist throughout the anomalous interval, indicating severe I/O contention on the underlying infrastructure. This physical stress correlates temporally with high CPU throttling (M02) and memory pressure (M08/M09) in Pod 69167, which hosts Service 350. The latency degradation observed in traces for Service 350 (e.g., GetQuote p95 rising from 2.31ms to 35.1ms) and associated logs (LT851 NullPointerExceptions) are downstream consequences of this node-level bottleneck. While Pod 93074 also exhibits memory faults, its metrics do not display the same degree of sustained I/O saturation seen on Node 4994, making it a less likely primary origin than the infrastructure layer.", "confidence": "medium"}
```

## INC-C0F62DB233F2 / aiops2022
RR 0.0 → 0.0; output 336; stop
Accepted (private): ['node-4']; numeric aliases: ['1267']

```json
{"services": ["7425", "34973", "12532", "26067", "71003"], "reason": "The leading hypothesis is a physical infrastructure fault on node 7425, which exhibits the earliest and most severe telemetry anomalies. The 'Earliest Anomaly Onset' list identifies entity 71003 (onset 2.7) as the first detected signal, but the metrics for Node 7425 (M02-M07) show extreme deviations in filesystem inode usage and network segments (z-scores up to 999) that temporally align with or precede the downstream service degradation. Specifically, M03 (system.fs.inodes.in_use) shows a massive spike from a baseline of ~0.98 to a peak of 0.86 (likely representing a drop in free space or high utilization depending on metric direction, but clearly anomalous), and M07 (net.tcp.out_segs) spikes significantly. These resource exhaustion patterns on the node are consistent with causing latency and CPU throttling in co-located pods like 34973 (service 280) and 12532 (service 261), which also appear in the topology graph as part of the affected cluster. The pod-level metrics (e.g., M792 for 34973 showing cfs_throttled_seconds) support a contention model where the node's resource pressure propagates to the workloads.", "confidence": "medium"}
```

## INC-F9112289109A / aiops2025
RR 0.0 → 0.0; output 254; stop
Accepted (private): ['emailservice']; numeric aliases: ['12220', '387', '78549', '82541']

```json
{"services": ["331", "669", "28736", "2089", "14805"], "reason": "Service 331 is the leading candidate as it exhibits the earliest anomaly onset (27.3) and a significant increase in 'region_pending' (M22, z=5.01), indicating a potential upstream bottleneck or resource exhaustion that precedes other observed failures. Service 669 follows with elevated error ratios (M29/M30) and RRT spikes (M09), suggesting it is either impacted by the delay from 331 or experiencing its own localized fault. Pod 28736 is ranked third due to concurrent network receive/transmit anomalies (M10-M12) which may be a symptom of the service-level congestion. Node 2089 and Pod 14805 are lower-ranked alternatives; while they show disk write time and RRT deviations respectively, their onsets coincide with the broader incident window rather than preceding it, making them less likely to be the initiating root cause compared to the early onset of Service 331.", "confidence": "medium"}
```

## INC-B324546FFC06 / aiops2025
RR 0.5 → 0.5; output 181; stop
Accepted (private): ['node-8']; numeric aliases: ['6421']

```json
{"services": ["3184", "6421", "267", "24984", "56747"], "reason": "Node 3184 exhibits a distinct, sustained step-change in filesystem usage (M01) and disk write time (M03) during the anomaly window, indicating resource exhaustion or hardware degradation. This correlates temporally with increased client errors in Service 267 and Pod 24984. Node 6421 shows similar but less severe filesystem anomalies. The topology confirms Service 267 calls downstream services, suggesting the node-level fault is propagating upstream to application layers. Log evidence from entity 56747 indicates volume drops consistent with this disruption, though no specific error templates are visible to confirm the mechanism.", "confidence": "medium"}
```

## INC-C76C22A65921 / aiops2025
RR 0.0 → 0.0; output 224; stop
Accepted (private): ['cartservice-1', 'cartservice']; numeric aliases: ['563', '69011', '70609', '86976']

```json
{"services": ["7920", "5653", "118", "50211", "306"], "reason": "The leading hypothesis is that Node 7920 is the initiating root cause, evidenced by its earliest anomaly onset (t=18.2) with a high z-score of 8.72 for node_disk_written_bytes_total, which precedes the service-level latency and error spikes observed in Service 118 and Pod 50211. The temporal alignment suggests that disk I/O pressure on Node 7920 propagated to dependent services, causing the subsequent rise in client_error_ratio and rtt_max. While the topology does not explicitly map Node 7920 to these specific pods, the chronological precedence of the infrastructure metric over the application-layer faults makes it the most plausible origin. Alternative explanations involving direct pod failure are less likely given the absence of early resource exhaustion signals (like CPU or memory spikes) in the pods prior to the node-level anomaly.", "confidence": "medium"}
```

## INC-CD9AAE6C9F71 / aiops2025
RR 1.0 → 0.5; output 230; stop
Accepted (private): ['node-3']; numeric aliases: ['4359']

```json
{"services": ["4070", "4359", "17633", "286", "753"], "reason": "The leading hypothesis is that Node 4070 is the initiating root cause due to a distinct, sharp drop in network receive and transmit packets (M02, M03) during the anomalous window, which typically indicates a physical or virtual link failure. This infrastructure-level disruption correlates temporally with the latency spikes observed downstream in Service 286 (M17) and its associated Pod 17633 (M14). While Service 753 also shows increased RRT (M15), it is a caller in the topology (G), making it more likely to be affected by the propagation of the fault from the lower-level nodes rather than being the origin. The evidence for Node 4359 is weaker, showing a sustained increase in CPU usage (M06) but without the clear binary-like signal seen in 4070's packet loss.", "confidence": "medium"}
```

## INC-CAF8151C7C9C / aiops2025
RR 0.0 → 0.0; output 266; stop
Accepted (private): ['tidb-tikv', 'tidb-tikv-0']; numeric aliases: ['399']

```json
{"services": ["207", "284", "24729", "161", "238"], "reason": "Service 207 is the leading hypothesis due to a distinct resource anomaly (memory_usage drop from ~1.45G to ~737M, z=-28.9) that temporally precedes the latency and error spikes observed in its downstream dependencies. Service 284 exhibits severe RRT degradation (peak 25.8M) and timeout increases, consistent with being impacted by the upstream 207 failure or acting as a secondary bottleneck. Pod 24729 (member of service 284) shows corresponding rrt and error_ratio anomalies. Services 161 and 238 are ranked lower as they exhibit elevated client_error metrics and trace latency changes, but their onsets appear simultaneous with or subsequent to the initial resource shift in 207, suggesting they are likely propagating effects rather than the initiating root cause. The topology confirms 284 calls 161 and 238, supporting a propagation path where an issue in 207/284 impacts the rest of the graph.", "confidence": "medium"}
```

## INC-ECD8A1AFD496 / aiops2025
RR 1.0 → 1.0; output 261; stop
Accepted (private): ['adservice']; numeric aliases: ['122', '14187', '28199', '53466']

```json
{"services": ["14187", "28199", "53466", "122", "1322"], "reason": "The primary evidence points to Pod 14187 as the initiating fault. The Logs panel (L) explicitly identifies entity 14187 with a 'level unknown' status and messages indicating an agent failure ('Agent failed to start!') and a reflection exception, accompanied by a significant increase in error rates (0 -> 0.4). This is corroborated by Metrics (M), where M127 (client_error_ratio) and M128 (error_ratio) for Service 122 show a sharp deviation from baseline during the anomalous interval; since Pod 14187 is a member of Service 122 (per Topology G), these service-level errors are consistent with a failure within that pod. Node 1322 shows concurrent disk I/O anomalies (increased read bytes and write time), which may be a downstream effect or co-occurring issue, but the specific application-level exceptions in Pod 14187 provide a more direct causal link to the service degradation.", "confidence": "medium"}
```

## INC-17BB91ED69B2 / aiops2025
RR 0.0 → 0.0; output 307; stop
Accepted (private): ['node-7']; numeric aliases: ['9569']

```json
{"services": ["1818", "3863", "202", "730", "21659"], "reason": "The leading hypothesis is that Node 1818 is the initiating root cause due to a storage exhaustion event. Metrics M111 and M112 show Node 1818 experiencing a massive spike in disk read activity (z=3.87), while Metric M07 for Node 3863 shows a critical drop in free filesystem bytes (base 8.2G, peak 8.13G, z=-79.2) coinciding with the incident window. This resource constraint on the infrastructure layer correlates temporally with latency degradation observed in Service 202 (M09 memory usage rise, z=67.6) and Service 730 (client errors, z=3.87). The topology graph indicates these services are interconnected, suggesting the node-level disk pressure propagated as service-level failures. While Node 3863 also exhibits severe anomalies, the specific nature of 'free_bytes' dropping suggests a capacity limit being hit which often precedes or accompanies the high-read spikes seen on 1818; however, without explicit hosting edges linking the pods to specific nodes, the exact causal direction between 1818 and 3863 remains uncertain, though both are strong primary candidates.", "confidence": "medium"}
```

## INC-BF5E3D25D876 / aiops2025
RR 0.3333333333333333 → 1.0; output 226; stop
Accepted (private): ['checkoutservice-1', 'checkoutservice']; numeric aliases: ['342', '46678', '53569', '87970']

```json
{"services": ["342", "858", "411", "511", "2450"], "reason": "Service 342 is the leading hypothesis due to its member pod 46678 exhibiting a sustained, multi-metric resource collapse (CPU, network receive/transmit bytes and packets) that coincides with the telemetry-estimated anomalous interval. This local resource exhaustion in 342 likely propagates to downstream service 858, which shows increased exclusive latency and a volume drop in logs; however, 858's behavior could also be an independent fault given the lack of direct error evidence in 342. Service 411 is ranked lower as it shares the same topology but lacks the severe resource metrics seen in 342. Node 2450 is included as a lower-ranked alternative because its filesystem usage rate spike during the incident window suggests potential infrastructure-level pressure, though the correlation with the specific service-level failures is less certain than the pod-level anomalies.", "confidence": "medium"}
```

## INC-987C8AAB3A59 / aiops2025
RR 0.0 → 0.0; output 228; stop
Accepted (private): ['tidb-tidb', 'tidb-tidb-0']; numeric aliases: ['759']

```json
{"services": ["33118", "70044", "55634", "42078", "90452"], "reason": "The telemetry indicates a systemic degradation originating from the service group 988, which manifests as extreme latency (rtr/rtr_max) across its constituent pods. Pod 33118 is ranked highest due to the explicit log evidence of 'connection refused' errors and a significant spike in error rates, suggesting it is the specific instance experiencing resource exhaustion or failure that is driving the broader service-level latency. Pods 70044 and 55634 are strong alternatives within the same service group showing identical latency anomalies but lacking the specific error logs seen in 33118. Pods 42078 and 90452 are lower-ranked alternatives as they show client_error spikes consistent with the downstream impact of the 988 group's instability, but their latency metrics are less severe than those of the primary suspects.", "confidence": "medium"}
```

## INC-2522930091BF / aiops2025
RR 0.5 → 0.5; output 261; stop
Accepted (private): ['checkoutservice', 'paymentservice']; numeric aliases: ['19026', '22521', '33849', '39530', '60978', '80520', '844', '921']

```json
{"services": ["236", "844", "921", "614", "866"], "reason": "The telemetry indicates a systemic latency and error incident propagating through the service mesh. Service 236 (M17) exhibits the most severe response time degradation (base 218k -> peak 60M, z=999), which correlates with a massive exclusive p95 latency increase in trace 921 (34.4ms -> 60k ms). The topology shows a call chain involving services 614, 844, 921, and 866; while 236 is not explicitly shown as a node in the G card's edge ledger, its extreme metric anomaly aligns temporally with the elevated latencies in the downstream/related services 844 and 921. Logs from pods associated with these services (e.g., LT1451 on entity 45473/77465) confirm a rise in error rates from zero to non-zero levels during the same interval, supporting a shared root cause within this cluster of interacting services.", "confidence": "medium"}
```

## INC-209913B37F61 / aiops2025
RR 0.25 → 0.0; output 313; stop
Accepted (private): ['node-6']; numeric aliases: ['5669']

```json
{"services": ["9564", "34875", "12813", "524", "51512"], "reason": "The leading hypothesis is that Node 9564 (ID 9564) initiated the incident due to a disk I/O failure. Evidence from Metrics M20 shows node_disk_write_time_seconds_total for Node 9564 spiking to a peak of 0.02s (z=6.52) within the anomaly window, representing a significant deviation from its baseline of ~0.01s. This onset (t=19.3) is the earliest among the displayed anomalies and temporally precedes the degradation in Service 945 (onset t=25.2), which exhibits increased raft_apply_wait (M03) and snapshot_apply_count (M05). While Pod 34875 (Service 945) shows high memory working set bytes (M01) and Pod 12813 (Service 205) shows high rtt_max (M06), these are likely downstream effects or concurrent symptoms rather than the primary root cause given the earlier infrastructure-level spike on Node 9564. The topology does not explicitly link Node 9564 to Service 945, but the temporal precedence of the disk write latency spike supports it as the initiating fault.", "confidence": "medium"}
```

## INC-09ED18E6FF30 / aiops2025
RR 0.0 → 0.5; output 225; stop
Accepted (private): ['emailservice']; numeric aliases: ['58504', '71843', '74209', '885']

```json
{"services": ["2134", "885", "71843", "939", "754"], "reason": "Node 2134 (M06) exhibits the earliest and most distinct resource anomaly, with node_disk_read_bytes_total spiking from a near-zero baseline to 6.55k (z=321), which precedes or coincides with latency degradation in dependent services. Service 885 shows a significant latency increase (p95 3.63k -> 29k ms, z=3.74) consistent with I/O contention on the underlying infrastructure. Pod 71843 (part of service 885) mirrors this latency spike (rtrt_max 4.08k -> 46k ms). Services 939 and 754 show secondary latency impacts (z~0.34) likely due to propagation from the primary I/O bottleneck at Node 2134.", "confidence": "medium"}
```
