## INC-9FFDC80821DC / aiops2022
RR 1.0 -> 1.0
Accepted (private): ['emailservice']

```json
{"services": ["31794", "36490", "41307", "2649", "6522"], "reason": "The incident is characterized by a simultaneous, sharp increase in CPU and memory utilization across multiple pods (31794, 36490, 41307) and nodes (2649, 6522). The traces for service 459 (pods 31794, 36490, 41307) show significant latency degradation (e.g., 31794: 0.238ms -> 3.29ms), and logs from pod 31794 reveal new errors related to gRPC transport timeouts ('dial tcp: i/o timeout'), indicating that the resource saturation caused connectivity failures. Pod 31794 is ranked highest due to the explicit error logs and high latency impact, while other pods and nodes are included as co-affected components or potential shared-infrastructure contributors.", "confidence": "medium"}
```

## INC-107AD4FC7293 / aiops2022
RR 1.0 -> 1.0
Accepted (private): ['checkoutservice']

```json
{"services": ["44733", "71623", "58485", "738", "161"], "reason": "Pod 44733 is the primary suspect as it exhibits a new error rate (0 -> 0.162) in logs with specific gRPC dialing errors, and its trace latency for the 'Convert' operation increased significantly (Δlog2 11.4). The topology graph identifies 44733 as the caller to services 12739, 24552, 29024, 33103, 36069, and 43969; since these callees are not shown with independent anomalies, the fault likely originates at or within 44733's local processing or network egress. Pods 71623 and 58485 show similar high-latency increases (Δlog2 ~11.3-11.4) for their respective operations ('GetCart'), suggesting they may be affected by the same underlying issue or are part of the same failing service group (Service 738), but lack the direct error logs seen in 44733.", "confidence": "medium"}
```

## INC-C46E27857BC0 / aiops2022
RR 0.0 -> 0.0
Accepted (private): ['node-5']

```json
{"services": ["31135", "80931", "274", "163", "303"], "reason": "The leading hypothesis is that pod 31135 (service 274) is the root cause, evidenced by a distinct error rate increase from baseline 5.19 to fault 5.24 and an event rate increase from 416 to 416 in the logs. This aligns with the trace data for operation 'SendOrderConfirmation' on entity 91437 (a member of service 163), which shows a significant latency spike (p95 3.34 -> 28.4 ms). The topology indicates 31135 calls 91437, suggesting 31135's failure propagates to 91437. An alternative explanation involving node-level resource exhaustion was considered but rejected; while nodes 1728 and 6111 show memory fluctuations, they do not exhibit the specific error patterns seen in 31135. The absence of direct metrics for 31135 introduces uncertainty, but the log evidence provides a concrete signal for its involvement.", "confidence": "medium"}
```

## INC-284EAF7B78B5 / aiops2022
RR 0.0 -> 0.0
Accepted (private): ['adservice']

```json
{"services": ["8448", "43483", "9357", "2557", "1712"], "reason": "Node 8448 is the primary root cause, exhibiting a sustained and simultaneous step-change anomaly in its filesystem metrics (disk.free, disk.used, fs.inodes.free) during the final portion of the observation window. This coincides with a sharp spike in container_cpu_cfs_throttled_seconds for Pod 43483 (a member of service 705), which acts as a downstream consumer of these resources; the throttling indicates the pod was starved due to the node-level resource exhaustion or I/O contention. While other nodes like 2557 show minor fluctuations and services 137/690 show trace latency changes, the magnitude and specificity of the Node 8448 storage anomalies provide the strongest causal evidence for the incident's origin.", "confidence": "high"}
```

## INC-4BA2D386B400 / aiops2022
RR 0.0 -> 0.0
Accepted (private): ['node-2']

