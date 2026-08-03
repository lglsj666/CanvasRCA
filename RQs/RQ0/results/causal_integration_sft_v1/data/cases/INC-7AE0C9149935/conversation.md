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
opaque_id: INC-7AE0C9149935
observation_window={"duration_rel_s":1440.0,"source_metric_rows":1441}
selection_summary={"candidate_count":17,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":271,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","cartservice","checkoutservice","currencyservice","emailservice","frontend","frontend-external","gke-gke-cluster-default-pool-2e1807ce-0e4z","gke-gke-cluster-default-pool-2e1807ce-cx8g","gke-gke-cluster-default-pool-2e1807ce-w819","gke-gke-cluster-default-pool-2e1807ce-xte3","loadgenerator","paymentservice","productcatalogservice","recommendationservice","redis","shippingservice"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[11.25,33.75,56.25,78.75,101.25,123.75,146.25,168.75,191.25,213.75,236.25,258.75,281.25,303.75,326.25,348.75,371.25,393.75,416.25,438.75,461.25,483.75,506.25,528.75,551.25,573.75,596.25,618.75,641.25,663.75,686.25,708.75,731.25,753.75,776.25,798.75,821.25,843.75,866.25,888.75,911.25,933.75,956.25,978.75,1001.25,1023.75,1046.25,1068.75,1091.25,1113.75,1136.25,1158.75,1181.25,1203.75,1226.25,1248.75,1271.25,1293.75,1316.25,1338.75,1361.25,1383.75,1406.25,1428.75]
[M1] rank=1 service=productcatalogservice metric=container-memory-failures-total baseline=38.320073 peak=15576.661734 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=delta:44.32541,5.822935,-18.776377,2.106796,4.135184,8.936455,4.510483,-12.551648,3.744002,-1.125069,-7.114353,11.948915,-3.630573,-2.626595,-7.702597,-8.996617,10.557938,-0.633763,5.734557,20.317091,1.259957,-3.751071,-29.340893,7.155626,13.98137,-4.124573,-10.347057,0.152708,-2.239056,0.130698,-3.912396,-13.000008,5.569767,9690.935512,4971.280101,601.34543,-381.944988,-483.372169,484.844525,661.014887,-1004.938846,-18.323382,123.396622,-297.941207,-282.781559,332.568642,583.204095,313.02648,9.404723,-459.447182,-125.448008,-207.189229,129.843326,308.273951,17.658932,144.18627,-106.129582,-643.974521,350.176068,332.693361,15.260743,-218.081251,-615.360329,0
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M2] rank=2 service=productcatalogservice metric=container-memory-mapped-file baseline=0.0 peak=2220032.0 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=rle:0*33,2220032*31
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M3] rank=3 service=recommendationservice metric=container-memory-rss baseline=42578153.244444 peak=85032960.0 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=delta:42565632,0,8192,-4096,4096,0,-20480,-45056,24576,0,49152,0,-4096,-16384,16384,0,0,4096,12288,4096,-8192,8192,-122880,143360,-16384,16384,0,-4096,-12288,-4096,12288,-4096,69632,86016,200704,65536,4096,0,40960,-20480,65536,98304,2125824,38641664,204800,315392,-114688,208896,-4096,221184,-20480,0,131072,-131072,167936,-43032576,-352256,438272,61440,-61440,-65536,223232,-145408,180224
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M4] rank=4 service=productcatalogservice metric=istio-error-total baseline=0.0 peak=0.533 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=rle:0*42,0.533*1,0*21
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M5] rank=5 service=productcatalogservice metric=istio-latency-50 baseline=0.002336 peak=0.077426 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.002233,0.002378,0.002369,0.002284,0.002323,0.002334,0.002301,0.002329,0.00239,0.002397,0.002392,0.002249,0.00219,0.002207,0.002243,0.002373,0.002423,0.002409,0.002431,0.002403,0.002368,0.002407,0.002373,0.002355,0.002327,0.002308,0.002359,0.0023,0.002275,0.002358,0.002347,0.002309,0.002339,0.003616,0.070183,0.073353,0.072018,0.071815,0.068541,0.067859,0.068081,0.072622,0.07709,0.075955,0.073196,0.071611,0.073006,0.072096,0.072304,0.07535,0.076249,0.073764,0.072172,0.073203,0.071037,0.073308,0.073752,0.070493,0.067946,0.06613,0.065581,0.067969,0.068507,0.068313]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M6] rank=6 service=recommendationservice metric=istio-latency-50 baseline=0.007549 peak=0.902778 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.007599,0.007632,0.00753,0.00749,0.007547,0.007554,0.007516,0.007623,0.007629,0.007535,0.007507,0.007459,0.007394,0.007411,0.007531,0.007636,0.007626,0.007584,0.007573,0.007527,0.007549,0.007568,0.007497,0.007532,0.007569,0.00761,0.007709,0.007582,0.007503,0.007566,0.007536,0.007489,0.007526,0.008442,0.193307,0.187931,0.181711,0.180773,0.160714,0.14726,0.151618,0.157407,0.654412,0.852904,0.178777,0.178774,0.169328,0.142233,0.152174,0.184483,0.205252,0.194344,0.1924,0.171341,0.147482,0.170982,0.146646,0.119173,0.150704,0.162501,0.169566,0.184449,0.208948,0.187044]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M7] rank=7 service=productcatalogservice metric=istio-latency-90 baseline=0.004503 peak=1.803224 signed_z=999.0 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=raw:[0.004495,0.004528,0.004498,0.004479,0.004492,0.004489,0.004488,0.004505,0.004526,0.004519,0.004511,0.004472,0.004453,0.004461,0.004476,0.004501,0.004514,0.004512,0.004511,0.004503,0.004511,0.004515,0.004501,0.004513,0.004506,0.004504,0.00453,0.004509,0.004524,0.004551,0.004515,0.0045,0.004577,0.099616,1.56832,1.657447,1.608647,1.583236,1.543985,1.453932,1.472678,1.677683,1.776332,1.757144,1.637975,1.602795,1.682374,1.644955,1.633152,1.663797,1.637917,1.549668,1.597878,1.668082,1.639916,1.622271,1.613965,1.680638,1.702893,1.614373,1.459996,1.509206,1.599136,1.55525]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M8] rank=8 service=recommendationservice metric=istio-latency-90 baseline=0.009754 peak=2.195431 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.009873,0.009926,0.0097,0.009632,0.009704,0.009718,0.009657,0.009854,0.009899,0.009714,0.009704,0.009684,0.009586,0.009582,0.009732,0.009906,0.009833,0.009774,0.009791,0.009714,0.009752,0.009755,0.009643,0.009743,0.009814,0.009842,0.009965,0.009815,0.009721,0.009788,0.009707,0.00966,0.009831,0.874963,2.104061,2.076087,1.999695,1.98872,1.925385,1.948467,1.840789,1.845946,2.168883,2.191033,2.090909,2.075291,2.051807,2.002041,1.882052,1.995172,2.112042,2.08637,2.083333,2.055143,1.98494,2.021084,2.023248,1.927965,2.047656,2.036267,1.989405,2.057584,2.133824,2.061471]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M9] rank=9 service=productcatalogservice metric=istio-latency-95 baseline=0.004774 peak=2.176494 signed_z=999.0 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=raw:[0.004777,0.004797,0.004764,0.004754,0.004763,0.004759,0.004761,0.004777,0.004793,0.004784,0.004775,0.00475,0.004735,0.004743,0.004756,0.004766,0.004776,0.004775,0.004771,0.004765,0.004779,0.004779,0.004769,0.004783,0.00478,0.004779,0.004801,0.004786,0.004805,0.004825,0.004786,0.004774,0.004857,1.194752,2.03416,2.078723,2.054324,2.041618,2.021993,1.976966,1.986339,2.088841,2.138166,2.128572,2.077294,2.05955,2.091187,2.072478,2.068894,2.084185,2.068958,2.027326,2.05012,2.0856,2.07521,2.063812,2.056982,2.154828,2.173347,2.064141,1.981387,2.007113,2.05065,2.027625]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M10] rank=10 service=productcatalogservice metric=istio-latency-99 baseline=0.005276 peak=3.364224 signed_z=999.0 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=raw:[0.005077,0.005922,0.004978,0.004973,0.004979,0.004974,0.00498,0.004995,0.005495,0.004997,0.004986,0.004972,0.00496,0.004968,0.004981,0.00498,0.004985,0.004985,0.004979,0.004975,0.004992,0.00499,0.004983,0.004999,0.004999,0.004998,0.006325,0.005564,0.006959,0.007798,0.00528,0.004994,0.0605,2.23895,2.406832,2.415745,2.410865,2.408324,2.404399,2.395393,2.397268,2.417768,2.427633,2.425969,2.426696,2.423931,2.421096,2.414496,2.416894,2.420496,2.415246,2.409452,2.41308,2.417911,2.423445,2.421664,2.411396,3.148066,3.36121,2.423956,2.3985,2.405438,2.411862,2.405525]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M11] rank=11 service=recommendationservice metric=istio-latency-95 baseline=0.01209 peak=2.351523 signed_z=948.982 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.01535,0.016383,0.009971,0.009899,0.009974,0.009989,0.009924,0.015292,0.015869,0.009987,0.009979,0.009962,0.00986,0.009853,0.010366,0.016011,0.014241,0.012279,0.012957,0.009988,0.011383,0.011411,0.00991,0.011446,0.0151,0.014687,0.01719,0.013791,0.009998,0.01291,0.009979,0.009933,0.017547,1.744641,2.30203,2.288043,2.249848,2.24468,2.224231,2.238474,2.176974,2.174871,2.338431,2.349276,2.3125,2.305087,2.275904,2.25102,2.191026,2.247586,2.306021,2.293185,2.291667,2.277571,2.24247,2.260542,2.261624,2.252117,2.344141,2.299822,2.244702,2.278792,2.316912,2.280735]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M12] rank=12 service=recommendationservice metric=container-memory-usage-bytes baseline=45334869.333333 peak=90517504.0 signed_z=937.755 onset_bin=25 onset_rel_s=573.75 persistence_bins=33
values_compact=delta:45309952,-4096,16384,-12288,8192,4096,-20480,-43008,149504,0,-90112,8192,0,-20480,16384,4096,0,0,16384,4096,-12288,12288,-122880,139264,-12288,147456,0,-139264,-8192,-4096,4096,0,69632,77824,217088,57344,16384,0,28672,-24576,73728,98304,2670592,40816640,212992,319488,-118784,212992,-4096,229376,-28672,0,131072,-139264,172032,-45785088,-348160,442368,53248,-49152,-73728,217088,-135168,172032
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[713.0,1440.0]

