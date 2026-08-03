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
opaque_id: INC-E41E754E5173
observation_window={"duration_rel_s":1440.0,"source_metric_rows":1441}
selection_summary={"candidate_count":17,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":269,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","cartservice","checkoutservice","currencyservice","emailservice","frontend","frontend-external","gke-gke-cluster-default-pool-2e1807ce-0e4z","gke-gke-cluster-default-pool-2e1807ce-cx8g","gke-gke-cluster-default-pool-2e1807ce-w819","gke-gke-cluster-default-pool-2e1807ce-xte3","loadgenerator","paymentservice","productcatalogservice","recommendationservice","redis","shippingservice"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[11.25,33.75,56.25,78.75,101.25,123.75,146.25,168.75,191.25,213.75,236.25,258.75,281.25,303.75,326.25,348.75,371.25,393.75,416.25,438.75,461.25,483.75,506.25,528.75,551.25,573.75,596.25,618.75,641.25,663.75,686.25,708.75,731.25,753.75,776.25,798.75,821.25,843.75,866.25,888.75,911.25,933.75,956.25,978.75,1001.25,1023.75,1046.25,1068.75,1091.25,1113.75,1136.25,1158.75,1181.25,1203.75,1226.25,1248.75,1271.25,1293.75,1316.25,1338.75,1361.25,1383.75,1406.25,1428.75]
[M1] rank=1 service=productcatalogservice metric=container-memory-mapped-file baseline=0.0 peak=2211840.0 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=rle:0*33,2211840*31
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M2] rank=2 service=productcatalogservice metric=istio-latency-90 baseline=0.004421 peak=0.080226 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.004472,0.004453,0.004413,0.00444,0.004451,0.004426,0.004421,0.004426,0.004435,0.00442,0.004405,0.004414,0.004416,0.004424,0.004425,0.004415,0.004418,0.004429,0.004434,0.004418,0.00441,0.004425,0.00442,0.004399,0.004393,0.004399,0.004409,0.004398,0.004382,0.004396,0.004429,0.004455,0.004459,0.033696,0.074004,0.074862,0.07766,0.076325,0.075404,0.078481,0.07811,0.075334,0.074725,0.07744,0.075463,0.075676,0.075755,0.076799,0.078289,0.076675,0.078447,0.076861,0.077141,0.077743,0.0757,0.07622,0.074916,0.076995,0.078041,0.07736,0.076991,0.075182,0.07603,0.078407]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M3] rank=3 service=productcatalogservice metric=istio-latency-95 baseline=0.004716 peak=0.090508 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.004754,0.004739,0.004709,0.004736,0.004742,0.004719,0.004713,0.004716,0.004725,0.004719,0.004704,0.00471,0.004714,0.004717,0.004716,0.00471,0.004711,0.004717,0.004718,0.00471,0.004709,0.004718,0.004715,0.004705,0.004701,0.004703,0.004709,0.004702,0.004692,0.004699,0.004724,0.004744,0.004745,0.073741,0.08709,0.087553,0.088923,0.088183,0.087999,0.089647,0.089215,0.087834,0.0877,0.088875,0.087731,0.087838,0.087923,0.088481,0.089216,0.088394,0.089395,0.088662,0.088741,0.088963,0.087919,0.088424,0.087718,0.088552,0.089091,0.088699,0.088496,0.087591,0.088015,0.089259]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M4] rank=4 service=productcatalogservice metric=istio-latency-99 baseline=0.004952 peak=0.098733 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.00498,0.004968,0.004946,0.004971,0.004975,0.004951,0.004948,0.004945,0.004957,0.004957,0.004943,0.004947,0.004952,0.004951,0.004949,0.004946,0.004945,0.004948,0.004946,0.004944,0.004947,0.004953,0.004951,0.00495,0.004948,0.004946,0.004949,0.004945,0.00494,0.004942,0.00496,0.004974,0.004973,0.094892,0.097575,0.097706,0.097934,0.097669,0.098068,0.09858,0.098095,0.097873,0.09808,0.098022,0.097546,0.097568,0.097656,0.097826,0.097931,0.097769,0.098135,0.098164,0.09802,0.097948,0.09772,0.098188,0.09796,0.097796,0.097931,0.09777,0.097699,0.097518,0.097603,0.097941]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M5] rank=5 service=gke-gke-cluster-default-pool-2e1807ce-w819 metric=node-memory-active-bytes baseline=1791.74716 peak=10835285.333333 signed_z=999.0 onset_bin=51 onset_rel_s=1158.75 persistence_bins=5
values_compact=delta:1911.466667,-546.133334,182.044445,728.177778,182.044444,-455.111111,-455.111111,-182.044445,182.044445,364.088889,364.088889,-364.088889,-273.066667,546.133333,-182.044444,-637.155556,364.088889,1001.244445,-455.111111,-273.066667,182.044444,-455.111111,91.022222,91.022223,0,-273.066667,-364.088889,-273.066667,0,273.066667,364.088889,273.066667,-91.022223,-91.022222,-182.044444,-91.022222,273.066666,273.066667,-182.044445,-364.088888,364.088888,364.088889,-91.022222,-728.177778,-91.022222,455.111111,-182.044444,91.022222,364.088889,91.022222,-182.044444,14654.577777,10818264.177778,-14199.466666,-10818355.2,91.022222,91.022222,-1001.244444,-455.111112,182.044445,10825363.911111,91.022222,-10824362.666666,91.022222
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M6] rank=6 service=gke-gke-cluster-default-pool-2e1807ce-cx8g metric=node-disk-reads-completed-total baseline=0.005556 peak=360.177778 signed_z=999.0 onset_bin=14 onset_rel_s=326.25 persistence_bins=33
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.088889,0,-0.088889,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,64.977778,291.422222,-58.2,39.822222,14.555556,-103.222222,110.666666,-47.488889,47.4,-1.111111,-0.711111,0.311111,-21.155555,22.711111,-57.8,53.488889,-82.177778,64.111111,0.955556,-76.711112,94.822223,-64.355556,67.266667,-0.222222,0.822222,-1.955556,-48.8,47.666667,-80.533333,80.911111,-48.377778
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M7] rank=7 service=gke-gke-cluster-default-pool-2e1807ce-cx8g metric=node-disk-read-bytes-total baseline=733.866667 peak=47721858.844444 signed_z=999.0 onset_bin=14 onset_rel_s=326.25 persistence_bins=33
values_compact=rle:0*14,11741.866667*2,0*17,8778911.288889*1,47721858.844444*1,39840062.577778*1,44809147.733333*1,46824743.822222*1,33167041.422222*1,47721858.844444*1,41328457.955556*1,47721858.844444*4,44870314.666667*1,47721858.844444*1,40070166.755556*1,47721858.844444*1,36813755.733333*1,45286832.355556*1,45272268.8*1,34972922.311111*1,47721858.844444*1,39044892.444444*1,47721858.844444*4,41712935.822222*1,47721858.844444*1,36988518.4*1,47721858.844444*1,41089615.644444*1
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M8] rank=8 service=recommendationservice metric=istio-latency-90 baseline=0.009648 peak=0.064777 signed_z=539.345 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.009912,0.00979,0.009618,0.009786,0.009796,0.009612,0.009599,0.009577,0.009554,0.009518,0.009595,0.009841,0.009828,0.009802,0.009788,0.009553,0.009617,0.009603,0.009569,0.009596,0.009639,0.009653,0.009612,0.009637,0.009642,0.009527,0.009548,0.009546,0.009534,0.009625,0.009676,0.009644,0.009612,0.022425,0.055,0.061296,0.061279,0.055977,0.054699,0.063602,0.055217,0.0234,0.023459,0.055996,0.055698,0.057202,0.058412,0.052927,0.057831,0.050263,0.024302,0.024545,0.024846,0.061865,0.057284,0.024577,0.024534,0.038079,0.054425,0.056629,0.056928,0.024554,0.024498,0.062222]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M9] rank=9 service=productcatalogservice metric=container-memory-cache baseline=0.0 peak=120143872.0 signed_z=438.945 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,119824384,-1622016,0,-102400,-557056,831488,-1564672,1150976,815104,-1474560,761856,-47968256,48320512,364544,1056768,-1413120,1720320,-1433600,1118208,-3166208,630784,802816,-1228800,81920,-29179904,31981568,0,-520192,-417792,1200128,-3948544
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M10] rank=10 service=productcatalogservice metric=container-memory-usage-bytes baseline=10608833.422222 peak=134217728.0 signed_z=435.261 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=delta:10469376,-233472,462848,-483328,299008,307200,-53248,-319488,-126976,126976,61440,184320,-8192,233472,-679936,417792,69632,65536,106496,-241664,380928,-659456,286720,-344064,98304,360448,-339968,-176128,827392,-651264,528384,-573440,-131072,122990592,782336,102400,0,53248,-61440,-32768,32768,8192,65536,-73728,-52322304,52404224,-28672,-81920,-61440,-126976,245760,-376832,167936,196608,28672,-28672,-114688,-31940608,32059392,0,0,-49152,-8192,-53248
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M11] rank=11 service=productcatalogservice metric=container-cpu-system-seconds-total baseline=1.034488 peak=14.751998 signed_z=110.928 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.806021,1.161951,1.072738,1.014799,0.967554,0.915672,1.030304,0.916521,1.046947,1.205094,1.113812,0.980496,0.999099,1.026001,1.018129,1.069533,1.11118,1.112044,1.069094,1.116177,1.104035,1.06757,1.198612,1.187342,1.15098,1.142056,1.084955,0.964153,0.927466,1.060043,1.11153,1.117927,1.119286,7.929905,12.432904,13.761815,13.788772,13.453531,14.103253,13.690247,13.661749,13.914586,13.509065,13.806353,14.230583,13.669049,13.364168,13.815062,13.057272,13.310391,13.584159,13.511941,13.572243,13.088511,13.755012,13.711402,13.135955,13.346114,12.935778,13.293584,13.24635,12.582537,13.386688,13.267605]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M12] rank=12 service=recommendationservice metric=istio-latency-50 baseline=0.007439 peak=0.012079 signed_z=82.487 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.007556,0.007493,0.007408,0.0075,0.007535,0.007425,0.007417,0.007415,0.007369,0.00732,0.007393,0.007531,0.007496,0.007519,0.007521,0.007362,0.007405,0.007474,0.007423,0.007411,0.007434,0.007462,0.007433,0.007395,0.007407,0.007394,0.007397,0.00741,0.007406,0.007415,0.007473,0.007457,0.007412,0.00821,0.009322,0.009768,0.009924,0.010426,0.010025,0.011293,0.010721,0.009556,0.009471,0.009698,0.010389,0.010542,0.0098,0.009892,0.011656,0.011127,0.009876,0.010069,0.010431,0.009983,0.009901,0.009975,0.009748,0.00975,0.010303,0.01195,0.011887,0.010259,0.010372,0.011131]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[710.0,1440.0]

