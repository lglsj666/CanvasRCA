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
opaque_id: INC-C779F759211C
observation_window={"duration_rel_s":2340.0,"source_metric_rows":40}
selection_summary={"candidate_count":63,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":1537,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","adservice-grpc","adservice-http","adservice2","adservice2-0","cartservice-0","cartservice-1","cartservice-2","cartservice-grpc","cartservice2-0","checkoutservice-0","checkoutservice-1","checkoutservice-2","checkoutservice-grpc","checkoutservice2-0","currencyservice-0","currencyservice-1","currencyservice-2","currencyservice-grpc","currencyservice2-0","emailservice-0","emailservice-1","emailservice-2","emailservice-grpc","emailservice2-0","frontend-0","frontend-1","frontend-2","frontend-http","frontend2-0","istio-egressgateway-7bfdcc9d86-22q7z","istio-ingressgateway-565bffd4d-4nr6v","node-1","node-2","node-3","node-4","node-5","node-6","paymentservice-0","paymentservice-1","paymentservice-2","paymentservice-grpc","paymentservice2-0","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","productcatalogservice-grpc","productcatalogservice2-0","recommendationservice-0","recommendationservice-1","recommendationservice-2","recommendationservice-grpc","recommendationservice2-0","redis-cart-0","redis-cart2-0","shippingservice-0","shippingservice-1","shippingservice-2","shippingservice-grpc","shippingservice2-0"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[18.281,54.844,91.406,127.969,164.531,201.094,237.656,274.219,310.781,347.344,383.906,420.469,457.031,493.594,530.156,566.719,603.281,639.844,676.406,712.969,749.531,786.094,822.656,859.219,895.781,932.344,968.906,1005.469,1042.031,1078.594,1115.156,1151.719,1188.281,1224.844,1261.406,1297.969,1334.531,1371.094,1407.656,1444.219,1480.781,1517.344,1553.906,1590.469,1627.031,1663.594,1700.156,1736.719,1773.281,1809.844,1846.406,1882.969,1919.531,1956.094,1992.656,2029.219,2065.781,2102.344,2138.906,2175.469,2212.031,2248.594,2285.156,2321.719]
[M1] rank=1 service=frontend-2 metric=container_cpu_cfs_throttled_seconds baseline=0.0 peak=0.007472 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.007472,-0.007472,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M2] rank=2 service=node-5 metric=system.disk.free baseline=925530634.971 peak=1286670677.33 signed_z=999.0 onset_bin=41 onset_rel_s=1517.344 persistence_bins=15
values_compact=delta:925505243.43,270043.43,261193.14,-133851.43,-64438.86,-7972.57,-50541.71,-83090.29,-78409.14,-136484.57,17481.14,-35108.57,-52370.29,-85504,-111762.28,73435.43,-1243.43,-26916.57,-62610.29,4608,-117760,-46080,-64000,-72192,-4900.57,361773909.33,-363975.11,-286264.89,-372053.33,-158168832,-113664,-27520,-158720,-92416,123776,-101504,-14848,-157440,-67456,55040
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M3] rank=3 service=node-5 metric=system.disk.total baseline=3767720813.710001 peak=5516931072.0 signed_z=999.0 onset_bin=41 onset_rel_s=1517.344 persistence_bins=15
values_compact=delta:3767720813.71,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1749210258.29,0,0,0,-765279232,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M4] rank=4 service=node-5 metric=system.disk.used baseline=2824074415.5425 peak=4217192903.11 signed_z=999.0 onset_bin=41 onset_rel_s=1517.344 persistence_bins=15
values_compact=delta:2824099840,-270043.43,-261266.28,133997.71,64365.71,7899.43,50614.86,83090.29,78409.14,136338.28,-17554.28,35401.14,52370.29,85430.85,111762.29,-73435.43,1170.29,26916.57,62610.28,-4681.14,117906.29,45933.71,64073.14,72265.15,4973.71,1391462334.99,363633.77,286264.89,372280.89,-608872135.11,113664,27648,158720,92416,-123904,101632,14848,157440,67328,-55040
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M5] rank=5 service=node-5 metric=system.fs.inodes.free baseline=2946961920.0 peak=4559987143.11 signed_z=999.0 onset_bin=41 onset_rel_s=1517.344 persistence_bins=15
values_compact=delta:2945991241.14,1206857.15,1136347.42,-438272,-161792,94208,-100059.42,-240493.72,-208896,-426276.57,169984,-39497.14,-255707.43,-241664,-322121.14,387072,-56173.72,-287597.71,-126098.29,108251.43,-380928,-95085.71,-168228.58,-169106.28,72850.28,1614538329.4,-1358051.55,-1186929.78,-1411754.67,-705914567.11,-372480,-8704,-553728,-289280,575744,-300288,15360,-548096,-286464,302592
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M6] rank=6 service=node-5 metric=system.fs.inodes.in_use baseline=0.98 peak=0.77 signed_z=-999.0 onset_bin=41 onset_rel_s=1517.344 persistence_bins=15
values_compact=delta:0.98,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-0.21,0,0,0,0.09,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M7] rank=7 service=node-5 metric=system.fs.inodes.total baseline=2948392667.429 peak=4561915904.0 signed_z=999.0 onset_bin=41 onset_rel_s=1517.344 persistence_bins=15
values_compact=delta:2947421915.43,1206857.14,1136347.43,-438272,-161792,94500.57,-100352,-240493.71,-208896,-426276.57,170276.57,-39497.15,-256000,-241371.42,-322413.72,387072,-56173.71,-287597.72,-126098.28,108544,-381220.57,-95085.72,-168228.57,-168813.71,72557.71,1615036416,-1357596.44,-1186929.78,-1412209.78,-706132480,-371968,-9216,-553728,-288768,575488,-300544,15872,-548096,-286976,302592
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M8] rank=8 service=node-5 metric=system.fs.inodes.used baseline=1430776.385 peak=1929140.22 signed_z=999.0 onset_bin=41 onset_rel_s=1517.344 persistence_bins=15
values_compact=delta:1430803.57,-23.57,-38.86,6,20.57,11.43,-7.71,-4.29,11.72,-6.86,6.86,-2,2.57,-7.72,9.86,12.72,-9.15,-5.14,-4,19.71,-15.85,-1.86,0,5.43,6.71,498220.3,46.89,-3.11,86,-217927.22,14.13,-13.25,3.62,23,-12.25,-10,-4.62,24.5,-13.63,-2.87
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M9] rank=9 service=checkoutservice2-0 metric=container_memory_cache baseline=11607040.0 peak=9871360.0 signed_z=-978.609 onset_bin=44 onset_rel_s=1627.031 persistence_bins=13
values_compact=delta:11603968,0,0,0,0,4096,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-1226069.333333,-277162.666667,-233472,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M10] rank=10 service=node-5 metric=system.net.tcp.out_segs baseline=366.5575 peak=7404.28 signed_z=695.693 onset_bin=41 onset_rel_s=1517.344 persistence_bins=14
values_compact=delta:366.02,0.36,-6.86,-0.04,11.55,-14.43,15.52,-14.15,13.21,32.31,-34.62,-3.87,-4.82,5.3,7.96,-19.21,11.44,-7.75,12.27,-3.81,3.6,-23.05,18.94,-2.26,6.57,121.46,5278.29,812.46,821.89,-4922.78,-2061.17,4.95,4.41,-5.72,2.36,-3.23,-28.56,31.84,25.87,-31.95
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M11] rank=11 service=paymentservice-2 metric=container_cpu_system_seconds baseline=0.0005 peak=0.37 signed_z=246.333 onset_bin=18 onset_rel_s=676.406 persistence_bins=4
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0.005,0,-0.005,0,0,0,0,0,0,0,0,0,0,0.37,-0.37,0,0,0,0,0,0,0,0,0,0.01,-0.01,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M12] rank=12 service=node-5 metric=system.disk.pct_usage baseline=60.768 peak=64.66 signed_z=198.098 onset_bin=41 onset_rel_s=1517.344 persistence_bins=15
values_compact=delta:60.73,0.01,0,0,0.01,0,0.01,0,0.01,0,0.01,0,0,0,0.01,0,0,-0.01,0.01,0,0.01,0,0.01,0,0,3.83,0.01,0,0.01,-1.68,0.01,0,0.01,0,0,0.01,0,0,0,0.01
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[1440.0,2340.0]

