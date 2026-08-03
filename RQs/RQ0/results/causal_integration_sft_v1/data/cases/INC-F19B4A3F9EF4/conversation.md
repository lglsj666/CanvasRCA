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
opaque_id: INC-F19B4A3F9EF4
observation_window={"duration_rel_s":2100.0,"source_metric_rows":36}
selection_summary={"candidate_count":63,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":1334,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","adservice-grpc","adservice-http","adservice2","adservice2-0","cartservice-0","cartservice-1","cartservice-2","cartservice-grpc","cartservice2-0","checkoutservice-0","checkoutservice-1","checkoutservice-2","checkoutservice-grpc","checkoutservice2-0","currencyservice-0","currencyservice-1","currencyservice-2","currencyservice-grpc","currencyservice2-0","emailservice-0","emailservice-1","emailservice-2","emailservice-grpc","emailservice2-0","frontend-0","frontend-1","frontend-2","frontend-http","frontend2-0","istio-egressgateway-7bfdcc9d86-zpjpg","istio-ingressgateway-565bffd4d-6bl7m","node-1","node-2","node-3","node-4","node-5","node-6","paymentservice-0","paymentservice-1","paymentservice-2","paymentservice-grpc","paymentservice2-0","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","productcatalogservice-grpc","productcatalogservice2-0","recommendationservice-0","recommendationservice-1","recommendationservice-2","recommendationservice-grpc","recommendationservice2-0","redis-cart-0","redis-cart2-0","shippingservice-0","shippingservice-1","shippingservice-2","shippingservice-grpc","shippingservice2-0"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[16.406,49.219,82.031,114.844,147.656,180.469,213.281,246.094,278.906,311.719,344.531,377.344,410.156,442.969,475.781,508.594,541.406,574.219,607.031,639.844,672.656,705.469,738.281,771.094,803.906,836.719,869.531,902.344,935.156,967.969,1000.781,1033.594,1066.406,1099.219,1132.031,1164.844,1197.656,1230.469,1263.281,1296.094,1328.906,1361.719,1394.531,1427.344,1460.156,1492.969,1525.781,1558.594,1591.406,1624.219,1657.031,1689.844,1722.656,1755.469,1788.281,1821.094,1853.906,1886.719,1919.531,1952.344,1985.156,2017.969,2050.781,2083.594]
[M1] rank=1 service=node-3 metric=system.disk.pct_usage baseline=42.04 peak=42.02 signed_z=-999.0 onset_bin=62 onset_rel_s=2050.781 persistence_bins=2
values_compact=delta:42.04,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-0.02,0,0,0,0
missing_mask_bits=0010101010010101010100101010101001010101010010101010100101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1
[M2] rank=2 service=node-4 metric=system.disk.pct_usage baseline=43.34 peak=43.32 signed_z=-999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:43.34,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-0.02,0,0
missing_mask_bits=1010101110010111010101101011101001110101011010101110100111010101
observed_counts_compact=csv:0,1,0,1,0,1,0,0,0,1,1,0,1,0,0,0,1,0,1,0,1,0,0,1,0,1,0,0,0,1,0,1,1,0,0,0,1,0,1,0,1,0,0,1,0,1,0,1,0,0,0,1,0,1,1,0,0,0,1,0,1,0,1,0
[M3] rank=3 service=paymentservice-0 metric=container_cpu_system_seconds baseline=0.0 peak=0.01 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.01,0,-0.01,0,0
missing_mask_bits=0010101010010101010100101010101001010101010010101010100101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1
[M4] rank=4 service=node-4 metric=system.net.bytes_rcvd baseline=331917.822778 peak=3698072.89 signed_z=965.4 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:336738.25,-5477.89,5140.2,-3116.98,1990.03,-11111.08,11223.61,-4161.06,1865.89,-5919.66,8769.94,-5813.44,3206.8,-2532.5,2218.42,-6640.95,5900.28,-3637.19,1500553.55,-1427308.66,-72663.48,9583.56,-6299.78,1376.67,-5726.92,3012.17,10510.94,-5020.47,-5213.44,-414.37,2022.64,-4730.27,3369748.08,-2727536.56,-344031.5,-288868.3
missing_mask_bits=0010101010010101010100101010101001010101010010101010100101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1
[M5] rank=5 service=node-6 metric=system.net.bytes_sent baseline=122292.533333 peak=563741.02 signed_z=648.821 onset_bin=62 onset_rel_s=2050.781 persistence_bins=2
values_compact=delta:121819.83,571.33,-239.85,526.26,-1307.08,372.2,1572.88,-682.69,526.23,-749.83,-516.56,1919.38,-2494.8,685.76,-381.53,632.79,760.19,-1334.34,368.55,132.31,703.94,-2221.98,1907.5,-138.46,438.63,89.26,-1048.19,851.36,-917.89,-370.59,434635.79,7630.62,-104336.04,-49061.47,-48746.67,-42227.71
missing_mask_bits=0010101010010101010100101010101001010101010010101010100101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1
[M6] rank=6 service=node-6 metric=system.net.bytes_rcvd baseline=119488.617778 peak=573629.6 signed_z=607.506 onset_bin=62 onset_rel_s=2050.781 persistence_bins=2
values_compact=delta:118954.25,82.03,83.07,1491.71,-2239.17,169.28,1737.07,-18.93,147.36,-787.27,-945.9,2313.44,-1951.1,-0.03,-62.32,219.27,750.41,-187.18,-785.16,-6.44,992.35,-2067.27,2409.04,-631.33,-41.55,327.77,-418.72,464.59,-1435.59,121.89,454542.7,401.33,-104766.67,-51228.89,-50011.75,-43191.6
missing_mask_bits=0010101010010101010100101010101001010101010010101010100101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1
[M7] rank=7 service=node-4 metric=system.net.bytes_sent baseline=373653.978889 peak=5199189.78 signed_z=458.524 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:375730.89,-14628.2,6138.25,8621.56,-5474.31,-14369.69,14627.19,-5693.36,23033.34,-24295.28,11928.05,14361.42,-14649.22,-3693.56,29420.42,-33107.39,9404.53,-4129.08,951601.33,-432348.28,-536882.72,19230.11,-16447.31,2869.73,-6352.36,11364.55,5773.86,-4751,2087.31,-9692.09,2417.06,-5679.47,4842773.5,-3657570,-863958.11,-295344.25
missing_mask_bits=0010101010010101010100101010101001010101010010101010100101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1
[M8] rank=8 service=node-3 metric=system.net.tcp.retrans_segs baseline=0.021111 peak=9.11 signed_z=448.936 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.03,0,0,-0.01,-0.02,0.05,-0.05,0.02,0,0.01,0,-0.03,0,0.02,-0.02,0,0.08,-0.06,-0.02,0.05,0,-0.03,0.05,-0.07,0,0,0,0.02,0,-0.02,9.11,-9.09,-0.02,0,0.02,0
missing_mask_bits=0010101010010101010100101010101001010101010010101010100101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1
[M9] rank=9 service=adservice2 metric=jvm_memory_pool_MB_used.Tenured_Gen baseline=35.909621 peak=36.359893 signed_z=441.278 onset_bin=53 onset_rel_s=1755.469 persistence_bins=7
values_compact=delta:35.90815,0.00032,0.000046,0,0,0.000046,0.000015,0.000046,0.001513,0.000287,0.000061,0.000061,0.000021,0.00004,0,0,0,0.000061,0.000006,0.000055,0.000041,0.000122,0.000021,0,0.064254,0.12851,0.000032,0.000113,0.000147,0.000188,0.000234,0.095804,0.09559,0.000056,0.000259,0.063794
missing_mask_bits=0010101010010101010100101010101001010101010010101010100101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1
[M10] rank=10 service=adservice2 metric=jvm_memory_pool_allocated_MB_total.Tenured_Gen baseline=42.746186 peak=43.196468 signed_z=441.062 onset_bin=53 onset_rel_s=1755.469 persistence_bins=7
values_compact=delta:42.744687,0.000346,0.000061,0,0,0.000041,0.00002,0.000036,0.00138,0.000431,0.000056,0.000061,0.00002,0.000046,0,0,0,0.000056,0.000005,0.000061,0.000035,0.000117,0.000031,0,0.048191,0.144573,0.000021,0.000124,0.000122,0.000199,0.000228,0.079889,0.111525,0.000041,0.000259,0.063806
missing_mask_bits=0010101010010101010100101010101001010101010010101010100101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1
[M11] rank=11 service=adservice2 metric=java_lang_GarbageCollector_LastGcInfo_memoryUsageAfterGc_used.Tenured_Gen.Copy baseline=37653961.925926 peak=38126107.333333 signed_z=439.831 onset_bin=53 onset_rel_s=1755.469 persistence_bins=7
values_compact=delta:37652386.666667,357.333333,64,0,0,42.666667,21.333333,42.666667,1592,301.333333,58.666667,64,21.333333,48,0,0,0,58.666667,10.666666,58.666667,37.333333,122.666667,32,0,50532,151596,26.666667,125.333333,138.666667,197.333333,240,83768.666667,116943.333333,48,282.666667,66888.666666
missing_mask_bits=0010101010010101010100101010101001010101010010101010100101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1
[M12] rank=12 service=adservice2 metric=java_lang_MemoryPool_PeakUsage_used.Tenured_Gen baseline=37653961.62963 peak=38126107.333333 signed_z=439.713 onset_bin=53 onset_rel_s=1755.469 persistence_bins=7
values_compact=delta:37652386.666667,357.333333,64,0,0,42.666667,21.333333,37.333333,1597.333334,301.333333,58.666667,64,21.333333,48,0,0,0,58.666667,10.666666,58.666667,37.333333,122.666667,32,0,50532,151596,26.666667,125.333333,138.666667,197.333333,240,83768.666667,116943.333333,48,282.666667,66888.666666
missing_mask_bits=0010101010010101010100101010101001010101010010101010100101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[1800.0,2100.0]

=== LOG SUMMARY ===
{"entries":[{"change_pct":-100.0,"n_during":0,"n_pre":2,"service":"frontend-1"},{"change_pct":-92.1,"n_during":6,"n_pre":76,"service":"emailservice-1"},{"change_pct":-86.8,"n_during":9,"n_pre":68,"service":"paymentservice-0"},{"change_pct":-86.2,"n_during":9,"n_pre":65,"service":"emailservice-0"},{"change_pct":-86.1,"n_during":51,"n_pre":367,"service":"checkoutservice-0"},{"change_pct":-85.9,"n_during":94,"n_pre":666,"service":"adservice-2"},{"change_pct":-85.9,"n_during":53,"n_pre":375,"service":"checkoutservice-1"},{"change_pct":-85.5,"n_during":96,"n_pre":664,"service":"adservice-1"}],"mode":"volume","omitted_services":23,"service_count":31}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":107.7,"error_pct":0.0,"p95_during_ms":0.0509999999999998,"p95_pre_ms":0.024550000000000013,"service":"adservice-0","spans":379},{"delta_pct":95.9,"error_pct":0.0,"p95_during_ms":0.25369999999999976,"p95_pre_ms":0.1295,"service":"shippingservice-1","spans":174},{"delta_pct":-53.2,"error_pct":0.0,"p95_during_ms":0.2209,"p95_pre_ms":0.47179999999999983,"service":"paymentservice-2","spans":25},{"delta_pct":-33.3,"error_pct":0.0,"p95_during_ms":0.1645,"p95_pre_ms":0.2465,"service":"shippingservice-2","spans":177},{"delta_pct":-28.5,"error_pct":0.0,"p95_during_ms":0.0835,"p95_pre_ms":0.11674999999999924,"service":"shippingservice-0","spans":176},{"delta_pct":-25.0,"error_pct":0.0,"p95_during_ms":0.75,"p95_pre_ms":1.0,"service":"cartservice-1","spans":1267},{"delta_pct":-13.6,"error_pct":0.0,"p95_during_ms":0.017799999999999983,"p95_pre_ms":0.020599999999999966,"service":"adservice-2","spans":378},{"delta_pct":-10.8,"error_pct":0.0,"p95_during_ms":0.2247,"p95_pre_ms":0.2519999999999998,"service":"paymentservice2-0","spans":116}],"omitted_services":31,"service_count":39}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=16 omitted_edges=3
[{"evidence_source":"metric","onset_rel_s":1080.0,"rank":1,"service":"frontend","severity_z":202.663},{"evidence_source":"metric","onset_rel_s":1080.0,"rank":2,"service":"cartservice","severity_z":118.587},{"evidence_source":"metric","onset_rel_s":1080.0,"rank":3,"service":"checkoutservice","severity_z":76.067},{"evidence_source":"metric","onset_rel_s":1200.0,"rank":4,"service":"recommendationservice","severity_z":95.462},{"evidence_source":"metric","onset_rel_s":1320.0,"rank":5,"service":"cartservice2","severity_z":88.572},{"evidence_source":"metric","onset_rel_s":1440.0,"rank":6,"service":"paymentservice2","severity_z":141.152},{"evidence_source":"metric","onset_rel_s":1500.0,"rank":7,"service":"adservice","severity_z":101.132},{"evidence_source":"metric","onset_rel_s":1800.0,"rank":8,"service":"node-6","severity_z":648.821},{"evidence_source":"metric","onset_rel_s":1800.0,"rank":9,"service":"node-5","severity_z":90.909},{"evidence_source":"metric","onset_rel_s":1860.0,"rank":10,"service":"node-3","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1860.0,"rank":11,"service":"paymentservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1860.0,"rank":12,"service":"adservice2","severity_z":441.278},{"evidence_source":"metric","onset_rel_s":1920.0,"rank":13,"service":"node-4","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1920.0,"rank":14,"service":"node-2","severity_z":218.378}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"cartservice","caller":"checkoutservice"},{"callee":"paymentservice","caller":"checkoutservice"},{"callee":"adservice","caller":"frontend"},{"callee":"cartservice","caller":"frontend"},{"callee":"checkoutservice","caller":"frontend"},{"callee":"recommendationservice","caller":"frontend"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"medium","reason":"Rank node-4 first because node-4 has direct system.disk.pct_usage evidence (signed-z -999, persistence 0 bins); frontend-0 is second despite propagation rank 1 because onset ordering alone does not establish the causal origin.","services":["node-4","frontend-0"]}
