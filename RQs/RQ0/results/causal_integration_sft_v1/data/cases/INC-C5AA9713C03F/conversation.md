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
opaque_id: INC-C5AA9713C03F
observation_window={"duration_rel_s":2340.0,"source_metric_rows":40}
selection_summary={"candidate_count":63,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":1354,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","adservice-grpc","adservice-http","adservice2","adservice2-0","cartservice-0","cartservice-1","cartservice-2","cartservice-grpc","cartservice2-0","checkoutservice-0","checkoutservice-1","checkoutservice-2","checkoutservice-grpc","checkoutservice2-0","currencyservice-0","currencyservice-1","currencyservice-2","currencyservice-grpc","currencyservice2-0","emailservice-0","emailservice-1","emailservice-2","emailservice-grpc","emailservice2-0","frontend-0","frontend-1","frontend-2","frontend-http","frontend2-0","istio-egressgateway-7bfdcc9d86-22q7z","istio-ingressgateway-565bffd4d-4nr6v","node-1","node-2","node-3","node-4","node-5","node-6","paymentservice-0","paymentservice-1","paymentservice-2","paymentservice-grpc","paymentservice2-0","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","productcatalogservice-grpc","productcatalogservice2-0","recommendationservice-0","recommendationservice-1","recommendationservice-2","recommendationservice-grpc","recommendationservice2-0","redis-cart-0","redis-cart2-0","shippingservice-0","shippingservice-1","shippingservice-2","shippingservice-grpc","shippingservice2-0"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[18.281,54.844,91.406,127.969,164.531,201.094,237.656,274.219,310.781,347.344,383.906,420.469,457.031,493.594,530.156,566.719,603.281,639.844,676.406,712.969,749.531,786.094,822.656,859.219,895.781,932.344,968.906,1005.469,1042.031,1078.594,1115.156,1151.719,1188.281,1224.844,1261.406,1297.969,1334.531,1371.094,1407.656,1444.219,1480.781,1517.344,1553.906,1590.469,1627.031,1663.594,1700.156,1736.719,1773.281,1809.844,1846.406,1882.969,1919.531,1956.094,1992.656,2029.219,2065.781,2102.344,2138.906,2175.469,2212.031,2248.594,2285.156,2321.719]
[M1] rank=1 service=adservice2 metric=java_lang_Memory_ObjectPendingFinalizationCount baseline=0.0 peak=0.083333 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.083333,-0.083333,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M2] rank=2 service=adservice metric=java_lang_GarbageCollector_LastGcInfo_memoryUsageAfterGc_used.Tenured_Gen.Copy baseline=52554647.8 peak=52757440.0 signed_z=999.0 onset_bin=41 onset_rel_s=1517.344 persistence_bins=15
values_compact=delta:52554340,148,0,0,0,53.333333,10.666667,26.666667,53.333333,0,0,32,32,0,0,69.333333,122.666667,0,0,26.666667,53.333333,37.333333,26.666667,167284,34004,416,128,0,10.666667,85.333333,37.333333,58.666667,21.333333,58.666667,48,0,26.666667,160,69.333333,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M3] rank=3 service=adservice metric=java_lang_GarbageCollector_LastGcInfo_memoryUsageBeforeGc_used.Tenured_Gen.Copy baseline=52554635.466667 peak=52757440.0 signed_z=999.0 onset_bin=41 onset_rel_s=1517.344 persistence_bins=15
values_compact=delta:52554306.666667,133.333333,48,0,0,32,32,0,80,0,0,5.333333,58.666667,0,0,16,165.333333,10.666667,0,0,80,16,48,100358.666667,100646.666666,666.666667,117.333333,42.666667,0,64,64,48,16,64,58.666667,5.333333,5.333333,112,138.666667,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M4] rank=4 service=adservice metric=java_lang_MemoryPool_Usage_used.Tenured_Gen baseline=52554647.8 peak=52757440.0 signed_z=999.0 onset_bin=41 onset_rel_s=1517.344 persistence_bins=15
values_compact=delta:52554340,148,0,0,0,53.333333,10.666667,26.666667,53.333333,0,0,32,32,0,0,69.333333,122.666667,0,0,26.666667,53.333333,37.333333,26.666667,167284,34004,416,128,0,10.666667,85.333333,37.333333,58.666667,21.333333,58.666667,48,0,26.666667,160,69.333333,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M5] rank=5 service=adservice metric=jvm_memory_pool_MB_used.Tenured_Gen baseline=50.120019 peak=50.313416 signed_z=999.0 onset_bin=41 onset_rel_s=1517.344 persistence_bins=15
values_compact=delta:50.119729,0.000136,0,0,0,0.000051,0.00001,0.000032,0.000045,0,0,0.00003,0.000031,0,0,0.000081,0.000102,0,0,0.000032,0.000044,0.000041,0.00002,0.175485,0.01655,0.000335,0.000112,0,0.000015,0.000082,0.000035,0.000051,0.000021,0.000061,0.00004,0,0.000031,0.000147,0.000067,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M6] rank=6 service=adservice metric=jvm_memory_pool_allocated_MB_total.Tenured_Gen baseline=109.789428 peak=109.982826 signed_z=999.0 onset_bin=41 onset_rel_s=1517.344 persistence_bins=15
values_compact=delta:109.789124,0.000152,0,0,0,0.000051,0.00001,0.000026,0.00005,0,0,0.000026,0.000035,0,0,0.000067,0.000117,0,0,0.000025,0.000051,0.000035,0.000026,0.159526,0.032437,0.000397,0.000122,0,0.00001,0.000081,0.000036,0.000056,0.000015,0.000061,0.000046,0,0.000026,0.000137,0.000081,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M7] rank=7 service=paymentservice2-0 metric=container_network_receive_MB.eth0 baseline=0.018847 peak=0.539347 signed_z=320.302 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.020311,-0.001207,0,-0.000395,0.002809,-0.004784,0.000363,-0.000654,0.001771,0.00394,-0.002956,-0.001071,0.00372,-0.002806,-0.002339,0.002796,-0.000826,0.000794,-0.001888,-0.00015,0.002851,-0.003008,0.002595,-0.00513,0.00362,0.003006,-0.003103,0.001984,-0.002972,0.522076,-0.520912,-0.002033,-0.000096,0.00185,0.004069,-0.001833,-0.002051,0.001189,-0.003422,0.003622
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M8] rank=8 service=currencyservice2-0 metric=container_network_receive_MB.eth0 baseline=0.018322 peak=0.541067 signed_z=221.948 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.018274,-0.000541,0,0.002985,-0.001944,-0.001489,0.002239,-0.00125,-0.000499,0.002518,-0.004038,0.004268,-0.002499,0.003269,-0.005943,0.000711,0.007757,-0.004701,-0.006556,0.004497,0.524009,-0.51857,-0.004149,0.000526,0.000657,0.000324,0.002249,-0.003748,0.000668,-0.0005,-0.000313,0.000563,0.001157,-0.000158,-0.00293,0.00343,-0.001754,-0.000663,0.001418,-0.001562
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M9] rank=9 service=paymentservice-2 metric=container_network_receive_MB.eth0 baseline=0.019806 peak=0.535219 signed_z=196.244 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.022196,0.001792,0,-0.004319,-0.002628,0.00565,-0.006475,0.006442,-0.003658,-0.000364,-0.000163,0.002128,-0.006596,0.004176,0.000221,0.002899,0.000679,-0.002267,0.000994,-0.004028,0.004709,-0.002269,0.001437,-0.002132,-0.000464,0.004334,-0.004252,0.001443,0.515734,-0.512934,-0.000844,0.001199,-0.00301,-0.003576,0.005957,-0.003352,-0.000229,0.00287,-0.002051,-0.001645
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M10] rank=10 service=cartservice2-0 metric=container_network_receive_MB.eth0 baseline=0.020249 peak=0.536736 signed_z=185.361 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.020617,-0.003216,0,0.001394,0.000497,0.00607,-0.008316,0.00563,-0.002128,-0.007713,0.010697,-0.00077,-0.0023,0.000833,-0.000247,-0.002771,0.005201,-0.003524,-0.000242,0.002769,-0.00471,0.005831,-0.010286,0.008007,0.002392,-0.002901,-0.000689,-0.002917,0.001282,0.006128,0.512118,-0.513007,-0.003743,0.000694,-0.000894,0.000831,0.000558,-0.007436,0.007244,0.004505
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M11] rank=11 service=node-5 metric=system.udp.connect.num baseline=10.0 peak=12.0 signed_z=166.667 onset_bin=41 onset_rel_s=1517.344 persistence_bins=15
values_compact=delta:10,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,-1,1,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M12] rank=12 service=productcatalogservice2-0 metric=container_network_receive_MB.eth0 baseline=0.021369 peak=0.590576 signed_z=164.052 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.020102,-0.002501,0,0.00466,-0.00034,0.003535,-0.002539,0.002909,-0.013016,0.008344,0.000535,-0.000315,0.006631,-0.009777,0.000561,0.001189,0.006005,-0.004215,-0.002333,0.005036,0.00003,-0.003983,0.004446,0.565612,-0.567912,0.00135,-0.001248,-0.001127,0.003444,-0.0024,-0.005814,0.006107,-0.003985,0.005051,-0.003448,0.001839,-0.002643,-0.003873,0.006534,0.003424
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[1320.0,2340.0]