```json
{"services": ["92497", "3045", "43286", "21457", "79816"], "reason": "Pod 92497 is the leading root cause because it exhibits a severe, sustained local resource failure: metrics M13 (node 4784) and M359 (node 4938) show memory pressure rising from ~55% to ~80%, while logs LT57 explicitly report 'FailedPrecondition' errors with a count of 25 for entity 92497. The topology graph confirms that multiple upstream services (18352, 21457, 25545, 79816, 83279) call into 92497, making its failure a likely origin point for downstream latency. While Pod 43286 also shows significant metric spikes (M01-M08), these appear concurrent or slightly subsequent to the onset of 92497's failure, suggesting propagation rather than independent causality. Node 3045 (service alias for pod 43286) is ranked second due to the high volume of traffic and latency shifts observed in its associated traces (R panel). The other candidates are included as lower-likelihood alternatives given the lack of unique exonerating evidence for all nodes in the cluster.", "confidence": "medium"}
```

## INC-0BD935F7BAAE / aiops2022
RR 1.0 -> 1.0
Accepted (private): ['emailservice-1']

```json
{"services": ["68063", "25190", "460", "716", "681"], "reason": "The leading hypothesis is that Pod 68063 (Service 460) is the root cause due to a massive, sustained resource exhaustion event. Metrics M02 and M03 for Pod 68063 show container CPU usage spiking from a baseline of ~0.02s to a peak of 15.2s, representing a >700x increase. This coincides with Log LT64 for entity 68063 reporting an 'Exception while exporting Span batch', indicating the service was overwhelmed. While Node 9174 shows disk capacity changes (M04-M08), these are likely secondary or unrelated as they do not align temporally with the CPU spike in 68063. The topology shows 68063 is called by 42320 and 60562; the high latency on 68063 would propagate to callers, but the exclusive latency increase is most pronounced at the source. Pod 25190 (Service 681) is ranked second as it shares the same upstream caller (42320) and might be affected by similar load or co-located issues, though its specific metrics are less dramatic than 68063's.", "confidence": "high"}
```

## INC-2833D299D245 / aiops2022
RR 0.0 -> 0.0
Accepted (private): ['recommendationservice-0']

```json
{"services": ["347", "62419", "34899", "73454", "341"], "reason": "The telemetry indicates a latency degradation originating from service 347 (hipstershop.347). The topology shows service 347 calling pods 62419 and 87866. Traces for pod 62419 (associated with operation hipstershop.969) show an increase in exclusive p95 latency from 24.3 ms to 48.4 ms, while the caller service 347's operation (hipstershop.347/Charge) also shows increased latency (implied by the flow, though specific trace rows for 347 are not explicitly detailed in the R card, the logs link them). Metrics for node 3419 (hosting or related to these services based on ID proximity in the candidate list, though strictly 341 is a separate candidate) show network byte spikes (M03, M04) and memory drops (M363), suggesting resource contention. The log template LT247 owned by entity 87866 (pod of service 347) records 'Charge invoked' events with variable summaries indicating high volume. The rise in exclusive latency at the callee level (pod 62419) combined with the network pressure on the associated infrastructure suggests the root cause is the service logic or resource usage within service 347/pod 62419 rather than an upstream caller.", "confidence": "medium"}
```

## INC-35164E740447 / aiops2022
RR 0.0 -> 0.0
Accepted (private): ['node-4']

```json
{"services": ["38624", "12931", "53127", "41388", "1550"], "reason": "Pod 38624 (hipstershop.807) exhibits the most severe and direct degradation: trace exclusive p95 latency for GetSupportedCurrencies spiked from a baseline of 2.38 ms to 56.6k ms, representing a massive local delay (Δlog2 14.5). This is corroborated by its Istio metrics showing request bytes increasing from 0 to 1.75k and duration from 0 to 296k ms. The topology indicates 38624 calls 80771, which in turn calls 53127; while 53127 shows increased traffic (M01/M02), its extreme latency is not explicitly shown in the provided R section, making 38624's local spike the primary evidence of fault. Pod 12931 and 41388 are secondary suspects as they also call 80771 and show 'failed to retrieve ads' errors, but their specific latency spikes are less pronounced than 38624's.", "confidence": "medium"}
```

