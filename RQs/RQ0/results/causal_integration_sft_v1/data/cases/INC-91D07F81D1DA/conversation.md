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
opaque_id: INC-91D07F81D1DA
observation_window={"duration_rel_s":1440.0,"source_metric_rows":1441}
selection_summary={"candidate_count":17,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":285,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","cartservice","checkoutservice","currencyservice","emailservice","frontend","frontend-external","gke-gke-cluster-default-pool-2e1807ce-0e4z","gke-gke-cluster-default-pool-2e1807ce-cx8g","gke-gke-cluster-default-pool-2e1807ce-w819","gke-gke-cluster-default-pool-2e1807ce-xte3","loadgenerator","paymentservice","productcatalogservice","recommendationservice","redis","shippingservice"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[11.25,33.75,56.25,78.75,101.25,123.75,146.25,168.75,191.25,213.75,236.25,258.75,281.25,303.75,326.25,348.75,371.25,393.75,416.25,438.75,461.25,483.75,506.25,528.75,551.25,573.75,596.25,618.75,641.25,663.75,686.25,708.75,731.25,753.75,776.25,798.75,821.25,843.75,866.25,888.75,911.25,933.75,956.25,978.75,1001.25,1023.75,1046.25,1068.75,1091.25,1113.75,1136.25,1158.75,1181.25,1203.75,1226.25,1248.75,1271.25,1293.75,1316.25,1338.75,1361.25,1383.75,1406.25,1428.75]
[M1] rank=1 service=recommendationservice metric=container-memory-failures-total baseline=7.164652 peak=730537.912052 signed_z=999.0 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=delta:8.396178,-1.661997,-0.941157,-0.096009,1.790662,1.096256,-0.646035,-1.01097,3.656564,-1.044947,-1.456934,1.917385,-0.69567,-2.577429,-2.111222,1.50958,1.007152,-0.287758,-0.073871,3.257388,-4.529441,0.07244,1.090258,-1.971022,4.17134,1.285429,-2.819083,1.5758,-1.534272,-2.841256,0.098123,1.107095,100887.289422,289768.201163,163280.952767,36012.263057,58588.130659,12879.313602,17294.755962,-19342.391803,-45711.25087,0,6517.212949,49859.876194,17908.942596,-30083.864971,-68105.456582,9484.762095,87080.948593,-34286.435135,-28114.091599,-11373.06445,-2826.722547,87789.680626,-55379.560255,-62934.164672,75091.780576,14717.454877,-6644.884865,-24146.165554,-5287.575798,33432.254837,-16560.17081,-56296.782757
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M2] rank=2 service=recommendationservice metric=istio-latency-50 baseline=0.007437 peak=0.082185 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.007503,0.007474,0.007503,0.007472,0.007419,0.007463,0.007473,0.007455,0.007468,0.0075,0.007485,0.00747,0.007482,0.007469,0.007457,0.007377,0.00737,0.007411,0.007396,0.007413,0.007452,0.007484,0.007422,0.007323,0.007281,0.007309,0.007367,0.007429,0.007516,0.007484,0.00743,0.007416,0.007513,0.0096,0.077546,0.080738,0.077059,0.076245,0.079382,0.080319,0.078571,0.077434,0.079486,0.078627,0.079144,0.075278,0.07516,0.076424,0.075,0.074107,0.075277,0.077171,0.075484,0.077155,0.077517,0.077105,0.076407,0.076525,0.079276,0.080705,0.080189,0.075698,0.076993,0.079701]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M3] rank=3 service=recommendationservice metric=istio-latency-90 baseline=0.009593 peak=1.575769 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.009607,0.009562,0.00962,0.009635,0.009559,0.009576,0.009606,0.009585,0.009588,0.009622,0.009608,0.009622,0.009647,0.009634,0.009613,0.009518,0.009494,0.009525,0.00956,0.009576,0.009611,0.00968,0.009637,0.009562,0.00961,0.00963,0.00953,0.00957,0.009672,0.009625,0.009558,0.009586,0.009705,0.149355,0.794737,1.368182,1.316337,0.934722,1.088953,1.418142,1.451282,1.234375,1.297087,1.321212,1.328846,0.985849,1.040761,1.270297,1.312981,1.254687,1.139535,1.271782,1.146739,1.245313,1.225,1.330263,1.307143,1.170225,1.552692,1.539764,1.170455,1.032278,1.065854,1.232813]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M4] rank=4 service=recommendationservice metric=istio-latency-95 baseline=0.009863 peak=2.037885 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.00987,0.009823,0.009884,0.009906,0.009827,0.00984,0.009874,0.009851,0.009852,0.009887,0.009873,0.009891,0.009917,0.009905,0.009883,0.009785,0.00976,0.009791,0.00983,0.009846,0.009884,0.009954,0.009914,0.009841,0.0099,0.00992,0.009801,0.009838,0.009941,0.009893,0.009824,0.009858,0.009979,0.6,1.572727,1.934091,1.908168,1.704808,1.794477,1.959071,1.975641,1.867187,1.898544,1.910606,1.914423,1.73628,1.77038,1.885149,1.90649,1.877344,1.819767,1.885891,1.82337,1.872656,1.8625,1.915132,1.903571,1.835112,2.026346,2.019882,1.835227,1.766139,1.782927,1.866406]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M5] rank=5 service=gke-gke-cluster-default-pool-2e1807ce-cx8g metric=node-memory-active-bytes baseline=9429.148434 peak=21801460.622222 signed_z=999.0 onset_bin=59 onset_rel_s=1338.75 persistence_bins=2
values_compact=delta:9921.422222,-1729.422222,273.066667,455.111111,1363.733614,1913.066386,-453.284315,-2823.515685,-2366.577778,1638.4,2002.488889,-91.022222,91.022222,1456.355555,-910.222222,-1820.444444,455.111111,546.133333,-2639.644444,-182.044445,91.022223,546.133333,2184.533333,-1092.266666,-182.044445,637.155556,819.2,0,-91.022223,-182.044444,364.088889,1183.288889,-1456.355556,-1729.422222,1092.266667,273.066666,-1183.288889,182.044445,910.222222,364.088889,-1274.311111,-182.044445,3367.822223,910.222222,-2457.6,-2457.6,-273.066667,1183.288889,1092.266667,1274.311111,-2184.533333,-1365.333334,455.111111,1183.288889,2275.555556,-728.177778,-1274.311111,-182.044445,1365.333334,21790902.044444,-728.177778,-21791357.155555,455.111111,91.022222
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M6] rank=6 service=gke-gke-cluster-default-pool-2e1807ce-xte3 metric=node-memory-active-bytes baseline=7574.060247 peak=21535402.666667 signed_z=999.0 onset_bin=2 onset_rel_s=56.25 persistence_bins=4
values_compact=raw:[7099.733333,8283.022222,22937.6,21663.288889,7281.777778,6826.666667,6917.688889,7827.911111,6189.511111,6098.488889,8009.955556,8100.977778,6007.466667,6280.533333,6553.6,6189.511111,6644.622222,7099.733333,4915.2,5643.377778,6553.6,5188.266667,6462.577778,8009.955556,7645.866667,5279.288889,5188.266667,6917.688889,7554.844444,7008.711111,4824.177778,4460.088889,6098.488889,6189.511111,6735.644444,6917.688889,5097.244444,6189.511111,6735.644444,5552.355556,5734.4,6826.666667,8100.977778,6917.688889,6462.577778,7645.866667,7372.8,21534765.511111,21535402.666667,6553.6,7190.755556,8009.955556,3913.955556,6189.511111,9011.2,5916.444444,4915.2,6098.488889,6007.466667,4733.155556,6462.577778,7190.755556,6462.577778,6007.466667]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M7] rank=7 service=gke-gke-cluster-default-pool-2e1807ce-cx8g metric=node-disk-reads-completed-total baseline=0.0 peak=0.133333 signed_z=999.0 onset_bin=62 onset_rel_s=1406.25 persistence_bins=2
values_compact=rle:0*62,0.133333*2
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M8] rank=8 service=gke-gke-cluster-default-pool-2e1807ce-w819 metric=node-disk-reads-completed-total baseline=0.0 peak=0.488889 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=2
values_compact=rle:0*33,0.488889*2,0*29
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M9] rank=9 service=gke-gke-cluster-default-pool-2e1807ce-cx8g metric=node-disk-read-bytes-total baseline=0.0 peak=17476.266667 signed_z=999.0 onset_bin=62 onset_rel_s=1406.25 persistence_bins=2
values_compact=rle:0*62,17476.266667*2
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M10] rank=10 service=gke-gke-cluster-default-pool-2e1807ce-w819 metric=node-disk-read-bytes-total baseline=0.0 peak=2002.488889 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=2
values_compact=rle:0*33,2002.488889*2,0*29
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M11] rank=11 service=recommendationservice metric=istio-latency-99 baseline=0.01842 peak=2.407577 signed_z=670.16 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=raw:[0.020042,0.01605,0.019668,0.020392,0.016493,0.017332,0.019327,0.018197,0.018192,0.019769,0.019211,0.019961,0.020684,0.020371,0.019711,0.009999,0.009972,0.010783,0.016919,0.018053,0.019773,0.024778,0.024786,0.017992,0.023248,0.023575,0.013955,0.017368,0.021149,0.020008,0.016086,0.018693,0.061545,1.937143,2.314545,2.386818,2.381634,2.340962,2.358895,2.391814,2.395128,2.373438,2.379709,2.382121,2.382885,2.347256,2.354076,2.37703,2.381298,2.375469,2.363953,2.377178,2.364674,2.374531,2.3725,2.383026,2.380714,2.367022,2.405269,2.403976,2.367045,2.353228,2.356585,2.373281]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M12] rank=12 service=recommendationservice metric=container-cpu-system-seconds-total baseline=0.410221 peak=16.53345 signed_z=317.302 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=delta:0.425397,-0.042111,-0.020119,0.006839,0.005349,0.017493,0.010913,-0.011678,0.0318,0.018542,0.011046,0.020821,-0.022473,-0.02924,-0.005906,0.020399,-0.00166,0.012466,0.0101,0.002991,-0.078453,-0.002947,0.047166,-0.018652,-0.114716,0.137558,-0.016219,-0.017368,0.03836,0.061106,-0.023636,-0.042954,2.010592,6.389735,4.526025,0.810598,0.430589,0.134436,0.307687,0.088045,-0.033282,0.002891,0.030052,0.426665,0.100865,-0.103082,-0.389095,0.167436,0.364426,-0.161154,0.4556,-0.510894,-0.655502,0.919194,0.012348,-0.315574,0.687738,-0.150458,-0.284279,0.015565,-0.116926,0.371327,-0.065228,-0.281705
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[715.0,1440.0]

