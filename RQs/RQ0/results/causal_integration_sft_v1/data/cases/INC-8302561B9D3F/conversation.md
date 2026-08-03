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
opaque_id: INC-8302561B9D3F
observation_window={"duration_rel_s":2340.0,"source_metric_rows":40}
selection_summary={"candidate_count":63,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":1392,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","adservice-grpc","adservice-http","adservice2","adservice2-0","cartservice-0","cartservice-1","cartservice-2","cartservice-grpc","cartservice2-0","checkoutservice-0","checkoutservice-1","checkoutservice-2","checkoutservice-grpc","checkoutservice2-0","currencyservice-0","currencyservice-1","currencyservice-2","currencyservice-grpc","currencyservice2-0","emailservice-0","emailservice-1","emailservice-2","emailservice-grpc","emailservice2-0","frontend-0","frontend-1","frontend-2","frontend-http","frontend2-0","istio-egressgateway-7bfdcc9d86-22q7z","istio-ingressgateway-565bffd4d-4nr6v","node-1","node-2","node-3","node-4","node-5","node-6","paymentservice-0","paymentservice-1","paymentservice-2","paymentservice-grpc","paymentservice2-0","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","productcatalogservice-grpc","productcatalogservice2-0","recommendationservice-0","recommendationservice-1","recommendationservice-2","recommendationservice-grpc","recommendationservice2-0","redis-cart-0","redis-cart2-0","shippingservice-0","shippingservice-1","shippingservice-2","shippingservice-grpc","shippingservice2-0"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[18.281,54.844,91.406,127.969,164.531,201.094,237.656,274.219,310.781,347.344,383.906,420.469,457.031,493.594,530.156,566.719,603.281,639.844,676.406,712.969,749.531,786.094,822.656,859.219,895.781,932.344,968.906,1005.469,1042.031,1078.594,1115.156,1151.719,1188.281,1224.844,1261.406,1297.969,1334.531,1371.094,1407.656,1444.219,1480.781,1517.344,1553.906,1590.469,1627.031,1663.594,1700.156,1736.719,1773.281,1809.844,1846.406,1882.969,1919.531,1956.094,1992.656,2029.219,2065.781,2102.344,2138.906,2175.469,2212.031,2248.594,2285.156,2321.719]
[M1] rank=1 service=adservice2 metric=jvm_classes_loaded baseline=0.0 peak=5162.0 signed_z=999.0 onset_bin=54 onset_rel_s=1992.656 persistence_bins=7
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,5162,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M2] rank=2 service=adservice metric=jvm_classes_loaded baseline=0.0 peak=5181.0 signed_z=999.0 onset_bin=54 onset_rel_s=1992.656 persistence_bins=7
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,5181,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M3] rank=3 service=emailservice-1 metric=container_cpu_cfs_throttled_seconds baseline=0.0 peak=0.188475 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.188475,-0.188475,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M4] rank=4 service=frontend-0 metric=container_cpu_cfs_throttled_seconds baseline=0.0 peak=0.003995 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.003995,0,-0.003995,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M5] rank=5 service=frontend2-0 metric=container_fs_inodes./dev/vda1 baseline=0.0 peak=0.5 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.5,0,-0.5,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M6] rank=6 service=frontend2-0 metric=container_fs_reads./dev/vda baseline=7.025 peak=70748.5 signed_z=999.0 onset_bin=31 onset_rel_s=1151.719 persistence_bins=5
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,140.5,48295,22313,-29247.5,-23981.5,-17519.5,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M7] rank=7 service=frontend2-0 metric=container_fs_reads_MB./dev/vda baseline=0.46709 peak=8753.900391 signed_z=999.0 onset_bin=31 onset_rel_s=1151.719 persistence_bins=5
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,9.341797,5983.253906,2761.304688,-3671.955079,-2927.58789,-2154.357422,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M8] rank=8 service=frontend2-0 metric=container_fs_usage_MB./dev/vda1 baseline=83.640625 peak=684.226562 signed_z=999.0 onset_bin=36 onset_rel_s=1334.531 persistence_bins=2
values_compact=delta:83.640625,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,300.292969,300.292968,0,-300.291015,-300.291016,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M9] rank=9 service=node-5 metric=system.disk.total baseline=4751651840.0 peak=5516931072.0 signed_z=999.0 onset_bin=54 onset_rel_s=1992.656 persistence_bins=2
values_compact=delta:4751651840,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,765279232,0,0,0,-765279232,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M10] rank=10 service=node-5 metric=system.disk.used baseline=3623962291.2 peak=4238800668.44 signed_z=999.0 onset_bin=54 onset_rel_s=1992.656 persistence_bins=2
values_compact=delta:3623925504,166144,-38400,-701952,107776,120320,-124160,140288,66560,106496,144128,27648,82688,116736,108032,97792,-13056,43264,36864,161280,111360,-37888,70144,93440,136704,120320,-279808,208640,-1981696,84224,163584,614688455.11,286264.89,197518.22,365454.22,-615085340.44,182272,46592,8448,50944
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M11] rank=11 service=node-5 metric=system.fs.inodes.in_use baseline=0.86 peak=0.77 signed_z=-999.0 onset_bin=54 onset_rel_s=1992.656 persistence_bins=2
values_compact=delta:0.86,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-0.09,0,0,0,0.09,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M12] rank=12 service=node-5 metric=system.fs.inodes.used baseline=1715764.2645 peak=1934787.56 signed_z=999.0 onset_bin=54 onset_rel_s=1992.656 persistence_bins=7
values_compact=delta:1715761.5,8.75,5.63,-62.5,17.87,13.13,4.37,-4.12,0.87,1.5,19.13,-5.75,21.12,-1.37,-3.88,16.5,-2.75,-11,9.13,0.37,27.75,-22.5,-14.12,14.5,2.87,1.5,-12.25,19.88,-18,12.37,-7.37,218888.65,8.44,3.56,93.78,-218830.06,15.5,-2.62,8.25,6.37
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[1800.0,2340.0]