## INC-C88979DF4D19 / aiops2022
RR 1.0 -> 1.0
Accepted (private): ['checkoutservice']

```json
{"services": ["37956", "38128", "73449", "49346", "63706"], "reason": "Pod 37956 (service 858) is the primary suspect because it exhibits the largest absolute increase in exclusive p95 latency (baseline ~2.26ms to current ~933ms, Δlog2 8.69) for the ShipOrder operation, as seen in the R panel. The M panel confirms this with a sharp spike in request duration metrics (M07/M08) for Pod 37956. While Pods 38128 and 73449 also show significant latency degradation (~933ms), their baseline latencies were slightly higher or comparable, making 37956's relative deviation more extreme. The G panel shows that 37956 is called by 51750 and calls downstream services; however, since its own local latency exploded, it is likely the origin of the delay rather than a victim of downstream issues, unless the downstream services (49346/63706) failed simultaneously. No error logs are present for 37956, suggesting a resource exhaustion or hang rather than a crash, which aligns with high latency but low error rates.", "confidence": "medium"}
```

## INC-E1E599C9691A / aiops2022
RR 0.25 -> 0.0
Accepted (private): ['recommendationservice']

```json
{"services": ["363", "761", "20523", "29113", "33631"], "reason": "Service 363 is the leading root cause due to a massive, sustained increase in `jvm_classes_loaded` (M04) from a baseline of 0 to a peak of 5.18k, indicating a severe resource exhaustion or classloader leak that likely degrades performance. This is supported by Service 761, which shows a significant drop in garbage collection efficiency (M01), with `memoryUsageBeforeGc` dropping sharply, potentially a consequence of the system-wide stress. Pod 20523 (a member of service 363 per the NAME GROUPS strip) is ranked third as a specific instance exhibiting these symptoms. Pods 29113 and 33631 are also members of service 363 and are included as plausible alternatives if the fault is distributed across the service's replicas rather than isolated to a single pod.", "confidence": "medium"}
```

## INC-AEB63063B99C / aiops2022
RR 0.3333333333333333 -> 0.5
Accepted (private): ['frontend']

```json
{"services": ["40393", "25855", "13347", "44256", "8377"], "reason": "Pod 40393 is the leading root cause candidate because it is the terminal callee in the topology (receiving calls from 25855 and 13347) and exhibits a significant spike in network receive traffic (M06, container_network_receive_MB.eth0), suggesting resource saturation or processing failure. This aligns with the logs for entity 44256 (a peer pod of service 596) showing NullPointerExceptions and increased error rates, which may be propagated downstream to 40393. The traces show elevated exclusive latency for operations associated with the upstream services (63713, 98023), consistent with a bottleneck at the 40393 endpoint. Node 8377 shows high IO utilization metrics (M01-M05), but as a physical node, its impact on specific pods is less direct than the explicit network anomaly seen on 40393.", "confidence": "medium"}
```

## INC-877AD157CB24 / aiops2022
RR 0.0 -> 0.0
Accepted (private): ['node-5']

```json
{"services": ["64331", "70893", "28633", "43068", "95175"], "reason": "The telemetry indicates a network-level failure originating from the gRPC endpoint associated with entity 64331. Log templates LT254 and LT253, owned by 64331, explicitly report 'transport: Error while dialing' and 'i/o timeout', which are definitive signs of connectivity loss to that specific callee. This aligns with the topology (G) showing 64331 as a downstream dependency of callers 73701 and 81028. The observed increase in exclusive latency for these callers (R) is consistent with the time spent waiting for or failing to reach 64331. While the trace counts have decreased (possibly due to connection failures), the explicit transport errors in the logs provide the strongest evidence for 64331 as the root cause of the incident.", "confidence": "high"}
```

## INC-492AFB4CE9D6 / aiops2025
RR 0.25 -> 0.25
Accepted (private): ['checkoutservice', 'cartservice']

