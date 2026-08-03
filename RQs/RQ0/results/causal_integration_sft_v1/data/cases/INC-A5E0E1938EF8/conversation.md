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
opaque_id: INC-A5E0E1938EF8
observation_window={"duration_rel_s":2340.0,"source_metric_rows":40}
selection_summary={"candidate_count":63,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":1539,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","adservice-grpc","adservice-http","adservice2","adservice2-0","cartservice-0","cartservice-1","cartservice-2","cartservice-grpc","cartservice2-0","checkoutservice-0","checkoutservice-1","checkoutservice-2","checkoutservice-grpc","checkoutservice2-0","currencyservice-0","currencyservice-1","currencyservice-2","currencyservice-grpc","currencyservice2-0","emailservice-0","emailservice-1","emailservice-2","emailservice-grpc","emailservice2-0","frontend-0","frontend-1","frontend-2","frontend-http","frontend2-0","istio-egressgateway-7bfdcc9d86-22q7z","istio-ingressgateway-565bffd4d-4nr6v","node-1","node-2","node-3","node-4","node-5","node-6","paymentservice-0","paymentservice-1","paymentservice-2","paymentservice-grpc","paymentservice2-0","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","productcatalogservice-grpc","productcatalogservice2-0","recommendationservice-0","recommendationservice-1","recommendationservice-2","recommendationservice-grpc","recommendationservice2-0","redis-cart-0","redis-cart2-0","shippingservice-0","shippingservice-1","shippingservice-2","shippingservice-grpc","shippingservice2-0"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[18.281,54.844,91.406,127.969,164.531,201.094,237.656,274.219,310.781,347.344,383.906,420.469,457.031,493.594,530.156,566.719,603.281,639.844,676.406,712.969,749.531,786.094,822.656,859.219,895.781,932.344,968.906,1005.469,1042.031,1078.594,1115.156,1151.719,1188.281,1224.844,1261.406,1297.969,1334.531,1371.094,1407.656,1444.219,1480.781,1517.344,1553.906,1590.469,1627.031,1663.594,1700.156,1736.719,1773.281,1809.844,1846.406,1882.969,1919.531,1956.094,1992.656,2029.219,2065.781,2102.344,2138.906,2175.469,2212.031,2248.594,2285.156,2321.719]
[M1] rank=1 service=adservice2 metric=jvm_classes_loaded baseline=5162.0 peak=0.0 signed_z=-999.0 onset_bin=59 onset_rel_s=2175.469 persistence_bins=4
values_compact=delta:5162,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-5162,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M2] rank=2 service=adservice metric=jvm_classes_loaded baseline=5181.0 peak=0.0 signed_z=-999.0 onset_bin=59 onset_rel_s=2175.469 persistence_bins=4
values_compact=delta:5181,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-5181,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M3] rank=3 service=frontend-0 metric=container_cpu_cfs_throttled_seconds baseline=0.0 peak=0.004994 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.000328,0.000328,-0.000656,0,0,0,0,0,0,0,0,0,0,0.004994
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M4] rank=4 service=istio-ingressgateway-565bffd4d-4nr6v metric=istio_agent_go_gc_duration_seconds.0.0 baseline=4.2e-05 peak=4.2e-05 signed_z=-999.0 onset_bin=0 onset_rel_s=18.281 persistence_bins=40
values_compact=delta:0.000042,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M5] rank=5 service=node-5 metric=system.disk.total baseline=3767720813.710001 peak=4751651840.0 signed_z=999.0 onset_bin=59 onset_rel_s=2175.469 persistence_bins=3
values_compact=delta:3767720813.71,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,983931026.29,0,0,0,-983931026.29
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M6] rank=6 service=node-5 metric=system.fs.inodes.in_use baseline=0.98 peak=0.86 signed_z=-999.0 onset_bin=59 onset_rel_s=2175.469 persistence_bins=3
values_compact=delta:0.98,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-0.12,0,0,0,0.12
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M7] rank=7 service=node-5 metric=system.fs.inodes.used baseline=1429705.429 peak=1709745.63 signed_z=999.0 onset_bin=59 onset_rel_s=2175.469 persistence_bins=4
values_compact=delta:1429680.71,8.86,26.29,-47.15,37.29,0.71,-8.57,-1.85,6.57,12,3.14,-17.29,15.29,7.86,-7,-2,-1,-4,15.14,-35.14,-48.72,7.57,16.86,21.72,-29.43,4.28,17.43,15.43,-19.14,-2,9.57,-5.86,16,-8.86,0.29,279951.13,22.87,11.88,74.75,-279859.06
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M8] rank=8 service=node-5 metric=system.fs.inodes.total baseline=2978120938.057 peak=3895915520.0 signed_z=864.005 onset_bin=59 onset_rel_s=2175.469 persistence_bins=3
values_compact=delta:2979694006.86,-196900.57,-349915.43,130194.28,-336457.14,108836.57,-211236.57,-648338.29,140141.72,-181979.43,-96841.14,-300178.29,-364544,65243.43,-219428.57,182857.14,-403456,-296374.86,-1329737.14,3515830.86,1385910.86,-336749.72,-220891.43,-166180.57,-178176,-89819.43,-376539.43,-330898.28,155355.43,-206848,25453.71,-217965.71,-407552,95378.28,-126098.28,918009417.14,-1167872,-910592,-339712,-918028653.71
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M9] rank=9 service=node-5 metric=system.fs.inodes.free baseline=2976691243.886 peak=3894205952.0 signed_z=863.729 onset_bin=59 onset_rel_s=2175.469 persistence_bins=3
values_compact=delta:2978264210.29,-196900.58,-349915.42,130486.85,-336457.14,108836.57,-211529.14,-648338.29,140434.29,-182272,-96548.57,-300470.86,-364544,65243.43,-219428.57,182857.14,-403456,-296374.86,-1329444.57,3515830.86,1385618.28,-336457.14,-221184,-166180.57,-177883.43,-90112,-376539.43,-330898.28,155648,-206848,25453.71,-217965.71,-407552,95085.71,-126098.28,917729645.71,-1167616,-911104,-339712,-917748626.29
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M10] rank=10 service=node-5 metric=system.disk.used baseline=2809327235.6575 peak=3591063552.0 signed_z=521.222 onset_bin=59 onset_rel_s=2175.469 persistence_bins=3
values_compact=delta:2808225792,70217.14,109129.15,-11410.29,112347.43,-167643.43,73728,184027.43,-13458.29,1189010.29,1375670.86,1435940.57,1464612.57,-5130532.57,48859.43,-23405.72,122587.43,97133.71,354304,-850505.14,-323291.43,105618.29,41837.71,28964.57,67291.43,52077.72,117321.14,104155.43,-18432,71972.57,21357.71,75776,88941.72,-2048,51200,781255972.57,308992,246528,102912,-781279524.57
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M11] rank=11 service=node-5 metric=system.net.tcp.out_segs baseline=367.999 peak=8061.17 signed_z=516.581 onset_bin=59 onset_rel_s=2175.469 persistence_bins=4
values_compact=delta:355.81,35.29,-37.53,21.9,-21.14,22.52,-19.7,11.26,-11.64,43.26,-46.93,10.77,-14.9,31.3,9.29,-14.88,-27.48,33.27,-21.3,14.03,0.63,1.61,-18.17,24.04,-17.64,11.95,-17.36,18.96,50.15,-36.27,-40.61,23.78,-12.05,9.81,-19.1,154.82,4865.15,767.71,1920.56,-6760.7
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M12] rank=12 service=adservice metric=jvm_memory_pool_MB_used.Tenured_Gen baseline=52.121969 peak=52.508438 signed_z=466.095 onset_bin=36 onset_rel_s=1334.531 persistence_bins=18
values_compact=delta:52.120811,0,0,0,0.000036,0.000025,0.000186,0.001124,0.000163,0.000036,0.000025,0.000031,0.000101,0.000102,0.000041,0.00003,0.00001,0.000051,0,0,0.000061,0.031969,0.159537,0,0,0.000006,0.000472,0.000269,0.000795,0.001133,0.000224,0.07959,0.111427,0.000041,0.00002,0.000122,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[2040.0,2340.0]

