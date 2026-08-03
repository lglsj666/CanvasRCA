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
opaque_id: INC-BD136E891A8B
observation_window={"duration_rel_s":2340.0,"source_metric_rows":40}
selection_summary={"candidate_count":63,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":1330,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","adservice-grpc","adservice-http","adservice2","adservice2-0","cartservice-0","cartservice-1","cartservice-2","cartservice-grpc","cartservice2-0","checkoutservice-0","checkoutservice-1","checkoutservice-2","checkoutservice-grpc","checkoutservice2-0","currencyservice-0","currencyservice-1","currencyservice-2","currencyservice-grpc","currencyservice2-0","emailservice-0","emailservice-1","emailservice-2","emailservice-grpc","emailservice2-0","frontend-0","frontend-1","frontend-2","frontend-http","frontend2-0","istio-egressgateway-7bfdcc9d86-zpjpg","istio-ingressgateway-565bffd4d-6bl7m","node-1","node-2","node-3","node-4","node-5","node-6","paymentservice-0","paymentservice-1","paymentservice-2","paymentservice-grpc","paymentservice2-0","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","productcatalogservice-grpc","productcatalogservice2-0","recommendationservice-0","recommendationservice-1","recommendationservice-2","recommendationservice-grpc","recommendationservice2-0","redis-cart-0","redis-cart2-0","shippingservice-0","shippingservice-1","shippingservice-2","shippingservice-grpc","shippingservice2-0"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[18.281,54.844,91.406,127.969,164.531,201.094,237.656,274.219,310.781,347.344,383.906,420.469,457.031,493.594,530.156,566.719,603.281,639.844,676.406,712.969,749.531,786.094,822.656,859.219,895.781,932.344,968.906,1005.469,1042.031,1078.594,1115.156,1151.719,1188.281,1224.844,1261.406,1297.969,1334.531,1371.094,1407.656,1444.219,1480.781,1517.344,1553.906,1590.469,1627.031,1663.594,1700.156,1736.719,1773.281,1809.844,1846.406,1882.969,1919.531,1956.094,1992.656,2029.219,2065.781,2102.344,2138.906,2175.469,2212.031,2248.594,2285.156,2321.719]
[M1] rank=1 service=adservice metric=jvm_threads_started baseline=0.0 peak=0.916667 signed_z=999.0 onset_bin=62 onset_rel_s=2285.156 persistence_bins=2
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.833333,-0.666666,-0.166667,0,0.083333,0.833334
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M2] rank=2 service=cartservice-1 metric=container_fs_reads./dev/vda baseline=0.0 peak=11.0 signed_z=999.0 onset_bin=44 onset_rel_s=1627.031 persistence_bins=3
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,11,0,0,-11,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M3] rank=3 service=cartservice-1 metric=container_fs_reads_MB./dev/vda baseline=0.0 peak=0.0625 signed_z=999.0 onset_bin=44 onset_rel_s=1627.031 persistence_bins=3
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.0625,0,0,-0.0625,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M4] rank=4 service=cartservice-2 metric=container_fs_reads./dev/vda baseline=0.0 peak=4.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,4,0,-4
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M5] rank=5 service=cartservice-2 metric=container_fs_reads_MB./dev/vda baseline=0.0 peak=0.046875 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.046875,0,-0.046875
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M6] rank=6 service=frontend-1 metric=container_fs_reads./dev/vda baseline=0.0 peak=5.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,5,-5,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M7] rank=7 service=frontend-1 metric=container_fs_reads_MB./dev/vda baseline=0.0 peak=0.023438 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.023438,-0.023438,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M8] rank=8 service=node-2 metric=system.disk.pct_usage baseline=41.45 peak=41.5 signed_z=999.0 onset_bin=49 onset_rel_s=1809.844 persistence_bins=10
values_compact=delta:41.45,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.01,0,0,0,0,0,0,0,0.04,0,-0.01,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M9] rank=9 service=node-6 metric=system.disk.free baseline=1417117952.0 peak=2030764763.43 signed_z=999.0 onset_bin=44 onset_rel_s=1627.031 persistence_bins=13
values_compact=delta:1417178112,-21333.33,32938.66,-20736,-19541.33,-13824,-39253.33,77397.33,-21077.33,-14848,-21162.67,-8192,14677.33,-13397.33,-19968,-33280,36693.33,-17237.33,-45397.33,-14933.34,-19797.33,27733.33,-6058.66,-21162.67,-48810.67,-19029.33,81920,613754331.43,-374637.72,-243419.42,-149504,-613657319.62,-37205.34,-16896,-46848,13482.67,-3162282.67,-40448,403200,19200
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M10] rank=10 service=node-6 metric=system.disk.pct_usage baseline=18.2945 peak=27.01 signed_z=999.0 onset_bin=44 onset_rel_s=1627.031 persistence_bins=8
values_compact=delta:18.29,0,0,0,0,0,0,0,0,0,0.01,-0.01,0.01,0,0,0,0,0,0,0,0,0,0,0,0,0,0,8.7,0.01,0,0,-8.71,0,0,0,0,0.02,0,0,-0.01
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M11] rank=11 service=node-6 metric=system.disk.total baseline=5101719893.33 peak=8303560996.57 signed_z=999.0 onset_bin=44 onset_rel_s=1627.031 persistence_bins=4
values_compact=delta:5101719893.33,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,3201841103.24,0,0,0,-3201841103.24,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M12] rank=12 service=node-6 metric=system.disk.used baseline=3663466717.865 peak=6255448064.0 signed_z=999.0 onset_bin=44 onset_rel_s=1627.031 persistence_bins=13
values_compact=delta:3663406421.33,21504,-33109.33,20821.33,19456,13653.34,39594.66,-77824,21504,14677.34,21162.66,8533.34,-14677.34,13312,20138.67,33109.33,-36864,17408,45397.34,15018.66,19797.34,-27648,5802.66,21162.67,48810.67,19114.66,-82261.33,2591106925.71,373906.29,243419.43,149796.57,-2591203328,37205.33,17066.67,46762.67,-13312,3162112,40618.66,-403456,-19114.66
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[1560.0,1800.0]

