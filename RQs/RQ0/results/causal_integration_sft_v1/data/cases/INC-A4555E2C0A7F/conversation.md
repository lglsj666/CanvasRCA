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
opaque_id: INC-A4555E2C0A7F
observation_window={"duration_rel_s":1003.0,"source_metric_rows":1004}
selection_summary={"candidate_count":17,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":266,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","cartservice","checkoutservice","currencyservice","emailservice","frontend","frontend-external","gke-gke-cluster-default-pool-2e1807ce-0e4z","gke-gke-cluster-default-pool-2e1807ce-cx8g","gke-gke-cluster-default-pool-2e1807ce-w819","gke-gke-cluster-default-pool-2e1807ce-xte3","loadgenerator","paymentservice","productcatalogservice","recommendationservice","redis","shippingservice"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[7.836,23.508,39.18,54.852,70.523,86.195,101.867,117.539,133.211,148.883,164.555,180.227,195.898,211.57,227.242,242.914,258.586,274.258,289.93,305.602,321.273,336.945,352.617,368.289,383.961,399.633,415.305,430.977,446.648,462.32,477.992,493.664,509.336,525.008,540.68,556.352,572.023,587.695,603.367,619.039,634.711,650.383,666.055,681.727,697.398,713.07,728.742,744.414,760.086,775.758,791.43,807.102,822.773,838.445,854.117,869.789,885.461,901.133,916.805,932.477,948.148,963.82,979.492,995.164]
[M1] rank=1 service=checkoutservice metric=container-memory-failures-total baseline=2.614555 peak=41482.058472 signed_z=999.0 onset_bin=46 onset_rel_s=728.742 persistence_bins=18
values_compact=delta:2.52505,-1.72178,1.732656,-0.651419,1.194384,1.723191,-0.544284,0.824273,0.226845,1.631286,-2.135927,-2.818807,0.352951,1.329148,-1.047314,-1.226687,-1.258349,-0.135217,0,0.094357,0.001829,0.08493,3.822365,-0.07217,0.239217,-1.394386,0.081603,-1.200325,-1.157118,0.204034,2.923077,2.859124,0.271103,-3.295267,-0.3943,0.093679,1.737528,0.078793,-1.985771,-0.81586,-1.694031,0.086808,1.042698,0.258724,0,-0.79327,4849.996347,9957.388692,9744.353436,14564.765903,1150.807711,1213.669012,-2681.258396,-634.176839,1392.572974,1097.817946,-194.97882,-975.594696,0,1115.619901,-16353.499843,-16398.54484,-7698.132526,0
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:16,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,11
[M2] rank=2 service=checkoutservice metric=container-memory-rss baseline=11674375.139442 peak=264949760.0 signed_z=999.0 onset_bin=46 onset_rel_s=728.742 persistence_bins=18
values_compact=delta:11452416,12288,151552,8192,106496,-303104,4096,180224,262144,-364544,0,180224,65536,110592,12288,0,0,0,0,8192,-385024,12288,270336,24576,147456,-512000,4096,45056,0,28672,315392,225280,-565248,20480,180224,-442368,208896,221184,4096,0,28672,20480,98304,49152,-417792,20480,253370368,90112,-230789120,118054912,112734208,0,-246423552,123211776,123211776,-131129344,-6760448,16574464,121315328,-33538048,2232320,5369856,0,0
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:16,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,16
[M3] rank=3 service=checkoutservice metric=container-memory-usage-bytes baseline=14270692.462151 peak=268439552.0 signed_z=999.0 onset_bin=46 onset_rel_s=728.742 persistence_bins=18
values_compact=delta:14049280,8192,151552,8192,110592,-307200,8192,176128,262144,-364544,0,184320,65536,110592,16384,-4096,4096,-4096,0,8192,-385024,12288,270336,24576,147456,-512000,8192,45056,-4096,28672,315392,225280,-565248,24576,176128,-442368,208896,221184,4096,0,28672,20480,102400,45056,-413696,16384,254259200,90112,-231202816,118272000,112930816,0,-246857728,123428864,123428864,-131268608,-6887424,16607232,121552896,-33587200,2793472,5533696,0,0
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:16,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,16
[M4] rank=4 service=checkoutservice metric=container-memory-working-set-bytes baseline=13197540.462151 peak=268439552.0 signed_z=999.0 onset_bin=46 onset_rel_s=728.742 persistence_bins=18
values_compact=delta:12976128,8192,151552,8192,110592,-307200,8192,176128,262144,-364544,0,184320,65536,110592,16384,-4096,4096,-4096,0,8192,-385024,12288,270336,24576,147456,-512000,8192,45056,-4096,28672,315392,225280,-565248,24576,176128,-442368,208896,221184,4096,0,28672,20480,102400,45056,-413696,16384,255332352,90112,-231202816,118272000,112930816,0,-246857728,123428864,123428864,-131268608,-6887424,16607232,121552896,-33587200,2793472,5308416,0,0
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:16,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,16
[M5] rank=5 service=gke-gke-cluster-default-pool-2e1807ce-w819 metric=node-memory-active-bytes baseline=1382.558654 peak=22034841.6 signed_z=999.0 onset_bin=57 onset_rel_s=901.133 persistence_bins=3
values_compact=delta:1274.311111,182.044445,91.022222,-91.022222,0,-91.022223,182.044445,0,-455.111111,0,-273.066667,455.111111,910.222222,91.022223,-1001.244445,-546.133333,-91.022222,1001.244444,-182.044444,182.044444,91.022222,-273.066666,364.088888,-910.222222,455.111111,-182.044444,182.044444,-273.066666,182.044444,91.022222,364.088889,-364.088889,-364.088889,-273.066666,455.111111,364.088889,91.022222,-182.044444,273.066666,0,-364.088889,-273.066666,273.066666,273.066667,182.044444,-182.044444,-182.044444,91.022222,637.155555,-182.044444,-182.044445,-546.133333,455.111111,0,-364.088889,-364.088889,0,22033021.155556,364.088889,-11015964.444445,-11016783.644444,-364.088889,182.044445,-111.857209
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:16,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,16
[M6] rank=6 service=checkoutservice metric=container-memory-mapped-file baseline=126976.0 peak=2277376.0 signed_z=944.245 onset_bin=46 onset_rel_s=728.742 persistence_bins=18
values_compact=rle:126976*46,2211840*15,2277376*3
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:16,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,16
[M7] rank=7 service=shippingservice metric=istio-latency-99 baseline=0.004969 peak=0.0163 signed_z=941.794 onset_bin=57 onset_rel_s=901.133 persistence_bins=3
values_compact=delta:0.00497,-0.000012,-0.000001,0.000024,-0.000002,0.000001,-0.000023,0,0.000015,-0.000001,0.000013,-0.000014,0,-0.000012,0.000041,0,-0.000005,-0.000036,0,0.000013,0,0.000013,-0.000014,0,-0.000012,0,0.000001,0,0,0,0,-0.000001,0,0.000001,0,0,0,-0.000001,0,0,0.000036,-0.000001,0,-0.000034,0.000012,0.000013,0.000001,-0.000014,-0.000012,0.000013,0.000013,0.001002,-0.000993,-0.000014,-0.00001,0.000013,0.000005,0.004812,0.0047,-0.002475,-0.007055,0,-0.000012,0
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:16,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,16
[M8] rank=8 service=gke-gke-cluster-default-pool-2e1807ce-w819 metric=node-cpu-seconds-total baseline=395.61815 peak=176.256246 signed_z=-630.369 onset_bin=62 onset_rel_s=979.492 persistence_bins=2
values_compact=delta:394.4,0.355556,0.755555,0.422222,-0.177777,0.066666,-0.222222,-0.022222,0.044444,-0.266666,0.222222,0.022222,0.177778,-0.088889,0.2,0.022222,0.044445,-0.288889,0.044444,-0.111111,0.222222,0.155556,-0.044445,0.066667,-0.266667,0.022223,-0.444445,0.288889,-0.288889,0.311111,-0.111111,0.044445,0.022222,-0.111111,0.244444,-0.222222,0.066667,0.066666,0.244445,-0.133334,0.155556,-0.244445,0.2,-0.444444,0.311111,-0.311111,0.088889,-0.333333,0.222222,0.133333,0.2,-0.244444,-0.133334,0.044445,0.022222,0.111111,-0.2,0.133333,0.133334,0.033333,0.477778,0.088889,-64.418212,-106.061654
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:16,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,16
[M9] rank=9 service=gke-gke-cluster-default-pool-2e1807ce-0e4z metric=node-cpu-seconds-total baseline=396.070872 peak=254.646181 signed_z=-591.02 onset_bin=47 onset_rel_s=744.414 persistence_bins=17
values_compact=delta:395.488889,0.511111,0.133333,0,-0.288889,0.355556,-0.066667,0.111111,-0.6,0.311112,0.066666,0.066667,0.355555,-0.155555,-0.155556,-0.044444,0.044444,0.177778,-0.311111,-0.044444,0.133333,0.4,-0.2,0.044444,-0.222222,0.111111,-0.288889,-0.355555,0.222222,-0.111111,0.622222,-0.133333,-0.144445,-0.233333,-0.044444,0.044444,0.177778,0.333333,-0.155555,-0.066667,0.044444,0.133334,-0.044445,-0.111111,-0.155555,0.133333,-0.177778,-3.133333,-4.488889,-4.2,-0.955556,-0.133333,0.422222,0.288889,0.266667,-0.588889,-0.233333,-0.355556,0.977778,-0.2,2.2,3.044444,4.6,-89.296875
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:16,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,16
[M10] rank=10 service=checkoutservice metric=container-sockets baseline=9.0 peak=21.0 signed_z=571.429 onset_bin=46 onset_rel_s=728.742 persistence_bins=18
values_compact=rle:9*46,12*15,21*3
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:16,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,16
[M11] rank=11 service=gke-gke-cluster-default-pool-2e1807ce-xte3 metric=node-cpu-seconds-total baseline=394.701549 peak=209.767872 signed_z=-546.684 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:394.066667,0.2,-0.022223,0.511112,0.488888,0.155556,-0.333333,-0.155556,-0.111111,-0.155556,0,-0.133333,0.044445,-0.4,0.444444,0.155556,0.466666,-0.377778,-0.066666,-0.377778,0.511111,-0.111111,0.188889,-0.033333,-0.177778,-0.088889,-0.266667,0.044445,-0.133334,-0.066666,0.444444,0.555556,0.022222,-0.422222,-0.422223,0.311112,0,0.222222,-0.2,-0.066667,-0.355555,0.111111,0.155555,0.533334,-0.488889,-0.444445,-0.155555,0.177777,-0.355555,0.2,0.066667,0,-0.111112,-0.111111,0.133334,0.244444,0.111111,0.111111,-0.333333,-0.222222,0.088889,0.222222,0.222222,-135.554736
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:16,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,16
[M12] rank=12 service=gke-gke-cluster-default-pool-2e1807ce-cx8g metric=node-cpu-seconds-total baseline=395.175299 peak=217.633827 signed_z=-499.908 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:393.688889,1,0.488889,0.111111,-0.244445,0.488889,-0.288889,-0.066666,-0.022222,-0.022223,0.066667,-0.333333,0.177777,0.155556,0.155556,0.088888,-0.088888,0.133333,-0.355556,0.111111,0.133334,0.311111,0.022222,-0.3,-0.188889,-0.133333,-0.244445,-0.2,0.133334,0.333333,0.266667,0.222222,-0.022222,0.044444,-0.444444,-0.088889,0,0.155555,-0.088888,-0.066667,0.133333,0.177778,-0.377778,0.111111,0,0.2,-0.455555,0.055555,0.022223,0.111111,-0.022223,0.155556,0.088889,0.066667,0.133333,0.044444,0.222223,-0.222223,-0.066666,-0.111111,0.044444,-0.088889,-0.177778,-128.181253
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:16,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,15,16,16,16

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[723.0,979.0]

=== LOG SUMMARY ===
{"entries":[{"error_logs":3,"error_pct":0.01,"service":"frontend","total_logs":44035}],"mode":"errors","omitted_services":9,"service_count":10}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":452.4,"error_pct":0.0,"p95_during_ms":400.67539999999946,"p95_pre_ms":72.52839999999996,"service":"checkoutservice","spans":7687},{"delta_pct":-37.5,"error_pct":0.0,"p95_during_ms":0.3800999999999999,"p95_pre_ms":0.6081999999999999,"service":"paymentservice","spans":803},{"delta_pct":9.2,"error_pct":0.0,"p95_during_ms":60.927499999999846,"p95_pre_ms":55.77909999999995,"service":"frontend","spans":166791},{"delta_pct":6.1,"error_pct":0.0,"p95_during_ms":0.225,"p95_pre_ms":0.212,"service":"currencyservice","spans":46329},{"delta_pct":3.9,"error_pct":0.0,"p95_during_ms":0.5295999999999998,"p95_pre_ms":0.5094999999999996,"service":"emailservice","spans":1032},{"delta_pct":-2.6,"error_pct":0.0,"p95_during_ms":4.86675,"p95_pre_ms":4.997549999999996,"service":"recommendationservice","spans":22070},{"delta_pct":0.0,"error_pct":0.0,"p95_during_ms":0.031,"p95_pre_ms":0.031,"service":"productcatalogservice","spans":82436}],"omitted_services":0,"service_count":7}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=3 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":583.8,"rank":1,"service":"redis","severity_z":37.308},{"evidence_source":"trace","onset_rel_s":741.6,"rank":2,"service":"checkoutservice","severity_z":34.436},{"evidence_source":"metric","onset_rel_s":786.0,"rank":3,"service":"emailservice","severity_z":27.4},{"evidence_source":"metric","onset_rel_s":807.0,"rank":4,"service":"frontend","severity_z":40.0},{"evidence_source":"metric","onset_rel_s":888.0,"rank":5,"service":"gke-gke-cluster-default-pool-2e1807ce-w819","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":901.8,"rank":6,"service":"shippingservice","severity_z":941.794},{"evidence_source":"metric","onset_rel_s":952.2,"rank":7,"service":"paymentservice","severity_z":250.0},{"evidence_source":"metric","onset_rel_s":978.0,"rank":8,"service":"productcatalogservice","severity_z":10.485},{"evidence_source":"metric","onset_rel_s":979.2,"rank":9,"service":"adservice","severity_z":15.684},{"evidence_source":"metric","onset_rel_s":988.8,"rank":10,"service":"gke-gke-cluster-default-pool-2e1807ce-xte3","severity_z":546.684},{"evidence_source":"metric","onset_rel_s":990.0,"rank":11,"service":"gke-gke-cluster-default-pool-2e1807ce-cx8g","severity_z":499.908},{"evidence_source":"metric","onset_rel_s":993.0,"rank":12,"service":"gke-gke-cluster-default-pool-2e1807ce-0e4z","severity_z":591.02},{"evidence_source":"none","onset_rel_s":null,"rank":13,"service":"frontend-external","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":14,"service":"loadgenerator","severity_z":0.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"emailservice","caller":"checkoutservice"},{"callee":"paymentservice","caller":"checkoutservice"},{"callee":"productcatalogservice","caller":"checkoutservice"},{"callee":"checkoutservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"frontend"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"high","reason":"Rank checkoutservice first because checkoutservice has direct container-memory-failures-total evidence (signed-z 999, persistence 18 bins); although frontend is salient, the caller path frontend -> checkoutservice means a disturbance in the callee can propagate back toward that caller-side symptom.","services":["checkoutservice","frontend"]}
