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
opaque_id: INC-8BFCFB2E5E54
observation_window={"duration_rel_s":2340.0,"source_metric_rows":40}
selection_summary={"candidate_count":63,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":1379,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","adservice-grpc","adservice-http","adservice2","adservice2-0","cartservice-0","cartservice-1","cartservice-2","cartservice-grpc","cartservice2-0","checkoutservice-0","checkoutservice-1","checkoutservice-2","checkoutservice-grpc","checkoutservice2-0","currencyservice-0","currencyservice-1","currencyservice-2","currencyservice-grpc","currencyservice2-0","emailservice-0","emailservice-1","emailservice-2","emailservice-grpc","emailservice2-0","frontend-0","frontend-1","frontend-2","frontend-http","frontend2-0","istio-egressgateway-7bfdcc9d86-22q7z","istio-ingressgateway-565bffd4d-4nr6v","node-1","node-2","node-3","node-4","node-5","node-6","paymentservice-0","paymentservice-1","paymentservice-2","paymentservice-grpc","paymentservice2-0","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","productcatalogservice-grpc","productcatalogservice2-0","recommendationservice-0","recommendationservice-1","recommendationservice-2","recommendationservice-grpc","recommendationservice2-0","redis-cart-0","redis-cart2-0","shippingservice-0","shippingservice-1","shippingservice-2","shippingservice-grpc","shippingservice2-0"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[18.281,54.844,91.406,127.969,164.531,201.094,237.656,274.219,310.781,347.344,383.906,420.469,457.031,493.594,530.156,566.719,603.281,639.844,676.406,712.969,749.531,786.094,822.656,859.219,895.781,932.344,968.906,1005.469,1042.031,1078.594,1115.156,1151.719,1188.281,1224.844,1261.406,1297.969,1334.531,1371.094,1407.656,1444.219,1480.781,1517.344,1553.906,1590.469,1627.031,1663.594,1700.156,1736.719,1773.281,1809.844,1846.406,1882.969,1919.531,1956.094,1992.656,2029.219,2065.781,2102.344,2138.906,2175.469,2212.031,2248.594,2285.156,2321.719]
[M1] rank=1 service=adservice2 metric=java_lang_Memory_ObjectPendingFinalizationCount baseline=0.0 peak=0.666667 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.666667,-0.666667,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M2] rank=2 service=adservice metric=java_lang_Memory_ObjectPendingFinalizationCount baseline=0.0 peak=1.75 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.166667,-0.166667,0,0,0,0,0,0,0,0,0,0,0,0,1.75
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M3] rank=3 service=checkoutservice-0 metric=container_cpu_cfs_throttled_seconds baseline=0.174937 peak=656.438403 signed_z=999.0 onset_bin=36 onset_rel_s=1334.531 persistence_bins=8
values_compact=delta:0,0.37283,-0.213398,0.181722,-0.304216,0.140119,0.022085,0.006673,-0.07099,-0.00596,0.075194,-0.054911,-0.084545,0.030775,-0.080654,0.227945,-0.126684,0.119613,-0.059519,0.268356,314.048224,263.293349,78.652395,-223.596419,0,110.106151,82.7758,-106.675085,-415.559186,-100.6546,-2.484938,0.003856,-0.243648,0.076112,-0.067885,0.027655,0.054538,-0.069694,-0.037485,0.039556
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M4] rank=4 service=checkoutservice-0 metric=container_fs_inodes./dev/vda1 baseline=0.0 peak=1.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,-1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M5] rank=5 service=checkoutservice-0 metric=container_fs_writes./dev/vda baseline=0.0 peak=9.0 signed_z=999.0 onset_bin=44 onset_rel_s=1627.031 persistence_bins=2
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,9,-9,0,0,0,0,0,1.5,0,-1.5,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M6] rank=6 service=checkoutservice-0 metric=container_fs_writes_MB./dev/vda baseline=0.0 peak=0.085938 signed_z=999.0 onset_bin=44 onset_rel_s=1627.031 persistence_bins=2
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.085938,-0.085938,0,0,0,0,0,0.013672,0,-0.013672,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M7] rank=7 service=checkoutservice-0 metric=container_memory_mapped_file baseline=274432.0 peak=7944192.0 signed_z=999.0 onset_bin=36 onset_rel_s=1334.531 persistence_bins=18
values_compact=delta:274432,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,348160,0,0,0,0,0,0,7321600,-5271552,40277.333333,43690.666667,8192,12288,8192,6144,6144,2730.666667,1365.333333,0,2048
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M8] rank=8 service=checkoutservice-1 metric=container_cpu_cfs_throttled_seconds baseline=0.178051 peak=730.813018 signed_z=999.0 onset_bin=31 onset_rel_s=1151.719 persistence_bins=11
values_compact=delta:0.308392,-0.035172,-0.27322,0.219855,0.02184,-0.130035,-0.042578,0.116547,-0.053173,0.043844,0.044767,-0.122344,0.031096,0.020992,-0.01176,0.049142,-0.08089,0.092229,-0.122779,0.454717,386.159898,30.528882,52.389138,202.986209,0,58.217421,-375.000044,137.225624,-416.65038,-73.90031,-2.157342,-0.004199,-0.168925,0.135294,-0.223662,0.029071,0.147425,-0.078138,-0.026808,-0.047453
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M9] rank=9 service=checkoutservice-1 metric=container_fs_inodes./dev/vda1 baseline=0.0 peak=0.5 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.5,0,-0.5,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M10] rank=10 service=checkoutservice-1 metric=container_fs_writes./dev/vda baseline=0.0 peak=8.0 signed_z=999.0 onset_bin=44 onset_rel_s=1627.031 persistence_bins=2
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,8,-8,0,0,0,0,0,1.5,0,-1.5,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M11] rank=11 service=checkoutservice-1 metric=container_fs_writes_MB./dev/vda baseline=0.0 peak=0.085938 signed_z=999.0 onset_bin=44 onset_rel_s=1627.031 persistence_bins=2
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.085938,-0.085938,0,0,0,0,0,0.013672,0,-0.013672,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M12] rank=12 service=checkoutservice-1 metric=container_memory_mapped_file baseline=110592.0 peak=1826816.0 signed_z=999.0 onset_bin=44 onset_rel_s=1627.031 persistence_bins=13
values_compact=delta:110592,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-4096,0,0,0,0,0,0,802816,847872,30720,12970.666667,5461.333333,2048,2048,0,4096,8192,2048,2048,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[1140.0,1680.0]

