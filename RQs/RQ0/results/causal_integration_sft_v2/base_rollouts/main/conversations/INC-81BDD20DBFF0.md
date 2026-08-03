# Causal SFT v2 base rollout — INC-81BDD20DBFF0

## System

You are an expert Site Reliability Engineer performing Root Cause Analysis (RCA) for a microservice application deployed on a Kubernetes cluster. A fault has occurred in the system. Your task is to identify the root cause of the incident.

Root causes can occur at three levels:
- Pod level: a specific container replica (e.g., "cartservice-0")
- Service level: a microservice type (e.g., "paymentservice") — predict any pod of that service
- Node level: an infrastructure host (e.g., "node-6") — nodes appear as isolated entities with system metrics (CPU, memory, network, disk) but no application logs or traces

The system consists of multiple services communicating over HTTP/gRPC, running on shared infrastructure nodes. A fault in one component (pod, service, or node) can propagate to dependent components, causing them to appear degraded even though they are not the root cause.

Node-level faults (e.g., host memory exhaustion, CPU saturation, disk I/O) often manifest as correlated anomalies across multiple pods. If several unrelated pods show simultaneous degradation and a node shows critical system-level metrics, the node is likely the root cause.

Focus on distinguishing the ORIGIN of the fault from its SYMPTOMS in downstream or co-located components.

## User

[image: RQs/RQ0/results/causal_integration_sft_v1/data/cases/INC-81BDD20DBFF0/dashboard.png]

Analyze this incident using only the supplied evidence. Rank the most likely
root-cause components, distinguishing the origin from propagated symptoms.

Evidence semantics shared by all representations:
- candidates are exhaustive and appear in a fixed alphabetical order;
- every metric has 64 equal-width bins from window start t=0; null means no
  observed sample in that bin and observed_count gives the number aggregated;
- shared_bin_centers_rel_s applies to all metric series; missing_mask_bits uses
  one bit per bin (1=missing, 0=observed); observed_counts_compact is either a
  comma-separated integer vector prefixed csv: or value*run pairs prefixed rle:;
- values_compact is lossless: raw: is a JSON vector, rle: is value*run pairs,
  and delta: stores the first observed value followed by cumulative deltas;
  missing_mask_bits restores null positions for delta encoding;
- signed_z is relative to the pre-incident baseline; onset and persistence are
  deterministic label-blind anomaly summaries;
- a directed edge A -> B means A calls B, so a disturbance in B can propagate
  back to A;
- propagation ranks are ordered by relative onset, not by causal likelihood;
- source t/trace and m/metric use different instruments and their z magnitudes
  must not be compared directly.


