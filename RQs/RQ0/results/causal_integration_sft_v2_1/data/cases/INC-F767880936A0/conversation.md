# System

You are an expert Site Reliability Engineer performing Root Cause Analysis (RCA) for a microservice application deployed on a Kubernetes cluster. A fault has occurred in the system. Your task is to identify the root cause of the incident.

Root causes can occur at three levels:
- Pod level: a specific container replica (e.g., "cartservice-0")
- Service level: a microservice type (e.g., "paymentservice") — predict any pod of that service
- Node level: an infrastructure host (e.g., "node-6") — nodes appear as isolated entities with system metrics (CPU, memory, network, disk) but no application logs or traces

The system consists of multiple services communicating over HTTP/gRPC, running on shared infrastructure nodes. A fault in one component (pod, service, or node) can propagate to dependent components, causing them to appear degraded even though they are not the root cause.

Node-level faults (e.g., host memory exhaustion, CPU saturation, disk I/O) often manifest as correlated anomalies across multiple pods. If several unrelated pods show simultaneous degradation and a node shows critical system-level metrics, the node is likely the root cause.

Focus on distinguishing the ORIGIN of the fault from its SYMPTOMS in downstream or co-located components.

# User

[image: dashboard.png]

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
opaque_id: INC-F767880936A0
observation_window={"duration_rel_s":2340.0,"source_metric_rows":40}
selection_summary={"candidate_count":63,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":1535,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","adservice-grpc","adservice-http","adservice2","adservice2-0","cartservice-0","cartservice-1","cartservice-2","cartservice-grpc","cartservice2-0","checkoutservice-0","checkoutservice-1","checkoutservice-2","checkoutservice-grpc","checkoutservice2-0","currencyservice-0","currencyservice-1","currencyservice-2","currencyservice-grpc","currencyservice2-0","emailservice-0","emailservice-1","emailservice-2","emailservice-grpc","emailservice2-0","frontend-0","frontend-1","frontend-2","frontend-http","frontend2-0","istio-egressgateway-7bfdcc9d86-22q7z","istio-ingressgateway-565bffd4d-4nr6v","node-1","node-2","node-3","node-4","node-5","node-6","paymentservice-0","paymentservice-1","paymentservice-2","paymentservice-grpc","paymentservice2-0","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","productcatalogservice-grpc","productcatalogservice2-0","recommendationservice-0","recommendationservice-1","recommendationservice-2","recommendationservice-grpc","recommendationservice2-0","redis-cart-0","redis-cart2-0","shippingservice-0","shippingservice-1","shippingservice-2","shippingservice-grpc","shippingservice2-0"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[18.281,54.844,91.406,127.969,164.531,201.094,237.656,274.219,310.781,347.344,383.906,420.469,457.031,493.594,530.156,566.719,603.281,639.844,676.406,712.969,749.531,786.094,822.656,859.219,895.781,932.344,968.906,1005.469,1042.031,1078.594,1115.156,1151.719,1188.281,1224.844,1261.406,1297.969,1334.531,1371.094,1407.656,1444.219,1480.781,1517.344,1553.906,1590.469,1627.031,1663.594,1700.156,1736.719,1773.281,1809.844,1846.406,1882.969,1919.531,1956.094,1992.656,2029.219,2065.781,2102.344,2138.906,2175.469,2212.031,2248.594,2285.156,2321.719]
[M1] rank=1 service=adservice-1 metric=container_fs_inodes./dev/vda1 baseline=0.0 peak=1.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,-1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M2] rank=2 service=adservice-1 metric=container_memory_cache baseline=3773986.133333 peak=28258304.0 signed_z=999.0 onset_bin=36 onset_rel_s=1334.531 persistence_bins=18
values_compact=delta:3801088,0,0,0,0,0,-9557.333333,-31402.666667,0,0,0,0,0,0,0,0,0,0,0,0,24498176,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M3] rank=3 service=adservice-1 metric=container_memory_failures.container.pgfault baseline=10.241667 peak=80568.0 signed_z=999.0 onset_bin=36 onset_rel_s=1334.531 persistence_bins=5
values_compact=delta:8.333333,-2.333333,2,2,-2,21,-19,0,-4,2,0,1,-3,2,22,-20,-2,-1.333333,2.666666,-2.833333,74802.5,-73405,-1321.5,-5.5,80491,-80550.5,1,-11.166667,-0.666666,3.333333,30,-23.5,1,-10.5,1,2,-4,24,-22,2
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M4] rank=4 service=adservice-1 metric=container_memory_failures.hierarchy.pgfault baseline=10.241667 peak=80568.0 signed_z=999.0 onset_bin=36 onset_rel_s=1334.531 persistence_bins=5
values_compact=delta:8.333333,-2.333333,2,2,-2,21,-19,0,-4,2,0,1,-3,2,22,-20,-2,-1.333333,2.666666,-2.833333,74802.5,-73405,-1321.5,-5.5,80491,-80550.5,1,-11.166667,-0.666666,3.333333,30,-23.5,1,-10.5,1,2,-4,24,-22,2
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M5] rank=5 service=adservice-1 metric=container_memory_usage_MB baseline=152.35306 peak=308.738281 signed_z=999.0 onset_bin=36 onset_rel_s=1334.531 persistence_bins=18
values_compact=delta:152.378906,0,0,0,0,0,-0.009114,-0.029948,0,0,0,0,0,0,0,0,0,0,0,0,150.666015,5.335938,0.175781,0.220703,-132.339843,0.042968,-0.046875,0,0,0,0.046875,0.003906,-0.003906,-0.089844,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M6] rank=6 service=frontend2-0 metric=container_fs_reads_MB./dev/vda baseline=0.004102 peak=13.292969 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0.027344,-0.027344,0,0,0.054688,-0.054688,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,13.292969,-13.292969,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M7] rank=7 service=frontend2-0 metric=container_fs_reads./dev/vda baseline=0.1 peak=173.0 signed_z=576.333 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,1,-1,0,0,1,-1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,173,-173,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M8] rank=8 service=adservice-1 metric=container_fs_usage_MB./dev/vda1 baseline=22.710938 peak=26.707031 signed_z=433.604 onset_bin=36 onset_rel_s=1334.531 persistence_bins=18
values_compact=delta:22.710938,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,3.996093,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M9] rank=9 service=frontend2-0 metric=container_memory_cache baseline=11541504.0 peak=53248.0 signed_z=-299.691 onset_bin=62 onset_rel_s=2285.156 persistence_bins=2
values_compact=delta:11505664,0,0,0,0,0,0,0,0,28672,0,0,0,57344,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-11538432,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M10] rank=10 service=emailservice2-0 metric=container_network_receive_MB.eth0 baseline=0.022842 peak=0.545914 signed_z=252.288 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.024448,-0.000273,0.002337,-0.007263,0.00286,-0.003792,0.00274,0,0.000947,0.001184,-0.000913,0.001642,0.00311,-0.004574,-0.001313,0.00134,0.000803,0.000977,-0.000664,0.00069,-0.002573,0.002891,-0.000773,0.004571,-0.007392,-0.001692,0.00487,-0.000521,0.522247,-0.519827,-0.002557,-0.003906,0.007702,-0.006495,0.002031,0.000301,0.000465,0.001688,-0.001392,0.001144
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M11] rank=11 service=currencyservice-0 metric=container_memory_mapped_file baseline=233062.4 peak=520192.0 signed_z=233.667 onset_bin=49 onset_rel_s=1809.844 persistence_bins=10
values_compact=delta:229376,0,4096,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,133120,133120,0,10240,10240,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M12] rank=12 service=emailservice-2 metric=container_memory_mapped_file baseline=4096.0 peak=8192.0 signed_z=227.128 onset_bin=36 onset_rel_s=1334.531 persistence_bins=2
values_compact=delta:4096,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,4096,0,0,0,-4096,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[1140.0,2340.0]

