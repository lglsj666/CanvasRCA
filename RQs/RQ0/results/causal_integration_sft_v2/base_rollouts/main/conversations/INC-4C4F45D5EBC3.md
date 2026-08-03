# Causal SFT v2 base rollout — INC-4C4F45D5EBC3

## System

You are an expert Site Reliability Engineer performing Root Cause Analysis (RCA) for a microservice application deployed on a Kubernetes cluster. A fault has occurred in the system. Your task is to identify the root cause of the incident.

Root causes can occur at three levels:
- Pod level: a specific container replica (e.g., "cartservice-0")
- Service level: a microservice type (e.g., "paymentservice") — predict any pod of that service
- Node level: an infrastructure host (e.g., "node-6") — nodes appear as isolated entities with system metrics (CPU, memory, network, disk) but no application logs or traces

The system consists of multiple services communicating over HTTP/gRPC, running on shared infrastructure nodes. A fault in one component (pod, service, or node) can propagate to dependent components, causing them to appear degraded even though they are not the root cause.

Node-level faults (e.g., host memory exhaustion, CPU saturation, disk I/O) often manifest as correlated anomalies across multiple pods. If several unrelated pods show simultaneous degradation and a node shows critical system-level metrics, the node is likely the root cause.

Focus on distinguishing the ORIGIN of the fault from its SYMPTOMS in downstream or co-located components.

## User

