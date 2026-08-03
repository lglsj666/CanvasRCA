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
opaque_id: INC-E3490B9CF793
observation_window={"duration_rel_s":2340.0,"source_metric_rows":40}
selection_summary={"candidate_count":63,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":1412,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","adservice-grpc","adservice-http","adservice2","adservice2-0","cartservice-0","cartservice-1","cartservice-2","cartservice-grpc","cartservice2-0","checkoutservice-0","checkoutservice-1","checkoutservice-2","checkoutservice-grpc","checkoutservice2-0","currencyservice-0","currencyservice-1","currencyservice-2","currencyservice-grpc","currencyservice2-0","emailservice-0","emailservice-1","emailservice-2","emailservice-grpc","emailservice2-0","frontend-0","frontend-1","frontend-2","frontend-http","frontend2-0","istio-egressgateway-7bfdcc9d86-zpjpg","istio-ingressgateway-565bffd4d-6bl7m","node-1","node-2","node-3","node-4","node-5","node-6","paymentservice-0","paymentservice-1","paymentservice-2","paymentservice-grpc","paymentservice2-0","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","productcatalogservice-grpc","productcatalogservice2-0","recommendationservice-0","recommendationservice-1","recommendationservice-2","recommendationservice-grpc","recommendationservice2-0","redis-cart-0","redis-cart2-0","shippingservice-0","shippingservice-1","shippingservice-2","shippingservice-grpc","shippingservice2-0"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[18.281,54.844,91.406,127.969,164.531,201.094,237.656,274.219,310.781,347.344,383.906,420.469,457.031,493.594,530.156,566.719,603.281,639.844,676.406,712.969,749.531,786.094,822.656,859.219,895.781,932.344,968.906,1005.469,1042.031,1078.594,1115.156,1151.719,1188.281,1224.844,1261.406,1297.969,1334.531,1371.094,1407.656,1444.219,1480.781,1517.344,1553.906,1590.469,1627.031,1663.594,1700.156,1736.719,1773.281,1809.844,1846.406,1882.969,1919.531,1956.094,1992.656,2029.219,2065.781,2102.344,2138.906,2175.469,2212.031,2248.594,2285.156,2321.719]
[M1] rank=1 service=node-2 metric=system.disk.pct_usage baseline=41.42 peak=41.43 signed_z=999.0 onset_bin=49 onset_rel_s=1809.844 persistence_bins=10
values_compact=delta:41.42,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.01,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M2] rank=2 service=frontend-2 metric=container_fs_usage_MB./dev/vda1 baseline=69.433919 peak=22.351562 signed_z=-229.638 onset_bin=54 onset_rel_s=1992.656 persistence_bins=7
values_compact=delta:69.076172,0.039062,0.039063,0.041015,0.039063,0.041016,0.042968,0.03711,0.039062,0.023438,0.0625,0.041015,0.03125,0.013672,0.032552,0.033854,0.027344,0.011719,0.040365,0.031901,0.02539,0.023438,0.02539,0.027344,0.027344,0.025391,0.011718,0.03125,0.046875,0.035157,0.011718,0.023438,-47.707032,0.033855,0.020833,0.042969,0.037109,0.027344,0.023437,0.025391
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M3] rank=3 service=paymentservice-2 metric=container_network_receive_MB.eth0 baseline=0.023016 peak=0.314277 signed_z=168.449 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.023112,0.001865,-0.003626,0.002447,-0.002429,0.000573,0.002973,-0.002698,-0.000975,0.001231,0.001526,0.002094,-0.002597,-0.000602,-0.000955,0.001079,-0.00279,0.000699,0.006213,-0.003954,-0.003989,0.006124,-0.003066,0.000874,0.291148,-0.000551,-0.288934,0.001435,-0.002766,-0.003306,0.005279,-0.004565,0.002034,0.000294,-0.000154,-0.001225,0.00242,-0.00291,0.00615,-0.009406
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M4] rank=4 service=shippingservice2-0 metric=container_memory_mapped_file baseline=277094.4 peak=5068800.0 signed_z=162.656 onset_bin=31 onset_rel_s=1151.719 persistence_bins=21
values_compact=delta:270336,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,135168,0,0,0,4663296,-540672,-4528128,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M5] rank=5 service=emailservice-2 metric=container_network_receive_MB.eth0 baseline=0.025287 peak=0.315239 signed_z=131.221 onset_bin=36 onset_rel_s=1334.531 persistence_bins=2
values_compact=delta:0.025411,0.000411,-0.000872,0.000886,-0.000303,-0.003092,0.002887,-0.000632,-0.001643,0.004778,-0.000875,-0.005016,0.005069,-0.001342,-0.006806,0.008355,-0.000957,0.002129,-0.001032,-0.002173,-0.0027,0.00478,0.284379,0.003597,-0.288919,-0.002292,0.002371,-0.002463,-0.001938,0.003919,-0.001778,-0.001641,0.006644,-0.00593,-0.000294,0.002255,0.002218,-0.000232,-0.00719,0.005651
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M6] rank=6 service=shippingservice2-0 metric=container_network_receive_MB.eth0 baseline=0.069371 peak=0.691296 signed_z=108.671 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.077871,-0.010004,0.00483,-0.002962,-0.006998,0.003788,-0.001419,0.016066,-0.016205,0.010143,-0.006537,-0.008491,0.016003,-0.005867,-0.000873,-0.002307,0.001607,-0.004626,0.014157,-0.016717,0.008395,0.00473,-0.006028,-0.001963,-0.005607,0.012057,-0.015543,0.011275,0.622521,-0.627949,0.01176,-0.005003,-0.009608,0.010411,-0.000627,-0.004903,0.007632,-0.01078,-0.001679,0.000576
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M7] rank=7 service=shippingservice-0 metric=container_network_receive_MB.eth0 baseline=0.031737 peak=0.323819 signed_z=94.95 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.030677,0.001742,-0.001209,0.003469,-0.00296,0.000248,-0.00091,0.000733,0.001187,-0.008317,0.012909,-0.004233,-0.002493,-0.003204,0.007304,-0.007054,0.003389,0.004112,-0.008135,0.008185,0.287665,0.000714,-0.295165,0.002694,0.000891,-0.003175,-0.000139,0.003495,0.002785,-0.007846,0.00457,0.004266,-0.012507,0.00767,0.001603,-0.005774,0.006995,-0.008027,0.00853,-0.004059
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M8] rank=8 service=shippingservice2-0 metric=istio_request_duration_milliseconds.grpc.200.0.0 baseline=21.635 peak=6791.0125 signed_z=73.471 onset_bin=31 onset_rel_s=1151.719 persistence_bins=8
values_compact=delta:0.525,-0.2625,0.525,0,-0.2625,0.2625,-0.525,0,0,0.2625,-0.2625,0.2625,-0.2625,0.525,-0.2625,0,-0.525,1.3125,-1.05,422.9875,3270.8875,420.8875,1465.1125,156.3875,1054.4875,-1922.125,-1471.25,-3396.325,-0.2625,0.525,-1.3125,0.2625,-0.2625,0,0.525,0,-0.525,0,0.7875,-0.7875
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M9] rank=9 service=adservice-2 metric=container_network_receive_MB.eth0 baseline=0.040157 peak=0.428434 signed_z=55.48 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.031363,0.013982,0.007464,-0.008732,-0.004302,-0.010134,-0.000733,0.018826,-0.002213,-0.001243,-0.002316,-0.01065,0.006549,0.010063,-0.010405,0.002428,-0.009211,0.006768,0.012977,-0.012044,-0.009268,0.399265,-0.184376,-0.205189,-0.002582,0.006246,-0.004007,-0.002094,0.000183,0.00556,-0.012372,0.002884,0.017509,-0.014655,0.001436,-0.009439,0.013148,0.005498,-0.02388,0.01816
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M10] rank=10 service=node-3 metric=system.io.svctm baseline=0.361 peak=4.0 signed_z=51.061 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.41,0.01,-0.06,0.02,-0.06,0.11,-0.05,-0.03,-0.19,0.33,-0.21,-0.03,0.09,0.1,-0.1,-0.02,0.05,0.02,0.02,-0.03,-0.02,0.07,-0.11,0.08,-0.01,0.08,-0.17,0.01,-0.02,0.12,-0.06,-0.35,0,0.28,0.12,-0.09,-0.22,0.33,-0.02,3.6
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M11] rank=11 service=cartservice-1 metric=istio_request_duration_milliseconds.grpc.200.0.0 baseline=24.998125 peak=99.6125 signed_z=49.923 onset_bin=62 onset_rel_s=2285.156 persistence_bins=2
values_compact=delta:25.6875,1.075,0.275,-0.2875,-2.35,0.7875,1.0625,-2.6375,3.1,-0.725,0.25,-0.525,-1.0625,-1.8375,2.65,-3.4375,1.8125,0.8375,-2.3875,1.5875,-2.3625,1.8375,0.2625,-0.25,76.225,0.025,-75.9875,2.2875,-4.9125,-1.05,1.05,0.5,-1.55,1.2875,0,1.8375,-1.0375,-0.2625,-1.5625,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M12] rank=12 service=istio-egressgateway-7bfdcc9d86-zpjpg metric=istio_agent_process_open_fds baseline=25.0 peak=24.0 signed_z=-40.0 onset_bin=59 onset_rel_s=2175.469 persistence_bins=4
values_compact=delta:25,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-0.5,-0.5,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[1620.0,2340.0]

