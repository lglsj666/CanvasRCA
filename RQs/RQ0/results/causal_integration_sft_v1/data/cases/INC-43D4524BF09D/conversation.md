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
opaque_id: INC-43D4524BF09D
observation_window={"duration_rel_s":1440.0,"source_metric_rows":1441}
selection_summary={"candidate_count":16,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":255,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","cartservice","checkoutservice","currencyservice","emailservice","frontend","frontend-external","gke-gke-cluster-default-pool-2e1807ce-0e4z","gke-gke-cluster-default-pool-2e1807ce-cx8g","gke-gke-cluster-default-pool-2e1807ce-w819","loadgenerator","paymentservice","productcatalogservice","recommendationservice","redis","shippingservice"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[11.25,33.75,56.25,78.75,101.25,123.75,146.25,168.75,191.25,213.75,236.25,258.75,281.25,303.75,326.25,348.75,371.25,393.75,416.25,438.75,461.25,483.75,506.25,528.75,551.25,573.75,596.25,618.75,641.25,663.75,686.25,708.75,731.25,753.75,776.25,798.75,821.25,843.75,866.25,888.75,911.25,933.75,956.25,978.75,1001.25,1023.75,1046.25,1068.75,1091.25,1113.75,1136.25,1158.75,1181.25,1203.75,1226.25,1248.75,1271.25,1293.75,1316.25,1338.75,1361.25,1383.75,1406.25,1428.75]
[M1] rank=1 service=emailservice metric=istio-latency-50 baseline=0.003023 peak=0.122059 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.003,0.003,0.003,0.003,0.003053,0.003045,0.003,0.003051,0.003043,0.003,0.003,0.003,0.003048,0.00308,0.003044,0.003,0.003,0.003041,0.003041,0.003,0.003,0.003,0.003057,0.003059,0.003057,0.00308,0.00304,0.003,0.003,0.003,0.003,0.003,0.003,0.004097,0.005,0.104167,0.004926,0.10375,0.005,0.004826,0.104167,0.0049,0.005,0.111842,0.004789,0.106522,0.105556,0.004733,0.00475,0.103125,0.105769,0.004757,0.004895,0.005,0.105769,0.004833,0.005,0.108654,0.103,0.102603,0.102206,0.004788,0.105769,0.005]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M2] rank=2 service=emailservice metric=istio-latency-90 baseline=0.004642 peak=0.224412 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=delta:0.0046,0,0,0,0.000095,-0.000013,-0.000082,0.000092,-0.000014,-0.000078,0,0,0.000086,0.000058,-0.000064,-0.00008,0,0.000073,0,-0.000073,0,0,0.000103,0.000003,-0.000003,0.000041,-0.000072,-0.000072,0,0,0,0,0,0.203047,0.012353,0.000833,-0.00141,0.001327,-0.00075,-0.001429,0.002262,-0.001622,0.000789,0.002368,-0.004133,0.003069,-0.000193,-0.003419,0.000165,0.002768,0.000529,-0.003225,0.001238,0.000833,0.001154,-0.002518,0.001364,0.001731,-0.001131,-0.000079,-0.00008,-0.00246,0.003173,-0.001154
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M3] rank=3 service=emailservice metric=istio-latency-95 baseline=0.004845 peak=0.237206 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=delta:0.0048,0,0,0,0.0001,-0.000014,-0.000086,0.000097,-0.000014,-0.000083,0,0,0.00009,0.000062,-0.000068,-0.000084,0,0.000078,0,-0.000078,0,0,0.000109,0.000003,-0.000003,0.000043,-0.000076,-0.000076,0,0,0,0,0,0.224024,0.006176,0.000417,-0.000705,0.000663,-0.000375,-0.000714,0.001131,-0.000812,0.000395,0.001184,-0.002066,0.001534,-0.000096,-0.00171,0.000083,0.001383,0.000265,-0.001613,0.000619,0.000417,0.000577,-0.001259,0.000682,0.000865,-0.000565,-0.00004,-0.000039,-0.001231,0.001587,-0.000577
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M4] rank=4 service=adservice metric=container-memory-failures-total baseline=4.586937 peak=1882.36697 signed_z=670.554 onset_bin=45 onset_rel_s=1023.75 persistence_bins=7
values_compact=raw:[2.537115,5.180783,3.420228,0.706747,5.039483,5.287191,4.78679,4.624419,0.575093,7.091585,13.350785,1.625267,5.655042,6.60594,5.677815,7.279595,6.699653,3.216708,6.074224,7.406091,2.734909,2.679808,3.686823,2.323707,5.864622,0.391194,4.263595,4.705691,0.461851,2.212992,5.25,4.465747,4.149477,4.405256,6.810785,1.877934,1.877934,5.466456,4.611689,8.047684,8.457689,6.080499,4.540342,3.882624,3.852822,529.346892,583.937901,21.102747,15.557568,5.90165,2.64995,2.719914,5.259726,67.440753,1338.729105,9.071203,6.739608,2.798243,20.572197,3.453258,3.324224,5.770766,4.415011,4.603561]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M5] rank=5 service=emailservice metric=container-memory-failures-total baseline=0.052128 peak=33.363219 signed_z=324.771 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=rle:0*4,0.128609*1,0.319554*1,0.23447*1,0*8,0.182688*1,0.238283*1,0*9,0.169575*1,0.232387*1,0.212078*1,0*4,33.062301*1,0.036683*1,0.044253*1,0.047749*1,0*1,0.189493*1,0.155159*1,0*9,0.315756*1,0.301233*1,0*8,0.116286*1,0.120741*1,0*3
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M6] rank=6 service=adservice metric=container-memory-rss baseline=108105307.022222 peak=123260928.0 signed_z=181.882 onset_bin=45 onset_rel_s=1023.75 persistence_bins=17
values_compact=delta:107986944,0,4096,0,4096,12288,0,0,0,12288,94208,73728,0,-90112,4096,4096,12288,0,184320,4096,-90112,-77824,0,-12288,8192,0,-12288,0,0,12288,-12288,12288,8192,0,-8192,90112,0,0,0,20480,0,-4096,-90112,4096,0,15106048,-14897152,4096,-4096,102400,0,-196608,0,4644864,-4255744,0,12288,0,-94208,0,98304,-8192,0,0
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M7] rank=7 service=emailservice metric=istio-latency-99 baseline=0.00631 peak=0.247441 signed_z=162.055 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=delta:0.00496,0,0,0,0.00309,-0.0003,-0.00279,0.00304,-0.00035,-0.00269,0,0,0.00289,0.00085,-0.001,-0.00274,0,0.00254,0,-0.00254,0,0,0.00324,0.00005,-0.00005,0.0005,-0.00125,-0.00249,0,0,0,0,0,0.240805,0.001235,0.000083,-0.000141,0.000133,-0.000075,-0.000143,0.000226,-0.000162,0.000079,0.000237,-0.000413,0.000306,-0.000019,-0.000342,0.000017,0.000276,0.000053,-0.000322,0.000124,0.000083,0.000115,-0.000251,0.000136,0.000173,-0.000113,-0.000008,-0.000008,-0.000246,0.000317,-0.000115
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M8] rank=8 service=adservice metric=container-memory-working-set-bytes baseline=109447714.133333 peak=124669952.0 signed_z=153.37 onset_bin=49 onset_rel_s=1113.75 persistence_bins=13
values_compact=delta:109314048,-4096,8192,0,4096,16384,-8192,4096,0,12288,118784,73728,0,-106496,0,4096,12288,0,229376,0,-106496,-102400,-4096,-4096,4096,135168,-151552,4096,0,12288,-12288,16384,0,0,-4096,114688,0,-8192,8192,16384,0,-4096,-106496,0,4096,15179776,-14954496,4096,4096,118784,8192,-241664,-8192,4689920,-4272128,0,12288,4096,-114688,-2048,120832,-12288,4096,0
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M9] rank=9 service=adservice metric=container-memory-usage-bytes baseline=109752877.511111 peak=124989440.0 signed_z=150.045 onset_bin=49 onset_rel_s=1113.75 persistence_bins=13
values_compact=delta:109613056,-4096,8192,0,4096,20480,-8192,4096,0,12288,118784,73728,0,-106496,0,4096,12288,4096,229376,0,-106496,-102400,-4096,-4096,4096,139264,-151552,4096,0,12288,-12288,16384,0,0,-4096,118784,0,-8192,8192,16384,0,-4096,-106496,0,8192,15179776,-14954496,4096,4096,118784,8192,-241664,-8192,4689920,-4268032,0,12288,4096,-114688,-2048,120832,-12288,4096,0
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M10] rank=10 service=adservice metric=istio-latency-99 baseline=0.00551 peak=0.077143 signed_z=72.671 onset_bin=46 onset_rel_s=1046.25 persistence_bins=5
values_compact=delta:0.007804,-0.000042,-0.002785,0.000008,0,0.000004,-0.000001,0.002142,-0.000743,-0.00141,0.00013,0.001035,-0.001158,-0.000018,0,0.000006,0,0.002282,0.000227,-0.002491,-0.000006,0.000014,-0.000002,-0.000036,0.000011,0.000322,-0.000296,-0.000025,0,0.000019,0.000001,-0.000014,-0.000006,0,0.000005,0.000008,-0.000006,0.000011,0,-0.000007,0.000012,-0.000024,0,0.000006,-0.000011,0.002761,0.001585,-0.000651,-0.003684,-0.000012,0.000001,0.000006,0.000019,0.065054,0.005884,-0.060679,-0.010271,0.000005,0.000058,-0.000047,-0.000012,0,-0.000005,-0.000012
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M11] rank=11 service=paymentservice metric=container-network-receive-bytes-total baseline=775.56661 peak=7396.368989 signed_z=60.698 onset_bin=36 onset_rel_s=821.25 persistence_bins=2
values_compact=delta:882.978094,1.551157,-214.263327,24.4768,19.590026,93.673375,76.959324,-120.956317,56.240482,94.496373,-13.239296,-215.210387,120.607876,76.847236,-117.745778,54.655723,33.563485,-20.146124,-141.622263,99.770645,-124.904818,138.387343,23.564023,-119.829861,-62.126205,178.040229,-38.310333,102.691831,-61.449586,-144.631653,28.768973,147.937636,-85.660594,90.685291,151.358155,-357.482855,4076.37256,397.37868,-4347.285276,17.750981,-151.443559,49.401216,43.499029,16.937883,-121.227267,170.452145,32.381797,44.55571,-58.193961,-38.20469,6.782622,-148.923446,-161.757961,405.269096,-145.818548,125.328387,-48.192788,-44.182158,40.429315,233.362454,29.900425,-490.299555,78.771476,231.495224
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M12] rank=12 service=adservice metric=container-cpu-user-seconds-total baseline=0.494651 peak=4.072485 signed_z=53.235 onset_bin=45 onset_rel_s=1023.75 persistence_bins=3
values_compact=raw:[0.56027,0.560073,0.495619,0.441955,0.468917,0.51512,0.520563,0.497125,0.491118,0.618502,0.578724,0.499382,0.499356,0.544944,0.50074,0.508539,0.502056,0.515946,0.508467,0.57459,0.509557,0.517398,0.508428,0.537594,0.550699,0.363715,0.510003,0.522395,0.45848,0.462277,0.492802,0.484712,0.48298,0.46313,0.549531,0.485932,0.532532,0.477319,0.571376,0.61698,0.52886,0.49764,0.526547,0.54805,0.492575,1.274989,1.401415,0.539371,0.498186,0.482763,0.551228,0.591601,0.523336,0.658472,3.023703,0.457617,0.515717,0.433485,0.568011,0.552091,0.533562,0.564514,0.47993,0.539184]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[712.0,1440.0]