=== LOG SUMMARY ===
{"entries":[{"change_pct":-90.4,"n_during":18,"n_pre":187,"service":"paymentservice-1"},{"change_pct":-89.8,"n_during":102,"n_pre":1003,"service":"checkoutservice-2"},{"change_pct":-89.1,"n_during":1527,"n_pre":14031,"service":"frontend-2"},{"change_pct":-89.0,"n_during":177,"n_pre":1613,"service":"shippingservice-0"},{"change_pct":-89.0,"n_during":178,"n_pre":1624,"service":"shippingservice-2"},{"change_pct":-88.9,"n_during":20,"n_pre":180,"service":"emailservice-1"},{"change_pct":-88.4,"n_during":116,"n_pre":1001,"service":"checkoutservice-0"},{"change_pct":-88.4,"n_during":424,"n_pre":3650,"service":"recommendationservice-1"}],"mode":"volume","omitted_services":23,"service_count":31}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":-100.0,"error_pct":0.0,"p95_during_ms":0.0,"p95_pre_ms":1.0,"service":"cartservice-1","spans":3315},{"delta_pct":-100.0,"error_pct":0.0,"p95_during_ms":0.0,"p95_pre_ms":1.0,"service":"cartservice-2","spans":3342},{"delta_pct":-97.0,"error_pct":0.0,"p95_during_ms":5.912799999999998,"p95_pre_ms":199.7791,"service":"productcatalogservice-0","spans":9024},{"delta_pct":-97.0,"error_pct":0.0,"p95_during_ms":5.932299999999997,"p95_pre_ms":196.8505,"service":"productcatalogservice-2","spans":9023},{"delta_pct":-96.9,"error_pct":0.0,"p95_during_ms":6.039099999999999,"p95_pre_ms":197.979,"service":"productcatalogservice-1","spans":9023},{"delta_pct":-96.6,"error_pct":0.0,"p95_during_ms":3.03225,"p95_pre_ms":89.55085,"service":"recommendationservice-2","spans":2396},{"delta_pct":-96.5,"error_pct":0.0,"p95_during_ms":3.054349999999999,"p95_pre_ms":88.15795,"service":"recommendationservice-0","spans":2398},{"delta_pct":-96.5,"error_pct":0.0,"p95_during_ms":3.05,"p95_pre_ms":88.29435,"service":"recommendationservice-1","spans":2398}],"omitted_services":22,"service_count":30}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=16 omitted_edges=7
[{"evidence_source":"metric","onset_rel_s":1200.0,"rank":1,"service":"frontend2","severity_z":169.028},{"evidence_source":"metric","onset_rel_s":1260.0,"rank":2,"service":"redis-cart2","severity_z":115.667},{"evidence_source":"metric","onset_rel_s":1620.0,"rank":3,"service":"node-6","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1620.0,"rank":4,"service":"cartservice2","severity_z":375.825},{"evidence_source":"metric","onset_rel_s":1740.0,"rank":5,"service":"currencyservice","severity_z":116.384},{"evidence_source":"trace","onset_rel_s":2023.2,"rank":6,"service":"cartservice","severity_z":8.704},{"evidence_source":"trace","onset_rel_s":2023.2,"rank":7,"service":"frontend","severity_z":682.344},{"evidence_source":"trace","onset_rel_s":2023.2,"rank":8,"service":"productcatalogservice","severity_z":999.0},{"evidence_source":"trace","onset_rel_s":2023.2,"rank":9,"service":"recommendationservice","severity_z":999.0},{"evidence_source":"trace","onset_rel_s":2023.2,"rank":10,"service":"checkoutservice","severity_z":125.352},{"evidence_source":"metric","onset_rel_s":2040.0,"rank":11,"service":"productcatalogservice2","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":2160.0,"rank":12,"service":"node-2","severity_z":999.0},{"evidence_source":"trace","onset_rel_s":2169.6,"rank":13,"service":"shippingservice","severity_z":8.763},{"evidence_source":"metric","onset_rel_s":2340.0,"rank":14,"service":"adservice","severity_z":999.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"cartservice","caller":"checkoutservice"},{"callee":"currencyservice","caller":"checkoutservice"},{"callee":"productcatalogservice","caller":"checkoutservice"},{"callee":"shippingservice","caller":"checkoutservice"},{"callee":"adservice","caller":"frontend"},{"callee":"cartservice","caller":"frontend"},{"callee":"checkoutservice","caller":"frontend"},{"callee":"currencyservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"frontend"},{"callee":"recommendationservice","caller":"frontend"},{"callee":"shippingservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"recommendationservice"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

[excluded before optimizer]