=== INCIDENT ===
schema_version: CanonicalEvidenceBundleV1
opaque_id: INC-81BDD20DBFF0
observation_window={"duration_rel_s":1920.0,"source_metric_rows":33}
selection_summary={"candidate_count":60,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":484,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","cartservice","cartservice-0","cartservice-1","cartservice-2","checkoutservice","checkoutservice-0","checkoutservice-1","checkoutservice-2","currencyservice","currencyservice-0","currencyservice-1","currencyservice-2","emailservice","emailservice-0","emailservice-1","emailservice-2","example-ant-10-29158080-vxbvl","example-ant-29158080-drlxt","frontend","frontend-0","frontend-1","frontend-2","hipstershop","k8s-master1","k8s-master2","k8s-master3","node-1","node-2","node-3","node-4","node-5","node-6","node-7","node-8","paymentservice","paymentservice-0","paymentservice-1","paymentservice-2","productcatalogservice","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","recommendationservice","recommendationservice-0","recommendationservice-1","recommendationservice-2","redis","redis-cart","redis-cart-0","shippingservice","shippingservice-0","shippingservice-1","shippingservice-2","tidb-pd","tidb-tidb","tidb-tikv"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[15.0,45.0,75.0,105.0,135.0,165.0,195.0,225.0,255.0,285.0,315.0,345.0,375.0,405.0,435.0,465.0,495.0,525.0,555.0,585.0,615.0,645.0,675.0,705.0,735.0,765.0,795.0,825.0,855.0,885.0,915.0,945.0,975.0,1005.0,1035.0,1065.0,1095.0,1125.0,1155.0,1185.0,1215.0,1245.0,1275.0,1305.0,1335.0,1365.0,1395.0,1425.0,1455.0,1485.0,1515.0,1545.0,1575.0,1605.0,1635.0,1665.0,1695.0,1725.0,1755.0,1785.0,1815.0,1845.0,1875.0,1905.0]
[M1] rank=1 service=hipstershop metric=client_error baseline=0.0 peak=12.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,12
missing_mask_bits=0101010101010101010101010101010101010101010101010101010101010100
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M2] rank=2 service=hipstershop metric=client_error_ratio baseline=0.0 peak=0.04 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.04
missing_mask_bits=0101010101010101010101010101010101010101010101010101010101010100
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M3] rank=3 service=shippingservice-1 metric=client_error baseline=0.0 peak=12.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,12
missing_mask_bits=0101010101010101010101010101010101010101111111111111111111111110
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1
[M4] rank=4 service=shippingservice-1 metric=client_error_ratio baseline=0.0 peak=33.33 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,33.33
missing_mask_bits=0101010101010101010101010101010101010101111111111111111111111110
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1
[M5] rank=5 service=shippingservice metric=client_error baseline=0.0 peak=12.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,12
missing_mask_bits=0101010101010101010101010101010101010101010101010101010101010100
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M6] rank=6 service=shippingservice metric=client_error_ratio baseline=0.0 peak=3.12 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,3.12
missing_mask_bits=0101010101010101010101010101010101010101010101010101010101010100
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M7] rank=7 service=tidb-tikv metric=raft_propose_wait baseline=0.0 peak=0.02 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.02,-0.02,0,0,0,0,0
missing_mask_bits=0101010101010101010101010101010101010101010101010101010101010100
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M8] rank=8 service=k8s-master2 metric=node_filesystem_free_bytes baseline=9520880128.0 peak=9588203520.0 signed_z=118.239 onset_bin=62 onset_rel_s=1875.0 persistence_bins=2
values_compact=delta:9521520640,0,-106496,466944,-466944,0,-1015808,0,0,-106496,20480,1032192,-1011712,0,462848,-483328,0,1007616,-1007616,0,28672,0,-73728,983040,-1024000,40960,-131072,0,67067904,999424,-999424,-65536,0
missing_mask_bits=0101010101010101010101010101010101010101010101010101010101010100
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M9] rank=9 service=k8s-master2 metric=node_filesystem_usage_rate baseline=35.134687 peak=35.005 signed_z=-107.153 onset_bin=62 onset_rel_s=1875.0 persistence_bins=2
values_compact=delta:35.135,0,0,-0.005,0.005,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-0.13,0,0,0,0
missing_mask_bits=0101010101010101010101010101010101010101010101010101010101010100
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M10] rank=10 service=emailservice metric=rrt_max baseline=5626.3125 peak=65951.0 signed_z=35.146 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:9540,-5682,4479,-3534,976,-1495,-494,1003,-669,3393,-442,-1264,795,-2629,1878,-1983,-82,2603,3126,-4184,4107,-5307,61816,-59990,1676,-415,-2258,1259,2963,-674,1463,-4034,-2841
missing_mask_bits=0101010101010101010101010101010101010101010101010101010101010100
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M11] rank=11 service=emailservice-1 metric=rrt_max baseline=4059.75 peak=65951.0 signed_z=34.215 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:9540,-6537,1881,-1757,132,837,-620,-278,-2,4321,-5062,759,-184,947,-147,-676,-38,310,515,-224,-460,454,62240,-62816,-256,17,2068,-1067,5289,-3871,-1684,2310,-2886
missing_mask_bits=0101010101010101010101010101010101010101010101010101010101010100
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M12] rank=12 service=node-1 metric=node_disk_write_time_seconds_total baseline=0.0 peak=0.01 signed_z=11.016 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.01,-0.01,0,0,0,0,0,0,0,0.01,-0.01,0,0,0,0,0.01
missing_mask_bits=0101010101010101010101010101010101010101010101010101010101010100
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[1140.0,1920.0]

