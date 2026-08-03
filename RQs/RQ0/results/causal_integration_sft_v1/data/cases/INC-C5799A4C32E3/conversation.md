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
opaque_id: INC-C5799A4C32E3
observation_window={"duration_rel_s":1440.0,"source_metric_rows":1441}
selection_summary={"candidate_count":17,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":268,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","cartservice","checkoutservice","currencyservice","emailservice","frontend","frontend-external","gke-gke-cluster-default-pool-2e1807ce-0e4z","gke-gke-cluster-default-pool-2e1807ce-cx8g","gke-gke-cluster-default-pool-2e1807ce-w819","gke-gke-cluster-default-pool-2e1807ce-xte3","loadgenerator","paymentservice","productcatalogservice","recommendationservice","redis","shippingservice"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[11.25,33.75,56.25,78.75,101.25,123.75,146.25,168.75,191.25,213.75,236.25,258.75,281.25,303.75,326.25,348.75,371.25,393.75,416.25,438.75,461.25,483.75,506.25,528.75,551.25,573.75,596.25,618.75,641.25,663.75,686.25,708.75,731.25,753.75,776.25,798.75,821.25,843.75,866.25,888.75,911.25,933.75,956.25,978.75,1001.25,1023.75,1046.25,1068.75,1091.25,1113.75,1136.25,1158.75,1181.25,1203.75,1226.25,1248.75,1271.25,1293.75,1316.25,1338.75,1361.25,1383.75,1406.25,1428.75]
[M1] rank=1 service=checkoutservice metric=container-memory-mapped-file baseline=0.0 peak=2211840.0 signed_z=999.0 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=rle:0*32,2211840*32
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M2] rank=2 service=gke-gke-cluster-default-pool-2e1807ce-w819 metric=node-memory-active-bytes baseline=2295.656296 peak=11219035.022222 signed_z=999.0 onset_bin=56 onset_rel_s=1271.25 persistence_bins=2
values_compact=delta:2457.6,364.088889,182.044444,-1092.266666,-182.044445,546.133334,273.066666,273.066667,2639.644444,-819.2,-3094.755555,182.044444,0,637.155556,91.022222,-546.133333,-91.022223,-91.022222,91.022222,182.044445,-273.066667,364.088889,637.155556,-455.111111,-182.044445,-546.133333,-546.133334,546.133334,273.066666,728.177778,455.111111,-546.133333,273.066667,819.2,-273.066667,0,0,-91.022222,91.022222,-273.066667,-182.044444,546.133333,455.111111,-728.177777,-364.088889,273.066666,0,273.066667,0,-364.088889,-364.088889,728.177778,637.155556,-182.044445,-91.022222,364.088889,11215030.044444,-819.2,-11214939.022222,182.044444,-455.111111,-364.088889,-364.088888,91.022222
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M3] rank=3 service=gke-gke-cluster-default-pool-2e1807ce-w819 metric=node-disk-written-bytes-total baseline=993374.309136 peak=59601078.044444 signed_z=999.0 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=delta:949816.888889,43781.688889,-29764.266667,9375.288889,36135.822222,-2821.688889,-25850.311111,15564.8,43053.511111,-22027.377777,-44782.933334,14836.622222,56433.777778,-11377.777778,-76549.688888,-2457.6,68175.644444,-18659.555556,-48332.8,19114.666667,55705.6,-5006.222222,-29946.311111,-39867.733334,33405.155556,37865.244444,-42325.333333,-26123.377778,34679.466667,-25395.2,49243.022222,39776.711111,723444.622223,40381462.755555,13537006.933333,-273794.844444,1213872.355556,-7588704.711112,6670563.555556,-2637368.888889,-2489275.733333,7177648.355555,-4774479.644444,4329654.044444,210807.466667,-6234294.044444,4628935.111111,-4597714.488889,1691374.933333,4748083.2,-6018116.266667,6214906.311112,333505.422222,-5897329.777778,4935588.977778,-2468522.666667,-2776268.8,7504418.133333,-2697352.533333,-994508.8,2432022.755556,-8208292.977778,5145941.333333,2289846.044445
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M4] rank=4 service=checkoutservice metric=container-memory-usage-bytes baseline=10465365.333333 peak=134213632.0 signed_z=655.856 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=delta:10190848,4096,8192,53248,49152,-77824,40960,0,110592,151552,49152,147456,-557056,241664,94208,0,253952,-172032,-241664,8192,36864,98304,192512,-106496,73728,-155648,40960,4096,0,28672,135168,94208,123396096,-221184,221184,-32768,-40960,-90112,126976,-157696,190464,-14336,-22528,-12288,-45056,0,-94208,-20480,135168,-77824,139264,0,-4096,28672,-266240,278528,-28672,0,-77824,32768,-94208,133120,-34816,20480
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M5] rank=5 service=checkoutservice metric=container-memory-cache baseline=4096.0 peak=120008704.0 signed_z=578.096 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=delta:4096,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,117997568,81920,-704512,-20480,1437696,356352,458752,-2158592,2281472,-1269760,-86016,1310720,-2404352,0,1490944,741376,98304,-823296,-1744896,0,2424832,466944,-1765376,753664,0,565248,-1925120,585728,-299008,141312,-43008,1105920
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M6] rank=6 service=checkoutservice metric=container-cpu-system-seconds-total baseline=0.153693 peak=13.424444 signed_z=390.259 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=delta:0.140025,0.023624,-0.032391,0.000499,0.031203,0.019622,0.031575,-0.028543,0.015663,-0.098825,0.018406,0.031632,0.014142,0.0175,-0.025004,-0.038877,0.029354,-0.020807,0.060529,0.006713,-0.038,-0.038989,0.024691,-0.017644,-0.007711,0.041113,-0.003244,-0.03363,0.015655,0.043108,-0.002648,-0.023265,1.918848,4.112224,6.512496,0.068053,0.108367,-0.229516,-0.235375,0.703688,0.127064,-0.269174,0.072538,0.147815,-0.575899,-2.554912,3.173858,-0.514252,-0.062536,0.486196,-0.186332,-0.121758,0.284417,-0.190971,-0.103002,0.312236,-0.218078,-0.141056,-0.026836,0.418579,-1.536305,1.598883,-0.415978,0.563029
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M7] rank=7 service=gke-gke-cluster-default-pool-2e1807ce-w819 metric=node-disk-writes-completed-total baseline=80.546636 peak=364.066667 signed_z=283.761 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=delta:79.155556,0.8,0.666666,-0.422222,-0.511111,0.644444,0.644445,0.066666,0.355556,0.311111,0.888889,0.8,-0.844444,-1.555556,-1.444444,0.266666,1.488889,-1.622222,-0.022222,0.733333,-0.555556,0.622223,-0.311111,-0.911112,0.488889,0.511111,-0.266666,0.111111,0.466667,-0.355556,0.6,0.133333,2.311111,186.977778,64.6,1.355556,6.066666,-28.888888,33.955555,-11.511111,-11.222222,31.133333,-23.044444,23.244444,-1.022222,-26.688889,24.133333,-26.311111,9.288889,23.844445,-27.888889,24.733333,-1.444444,-22.577778,24.088889,-13.288889,-11.288889,32.577778,-13.288889,2,11.022222,-44.2,22.444444,11.444445
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M8] rank=8 service=checkoutservice metric=container-cpu-usage-seconds-total baseline=0.409057 peak=19.846161 signed_z=257.827 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=delta:0.384241,0.045172,-0.042313,0.025963,0.00798,-0.003778,0.073726,-0.050879,0.034706,-0.20014,0.040011,0.109803,0.069068,0.040216,-0.106019,-0.098127,0.013009,0.030396,0.058329,0.072775,-0.064281,-0.103918,0.024853,-0.010021,-0.01359,0.091486,0.01338,-0.0246,-0.030425,0.060004,0.055931,-0.069685,3.356921,5.939422,9.380641,0.170819,-0.128658,0.157825,0.080209,-0.097648,0.054345,0.016577,0.001131,-0.131322,0.266969,-3.532373,3.30389,0.106133,0.089369,0.014802,0.002519,-0.072039,0,0.131042,-0.035937,-0.145885,0.133348,0.27916,-0.069721,-0.193318,-2.536759,2.700808,-0.020057,-0.03673
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M9] rank=9 service=emailservice metric=istio-latency-95 baseline=0.004806 peak=0.00825 signed_z=150.392 onset_bin=3 onset_rel_s=78.75 persistence_bins=22
values_compact=rle:0.0048*3,0.004893*2,0.0048*28,0.004895*1,0.004886*1,0.0048*5,0.004995*1,0.007*1,0.00575*1,0.004983*1,0.004949*1,0.006*1,0.0055*1,0.0048*3,0.0055*1,0.007*1,0.00725*1,0.008042*1,0.007187*1,0.0048*2,0.004895*1,0.004981*1,0.007083*1,0.007687*1,0.006875*1,0.004888*1,0.0048*1
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M10] rank=10 service=checkoutservice metric=container-cpu-user-seconds-total baseline=0.255364 peak=7.257218 signed_z=142.769 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=raw:[0.244216,0.265764,0.255844,0.281304,0.258081,0.226544,0.276834,0.255274,0.273541,0.172229,0.193831,0.272002,0.326928,0.349645,0.26863,0.200978,0.183887,0.22392,0.279129,0.308098,0.288683,0.218096,0.217051,0.228058,0.226769,0.265926,0.285794,0.29482,0.248742,0.26564,0.321173,0.271217,1.71587,3.543071,6.411215,6.513976,5.993484,6.664295,6.82154,6.094501,6.105821,6.388823,6.320168,5.957508,6.883901,5.906438,6.03647,6.656855,6.733543,6.337366,6.526215,6.291522,6.291522,6.61353,6.571648,6.087856,6.232099,7.001082,6.951233,6.206347,5.338885,6.440805,6.286552,6.23697]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M11] rank=11 service=adservice metric=istio-latency-99 baseline=0.004966 peak=0.006088 signed_z=117.32 onset_bin=34 onset_rel_s=776.25 persistence_bins=2
values_compact=delta:0.004985,-0.000001,-0.000025,0,0,0.000001,0.000032,-0.000001,-0.00002,0.000001,-0.000013,0,0,0,0,0,0.000013,0,-0.000013,0,0,0,0,0.000006,0.000007,-0.000006,-0.000007,0,0.000007,0.000005,-0.000006,-0.000006,0,0,0.000935,0.000194,-0.001129,0,0,0,0.000013,-0.000001,-0.000012,0.000007,0.000006,0.000001,-0.000007,-0.000007,0.000006,0,0,0.000001,-0.000006,-0.000001,0.000012,0.000001,0.000012,0,-0.000025,0,0.000018,0.000001,-0.000012,0.000012
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M12] rank=12 service=emailservice metric=istio-latency-90 baseline=0.004606 peak=0.0065 signed_z=87.318 onset_bin=3 onset_rel_s=78.75 persistence_bins=22
values_compact=rle:0.0046*3,0.004688*2,0.0046*28,0.00469*1,0.004682*1,0.0046*5,0.004785*1,0.004927*1,0.004825*1,0.004774*1,0.004741*1,0.00484*1,0.004812*1,0.0046*3,0.004812*1,0.004927*1,0.00496*1,0.006083*1,0.004951*1,0.0046*2,0.00469*1,0.004771*1,0.004938*1,0.005375*1,0.004913*1,0.004684*1,0.0046*1
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[706.0,1440.0]

