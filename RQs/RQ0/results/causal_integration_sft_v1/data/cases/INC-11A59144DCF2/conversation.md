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
opaque_id: INC-11A59144DCF2
observation_window={"duration_rel_s":1440.0,"source_metric_rows":1441}
selection_summary={"candidate_count":17,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":269,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","cartservice","checkoutservice","currencyservice","emailservice","frontend","frontend-external","gke-gke-cluster-default-pool-2e1807ce-0e4z","gke-gke-cluster-default-pool-2e1807ce-cx8g","gke-gke-cluster-default-pool-2e1807ce-w819","gke-gke-cluster-default-pool-2e1807ce-xte3","loadgenerator","paymentservice","productcatalogservice","recommendationservice","redis","shippingservice"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[11.25,33.75,56.25,78.75,101.25,123.75,146.25,168.75,191.25,213.75,236.25,258.75,281.25,303.75,326.25,348.75,371.25,393.75,416.25,438.75,461.25,483.75,506.25,528.75,551.25,573.75,596.25,618.75,641.25,663.75,686.25,708.75,731.25,753.75,776.25,798.75,821.25,843.75,866.25,888.75,911.25,933.75,956.25,978.75,1001.25,1023.75,1046.25,1068.75,1091.25,1113.75,1136.25,1158.75,1181.25,1203.75,1226.25,1248.75,1271.25,1293.75,1316.25,1338.75,1361.25,1383.75,1406.25,1428.75]
[M1] rank=1 service=emailservice metric=container-cpu-system-seconds-total baseline=0.067509 peak=16.393819 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=delta:0.064159,-0.010703,0.010388,-0.008669,-0.001011,0.02053,-0.009573,-0.003562,-0.00015,0.023714,0.001039,-0.030637,0.019453,0.01678,-0.024601,-0.015868,0.023209,0.011658,0.002146,-0.014595,-0.01409,0.002137,0.015807,0.002769,0.002354,-0.007497,-0.009005,-0.004578,0.003455,0.009473,-0.002069,0.000748,0.004348,8.794012,5.657919,1.060319,-0.067423,-0.097219,0.225699,-0.974156,0.14159,1.121473,-0.397361,-0.593885,0.740319,0.35783,-1.174248,-0.058904,0.843927,-0.847948,-0.05254,0.925243,-0.664261,-0.357842,0.721661,-0.480172,-0.302909,0.367489,0.423524,-0.817301,0,0.020632,0.6219,0.283389
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M2] rank=2 service=emailservice metric=container-memory-failures-total baseline=0.014572 peak=135.536398 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=2
values_compact=rle:0*2,0.043195*1,0.042128*1,0*10,0.113716*1,0.113576*1,0*9,0.035123*1,0.06065*1,0.041244*1,0*5,122.318872*1,86.494747*1,0*2,0.042895*1,0.037887*1,0*9,0.041512*1,0.042179*1,0*14
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M3] rank=3 service=emailservice metric=container-memory-mapped-file baseline=0.0 peak=2293760.0 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=rle:0*33,2293760*31
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M4] rank=4 service=emailservice metric=container-memory-rss baseline=41353045.333333 peak=42999808.0 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=rle:41353216*33,42995712*15,42999808*16
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M5] rank=5 service=emailservice metric=container-memory-usage-bytes baseline=42363426.133333 peak=268427264.0 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=delta:42364928,0,0,0,-4096,0,4096,0,-4096,0,0,4096,0,-4096,0,8192,-4096,-4096,0,4096,-4096,0,0,4096,-4096,4096,-4096,4096,-4096,4096,0,4096,-4096,225976320,-36864,4096,69632,-110559232,110563328,28672,-147456,-54386688,54517760,-323584,217088,-100478976,100458496,16384,28672,98304,-32768,32768,-28672,4096,-106496,-36864,98304,20480,8192,40960,0,-32768,49152,-16384
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M6] rank=6 service=emailservice metric=container-memory-working-set-bytes baseline=42363426.133333 peak=55250944.0 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=delta:42364928,0,0,0,-4096,0,4096,0,-4096,0,0,4096,0,-4096,0,8192,-4096,-4096,0,4096,-4096,0,0,4096,-4096,4096,-4096,4096,-4096,4096,0,4096,-4096,12349440,-212992,-4145152,4050944,-3891200,-794624,0,5529600,-3280896,-2105344,4796416,-581632,-3383296,4075520,-356352,-532480,-69632,1413120,-5586944,3821568,1576960,-5480448,5615616,-274432,167936,-5349376,0,53248,5206016,-1036288,-4222976
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M7] rank=7 service=emailservice metric=istio-latency-50 baseline=0.003053 peak=0.063793 signed_z=723.281 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.003069,0.003018,0.003,0.003,0.003,0.003,0.003,0.003054,0.003071,0.003,0.003042,0.003092,0.003067,0.003,0.003,0.003049,0.003059,0.003093,0.003095,0.003,0.003,0.003041,0.003053,0.003,0.003,0.003,0.003,0.003022,0.003057,0.003174,0.003438,0.003258,0.003,0.004044,0.004733,0.060897,0.058333,0.004415,0.01,0.056771,0.063636,0.032976,0.004417,0.028422,0.004714,0.056848,0.05,0.026042,0.015,0.044751,0.060714,0.060829,0.06371,0.027878,0.004636,0.051794,0.005,0.05354,0.05625,0.05413,0.005,0.029778,0.04375,0.00481]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M8] rank=8 service=emailservice metric=container-cpu-usage-seconds-total baseline=0.303233 peak=20.006288 signed_z=499.242 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=delta:0.400494,-0.098064,-0.008363,-0.008184,-0.008544,0.021829,-0.0331,0.037436,-0.028807,0.006785,0.030051,0.001758,-0.026755,0.033074,-0.004717,-0.010267,0.004178,0.005509,0.010801,-0.011512,0.031246,0.017812,-0.06731,-0.016703,0.030251,0.019798,0.027011,-0.012991,-0.048613,0.021612,-0.002445,-0.02135,0.001348,11.580458,6.87571,1.109298,-0.068098,-0.032783,0.097758,-0.000787,0.061189,0.004313,0.007088,0.029873,-0.060025,0.013,0.039831,-0.036202,-0.053834,0.053139,0.026863,-0.151046,0.051762,0.09773,-0.133151,-0.009129,0.097993,0.014103,-0.051392,0.002579,0.128844,-0.016425,-0.033216,-0.007299
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M9] rank=9 service=emailservice metric=container-memory-cache baseline=0.0 peak=221159424.0 signed_z=226.309 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,215924736,241664,4128768,-3960832,-106680320,111390720,-8192,-5677056,-51060736,56659968,-5222400,786432,-97034240,96301056,430080,593920,118784,-1396736,5570560,-3891200,-1388544,5197824,-5623808,335872,-147456,5496832,45056,-69632,-5259264,1019904,4337664
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M10] rank=10 service=emailservice metric=istio-latency-90 baseline=0.004759 peak=0.094048 signed_z=209.345 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.004724,0.004632,0.0046,0.0046,0.0046,0.0046,0.0046,0.004697,0.004729,0.0046,0.004675,0.004766,0.00472,0.0046,0.0046,0.004688,0.004706,0.004767,0.004771,0.0046,0.0046,0.004674,0.004695,0.0046,0.0046,0.0046,0.0046,0.004639,0.004703,0.004914,0.007214,0.005625,0.0046,0.083214,0.088333,0.092179,0.091667,0.08683,0.089524,0.091354,0.092727,0.090595,0.087188,0.089866,0.089167,0.09137,0.09,0.087614,0.0875,0.091795,0.094048,0.092166,0.092742,0.088328,0.0875,0.090359,0.09,0.090708,0.09125,0.090826,0.088,0.08956,0.089706,0.0875]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M11] rank=11 service=emailservice metric=container-cpu-user-seconds-total baseline=0.235725 peak=5.742488 signed_z=146.257 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.336337,0.248972,0.230221,0.230915,0.223175,0.224476,0.200416,0.241946,0.213289,0.196359,0.215701,0.257766,0.211555,0.222043,0.255734,0.254132,0.234306,0.228156,0.236814,0.239894,0.291984,0.300908,0.21779,0.197262,0.226211,0.247725,0.285202,0.28111,0.229046,0.241186,0.236358,0.218707,0.218418,3.002156,4.219948,4.268923,4.268923,3.782981,4.197825,5.178116,5.07741,3.980551,4.385004,4.985937,4.208416,3.863705,5.077665,5.100365,4.214853,5.103695,5.183096,4.106806,4.82283,5.226729,4.423591,4.894636,5.15095,4.942149,4.469812,4.469812,5.415957,5.378898,4.521755,4.433097]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M12] rank=12 service=emailservice metric=istio-latency-95 baseline=0.00513 peak=0.098214 signed_z=108.675 onset_bin=30 onset_rel_s=686.25 persistence_bins=33
values_compact=raw:[0.004931,0.004834,0.0048,0.0048,0.0048,0.0048,0.0048,0.004903,0.004936,0.0048,0.004879,0.004975,0.004927,0.0048,0.0048,0.004893,0.004912,0.004977,0.004981,0.0048,0.0048,0.004878,0.0049,0.0048,0.0048,0.0048,0.0048,0.004841,0.004909,0.006875,0.008607,0.007813,0.0048,0.091607,0.094167,0.09609,0.095833,0.093415,0.094762,0.095677,0.096364,0.095298,0.093594,0.094933,0.094583,0.095685,0.095,0.093807,0.09375,0.096966,0.098214,0.096083,0.096371,0.094164,0.09375,0.095179,0.095,0.095354,0.095625,0.095413,0.094,0.09478,0.094853,0.09375]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[713.0,1440.0]

