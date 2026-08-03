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
opaque_id: INC-EB7D948141D5
observation_window={"duration_rel_s":1440.0,"source_metric_rows":1441}
selection_summary={"candidate_count":17,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":264,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","cartservice","checkoutservice","currencyservice","emailservice","frontend","frontend-external","gke-gke-cluster-default-pool-2e1807ce-0e4z","gke-gke-cluster-default-pool-2e1807ce-cx8g","gke-gke-cluster-default-pool-2e1807ce-w819","gke-gke-cluster-default-pool-2e1807ce-xte3","loadgenerator","paymentservice","productcatalogservice","recommendationservice","redis","shippingservice"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[11.25,33.75,56.25,78.75,101.25,123.75,146.25,168.75,191.25,213.75,236.25,258.75,281.25,303.75,326.25,348.75,371.25,393.75,416.25,438.75,461.25,483.75,506.25,528.75,551.25,573.75,596.25,618.75,641.25,663.75,686.25,708.75,731.25,753.75,776.25,798.75,821.25,843.75,866.25,888.75,911.25,933.75,956.25,978.75,1001.25,1023.75,1046.25,1068.75,1091.25,1113.75,1136.25,1158.75,1181.25,1203.75,1226.25,1248.75,1271.25,1293.75,1316.25,1338.75,1361.25,1383.75,1406.25,1428.75]
[M1] rank=1 service=currencyservice metric=container-memory-mapped-file baseline=0.0 peak=2215936.0 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=rle:0*33,2215936*31
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M2] rank=2 service=frontend-external metric=istio-error-total baseline=0.0 peak=0.133 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=rle:0*34,0.133*1,0*29
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M3] rank=3 service=cartservice metric=istio-latency-90 baseline=0.004807 peak=0.126071 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.004927,0.004802,0.004777,0.004762,0.004847,0.004848,0.004849,0.004989,0.004926,0.004776,0.004723,0.00483,0.004869,0.00481,0.004798,0.004746,0.004791,0.004815,0.004736,0.004713,0.004694,0.004759,0.004801,0.004798,0.004775,0.004729,0.004794,0.00481,0.004832,0.004843,0.004782,0.0048,0.004831,0.006609,0.009331,0.122917,0.008288,0.007628,0.007276,0.007097,0.006911,0.007136,0.007405,0.006727,0.006767,0.007322,0.007194,0.00721,0.006741,0.007677,0.007875,0.007864,0.008223,0.007402,0.007817,0.008295,0.00849,0.008205,0.008905,0.009391,0.007923,0.008825,0.009279,0.008471]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M4] rank=4 service=gke-gke-cluster-default-pool-2e1807ce-w819 metric=node-memory-active-bytes baseline=2491.101235 peak=22335579.022222 signed_z=999.0 onset_bin=57 onset_rel_s=1293.75 persistence_bins=2
values_compact=delta:2548.622222,364.088889,-273.066667,0,364.088889,455.111111,-819.2,-546.133333,637.155556,182.044444,-819.2,-546.133333,728.177778,455.111111,-546.133334,-91.022222,637.155556,-91.022223,-364.088888,-182.044445,91.022222,-91.022222,-182.044444,364.088889,-91.022223,0,182.044445,273.066666,273.066667,-91.022222,-91.022222,273.066666,-182.044444,91.022222,-182.044444,-91.022223,-364.088888,-637.155556,182.044444,0,455.111112,0,637.155555,182.044445,-728.177778,91.022222,-273.066667,273.066667,91.022222,-364.088889,637.155556,-182.044445,-637.155555,455.111111,-364.088889,-182.044444,819.2,22332848.355555,-455.111111,-22333030.4,1183.288889,273.066667,-1092.266667,-91.022222
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M5] rank=5 service=currencyservice metric=istio-latency-50 baseline=0.004053 peak=0.079039 signed_z=573.871 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.004056,0.003983,0.004079,0.004115,0.004102,0.004106,0.004211,0.004411,0.004407,0.004175,0.004046,0.003999,0.003983,0.004059,0.004166,0.004181,0.004038,0.003869,0.003879,0.00398,0.00403,0.004042,0.004024,0.003949,0.00386,0.003951,0.004023,0.003948,0.003932,0.003953,0.00401,0.004151,0.004068,0.030406,0.071636,0.071357,0.072957,0.071316,0.069578,0.071864,0.074649,0.073027,0.071323,0.070966,0.072396,0.072926,0.072012,0.071464,0.069045,0.072452,0.072212,0.066599,0.067187,0.068157,0.068722,0.075321,0.076775,0.075768,0.076963,0.077289,0.075454,0.072157,0.073176,0.067546]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M6] rank=6 service=currencyservice metric=istio-latency-99 baseline=0.095181 peak=0.486641 signed_z=477.938 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.093884,0.095629,0.096122,0.096113,0.096195,0.095762,0.096038,0.095996,0.096695,0.096398,0.095102,0.094919,0.094776,0.095338,0.095825,0.095332,0.094369,0.093407,0.093614,0.094621,0.095154,0.095196,0.095119,0.094865,0.09396,0.0951,0.095605,0.094757,0.09502,0.094907,0.094972,0.095209,0.094416,0.242572,0.249349,0.271758,0.313906,0.27361,0.246132,0.4035,0.447646,0.422788,0.329896,0.257892,0.405718,0.433121,0.420173,0.406494,0.306382,0.303248,0.359237,0.308048,0.272083,0.380723,0.3908,0.418474,0.437428,0.475093,0.474247,0.484021,0.486489,0.40539,0.32025,0.24835]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M7] rank=7 service=cartservice metric=istio-latency-95 baseline=0.005693 peak=0.459821 signed_z=454.794 onset_bin=33 onset_rel_s=753.75 persistence_bins=27
values_compact=raw:[0.007092,0.005323,0.004986,0.004971,0.006529,0.006353,0.006823,0.009065,0.007684,0.004985,0.00493,0.006297,0.007058,0.005484,0.005225,0.004954,0.005052,0.00577,0.004943,0.00492,0.004899,0.004967,0.00539,0.005215,0.004984,0.004936,0.005159,0.005628,0.005878,0.00612,0.004992,0.005372,0.006383,0.008977,0.233636,0.4215,0.138437,0.009043,0.00873,0.008635,0.008739,0.008723,0.008768,0.008396,0.008415,0.008685,0.008694,0.009038,0.008821,0.009635,0.009667,0.009851,0.015125,0.009021,0.009664,0.009833,0.009874,0.00965,0.266964,0.449107,0.009701,0.342763,0.430729,0.195357]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M8] rank=8 service=currencyservice metric=container-memory-cache baseline=28672.0 peak=2244608.0 signed_z=391.814 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=rle:28672*33,2244608*31
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M9] rank=9 service=productcatalogservice metric=istio-latency-99 baseline=0.00495 peak=0.007385 signed_z=358.972 onset_bin=33 onset_rel_s=753.75 persistence_bins=24
values_compact=raw:[0.004965,0.004955,0.004949,0.004942,0.004949,0.004947,0.004955,0.004969,0.004957,0.004947,0.00495,0.004959,0.004959,0.004953,0.004959,0.004957,0.004951,0.00495,0.004945,0.004941,0.004944,0.00495,0.00495,0.004947,0.004946,0.004946,0.004943,0.00494,0.00495,0.004947,0.004939,0.004946,0.004953,0.004976,0.004986,0.004975,0.004973,0.004973,0.004981,0.004997,0.004999,0.005,0.004988,0.00497,0.004975,0.004981,0.00497,0.004978,0.004982,0.00498,0.004976,0.004965,0.004968,0.004968,0.004966,0.004978,0.007251,0.007381,0.005662,0.005235,0.00499,0.004993,0.004977,0.004964]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M10] rank=10 service=recommendationservice metric=istio-latency-95 baseline=0.009824 peak=0.0215 signed_z=321.59 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.009835,0.009803,0.00978,0.009817,0.009823,0.009797,0.009838,0.009936,0.009929,0.009802,0.009767,0.009894,0.009908,0.009794,0.009794,0.009839,0.00984,0.009805,0.009789,0.009801,0.009824,0.00983,0.00982,0.009822,0.009821,0.009817,0.009819,0.009798,0.009808,0.009807,0.009794,0.009843,0.0099,0.012049,0.01405,0.018123,0.017342,0.009937,0.009938,0.009979,0.009949,0.012936,0.015661,0.013617,0.011382,0.009982,0.009973,0.009973,0.009959,0.012856,0.013191,0.01625,0.015379,0.009934,0.01225,0.016318,0.017333,0.019908,0.0215,0.0187,0.012163,0.016409,0.018022,0.0193]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M11] rank=11 service=checkoutservice metric=istio-latency-90 baseline=0.223079 peak=1.7 signed_z=206.138 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.225625,0.221765,0.226111,0.22975,0.235,0.225806,0.2225,0.224615,0.222885,0.21775,0.21875,0.223,0.236304,0.237069,0.2218,0.223103,0.233548,0.225,0.20875,0.216539,0.220968,0.226429,0.224565,0.221304,0.223,0.223913,0.22,0.2175,0.21775,0.214783,0.211562,0.22075,0.22,0.478125,0.927778,1.0,0.841667,0.794444,0.783333,0.955,1.45,0.911111,0.473077,0.49375,0.8875,0.80625,0.65625,0.823077,0.807692,0.675,0.892857,0.922222,0.83,0.7625,0.9,0.975,0.85,0.458824,1.6,1.5,0.914286,0.84,0.65,0.467857]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M12] rank=12 service=recommendationservice metric=istio-latency-90 baseline=0.009565 peak=0.015 signed_z=157.248 onset_bin=33 onset_rel_s=753.75 persistence_bins=30
values_compact=delta:0.009573,-0.000028,-0.00002,0.000035,0.000004,-0.000023,0.000039,0.000091,-0.000006,-0.000117,-0.000033,0.000118,0.000013,-0.000106,0,0.000041,0,-0.000032,-0.000016,0.00001,0.000022,0.000005,-0.000009,0.000002,0,-0.000005,-0.000001,-0.00002,0.000011,0,-0.000014,0.000047,0.000056,0.000127,0.000062,0.001421,-0.001259,-0.000318,0.000002,0.000041,-0.00003,0.00011,0.000098,-0.000085,-0.000051,-0.00004,-0.000007,0,-0.000013,0.000097,0.000009,0.000119,-0.000042,-0.00021,0.000108,0.000148,0.00005,0.001885,0.003141,-0.0038,-0.001425,0.000154,0.000925,-0.000866
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[708.0,1440.0]

