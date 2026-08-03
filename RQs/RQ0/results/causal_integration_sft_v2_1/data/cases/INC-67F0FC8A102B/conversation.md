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
opaque_id: INC-67F0FC8A102B
observation_window={"duration_rel_s":2340.0,"source_metric_rows":40}
selection_summary={"candidate_count":63,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":1516,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","adservice-grpc","adservice-http","adservice2","adservice2-0","cartservice-0","cartservice-1","cartservice-2","cartservice-grpc","cartservice2-0","checkoutservice-0","checkoutservice-1","checkoutservice-2","checkoutservice-grpc","checkoutservice2-0","currencyservice-0","currencyservice-1","currencyservice-2","currencyservice-grpc","currencyservice2-0","emailservice-0","emailservice-1","emailservice-2","emailservice-grpc","emailservice2-0","frontend-0","frontend-1","frontend-2","frontend-http","frontend2-0","istio-egressgateway-7bfdcc9d86-22q7z","istio-ingressgateway-565bffd4d-4nr6v","node-1","node-2","node-3","node-4","node-5","node-6","paymentservice-0","paymentservice-1","paymentservice-2","paymentservice-grpc","paymentservice2-0","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","productcatalogservice-grpc","productcatalogservice2-0","recommendationservice-0","recommendationservice-1","recommendationservice-2","recommendationservice-grpc","recommendationservice2-0","redis-cart-0","redis-cart2-0","shippingservice-0","shippingservice-1","shippingservice-2","shippingservice-grpc","shippingservice2-0"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[18.281,54.844,91.406,127.969,164.531,201.094,237.656,274.219,310.781,347.344,383.906,420.469,457.031,493.594,530.156,566.719,603.281,639.844,676.406,712.969,749.531,786.094,822.656,859.219,895.781,932.344,968.906,1005.469,1042.031,1078.594,1115.156,1151.719,1188.281,1224.844,1261.406,1297.969,1334.531,1371.094,1407.656,1444.219,1480.781,1517.344,1553.906,1590.469,1627.031,1663.594,1700.156,1736.719,1773.281,1809.844,1846.406,1882.969,1919.531,1956.094,1992.656,2029.219,2065.781,2102.344,2138.906,2175.469,2212.031,2248.594,2285.156,2321.719]
[M1] rank=1 service=adservice2 metric=jvm_classes_loaded baseline=5162.0 peak=0.0 signed_z=-999.0 onset_bin=49 onset_rel_s=1809.844 persistence_bins=10
values_compact=delta:5162,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-5162,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M2] rank=2 service=adservice metric=jvm_classes_loaded baseline=5181.0 peak=0.0 signed_z=-999.0 onset_bin=49 onset_rel_s=1809.844 persistence_bins=10
values_compact=delta:5181,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-5181,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M3] rank=3 service=node-5 metric=system.disk.total baseline=3767720813.710001 peak=4751651840.0 signed_z=999.0 onset_bin=49 onset_rel_s=1809.844 persistence_bins=4
values_compact=delta:3767720813.71,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,983931026.29,0,0,0,-983931026.29,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M4] rank=4 service=node-5 metric=system.disk.used baseline=2827522399.085999 peak=3615018752.0 signed_z=999.0 onset_bin=44 onset_rel_s=1627.031 persistence_bins=12
values_compact=delta:2827053348.57,109421.72,-62902.86,46811.43,97133.71,15798.86,-15213.72,117321.15,57344,57344,79579.43,-20772.58,121417.15,68754.28,96256,21650.29,-23698.29,77238.86,133705.14,64658.29,53540.57,-105618.29,98889.15,78116.57,89526.86,52077.71,-21942.86,-2149522.28,61147.43,61147.42,787991954.29,121856,296448,295936,-788406016,-280868.57,-34816,83968,72265.14,101814.86
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M5] rank=5 service=node-5 metric=system.fs.inodes.free baseline=2898080124.3435 peak=3787887104.0 signed_z=999.0 onset_bin=49 onset_rel_s=1809.844 persistence_bins=10
values_compact=delta:2899223698.29,-327680,341430.85,-108836.57,-308077.71,-133997.72,149211.43,-382390.86,-143360,-147163.42,-208896,162377.14,-399945.14,-167643.43,-297545.15,-3803.42,182564.57,-228205.72,-419840,-181686.85,-129024,503515.42,-281453.71,-237568,-277065.14,-131949.72,200411.43,-337334.86,-161206.85,-171446.86,892310016,-419584,-1111296,-1118720,-890837430.86,923940.57,220013.72,-259510.86,-197485.71,-300470.86
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M6] rank=6 service=node-5 metric=system.fs.inodes.in_use baseline=0.98 peak=0.86 signed_z=-999.0 onset_bin=49 onset_rel_s=1809.844 persistence_bins=4
values_compact=delta:0.98,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-0.12,0,0,0,0.12,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M7] rank=7 service=node-5 metric=system.fs.inodes.total baseline=2899513358.6275 peak=3789601536.0 signed_z=999.0 onset_bin=49 onset_rel_s=1809.844 persistence_bins=10
values_compact=delta:2900656713.14,-327680,341430.86,-108544,-308077.71,-133997.72,149211.43,-382390.86,-143360,-147163.43,-208896,162084.58,-399652.58,-167643.42,-297545.15,-3803.43,182564.58,-228205.72,-419840,-181979.43,-128731.43,503515.43,-281453.71,-237568,-277065.14,-132242.29,200704,-337334.86,-161206.85,-171446.86,892591140.57,-419584,-1111808,-1118464,-891118299.43,923940.57,220013.72,-259510.86,-197485.71,-300470.86
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M8] rank=8 service=node-5 metric=system.fs.inodes.used baseline=1433236.778 peak=1714420.75 signed_z=999.0 onset_bin=49 onset_rel_s=1809.844 persistence_bins=10
values_compact=delta:1433223.29,-5.86,3.14,-2.28,0.85,-0.85,18.28,-6,-15.43,13.72,22.85,4.29,-37.43,20.57,20.86,7.71,-20,2.86,10.29,-5.72,7,-10.28,9.85,-8.14,19.29,1.43,-24,3.57,15.71,4,281037.56,24.37,25.25,60,-281062.32,-17.29,17.43,-3.28,0.85,-3.14
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M9] rank=9 service=node-5 metric=system.net.tcp.out_segs baseline=364.5085 peak=7469.19 signed_z=673.137 onset_bin=49 onset_rel_s=1809.844 persistence_bins=5
values_compact=delta:361.27,6.21,-7.33,0.78,5.52,-4.69,-1.16,4.63,-8.38,14.97,-12.51,10.11,-9.49,5.42,-10.15,7.88,-5.69,5.71,-4.98,48.61,-46.35,53.41,-57.01,6.34,0.85,6.23,-22.46,20.46,-10.15,6.3,132.13,5175.65,784.22,1012.84,-5064.66,-2042.28,-1.23,5.86,-9.31,10.21
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M10] rank=10 service=node-5 metric=system.disk.free baseline=922082614.858 peak=1121495808.0 signed_z=630.733 onset_bin=44 onset_rel_s=1627.031 persistence_bins=12
values_compact=delta:922551588.57,-109421.71,62976,-46738.29,-97133.71,-15945.15,15360,-117394.28,-57417.14,-57197.72,-79725.71,20772.57,-121417.14,-68754.29,-96109.71,-21723.43,23698.28,-77165.71,-133632,-64731.43,-53686.86,105618.29,-98889.14,-78043.43,-89526.86,-52004.57,21942.86,2149376,-61220.58,-61147.42,198203501.71,-121728,-296448,-295936,-197789275.43,280868.57,34669.72,-84041.15,-72045.71,-102034.29
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M11] rank=11 service=istio-ingressgateway-565bffd4d-4nr6v metric=istio_agent_go_memstats_alloc_bytes baseline=966940.6 peak=9388876.0 signed_z=435.673 onset_bin=49 onset_rel_s=1809.844 persistence_bins=10
values_compact=delta:958400,-28096,37996,-3396,7068,19032,-28,-28584,-4472,9080,-16556,20756,3672,26344,-43588,6036,13688,14552,-74004,51560,-72688,20628,40168,1164,40868,-27372,-36240,33000,16456,4080,7297932,681952,419468,-544580,-514276,-103672,-94256,-21496,42900,-24624
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M12] rank=12 service=paymentservice-0 metric=container_network_receive_MB.eth0 baseline=0.02211 peak=0.540275 signed_z=229.314 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.022874,-0.000265,-0.00111,0.00029,0.000357,0.001253,-0.002379,0.003177,0.00254,-0.005477,-0.004253,0.004451,0.001032,-0.000623,0.005562,-0.006925,-0.002048,0.003784,-0.000806,0.000353,0.002009,0.008626,0.507853,-0.521122,0.004201,-0.003599,0.002231,-0.000539,0.002201,-0.001626,0.000469,0,0.000546,0.002793,0.000401,-0.006724,-0.004955,0.007443,0.005661,-0.001714
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[1740.0,2340.0]

