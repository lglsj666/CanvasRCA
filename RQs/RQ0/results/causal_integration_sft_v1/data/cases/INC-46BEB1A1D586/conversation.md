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
opaque_id: INC-46BEB1A1D586
observation_window={"duration_rel_s":1440.0,"source_metric_rows":1441}
selection_summary={"candidate_count":16,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":283,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","cartservice","checkoutservice","currencyservice","emailservice","frontend","frontend-external","gke-gke-cluster-default-pool-c49c2b06-crhc","gke-gke-cluster-default-pool-c49c2b06-d258","gke-gke-cluster-default-pool-c49c2b06-vlhn","loadgenerator","paymentservice","productcatalogservice","recommendationservice","redis","shippingservice"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[11.25,33.75,56.25,78.75,101.25,123.75,146.25,168.75,191.25,213.75,236.25,258.75,281.25,303.75,326.25,348.75,371.25,393.75,416.25,438.75,461.25,483.75,506.25,528.75,551.25,573.75,596.25,618.75,641.25,663.75,686.25,708.75,731.25,753.75,776.25,798.75,821.25,843.75,866.25,888.75,911.25,933.75,956.25,978.75,1001.25,1023.75,1046.25,1068.75,1091.25,1113.75,1136.25,1158.75,1181.25,1203.75,1226.25,1248.75,1271.25,1293.75,1316.25,1338.75,1361.25,1383.75,1406.25,1428.75]
[M1] rank=1 service=productcatalogservice metric=istio-latency-90 baseline=0.00438 peak=0.088291 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.004416,0.004471,0.004457,0.004364,0.004337,0.004358,0.004366,0.004395,0.004403,0.004387,0.004378,0.004389,0.004405,0.004408,0.004387,0.004383,0.004386,0.004368,0.004371,0.004365,0.004357,0.004343,0.004349,0.004374,0.004368,0.004354,0.004372,0.004382,0.004373,0.004368,0.004368,0.00437,0.004367,0.07752,0.087256,0.087698,0.086662,0.087431,0.08669,0.085522,0.086669,0.087277,0.088282,0.087177,0.08612,0.087335,0.086395,0.08732,0.087566,0.086298,0.087434,0.087545,0.08695,0.087238,0.086722,0.08647,0.08606,0.086815,0.088284,0.086667,0.085965,0.086925,0.085606,0.085774]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M2] rank=2 service=productcatalogservice metric=istio-latency-95 baseline=0.004709 peak=0.094324 signed_z=999.0 onset_bin=1 onset_rel_s=33.75 persistence_bins=33
values_compact=raw:[0.004735,0.004787,0.004777,0.004698,0.004676,0.004696,0.0047,0.004718,0.004724,0.004709,0.004701,0.004712,0.004725,0.004729,0.004716,0.004714,0.004713,0.004695,0.004699,0.004698,0.004691,0.004678,0.004682,0.004704,0.004699,0.004688,0.004702,0.004709,0.004702,0.0047,0.004704,0.004703,0.004699,0.08907,0.093829,0.093956,0.093438,0.093756,0.093388,0.092773,0.093368,0.093726,0.09426,0.093718,0.093155,0.093838,0.093361,0.093803,0.093997,0.093363,0.093858,0.093905,0.093593,0.093648,0.093472,0.093356,0.093065,0.093517,0.094321,0.093469,0.093053,0.093506,0.092828,0.092947]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M3] rank=3 service=gke-gke-cluster-default-pool-c49c2b06-vlhn metric=node-disk-reads-completed-total baseline=0.00963 peak=360.377778 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=delta:0.133333,-0.088889,-0.044444,0,0,0,0,0,0,0,0.022222,0,-0.022222,0,0,0.022222,0,-0.022222,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,180.222222,68.777778,104.2,-63.955556,-60.8,127.711112,-44.422223,46.288889,-0.622222,-85.311111,86.688889,-93.511111,-22.666667,114.022222,-64.577778,65.022223,1.555555,-49.511111,51.266667,-129.533334,12.355556,113.244444,-63.6,64.733334,-0.8,-24.555556,26.244445,-141.933334,87.911111,43.511112,-113.577778
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M4] rank=4 service=gke-gke-cluster-default-pool-c49c2b06-vlhn metric=node-disk-read-bytes-total baseline=554.097778 peak=47737514.666667 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=delta:9011.2,-7372.8,-1638.4,0,0,0,0,0,0,0,273.066667,0,-273.066667,0,0,1547.377778,0,-1547.377778,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,23860929.422222,9105134.933334,14109172.622222,-8458513.066667,-7957526.755555,17062661.688888,-6151645.866666,6151645.866666,0,-11327533.511111,11327533.511111,-12533395.911111,-2755424.711111,15288820.622222,-8572108.8,8572108.8,0,-6801180.444444,6801180.444444,-17059748.977777,1835008,15224740.977777,-8636188.444444,8636188.444444,6826.666667,-3515642.311111,3508815.644444,-18858712.177777,11557637.688889,5830155.377777,-15073280
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M5] rank=5 service=recommendationservice metric=istio-latency-90 baseline=0.009576 peak=0.093609 signed_z=788.468 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.009841,0.009848,0.009751,0.009554,0.00941,0.009466,0.009549,0.009667,0.009729,0.009706,0.00959,0.009606,0.009615,0.009621,0.009667,0.009528,0.009458,0.009474,0.009499,0.009526,0.009507,0.009462,0.009469,0.009653,0.009664,0.009517,0.009477,0.009493,0.009551,0.009514,0.009515,0.009543,0.009517,0.088494,0.092851,0.09311,0.092984,0.093323,0.09296,0.092002,0.092787,0.093568,0.09348,0.093282,0.09285,0.093015,0.092935,0.092824,0.092796,0.092911,0.09344,0.093513,0.093267,0.092938,0.092629,0.092771,0.09273,0.093031,0.093609,0.092568,0.092234,0.092862,0.092338,0.092438]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M6] rank=6 service=recommendationservice metric=istio-latency-50 baseline=0.007068 peak=0.0672 signed_z=476.136 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.007263,0.007273,0.00719,0.007048,0.006866,0.006986,0.007179,0.007271,0.007264,0.007227,0.007159,0.007178,0.007186,0.007149,0.007159,0.007028,0.006929,0.006914,0.006976,0.007105,0.007113,0.007016,0.006983,0.007016,0.007013,0.007071,0.006996,0.006883,0.00695,0.006933,0.006965,0.006915,0.006889,0.00988,0.064255,0.064873,0.064223,0.066613,0.064802,0.06001,0.062429,0.06528,0.06612,0.062321,0.060011,0.065077,0.064675,0.064119,0.063982,0.064555,0.0672,0.066966,0.065716,0.064692,0.063145,0.063855,0.063649,0.062859,0.065171,0.062064,0.061171,0.064312,0.06169,0.06142]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M7] rank=7 service=gke-gke-cluster-default-pool-c49c2b06-vlhn metric=node-memory-active-bytes baseline=47463.917037 peak=17756433.066667 signed_z=309.742 onset_bin=35 onset_rel_s=798.75 persistence_bins=2
values_compact=delta:303741.155556,-245213.866667,-11104.711111,728.177778,-2366.577778,11741.866666,-1638.4,-18659.555555,910.222222,-7554.844444,-3458.844445,10285.511111,1183.288889,-5006.222222,-2366.577778,-3003.733333,-91.022222,-2002.488889,4642.133333,2912.711111,-2275.555555,-2912.711111,-728.177778,3185.777778,34861.511111,-4642.133334,-37410.133333,-1547.377778,-2275.555555,-3640.888889,-182.044445,4642.133334,10467.555555,273.066667,-7463.822222,17732403.2,-3185.777778,-17736772.266667,546.133334,-1456.355556,1001.244444,-910.222222,-1547.377778,2366.577778,-455.111111,2639.644445,910.222222,-4278.044445,273.066667,182.044444,-1365.333333,-1274.311111,728.177778,-2548.622222,-455.111112,1274.311112,-637.155556,364.088889,819.2,637.155555,3276.8,-1001.244444,-4915.2,1365.333333
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M8] rank=8 service=gke-gke-cluster-default-pool-c49c2b06-vlhn metric=node-disk-written-bytes-total baseline=2524976.165926 peak=50483746.133333 signed_z=158.572 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=delta:3872995.555556,-1737432.177778,89747.911111,75184.355555,-78643.2,127067.022223,126884.977777,175035.733334,67902.577778,-254225.066667,-28398.933333,118784,-210352.355556,-10831.644444,114961.066666,416790.755556,66446.222222,-453381.688889,-66173.155555,-53248,-31311.644445,46057.244445,-10831.644445,310476.8,96392.533333,-446008.888888,-61531.022223,172396.088889,489699.555556,20297.955555,-527018.666666,219272.533333,1696472.177778,29653583.644444,14643655.111111,-3012198.4,3849784.888889,856792.177778,-7974365.866667,2172336.355556,-2720563.2,-359446.755556,5140297.955556,-4004977.777778,4820718.933333,1254923.377778,-5471982.933333,2694439.822222,-3191512.177778,-621681.777777,1706939.733333,-2791560.533333,7037110.044444,191783.822222,-6518192.355555,3333415.822222,-1849480.533333,512455.111111,724718.933333,-1288965.688889,6900849.777778,-4798327.466667,-1866046.577778,4585517.511112
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M9] rank=9 service=productcatalogservice metric=container-memory-cache baseline=2341745.777778 peak=120918016.0 signed_z=158.547 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=delta:4014080,0,0,0,0,0,-2007040,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,116768768,-2789376,1515520,3235840,-2076672,-36864,245760,-700416,-46821376,47546368,1601536,-3461120,233472,1490944,-434176,-30810112,31887360,-700416,1376256,491520,-266240,-2772992,1482752,-356352,1560576,-2138112,2506752,-3457024,3440640,-3674112,1159168,-1380352
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M10] rank=10 service=productcatalogservice metric=container-cpu-system-seconds-total baseline=1.026271 peak=13.082491 signed_z=103.209 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=delta:0.742227,0.184554,0.101392,0.079214,-0.047364,0,-0.259572,0.164188,0.110845,0.033009,-0.007403,-0.003646,0.098133,-0.091644,-0.063629,0.029397,-0.017497,-0.006632,-0.053635,0.038084,0.057278,0.035069,0.006273,-0.102258,-0.008531,0.103624,-0.063506,-0.062132,0.070558,0.055324,-0.028682,-0.072239,1.712387,4.595693,4.716796,-0.215216,0.73366,-0.214689,-0.391152,0.629384,0.309214,-0.409945,-0.976575,0.670052,-0.063977,0.3533,0.158095,-0.896798,0.622122,-0.000005,-0.10268,0.171252,-0.063923,-0.262087,0.558829,0.200714,-0.234274,-0.730323,0.309929,0.098494,-0.012345,-0.065454,-0.080014,0.17743
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M11] rank=11 service=productcatalogservice metric=istio-latency-99 baseline=0.005236 peak=0.099309 signed_z=85.937 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.00499,0.009687,0.007933,0.004966,0.004948,0.004966,0.004966,0.004976,0.004982,0.004966,0.004959,0.004971,0.004981,0.004986,0.004981,0.004978,0.004975,0.004957,0.004962,0.004963,0.004958,0.004947,0.004947,0.004967,0.004964,0.004956,0.004966,0.004971,0.004965,0.004965,0.004972,0.004969,0.004965,0.098311,0.099087,0.098963,0.098859,0.098837,0.098746,0.098575,0.098727,0.098885,0.099043,0.098958,0.098783,0.09904,0.098934,0.09899,0.09914,0.099016,0.098998,0.098993,0.098907,0.098778,0.098872,0.098865,0.098669,0.098879,0.09915,0.09891,0.098724,0.098772,0.098606,0.098684]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M12] rank=12 service=productcatalogservice metric=istio-latency-50 baseline=0.00175 peak=0.007592 signed_z=77.216 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.001864,0.001942,0.001901,0.001691,0.001625,0.001659,0.001702,0.001812,0.001829,0.001814,0.001791,0.001802,0.001843,0.001836,0.001751,0.001743,0.001769,0.001747,0.001745,0.001704,0.001686,0.00166,0.00169,0.001742,0.001718,0.001675,0.001734,0.001762,0.001745,0.001712,0.001684,0.001707,0.001711,0.003231,0.004825,0.006549,0.004861,0.005344,0.004776,0.004425,0.00479,0.005108,0.007564,0.004873,0.004671,0.004982,0.004738,0.005251,0.005251,0.004598,0.004867,0.005213,0.004863,0.004966,0.004785,0.0047,0.00462,0.004671,0.005191,0.004574,0.004397,0.004774,0.004581,0.004587]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[710.0,1440.0]