=== LOG SUMMARY ===
{"entries":[{"change_pct":-54.5,"n_during":10,"n_pre":22,"service":"redis-cart-0"},{"change_pct":-39.1,"n_during":78,"n_pre":128,"service":"paymentservice-1"},{"change_pct":-36.2,"n_during":81,"n_pre":127,"service":"emailservice-1"},{"change_pct":-35.0,"n_during":455,"n_pre":700,"service":"checkoutservice-1"},{"change_pct":-33.6,"n_during":81,"n_pre":122,"service":"emailservice-0"},{"change_pct":-31.9,"n_during":461,"n_pre":677,"service":"checkoutservice-0"},{"change_pct":-30.8,"n_during":756,"n_pre":1092,"service":"shippingservice-2"},{"change_pct":-29.9,"n_during":16044,"n_pre":22884,"service":"frontend-2"}],"mode":"volume","omitted_services":23,"service_count":31}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":-9.6,"error_pct":0.0,"p95_during_ms":0.017,"p95_pre_ms":0.018799999999999952,"service":"adservice-0","spans":1018},{"delta_pct":-6.8,"error_pct":0.0,"p95_during_ms":0.148,"p95_pre_ms":0.15874999999999995,"service":"paymentservice-2","spans":68},{"delta_pct":-6.1,"error_pct":0.0,"p95_during_ms":0.14774999999999996,"p95_pre_ms":0.1574,"service":"paymentservice-0","spans":69},{"delta_pct":-6.0,"error_pct":0.0,"p95_during_ms":0.07714999999999998,"p95_pre_ms":0.08210000000000002,"service":"shippingservice-2","spans":478},{"delta_pct":-5.4,"error_pct":0.0,"p95_during_ms":0.24495,"p95_pre_ms":0.2588999999999999,"service":"emailservice-1","spans":70},{"delta_pct":-5.0,"error_pct":0.0,"p95_during_ms":0.019,"p95_pre_ms":0.02,"service":"adservice-1","spans":1019},{"delta_pct":-5.0,"error_pct":0.0,"p95_during_ms":0.114,"p95_pre_ms":0.12,"service":"currencyservice-1","spans":5202},{"delta_pct":-4.9,"error_pct":0.0,"p95_during_ms":0.07514999999999998,"p95_pre_ms":0.079,"service":"shippingservice-0","spans":476}],"omitted_services":22,"service_count":30}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=15 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":1200.0,"rank":1,"service":"currencyservice2","severity_z":221.948},{"evidence_source":"metric","onset_rel_s":1200.0,"rank":2,"service":"emailservice","severity_z":76.996},{"evidence_source":"metric","onset_rel_s":1320.0,"rank":3,"service":"redis-cart2","severity_z":148.377},{"evidence_source":"metric","onset_rel_s":1380.0,"rank":4,"service":"adservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1380.0,"rank":5,"service":"productcatalogservice2","severity_z":164.052},{"evidence_source":"metric","onset_rel_s":1440.0,"rank":6,"service":"checkoutservice","severity_z":102.809},{"evidence_source":"metric","onset_rel_s":1440.0,"rank":7,"service":"emailservice2","severity_z":101.412},{"evidence_source":"metric","onset_rel_s":1500.0,"rank":8,"service":"adservice2","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1500.0,"rank":9,"service":"node-5","severity_z":166.667},{"evidence_source":"metric","onset_rel_s":1680.0,"rank":10,"service":"paymentservice","severity_z":196.244},{"evidence_source":"metric","onset_rel_s":1740.0,"rank":11,"service":"paymentservice2","severity_z":320.302},{"evidence_source":"metric","onset_rel_s":1800.0,"rank":12,"service":"cartservice2","severity_z":185.361},{"evidence_source":"trace","onset_rel_s":2120.4,"rank":13,"service":"cartservice","severity_z":7.452},{"evidence_source":"metric","onset_rel_s":2280.0,"rank":14,"service":"node-3","severity_z":32.829}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"cartservice","caller":"checkoutservice"},{"callee":"emailservice","caller":"checkoutservice"},{"callee":"paymentservice","caller":"checkoutservice"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

[excluded before optimizer]
