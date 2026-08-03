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
opaque_id: INC-6B265C849A77
observation_window={"duration_rel_s":2340.0,"source_metric_rows":40}
selection_summary={"candidate_count":63,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":1527,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","adservice-grpc","adservice-http","adservice2","adservice2-0","cartservice-0","cartservice-1","cartservice-2","cartservice-grpc","cartservice2-0","checkoutservice-0","checkoutservice-1","checkoutservice-2","checkoutservice-grpc","checkoutservice2-0","currencyservice-0","currencyservice-1","currencyservice-2","currencyservice-grpc","currencyservice2-0","emailservice-0","emailservice-1","emailservice-2","emailservice-grpc","emailservice2-0","frontend-0","frontend-1","frontend-2","frontend-http","frontend2-0","istio-egressgateway-7bfdcc9d86-g2d4q","istio-ingressgateway-565bffd4d-rn678","node-1","node-2","node-3","node-4","node-5","node-6","paymentservice-0","paymentservice-1","paymentservice-2","paymentservice-grpc","paymentservice2-0","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","productcatalogservice-grpc","productcatalogservice2-0","recommendationservice-0","recommendationservice-1","recommendationservice-2","recommendationservice-grpc","recommendationservice2-0","redis-cart-0","redis-cart2-0","shippingservice-0","shippingservice-1","shippingservice-2","shippingservice-grpc","shippingservice2-0"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[18.281,54.844,91.406,127.969,164.531,201.094,237.656,274.219,310.781,347.344,383.906,420.469,457.031,493.594,530.156,566.719,603.281,639.844,676.406,712.969,749.531,786.094,822.656,859.219,895.781,932.344,968.906,1005.469,1042.031,1078.594,1115.156,1151.719,1188.281,1224.844,1261.406,1297.969,1334.531,1371.094,1407.656,1444.219,1480.781,1517.344,1553.906,1590.469,1627.031,1663.594,1700.156,1736.719,1773.281,1809.844,1846.406,1882.969,1919.531,1956.094,1992.656,2029.219,2065.781,2102.344,2138.906,2175.469,2212.031,2248.594,2285.156,2321.719]
[M1] rank=1 service=node-5 metric=system.process.zombie.num baseline=0.0 peak=1.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,-1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M2] rank=2 service=shippingservice-0 metric=container_fs_inodes./dev/vda1 baseline=0.0 peak=20.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,20,-20,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M3] rank=3 service=shippingservice-0 metric=container_fs_usage_MB./dev/vda1 baseline=33.118164 peak=656.277344 signed_z=999.0 onset_bin=36 onset_rel_s=1334.531 persistence_bins=18
values_compact=delta:33.011719,0.007812,0.015625,0.011719,0.011719,0.007812,0.011719,0.011719,0.011718,0.011719,0.011719,0.007812,0.015626,0.007812,0.011719,0.011719,0.011718,0.011719,0.011719,0.007812,622.972656,0.011719,0.011719,0.011719,0.011719,0.011718,0.011719,0.011719,-600.578125,0.011719,0.011718,0.015625,0.003907,0.015624,0.011719,0.011719,0.007812,0.011719,0.011719,0.007812
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M4] rank=4 service=shippingservice-1 metric=container_fs_inodes./dev/vda1 baseline=0.0 peak=20.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,20,-20,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M5] rank=5 service=shippingservice-1 metric=container_fs_usage_MB./dev/vda1 baseline=33.118164 peak=656.269531 signed_z=999.0 onset_bin=36 onset_rel_s=1334.531 persistence_bins=18
values_compact=delta:33.013672,0.005859,0.017578,0.011719,0.009766,0.003906,0.011719,0.017578,0.011719,0.011718,0.009766,0.009766,0.011718,0.011719,0.011719,0.011719,0.011718,0.00586,0.011719,0.007812,622.972656,0.017578,0.011719,0.011719,0.011719,0.009765,0.009766,0.005859,-600.574219,0.017579,0.011718,0.011719,0.011719,0.005859,0.017578,0.009766,0.003906,0.017578,0.011719,0.005859
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M6] rank=6 service=shippingservice-1 metric=container_memory_mapped_file baseline=28774.4 peak=3997696.0 signed_z=999.0 onset_bin=31 onset_rel_s=1151.719 persistence_bins=21
values_compact=delta:28672,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,2048,6144,708608,393216,-18432,-20480,36864,26624,2834432,-2537472,59392,22528,38912,18432,8192,30720,2048,26624,20480,4096,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M7] rank=7 service=shippingservice-2 metric=container_fs_inodes./dev/vda1 baseline=0.0 peak=20.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,20,-20,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M8] rank=8 service=shippingservice-2 metric=container_fs_usage_MB./dev/vda1 baseline=33.117676 peak=656.273438 signed_z=999.0 onset_bin=36 onset_rel_s=1334.531 persistence_bins=18
values_compact=delta:33.011719,0.013672,0.011718,0.00586,0.017578,0.011719,0.005859,0.007813,0.011718,0.011719,0.019531,0.003906,0.011719,0.011719,0.011719,0.007812,0.017578,0.00586,0.011719,0.011718,622.972656,0.017579,0.005859,0.007812,0.017579,0.011718,0.011719,0.00586,-600.574219,0.015625,0.011718,0.007813,0.007813,0.015624,0.007813,0.017578,0.005859,0.011719,0.013672,0.005859
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M9] rank=9 service=shippingservice2-0 metric=container_fs_inodes./dev/vda1 baseline=0.0 peak=20.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,20,-20,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M10] rank=10 service=shippingservice2-0 metric=container_fs_usage_MB./dev/vda1 baseline=27.418164 peak=650.492188 signed_z=999.0 onset_bin=36 onset_rel_s=1334.531 persistence_bins=18
values_compact=delta:27.355469,0.007812,0.003907,0.007812,0.003906,0.011719,0.003906,0.007813,0.007812,0.003906,0.007813,0.007813,0.003906,0.007812,0.007813,0.003906,0.007813,0.003906,0.011718,0.003907,622.96875,0.003906,0.011719,0.003906,0.007812,0,0.011719,0.003907,-600.578126,0.003907,0.011719,0.003906,0.007812,0.003906,0.007813,0.007813,0.003906,0.007812,0.007813,0.003906
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M11] rank=11 service=paymentservice-1 metric=container_network_receive_MB.eth0 baseline=0.022162 peak=0.580121 signed_z=290.539 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.019262,0.001106,0.002771,-0.00144,0.002318,-0.004194,0.002504,0.000052,-0.000575,0.001674,-0.003447,0.005301,-0.006987,0.004053,-0.00124,0.00526,-0.003739,0.000022,0.000157,0.000161,-0.003453,0.002575,-0.001461,0.003129,-0.001503,-0.00066,-0.00013,0.000647,0.557958,-0.558677,0.001738,0.00024,-0.000758,0.000265,-0.000979,-0.001675,-0.00119,0.004122,0.0005,-0.001388
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M12] rank=12 service=shippingservice2-0 metric=container_memory_failcnt baseline=3048.75 peak=2397029.0 signed_z=180.145 onset_bin=31 onset_rel_s=1151.719 persistence_bins=21
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,60975,309450,308926.5,268364,298126.5,302761.5,294245.5,257616,265661.5,30902.5,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[1140.0,1680.0]