=== LOG SUMMARY ===
{"entries":[{"change_pct":-71.4,"n_during":10,"n_pre":35,"service":"redis-cart-0"},{"change_pct":-68.7,"n_during":108,"n_pre":345,"service":"emailservice-1"},{"change_pct":-67.8,"n_during":636,"n_pre":1973,"service":"checkoutservice-2"},{"change_pct":-67.6,"n_during":117,"n_pre":361,"service":"paymentservice-2"},{"change_pct":-67.2,"n_during":17408,"n_pre":53153,"service":"frontend-2"},{"change_pct":-67.1,"n_during":113,"n_pre":343,"service":"emailservice-2"},{"change_pct":-67.0,"n_during":648,"n_pre":1966,"service":"checkoutservice-0"},{"change_pct":-66.9,"n_during":114,"n_pre":344,"service":"emailservice-0"}],"mode":"volume","omitted_services":23,"service_count":31}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":6.8,"error_pct":0.0,"p95_during_ms":0.08119999999999993,"p95_pre_ms":0.076,"service":"shippingservice-2","spans":1104},{"delta_pct":6.1,"error_pct":0.0,"p95_during_ms":0.121,"p95_pre_ms":0.114,"service":"currencyservice-2","spans":12047},{"delta_pct":-5.6,"error_pct":0.0,"p95_during_ms":0.07459999999999996,"p95_pre_ms":0.079,"service":"shippingservice2-0","spans":1057},{"delta_pct":-5.3,"error_pct":0.0,"p95_during_ms":0.018,"p95_pre_ms":0.019,"service":"adservice-0","spans":2373},{"delta_pct":-5.3,"error_pct":0.0,"p95_during_ms":0.15535,"p95_pre_ms":0.164,"service":"paymentservice2-0","spans":151},{"delta_pct":4.9,"error_pct":0.0,"p95_during_ms":41.0085,"p95_pre_ms":39.09279999999999,"service":"checkoutservice-2","spans":1846},{"delta_pct":-4.9,"error_pct":0.0,"p95_during_ms":0.1371,"p95_pre_ms":0.14414999999999997,"service":"paymentservice-1","spans":158},{"delta_pct":4.7,"error_pct":0.0,"p95_during_ms":0.2492,"p95_pre_ms":0.238,"service":"emailservice-0","spans":158}],"omitted_services":32,"service_count":40}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=15 omitted_edges=1
[{"evidence_source":"metric","onset_rel_s":1320.0,"rank":1,"service":"paymentservice","severity_z":229.314},{"evidence_source":"metric","onset_rel_s":1320.0,"rank":2,"service":"checkoutservice","severity_z":40.191},{"evidence_source":"metric","onset_rel_s":1380.0,"rank":3,"service":"node-3","severity_z":14.418},{"evidence_source":"metric","onset_rel_s":1560.0,"rank":4,"service":"emailservice","severity_z":187.556},{"evidence_source":"metric","onset_rel_s":1620.0,"rank":5,"service":"istio-egressgateway","severity_z":107.296},{"evidence_source":"metric","onset_rel_s":1620.0,"rank":6,"service":"cartservice","severity_z":30.613},{"evidence_source":"metric","onset_rel_s":1620.0,"rank":7,"service":"node-2","severity_z":14.044},{"evidence_source":"metric","onset_rel_s":1800.0,"rank":8,"service":"adservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1800.0,"rank":9,"service":"adservice2","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1800.0,"rank":10,"service":"node-5","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1800.0,"rank":11,"service":"istio-ingressgateway","severity_z":435.673},{"evidence_source":"metric","onset_rel_s":1800.0,"rank":12,"service":"cartservice2","severity_z":73.537},{"evidence_source":"metric","onset_rel_s":1920.0,"rank":13,"service":"node-1","severity_z":43.5},{"evidence_source":"metric","onset_rel_s":2160.0,"rank":14,"service":"currencyservice2","severity_z":22.063}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"cartservice","caller":"checkoutservice"},{"callee":"emailservice","caller":"checkoutservice"},{"callee":"paymentservice","caller":"checkoutservice"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"high","reason":"Rank emailservice-0 first because emailservice-0 has direct trace evidence; although checkoutservice-0 is salient, the caller path checkoutservice -> emailservice means a disturbance in the callee can propagate back toward that caller-side symptom. The remaining entries preserve evidence-supported alternatives so the ranking retains calibrated uncertainty instead of collapsing to one answer.","services":["emailservice-0","node-5","adservice2","adservice","istio-ingressgateway-565bffd4d-4nr6v"]}