=== LOG SUMMARY ===
{"entries":[{"change_pct":-33.3,"n_during":10,"n_pre":15,"service":"redis"},{"change_pct":5.3,"n_during":1074,"n_pre":1020,"service":"checkoutservice"},{"change_pct":5.3,"n_during":358,"n_pre":340,"service":"emailservice"},{"change_pct":5.3,"n_during":716,"n_pre":680,"service":"paymentservice"},{"change_pct":4.6,"n_during":5618,"n_pre":5372,"service":"shippingservice"},{"change_pct":4.2,"n_during":29075,"n_pre":27916,"service":"currencyservice"},{"change_pct":4.1,"n_during":32642,"n_pre":31354,"service":"frontend"},{"change_pct":3.8,"n_during":9423,"n_pre":9074,"service":"cartservice"}],"mode":"volume","omitted_services":2,"service_count":10}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":249.6,"error_pct":0.0,"p95_during_ms":268.8234999999999,"p95_pre_ms":76.8902,"service":"checkoutservice","spans":9548},{"delta_pct":-7.9,"error_pct":0.0,"p95_during_ms":0.41889999999999983,"p95_pre_ms":0.45475,"service":"emailservice","spans":1274},{"delta_pct":4.7,"error_pct":0.0,"p95_during_ms":66.54639999999996,"p95_pre_ms":63.579499999999996,"service":"frontend","spans":207464},{"delta_pct":4.1,"error_pct":0.0,"p95_during_ms":5.396,"p95_pre_ms":5.18195,"service":"recommendationservice","spans":27498},{"delta_pct":3.9,"error_pct":0.0,"p95_during_ms":0.40395000000000003,"p95_pre_ms":0.3886499999999997,"service":"paymentservice","spans":986},{"delta_pct":1.7,"error_pct":0.0,"p95_during_ms":0.241,"p95_pre_ms":0.237,"service":"currencyservice","spans":57277},{"delta_pct":0.0,"error_pct":0.0,"p95_during_ms":0.028,"p95_pre_ms":0.028,"service":"productcatalogservice","spans":103259}],"omitted_services":0,"service_count":7}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=2 omitted_edges=0
[{"evidence_source":"trace","onset_rel_s":735.0,"rank":1,"service":"checkoutservice","severity_z":26.412},{"evidence_source":"metric","onset_rel_s":766.2,"rank":2,"service":"emailservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":802.8,"rank":3,"service":"frontend","severity_z":23.016},{"evidence_source":"metric","onset_rel_s":817.2,"rank":4,"service":"paymentservice","severity_z":60.698},{"evidence_source":"metric","onset_rel_s":1086.0,"rank":5,"service":"gke-gke-cluster-default-pool-2e1807ce-w819","severity_z":12.952},{"evidence_source":"metric","onset_rel_s":1204.8,"rank":6,"service":"adservice","severity_z":670.554},{"evidence_source":"metric","onset_rel_s":1338.0,"rank":7,"service":"recommendationservice","severity_z":12.732},{"evidence_source":"none","onset_rel_s":null,"rank":8,"service":"cartservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":9,"service":"productcatalogservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":10,"service":"gke-gke-cluster-default-pool-2e1807ce-cx8g","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":11,"service":"redis","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":12,"service":"gke-gke-cluster-default-pool-2e1807ce-0e4z","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":13,"service":"loadgenerator","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":14,"service":"shippingservice","severity_z":0.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"emailservice","caller":"checkoutservice"},{"callee":"paymentservice","caller":"checkoutservice"},{"callee":"productcatalogservice","caller":"checkoutservice"},{"callee":"checkoutservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"frontend"},{"callee":"recommendationservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"recommendationservice"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"high","reason":"Rank emailservice first because emailservice has direct istio-latency-50 evidence (signed-z 999, persistence 31 bins); although checkoutservice is salient, the caller path checkoutservice -> emailservice means a disturbance in the callee can propagate back toward that caller-side symptom.","services":["emailservice","checkoutservice"]}
