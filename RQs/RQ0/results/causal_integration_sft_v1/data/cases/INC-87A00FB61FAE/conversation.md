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
opaque_id: INC-87A00FB61FAE
observation_window={"duration_rel_s":1440.0,"source_metric_rows":1441}
selection_summary={"candidate_count":17,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":267,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","cartservice","checkoutservice","currencyservice","emailservice","frontend","frontend-external","gke-gke-cluster-default-pool-2e1807ce-0e4z","gke-gke-cluster-default-pool-2e1807ce-cx8g","gke-gke-cluster-default-pool-2e1807ce-w819","gke-gke-cluster-default-pool-2e1807ce-xte3","loadgenerator","paymentservice","productcatalogservice","recommendationservice","redis","shippingservice"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[11.25,33.75,56.25,78.75,101.25,123.75,146.25,168.75,191.25,213.75,236.25,258.75,281.25,303.75,326.25,348.75,371.25,393.75,416.25,438.75,461.25,483.75,506.25,528.75,551.25,573.75,596.25,618.75,641.25,663.75,686.25,708.75,731.25,753.75,776.25,798.75,821.25,843.75,866.25,888.75,911.25,933.75,956.25,978.75,1001.25,1023.75,1046.25,1068.75,1091.25,1113.75,1136.25,1158.75,1181.25,1203.75,1226.25,1248.75,1271.25,1293.75,1316.25,1338.75,1361.25,1383.75,1406.25,1428.75]
[M1] rank=1 service=emailservice metric=container-memory-failures-total baseline=0.154603 peak=988.963464 signed_z=999.0 onset_bin=32 onset_rel_s=731.25 persistence_bins=11
values_compact=raw:[3.443142,0.044145,0.052089,0.041157,0.041551,0.0,0.0,0.062773,0.176095,0.121706,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.192229,0.32293,0.087881,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.190621,28.629766,29.600554,0.0,539.878695,470.446233,0.872709,0.178784,0.059911,0.068067,482.902217,2.375238,2.17477,0.237175,0.116877,0.127191,0.019149,0.0,0.081538,0.09033,0.0,0.040392,0.398781,0.383501,0.137196,0.083908,0.087598,0.085244,554.816667,564.260961,558.5,558.5,null]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000001
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,20,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,15,0
[M2] rank=2 service=emailservice metric=container-memory-rss baseline=40905062.4 peak=123469824.0 signed_z=999.0 onset_bin=34 onset_rel_s=776.25 persistence_bins=30
values_compact=delta:40894464,4096,0,4096,0,0,0,4096,-4096,0,0,0,0,0,0,0,0,0,0,0,8192,0,0,0,0,0,0,0,0,0,0,-4096,0,0,2158592,38289408,73728,12288,0,4096,2162688,38449152,114688,0,20480,8192,4096,-40906752,0,8192,0,0,-40534016,-106496,12288,0,8192,0,1798144,38359040,2129920,38674432,0,1822720
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M3] rank=3 service=emailservice metric=container-memory-usage-bytes baseline=43922386.488889 peak=131764224.0 signed_z=999.0 onset_bin=34 onset_rel_s=776.25 persistence_bins=30
values_compact=delta:43909120,6144,-2048,8192,0,0,-4096,4096,-4096,4096,0,0,0,-4096,0,0,4096,-2048,6144,-4096,4096,0,4096,0,4096,0,-8192,4096,0,0,-4096,-4096,20480,-4096,2691072,40325120,73728,12288,0,0,2637824,40615936,110592,0,20480,8192,4096,-43941888,4096,8192,0,0,-42958848,-249856,16384,-4096,24576,0,2326528,40382464,2588672,40783872,0,2347008
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M4] rank=4 service=emailservice metric=container-memory-working-set-bytes baseline=43844562.488889 peak=131543040.0 signed_z=999.0 onset_bin=34 onset_rel_s=776.25 persistence_bins=30
values_compact=delta:43831296,6144,-2048,8192,0,0,-4096,4096,-4096,4096,0,0,0,-4096,0,0,4096,-2048,6144,-4096,4096,0,4096,0,4096,0,-8192,4096,0,0,-4096,-4096,20480,-4096,2691072,40251392,73728,12288,0,0,2637824,40542208,110592,0,20480,8192,4096,-43864064,4096,8192,0,0,-42885120,-249856,16384,-4096,24576,0,2326528,40308736,2588672,40710144,0,2347008
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M5] rank=5 service=emailservice metric=istio-latency-50 baseline=0.003041 peak=0.185714 signed_z=999.0 onset_bin=35 onset_rel_s=798.75 persistence_bins=27
values_compact=rle:0.004*1,0.003041*1,0.003*1,0.003048*1,0.003051*1,0.003*6,0.003049*1,0.003054*1,0.003*7,0.00308*1,0.003111*1,0.003*11,0.003043*1,0.003147*1,0.003846*2,0.004833*1,0.01*1,0.11875*1,0.1375*1,0.004778*1,0.004538*1,0.0045*1,0.004143*1,0.004818*1,0.004333*1,0.004077*1,0.0044*1,0.003182*1,0.003889*1,0.1125*1,0.00475*1,0.1375*1,0.005*1,0.004167*1,0.0046*2,0.004*1,0.003*1,0.01*1,0.127273*1,0.1375*1,0.005*1
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M6] rank=6 service=emailservice metric=istio-latency-90 baseline=0.005041 peak=6.75 signed_z=999.0 onset_bin=35 onset_rel_s=798.75 persistence_bins=27
values_compact=rle:0.01915*1,0.004673*1,0.0046*1,0.004686*1,0.004692*1,0.0046*6,0.004688*1,0.004697*1,0.0046*7,0.004744*1,0.0048*1,0.0046*11,0.004677*1,0.004865*1,1.225*1,0.975*1,0.4625*1,0.4*1,0.3*1,0.4375*1,1.225*1,0.85*1,0.395*1,0.316667*1,0.3625*1,0.416667*1,0.25*1,0.325*1,0.004927*1,6.75*1,6.25*1,0.2375*1,0.39375*1,0.366667*1,0.4125*1,0.4*2,1.375*1,0.0046*1,0.5*1,0.425*1,0.6*1,0.9*1
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M7] rank=7 service=emailservice metric=istio-latency-95 baseline=0.005402 peak=8.375 signed_z=999.0 onset_bin=34 onset_rel_s=776.25 persistence_bins=29
values_compact=delta:0.022075,-0.017197,-0.000078,0.00009,0.000007,-0.000097,0,0,0,0,0,0.000093,0.00001,-0.000103,0,0,0,0,0,0,0.000152,0.000298,-0.00045,0,0,0,0,0,0,0,0,0,0,0.000081,0.135839,3.580061,-1.239531,-1.76875,-0.0125,-0.15,0.075,1.2375,-0.225,-1.19,-0.039167,0.085417,0.00625,0,0.075,-0.225,8.025,-0.25,-7.8125,0.134375,-0.013542,0.141667,-0.025,0.75,0.6375,-1.9327,0.7452,0.1,0.3,-0.2
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M8] rank=8 service=emailservice metric=istio-latency-99 baseline=0.00648 peak=9.675 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=30
values_compact=rle:0.024415*1,0.0175*1,0.00496*1,0.00785*1,0.008*1,0.00496*6,0.0079*1,0.0081*1,0.00496*7,0.0087*1,0.00905*1,0.00496*11,0.178*1,0.228144*1,8.488312*1,7.975*1,0.9425*1,0.94*1,0.91*1,0.925*1,2.3725*1,2.3275*1,0.4895*1,0.481667*1,0.895*1,0.9*2,0.915*1,0.47*1,9.675*1,9.625*1,0.4625*1,0.489375*1,0.486667*1,0.915*1,0.91*1,2.26*1,2.3875*1,0.00496*1,0.95*1,2.11*1,2.23*1,0.99*1
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M9] rank=9 service=gke-gke-cluster-default-pool-2e1807ce-0e4z metric=node-memory-active-bytes baseline=8457.860741 peak=17252534.044444 signed_z=999.0 onset_bin=13 onset_rel_s=303.75 persistence_bins=4
values_compact=delta:7008.711111,910.222222,364.088889,-728.177778,-364.088888,-819.2,819.2,728.177777,-728.177777,182.044444,-1001.244444,182.044444,546.133333,10103.466667,1911.466667,-9830.4,546.133333,-1001.244444,-1274.311112,1183.288889,-1365.333333,273.066667,637.155555,819.2,728.177778,-2548.622222,728.177778,-728.177778,-1365.333334,3458.844445,-728.177778,-2275.555555,2275.555555,1820.444445,3003.733333,-3367.822222,17240155.022222,2275.555555,-17245525.333333,910.222222,1638.4,-910.222222,91.022222,182.044445,-455.111111,-273.066667,273.066667,-1547.377778,-364.088889,2548.622222,-1092.266666,0,819.2,3003.733333,910.222222,-4733.155555,-3003.733334,-637.155555,2821.688889,2912.711111,-728.177778,-3003.733333,-728.177778,637.155555
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M10] rank=10 service=gke-gke-cluster-default-pool-2e1807ce-w819 metric=node-memory-active-bytes baseline=2877.945679 peak=10684279.466667 signed_z=999.0 onset_bin=35 onset_rel_s=798.75 persistence_bins=6
values_compact=delta:25031.111111,-23392.711111,273.066667,91.022222,0,1547.377778,273.066666,-1274.311111,-819.2,-91.022222,0,-91.022222,637.155555,273.066667,-364.088889,-273.066667,1456.355556,1820.444444,-1547.377777,-1911.466667,273.066667,364.088889,-364.088889,-91.022223,455.111112,-273.066667,182.044444,-91.022222,-546.133333,91.022222,91.022222,273.066667,1820.444444,91.022223,-2275.555556,199234.252934,13.39151,-199611.648373,637.070596,364.088889,221275.022222,91.022222,-221184,-273.066667,0,182.044445,1547.377778,-182.044445,-1638.4,91.022222,-455.111111,-364.088889,1729.422223,182.044444,-1183.288889,91.022222,-91.022222,-91.022222,9193.244444,1820.444445,-8009.955556,10676542.577778,1729.422222,-10678454.044444
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M11] rank=11 service=cartservice metric=istio-latency-90 baseline=0.004956 peak=0.194167 signed_z=347.798 onset_bin=46 onset_rel_s=1046.25 persistence_bins=4
values_compact=raw:[0.004777,0.004824,0.004797,0.004761,0.004883,0.004991,0.004857,0.004794,0.004874,0.004928,0.004972,0.004823,0.004853,0.004892,0.004794,0.004823,0.00485,0.004813,0.004811,0.00484,0.00484,0.004922,0.00725,0.00491,0.004886,0.004914,0.004934,0.004876,0.004747,0.00485,0.004955,0.004984,0.004989,0.004923,0.004763,0.004739,0.006117,0.006125,0.004855,0.004901,0.00504,0.004961,0.004766,0.004725,0.004838,0.004974,0.006696,0.006727,0.00488,0.004779,0.004751,0.004745,0.004768,0.004947,0.010003,0.00865,0.004969,0.004856,0.004711,0.004739,0.004709,0.004673,0.004907,0.004936]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M12] rank=12 service=adservice metric=istio-latency-99 baseline=0.004971 peak=0.007679 signed_z=256.698 onset_bin=46 onset_rel_s=1046.25 persistence_bins=4
values_compact=delta:0.004966,-0.000007,0,0.000006,0,0.000013,0.000001,-0.00002,0,0.000013,-0.000001,-0.000012,0.000013,0.000001,0.000006,0.000005,-0.000019,-0.000005,0,0.000006,0.000018,-0.000006,0.000015,0,-0.000007,0,-0.000026,0,0.000018,0,-0.000019,0.000006,0,-0.000006,0.000007,0,-0.000007,0,0.000001,0,0.000005,0,-0.000005,0,0.000012,0,0.001103,-0.000063,-0.001022,0.002302,-0.00031,-0.001998,-0.000025,0,0.000007,0,-0.000007,0,0.000013,0,-0.000012,0,-0.000001,0
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[1297.0,1440.0]

