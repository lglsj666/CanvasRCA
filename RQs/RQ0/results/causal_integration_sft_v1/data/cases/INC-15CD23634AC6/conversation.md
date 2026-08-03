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
opaque_id: INC-15CD23634AC6
observation_window={"duration_rel_s":1440.0,"source_metric_rows":1441}
selection_summary={"candidate_count":17,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":261,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","cartservice","checkoutservice","currencyservice","emailservice","frontend","frontend-external","gke-gke-cluster-default-pool-2e1807ce-0e4z","gke-gke-cluster-default-pool-2e1807ce-cx8g","gke-gke-cluster-default-pool-2e1807ce-w819","gke-gke-cluster-default-pool-2e1807ce-xte3","loadgenerator","paymentservice","productcatalogservice","recommendationservice","redis","shippingservice"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[11.25,33.75,56.25,78.75,101.25,123.75,146.25,168.75,191.25,213.75,236.25,258.75,281.25,303.75,326.25,348.75,371.25,393.75,416.25,438.75,461.25,483.75,506.25,528.75,551.25,573.75,596.25,618.75,641.25,663.75,686.25,708.75,731.25,753.75,776.25,798.75,821.25,843.75,866.25,888.75,911.25,933.75,956.25,978.75,1001.25,1023.75,1046.25,1068.75,1091.25,1113.75,1136.25,1158.75,1181.25,1203.75,1226.25,1248.75,1271.25,1293.75,1316.25,1338.75,1361.25,1383.75,1406.25,1428.75]
[M1] rank=1 service=emailservice metric=istio-latency-50 baseline=0.003017 peak=0.123684 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=rle:0.003059*1,0.003069*1,0.003*1,0.003038*1,0.003063*1,0.003*1,0.003034*1,0.003032*1,0.003*6,0.003071*1,0.003054*3,0.003*15,0.003625*1,0.117308*1,0.113043*1,0.00492*1,0.00481*1,0.005*2,0.004909*1,0.0049*1,0.004895*1,0.004875*1,0.109375*1,0.1125*1,0.004765*1,0.004889*1,0.104688*1,0.005*1,0.108333*1,0.005*1,0.00476*1,0.104412*1,0.105357*1,0.0048*1,0.005*1,0.10625*1,0.004846*1,0.005*1,0.004917*1,0.102679*2,0.01*1
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M2] rank=2 service=paymentservice metric=istio-latency-50 baseline=0.003257 peak=0.125 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.003118,0.00316,0.003178,0.003236,0.003286,0.003164,0.003222,0.003228,0.003233,0.003308,0.00324,0.003343,0.003278,0.003087,0.003154,0.003105,0.003158,0.003323,0.003345,0.003406,0.003462,0.003267,0.003273,0.003188,0.003071,0.003467,0.003538,0.003195,0.003154,0.003236,0.003424,0.003261,0.003051,0.003611,0.01,0.009375,0.005,0.0564,0.075,0.1,0.103571,0.0049,0.005,0.005,0.004889,0.104167,0.005,0.005,0.104688,0.004833,0.005,0.01,0.0075,0.104167,0.105,0.005,0.005,0.005,0.100003,0.005,0.004917,0.005,0.025,0.005]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M3] rank=3 service=emailservice metric=istio-latency-90 baseline=0.00463 peak=0.224737 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=rle:0.004706*1,0.004724*1,0.0046*1,0.004669*1,0.004712*1,0.0046*1,0.004662*1,0.004658*1,0.0046*6,0.004729*1,0.004697*3,0.0046*15,0.187*1,0.223462*1,0.222609*1,0.219375*1,0.218421*1,0.22*2,0.219286*1,0.219211*1,0.219167*1,0.219*1,0.221875*1,0.2225*1,0.218*1,0.219118*1,0.220938*1,0.22*1,0.221667*1,0.22*1,0.217955*1,0.220882*1,0.221071*1,0.218333*1,0.22*1,0.22125*1,0.21875*1,0.22*1,0.219348*1,0.220536*2,0.22*1
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M4] rank=4 service=shippingservice metric=istio-latency-90 baseline=0.004629 peak=0.1561 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.004644,0.00467,0.004654,0.004616,0.004593,0.004605,0.004623,0.00461,0.004649,0.004678,0.004647,0.004684,0.004663,0.004608,0.004622,0.004614,0.004605,0.004642,0.004672,0.004661,0.004656,0.004633,0.00458,0.004585,0.004618,0.004631,0.004604,0.004653,0.004649,0.004594,0.004587,0.004572,0.004586,0.004742,0.0095,0.147609,0.14337,0.130395,0.131538,0.138152,0.13,0.120132,0.11,0.103,0.126029,0.120417,0.004969,0.007,0.00525,0.004905,0.121667,0.154,0.142333,0.1275,0.105323,0.00875,0.106486,0.004972,0.004973,0.122143,0.13163,0.151429,0.151842,0.135581]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M5] rank=5 service=emailservice metric=istio-latency-95 baseline=0.004831 peak=0.237368 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=rle:0.004912*1,0.004931*1,0.0048*1,0.004873*1,0.004919*1,0.0048*1,0.004866*1,0.004861*1,0.0048*6,0.004936*1,0.004903*3,0.0048*15,0.2185*1,0.236731*1,0.236304*1,0.234687*1,0.234211*1,0.235*2,0.234643*1,0.234605*1,0.234583*1,0.2345*1,0.235937*1,0.23625*1,0.234*1,0.234559*1,0.235469*1,0.235*1,0.235833*1,0.235*1,0.233977*1,0.235441*1,0.235536*1,0.234167*1,0.235*1,0.235625*1,0.234375*1,0.235*1,0.234674*1,0.235268*2,0.235*1
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M6] rank=6 service=shippingservice metric=istio-latency-95 baseline=0.004842 peak=0.20305 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.004857,0.004888,0.00487,0.004832,0.004811,0.00482,0.004838,0.004822,0.004864,0.004893,0.004859,0.004896,0.004873,0.004818,0.004831,0.004827,0.004815,0.004851,0.004883,0.004872,0.004872,0.004848,0.004797,0.004799,0.00483,0.004845,0.004815,0.004864,0.004856,0.004803,0.0048,0.004793,0.004806,0.004965,0.174464,0.198804,0.196685,0.190197,0.190769,0.194076,0.19,0.185066,0.18,0.1765,0.188015,0.185208,0.166983,0.173015,0.169677,0.151477,0.185833,0.202,0.196167,0.18875,0.177661,0.17379,0.178243,0.156875,0.157187,0.186071,0.190815,0.200714,0.200921,0.192791]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M7] rank=7 service=adservice metric=istio-latency-99 baseline=0.004984 peak=0.072542 signed_z=999.0 onset_bin=34 onset_rel_s=776.25 persistence_bins=4
values_compact=delta:0.004983,-0.000006,-0.000006,-0.000005,-0.000006,0.000006,0,-0.000006,0,0.000012,0,-0.000006,0.000384,-0.000353,-0.000037,0,0.000006,-0.000001,0.000006,0,-0.000011,0.000006,0.000025,-0.000002,-0.000018,0.000001,0.000006,-0.000001,0.000007,-0.000006,-0.000012,0,-0.000006,0.000006,0.062584,0.004992,-0.060892,-0.006672,0.000001,0.000342,-0.000325,-0.000019,-0.000005,-0.000006,0.000018,0.000007,-0.000018,-0.000007,-0.000006,0.000006,0,0,0,-0.000006,0,0,0.000018,0,-0.000012,0.000007,-0.000007,0.000005,0.000001,-0.000012
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M8] rank=8 service=productcatalogservice metric=istio-latency-99 baseline=0.004964 peak=0.127778 signed_z=999.0 onset_bin=35 onset_rel_s=798.75 persistence_bins=16
values_compact=raw:[0.004961,0.004954,0.004946,0.004941,0.004991,0.005314,0.004965,0.004953,0.004948,0.004951,0.004948,0.004947,0.004952,0.004956,0.004953,0.004959,0.004964,0.004956,0.004954,0.004951,0.004949,0.004951,0.004946,0.004944,0.004947,0.004951,0.004985,0.004981,0.004945,0.004943,0.004945,0.004953,0.00496,0.00496,0.004975,0.005694,0.008788,0.0058,0.008212,0.009456,0.004998,0.004992,0.004998,0.00499,0.005624,0.006257,0.004987,0.004991,0.004989,0.004989,0.102648,0.122176,0.005739,0.004994,0.004982,0.004984,0.00499,0.00498,0.007323,0.009982,0.009054,0.109182,0.1245,0.008982]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M9] rank=9 service=checkoutservice metric=istio-latency-90 baseline=0.223568 peak=4.818182 signed_z=550.61 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.223,0.217353,0.225,0.224355,0.208462,0.214706,0.222273,0.219,0.21325,0.218125,0.226316,0.236071,0.238103,0.22375,0.218333,0.231786,0.23125,0.2275,0.225455,0.228125,0.237368,0.228,0.21475,0.220714,0.222,0.214545,0.218235,0.2248,0.2242,0.234444,0.235,0.210769,0.222857,2.25625,4.125,4.375,4.454545,4.460526,4.441176,4.489583,4.359375,4.15,4.486111,4.5,4.75,4.729167,4.558824,4.555556,4.546875,4.625,4.604167,4.509615,4.454545,4.527778,4.5,4.433333,4.5,4.519231,4.59375,4.52381,4.427083,4.554688,4.583333,4.5]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M10] rank=10 service=checkoutservice metric=istio-latency-95 baseline=0.241382 peak=6.5 signed_z=450.516 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.2365,0.233676,0.2375,0.237177,0.229231,0.232353,0.236136,0.2345,0.231625,0.234063,0.238158,0.245714,0.25625,0.243125,0.2425,0.26875,0.24375,0.23875,0.237727,0.239063,0.275,0.249,0.232375,0.235357,0.236,0.232273,0.234118,0.2374,0.2371,0.2479,0.249318,0.230385,0.236429,2.471875,4.5625,4.6875,4.727273,4.730263,4.720588,4.744792,4.679688,4.575,4.743056,4.75,5.875,5.875,4.779412,4.777778,4.773438,4.8125,4.802083,4.754808,4.727273,4.763889,4.75,4.716667,4.75,4.759615,4.796875,4.761905,4.713542,4.777344,4.791667,4.75]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M11] rank=11 service=paymentservice metric=istio-latency-90 baseline=0.005788 peak=0.228333 signed_z=216.749 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.004812,0.004888,0.00492,0.005287,0.006,0.004896,0.005,0.005236,0.0052,0.00625,0.005333,0.006583,0.0059,0.004757,0.004877,0.004789,0.004884,0.0064,0.0066,0.007024,0.007333,0.00575,0.005833,0.004939,0.004729,0.00825,0.0087,0.005029,0.004877,0.005467,0.007143,0.00568,0.004692,0.185499,0.22,0.219674,0.22,0.220414,0.225833,0.225455,0.220714,0.219211,0.22,0.22,0.219118,0.220833,0.22,0.22,0.220938,0.218636,0.22,0.22,0.219318,0.220833,0.221,0.22,0.22,0.22,0.220001,0.22,0.219347,0.22,0.22,0.218571]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M12] rank=12 service=emailservice metric=istio-latency-99 baseline=0.005888 peak=0.247474 signed_z=170.989 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=rle:0.00825*1,0.0085*1,0.00496*1,0.00735*1,0.00835*1,0.00496*1,0.00705*1,0.00685*1,0.00496*6,0.00855*1,0.0081*3,0.00496*15,0.2437*1,0.247346*1,0.247261*1,0.246938*1,0.246842*1,0.247*2,0.246929*1,0.246921*1,0.246917*1,0.2469*1,0.247187*1,0.24725*1,0.2468*1,0.246912*1,0.247094*1,0.247*1,0.247167*1,0.247*1,0.246795*1,0.247088*1,0.247107*1,0.246833*1,0.247*1,0.247125*1,0.246875*1,0.247*1,0.246935*1,0.247054*2,0.247*1
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[728.0,1440.0]

