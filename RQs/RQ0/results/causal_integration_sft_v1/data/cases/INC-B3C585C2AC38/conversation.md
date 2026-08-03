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
opaque_id: INC-B3C585C2AC38
observation_window={"duration_rel_s":2340.0,"source_metric_rows":40}
selection_summary={"candidate_count":63,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":1500,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","adservice-grpc","adservice-http","adservice2","adservice2-0","cartservice-0","cartservice-1","cartservice-2","cartservice-grpc","cartservice2-0","checkoutservice-0","checkoutservice-1","checkoutservice-2","checkoutservice-grpc","checkoutservice2-0","currencyservice-0","currencyservice-1","currencyservice-2","currencyservice-grpc","currencyservice2-0","emailservice-0","emailservice-1","emailservice-2","emailservice-grpc","emailservice2-0","frontend-0","frontend-1","frontend-2","frontend-http","frontend2-0","istio-egressgateway-7bfdcc9d86-g2d4q","istio-ingressgateway-565bffd4d-rn678","node-1","node-2","node-3","node-4","node-5","node-6","paymentservice-0","paymentservice-1","paymentservice-2","paymentservice-grpc","paymentservice2-0","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","productcatalogservice-grpc","productcatalogservice2-0","recommendationservice-0","recommendationservice-1","recommendationservice-2","recommendationservice-grpc","recommendationservice2-0","redis-cart-0","redis-cart2-0","shippingservice-0","shippingservice-1","shippingservice-2","shippingservice-grpc","shippingservice2-0"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[18.281,54.844,91.406,127.969,164.531,201.094,237.656,274.219,310.781,347.344,383.906,420.469,457.031,493.594,530.156,566.719,603.281,639.844,676.406,712.969,749.531,786.094,822.656,859.219,895.781,932.344,968.906,1005.469,1042.031,1078.594,1115.156,1151.719,1188.281,1224.844,1261.406,1297.969,1334.531,1371.094,1407.656,1444.219,1480.781,1517.344,1553.906,1590.469,1627.031,1663.594,1700.156,1736.719,1773.281,1809.844,1846.406,1882.969,1919.531,1956.094,1992.656,2029.219,2065.781,2102.344,2138.906,2175.469,2212.031,2248.594,2285.156,2321.719]
[M1] rank=1 service=adservice2 metric=java_lang_Memory_ObjectPendingFinalizationCount baseline=0.0 peak=1.5 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1.5,-1.5,0,0,0,0,0,0,0,0,0,0,0.083333,-0.083333,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M2] rank=2 service=adservice metric=java_lang_Memory_ObjectPendingFinalizationCount baseline=0.0 peak=0.083333 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.083333,-0.083333,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M3] rank=3 service=node-5 metric=system.mem.pct_usage baseline=25.2875 peak=65.96 signed_z=999.0 onset_bin=36 onset_rel_s=1334.531 persistence_bins=2
values_compact=delta:25.31,-0.02,0.03,-0.01,0.03,-0.01,0,-0.07,-0.01,-0.02,0.06,-0.05,-0.01,0.04,0.01,0.01,-0.02,0,0.02,0.06,39.93,0.05,-0.45,1.08,-40.72,0,0,0.01,-0.01,0.06,-0.04,0.03,0,0,-0.02,-0.01,0,0,-0.01,0.02
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M4] rank=4 service=node-5 metric=system.mem.real.pct_useage baseline=21.4165 peak=62.09 signed_z=999.0 onset_bin=36 onset_rel_s=1334.531 persistence_bins=2
values_compact=delta:21.44,-0.02,0.03,-0.01,0.03,-0.01,0,-0.08,0,-0.02,0.05,-0.04,-0.01,0.04,0.01,0.01,-0.02,0,0.02,0.06,39.93,0.05,-0.44,1.07,-40.72,0,0,0.01,-0.01,0.06,-0.03,0.01,0.02,-0.01,-0.01,-0.01,-0.01,0.01,-0.01,0.01
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M5] rank=5 service=node-5 metric=system.mem.used baseline=8094.8 peak=21115.0 signed_z=999.0 onset_bin=36 onset_rel_s=1334.531 persistence_bins=2
values_compact=delta:8101,-4,8,-3,11,-5,-1,-22,-2,-6,17,-14,-4,14,3,4,-8,1,5,19,12782,16,-142,345,-13035,1,-1,4,-3,17,-11,7,2,-1,-5,-4,-1,2,-3,5
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M6] rank=6 service=node-6 metric=system.disk.total baseline=5283914183.11 peak=5867010867.2 signed_z=999.0 onset_bin=49 onset_rel_s=1809.844 persistence_bins=2
values_compact=delta:5283914183.11,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,583096684.09,0,0,0,-583096684.09,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M7] rank=7 service=node-6 metric=system.disk.used baseline=3948817840.356 peak=4425350758.4 signed_z=999.0 onset_bin=49 onset_rel_s=1809.844 persistence_bins=10
values_compact=delta:3948337379.56,58254.22,54158.22,136078.22,-74183.11,79644.45,67811.55,36864,96938.67,-31857.78,48241.78,182499.55,44145.78,-35043.55,50062.22,136988.44,7736.89,59164.45,-254862.23,48241.78,36408.89,18659.56,-217998.23,-94663.11,73272.89,41415.11,42325.34,165660.44,475339161.6,262963.2,276889.6,358400,-475437784.18,-42325.33,116053.33,21845.34,25031.11,-222094.23,58254.23,115143.11
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M8] rank=8 service=node-6 metric=system.fs.inodes.in_use baseline=0.7 peak=0.63 signed_z=-999.0 onset_bin=49 onset_rel_s=1809.844 persistence_bins=2
values_compact=delta:0.7,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-0.07,0,0,0,0.07,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M9] rank=9 service=node-6 metric=system.fs.inodes.used baseline=1915090.9015 peak=2094409.0 signed_z=999.0 onset_bin=49 onset_rel_s=1809.844 persistence_bins=10
values_compact=delta:1915079.78,10.22,10.89,-26.89,12.89,4,-9.56,0,-1.77,11.77,-9.77,25.11,-10.89,-15.56,5.34,21.33,-17.33,16,-16.89,32.89,-40,20.44,-14.67,-8,0,4.67,-4.44,0.44,179188,29,-36.6,148.6,-179098.56,-13.55,15.11,-18.67,13.11,-15.11,22.67,-5.11
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M10] rank=10 service=node-6 metric=system.net.tcp.out_segs baseline=381.1975 peak=8683.05 signed_z=812.687 onset_bin=49 onset_rel_s=1809.844 persistence_bins=3
values_compact=delta:387.62,-12.39,18.79,-24.07,28.83,-21.91,0.56,-0.8,9.07,-18.68,33.33,-35.12,25.92,-15.7,6.63,-6.4,14.52,-23.82,21.75,-8.08,8.8,-15.77,11.62,-6.55,10.02,-7.46,7.66,-9.84,112.78,4920.99,824.92,2445.83,-7836.43,-483.47,29.95,-19,19.98,-16.63,10.73,-14.38
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M11] rank=11 service=node-6 metric=system.fs.inodes.total baseline=4311398650.3115 peak=4844984729.6 signed_z=584.211 onset_bin=49 onset_rel_s=1809.844 persistence_bins=10
values_compact=delta:4312976952.89,-194787.56,-174307.55,-507448.89,335416.89,-279893.34,-232106.66,-109226.67,-353166.22,160199.11,-159744,-698595.56,-142904.88,172487.11,-167480.89,-516096,-4096,-211626.67,1049486.22,-165660.44,-121059.56,-47331.55,899754.66,403228.45,-267150.22,-144270.23,-146545.77,-638520.89,534269223.82,-1030144,-1086259.2,-1413120,-533823533.51,192056.89,-443733.34,-65536,-76913.77,911587.55,-211626.66,-436906.67
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M12] rank=12 service=node-6 metric=system.fs.inodes.free baseline=4309483519.999 peak=4842890035.2 signed_z=584.005 onset_bin=49 onset_rel_s=1809.844 persistence_bins=10
values_compact=delta:4311061845.33,-194787.55,-174307.56,-507448.89,335416.89,-279893.33,-232106.67,-109226.66,-353166.23,160199.11,-159744,-698595.55,-142904.89,172032,-167025.78,-516096,-4096,-211626.66,1049486.22,-165660.45,-121059.55,-47331.56,899754.67,403228.44,-267150.22,-144270.22,-146545.78,-638520.89,534089636.98,-1030144,-1086259.2,-1413120,-533644401.78,192056.89,-443733.33,-65080.89,-76913.78,911132.45,-211171.56,-437361.78
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[1140.0,1440.0]