=== LOG SUMMARY ===
{"entries":[{"error_logs":33,"error_pct":1.75,"service":"checkoutservice","total_logs":1887},{"error_logs":7,"error_pct":1.13,"service":"emailservice","total_logs":618}],"mode":"errors","omitted_services":8,"service_count":10}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":-36.7,"error_pct":0.0,"p95_during_ms":0.3128500000000001,"p95_pre_ms":0.49439999999999984,"service":"paymentservice","spans":917},{"delta_pct":-8.3,"error_pct":0.0,"p95_during_ms":0.022,"p95_pre_ms":0.024,"service":"productcatalogservice","spans":97837},{"delta_pct":4.0,"error_pct":0.0,"p95_during_ms":0.41914999999999975,"p95_pre_ms":0.403,"service":"emailservice","spans":1012},{"delta_pct":-2.9,"error_pct":0.0,"p95_during_ms":189.5223999999999,"p95_pre_ms":195.269,"service":"frontend","spans":197315},{"delta_pct":-1.6,"error_pct":0.0,"p95_during_ms":0.18,"p95_pre_ms":0.183,"service":"currencyservice","spans":54654},{"delta_pct":0.8,"error_pct":0.0,"p95_during_ms":307.61294999999996,"p95_pre_ms":305.2203499999999,"service":"checkoutservice","spans":8660},{"delta_pct":0.3,"error_pct":0.0,"p95_during_ms":4.867,"p95_pre_ms":4.854,"service":"recommendationservice","spans":26072}],"omitted_services":0,"service_count":7}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=3 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":790.8,"rank":1,"service":"emailservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":808.8,"rank":2,"service":"gke-gke-cluster-default-pool-2e1807ce-0e4z","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":915.0,"rank":3,"service":"shippingservice","severity_z":184.742},{"evidence_source":"metric","onset_rel_s":1075.2,"rank":4,"service":"recommendationservice","severity_z":49.13},{"evidence_source":"metric","onset_rel_s":1084.2,"rank":5,"service":"gke-gke-cluster-default-pool-2e1807ce-xte3","severity_z":35.349},{"evidence_source":"metric","onset_rel_s":1105.2,"rank":6,"service":"adservice","severity_z":256.698},{"evidence_source":"metric","onset_rel_s":1125.0,"rank":7,"service":"checkoutservice","severity_z":39.825},{"evidence_source":"metric","onset_rel_s":1228.2,"rank":8,"service":"cartservice","severity_z":347.798},{"evidence_source":"metric","onset_rel_s":1369.8,"rank":9,"service":"gke-gke-cluster-default-pool-2e1807ce-w819","severity_z":999.0},{"evidence_source":"none","onset_rel_s":null,"rank":10,"service":"gke-gke-cluster-default-pool-2e1807ce-cx8g","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":11,"service":"frontend","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":12,"service":"productcatalogservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":13,"service":"currencyservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":14,"service":"paymentservice","severity_z":0.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"currencyservice","caller":"checkoutservice"},{"callee":"emailservice","caller":"checkoutservice"},{"callee":"paymentservice","caller":"checkoutservice"},{"callee":"productcatalogservice","caller":"checkoutservice"},{"callee":"checkoutservice","caller":"frontend"},{"callee":"currencyservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"frontend"},{"callee":"recommendationservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"recommendationservice"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"high","reason":"Rank emailservice first because emailservice has direct container-memory-failures-total evidence (signed-z 999, persistence 11 bins); although checkoutservice is salient, the caller path checkoutservice -> emailservice means a disturbance in the callee can propagate back toward that caller-side symptom.","services":["emailservice","checkoutservice"]}