=== LOG SUMMARY ===
{"entries":[{"change_pct":50.0,"n_during":15,"n_pre":10,"service":"redis"},{"change_pct":6.6,"n_during":28127,"n_pre":26391,"service":"currencyservice"},{"change_pct":5.7,"n_during":31482,"n_pre":29790,"service":"frontend"},{"change_pct":5.4,"n_during":9116,"n_pre":8647,"service":"cartservice"},{"change_pct":5.4,"n_during":5346,"n_pre":5072,"service":"shippingservice"},{"change_pct":4.9,"n_during":5284,"n_pre":5038,"service":"adservice"},{"change_pct":4.9,"n_during":6630,"n_pre":6322,"service":"recommendationservice"},{"change_pct":0.3,"n_during":978,"n_pre":975,"service":"checkoutservice"}],"mode":"volume","omitted_services":2,"service_count":10}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":51.5,"error_pct":0.0,"p95_during_ms":0.5993999999999996,"p95_pre_ms":0.3956000000000002,"service":"emailservice","spans":1227},{"delta_pct":42.9,"error_pct":0.0,"p95_during_ms":300.603,"p95_pre_ms":210.33379999999997,"service":"checkoutservice","spans":8924},{"delta_pct":-25.4,"error_pct":0.0,"p95_during_ms":0.30445,"p95_pre_ms":0.4078999999999998,"service":"paymentservice","spans":939},{"delta_pct":5.6,"error_pct":0.0,"p95_during_ms":5.110699999999997,"p95_pre_ms":4.8415,"service":"recommendationservice","spans":26480},{"delta_pct":-0.5,"error_pct":0.0,"p95_during_ms":0.182,"p95_pre_ms":0.183,"service":"currencyservice","spans":54794},{"delta_pct":0.5,"error_pct":0.0,"p95_during_ms":193.85569999999998,"p95_pre_ms":192.98654999999997,"service":"frontend","spans":199330},{"delta_pct":0.0,"error_pct":0.0,"p95_during_ms":0.023,"p95_pre_ms":0.023,"service":"productcatalogservice","spans":99359}],"omitted_services":0,"service_count":7}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=3 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":730.2,"rank":1,"service":"checkoutservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":772.2,"rank":2,"service":"adservice","severity_z":117.32},{"evidence_source":"metric","onset_rel_s":937.8,"rank":3,"service":"currencyservice","severity_z":29.553},{"evidence_source":"metric","onset_rel_s":1147.2,"rank":4,"service":"recommendationservice","severity_z":25.392},{"evidence_source":"metric","onset_rel_s":1261.8,"rank":5,"service":"gke-gke-cluster-default-pool-2e1807ce-w819","severity_z":999.0},{"evidence_source":"trace","onset_rel_s":1335.0,"rank":6,"service":"emailservice","severity_z":7.728},{"evidence_source":"metric","onset_rel_s":1390.8,"rank":7,"service":"shippingservice","severity_z":21.519},{"evidence_source":"none","onset_rel_s":null,"rank":8,"service":"gke-gke-cluster-default-pool-2e1807ce-cx8g","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":9,"service":"frontend","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":10,"service":"productcatalogservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":11,"service":"gke-gke-cluster-default-pool-2e1807ce-xte3","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":12,"service":"gke-gke-cluster-default-pool-2e1807ce-0e4z","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":13,"service":"redis","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":14,"service":"cartservice","severity_z":0.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"currencyservice","caller":"checkoutservice"},{"callee":"emailservice","caller":"checkoutservice"},{"callee":"productcatalogservice","caller":"checkoutservice"},{"callee":"checkoutservice","caller":"frontend"},{"callee":"currencyservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"frontend"},{"callee":"recommendationservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"recommendationservice"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"high","reason":"Rank checkoutservice first because checkoutservice has direct container-memory-mapped-file evidence (signed-z 999, persistence 32 bins); although frontend is salient, the caller path frontend -> checkoutservice means a disturbance in the callee can propagate back toward that caller-side symptom.","services":["checkoutservice","frontend"]}
