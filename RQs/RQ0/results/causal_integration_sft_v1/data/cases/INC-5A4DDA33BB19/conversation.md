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
opaque_id: INC-5A4DDA33BB19
observation_window={"duration_rel_s":1440.0,"source_metric_rows":1441}
selection_summary={"candidate_count":17,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":265,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","cartservice","checkoutservice","currencyservice","emailservice","frontend","frontend-external","gke-gke-cluster-default-pool-2e1807ce-0e4z","gke-gke-cluster-default-pool-2e1807ce-cx8g","gke-gke-cluster-default-pool-2e1807ce-w819","gke-gke-cluster-default-pool-2e1807ce-xte3","loadgenerator","paymentservice","productcatalogservice","recommendationservice","redis","shippingservice"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[11.25,33.75,56.25,78.75,101.25,123.75,146.25,168.75,191.25,213.75,236.25,258.75,281.25,303.75,326.25,348.75,371.25,393.75,416.25,438.75,461.25,483.75,506.25,528.75,551.25,573.75,596.25,618.75,641.25,663.75,686.25,708.75,731.25,753.75,776.25,798.75,821.25,843.75,866.25,888.75,911.25,933.75,956.25,978.75,1001.25,1023.75,1046.25,1068.75,1091.25,1113.75,1136.25,1158.75,1181.25,1203.75,1226.25,1248.75,1271.25,1293.75,1316.25,1338.75,1361.25,1383.75,1406.25,1428.75]
[M1] rank=1 service=emailservice metric=container-memory-failures-total baseline=0.048649 peak=245527.137042 signed_z=999.0 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=delta:0,0,0,0,0.256066,0.012661,-0.268727,0,0,0,0,0,0,0,0,0.227879,0.037109,-0.224848,-0.04014,0,0,0,0,0,0,0,0,0.232261,0.036773,-0.228829,-0.040205,0,16835.242608,101274.959506,81209.476976,29047.890305,15.885654,-9414.179637,4603.768349,10405.303329,-15643.861052,10008.28885,-1332.532276,-15226.945026,5119.060612,7565.429368,14648.068579,-20583.224136,9496.043082,7609.096806,-7810.971698,2906.266513,-5416.571378,-12206.173106,5937.441734,17764.577488,-2221.809673,-18165.039061,1336.728236,15092.820082,1274.796241,-2754.407612,-7591.153409,2738.469891
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M2] rank=2 service=emailservice metric=container-memory-mapped-file baseline=0.0 peak=2293760.0 signed_z=999.0 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=rle:0*32,2293760*32
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M3] rank=3 service=emailservice metric=container-memory-rss baseline=40962764.8 peak=261324800.0 signed_z=999.0 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=delta:40964096,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-4096,0,4096,0,0,0,0,0,0,0,0,-24576,20480,4096,0,0,0,65949696,-36861952,-6408192,-21090304,70156288,148615168,-63246336,-16289792,79536128,-166199296,166199296,0,0,-218710016,68792320,149917696,-177999872,177995776,-146460672,-70283264,39481344,177266688,0,-129617920,-75149312,204767232,-4096,4096,-64536576,-57815040,122347520,-11755520
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M4] rank=4 service=emailservice metric=container-memory-usage-bytes baseline=43980640.711111 peak=268439552.0 signed_z=999.0 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=delta:43982848,-4096,4096,0,0,0,0,0,4096,-4096,4096,-4096,0,-4096,0,-4096,0,8192,-4096,2048,-2048,0,4096,-4096,4096,4096,-28672,20480,4096,0,4096,-4096,72105984,-40101888,-5232640,-21549056,70713344,148516864,-63148032,-16297984,79446016,-166137856,166137856,0,4096,-219664384,69758976,149905408,-177946624,177946624,-146280448,-70471680,39550976,177199104,-2048,-129617920,-75149312,204767232,0,0,-64532480,-57819136,122351616,-11640832
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M5] rank=5 service=emailservice metric=container-memory-working-set-bytes baseline=43902816.711111 peak=268439552.0 signed_z=999.0 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=delta:43905024,-4096,4096,0,0,0,0,0,4096,-4096,4096,-4096,0,-4096,0,-4096,0,8192,-4096,2048,-2048,0,4096,-4096,4096,4096,-28672,20480,4096,0,4096,-4096,72105984,-40024064,-5232640,-21549056,70713344,148516864,-63148032,-16297984,79446016,-166137856,166137856,0,4096,-219664384,69758976,149905408,-177946624,177946624,-146280448,-70471680,39550976,177199104,-2048,-129617920,-75149312,204767232,0,0,-64532480,-57819136,122351616,-11640832
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M6] rank=6 service=emailservice metric=istio-latency-50 baseline=0.003049 peak=0.625 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.003133,0.003167,0.003,0.003,0.003,0.003065,0.003065,0.003,0.003,0.003,0.003,0.003105,0.003118,0.003107,0.003083,0.003045,0.003049,0.003,0.003,0.003049,0.003057,0.003053,0.003047,0.003048,0.003043,0.003044,0.003049,0.003,0.003043,0.003091,0.003098,0.003065,0.003,0.004467,0.375,0.1,0.090909,0.5625,0.1375,0.0825,0.084091,0.08125,0.0875,0.6,0.607143,0.25,0.375,0.25,0.25,0.35,0.34375,0.333333,0.28125,0.077273,0.075,0.0625,0.075,0.625,0.08,0.075,0.095,0.072222,0.0775,0.2125]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M7] rank=7 service=emailservice metric=istio-latency-90 baseline=0.004689 peak=2.171875 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.00484,0.0049,0.0046,0.0046,0.0046,0.004716,0.004716,0.0046,0.0046,0.0046,0.0046,0.004789,0.004812,0.004793,0.00475,0.004682,0.004688,0.0046,0.0046,0.004688,0.004703,0.004695,0.004684,0.004686,0.004677,0.00468,0.004688,0.0046,0.004678,0.004764,0.004776,0.004716,0.0046,1.72,2.083333,1.675,0.92,1.885,1.915,1.2625,0.7875,1.0,1.9,2.0,1.87,1.985714,2.10625,2.0875,1.975,1.72,1.45,1.95,1.9125,1.87,1.885,1.575,1.99,2.171875,2.05,1.75,2.025,1.875,1.8375,1.975]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M8] rank=8 service=emailservice metric=istio-latency-95 baseline=0.005009 peak=2.335938 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.006,0.00675,0.0048,0.0048,0.0048,0.004923,0.004923,0.0048,0.0048,0.0048,0.0048,0.005,0.0055,0.005083,0.004958,0.004886,0.004893,0.0048,0.0048,0.004893,0.004909,0.0049,0.004888,0.00489,0.004881,0.004884,0.004893,0.0048,0.004883,0.004973,0.004985,0.004923,0.0048,2.11,2.291667,2.0875,1.15,2.1925,2.2075,1.88125,1.1125,1.75,2.2,2.25,2.185,2.242857,2.303125,2.29375,2.2375,2.11,1.975,2.225,2.20625,2.185,2.1925,2.0375,2.245,2.335938,2.275,2.125,2.2625,2.1875,2.16875,2.2375]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M9] rank=9 service=emailservice metric=istio-latency-99 baseline=0.007199 peak=2.467188 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.0092,0.00935,0.00496,0.00496,0.00496,0.0084,0.0084,0.00496,0.00496,0.00496,0.00496,0.009,0.0091,0.009017,0.00875,0.00775,0.0079,0.00496,0.00496,0.0079,0.0082,0.00805,0.0078,0.00785,0.0076,0.0077,0.0079,0.00496,0.00765,0.00885,0.008925,0.0084,0.00496,2.422,2.458333,2.4175,2.23,2.4385,2.4415,2.37625,2.2225,2.35,2.44,2.45,2.437,2.448571,2.460625,2.45875,2.4475,2.422,2.395,2.445,2.44125,2.437,2.4385,2.4075,2.449,2.467188,2.455,2.425,2.4525,2.4375,2.43375,2.4475]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M10] rank=10 service=productcatalogservice metric=istio-latency-99 baseline=0.004952 peak=0.024086 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=30
values_compact=delta:0.004956,-0.000005,-0.000002,0.000004,0,-0.000005,-0.000001,0.00001,-0.000001,-0.000008,0.000002,0.000002,-0.000001,0,0.000002,-0.000005,-0.000001,0.000002,0.000004,0,-0.000002,0,0.000013,0.000004,-0.000013,-0.00001,0,0.000002,0.00001,0.000002,-0.000006,-0.000006,-0.000004,0.000033,0.000022,0.002602,-0.001389,0.007671,0.000751,0.00142,-0.007286,-0.003805,0.000009,0.001535,0.000164,-0.000264,0.005403,0.005822,-0.006419,-0.006214,-0.000012,0.000013,0.006366,-0.006379,-0.000004,0.000007,0,0.0008,0.000086,0.00107,0.008725,-0.010583,0.008674,0.003807
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M11] rank=11 service=shippingservice metric=istio-latency-99 baseline=0.004968 peak=0.0465 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=25
values_compact=delta:0.004958,0.000025,0.000001,-0.000026,-0.000001,-0.000001,0,0.000029,-0.000002,0,0.000001,-0.000028,0.000024,0.000011,-0.000022,0.000001,0,0.000001,-0.000001,-0.000015,0.000001,0,0.000013,0.000001,-0.000012,0.000012,-0.000001,-0.000012,0.000011,0.000002,-0.000012,0,0,0.012742,-0.00005,0.002075,-0.005025,-0.009742,0,0.000039,0.004153,-0.000302,0.014127,-0.014275,-0.00205,0.016625,-0.000037,-0.012413,0.00075,0.02355,0.006125,-0.033819,0.000486,0.003158,-0.002475,0.003423,0.007027,0.0004,0.02355,-0.025,-0.005863,-0.007168,-0.000011,0.000012
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M12] rank=12 service=adservice metric=container-memory-failures-total baseline=3.466236 peak=1454.685668 signed_z=859.483 onset_bin=47 onset_rel_s=1068.75 persistence_bins=2
values_compact=raw:[5.549759,5.852286,3.941828,2.976081,1.773744,0.556837,2.071758,4.956681,4.929972,4.836377,4.978716,7.574745,6.455885,3.687486,2.552609,3.073995,2.126363,4.465273,3.339614,2.613961,2.507332,3.765174,5.094365,2.913687,0.432664,2.672577,2.729024,3.314696,3.612998,2.351426,2.300721,0.474707,4.493556,5.283624,4.863813,2.633784,3.892634,5.544189,3.398027,4.302633,4.435683,2.604558,2.353829,2.298952,1.971059,3.501332,4.765687,994.671553,1013.017701,3.320662,4.418454,2.094361,1.738359,2.279441,4.963941,3.731085,0.557734,0.409314,5.284742,5.517871,4.473928,2.568012,1.872292,2.584105]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[698.0,1440.0]