```json
{"services": ["27701", "65309", "55138", "751", "1893"], "reason": "The primary evidence points to a resource contention or failure on Pod 27701, which is grouped under Service 639. Log LT1623 for entity 27701 explicitly reports 'Background saving terminated with success' followed by a volume drop signal (volume_drop_x30:0.90) and an event rate decrease from 0.89 to 0.8. This coincides temporally with the metrics in the M section showing spikes in rtt_max for Pods 55138 and 65309 (grouped under Service 688) and pod_cpu_usage for Pod 96506 (Service 868). While the topology shows Service 751 as a central caller, its exclusive latency change is minimal (Δlog2 0.58), suggesting it may be experiencing downstream delays rather than being the origin. The specific log termination event on 27701 provides a concrete causal trigger distinct from the general latency spikes seen elsewhere.", "confidence": "medium"}
```

## INC-C6AD1614BF41 / aiops2025
RR 0.25 -> 0.25
Accepted (private): ['checkoutservice', 'paymentservice']

```json
{"services": ["852", "14361", "15391", "767", "155"], "reason": "The leading hypothesis is that service 852 is the root cause, evidenced by a sustained and significant increase in its client_error_ratio metric (M08), which rose from a baseline of ~0.004 to a peak of 1.07. This error spike correlates temporally with an increase in 'request error' logs for pod 14361 (LT736) and pod 84506 (LT736), both members of service 852 per the topology groups. The trace data shows service 767 experiencing massive latency degradation (p95 121ms -> 4.08k ms) and count drops, but as a caller to 852, this is likely a downstream effect of the errors originating in 852. Alternative explanations involving infrastructure nodes (e.g., node 3809 or 4226 showing memory spikes) are less likely because the specific application-level error metrics and logs are concentrated on service 852's components.", "confidence": "medium"}
```

## INC-56FC27993C6C / aiops2025
RR 1.0 -> 0.0
Accepted (private): ['node-6']

```json
{"services": ["335", "711", "409", "212", "725"], "reason": "The telemetry indicates a localized latency fault originating at service 335. The trace data (R) shows that the exclusive p95 latency for operation '538.335/Charge' owned by entity 335 increased significantly from 46.1ms to 60.4ms (a Δlog2 of 0.39), representing the largest relative increase among all displayed operations. In contrast, downstream services in the topology graph (G), such as 711 and 725, show negligible changes in their own exclusive latency (Δlog2 < 0.25). Since exclusive latency represents local processing time after child calls are subtracted, the significant rise in 335's local delay suggests it is the root cause rather than being delayed by its callees. No other services or nodes exhibit comparable metric anomalies or error spikes that would suggest an alternative origin.", "confidence": "high"}
```

## INC-D142F47FE539 / aiops2025
RR 1.0 -> 1.0
Accepted (private): ['tidb-tikv', 'tidb-tikv-0']

```json
{"services": ["250", "893", "1461", "17272", "18625"], "reason": "Service 250 is the leading candidate due to a sustained, sharp spike in write_wal_mbps (M05) reaching a peak of 2.62k against a base of 19.7, indicating significant I/O load or WAL pressure. Service 893 shows correlated anomalies with spikes in block_cache_size (M03), duration_99th (M02), and duration_avg (M01), suggesting it may be impacted by or contributing to the same storage subsystem issue. Node 1461 exhibits elevated CPU usage (M391) and memory usage (M66) that temporally aligns with the service-level latency increases, providing a plausible infrastructure-level root cause for the observed degradation. Pods 17272 and 18625 are included as lower-ranked alternatives; pod 17272 shows an rrt_max spike (M08) consistent with the latency issues seen in its parent services, while pod 18625 shows a working set increase (M04). The topology (G) confirms call edges between these services (e.g., 906 -> 627, 397 -> 444), supporting the propagation of latency from the storage-heavy operations.", "confidence": "medium"}
```

## INC-0917F17160F5 / aiops2025
RR 0.0 -> 0.0
Accepted (private): ['tidb-tikv', 'tidb-tikv-0']