=== LOG SUMMARY ===
{"entries":[{"change_pct":-79.9,"n_during":2180,"n_pre":10825,"service":"frontend-0"},{"change_pct":-66.1,"n_during":56,"n_pre":165,"service":"emailservice-2"},{"change_pct":-64.6,"n_during":4604,"n_pre":13001,"service":"frontend-2"},{"change_pct":-63.4,"n_during":596,"n_pre":1628,"service":"adservice-2"},{"change_pct":-63.3,"n_during":542,"n_pre":1478,"service":"shippingservice-0"},{"change_pct":-63.2,"n_during":4778,"n_pre":12977,"service":"cartservice-2"},{"change_pct":-63.1,"n_during":4790,"n_pre":12975,"service":"cartservice-0"},{"change_pct":-63.1,"n_during":4153,"n_pre":11259,"service":"currencyservice-1"}],"mode":"volume","omitted_services":23,"service_count":31}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":-100.0,"error_pct":0.0,"p95_during_ms":0.0,"p95_pre_ms":1.0,"service":"cartservice-0","spans":3711},{"delta_pct":-48.5,"error_pct":0.0,"p95_during_ms":44.09844999999999,"p95_pre_ms":85.63925,"service":"checkoutservice2-0","spans":5416},{"delta_pct":23.4,"error_pct":0.0,"p95_during_ms":0.029,"p95_pre_ms":0.0235,"service":"adservice-1","spans":1110},{"delta_pct":-17.7,"error_pct":0.0,"p95_during_ms":0.086,"p95_pre_ms":0.1045,"service":"shippingservice2-0","spans":3205},{"delta_pct":-13.5,"error_pct":0.0,"p95_during_ms":0.25475,"p95_pre_ms":0.2945,"service":"emailservice-2","spans":74},{"delta_pct":12.8,"error_pct":0.0,"p95_during_ms":0.09590000000000004,"p95_pre_ms":0.085,"service":"shippingservice-1","spans":519},{"delta_pct":11.4,"error_pct":0.0,"p95_during_ms":0.19545,"p95_pre_ms":0.1754,"service":"paymentservice-2","spans":73},{"delta_pct":-10.3,"error_pct":0.0,"p95_during_ms":0.1514,"p95_pre_ms":0.16879999999999995,"service":"paymentservice-0","spans":74}],"omitted_services":32,"service_count":40}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=16 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":1200.0,"rank":1,"service":"shippingservice","severity_z":94.95},{"evidence_source":"metric","onset_rel_s":1200.0,"rank":2,"service":"frontend2","severity_z":26.002},{"evidence_source":"metric","onset_rel_s":1260.0,"rank":3,"service":"adservice","severity_z":55.48},{"evidence_source":"metric","onset_rel_s":1320.0,"rank":4,"service":"emailservice","severity_z":131.221},{"evidence_source":"metric","onset_rel_s":1380.0,"rank":5,"service":"shippingservice2","severity_z":162.656},{"evidence_source":"metric","onset_rel_s":1440.0,"rank":6,"service":"paymentservice","severity_z":168.449},{"evidence_source":"metric","onset_rel_s":1440.0,"rank":7,"service":"cartservice","severity_z":49.923},{"evidence_source":"metric","onset_rel_s":1560.0,"rank":8,"service":"node-1","severity_z":38.559},{"evidence_source":"metric","onset_rel_s":1680.0,"rank":9,"service":"node-2","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1680.0,"rank":10,"service":"recommendationservice","severity_z":36.58},{"evidence_source":"metric","onset_rel_s":1920.0,"rank":11,"service":"frontend","severity_z":229.638},{"evidence_source":"metric","onset_rel_s":2100.0,"rank":12,"service":"istio-egressgateway","severity_z":40.0},{"evidence_source":"metric","onset_rel_s":2160.0,"rank":13,"service":"node-4","severity_z":39.307},{"evidence_source":"metric","onset_rel_s":2340.0,"rank":14,"service":"node-3","severity_z":51.061}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"adservice","caller":"frontend"},{"callee":"cartservice","caller":"frontend"},{"callee":"recommendationservice","caller":"frontend"},{"callee":"shippingservice","caller":"frontend"},{"callee":"shippingservice2","caller":"frontend2"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"high","reason":"Rank shippingservice2-0 first because shippingservice2-0 has direct container_memory_mapped_file evidence (signed-z 162.66, persistence 21 bins); although frontend2-0 is salient, the caller path frontend2 -> shippingservice2 means a disturbance in the callee can propagate back toward that caller-side symptom.","services":["shippingservice2-0","frontend2-0"]}