=== LOG SUMMARY ===
{"entries":[{"change_pct":-33.3,"n_during":10,"n_pre":15,"service":"redis"},{"change_pct":12.5,"n_during":1056,"n_pre":939,"service":"checkoutservice"},{"change_pct":12.5,"n_during":352,"n_pre":313,"service":"emailservice"},{"change_pct":12.5,"n_during":704,"n_pre":626,"service":"paymentservice"},{"change_pct":9.4,"n_during":29954,"n_pre":27374,"service":"currencyservice"},{"change_pct":7.7,"n_during":33141,"n_pre":30761,"service":"frontend"},{"change_pct":6.6,"n_during":5568,"n_pre":5224,"service":"shippingservice"},{"change_pct":6.4,"n_during":9487,"n_pre":8916,"service":"cartservice"}],"mode":"volume","omitted_services":2,"service_count":10}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":13413.6,"error_pct":0.0,"p95_during_ms":66.89214999999997,"p95_pre_ms":0.495,"service":"emailservice","spans":1151},{"delta_pct":792.1,"error_pct":0.0,"p95_during_ms":628.7748999999995,"p95_pre_ms":70.48319999999994,"service":"checkoutservice","spans":9200},{"delta_pct":25.5,"error_pct":0.0,"p95_during_ms":0.5639,"p95_pre_ms":0.4495,"service":"paymentservice","spans":953},{"delta_pct":23.5,"error_pct":0.0,"p95_during_ms":64.452,"p95_pre_ms":52.18425,"service":"frontend","spans":207178},{"delta_pct":19.3,"error_pct":0.0,"p95_during_ms":5.604299999999996,"p95_pre_ms":4.699,"service":"recommendationservice","spans":27262},{"delta_pct":-0.9,"error_pct":0.0,"p95_during_ms":0.214,"p95_pre_ms":0.216,"service":"currencyservice","spans":57615},{"delta_pct":0.0,"error_pct":0.0,"p95_during_ms":0.029,"p95_pre_ms":0.029,"service":"productcatalogservice","spans":102689}],"omitted_services":0,"service_count":7}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=3 omitted_edges=1
[{"evidence_source":"trace","onset_rel_s":735.0,"rank":1,"service":"emailservice","severity_z":999.0},{"evidence_source":"trace","onset_rel_s":735.0,"rank":2,"service":"checkoutservice","severity_z":105.314},{"evidence_source":"trace","onset_rel_s":735.0,"rank":3,"service":"recommendationservice","severity_z":46.517},{"evidence_source":"metric","onset_rel_s":756.0,"rank":4,"service":"gke-gke-cluster-default-pool-2e1807ce-cx8g","severity_z":41.916},{"evidence_source":"metric","onset_rel_s":763.8,"rank":5,"service":"frontend","severity_z":20.781},{"evidence_source":"trace","onset_rel_s":765.0,"rank":6,"service":"paymentservice","severity_z":14.737},{"evidence_source":"metric","onset_rel_s":838.8,"rank":7,"service":"productcatalogservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":882.0,"rank":8,"service":"gke-gke-cluster-default-pool-2e1807ce-0e4z","severity_z":19.934},{"evidence_source":"metric","onset_rel_s":1024.8,"rank":9,"service":"cartservice","severity_z":11.719},{"evidence_source":"metric","onset_rel_s":1065.0,"rank":10,"service":"adservice","severity_z":859.483},{"evidence_source":"metric","onset_rel_s":1098.0,"rank":11,"service":"shippingservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1189.8,"rank":12,"service":"gke-gke-cluster-default-pool-2e1807ce-xte3","severity_z":40.475},{"evidence_source":"metric","onset_rel_s":1309.2,"rank":13,"service":"redis","severity_z":20.253},{"evidence_source":"metric","onset_rel_s":1360.2,"rank":14,"service":"currencyservice","severity_z":45.618}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"currencyservice","caller":"checkoutservice"},{"callee":"emailservice","caller":"checkoutservice"},{"callee":"paymentservice","caller":"checkoutservice"},{"callee":"productcatalogservice","caller":"checkoutservice"},{"callee":"checkoutservice","caller":"frontend"},{"callee":"currencyservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"frontend"},{"callee":"recommendationservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"recommendationservice"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"high","reason":"Rank emailservice first because emailservice has direct container-memory-failures-total evidence (signed-z 999, persistence 32 bins); although checkoutservice is salient, the caller path checkoutservice -> emailservice means a disturbance in the callee can propagate back toward that caller-side symptom.","services":["emailservice","checkoutservice"]}