=== LOG SUMMARY ===
{"entries":[{"error_logs":46,"error_pct":0.09,"service":"frontend","total_logs":49891}],"mode":"errors","omitted_services":9,"service_count":10}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":40694.2,"error_pct":0.0,"p95_during_ms":2207.7418000000002,"p95_pre_ms":5.4118999999999975,"service":"recommendationservice","spans":21420},{"delta_pct":1152.3,"error_pct":0.0,"p95_during_ms":2568.695,"p95_pre_ms":205.1157999999998,"service":"frontend","spans":161499},{"delta_pct":678.5,"error_pct":0.0,"p95_during_ms":1695.7618,"p95_pre_ms":217.83549999999997,"service":"checkoutservice","spans":7372},{"delta_pct":12.9,"error_pct":0.0,"p95_during_ms":0.44509999999999983,"p95_pre_ms":0.39419999999999994,"service":"emailservice","spans":1101},{"delta_pct":-3.8,"error_pct":0.0,"p95_during_ms":0.025,"p95_pre_ms":0.026,"service":"productcatalogservice","spans":80203},{"delta_pct":-1.6,"error_pct":0.0,"p95_during_ms":0.187,"p95_pre_ms":0.19,"service":"currencyservice","spans":44677},{"delta_pct":0.4,"error_pct":0.0,"p95_during_ms":0.335,"p95_pre_ms":0.33359999999999995,"service":"paymentservice","spans":813}],"omitted_services":0,"service_count":7}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=3 omitted_edges=2
[{"evidence_source":"trace","onset_rel_s":735.0,"rank":1,"service":"recommendationservice","severity_z":999.0},{"evidence_source":"trace","onset_rel_s":735.0,"rank":2,"service":"frontend","severity_z":137.777},{"evidence_source":"trace","onset_rel_s":735.0,"rank":3,"service":"checkoutservice","severity_z":37.258},{"evidence_source":"metric","onset_rel_s":748.8,"rank":4,"service":"productcatalogservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":748.8,"rank":5,"service":"gke-gke-cluster-default-pool-2e1807ce-cx8g","severity_z":45.207},{"evidence_source":"metric","onset_rel_s":760.8,"rank":6,"service":"adservice","severity_z":76.459},{"evidence_source":"metric","onset_rel_s":765.0,"rank":7,"service":"gke-gke-cluster-default-pool-2e1807ce-0e4z","severity_z":15.593},{"evidence_source":"metric","onset_rel_s":769.8,"rank":8,"service":"gke-gke-cluster-default-pool-2e1807ce-xte3","severity_z":13.969},{"evidence_source":"metric","onset_rel_s":835.8,"rank":9,"service":"shippingservice","severity_z":55.474},{"evidence_source":"metric","onset_rel_s":942.0,"rank":10,"service":"paymentservice","severity_z":82.502},{"evidence_source":"metric","onset_rel_s":966.0,"rank":11,"service":"gke-gke-cluster-default-pool-2e1807ce-w819","severity_z":13.102},{"evidence_source":"metric","onset_rel_s":1000.8,"rank":12,"service":"cartservice","severity_z":263.543},{"evidence_source":"metric","onset_rel_s":1006.2,"rank":13,"service":"emailservice","severity_z":36.481},{"evidence_source":"metric","onset_rel_s":1405.2,"rank":14,"service":"currencyservice","severity_z":333.333}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"currencyservice","caller":"checkoutservice"},{"callee":"emailservice","caller":"checkoutservice"},{"callee":"paymentservice","caller":"checkoutservice"},{"callee":"productcatalogservice","caller":"checkoutservice"},{"callee":"checkoutservice","caller":"frontend"},{"callee":"currencyservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"frontend"},{"callee":"recommendationservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"recommendationservice"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"high","reason":"Rank productcatalogservice first because productcatalogservice has direct container-memory-failures-total evidence (signed-z 999, persistence 31 bins); although recommendationservice is salient, the caller path recommendationservice -> productcatalogservice means a disturbance in the callee can propagate back toward that caller-side symptom.","services":["productcatalogservice","recommendationservice"]}