=== LOG SUMMARY ===
{"entries":[{"change_pct":50.0,"n_during":15,"n_pre":10,"service":"redis"},{"change_pct":8.1,"n_during":1086,"n_pre":1005,"service":"checkoutservice"},{"change_pct":8.1,"n_during":362,"n_pre":335,"service":"emailservice"},{"change_pct":8.1,"n_during":724,"n_pre":670,"service":"paymentservice"},{"change_pct":-1.3,"n_during":27488,"n_pre":27857,"service":"currencyservice"},{"change_pct":-1.0,"n_during":31198,"n_pre":31528,"service":"frontend"},{"change_pct":0.8,"n_during":5386,"n_pre":5342,"service":"shippingservice"},{"change_pct":-0.5,"n_during":5280,"n_pre":5308,"service":"adservice"}],"mode":"volume","omitted_services":2,"service_count":10}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":1466.0,"error_pct":0.0,"p95_during_ms":82.22214999999998,"p95_pre_ms":5.250349999999998,"service":"recommendationservice","spans":27214},{"delta_pct":228.4,"error_pct":0.0,"p95_during_ms":214.89994999999863,"p95_pre_ms":65.43909999999991,"service":"frontend","spans":203719},{"delta_pct":54.1,"error_pct":0.0,"p95_during_ms":118.70664999999995,"p95_pre_ms":77.02350000000001,"service":"checkoutservice","spans":9368},{"delta_pct":24.0,"error_pct":0.0,"p95_during_ms":0.031,"p95_pre_ms":0.025,"service":"productcatalogservice","spans":101785},{"delta_pct":11.1,"error_pct":0.0,"p95_during_ms":0.24,"p95_pre_ms":0.216,"service":"currencyservice","spans":55632},{"delta_pct":10.3,"error_pct":0.0,"p95_during_ms":1.5851499999999978,"p95_pre_ms":1.437199999999999,"service":"paymentservice","spans":985},{"delta_pct":-1.1,"error_pct":0.0,"p95_during_ms":0.44135,"p95_pre_ms":0.44610000000000005,"service":"emailservice","spans":1273}],"omitted_services":0,"service_count":7}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=2 omitted_edges=1
[{"evidence_source":"trace","onset_rel_s":735.0,"rank":1,"service":"recommendationservice","severity_z":151.414},{"evidence_source":"trace","onset_rel_s":735.0,"rank":2,"service":"frontend","severity_z":27.375},{"evidence_source":"metric","onset_rel_s":736.8,"rank":3,"service":"productcatalogservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":753.0,"rank":4,"service":"gke-gke-cluster-default-pool-c49c2b06-vlhn","severity_z":999.0},{"evidence_source":"trace","onset_rel_s":795.0,"rank":5,"service":"checkoutservice","severity_z":7.873},{"evidence_source":"metric","onset_rel_s":820.2,"rank":6,"service":"cartservice","severity_z":14.503},{"evidence_source":"metric","onset_rel_s":1350.0,"rank":7,"service":"gke-gke-cluster-default-pool-c49c2b06-crhc","severity_z":39.401},{"evidence_source":"metric","onset_rel_s":1371.0,"rank":8,"service":"shippingservice","severity_z":62.571},{"evidence_source":"none","onset_rel_s":null,"rank":9,"service":"emailservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":10,"service":"adservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":11,"service":"paymentservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":12,"service":"gke-gke-cluster-default-pool-c49c2b06-d258","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":13,"service":"redis","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":14,"service":"currencyservice","severity_z":0.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"currencyservice","caller":"checkoutservice"},{"callee":"emailservice","caller":"checkoutservice"},{"callee":"paymentservice","caller":"checkoutservice"},{"callee":"productcatalogservice","caller":"checkoutservice"},{"callee":"checkoutservice","caller":"frontend"},{"callee":"currencyservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"frontend"},{"callee":"recommendationservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"recommendationservice"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"high","reason":"Rank productcatalogservice first because productcatalogservice has direct istio-latency-90 evidence (signed-z 999, persistence 31 bins); although recommendationservice is salient, the caller path recommendationservice -> productcatalogservice means a disturbance in the callee can propagate back toward that caller-side symptom.","services":["productcatalogservice","recommendationservice"]}