=== LOG SUMMARY ===
{"entries":[{"change_pct":-17.7,"n_during":921,"n_pre":1119,"service":"checkoutservice"},{"change_pct":-17.7,"n_during":307,"n_pre":373,"service":"emailservice"},{"change_pct":-17.7,"n_during":614,"n_pre":746,"service":"paymentservice"},{"change_pct":-7.5,"n_during":5032,"n_pre":5442,"service":"shippingservice"},{"change_pct":-5.5,"n_during":8792,"n_pre":9299,"service":"cartservice"},{"change_pct":-5.5,"n_during":6388,"n_pre":6761,"service":"recommendationservice"},{"change_pct":-3.3,"n_during":5195,"n_pre":5372,"service":"adservice"},{"change_pct":-3.3,"n_during":30706,"n_pre":31762,"service":"frontend"}],"mode":"volume","omitted_services":2,"service_count":10}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":277.7,"error_pct":0.0,"p95_during_ms":296.84475000000003,"p95_pre_ms":78.59599999999999,"service":"checkoutservice","spans":9260},{"delta_pct":245.6,"error_pct":0.0,"p95_during_ms":239.67659999999964,"p95_pre_ms":69.357,"service":"frontend","spans":202939},{"delta_pct":18.6,"error_pct":0.0,"p95_during_ms":5.40865,"p95_pre_ms":4.561,"service":"recommendationservice","spans":26874},{"delta_pct":-13.8,"error_pct":0.0,"p95_during_ms":0.37759999999999994,"p95_pre_ms":0.4381999999999998,"service":"paymentservice","spans":968},{"delta_pct":13.7,"error_pct":0.0,"p95_during_ms":0.283,"p95_pre_ms":0.249,"service":"currencyservice","spans":56048},{"delta_pct":-4.0,"error_pct":0.0,"p95_during_ms":0.024,"p95_pre_ms":0.025,"service":"productcatalogservice","spans":100989},{"delta_pct":2.7,"error_pct":0.0,"p95_during_ms":0.42140000000000005,"p95_pre_ms":0.4101999999999999,"service":"emailservice","spans":1256}],"omitted_services":0,"service_count":7}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=3 omitted_edges=1
[{"evidence_source":"metric","onset_rel_s":732.0,"rank":1,"service":"currencyservice","severity_z":999.0},{"evidence_source":"trace","onset_rel_s":735.0,"rank":2,"service":"checkoutservice","severity_z":57.14},{"evidence_source":"trace","onset_rel_s":735.0,"rank":3,"service":"frontend","severity_z":44.147},{"evidence_source":"metric","onset_rel_s":766.8,"rank":4,"service":"frontend-external","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":781.8,"rank":5,"service":"cartservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1003.2,"rank":6,"service":"paymentservice","severity_z":63.431},{"evidence_source":"metric","onset_rel_s":1011.0,"rank":7,"service":"adservice","severity_z":15.042},{"evidence_source":"trace","onset_rel_s":1245.0,"rank":8,"service":"recommendationservice","severity_z":8.268},{"evidence_source":"metric","onset_rel_s":1261.8,"rank":9,"service":"productcatalogservice","severity_z":358.972},{"evidence_source":"metric","onset_rel_s":1279.8,"rank":10,"service":"gke-gke-cluster-default-pool-2e1807ce-w819","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1389.0,"rank":11,"service":"shippingservice","severity_z":26.629},{"evidence_source":"trace","onset_rel_s":1425.0,"rank":12,"service":"emailservice","severity_z":5.488},{"evidence_source":"none","onset_rel_s":null,"rank":13,"service":"gke-gke-cluster-default-pool-2e1807ce-cx8g","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":14,"service":"gke-gke-cluster-default-pool-2e1807ce-xte3","severity_z":0.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"currencyservice","caller":"checkoutservice"},{"callee":"emailservice","caller":"checkoutservice"},{"callee":"paymentservice","caller":"checkoutservice"},{"callee":"productcatalogservice","caller":"checkoutservice"},{"callee":"checkoutservice","caller":"frontend"},{"callee":"currencyservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"frontend"},{"callee":"recommendationservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"recommendationservice"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"high","reason":"Rank currencyservice first because currencyservice has direct container-memory-mapped-file evidence (signed-z 999, persistence 31 bins); although checkoutservice is salient, the caller path checkoutservice -> currencyservice means a disturbance in the callee can propagate back toward that caller-side symptom.","services":["currencyservice","checkoutservice"]}
