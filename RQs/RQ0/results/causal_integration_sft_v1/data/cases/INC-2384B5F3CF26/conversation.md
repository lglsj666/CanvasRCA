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
opaque_id: INC-2384B5F3CF26
observation_window={"duration_rel_s":2340.0,"source_metric_rows":40}
selection_summary={"candidate_count":63,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":1465,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","adservice-grpc","adservice-http","adservice2","adservice2-0","cartservice-0","cartservice-1","cartservice-2","cartservice-grpc","cartservice2-0","checkoutservice-0","checkoutservice-1","checkoutservice-2","checkoutservice-grpc","checkoutservice2-0","currencyservice-0","currencyservice-1","currencyservice-2","currencyservice-grpc","currencyservice2-0","emailservice-0","emailservice-1","emailservice-2","emailservice-grpc","emailservice2-0","frontend-0","frontend-1","frontend-2","frontend-http","frontend2-0","istio-egressgateway-7bfdcc9d86-g2d4q","istio-ingressgateway-565bffd4d-rn678","node-1","node-2","node-3","node-4","node-5","node-6","paymentservice-0","paymentservice-1","paymentservice-2","paymentservice-grpc","paymentservice2-0","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","productcatalogservice-grpc","productcatalogservice2-0","recommendationservice-0","recommendationservice-1","recommendationservice-2","recommendationservice-grpc","recommendationservice2-0","redis-cart-0","redis-cart2-0","shippingservice-0","shippingservice-1","shippingservice-2","shippingservice-grpc","shippingservice2-0"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[18.281,54.844,91.406,127.969,164.531,201.094,237.656,274.219,310.781,347.344,383.906,420.469,457.031,493.594,530.156,566.719,603.281,639.844,676.406,712.969,749.531,786.094,822.656,859.219,895.781,932.344,968.906,1005.469,1042.031,1078.594,1115.156,1151.719,1188.281,1224.844,1261.406,1297.969,1334.531,1371.094,1407.656,1444.219,1480.781,1517.344,1553.906,1590.469,1627.031,1663.594,1700.156,1736.719,1773.281,1809.844,1846.406,1882.969,1919.531,1956.094,1992.656,2029.219,2065.781,2102.344,2138.906,2175.469,2212.031,2248.594,2285.156,2321.719]
[M1] rank=1 service=emailservice2-0 metric=container_network_receive_MB.eth0 baseline=0.024 peak=0.552522 signed_z=343.776 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.02374,0.000707,-0.001047,0.001175,-0.000658,-0.003451,0.005015,-0.00346,0.002788,-0.000166,-0.000894,-0.002305,0.005365,-0.002986,0.002084,-0.00151,-0.000423,-0.002125,0.002952,0.000947,-0.002331,0.009011,-0.001929,-0.003091,0.004154,0.52096,-0.531616,0.00587,-0.004531,0.000149,0.002074,-0.000721,0.000717,0.000543,-0.001921,0.002527,-0.001654,0.000847,-0.002973,0.001812
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M2] rank=2 service=emailservice-1 metric=container_network_receive_MB.eth0 baseline=0.025421 peak=0.595031 signed_z=186.012 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.023541,0.002489,0.000444,-0.00198,0.000277,0.00438,-0.005168,0.001668,-0.00083,0.004494,-0.005488,-0.002558,0.009038,-0.001886,-0.010627,0.009731,-0.005678,0.007548,-0.002862,-0.003267,0.00855,0.563215,-0.561908,0.002521,-0.012618,0.001064,0.001491,-0.000983,-0.000702,0.004566,-0.001829,-0.002338,0.004325,-0.003021,0.001451,-0.000729,0.000893,-0.00313,0.002198,-0.000044
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M3] rank=3 service=checkoutservice2-0 metric=container_network_receive_MB.eth0 baseline=0.039918 peak=0.570624 signed_z=98.525 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.041091,-0.005144,0.000015,0.006767,0.004273,-0.012118,0.012335,-0.013801,0.007033,0.003537,-0.009366,0.006902,0.00519,-0.009989,0.007258,-0.005651,-0.010555,0.021389,-0.012771,0.004045,-0.001489,0.002488,0.00164,-0.001846,-0.006763,0.536154,-0.532829,-0.003171,0.012248,-0.006419,-0.003945,0.005064,-0.004855,0.010961,-0.016596,0.007997,0.008542,-0.006214,-0.007264,0.01132
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M4] rank=4 service=adservice-1 metric=container_memory_max_usage_MB baseline=137.771875 peak=138.164062 signed_z=83.667 onset_bin=41 onset_rel_s=1517.344 persistence_bins=15
values_compact=delta:137.769531,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.011719,0,0,0,0,0,0,0,0,0.054688,0,0.125,0,0,0,0,0,0.070312,0,0,0.066406,0.066406,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M5] rank=5 service=node-2 metric=system.io.avg_q_sz baseline=0.007 peak=0.41 signed_z=72.381 onset_bin=59 onset_rel_s=2175.469 persistence_bins=2
values_compact=delta:0,0,0,0.01,0,0,0,0,0.01,-0.01,0,0,-0.01,0,0.01,0,-0.01,0.01,0,-0.01,0,0.01,0.4,-0.4,0,0,-0.01,0.05,-0.05,0,0.1,-0.1,0,0,0.01,-0.01,0.12,-0.08,-0.03,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M6] rank=6 service=redis-cart2-0 metric=container_network_receive_MB.eth0 baseline=0.040499 peak=0.307663 signed_z=70.338 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.043649,-0.003433,0.001842,-0.003643,-0.004349,0.01222,-0.0071,0.00705,-0.010097,0.007258,-0.005257,0.001831,-0.009139,0.012729,-0.000405,-0.004567,0.000927,0.000734,0.002522,0.000771,-0.002309,-0.007484,0.011047,-0.004674,0.257938,0.009602,-0.266139,-0.006005,0.010511,-0.001444,-0.002482,-0.009087,0.01491,-0.008988,0.003846,-0.004989,0.004728,-0.004136,-0.000066,0.002963
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M7] rank=7 service=cartservice-1 metric=container_network_receive_MB.eth0 baseline=0.08256 peak=0.615336 signed_z=70.076 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.088071,-0.021926,0.034934,-0.020203,-0.006876,0.00604,0.006374,-0.001558,0.000373,-0.015277,0.015713,0.002723,-0.014751,0.010993,-0.002993,0.00406,-0.008299,0.01392,-0.009351,0.002227,-0.001828,0.007849,-0.007553,0.001418,-0.002524,-0.004931,0.018284,0.520427,-0.533432,0.010464,-0.012195,0.008523,-0.008978,0.012956,-0.012567,0.013422,-0.014774,0.018308,-0.020535,0.007248
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M8] rank=8 service=currencyservice-1 metric=container_cpu_cfs_throttled_seconds baseline=0.000268 peak=0.067159 signed_z=57.189 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0.005367,-0.005367,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.067159,-0.067159,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M9] rank=9 service=adservice metric=jvm_memory_pool_MB_used.Tenured_Gen baseline=15.58561 peak=15.592931 signed_z=40.916 onset_bin=49 onset_rel_s=1809.844 persistence_bins=10
values_compact=delta:15.585208,0.000112,0.000025,0.000056,0.000046,0.000056,0.000101,0.000021,0,0,0,0,0.000101,0.000021,0,0.000046,0.000015,0,0,0,0,0,0,0.000112,0.000071,0,0.000112,0.00001,0,0.000046,0.000015,0.000071,0.000051,0.002059,0.000695,0.00053,0.002764,0.000025,0.000024,0.000538
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M10] rank=10 service=adservice metric=java_lang_GarbageCollector_LastGcInfo_memoryUsageAfterGc_used.Tenured_Gen.Copy baseline=16342694.666667 peak=16350373.333333 signed_z=40.455 onset_bin=49 onset_rel_s=1809.844 persistence_bins=10
values_compact=delta:16342253.333333,138.666667,26.666667,58.666666,48,58.666667,101.333333,26.666667,0,0,0,0,106.666667,21.333333,0,42.666667,21.333333,0,0,0,0,0,0,101.333333,90.666667,0,117.333333,10.666667,0,42.666667,21.333333,74.666667,53.333333,1922,966,552,2896,32,14.666667,574.666666
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M11] rank=11 service=adservice metric=java_lang_MemoryPool_PeakUsage_used.Tenured_Gen baseline=16342694.666667 peak=16350362.666667 signed_z=40.399 onset_bin=49 onset_rel_s=1809.844 persistence_bins=10
values_compact=delta:16342253.333333,138.666667,26.666667,58.666666,48,58.666667,101.333333,26.666667,0,0,0,0,106.666667,21.333333,0,42.666667,21.333333,0,0,0,0,0,0,101.333333,90.666667,0,117.333333,10.666667,0,42.666667,21.333333,74.666667,53.333333,1922,966,552,2896,32,14.666667,564
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M12] rank=12 service=adservice metric=java_lang_MemoryPool_Usage_used.Tenured_Gen baseline=16342694.666667 peak=16350362.666667 signed_z=40.399 onset_bin=49 onset_rel_s=1809.844 persistence_bins=10
values_compact=delta:16342253.333333,138.666667,26.666667,58.666666,48,58.666667,101.333333,26.666667,0,0,0,0,106.666667,21.333333,0,42.666667,21.333333,0,0,0,0,0,0,101.333333,90.666667,0,117.333333,10.666667,0,42.666667,21.333333,74.666667,53.333333,1922,966,552,2896,32,14.666667,564
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[1440.0,1560.0]