=== LOG SUMMARY ===
{"entries":[{"change_pct":50.0,"n_during":15,"n_pre":10,"service":"redis"},{"change_pct":3.6,"n_during":1026,"n_pre":990,"service":"checkoutservice"},{"change_pct":3.6,"n_during":342,"n_pre":330,"service":"emailservice"},{"change_pct":3.6,"n_during":684,"n_pre":660,"service":"paymentservice"},{"change_pct":3.4,"n_during":5470,"n_pre":5292,"service":"shippingservice"},{"change_pct":3.1,"n_during":6845,"n_pre":6638,"service":"recommendationservice"},{"change_pct":2.8,"n_during":9419,"n_pre":9159,"service":"cartservice"},{"change_pct":2.8,"n_during":32722,"n_pre":31841,"service":"frontend"}],"mode":"volume","omitted_services":2,"service_count":10}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":148.7,"error_pct":0.0,"p95_during_ms":1.3008499999999978,"p95_pre_ms":0.523,"service":"emailservice","spans":1248},{"delta_pct":40.3,"error_pct":0.0,"p95_during_ms":101.41799999999971,"p95_pre_ms":72.31139999999996,"service":"checkoutservice","spans":9252},{"delta_pct":8.8,"error_pct":0.0,"p95_during_ms":5.110199999999997,"p95_pre_ms":4.695949999999999,"service":"recommendationservice","spans":27542},{"delta_pct":7.1,"error_pct":0.0,"p95_during_ms":0.03,"p95_pre_ms":0.028,"service":"productcatalogservice","spans":103572},{"delta_pct":3.7,"error_pct":0.0,"p95_during_ms":0.7837500000000001,"p95_pre_ms":0.7557499999999991,"service":"paymentservice","spans":960},{"delta_pct":-2.7,"error_pct":0.0,"p95_during_ms":0.217,"p95_pre_ms":0.223,"service":"currencyservice","spans":57995},{"delta_pct":1.2,"error_pct":0.0,"p95_during_ms":55.83039999999999,"p95_pre_ms":55.170849999999994,"service":"frontend","spans":208961}],"omitted_services":0,"service_count":7}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=3 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":720.0,"rank":1,"service":"adservice","severity_z":10.199},{"evidence_source":"trace","onset_rel_s":735.0,"rank":2,"service":"emailservice","severity_z":732.209},{"evidence_source":"metric","onset_rel_s":1114.8,"rank":3,"service":"checkoutservice","severity_z":13.89},{"evidence_source":"trace","onset_rel_s":1155.0,"rank":4,"service":"paymentservice","severity_z":18.107},{"evidence_source":"none","onset_rel_s":null,"rank":5,"service":"frontend-external","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":6,"service":"gke-gke-cluster-default-pool-2e1807ce-cx8g","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":7,"service":"redis","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":8,"service":"recommendationservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":9,"service":"gke-gke-cluster-default-pool-2e1807ce-w819","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":10,"service":"cartservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":11,"service":"frontend","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":12,"service":"currencyservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":13,"service":"shippingservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":14,"service":"loadgenerator","severity_z":0.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"currencyservice","caller":"checkoutservice"},{"callee":"emailservice","caller":"checkoutservice"},{"callee":"paymentservice","caller":"checkoutservice"},{"callee":"checkoutservice","caller":"frontend"},{"callee":"currencyservice","caller":"frontend"},{"callee":"recommendationservice","caller":"frontend"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"high","reason":"Rank emailservice first because emailservice has direct container-cpu-system-seconds-total evidence (signed-z 999, persistence 31 bins); although checkoutservice is salient, the caller path checkoutservice -> emailservice means a disturbance in the callee can propagate back toward that caller-side symptom.","services":["emailservice","checkoutservice"]}