=== LOG SUMMARY ===
{"entries":[{"change_pct":50.0,"n_during":15,"n_pre":10,"service":"redis"},{"change_pct":5.0,"n_during":973,"n_pre":927,"service":"checkoutservice"},{"change_pct":4.9,"n_during":324,"n_pre":309,"service":"emailservice"},{"change_pct":4.9,"n_during":648,"n_pre":618,"service":"paymentservice"},{"change_pct":2.6,"n_during":27080,"n_pre":26395,"service":"currencyservice"},{"change_pct":2.5,"n_during":30440,"n_pre":29690,"service":"frontend"},{"change_pct":1.9,"n_during":5090,"n_pre":4994,"service":"shippingservice"},{"change_pct":1.7,"n_during":8776,"n_pre":8626,"service":"cartservice"}],"mode":"volume","omitted_services":2,"service_count":10}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":1588.1,"error_pct":0.0,"p95_during_ms":83.7805,"p95_pre_ms":4.963149999999998,"service":"recommendationservice","spans":25968},{"delta_pct":71.2,"error_pct":0.0,"p95_during_ms":331.67959999999994,"p95_pre_ms":193.68664999999993,"service":"frontend","spans":195467},{"delta_pct":36.1,"error_pct":0.0,"p95_during_ms":286.015049999999,"p95_pre_ms":210.13295,"service":"checkoutservice","spans":8746},{"delta_pct":20.8,"error_pct":0.0,"p95_during_ms":0.029,"p95_pre_ms":0.024,"service":"productcatalogservice","spans":97440},{"delta_pct":6.3,"error_pct":0.0,"p95_during_ms":0.43525,"p95_pre_ms":0.40939999999999993,"service":"emailservice","spans":1209},{"delta_pct":-1.1,"error_pct":0.0,"p95_during_ms":0.183,"p95_pre_ms":0.185,"service":"currencyservice","spans":53765},{"delta_pct":0.7,"error_pct":0.0,"p95_during_ms":0.3731499999999994,"p95_pre_ms":0.3705,"service":"paymentservice","spans":921}],"omitted_services":0,"service_count":7}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=3 omitted_edges=1
[{"evidence_source":"metric","onset_rel_s":733.8,"rank":1,"service":"productcatalogservice","severity_z":999.0},{"evidence_source":"trace","onset_rel_s":735.0,"rank":2,"service":"recommendationservice","severity_z":160.406},{"evidence_source":"trace","onset_rel_s":735.0,"rank":3,"service":"frontend","severity_z":9.917},{"evidence_source":"metric","onset_rel_s":747.0,"rank":4,"service":"gke-gke-cluster-default-pool-2e1807ce-xte3","severity_z":16.521},{"evidence_source":"metric","onset_rel_s":771.0,"rank":5,"service":"gke-gke-cluster-default-pool-2e1807ce-cx8g","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":876.0,"rank":6,"service":"cartservice","severity_z":12.857},{"evidence_source":"trace","onset_rel_s":1065.0,"rank":7,"service":"emailservice","severity_z":9.506},{"evidence_source":"metric","onset_rel_s":1162.8,"rank":8,"service":"shippingservice","severity_z":23.242},{"evidence_source":"metric","onset_rel_s":1168.2,"rank":9,"service":"gke-gke-cluster-default-pool-2e1807ce-w819","severity_z":999.0},{"evidence_source":"none","onset_rel_s":null,"rank":10,"service":"currencyservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":11,"service":"checkoutservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":12,"service":"adservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":13,"service":"redis","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":14,"service":"loadgenerator","severity_z":0.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"currencyservice","caller":"checkoutservice"},{"callee":"emailservice","caller":"checkoutservice"},{"callee":"productcatalogservice","caller":"checkoutservice"},{"callee":"checkoutservice","caller":"frontend"},{"callee":"currencyservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"frontend"},{"callee":"recommendationservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"recommendationservice"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"high","reason":"Rank productcatalogservice first because productcatalogservice has direct container-memory-mapped-file evidence (signed-z 999, persistence 31 bins); although recommendationservice is salient, the caller path recommendationservice -> productcatalogservice means a disturbance in the callee can propagate back toward that caller-side symptom.","services":["productcatalogservice","recommendationservice"]}