=== LOG SUMMARY ===
{"entries":[{"change_pct":-5.6,"n_during":6430,"n_pre":6808,"service":"recommendationservice"},{"change_pct":-5.4,"n_during":5158,"n_pre":5453,"service":"adservice"},{"change_pct":-4.7,"n_during":8837,"n_pre":9273,"service":"cartservice"},{"change_pct":-4.3,"n_during":5122,"n_pre":5350,"service":"shippingservice"},{"change_pct":-4.2,"n_during":30677,"n_pre":32009,"service":"frontend"},{"change_pct":-3.8,"n_during":27811,"n_pre":28901,"service":"currencyservice"},{"change_pct":-3.2,"n_during":304,"n_pre":314,"service":"emailservice"},{"change_pct":-2.9,"n_during":610,"n_pre":628,"service":"paymentservice"}],"mode":"volume","omitted_services":2,"service_count":10}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":2366.9,"error_pct":0.0,"p95_during_ms":1910.1390000000001,"p95_pre_ms":77.42944999999993,"service":"checkoutservice","spans":8770},{"delta_pct":5.4,"error_pct":0.0,"p95_during_ms":0.3976999999999999,"p95_pre_ms":0.3771999999999998,"service":"paymentservice","spans":907},{"delta_pct":-1.7,"error_pct":0.0,"p95_during_ms":4.474,"p95_pre_ms":4.5515,"service":"recommendationservice","spans":27052},{"delta_pct":-1.5,"error_pct":0.0,"p95_during_ms":0.241,"p95_pre_ms":0.2446999999999971,"service":"currencyservice","spans":56999},{"delta_pct":0.4,"error_pct":0.0,"p95_during_ms":68.3185,"p95_pre_ms":68.039,"service":"frontend","spans":205412},{"delta_pct":-0.3,"error_pct":0.0,"p95_during_ms":0.41564999999999985,"p95_pre_ms":0.417,"service":"emailservice","spans":1194},{"delta_pct":0.0,"error_pct":0.0,"p95_during_ms":0.024,"p95_pre_ms":0.024,"service":"productcatalogservice","spans":102120}],"omitted_services":0,"service_count":7}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=3 omitted_edges=0
[{"evidence_source":"trace","onset_rel_s":735.0,"rank":1,"service":"checkoutservice","severity_z":259.543},{"evidence_source":"metric","onset_rel_s":766.8,"rank":2,"service":"emailservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":766.8,"rank":3,"service":"paymentservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":775.2,"rank":4,"service":"adservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":775.2,"rank":5,"service":"frontend","severity_z":21.595},{"evidence_source":"metric","onset_rel_s":781.8,"rank":6,"service":"shippingservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":781.8,"rank":7,"service":"cartservice","severity_z":164.852},{"evidence_source":"metric","onset_rel_s":781.8,"rank":8,"service":"currencyservice","severity_z":111.682},{"evidence_source":"metric","onset_rel_s":840.0,"rank":9,"service":"gke-gke-cluster-default-pool-2e1807ce-xte3","severity_z":20.727},{"evidence_source":"metric","onset_rel_s":871.8,"rank":10,"service":"productcatalogservice","severity_z":999.0},{"evidence_source":"none","onset_rel_s":null,"rank":11,"service":"gke-gke-cluster-default-pool-2e1807ce-cx8g","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":12,"service":"gke-gke-cluster-default-pool-2e1807ce-0e4z","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":13,"service":"redis","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":14,"service":"gke-gke-cluster-default-pool-2e1807ce-w819","severity_z":0.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"currencyservice","caller":"checkoutservice"},{"callee":"emailservice","caller":"checkoutservice"},{"callee":"paymentservice","caller":"checkoutservice"},{"callee":"productcatalogservice","caller":"checkoutservice"},{"callee":"checkoutservice","caller":"frontend"},{"callee":"currencyservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"frontend"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"high","reason":"Rank checkoutservice first because checkoutservice has direct istio-latency-90 evidence (signed-z 550.61, persistence 31 bins); although frontend is salient, the caller path frontend -> checkoutservice means a disturbance in the callee can propagate back toward that caller-side symptom.","services":["checkoutservice","frontend"]}