=== LOG SUMMARY ===
{"entries":[{"error_logs":5344,"error_pct":9.02,"service":"adservice-0","total_logs":59272},{"error_logs":1022,"error_pct":1.3,"service":"frontend-2","total_logs":78889},{"error_logs":930,"error_pct":1.29,"service":"frontend-0","total_logs":71908},{"error_logs":720,"error_pct":1.29,"service":"frontend-1","total_logs":55981}],"mode":"errors","omitted_services":27,"service_count":31}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":12060.8,"error_pct":0.0,"p95_during_ms":8.707099999999999,"p95_pre_ms":0.0715999999999999,"service":"shippingservice-0","spans":1252},{"delta_pct":11598.0,"error_pct":0.0,"p95_during_ms":8.305600000000016,"p95_pre_ms":0.071,"service":"shippingservice-2","spans":1252},{"delta_pct":6341.1,"error_pct":0.0,"p95_during_ms":4.6376,"p95_pre_ms":0.072,"service":"shippingservice-1","spans":1255},{"delta_pct":5516.3,"error_pct":0.0,"p95_during_ms":4.0550000000000015,"p95_pre_ms":0.07219999999999993,"service":"shippingservice2-0","spans":730},{"delta_pct":11.9,"error_pct":0.0,"p95_during_ms":41.135349999999995,"p95_pre_ms":36.7658,"service":"checkoutservice-0","spans":2116},{"delta_pct":10.5,"error_pct":0.0,"p95_during_ms":0.021,"p95_pre_ms":0.019,"service":"adservice-2","spans":2671},{"delta_pct":10.0,"error_pct":0.0,"p95_during_ms":0.15184999999999998,"p95_pre_ms":0.138,"service":"paymentservice-2","spans":179},{"delta_pct":9.0,"error_pct":0.0,"p95_during_ms":39.64675,"p95_pre_ms":36.37325,"service":"checkoutservice-1","spans":2090}],"omitted_services":32,"service_count":40}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=14 omitted_edges=1
[{"evidence_source":"trace","onset_rel_s":1145.4,"rank":1,"service":"shippingservice","severity_z":999.0},{"evidence_source":"trace","onset_rel_s":1194.6,"rank":2,"service":"shippingservice2","severity_z":425.907},{"evidence_source":"metric","onset_rel_s":1200.0,"rank":3,"service":"adservice","severity_z":19.595},{"evidence_source":"metric","onset_rel_s":1260.0,"rank":4,"service":"checkoutservice","severity_z":87.3},{"evidence_source":"metric","onset_rel_s":1260.0,"rank":5,"service":"cartservice","severity_z":73.68},{"evidence_source":"metric","onset_rel_s":1260.0,"rank":6,"service":"recommendationservice","severity_z":30.209},{"evidence_source":"metric","onset_rel_s":1320.0,"rank":7,"service":"node-5","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1440.0,"rank":8,"service":"node-1","severity_z":102.105},{"evidence_source":"metric","onset_rel_s":1680.0,"rank":9,"service":"paymentservice","severity_z":290.539},{"evidence_source":"metric","onset_rel_s":1740.0,"rank":10,"service":"currencyservice","severity_z":37.992},{"evidence_source":"metric","onset_rel_s":1980.0,"rank":11,"service":"istio-egressgateway","severity_z":30.87},{"evidence_source":"metric","onset_rel_s":2100.0,"rank":12,"service":"paymentservice2","severity_z":39.297},{"evidence_source":"metric","onset_rel_s":2160.0,"rank":13,"service":"node-2","severity_z":41.846},{"evidence_source":"metric","onset_rel_s":2280.0,"rank":14,"service":"adservice2","severity_z":48.756}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"cartservice","caller":"checkoutservice"},{"callee":"currencyservice","caller":"checkoutservice"},{"callee":"paymentservice","caller":"checkoutservice"},{"callee":"shippingservice","caller":"checkoutservice"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"high","reason":"Rank shippingservice-0 first because shippingservice-0 has direct container_fs_inodes./dev/vda1 evidence (signed-z 999, persistence 0 bins); although checkoutservice-0 is salient, the caller path checkoutservice -> shippingservice means a disturbance in the callee can propagate back toward that caller-side symptom.","services":["shippingservice-0","checkoutservice-0"]}
