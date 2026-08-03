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
opaque_id: INC-C8377EA1FDB6
observation_window={"duration_rel_s":2340.0,"source_metric_rows":40}
selection_summary={"candidate_count":63,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":1448,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","adservice-grpc","adservice-http","adservice2","adservice2-0","cartservice-0","cartservice-1","cartservice-2","cartservice-grpc","cartservice2-0","checkoutservice-0","checkoutservice-1","checkoutservice-2","checkoutservice-grpc","checkoutservice2-0","currencyservice-0","currencyservice-1","currencyservice-2","currencyservice-grpc","currencyservice2-0","emailservice-0","emailservice-1","emailservice-2","emailservice-grpc","emailservice2-0","frontend-0","frontend-1","frontend-2","frontend-http","frontend2-0","istio-egressgateway-7bfdcc9d86-zpjpg","istio-ingressgateway-565bffd4d-6bl7m","node-1","node-2","node-3","node-4","node-5","node-6","paymentservice-0","paymentservice-1","paymentservice-2","paymentservice-grpc","paymentservice2-0","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","productcatalogservice-grpc","productcatalogservice2-0","recommendationservice-0","recommendationservice-1","recommendationservice-2","recommendationservice-grpc","recommendationservice2-0","redis-cart-0","redis-cart2-0","shippingservice-0","shippingservice-1","shippingservice-2","shippingservice-grpc","shippingservice2-0"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[18.281,54.844,91.406,127.969,164.531,201.094,237.656,274.219,310.781,347.344,383.906,420.469,457.031,493.594,530.156,566.719,603.281,639.844,676.406,712.969,749.531,786.094,822.656,859.219,895.781,932.344,968.906,1005.469,1042.031,1078.594,1115.156,1151.719,1188.281,1224.844,1261.406,1297.969,1334.531,1371.094,1407.656,1444.219,1480.781,1517.344,1553.906,1590.469,1627.031,1663.594,1700.156,1736.719,1773.281,1809.844,1846.406,1882.969,1919.531,1956.094,1992.656,2029.219,2065.781,2102.344,2138.906,2175.469,2212.031,2248.594,2285.156,2321.719]
[M1] rank=1 service=istio-egressgateway-7bfdcc9d86-zpjpg metric=istio_agent_go_gc_duration_seconds.1.0 baseline=0.000188 peak=0.000154 signed_z=-999.0 onset_bin=0 onset_rel_s=18.281 persistence_bins=40
values_compact=delta:0.000188,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-0.000034,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M2] rank=2 service=node-4 metric=system.disk.pct_usage baseline=43.19 peak=43.2 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:43.19,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.01,-0.01,0,0,0
missing_mask_bits=0110010110101011010110010110101011010011100101101001110010110101
observed_counts_compact=csv:1,0,0,1,1,0,1,0,0,1,0,1,0,1,0,0,1,0,1,0,0,1,1,0,1,0,0,1,0,1,0,1,0,0,1,0,1,1,0,0,0,1,1,0,1,0,0,1,0,1,1,0,0,0,1,1,0,1,0,0,1,0,1,0
[M3] rank=3 service=currencyservice-2 metric=container_memory_usage_MB baseline=255.989844 peak=251.677734 signed_z=-229.979 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:255.996094,0,0,0,0,0,0,-0.0625,0.0625,0,0,0,0,0,0,-0.0625,0.0625,0,0,0,-0.039063,-0.023437,0.0625,0,0,0,0,0,-0.046875,0.046875,0,-0.0625,-4.25586,4.31836,-0.023438,-0.074218,-1.548829,1.646485,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M4] rank=4 service=paymentservice-1 metric=container_network_receive_MB.eth0 baseline=0.022685 peak=0.602269 signed_z=219.067 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.018233,0.006256,-0.002575,-0.000712,0.002373,-0.004271,0.00444,0.002622,-0.000294,0.000839,-0.004137,-0.001257,-0.000275,0.002955,-0.001707,-0.00319,0.007594,-0.004835,0.001372,-0.005437,0.006327,-0.0008,-0.002767,0.001693,0.000372,-0.00206,0.006723,-0.004609,0.579396,-0.584937,0.006777,-0.001424,-0.000624,-0.001337,0.00236,0.001041,-0.000366,-0.004327,0.001565,0.002323
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M5] rank=5 service=adservice2 metric=java_lang_GarbageCollector_LastGcInfo_memoryUsageBeforeGc_used.Eden_Space.Copy baseline=26804215.333333 peak=26798080.666667 signed_z=-208.732 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:26804224,0,0,-130,86.666667,43.333333,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-6143.333333,6143.333333,0,0,0,0,0,0,0,0,0,-861.333333,861.333333,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M6] rank=6 service=node-2 metric=system.mem.free baseline=9693.65 peak=10955.0 signed_z=138.345 onset_bin=59 onset_rel_s=2175.469 persistence_bins=4
values_compact=delta:9693,0,7,6,-13,-1,3,-3,-2,-2,2,2,-8,-1,4,38,-33,-5,1,15,-18,0,-1,0,-2,-2,3,1,12,29,-28,-19,-5,2,0,1280,-34,-34,-33,-37
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M7] rank=7 service=paymentservice-2 metric=container_network_receive_MB.eth0 baseline=0.023847 peak=0.316808 signed_z=101.357 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.024323,-0.003862,0.004331,-0.00165,0.002613,-0.005663,0.005454,-0.005207,0.011509,-0.003974,-0.004968,-0.000189,0.001062,0.001272,-0.004755,0.005748,-0.002476,-0.002217,0.004753,-0.005151,0.295855,-0.008194,-0.284688,0.003033,-0.005716,0.003763,-0.002954,-0.000573,0.000031,0.005093,-0.003085,-0.000702,0.000863,-0.001685,0.001574,0.000158,0.001605,-0.003934,0.000228,0.001862
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M8] rank=8 service=paymentservice2-0 metric=container_network_receive_MB.eth0 baseline=0.024232 peak=0.314703 signed_z=97.495 onset_bin=36 onset_rel_s=1334.531 persistence_bins=2
values_compact=delta:0.023445,0.008941,-0.006827,-0.002952,0.002885,-0.000262,-0.001174,0.005135,-0.00302,0.001179,-0.00263,-0.004111,0.000024,0.004574,-0.005568,0.002928,-0.000379,-0.00055,0.001583,-0.000499,-0.001449,0.00247,0.288366,0.002594,-0.294713,0.003841,-0.002055,0.002553,-0.001071,-0.002805,0.000486,0.0003,0.00725,-0.006858,0.001296,-0.00054,-0.001714,0.002174,-0.000832,-0.000149
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M9] rank=9 service=node-2 metric=system.net.packets_in.count baseline=425.4875 peak=1808.83 signed_z=53.846 onset_bin=54 onset_rel_s=1992.656 persistence_bins=3
values_compact=delta:405.17,8.87,14.69,8.53,-39.15,24.51,-33.13,-20.51,23.86,30.28,-14.94,24.2,45.47,-30.98,0.04,-10.25,25.7,-16.35,-4.72,-10.41,35.72,40.87,3.29,-9.04,-5.84,6.38,-7.05,14.15,-7.49,-12.26,-0.08,2.19,751.25,565.86,-1157.66,-70.37,-105.91,14.62,-17.45,1.43
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M10] rank=10 service=node-2 metric=system.net.tcp.in_segs baseline=1032.568 peak=2398.75 signed_z=48.975 onset_bin=54 onset_rel_s=1992.656 persistence_bins=3
values_compact=delta:1011.46,38.26,-52.23,40.88,-46.08,44.04,-19.96,-11.24,-24.1,69.87,-39.11,43.56,-2.81,8.58,-50.6,60.76,-29.65,42.02,-62.54,42.17,-124.06,125.35,-36.64,37.32,-49.27,49.84,-31.85,43.45,-39.79,-2.11,-12.8,36.3,703.73,636,-1035.26,-163.24,-197.33,23.48,-42.73,59.33
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M11] rank=11 service=node-2 metric=system.net.bytes_rcvd baseline=636698.294 peak=2994728.29 signed_z=48.29 onset_bin=36 onset_rel_s=1334.531 persistence_bins=18
values_compact=delta:603045.29,12391.78,11801.14,25201.86,-56324.61,24117.18,-51020.89,-43381.75,53257.04,52151.03,-28368.28,61167.07,69803.28,-51207.93,9150.86,-38721.07,56903.29,-52557.29,8874.71,-14072.5,338802.86,103909.79,9781.07,-8139.43,932,-7211.43,-11370.71,7714.43,14585.28,-21511.93,-10771.93,6324.65,1101125.43,818348,-1711934.15,-97089,-128891.78,2253.64,-15100.14,-12936.65
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M12] rank=12 service=redis-cart-0 metric=container_network_receive_MB.eth0 baseline=0.065523 peak=0.641597 signed_z=45.941 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.054991,-0.001905,0.004384,-0.003088,-0.003843,0.007387,-0.007775,-0.010377,0.039763,-0.016365,0.004332,0.016614,-0.006388,0.00544,-0.010542,0.003943,-0.007286,0.009577,-0.015998,0.013833,-0.01186,0.001139,0.009865,-0.023123,0.588879,-0.574899,0.001268,0.000204,-0.0093,0.005837,-0.001535,-0.007066,0.014159,-0.004482,-0.01157,0.001958,0.005971,-0.001702,0.004152,-0.002126
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[2040.0,2340.0]