=== LOG SUMMARY ===
{"entries":[{"change_pct":-43.3,"n_during":881,"n_pre":1555,"service":"checkoutservice-0"},{"change_pct":-42.8,"n_during":20933,"n_pre":36596,"service":"frontend-0"},{"change_pct":-41.6,"n_during":153,"n_pre":262,"service":"emailservice-1"},{"change_pct":-41.3,"n_during":158,"n_pre":269,"service":"emailservice-2"},{"change_pct":-41.2,"n_during":164,"n_pre":279,"service":"paymentservice-0"},{"change_pct":-41.1,"n_during":159,"n_pre":270,"service":"emailservice-0"},{"change_pct":-40.5,"n_during":11446,"n_pre":19250,"service":"currencyservice-0"},{"change_pct":-40.1,"n_during":13210,"n_pre":22055,"service":"cartservice-0"}],"mode":"volume","omitted_services":23,"service_count":31}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":9.3,"error_pct":0.0,"p95_during_ms":0.16059999999999997,"p95_pre_ms":0.1469,"service":"paymentservice-0","spans":147},{"delta_pct":-6.6,"error_pct":0.0,"p95_during_ms":40.32855,"p95_pre_ms":43.182950000000005,"service":"checkoutservice-0","spans":1734},{"delta_pct":-5.8,"error_pct":0.0,"p95_during_ms":0.01884999999999991,"p95_pre_ms":0.02,"service":"adservice-0","spans":2202},{"delta_pct":-5.3,"error_pct":0.0,"p95_during_ms":39.51039999999999,"p95_pre_ms":41.7399,"service":"checkoutservice-1","spans":1712},{"delta_pct":-5.0,"error_pct":0.0,"p95_during_ms":0.019,"p95_pre_ms":0.02,"service":"adservice-1","spans":2200},{"delta_pct":-4.7,"error_pct":0.0,"p95_during_ms":40.496199999999995,"p95_pre_ms":42.511649999999996,"service":"checkoutservice-2","spans":1732},{"delta_pct":-4.5,"error_pct":0.0,"p95_during_ms":0.2323,"p95_pre_ms":0.24319999999999997,"service":"emailservice-0","spans":148},{"delta_pct":-4.3,"error_pct":0.0,"p95_during_ms":0.022,"p95_pre_ms":0.023,"service":"adservice-2","spans":2200}],"omitted_services":32,"service_count":40}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=16 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":1260.0,"rank":1,"service":"frontend","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1320.0,"rank":2,"service":"adservice","severity_z":81.732},{"evidence_source":"metric","onset_rel_s":1320.0,"rank":3,"service":"redis-cart2","severity_z":71.481},{"evidence_source":"metric","onset_rel_s":1380.0,"rank":4,"service":"emailservice","severity_z":152.474},{"evidence_source":"metric","onset_rel_s":1500.0,"rank":5,"service":"node-5","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1500.0,"rank":6,"service":"node-2","severity_z":120.004},{"evidence_source":"metric","onset_rel_s":1500.0,"rank":7,"service":"checkoutservice","severity_z":61.289},{"evidence_source":"metric","onset_rel_s":1560.0,"rank":8,"service":"checkoutservice2","severity_z":978.609},{"evidence_source":"metric","onset_rel_s":1680.0,"rank":9,"service":"shippingservice","severity_z":87.45},{"evidence_source":"metric","onset_rel_s":1740.0,"rank":10,"service":"node-4","severity_z":33.096},{"evidence_source":"metric","onset_rel_s":1920.0,"rank":11,"service":"frontend2","severity_z":173.205},{"evidence_source":"metric","onset_rel_s":1980.0,"rank":12,"service":"node-6","severity_z":30.432},{"evidence_source":"trace","onset_rel_s":2218.2,"rank":13,"service":"paymentservice","severity_z":9.913},{"evidence_source":"trace","onset_rel_s":2266.8,"rank":14,"service":"paymentservice2","severity_z":12.9}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"emailservice","caller":"checkoutservice"},{"callee":"paymentservice","caller":"checkoutservice"},{"callee":"shippingservice","caller":"checkoutservice"},{"callee":"paymentservice2","caller":"checkoutservice2"},{"callee":"adservice","caller":"frontend"},{"callee":"checkoutservice","caller":"frontend"},{"callee":"shippingservice","caller":"frontend"},{"callee":"checkoutservice2","caller":"frontend2"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

[excluded before optimizer]
