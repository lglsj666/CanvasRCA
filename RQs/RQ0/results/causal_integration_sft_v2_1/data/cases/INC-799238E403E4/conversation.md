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
opaque_id: INC-799238E403E4
observation_window={"duration_rel_s":2340.0,"source_metric_rows":40}
selection_summary={"candidate_count":63,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":1472,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","adservice-grpc","adservice-http","adservice2","adservice2-0","cartservice-0","cartservice-1","cartservice-2","cartservice-grpc","cartservice2-0","checkoutservice-0","checkoutservice-1","checkoutservice-2","checkoutservice-grpc","checkoutservice2-0","currencyservice-0","currencyservice-1","currencyservice-2","currencyservice-grpc","currencyservice2-0","emailservice-0","emailservice-1","emailservice-2","emailservice-grpc","emailservice2-0","frontend-0","frontend-1","frontend-2","frontend-http","frontend2-0","istio-egressgateway-7bfdcc9d86-22q7z","istio-ingressgateway-565bffd4d-4nr6v","node-1","node-2","node-3","node-4","node-5","node-6","paymentservice-0","paymentservice-1","paymentservice-2","paymentservice-grpc","paymentservice2-0","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","productcatalogservice-grpc","productcatalogservice2-0","recommendationservice-0","recommendationservice-1","recommendationservice-2","recommendationservice-grpc","recommendationservice2-0","redis-cart-0","redis-cart2-0","shippingservice-0","shippingservice-1","shippingservice-2","shippingservice-grpc","shippingservice2-0"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[18.281,54.844,91.406,127.969,164.531,201.094,237.656,274.219,310.781,347.344,383.906,420.469,457.031,493.594,530.156,566.719,603.281,639.844,676.406,712.969,749.531,786.094,822.656,859.219,895.781,932.344,968.906,1005.469,1042.031,1078.594,1115.156,1151.719,1188.281,1224.844,1261.406,1297.969,1334.531,1371.094,1407.656,1444.219,1480.781,1517.344,1553.906,1590.469,1627.031,1663.594,1700.156,1736.719,1773.281,1809.844,1846.406,1882.969,1919.531,1956.094,1992.656,2029.219,2065.781,2102.344,2138.906,2175.469,2212.031,2248.594,2285.156,2321.719]
[M1] rank=1 service=adservice metric=jvm_memory_pool_MB_used.Tenured_Gen baseline=39.87205 peak=40.067558 signed_z=874.179 onset_bin=41 onset_rel_s=1517.344 persistence_bins=15
values_compact=delta:39.87145,0.0003,0.000056,0.000081,0.000031,0.000032,0.000044,0,0,0,0,0.000071,0.000112,0.000051,0.000071,0,0,0,0,0,0,0,0,0.000285,0.000514,0.000056,0,0.000017,0.001383,0.000599,0.000137,0.191432,0.000031,0.000058,0,0.000412,0.000132,0.000035,0.000084,0.000084
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M2] rank=2 service=adservice metric=java_lang_GarbageCollector_LastGcInfo_memoryUsageAfterGc_used.Tenured_Gen.Copy baseline=41808870.4 peak=42013880.0 signed_z=853.373 onset_bin=41 onset_rel_s=1517.344 persistence_bins=15
values_compact=delta:41808202.666667,357.333333,58.666667,80,37.333333,26.666667,53.333333,0,0,0,0,58.666667,133.333333,42.666667,85.333333,0,0,0,0,0,0,0,0,240,597.333333,58.666667,0,9.333333,1458.666667,601.333333,170.666667,184002,16755.333333,66.666667,0,386.666667,184,37.333333,80.666667,95.333333
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M3] rank=3 service=adservice metric=java_lang_MemoryPool_Usage_used.Tenured_Gen baseline=41808870.4 peak=42013880.0 signed_z=853.373 onset_bin=41 onset_rel_s=1517.344 persistence_bins=15
values_compact=delta:41808202.666667,357.333333,58.666667,80,37.333333,26.666667,53.333333,0,0,0,0,58.666667,133.333333,42.666667,85.333333,0,0,0,0,0,0,0,0,240,592,64,0,9.333333,1458.666667,601.333333,170.666667,184002,16755.333333,66.666667,0,386.666667,178.666666,42.666667,80.666667,95.333333
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M4] rank=4 service=adservice metric=jvm_memory_pool_allocated_MB_total.Tenured_Gen baseline=99.541455 peak=99.736969 signed_z=846.107 onset_bin=41 onset_rel_s=1517.344 persistence_bins=15
values_compact=delta:99.54082,0.000315,0.000076,0.000082,0.000035,0.000026,0.000051,0,0,0,0,0.000056,0.000127,0.000041,0.000081,0,0,0,0,0,0,0,0,0.000229,0.000564,0.000061,0,0.000009,0.001248,0.000717,0.000163,0.175478,0.015979,0.000063,0,0.000369,0.00017,0.000041,0.00007,0.000098
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M5] rank=5 service=adservice metric=java_lang_GarbageCollector_LastGcInfo_memoryUsageBeforeGc_used.Tenured_Gen.Copy baseline=41808847.466667 peak=42013872.666667 signed_z=752.052 onset_bin=41 onset_rel_s=1517.344 persistence_bins=15
values_compact=delta:41808032,416,160,58.666667,69.333333,0,80,0,0,0,0,10.666667,165.333333,37.333333,85.333334,21.333333,0,0,0,0,0,0,0,48,688,149.333333,10.666667,0,837.333333,1125.333334,277.333333,117087.333333,83656.666667,66.666667,13.333333,205.333333,338.666667,64,22,146.666667
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M6] rank=6 service=frontend2-0 metric=istio_request_duration_milliseconds.http.302. baseline=67.18375 peak=8405.05 signed_z=507.075 onset_bin=36 onset_rel_s=1334.531 persistence_bins=7
values_compact=delta:50.275,29.775,-37.325,60.05,-60.6,36.15,-19.85,20.625,-22.625,5.775,11.575,-3.6,-18.225,47.175,-47,34,-25.35,5.875,2.8,-9.05,7303.85,-2639.3,2101.05,-526.05,-525,2100,-3150,3680.05,-6791.875,-1529.575,-46.4,54.95,-45.225,53.7,-68.775,62.075,-39.5,41.175,-48.45,44.125
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M7] rank=7 service=node-2 metric=system.cpu.user baseline=1.957 peak=82.44 signed_z=395.595 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:2.01,-0.53,0.49,-0.24,0.26,-0.23,0.25,-0.06,0.16,-0.23,-0.1,-0.02,0.29,-0.04,0.27,-0.27,0.38,-0.15,-0.36,-0.03,2.25,-2.21,0.33,0.31,-0.48,-0.13,0.04,-0.24,0.43,-0.27,0.11,-0.29,0.24,0.11,80.39,-0.14,0.1,-80.14,-0.27,-0.19
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M8] rank=8 service=paymentservice-0 metric=container_network_receive_MB.eth0 baseline=0.022082 peak=0.542659 signed_z=164.434 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.021693,0.001529,-0.001476,-0.000215,0.00053,0.004259,-0.004786,-0.005723,0.012567,-0.006423,-0.001272,0.005179,-0.004134,-0.003396,0.005091,0.003193,-0.007935,-0.002449,0.005844,0.001676,-0.001673,0.000148,0.001263,0.519169,-0.520406,-0.001564,0.003367,-0.001611,0.003973,-0.005877,-0.004092,0.00591,-0.000523,-0.00023,0.00381,-0.004681,0.001326,0.003188,0.002585,-0.00774
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M9] rank=9 service=emailservice-0 metric=container_network_receive_MB.eth0 baseline=0.025931 peak=0.555827 signed_z=163.655 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.027341,-0.006183,0.003064,0.003322,-0.000304,0.000114,0.004641,-0.005308,-0.007645,0.006238,0.005723,-0.007189,-0.002889,0.005754,-0.000642,-0.002026,0.002802,-0.000116,-0.002867,0.007114,-0.004148,-0.009937,0.009417,-0.000407,0.001135,0.528823,-0.526463,-0.006872,0.002406,0.003896,-0.001948,0.000181,-0.003789,0.003463,0.000267,-0.001384,0.00337,0.004311,-0.013867,-0.000895
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M10] rank=10 service=node-3 metric=system.fs.inodes.used baseline=449361.1 peak=449397.0 signed_z=119.667 onset_bin=44 onset_rel_s=1627.031 persistence_bins=13
values_compact=delta:449361,0,0,0,0,0,0,1,-1,0,0,0,0,0,0,0,1,-1,0,0,0,0,0,0,0,0,0,36,-35,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M11] rank=11 service=node-2 metric=system.cpu.pct_usage baseline=4.465 peak=84.47 signed_z=110.744 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:5.73,-2.3,0.75,-0.23,0.53,-0.7,0.67,0.28,-0.51,-0.1,-0.15,-0.19,0.68,0.1,0.75,-0.96,2.27,-1.62,-0.77,-0.28,3.35,-3.03,0.37,0.88,-0.92,-0.29,-0.26,0.01,1.9,-1.92,0.35,-0.35,0.48,0.17,79.78,-0.28,0.04,-79.02,-0.65,-0.58
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M12] rank=12 service=shippingservice2-0 metric=container_network_receive_MB.eth0 baseline=0.034269 peak=0.559323 signed_z=105.278 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.032069,-0.005041,0.006897,0.009075,-0.015588,0.00672,0.008246,-0.007071,-0.003694,0.003265,0.002629,-0.001483,-0.008189,0.012728,-0.01399,0.013736,-0.01091,0.007358,0.000919,-0.006688,0.003874,-0.005935,0.004103,-0.001191,-0.002029,0.004163,-0.007894,0.016974,-0.013514,0.006332,-0.002101,0.525553,-0.531927,0.012447,-0.011795,0.00299,0.004163,0.009712,-0.017245,0.01507
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[1800.0,2340.0]