=== LOG SUMMARY ===
{"entries":[{"change_pct":-33.3,"n_during":10,"n_pre":15,"service":"redis"},{"change_pct":-5.1,"n_during":316,"n_pre":333,"service":"emailservice"},{"change_pct":-5.1,"n_during":632,"n_pre":666,"service":"paymentservice"},{"change_pct":-4.9,"n_during":949,"n_pre":998,"service":"checkoutservice"},{"change_pct":-3.9,"n_during":30526,"n_pre":31749,"service":"frontend"},{"change_pct":-3.8,"n_during":5154,"n_pre":5358,"service":"adservice"},{"change_pct":-3.5,"n_during":27368,"n_pre":28346,"service":"currencyservice"},{"change_pct":-2.8,"n_during":8903,"n_pre":9157,"service":"cartservice"}],"mode":"volume","omitted_services":2,"service_count":10}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":3479.2,"error_pct":0.0,"p95_during_ms":188.39844999999977,"p95_pre_ms":5.2636499999999975,"service":"recommendationservice","spans":26918},{"delta_pct":109.7,"error_pct":0.0,"p95_during_ms":171.76899999999995,"p95_pre_ms":81.93019999999999,"service":"frontend","spans":203436},{"delta_pct":59.2,"error_pct":0.0,"p95_during_ms":0.9615999999999995,"p95_pre_ms":0.6041999999999997,"service":"paymentservice","spans":937},{"delta_pct":-8.1,"error_pct":0.0,"p95_during_ms":0.227,"p95_pre_ms":0.247,"service":"currencyservice","spans":55999},{"delta_pct":2.8,"error_pct":0.0,"p95_during_ms":105.3071999999999,"p95_pre_ms":102.415,"service":"checkoutservice","spans":8944},{"delta_pct":-2.1,"error_pct":0.0,"p95_during_ms":0.47,"p95_pre_ms":0.4802,"service":"emailservice","spans":1225},{"delta_pct":0.0,"error_pct":0.0,"p95_during_ms":0.025,"p95_pre_ms":0.025,"service":"productcatalogservice","spans":101417}],"omitted_services":0,"service_count":7}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=3 omitted_edges=1
[{"evidence_source":"metric","onset_rel_s":735.0,"rank":1,"service":"gke-gke-cluster-default-pool-2e1807ce-w819","severity_z":999.0},{"evidence_source":"trace","onset_rel_s":735.0,"rank":2,"service":"recommendationservice","severity_z":552.714},{"evidence_source":"trace","onset_rel_s":735.0,"rank":3,"service":"frontend","severity_z":22.281},{"evidence_source":"trace","onset_rel_s":735.0,"rank":4,"service":"paymentservice","severity_z":9.021},{"evidence_source":"metric","onset_rel_s":772.8,"rank":5,"service":"cartservice","severity_z":312.649},{"evidence_source":"metric","onset_rel_s":796.2,"rank":6,"service":"emailservice","severity_z":103.814},{"evidence_source":"metric","onset_rel_s":853.8,"rank":7,"service":"productcatalogservice","severity_z":188.117},{"evidence_source":"metric","onset_rel_s":1042.8,"rank":8,"service":"adservice","severity_z":38.884},{"evidence_source":"metric","onset_rel_s":1060.8,"rank":9,"service":"gke-gke-cluster-default-pool-2e1807ce-xte3","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1329.0,"rank":10,"service":"gke-gke-cluster-default-pool-2e1807ce-cx8g","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1404.0,"rank":11,"service":"checkoutservice","severity_z":15.574},{"evidence_source":"none","onset_rel_s":null,"rank":12,"service":"loadgenerator","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":13,"service":"shippingservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":14,"service":"redis","severity_z":0.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"emailservice","caller":"checkoutservice"},{"callee":"paymentservice","caller":"checkoutservice"},{"callee":"productcatalogservice","caller":"checkoutservice"},{"callee":"checkoutservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"frontend"},{"callee":"recommendationservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"recommendationservice"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"high","reason":"Rank recommendationservice first because recommendationservice has direct container-memory-failures-total evidence (signed-z 999, persistence 32 bins); although frontend is salient, the caller path frontend -> recommendationservice means a disturbance in the callee can propagate back toward that caller-side symptom.","services":["recommendationservice","frontend"]}