```json
{"services": ["3699", "52111", "66241", "73683", "81382"], "reason": "Node 3699 is the leading root-cause hypothesis due to a distinct, sustained spike in node_disk_read_bytes_total (M04) and node_disk_read_time_seconds_total (M05) that occurs simultaneously with a sharp peak in pod_memory_working_set_bytes for Pod 52111 (M01), Pod 66241 (M02), and Pod 73683 (M07). The co-occurrence of heavy disk I/O at the node level and memory pressure across multiple pods suggests an underlying storage or resource contention issue on Node 3699. While other nodes show minor fluctuations, only Node 3699 exhibits this specific multi-metric anomaly pattern. Confidence is medium because there are no explicit call edges provided in the topology section to definitively link the pod-level impact back to the node's disk activity, but the temporal correlation is strong.", "confidence": "medium"}
```

## INC-2B399A2FAEB2 / aiops2025
RR 0.0 -> 0.0
Accepted (private): ['tidb-tidb', 'tidb-tidb-0']

```json
{"services": ["23106", "851", "405", "961", "57877"], "reason": "The leading hypothesis is that pod 23106 (a member of service 851) is the root cause. The telemetry shows a specific error spike for entity 23106 (LT991) with an error rate jumping from a baseline of 1.31 to 24.4, while its event volume drops significantly (volume_drop x30). This indicates a high-frequency failure in this specific component. In the topology, service 405 calls service 851. Service 405 exhibits a massive latency regression (exclusive p95 increased by 13.2x to 129k ms) and a drop in request count, consistent with being blocked or timing out due to the downstream failure in 851/23106. Service 961 also shows increased latency and errors, likely propagating from the same source or related infrastructure issues, but 23106's specific error surge makes it the primary suspect.", "confidence": "medium"}
```

## INC-CDE4651C6884 / aiops2025
RR 1.0 -> 1.0
Accepted (private): ['frontend', 'adservice']

```json
{"services": ["93546", "83675", "945", "27811", "139"], "reason": "The telemetry indicates a distinct failure in service 945, manifested by its member pods 93546 and 83675. The log panel (L) explicitly identifies these two pods with 'failed to retrieve ads' errors and shows a sharp increase in error rates from a baseline of 0 to fault levels of 36.4 and 28.7 respectively. This represents the most significant deviation from baseline across all candidates. While the trace panel (R) shows a doubling of exclusive p95 latency for service 619 (22.4ms to 47.5ms), this is less severe than the hard failures seen in 945. Service 139 shows only minor latency fluctuations and no corresponding error logs, making it a lower-probability root cause compared to the clear evidence of failure in 945's pod members.", "confidence": "high"}
```

## INC-7BABC3F333B2 / aiops2025
RR 0.0 -> 0.0
Accepted (private): ['tidb-tikv', 'tidb-tikv-0']

```json
{"services": ["293", "57503", "149", "244", "174"], "reason": "Service 293 and its member pod 57503 (linked via the NAME GROUPS strip) exhibit a sharp, synchronized spike in client_error, error, and error_ratio metrics near the end of the observation window. This is corroborated by log entries for entity 97966 (a member of service 632, which is not in the candidate list but indicates broader system activity) showing a significant drop in event volume, potentially suggesting a failure mode or traffic shift. The topology shows Service 244 calling Service 293; however, traces for 244 show increased count and latency, while 293's error spike suggests it is the failing component causing upstream impact or reacting to an internal fault. Node 149 is ranked lower as a potential infrastructure cause due to resource constraints, though specific causal evidence is less direct than the application-level errors on 293/57503.", "confidence": "medium"}
```

## INC-4DBB272354A5 / aiops2025
RR 1.0 -> 1.0
Accepted (private): ['recommendationservice', 'productcatalogservice']