=== LOG SUMMARY ===
{"entries":[{"error_logs":5158,"error_pct":9.01,"service":"adservice-0","total_logs":57244},{"error_logs":925,"error_pct":1.29,"service":"frontend-0","total_logs":71548},{"error_logs":921,"error_pct":1.3,"service":"frontend-2","total_logs":71066},{"error_logs":733,"error_pct":1.29,"service":"frontend-1","total_logs":56716}],"mode":"errors","omitted_services":27,"service_count":31}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":-34.8,"error_pct":0.0,"p95_during_ms":55.28825,"p95_pre_ms":84.78450000000001,"service":"checkoutservice2-0","spans":1232},{"delta_pct":-26.3,"error_pct":0.0,"p95_during_ms":0.014,"p95_pre_ms":0.019,"service":"adservice-1","spans":2581},{"delta_pct":-20.5,"error_pct":0.0,"p95_during_ms":0.14859999999999998,"p95_pre_ms":0.187,"service":"paymentservice2-0","spans":105},{"delta_pct":-13.2,"error_pct":0.0,"p95_during_ms":0.0165,"p95_pre_ms":0.019,"service":"adservice-2","spans":2580},{"delta_pct":-7.7,"error_pct":0.0,"p95_during_ms":0.13365000000000002,"p95_pre_ms":0.14484999999999995,"service":"paymentservice-1","spans":170},{"delta_pct":-7.1,"error_pct":5.39,"p95_during_ms":65.86380000000003,"p95_pre_ms":70.8862,"service":"frontend2-0","spans":28772},{"delta_pct":6.8,"error_pct":0.0,"p95_during_ms":0.2428,"p95_pre_ms":0.22724999999999998,"service":"emailservice2-0","spans":105},{"delta_pct":6.3,"error_pct":0.0,"p95_during_ms":0.07549999999999998,"p95_pre_ms":0.071,"service":"shippingservice-0","spans":1206}],"omitted_services":32,"service_count":40}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=14 omitted_edges=1
[{"evidence_source":"metric","onset_rel_s":1260.0,"rank":1,"service":"emailservice","severity_z":186.012},{"evidence_source":"metric","onset_rel_s":1260.0,"rank":2,"service":"frontend","severity_z":18.743},{"evidence_source":"metric","onset_rel_s":1320.0,"rank":3,"service":"node-2","severity_z":72.381},{"evidence_source":"metric","onset_rel_s":1440.0,"rank":4,"service":"redis-cart2","severity_z":70.338},{"evidence_source":"metric","onset_rel_s":1440.0,"rank":5,"service":"checkoutservice","severity_z":38.886},{"evidence_source":"metric","onset_rel_s":1500.0,"rank":6,"service":"emailservice2","severity_z":343.776},{"evidence_source":"metric","onset_rel_s":1500.0,"rank":7,"service":"checkoutservice2","severity_z":98.525},{"evidence_source":"metric","onset_rel_s":1620.0,"rank":8,"service":"cartservice","severity_z":70.076},{"evidence_source":"metric","onset_rel_s":1680.0,"rank":9,"service":"shippingservice","severity_z":19.19},{"evidence_source":"metric","onset_rel_s":1800.0,"rank":10,"service":"node-1","severity_z":35.427},{"evidence_source":"metric","onset_rel_s":1860.0,"rank":11,"service":"node-4","severity_z":32.802},{"evidence_source":"metric","onset_rel_s":1980.0,"rank":12,"service":"adservice","severity_z":83.667},{"evidence_source":"metric","onset_rel_s":2040.0,"rank":13,"service":"istio-egressgateway","severity_z":19.608},{"evidence_source":"metric","onset_rel_s":2160.0,"rank":14,"service":"currencyservice","severity_z":57.189}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"cartservice","caller":"checkoutservice"},{"callee":"currencyservice","caller":"checkoutservice"},{"callee":"emailservice","caller":"checkoutservice"},{"callee":"shippingservice","caller":"checkoutservice"},{"callee":"emailservice2","caller":"checkoutservice2"},{"callee":"adservice","caller":"frontend"},{"callee":"cartservice","caller":"frontend"},{"callee":"checkoutservice","caller":"frontend"},{"callee":"currencyservice","caller":"frontend"},{"callee":"shippingservice","caller":"frontend"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"high","reason":"Rank emailservice-0 first because emailservice-0 has metric evidence at propagation rank 1; although checkoutservice-0 is salient, the caller path checkoutservice -> emailservice means a disturbance in the callee can propagate back toward that caller-side symptom.","services":["emailservice-0","checkoutservice-0"]}