=== LOG SUMMARY ===
{"entries":[{"change_pct":-75.2,"n_during":15803,"n_pre":63675,"service":"frontend-0"},{"change_pct":-74.5,"n_during":1228,"n_pre":4816,"service":"adservice-1"},{"change_pct":-74.5,"n_during":10836,"n_pre":42482,"service":"productcatalogservice-2"},{"change_pct":-74.4,"n_during":124,"n_pre":485,"service":"paymentservice-0"},{"change_pct":-74.4,"n_during":10881,"n_pre":42429,"service":"productcatalogservice-0"},{"change_pct":-74.4,"n_during":10871,"n_pre":42448,"service":"productcatalogservice-1"},{"change_pct":-74.4,"n_during":2324,"n_pre":9074,"service":"recommendationservice-2"},{"change_pct":-74.3,"n_during":9891,"n_pre":38500,"service":"cartservice-0"}],"mode":"volume","omitted_services":23,"service_count":31}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":-10.5,"error_pct":0.0,"p95_during_ms":0.017,"p95_pre_ms":0.019,"service":"adservice-0","spans":3021},{"delta_pct":6.5,"error_pct":0.0,"p95_during_ms":0.17049999999999996,"p95_pre_ms":0.16005,"service":"paymentservice-2","spans":202},{"delta_pct":6.3,"error_pct":0.0,"p95_during_ms":0.02125,"p95_pre_ms":0.02,"service":"adservice-1","spans":3021},{"delta_pct":-5.8,"error_pct":0.0,"p95_during_ms":0.114,"p95_pre_ms":0.121,"service":"currencyservice-2","spans":15425},{"delta_pct":-4.5,"error_pct":0.0,"p95_during_ms":0.239,"p95_pre_ms":0.25015,"service":"emailservice-2","spans":202},{"delta_pct":-4.1,"error_pct":0.0,"p95_during_ms":0.232,"p95_pre_ms":0.242,"service":"emailservice-0","spans":201},{"delta_pct":3.9,"error_pct":0.0,"p95_during_ms":0.079,"p95_pre_ms":0.076,"service":"shippingservice-0","spans":1413},{"delta_pct":-3.1,"error_pct":0.0,"p95_during_ms":0.153,"p95_pre_ms":0.15794999999999998,"service":"paymentservice-0","spans":203}],"omitted_services":22,"service_count":30}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=16 omitted_edges=2
[{"evidence_source":"metric","onset_rel_s":1200.0,"rank":1,"service":"frontend2","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1260.0,"rank":2,"service":"frontend","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1260.0,"rank":3,"service":"cartservice2","severity_z":240.716},{"evidence_source":"metric","onset_rel_s":1440.0,"rank":4,"service":"productcatalogservice2","severity_z":222.764},{"evidence_source":"metric","onset_rel_s":1800.0,"rank":5,"service":"emailservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1860.0,"rank":6,"service":"adservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1860.0,"rank":7,"service":"adservice2","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1860.0,"rank":8,"service":"node-5","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1920.0,"rank":9,"service":"checkoutservice","severity_z":228.832},{"evidence_source":"metric","onset_rel_s":1920.0,"rank":10,"service":"checkoutservice2","severity_z":202.003},{"evidence_source":"metric","onset_rel_s":1920.0,"rank":11,"service":"shippingservice","severity_z":199.16},{"evidence_source":"metric","onset_rel_s":1920.0,"rank":12,"service":"paymentservice","severity_z":155.237},{"evidence_source":"metric","onset_rel_s":1980.0,"rank":13,"service":"currencyservice","severity_z":268.509},{"evidence_source":"metric","onset_rel_s":2160.0,"rank":14,"service":"paymentservice2","severity_z":999.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"currencyservice","caller":"checkoutservice"},{"callee":"emailservice","caller":"checkoutservice"},{"callee":"paymentservice","caller":"checkoutservice"},{"callee":"shippingservice","caller":"checkoutservice"},{"callee":"adservice","caller":"frontend"},{"callee":"checkoutservice","caller":"frontend"},{"callee":"currencyservice","caller":"frontend"},{"callee":"shippingservice","caller":"frontend"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"medium","reason":"Rank frontend2-0 first because frontend2-0 has direct container_fs_inodes./dev/vda1 evidence (signed-z 999, persistence 0 bins); frontend-0 is second despite propagation rank 2 because onset ordering alone does not establish the causal origin.","services":["frontend2-0","frontend-0"]}