=== LOG SUMMARY ===
{"entries":[{"error_logs":24,"error_pct":6.38,"service":"emailservice-1","total_logs":376},{"error_logs":23,"error_pct":6.01,"service":"emailservice-0","total_logs":383},{"error_logs":14,"error_pct":4.75,"service":"emailservice-2","total_logs":295},{"error_logs":6,"error_pct":0.02,"service":"frontend-1","total_logs":39439},{"error_logs":5,"error_pct":0.36,"service":"checkoutservice-1","total_logs":1385},{"error_logs":2,"error_pct":0.14,"service":"checkoutservice-2","total_logs":1380},{"error_logs":1,"error_pct":0.07,"service":"checkoutservice-0","total_logs":1358},{"error_logs":1,"error_pct":0.0,"service":"frontend-2","total_logs":32858}],"mode":"errors","omitted_services":23,"service_count":31}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":221.8,"error_pct":0.0,"p95_during_ms":0.5804499999999997,"p95_pre_ms":0.18039999999999998,"service":"paymentservice-0","spans":82},{"delta_pct":-100.0,"error_pct":0.0,"p95_during_ms":0.0,"p95_pre_ms":1.0,"service":"cartservice-0","spans":4234},{"delta_pct":30.7,"error_pct":0.0,"p95_during_ms":0.115,"p95_pre_ms":0.088,"service":"shippingservice-0","spans":580},{"delta_pct":-22.5,"error_pct":0.0,"p95_during_ms":46.38145000000001,"p95_pre_ms":59.870700000000035,"service":"checkoutservice2-0","spans":1604},{"delta_pct":19.8,"error_pct":0.0,"p95_during_ms":0.1137999999999999,"p95_pre_ms":0.095,"service":"shippingservice-1","spans":584},{"delta_pct":-17.4,"error_pct":0.0,"p95_during_ms":0.02394999999999999,"p95_pre_ms":0.029,"service":"adservice2-0","spans":1923},{"delta_pct":-16.2,"error_pct":0.0,"p95_during_ms":0.02180000000000001,"p95_pre_ms":0.026,"service":"adservice-1","spans":1279},{"delta_pct":13.8,"error_pct":0.0,"p95_during_ms":0.023900000000000005,"p95_pre_ms":0.021,"service":"adservice-2","spans":1279}],"omitted_services":32,"service_count":40}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=14 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":1200.0,"rank":1,"service":"node-1","severity_z":31.514},{"evidence_source":"metric","onset_rel_s":1200.0,"rank":2,"service":"node-6","severity_z":26.058},{"evidence_source":"metric","onset_rel_s":1320.0,"rank":3,"service":"paymentservice2","severity_z":97.495},{"evidence_source":"metric","onset_rel_s":1440.0,"rank":4,"service":"redis-cart","severity_z":45.941},{"evidence_source":"metric","onset_rel_s":1500.0,"rank":5,"service":"adservice2","severity_z":208.732},{"evidence_source":"metric","onset_rel_s":1500.0,"rank":6,"service":"adservice","severity_z":36.852},{"evidence_source":"metric","onset_rel_s":1620.0,"rank":7,"service":"checkoutservice2","severity_z":32.127},{"evidence_source":"metric","onset_rel_s":1680.0,"rank":8,"service":"paymentservice","severity_z":219.067},{"evidence_source":"metric","onset_rel_s":1680.0,"rank":9,"service":"cartservice","severity_z":34.393},{"evidence_source":"metric","onset_rel_s":1920.0,"rank":10,"service":"currencyservice","severity_z":229.979},{"evidence_source":"metric","onset_rel_s":1980.0,"rank":11,"service":"node-4","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":2100.0,"rank":12,"service":"istio-egressgateway","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":2100.0,"rank":13,"service":"node-2","severity_z":138.345},{"evidence_source":"metric","onset_rel_s":2100.0,"rank":14,"service":"istio-ingressgateway","severity_z":40.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"paymentservice2","caller":"checkoutservice2"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"medium","reason":"Rank cartservice-0 first because cartservice-0 has direct trace evidence; node-1 is second despite propagation rank 1 because onset ordering alone does not establish the causal origin.","services":["cartservice-0","node-1"]}
