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
opaque_id: INC-4D8179724F94
observation_window={"duration_rel_s":2340.0,"source_metric_rows":40}
selection_summary={"candidate_count":63,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":1493,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","adservice-grpc","adservice-http","adservice2","adservice2-0","cartservice-0","cartservice-1","cartservice-2","cartservice-grpc","cartservice2-0","checkoutservice-0","checkoutservice-1","checkoutservice-2","checkoutservice-grpc","checkoutservice2-0","currencyservice-0","currencyservice-1","currencyservice-2","currencyservice-grpc","currencyservice2-0","emailservice-0","emailservice-1","emailservice-2","emailservice-grpc","emailservice2-0","frontend-0","frontend-1","frontend-2","frontend-http","frontend2-0","istio-egressgateway-7bfdcc9d86-g2d4q","istio-ingressgateway-565bffd4d-rn678","node-1","node-2","node-3","node-4","node-5","node-6","paymentservice-0","paymentservice-1","paymentservice-2","paymentservice-grpc","paymentservice2-0","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","productcatalogservice-grpc","productcatalogservice2-0","recommendationservice-0","recommendationservice-1","recommendationservice-2","recommendationservice-grpc","recommendationservice2-0","redis-cart-0","redis-cart2-0","shippingservice-0","shippingservice-1","shippingservice-2","shippingservice-grpc","shippingservice2-0"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[18.281,54.844,91.406,127.969,164.531,201.094,237.656,274.219,310.781,347.344,383.906,420.469,457.031,493.594,530.156,566.719,603.281,639.844,676.406,712.969,749.531,786.094,822.656,859.219,895.781,932.344,968.906,1005.469,1042.031,1078.594,1115.156,1151.719,1188.281,1224.844,1261.406,1297.969,1334.531,1371.094,1407.656,1444.219,1480.781,1517.344,1553.906,1590.469,1627.031,1663.594,1700.156,1736.719,1773.281,1809.844,1846.406,1882.969,1919.531,1956.094,1992.656,2029.219,2065.781,2102.344,2138.906,2175.469,2212.031,2248.594,2285.156,2321.719]
[M1] rank=1 service=cartservice2-0 metric=container_fs_reads./dev/vda baseline=0.0 peak=17.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,17,-17,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M2] rank=2 service=cartservice2-0 metric=container_fs_reads_MB./dev/vda baseline=0.0 peak=0.132812 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.132812,-0.132812,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M3] rank=3 service=cartservice2-0 metric=container_memory_failures.container.pgmajfault baseline=0.0 peak=2.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,2,-2,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M4] rank=4 service=cartservice2-0 metric=container_memory_failures.hierarchy.pgmajfault baseline=0.0 peak=2.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,2,-2,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M5] rank=5 service=frontend2-0 metric=container_fs_reads./dev/vda baseline=0.0 peak=6.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,4,-4,0,0,0,0,0,0,1,-1,0,0,6
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M6] rank=6 service=frontend2-0 metric=container_fs_reads_MB./dev/vda baseline=0.0 peak=0.105469 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.105469,-0.105469,0,0,0,0,0,0,0.003906,-0.003906,0,0,0.027344
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M7] rank=7 service=frontend2-0 metric=container_memory_failures.container.pgmajfault baseline=0.0 peak=1.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,-1,0,0,1
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M8] rank=8 service=frontend2-0 metric=container_memory_failures.hierarchy.pgmajfault baseline=0.0 peak=1.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,-1,0,0,1
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M9] rank=9 service=node-6 metric=system.io.avg_q_sz baseline=0.02 peak=63.29 signed_z=999.0 onset_bin=36 onset_rel_s=1334.531 persistence_bins=3
values_compact=delta:0,0,0,0.04,-0.02,-0.01,0,-0.01,0.03,0.01,0,0,-0.01,0,0.01,-0.01,0,-0.03,0.01,-0.01,62.12,1.11,0.03,0.03,-63.26,0,-0.01,-0.02,0.01,0.01,0,0.01,0,-0.01,-0.01,0.9,-0.85,-0.06,0.01,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M10] rank=10 service=node-6 metric=system.io.r_s baseline=0.05 peak=1126.0 signed_z=999.0 onset_bin=36 onset_rel_s=1334.531 persistence_bins=4
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,1,-1,0,0,0,0,0,0,0.5,2.5,-2,2,-3,0.5,-0.5,0,0.5,-0.5,0,0,0,0,0,1126,-1112,-14,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M11] rank=11 service=node-6 metric=system.io.w_await baseline=0.4465 peak=122.14 signed_z=657.44 onset_bin=36 onset_rel_s=1334.531 persistence_bins=2
values_compact=delta:0,0,0.34,0.3,-0.1,0.04,-0.06,-0.2,0.12,0.11,0.01,-0.06,0.04,0.04,-0.02,0.03,0.1,-0.34,-0.04,0.01,52.01,68.49,-6.25,7.57,-121.46,-0.18,-0.06,-0.25,0.37,-0.16,-0.1,0.11,0,0.06,-0.06,0.1,-0.11,-0.18,0.07,0.11
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M12] rank=12 service=node-6 metric=system.io.await baseline=0.446 peak=120.78 signed_z=650.939 onset_bin=36 onset_rel_s=1334.531 persistence_bins=2
values_compact=delta:0,0,0.34,0.3,-0.1,0.04,-0.06,-0.2,0.12,0.11,0.01,-0.06,0.03,0.05,-0.02,0.03,0.1,-0.34,-0.04,0.01,51.97,67.17,-5.29,6.61,-120.1,-0.18,-0.06,-0.25,0.36,-0.15,-0.1,0.11,0,0.06,-0.06,-0.01,-0.03,-0.15,0.07,0.11
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[2160.0,2280.0]