```json
{"services": ["337", "28096", "14520", "228", "334"], "reason": "Service 337 is the leading hypothesis because it exhibits a massive latency regression (exclusive p95 increasing from 6.45ms to 60k ms, a Δlog2 of 13.2) while its request count remains relatively stable. This extreme local delay aligns with the topology where service 337 is a callee for services 455 and 858, which then call service 228; the propagation of this latency likely causes the secondary slowdown observed in service 228. Pod 28096 (a member of service 455) shows corresponding metric anomalies, including a significant spike in rrt_max (up to 60M) and an increase in server errors, supporting the view that the 455/337 interaction is the primary fault point. Service 228 and 334 are ranked lower as they appear to be downstream victims or less severe contributors with smaller latency shifts.", "confidence": "high"}
```

## INC-6CB61FBD3E4F / aiops2025
RR 0.5 -> 0.5
Accepted (private): ['currencyservice']

```json
{"services": ["836", "243", "570", "12223", "953"], "reason": "The leading hypothesis is that Service 836 is the root cause. Evidence from R (Traces) shows Service 836's 'PlaceOrder' operation experienced a massive increase in exclusive p95 latency (68.7ms to 677k ms, Δlog2 13.3), indicating local processing delay rather than just waiting on downstream dependencies. This is corroborated by L (Logs), which reports new errors for entity 88974 (a pod of Service 836) with messages about 'Maximum call stack size exceeded'. While Service 243 also shows high latency increases, its magnitude (5.38 to 59.9k ms) is significantly lower than 836's, and the topology suggests 836 calls 243, making 243 a likely victim of 836's slowness or vice versa, but the specific error logs tied to 836's pod make it the stronger candidate. Service 570 is ranked third due to moderate latency increases. Pod 12223 (Service 243) is included as a plausible alternative if the fault is isolated to a specific instance within the service, though service-level metrics suggest a broader issue. Service 953 is a lower-ranked alternative callee.", "confidence": "medium"}
```

## INC-CB91FA13504C / aiops2025
RR 1.0 -> 1.0
Accepted (private): ['shippingservice']

```json
{"services": ["59167", "890", "20845", "91186", "18962"], "reason": "The evidence points to a latency and resource anomaly originating from Pod 59167. Metric M04 (POD 59167) shows a significant spike in 'rtr' (likely round-trip time or similar latency metric) reaching a peak of 31k compared to a baseline of 1.43k, which is an order-of-magnitude increase. This aligns with the topology in G, where Service 686 groups Pod 59167. While Service 890 (grouping Pods 53928, 77181, 78524) also shows elevated metrics (M08 rtr_max peak 55.5k), the specific, sharp spike in Pod 59167's local telemetry makes it the most likely root cause for its own degradation, potentially propagating to the service level if they are related (though no direct call edge is shown). The logs (L) show high volume counts (349) for entity 77181 (a member of Service 890) but marked as 'level unknown', which is less definitive than the clear metric deviation in 59167. Other candidates like Node 4552 (M205 memory jump) show changes, but the pod-level latency spike is a more direct indicator of application-level failure.", "confidence": "medium"}
```

## INC-6678662095B6 / aiops2025
RR 0.0 -> 0.0
Accepted (private): ['node-6']

```json
{"services": ["235", "100", "245", "894", "877"], "reason": "The telemetry indicates a localized performance degradation originating at service 235. The trace data for operation '692.235/SendOrderConfirmation' shows the most significant deviation from baseline, with exclusive p95 latency increasing by a factor of approximately 1.12 (Δlog2 0.17) and a substantial drop in request count (Δlog2 -1.26), suggesting a throughput bottleneck or resource exhaustion specific to this service. While upstream caller 100 also exhibits increased latency (Δlog2 0.05) and reduced volume, its local delay is less severe than that of 235, indicating it is likely experiencing propagated impact rather than being the primary source of failure. No infrastructure-level anomalies (CPU, memory, disk) are observed on the nodes hosting these services, supporting a software-layer root cause. Service 245 and others show negligible changes, placing them lower in likelihood.", "confidence": "medium"}
```