=== LOG SUMMARY ===
{"entries":[{"change_pct":-88.1,"n_during":56,"n_pre":469,"service":"emailservice-2"},{"change_pct":-87.8,"n_during":60,"n_pre":492,"service":"paymentservice-0"},{"change_pct":-87.1,"n_during":350,"n_pre":2707,"service":"checkoutservice-2"},{"change_pct":-87.0,"n_during":6933,"n_pre":53430,"service":"frontend-1"},{"change_pct":-86.8,"n_during":65,"n_pre":491,"service":"paymentservice-2"},{"change_pct":-86.7,"n_during":650,"n_pre":4869,"service":"adservice-1"},{"change_pct":-86.7,"n_during":4484,"n_pre":33708,"service":"currencyservice-0"},{"change_pct":-86.6,"n_during":4514,"n_pre":33667,"service":"currencyservice-1"}],"mode":"volume","omitted_services":23,"service_count":31}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":-20.4,"error_pct":0.0,"p95_during_ms":0.1399,"p95_pre_ms":0.17569999999999997,"service":"paymentservice2-0","spans":82},{"delta_pct":-8.4,"error_pct":0.0,"p95_during_ms":0.07529999999999998,"p95_pre_ms":0.0822,"service":"shippingservice2-0","spans":575},{"delta_pct":-7.3,"error_pct":0.0,"p95_during_ms":0.0185,"p95_pre_ms":0.01994999999999982,"service":"adservice-0","spans":2748},{"delta_pct":5.3,"error_pct":0.0,"p95_during_ms":0.02,"p95_pre_ms":0.019,"service":"adservice-1","spans":2747},{"delta_pct":-5.2,"error_pct":0.0,"p95_during_ms":0.073,"p95_pre_ms":0.077,"service":"shippingservice-1","spans":1281},{"delta_pct":-4.8,"error_pct":0.0,"p95_during_ms":38.8677,"p95_pre_ms":40.84599999999999,"service":"checkoutservice-0","spans":2158},{"delta_pct":-4.3,"error_pct":0.0,"p95_during_ms":0.022,"p95_pre_ms":0.023,"service":"adservice-2","spans":2746},{"delta_pct":4.3,"error_pct":0.0,"p95_during_ms":0.241,"p95_pre_ms":0.231,"service":"emailservice-2","spans":184}],"omitted_services":32,"service_count":40}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=16 omitted_edges=1
[{"evidence_source":"metric","onset_rel_s":1200.0,"rank":1,"service":"istio-ingressgateway","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1320.0,"rank":2,"service":"cartservice","severity_z":30.368},{"evidence_source":"metric","onset_rel_s":1680.0,"rank":3,"service":"emailservice","severity_z":131.915},{"evidence_source":"metric","onset_rel_s":1680.0,"rank":4,"service":"node-2","severity_z":81.0},{"evidence_source":"metric","onset_rel_s":1680.0,"rank":5,"service":"checkoutservice","severity_z":40.288},{"evidence_source":"metric","onset_rel_s":1680.0,"rank":6,"service":"redis-cart","severity_z":24.831},{"evidence_source":"metric","onset_rel_s":1980.0,"rank":7,"service":"node-3","severity_z":51.754},{"evidence_source":"metric","onset_rel_s":2100.0,"rank":8,"service":"adservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":2100.0,"rank":9,"service":"adservice2","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":2100.0,"rank":10,"service":"node-5","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":2100.0,"rank":11,"service":"istio-egressgateway","severity_z":237.224},{"evidence_source":"metric","onset_rel_s":2100.0,"rank":12,"service":"shippingservice2","severity_z":36.09},{"evidence_source":"metric","onset_rel_s":2160.0,"rank":13,"service":"currencyservice","severity_z":59.083},{"evidence_source":"metric","onset_rel_s":2340.0,"rank":14,"service":"frontend","severity_z":999.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"cartservice","caller":"checkoutservice"},{"callee":"currencyservice","caller":"checkoutservice"},{"callee":"emailservice","caller":"checkoutservice"},{"callee":"adservice","caller":"frontend"},{"callee":"cartservice","caller":"frontend"},{"callee":"checkoutservice","caller":"frontend"},{"callee":"currencyservice","caller":"frontend"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

[excluded before optimizer]