[image: RQs/RQ0/results/causal_integration_sft_v1/data/cases/INC-4C4F45D5EBC3/dashboard.png]

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
opaque_id: INC-4C4F45D5EBC3
observation_window={"duration_rel_s":2340.0,"source_metric_rows":40}
selection_summary={"candidate_count":63,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":1327,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","adservice-grpc","adservice-http","adservice2","adservice2-0","cartservice-0","cartservice-1","cartservice-2","cartservice-grpc","cartservice2-0","checkoutservice-0","checkoutservice-1","checkoutservice-2","checkoutservice-grpc","checkoutservice2-0","currencyservice-0","currencyservice-1","currencyservice-2","currencyservice-grpc","currencyservice2-0","emailservice-0","emailservice-1","emailservice-2","emailservice-grpc","emailservice2-0","frontend-0","frontend-1","frontend-2","frontend-http","frontend2-0","istio-egressgateway-7bfdcc9d86-22q7z","istio-ingressgateway-565bffd4d-4nr6v","node-1","node-2","node-3","node-4","node-5","node-6","paymentservice-0","paymentservice-1","paymentservice-2","paymentservice-grpc","paymentservice2-0","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","productcatalogservice-grpc","productcatalogservice2-0","recommendationservice-0","recommendationservice-1","recommendationservice-2","recommendationservice-grpc","recommendationservice2-0","redis-cart-0","redis-cart2-0","shippingservice-0","shippingservice-1","shippingservice-2","shippingservice-grpc","shippingservice2-0"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[18.281,54.844,91.406,127.969,164.531,201.094,237.656,274.219,310.781,347.344,383.906,420.469,457.031,493.594,530.156,566.719,603.281,639.844,676.406,712.969,749.531,786.094,822.656,859.219,895.781,932.344,968.906,1005.469,1042.031,1078.594,1115.156,1151.719,1188.281,1224.844,1261.406,1297.969,1334.531,1371.094,1407.656,1444.219,1480.781,1517.344,1553.906,1590.469,1627.031,1663.594,1700.156,1736.719,1773.281,1809.844,1846.406,1882.969,1919.531,1956.094,1992.656,2029.219,2065.781,2102.344,2138.906,2175.469,2212.031,2248.594,2285.156,2321.719]
[M1] rank=1 service=adservice metric=jvm_threads_started baseline=0.0 peak=0.666667 signed_z=999.0 onset_bin=36 onset_rel_s=1334.531 persistence_bins=2
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.666667,-0.333334,-0.333333,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M2] rank=2 service=node-1 metric=system.disk.pct_usage baseline=40.72 peak=40.73 signed_z=999.0 onset_bin=36 onset_rel_s=1334.531 persistence_bins=18
values_compact=delta:40.72,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.01,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M3] rank=3 service=productcatalogservice-1 metric=container_memory_mapped_file baseline=450662.4 peak=3401728.0 signed_z=999.0 onset_bin=31 onset_rel_s=1151.719 persistence_bins=21
values_compact=delta:450560,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,2048,2048,0,0,0,2947072,-3256320,34816,4096,12288,8192,4096,4096,4096,6144,8192,4778.666667,5461.333333,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M4] rank=4 service=adservice metric=java_lang_GarbageCollector_LastGcInfo_memoryUsageBeforeGc_used.Tenured_Gen.Copy baseline=39695198.466667 peak=39898368.0 signed_z=555.351 onset_bin=44 onset_rel_s=1627.031 persistence_bins=13
values_compact=delta:39694704,0,64,213.333333,42.666667,0,26.666667,37.333333,0,0,0,0,60,20,0,154.666667,485.333333,64,0,42.666667,229.333333,16,48,0,0,0,176,65.333333,184618.666667,16916,37.333333,58.666667,112,96,0,0,0,0,53.333333,26.666667
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M5] rank=5 service=adservice metric=jvm_memory_pool_allocated_MB_total.Tenured_Gen baseline=97.525724 peak=97.71946 signed_z=537.936 onset_bin=44 onset_rel_s=1627.031 persistence_bins=13
values_compact=delta:97.52523,0.000021,0.000086,0.000193,0.000006,0,0.000045,0.000016,0,0,0,0.000006,0.00007,0,0,0.00032,0.000331,0.00002,0,0.000127,0.000133,0.000035,0.000026,0,0,0.000056,0.000112,0.048098,0.144071,0.000112,0.000035,0.000036,0.000173,0.000025,0,0,0,0,0.000077,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M6] rank=6 service=adservice metric=java_lang_GarbageCollector_LastGcInfo_memoryUsageAfterGc_used.Tenured_Gen.Copy baseline=39695224.133333 peak=39898368.0 signed_z=536.44 onset_bin=44 onset_rel_s=1627.031 persistence_bins=13
values_compact=delta:39694704,21.333333,106.666667,186.666667,5.333333,0,48,16,0,0,0,13.333333,66.666667,0,0,336,357.333333,10.666667,0,144,128,37.333333,26.666667,0,0,73.333333,102.666667,50444,151070.666667,106.666666,37.333334,37.333333,181.333333,26.666667,0,0,0,0,80,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M7] rank=7 service=adservice metric=java_lang_MemoryPool_Usage_used.Tenured_Gen baseline=39695223.8 peak=39898368.0 signed_z=536.284 onset_bin=44 onset_rel_s=1627.031 persistence_bins=13
values_compact=delta:39694704,21.333333,106.666667,186.666667,5.333333,0,48,16,0,0,0,6.666667,73.333333,0,0,336,357.333333,10.666667,0,144,128,37.333333,26.666667,0,0,58.666667,117.333333,50444,151070.666667,106.666666,37.333334,37.333333,181.333333,26.666667,0,0,0,0,80,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M8] rank=8 service=adservice metric=jvm_memory_pool_MB_used.Tenured_Gen baseline=37.856319 peak=38.050049 signed_z=532.822 onset_bin=44 onset_rel_s=1627.031 persistence_bins=13
values_compact=delta:37.85582,0.000025,0.000097,0.000183,0,0,0.000051,0.00001,0,0,0,0.000013,0.000063,0,0,0.000366,0.000295,0.000011,0,0.000148,0.000111,0.000041,0.00002,0,0,0.00007,0.000098,0.064107,0.128072,0.000107,0.000036,0.00004,0.000169,0.00002,0,0,0,0.000006,0.00007,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M9] rank=9 service=shippingservice-1 metric=container_network_receive_MB.eth0 baseline=0.029767 peak=0.545834 signed_z=219.984 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.02948,-0.000785,0.001747,-0.003064,0.003373,-0.003413,0.000288,0.003196,-0.002178,0.001932,-0.002988,0.002637,-0.000329,0.000377,0.00049,-0.005405,0.004976,0.005629,-0.00144,-0.005851,-0.004968,0.003684,0.004143,-0.005554,0.004079,-0.00052,0.005097,-0.000196,0.511397,-0.515776,0.000325,0.002331,0.000506,-0.012823,0.016129,-0.007753,-0.007081,0.009352,0.002311,-0.004449
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M10] rank=10 service=currencyservice2-0 metric=container_network_receive_MB.eth0 baseline=0.018915 peak=0.537045 signed_z=205.103 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.019024,-0.002062,0.001562,0.000219,0.000731,0.000631,-0.001675,-0.00125,0.002144,0.004336,-0.005199,-0.001299,0.001349,-0.004244,0.005078,0.004821,-0.006798,-0.003287,0.006863,0.001616,-0.00283,0.517315,-0.518053,-0.000051,-0.00096,0.001674,-0.001775,-0.00478,0.007123,0.001795,-0.009163,0.010181,-0.002699,0.000579,-0.001373,-0.002644,0.002225,-0.00005,0.003217,-0.004198
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M11] rank=11 service=istio-egressgateway-7bfdcc9d86-22q7z metric=istio_agent_process_resident_memory_bytes baseline=43555635.2 peak=44343296.0 signed_z=201.585 onset_bin=31 onset_rel_s=1151.719 persistence_bins=21
values_compact=delta:43556864,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-8192,-8192,401408,401408,-442368,-442368,239616,239616,0,0,0,0,0,0,0,0,0,0,-147456,-147456,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M12] rank=12 service=cartservice2-0 metric=container_network_receive_MB.eth0 baseline=0.02038 peak=0.540387 signed_z=147.584 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.019181,0.004512,-0.013007,0.012802,0.00194,-0.006412,0.001706,-0.000986,0.001476,0.000198,-0.002229,-0.006002,0.006584,0.00149,0.004298,-0.000779,-0.004224,-0.00115,0.000619,-0.000657,0.002577,-0.002193,-0.002926,-0.000836,0.007074,0.002307,-0.004107,0.000683,-0.00276,0.521208,-0.522475,0.003199,-0.000318,-0.001112,-0.000416,0.002423,-0.001203,0.001937,-0.000212,-0.002936
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[1260.0,2340.0]