=== LOG SUMMARY ===
{"entries":[{"change_pct":-72.1,"n_during":135,"n_pre":484,"service":"paymentservice-0"},{"change_pct":-72.0,"n_during":129,"n_pre":461,"service":"emailservice-1"},{"change_pct":-71.7,"n_during":6913,"n_pre":24459,"service":"frontend-0"},{"change_pct":-71.4,"n_during":749,"n_pre":2617,"service":"checkoutservice-2"},{"change_pct":-71.4,"n_during":1170,"n_pre":4091,"service":"shippingservice-0"},{"change_pct":-71.3,"n_during":1169,"n_pre":4075,"service":"shippingservice-1"},{"change_pct":-71.1,"n_during":12201,"n_pre":42191,"service":"productcatalogservice-0"},{"change_pct":-71.0,"n_during":11061,"n_pre":38118,"service":"cartservice-1"}],"mode":"volume","omitted_services":23,"service_count":31}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":3116.9,"error_pct":0.0,"p95_during_ms":1318.9972999999993,"p95_pre_ms":41.002199999999995,"service":"checkoutservice-2","spans":2382},{"delta_pct":2910.5,"error_pct":0.0,"p95_during_ms":1206.5057499999998,"p95_pre_ms":40.076849999999986,"service":"checkoutservice-1","spans":2418},{"delta_pct":2646.4,"error_pct":0.0,"p95_during_ms":1105.4293999999984,"p95_pre_ms":40.2498,"service":"checkoutservice-0","spans":2420},{"delta_pct":45.5,"error_pct":0.0,"p95_during_ms":0.22699999999999984,"p95_pre_ms":0.156,"service":"paymentservice-0","spans":205},{"delta_pct":30.4,"error_pct":0.0,"p95_during_ms":0.206,"p95_pre_ms":0.15799999999999995,"service":"paymentservice-1","spans":203},{"delta_pct":18.9,"error_pct":0.0,"p95_during_ms":0.28099999999999975,"p95_pre_ms":0.2363,"service":"emailservice-2","spans":205},{"delta_pct":11.8,"error_pct":0.0,"p95_during_ms":5.0267,"p95_pre_ms":4.49725,"service":"productcatalogservice-1","spans":27763},{"delta_pct":10.4,"error_pct":0.0,"p95_during_ms":4.923500000000001,"p95_pre_ms":4.4615,"service":"productcatalogservice-2","spans":27762}],"omitted_services":22,"service_count":30}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=14 omitted_edges=0
[{"evidence_source":"trace","onset_rel_s":1194.6,"rank":1,"service":"checkoutservice","severity_z":383.604},{"evidence_source":"metric","onset_rel_s":1200.0,"rank":2,"service":"recommendationservice2","severity_z":151.226},{"evidence_source":"metric","onset_rel_s":1260.0,"rank":3,"service":"checkoutservice2","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1260.0,"rank":4,"service":"shippingservice2","severity_z":183.132},{"evidence_source":"metric","onset_rel_s":1320.0,"rank":5,"service":"currencyservice2","severity_z":180.882},{"evidence_source":"metric","onset_rel_s":1380.0,"rank":6,"service":"node-5","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1380.0,"rank":7,"service":"emailservice","severity_z":159.179},{"evidence_source":"metric","onset_rel_s":1440.0,"rank":8,"service":"cartservice","severity_z":238.188},{"evidence_source":"metric","onset_rel_s":1740.0,"rank":9,"service":"paymentservice2","severity_z":313.392},{"evidence_source":"metric","onset_rel_s":1740.0,"rank":10,"service":"shippingservice","severity_z":84.451},{"evidence_source":"metric","onset_rel_s":1860.0,"rank":11,"service":"cartservice2","severity_z":209.101},{"evidence_source":"metric","onset_rel_s":2040.0,"rank":12,"service":"adservice2","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":2220.0,"rank":13,"service":"node-2","severity_z":135.241},{"evidence_source":"metric","onset_rel_s":2340.0,"rank":14,"service":"adservice","severity_z":999.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"cartservice","caller":"checkoutservice"},{"callee":"emailservice","caller":"checkoutservice"},{"callee":"shippingservice","caller":"checkoutservice"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"medium","reason":"Rank checkoutservice-0 first because checkoutservice-0 has direct container_cpu_cfs_throttled_seconds evidence (signed-z 999, persistence 8 bins); recommendationservice2-0 is second despite propagation rank 2 because onset ordering alone does not establish the causal origin. The remaining entries preserve evidence-supported alternatives so the ranking retains calibrated uncertainty instead of collapsing to one answer.","services":["checkoutservice-0","checkoutservice-1","checkoutservice-2","node-5","node-2"]}