=== LOG SUMMARY ===
{"entries":[{"change_pct":21.6,"n_during":203,"n_pre":167,"service":"paymentservice-0"},{"change_pct":20.3,"n_during":22373,"n_pre":18599,"service":"frontend-0"},{"change_pct":20.0,"n_during":198,"n_pre":165,"service":"emailservice-1"},{"change_pct":19.8,"n_during":1115,"n_pre":931,"service":"checkoutservice-1"},{"change_pct":19.1,"n_during":1124,"n_pre":944,"service":"checkoutservice-0"},{"change_pct":17.0,"n_during":200,"n_pre":171,"service":"emailservice-0"},{"change_pct":14.7,"n_during":2008,"n_pre":1750,"service":"adservice-1"},{"change_pct":14.5,"n_during":2006,"n_pre":1752,"service":"adservice-0"}],"mode":"volume","omitted_services":23,"service_count":31}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":130.6,"error_pct":0.0,"p95_during_ms":12.39869999999997,"p95_pre_ms":5.37725,"service":"paymentservice2-0","spans":78},{"delta_pct":7.3,"error_pct":0.0,"p95_during_ms":0.07889999999999998,"p95_pre_ms":0.07354999999999995,"service":"shippingservice-1","spans":873},{"delta_pct":6.6,"error_pct":0.0,"p95_during_ms":0.0842,"p95_pre_ms":0.079,"service":"shippingservice2-0","spans":551},{"delta_pct":-6.4,"error_pct":0.0,"p95_during_ms":41.00109999999999,"p95_pre_ms":43.81715,"service":"checkoutservice2-0","spans":914},{"delta_pct":5.3,"error_pct":0.0,"p95_during_ms":0.02,"p95_pre_ms":0.019,"service":"adservice-1","spans":1880},{"delta_pct":4.5,"error_pct":0.0,"p95_during_ms":0.24599999999999997,"p95_pre_ms":0.2355,"service":"emailservice-2","spans":123},{"delta_pct":3.9,"error_pct":0.0,"p95_during_ms":0.14959999999999998,"p95_pre_ms":0.14404999999999998,"service":"paymentservice-0","spans":122},{"delta_pct":3.8,"error_pct":0.0,"p95_during_ms":0.07784999999999996,"p95_pre_ms":0.075,"service":"shippingservice-0","spans":874}],"omitted_services":32,"service_count":40}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=15 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":1200.0,"rank":1,"service":"adservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1200.0,"rank":2,"service":"emailservice","severity_z":227.128},{"evidence_source":"metric","onset_rel_s":1320.0,"rank":3,"service":"node-5","severity_z":29.471},{"evidence_source":"metric","onset_rel_s":1440.0,"rank":4,"service":"checkoutservice","severity_z":65.454},{"evidence_source":"metric","onset_rel_s":1500.0,"rank":5,"service":"adservice2","severity_z":65.954},{"evidence_source":"metric","onset_rel_s":1500.0,"rank":6,"service":"recommendationservice2","severity_z":31.69},{"evidence_source":"metric","onset_rel_s":1500.0,"rank":7,"service":"recommendationservice","severity_z":26.882},{"evidence_source":"metric","onset_rel_s":1680.0,"rank":8,"service":"emailservice2","severity_z":252.288},{"evidence_source":"metric","onset_rel_s":1860.0,"rank":9,"service":"currencyservice","severity_z":233.667},{"evidence_source":"metric","onset_rel_s":1860.0,"rank":10,"service":"node-4","severity_z":177.066},{"evidence_source":"metric","onset_rel_s":1860.0,"rank":11,"service":"node-6","severity_z":74.353},{"evidence_source":"trace","onset_rel_s":2169.6,"rank":12,"service":"paymentservice2","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":2220.0,"rank":13,"service":"frontend2","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":2280.0,"rank":14,"service":"node-2","severity_z":30.477}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"currencyservice","caller":"checkoutservice"},{"callee":"emailservice","caller":"checkoutservice"},{"callee":"adservice2","caller":"frontend2"},{"callee":"recommendationservice2","caller":"frontend2"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"medium","reason":"Rank adservice-1 first because adservice-1 has direct container_fs_inodes./dev/vda1 evidence (signed-z 999, persistence 0 bins); emailservice-0 is second despite propagation rank 2 because onset ordering alone does not establish the causal origin. The remaining entries preserve evidence-supported alternatives so the ranking retains calibrated uncertainty instead of collapsing to one answer.","services":["adservice-1","emailservice-2","checkoutservice-1","checkoutservice-0","emailservice-0"]}