=== LOG SUMMARY ===
{"entries":[{"error_logs":4,"error_pct":0.04,"service":"frontend-1","total_logs":11303},{"error_logs":2,"error_pct":0.01,"service":"frontend-2","total_logs":15593},{"error_logs":1,"error_pct":0.01,"service":"frontend-0","total_logs":11509}],"mode":"errors","omitted_services":19,"service_count":22}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":15.3,"error_pct":0.0,"p95_during_ms":2.273799999999994,"p95_pre_ms":1.9726499999999998,"service":"redis","spans":13141},{"delta_pct":12.2,"error_pct":0.0,"p95_during_ms":3.7565999999999984,"p95_pre_ms":3.3492,"service":"cartservice","spans":12124},{"delta_pct":-9.6,"error_pct":0.0,"p95_during_ms":0.41010000000000013,"p95_pre_ms":0.45359999999999995,"service":"shippingservice","spans":3522},{"delta_pct":-6.5,"error_pct":0.0,"p95_during_ms":1.0489999999999997,"p95_pre_ms":1.1217999999999984,"service":"emailservice","spans":495},{"delta_pct":-3.1,"error_pct":0.0,"p95_during_ms":125.34649999999999,"p95_pre_ms":129.3525,"service":"checkoutservice","spans":5872},{"delta_pct":-0.8,"error_pct":0.0,"p95_during_ms":5.041899999999999,"p95_pre_ms":5.081,"service":"recommendationservice","spans":18190},{"delta_pct":0.6,"error_pct":0.0,"p95_during_ms":87.021,"p95_pre_ms":86.477,"service":"frontend","spans":148007},{"delta_pct":0.3,"error_pct":0.0,"p95_during_ms":14.337349999999999,"p95_pre_ms":14.294099999999998,"service":"productcatalogservice","spans":68413}],"omitted_services":0,"service_count":8}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=7 omitted_edges=1
[{"evidence_source":"metric","onset_rel_s":1020.0,"rank":1,"service":"node-1","severity_z":11.016},{"evidence_source":"metric","onset_rel_s":1320.0,"rank":2,"service":"emailservice","severity_z":35.146},{"evidence_source":"metric","onset_rel_s":1560.0,"rank":3,"service":"tidb-tikv","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1680.0,"rank":4,"service":"k8s-master2","severity_z":118.239},{"evidence_source":"trace","onset_rel_s":1819.8,"rank":5,"service":"redis","severity_z":9.344},{"evidence_source":"trace","onset_rel_s":1819.8,"rank":6,"service":"cartservice","severity_z":7.307},{"evidence_source":"metric","onset_rel_s":1920.0,"rank":7,"service":"hipstershop","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1920.0,"rank":8,"service":"shippingservice","severity_z":999.0},{"evidence_source":"none","onset_rel_s":null,"rank":9,"service":"adservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":10,"service":"tidb-tidb","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":11,"service":"currencyservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":12,"service":"productcatalogservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":13,"service":"recommendationservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":14,"service":"k8s-master1","severity_z":0.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"redis","caller":"cartservice"},{"callee":"productcatalogservice","caller":"recommendationservice"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

## Assistant

{
"services": [
"node-1",
"emailservice",
"emailservice-1"
],
"reason": "node-1 is the root cause because it exhibits the earliest anomaly onset (1020s) with disk write time spikes, which precedes the latency degradation in emailservice (1320s) and subsequent cascading failures in dependent services.",
"confidence": "high"
}