=== LOG SUMMARY ===
{"entries":[{"change_pct":-23.5,"n_during":88,"n_pre":115,"service":"emailservice-2"},{"change_pct":-21.4,"n_during":506,"n_pre":644,"service":"checkoutservice-1"},{"change_pct":-21.0,"n_during":13995,"n_pre":17720,"service":"frontend-1"},{"change_pct":-20.9,"n_during":492,"n_pre":622,"service":"checkoutservice-0"},{"change_pct":-20.9,"n_during":87,"n_pre":110,"service":"paymentservice-2"},{"change_pct":-20.8,"n_during":900,"n_pre":1136,"service":"adservice-0"},{"change_pct":-20.8,"n_during":898,"n_pre":1134,"service":"adservice-1"},{"change_pct":-20.8,"n_during":506,"n_pre":639,"service":"checkoutservice-2"}],"mode":"volume","omitted_services":23,"service_count":31}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":-17.9,"error_pct":0.0,"p95_during_ms":0.015599999999999966,"p95_pre_ms":0.019,"service":"adservice-0","spans":1016},{"delta_pct":-8.1,"error_pct":0.0,"p95_during_ms":183.98949999999994,"p95_pre_ms":200.22694999999996,"service":"checkoutservice-0","spans":776},{"delta_pct":7.5,"error_pct":0.0,"p95_during_ms":0.08159999999999996,"p95_pre_ms":0.07589999999999995,"service":"shippingservice-2","spans":470},{"delta_pct":-6.6,"error_pct":0.0,"p95_during_ms":0.13994999999999996,"p95_pre_ms":0.14989999999999998,"service":"paymentservice-0","spans":68},{"delta_pct":-5.0,"error_pct":0.0,"p95_during_ms":0.019,"p95_pre_ms":0.02,"service":"adservice-1","spans":1015},{"delta_pct":-4.9,"error_pct":0.0,"p95_during_ms":0.117,"p95_pre_ms":0.123,"service":"currencyservice-0","spans":5177},{"delta_pct":4.9,"error_pct":0.0,"p95_during_ms":0.08139999999999999,"p95_pre_ms":0.07759999999999996,"service":"shippingservice-1","spans":470},{"delta_pct":4.3,"error_pct":0.0,"p95_during_ms":0.14775,"p95_pre_ms":0.14159999999999998,"service":"paymentservice-1","spans":69}],"omitted_services":22,"service_count":30}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=14 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":1200.0,"rank":1,"service":"redis-cart","severity_z":81.25},{"evidence_source":"metric","onset_rel_s":1260.0,"rank":2,"service":"currencyservice2","severity_z":205.103},{"evidence_source":"metric","onset_rel_s":1260.0,"rank":3,"service":"istio-egressgateway","severity_z":201.585},{"evidence_source":"metric","onset_rel_s":1260.0,"rank":4,"service":"emailservice2","severity_z":82.907},{"evidence_source":"metric","onset_rel_s":1320.0,"rank":5,"service":"adservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1320.0,"rank":6,"service":"node-1","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1440.0,"rank":7,"service":"productcatalogservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1440.0,"rank":8,"service":"cartservice","severity_z":58.622},{"evidence_source":"metric","onset_rel_s":1620.0,"rank":9,"service":"checkoutservice2","severity_z":110.201},{"evidence_source":"metric","onset_rel_s":1680.0,"rank":10,"service":"shippingservice","severity_z":219.984},{"evidence_source":"metric","onset_rel_s":1680.0,"rank":11,"service":"paymentservice","severity_z":91.704},{"evidence_source":"metric","onset_rel_s":1740.0,"rank":12,"service":"cartservice2","severity_z":147.584},{"evidence_source":"metric","onset_rel_s":1740.0,"rank":13,"service":"recommendationservice","severity_z":65.019},{"evidence_source":"metric","onset_rel_s":1920.0,"rank":14,"service":"frontend2","severity_z":131.333}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"productcatalogservice","caller":"recommendationservice"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

## Assistant

{
"services": [
"node-1",
"adservice",
"productcatalogservice-1",
"istio-egressgateway-7bfdcc9d86-22q7z",
"currencyservice2-0"
],
"reason": "Node-1 is the root cause because it exhibits a critical system-level disk usage anomaly (z=999) that coincides with the earliest onset of faults in co-located services like adservice and productcatalogservice-1, indicating infrastructure saturation rather than application-level failure.",
"confidence": "high"
}