=== LOG SUMMARY ===
{"entries":[{"error_logs":3038,"error_pct":9.09,"service":"adservice-0","total_logs":33433},{"error_logs":612,"error_pct":1.29,"service":"frontend-2","total_logs":47272},{"error_logs":587,"error_pct":1.29,"service":"frontend-1","total_logs":45499},{"error_logs":321,"error_pct":1.28,"service":"frontend-0","total_logs":25094},{"error_logs":1,"error_pct":0.06,"service":"checkoutservice-2","total_logs":1669}],"mode":"errors","omitted_services":26,"service_count":31}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":34.4,"error_pct":0.0,"p95_during_ms":49.72709999999993,"p95_pre_ms":37.011,"service":"checkoutservice-2","spans":1176},{"delta_pct":18.7,"error_pct":0.0,"p95_during_ms":0.019,"p95_pre_ms":0.016,"service":"adservice-0","spans":1519},{"delta_pct":-17.9,"error_pct":0.0,"p95_during_ms":0.015599999999999994,"p95_pre_ms":0.019,"service":"adservice-1","spans":1519},{"delta_pct":-9.1,"error_pct":0.0,"p95_during_ms":34.39875,"p95_pre_ms":37.82615,"service":"checkoutservice-0","spans":1174},{"delta_pct":-7.5,"error_pct":0.0,"p95_during_ms":0.13575,"p95_pre_ms":0.14675,"service":"paymentservice-2","spans":102},{"delta_pct":-7.4,"error_pct":0.0,"p95_during_ms":0.14079999999999998,"p95_pre_ms":0.152,"service":"paymentservice2-0","spans":214},{"delta_pct":-6.4,"error_pct":0.0,"p95_during_ms":0.06925,"p95_pre_ms":0.074,"service":"shippingservice-1","spans":706},{"delta_pct":-5.9,"error_pct":0.0,"p95_during_ms":0.20965,"p95_pre_ms":0.22275,"service":"emailservice2-0","spans":214}],"omitted_services":32,"service_count":40}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=15 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":1200.0,"rank":1,"service":"node-6","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1200.0,"rank":2,"service":"emailservice2","severity_z":335.611},{"evidence_source":"metric","onset_rel_s":1200.0,"rank":3,"service":"node-3","severity_z":63.0},{"evidence_source":"metric","onset_rel_s":1260.0,"rank":4,"service":"checkoutservice","severity_z":56.125},{"evidence_source":"metric","onset_rel_s":1320.0,"rank":5,"service":"paymentservice2","severity_z":370.179},{"evidence_source":"metric","onset_rel_s":1320.0,"rank":6,"service":"adservice","severity_z":39.816},{"evidence_source":"metric","onset_rel_s":1440.0,"rank":7,"service":"paymentservice","severity_z":297.301},{"evidence_source":"metric","onset_rel_s":1440.0,"rank":8,"service":"emailservice","severity_z":223.489},{"evidence_source":"metric","onset_rel_s":1440.0,"rank":9,"service":"node-4","severity_z":40.654},{"evidence_source":"metric","onset_rel_s":1500.0,"rank":10,"service":"shippingservice","severity_z":189.966},{"evidence_source":"metric","onset_rel_s":1560.0,"rank":11,"service":"cartservice","severity_z":104.665},{"evidence_source":"metric","onset_rel_s":1740.0,"rank":12,"service":"redis-cart2","severity_z":47.232},{"evidence_source":"metric","onset_rel_s":2220.0,"rank":13,"service":"cartservice2","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":2340.0,"rank":14,"service":"frontend2","severity_z":999.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"cartservice","caller":"checkoutservice"},{"callee":"emailservice","caller":"checkoutservice"},{"callee":"paymentservice","caller":"checkoutservice"},{"callee":"shippingservice","caller":"checkoutservice"},{"callee":"cartservice2","caller":"frontend2"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"medium","reason":"Rank node-6 first because node-6 has direct system.io.avg_q_sz evidence (signed-z 999, persistence 3 bins); emailservice2-0 is second despite propagation rank 2 because onset ordering alone does not establish the causal origin.","services":["node-6","emailservice2-0"]}