=== LOG SUMMARY ===
{"entries":[{"change_pct":-72.1,"n_during":101,"n_pre":362,"service":"paymentservice-2"},{"change_pct":-71.9,"n_during":98,"n_pre":349,"service":"emailservice-0"},{"change_pct":-71.9,"n_during":12037,"n_pre":42905,"service":"frontend-0"},{"change_pct":-71.7,"n_during":563,"n_pre":1990,"service":"checkoutservice-0"},{"change_pct":-71.5,"n_during":563,"n_pre":1973,"service":"checkoutservice-2"},{"change_pct":-71.0,"n_during":7191,"n_pre":24760,"service":"currencyservice-1"},{"change_pct":-70.9,"n_during":7174,"n_pre":24641,"service":"currencyservice-2"},{"change_pct":-70.8,"n_during":7215,"n_pre":24694,"service":"currencyservice-0"}],"mode":"volume","omitted_services":23,"service_count":31}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":-100.0,"error_pct":0.0,"p95_during_ms":0.0,"p95_pre_ms":362.0,"service":"cartservice2-0","spans":7036},{"delta_pct":-94.5,"error_pct":0.0,"p95_during_ms":39.768049999999995,"p95_pre_ms":727.5945,"service":"checkoutservice2-0","spans":1682},{"delta_pct":11.1,"error_pct":0.0,"p95_during_ms":0.15769999999999998,"p95_pre_ms":0.142,"service":"paymentservice-1","spans":153},{"delta_pct":-10.4,"error_pct":0.0,"p95_during_ms":45.974499999999985,"p95_pre_ms":51.31829999999998,"service":"frontend2-0","spans":38690},{"delta_pct":-9.3,"error_pct":0.0,"p95_during_ms":0.1615,"p95_pre_ms":0.178,"service":"paymentservice2-0","spans":143},{"delta_pct":-7.8,"error_pct":0.0,"p95_during_ms":0.14349999999999996,"p95_pre_ms":0.15569999999999984,"service":"paymentservice-0","spans":153},{"delta_pct":5.5,"error_pct":0.0,"p95_during_ms":0.2542,"p95_pre_ms":0.241,"service":"emailservice-0","spans":155},{"delta_pct":5.0,"error_pct":0.0,"p95_during_ms":0.021,"p95_pre_ms":0.02,"service":"adservice-1","spans":2285}],"omitted_services":32,"service_count":40}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=14 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":1200.0,"rank":1,"service":"frontend2","severity_z":507.075},{"evidence_source":"metric","onset_rel_s":1380.0,"rank":2,"service":"paymentservice","severity_z":164.434},{"evidence_source":"metric","onset_rel_s":1440.0,"rank":3,"service":"cartservice2","severity_z":58.641},{"evidence_source":"metric","onset_rel_s":1500.0,"rank":4,"service":"emailservice","severity_z":163.655},{"evidence_source":"metric","onset_rel_s":1560.0,"rank":5,"service":"istio-ingressgateway","severity_z":39.893},{"evidence_source":"metric","onset_rel_s":1620.0,"rank":6,"service":"node-3","severity_z":119.667},{"evidence_source":"metric","onset_rel_s":1680.0,"rank":7,"service":"frontend","severity_z":77.737},{"evidence_source":"metric","onset_rel_s":1740.0,"rank":8,"service":"adservice2","severity_z":68.46},{"evidence_source":"metric","onset_rel_s":1740.0,"rank":9,"service":"checkoutservice","severity_z":64.373},{"evidence_source":"metric","onset_rel_s":1740.0,"rank":10,"service":"redis-cart","severity_z":53.339},{"evidence_source":"metric","onset_rel_s":1860.0,"rank":11,"service":"adservice","severity_z":874.179},{"evidence_source":"metric","onset_rel_s":1860.0,"rank":12,"service":"shippingservice2","severity_z":105.278},{"evidence_source":"metric","onset_rel_s":2040.0,"rank":13,"service":"node-2","severity_z":395.595},{"evidence_source":"trace","onset_rel_s":2169.6,"rank":14,"service":"shippingservice","severity_z":10.048}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"emailservice","caller":"checkoutservice"},{"callee":"paymentservice","caller":"checkoutservice"},{"callee":"shippingservice","caller":"checkoutservice"},{"callee":"adservice","caller":"frontend"},{"callee":"checkoutservice","caller":"frontend"},{"callee":"shippingservice","caller":"frontend"},{"callee":"adservice2","caller":"frontend2"},{"callee":"cartservice2","caller":"frontend2"},{"callee":"shippingservice2","caller":"frontend2"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"high","reason":"Rank cartservice2-0 first because cartservice2-0 has direct trace evidence; although frontend2-0 is salient, the caller path frontend2 -> cartservice2 means a disturbance in the callee can propagate back toward that caller-side symptom. The remaining entries preserve evidence-supported alternatives so the ranking retains calibrated uncertainty instead of collapsing to one answer.","services":["cartservice2-0","node-2","adservice","frontend2-0","paymentservice-0"]}