=== LOG SUMMARY ===
{"entries":[{"error_logs":1734,"error_pct":9.09,"service":"adservice-0","total_logs":19082},{"error_logs":368,"error_pct":1.28,"service":"frontend-2","total_logs":28800},{"error_logs":349,"error_pct":1.28,"service":"frontend-1","total_logs":27168},{"error_logs":150,"error_pct":1.26,"service":"frontend-0","total_logs":11860}],"mode":"errors","omitted_services":27,"service_count":31}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":14.0,"error_pct":0.0,"p95_during_ms":0.0866499999999995,"p95_pre_ms":0.076,"service":"shippingservice-2","spans":402},{"delta_pct":-12.7,"error_pct":0.0,"p95_during_ms":33.30899999999999,"p95_pre_ms":38.146249999999995,"service":"checkoutservice-2","spans":674},{"delta_pct":-12.7,"error_pct":0.0,"p95_during_ms":0.1331,"p95_pre_ms":0.1525,"service":"paymentservice-1","spans":58},{"delta_pct":-12.0,"error_pct":0.0,"p95_during_ms":0.022,"p95_pre_ms":0.025,"service":"adservice2-0","spans":1490},{"delta_pct":9.4,"error_pct":0.0,"p95_during_ms":0.24625,"p95_pre_ms":0.225,"service":"emailservice-1","spans":58},{"delta_pct":9.1,"error_pct":0.0,"p95_during_ms":0.017450000000000004,"p95_pre_ms":0.016,"service":"adservice-1","spans":866},{"delta_pct":-7.9,"error_pct":0.0,"p95_during_ms":0.0175,"p95_pre_ms":0.019,"service":"adservice-2","spans":866},{"delta_pct":7.6,"error_pct":0.0,"p95_during_ms":0.24139999999999998,"p95_pre_ms":0.22440000000000002,"service":"emailservice2-0","spans":99}],"omitted_services":32,"service_count":40}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=16 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":1200.0,"rank":1,"service":"adservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1200.0,"rank":2,"service":"node-5","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1320.0,"rank":3,"service":"redis-cart","severity_z":75.067},{"evidence_source":"metric","onset_rel_s":1500.0,"rank":4,"service":"paymentservice2","severity_z":119.491},{"evidence_source":"metric","onset_rel_s":1680.0,"rank":5,"service":"node-6","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1680.0,"rank":6,"service":"istio-ingressgateway","severity_z":34.402},{"evidence_source":"metric","onset_rel_s":1680.0,"rank":7,"service":"istio-egressgateway","severity_z":24.331},{"evidence_source":"metric","onset_rel_s":1680.0,"rank":8,"service":"recommendationservice","severity_z":20.135},{"evidence_source":"metric","onset_rel_s":1740.0,"rank":9,"service":"node-2","severity_z":47.065},{"evidence_source":"trace","onset_rel_s":1779.6,"rank":10,"service":"shippingservice","severity_z":6.468},{"evidence_source":"metric","onset_rel_s":1800.0,"rank":11,"service":"checkoutservice","severity_z":114.466},{"evidence_source":"trace","onset_rel_s":1828.2,"rank":12,"service":"adservice2","severity_z":18.708},{"evidence_source":"metric","onset_rel_s":1920.0,"rank":13,"service":"node-1","severity_z":19.881},{"evidence_source":"metric","onset_rel_s":1920.0,"rank":14,"service":"node-4","severity_z":19.621}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"shippingservice","caller":"checkoutservice"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"medium","reason":"Rank node-5 first because node-5 has direct system.mem.pct_usage evidence (signed-z 999, persistence 2 bins); adservice is second despite propagation rank 1 because onset ordering alone does not establish the causal origin.","services":["node-5","adservice"]}
