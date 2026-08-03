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
opaque_id: INC-00F0B461C477
observation_window={"duration_rel_s":1440.0,"source_metric_rows":1441}
selection_summary={"candidate_count":16,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":256,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","cartservice","checkoutservice","currencyservice","emailservice","frontend","frontend-external","gke-gke-cluster-default-pool-2e1807ce-0e4z","gke-gke-cluster-default-pool-2e1807ce-cx8g","gke-gke-cluster-default-pool-2e1807ce-w819","loadgenerator","paymentservice","productcatalogservice","recommendationservice","redis","shippingservice"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[11.25,33.75,56.25,78.75,101.25,123.75,146.25,168.75,191.25,213.75,236.25,258.75,281.25,303.75,326.25,348.75,371.25,393.75,416.25,438.75,461.25,483.75,506.25,528.75,551.25,573.75,596.25,618.75,641.25,663.75,686.25,708.75,731.25,753.75,776.25,798.75,821.25,843.75,866.25,888.75,911.25,933.75,956.25,978.75,1001.25,1023.75,1046.25,1068.75,1091.25,1113.75,1136.25,1158.75,1181.25,1203.75,1226.25,1248.75,1271.25,1293.75,1316.25,1338.75,1361.25,1383.75,1406.25,1428.75]
[M1] rank=1 service=emailservice metric=container-cpu-system-seconds-total baseline=0.082652 peak=15.807358 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=16
values_compact=raw:[0.06779,0.082335,0.092433,0.102776,0.113215,0.108166,0.072457,0.077623,0.074837,0.056069,0.082819,0.093479,0.093634,0.098116,0.08552,0.078272,0.087075,0.086516,0.092427,0.077645,0.079205,0.096636,0.088332,0.072491,0.073922,0.072262,0.075541,0.095784,0.107462,0.085031,0.078476,0.081133,0.100246,8.780915,15.009532,15.617808,15.65431,15.580396,15.545993,14.746561,13.846337,13.556734,13.296327,13.359531,13.280923,13.422553,13.304309,10.329216,3.175335,0.094322,0.102653,0.077908,0.083749,0.07981,0.080972,0.093919,0.113035,0.094282,0.069743,0.074094,0.077754,0.06009,0.062571,0.09665]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M2] rank=2 service=emailservice metric=container-memory-failures-total baseline=0.086809 peak=146.673349 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=2
values_compact=rle:0.329598*1,0.372769*1,0.050478*1,0.045282*1,0*2,0.11446*1,0.13374*1,0*3,0.318899*1,0.436283*1,0.103877*1,0.041429*1,0*7,0.156204*1,0.213622*1,0.040221*1,0*1,0.048482*1,0.043649*1,0.042872*1,0.045016*1,0*1,0.043648*1,0.036682*1,105.777336*1,113.166536*1,0*7,0.038959*1,0.05077*1,0.255265*1,0.252557*1,0*5,0.102317*1,0.083689*1,0*2,0.240312*1,0.328812*1,0*4,0.099123*1,0.094035*1,0*1
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M3] rank=3 service=emailservice metric=container-memory-mapped-file baseline=0.0 peak=2297856.0 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=rle:0*33,2297856*31
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M4] rank=4 service=emailservice metric=container-memory-usage-bytes baseline=43543711.288889 peak=56451072.0 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=delta:43528192,-4096,4096,0,0,4096,12288,0,-4096,0,0,-4096,4096,4096,0,0,0,0,0,0,4096,0,-4096,4096,0,0,4096,4096,0,0,4096,0,0,8572928,3194880,-3313664,4435968,-2678784,372736,1781760,-303104,-1875968,2056192,-16384,-950272,176128,-1400832,2228224,0,-16384,-8192,8192,0,-2244608,-2256896,0,0,6144,2048,-4096,-4096,8192,0,-2248704
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M5] rank=5 service=emailservice metric=container-memory-working-set-bytes baseline=43469983.288889 peak=56377344.0 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=delta:43454464,-4096,4096,0,0,4096,12288,0,-4096,0,0,-4096,4096,4096,0,0,0,0,0,0,4096,0,-4096,4096,0,0,4096,4096,0,0,4096,0,0,8572928,3194880,-3313664,4435968,-2678784,372736,1781760,-303104,-1875968,2056192,-16384,-950272,176128,-1400832,2228224,0,-16384,-8192,8192,0,-2244608,-2256896,0,0,6144,2048,-4096,-4096,8192,0,-2248704
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M6] rank=6 service=emailservice metric=istio-latency-50 baseline=0.00302 peak=0.067187 signed_z=999.0 onset_bin=32 onset_rel_s=731.25 persistence_bins=17
values_compact=rle:0.003*4,0.003091*1,0.0031*1,0.003*7,0.00304*1,0.003038*1,0.003*6,0.003042*1,0.00305*1,0.003*4,0.003048*1,0.003041*1,0.003033*1,0.003089*1,0.003049*1,0.00319*1,0.004926*1,0.063571*1,0.064655*1,0.063793*1,0.065909*1,0.062963*1,0.00475*1,0.004*1,0.004286*1,0.004333*1,0.00428*1,0.005833*1,0.004739*1,0.0041*1,0.003625*1,0.00313*1,0.003*6,0.00304*1,0.003043*1,0.00304*1,0.003034*1,0.003*2,0.003043*1,0.003039*1,0.003042*1
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M7] rank=7 service=emailservice metric=istio-latency-90 baseline=0.004636 peak=0.09569 signed_z=999.0 onset_bin=32 onset_rel_s=731.25 persistence_bins=17
values_compact=rle:0.0046*4,0.004764*1,0.00478*1,0.0046*7,0.004672*1,0.004668*1,0.0046*6,0.004675*1,0.00469*1,0.0046*4,0.004686*1,0.004673*1,0.00466*1,0.00476*1,0.004688*1,0.004943*1,0.088478*1,0.093857*1,0.095667*1,0.094107*1,0.093182*1,0.092593*1,0.088462*1,0.083636*1,0.087222*1,0.0875*1,0.085357*1,0.088864*1,0.088056*1,0.0845*1,0.079*1,0.004835*1,0.0046*6,0.004672*1,0.004678*1,0.004672*1,0.004661*1,0.0046*2,0.004677*1,0.004671*1,0.004675*1
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M8] rank=8 service=emailservice metric=istio-latency-95 baseline=0.004838 peak=0.099569 signed_z=999.0 onset_bin=32 onset_rel_s=731.25 persistence_bins=17
values_compact=rle:0.0048*4,0.004973*1,0.00499*1,0.0048*7,0.004876*1,0.004872*1,0.0048*6,0.004879*1,0.004895*1,0.0048*4,0.00489*1,0.004878*1,0.004863*1,0.004969*1,0.004893*1,0.061667*1,0.094239*1,0.097643*1,0.0995*1,0.097946*1,0.096591*1,0.096296*1,0.094231*1,0.091818*1,0.093611*1,0.09375*1,0.092679*1,0.094432*1,0.094028*1,0.09225*1,0.0895*1,0.059167*1,0.0048*6,0.004876*1,0.004883*1,0.004876*1,0.004864*1,0.0048*2,0.004881*1,0.004875*1,0.004879*1
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M9] rank=9 service=gke-gke-cluster-default-pool-2e1807ce-cx8g metric=node-memory-active-bytes baseline=9094.651579 peak=31789420.088889 signed_z=999.0 onset_bin=47 onset_rel_s=1068.75 persistence_bins=2
values_compact=delta:9375.91395,1546.752717,-2184.533334,-3549.866666,0,1729.422222,1547.377778,2821.688889,-1092.266667,-1547.377778,455.111111,637.155556,-1183.288889,-2184.533333,3458.844444,819.2,-3458.844444,1001.244444,1820.444444,-91.022222,-728.177778,546.133334,546.133333,-182.044444,-91.022223,91.022223,364.088889,-455.111112,-182.044444,-546.133333,-637.155556,273.066667,-728.177778,637.155556,910.222222,-1911.466667,546.133333,1001.244445,-819.2,455.111111,91.022222,1820.444445,182.044444,-2548.622222,0,910.222222,1001.244445,31776768,-819.2,-31777951.288889,-455.111111,-728.177778,-455.111111,1183.288889,819.2,455.111111,-182.044445,273.066667,-546.133333,-182.044445,2184.533333,-273.066666,-2912.711111,-728.177778
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M10] rank=10 service=gke-gke-cluster-default-pool-2e1807ce-cx8g metric=node-disk-reads-completed-total baseline=0.0 peak=0.022222 signed_z=999.0 onset_bin=38 onset_rel_s=866.25 persistence_bins=4
values_compact=rle:0*38,0.022222*2,0*11,0.022222*2,0*11
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M11] rank=11 service=gke-gke-cluster-default-pool-2e1807ce-cx8g metric=node-disk-read-bytes-total baseline=0.0 peak=1729.422222 signed_z=999.0 onset_bin=38 onset_rel_s=866.25 persistence_bins=4
values_compact=rle:0*38,91.022222*2,0*11,1729.422222*2,0*11
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M12] rank=12 service=emailservice metric=container-sockets baseline=3.0 peak=10.0 signed_z=700.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=rle:3*33,9*1,10*1,9*6,10*2,9*2,10*1,9*18
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[711.0,1440.0]

=== LOG SUMMARY ===
{"entries":[{"change_pct":50.0,"n_during":15,"n_pre":10,"service":"redis"},{"change_pct":8.5,"n_during":1107,"n_pre":1020,"service":"checkoutservice"},{"change_pct":8.5,"n_during":369,"n_pre":340,"service":"emailservice"},{"change_pct":8.5,"n_during":738,"n_pre":680,"service":"paymentservice"},{"change_pct":6.3,"n_during":5642,"n_pre":5306,"service":"shippingservice"},{"change_pct":5.4,"n_during":9578,"n_pre":9089,"service":"cartservice"},{"change_pct":5.2,"n_during":33120,"n_pre":31471,"service":"frontend"},{"change_pct":5.0,"n_during":6935,"n_pre":6604,"service":"recommendationservice"}],"mode":"volume","omitted_services":2,"service_count":10}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":51.0,"error_pct":0.0,"p95_during_ms":0.69,"p95_pre_ms":0.45685000000000003,"service":"emailservice","spans":1285},{"delta_pct":27.0,"error_pct":0.0,"p95_during_ms":95.62759999999992,"p95_pre_ms":75.29989999999987,"service":"checkoutservice","spans":9698},{"delta_pct":-14.7,"error_pct":0.0,"p95_during_ms":0.39049999999999935,"p95_pre_ms":0.458,"service":"paymentservice","spans":997},{"delta_pct":-3.4,"error_pct":0.0,"p95_during_ms":0.028,"p95_pre_ms":0.029,"service":"productcatalogservice","spans":104017},{"delta_pct":1.9,"error_pct":0.0,"p95_during_ms":64.93789999999993,"p95_pre_ms":63.704399999999964,"service":"frontend","spans":209156},{"delta_pct":-1.6,"error_pct":0.0,"p95_during_ms":5.260199999999997,"p95_pre_ms":5.343349999999998,"service":"recommendationservice","spans":27654},{"delta_pct":-0.8,"error_pct":0.0,"p95_during_ms":0.241,"p95_pre_ms":0.243,"service":"currencyservice","spans":57860}],"omitted_services":0,"service_count":7}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=2 omitted_edges=1
[{"evidence_source":"metric","onset_rel_s":721.8,"rank":1,"service":"frontend","severity_z":12.337},{"evidence_source":"trace","onset_rel_s":735.0,"rank":2,"service":"emailservice","severity_z":597.238},{"evidence_source":"trace","onset_rel_s":735.0,"rank":3,"service":"checkoutservice","severity_z":5.327},{"evidence_source":"metric","onset_rel_s":754.8,"rank":4,"service":"gke-gke-cluster-default-pool-2e1807ce-w819","severity_z":10.429},{"evidence_source":"metric","onset_rel_s":793.2,"rank":5,"service":"shippingservice","severity_z":184.107},{"evidence_source":"metric","onset_rel_s":805.8,"rank":6,"service":"adservice","severity_z":11.309},{"evidence_source":"trace","onset_rel_s":825.0,"rank":7,"service":"paymentservice","severity_z":7.283},{"evidence_source":"metric","onset_rel_s":837.0,"rank":8,"service":"cartservice","severity_z":19.245},{"evidence_source":"metric","onset_rel_s":982.8,"rank":9,"service":"redis","severity_z":16.957},{"evidence_source":"metric","onset_rel_s":1045.2,"rank":10,"service":"recommendationservice","severity_z":333.333},{"evidence_source":"metric","onset_rel_s":1050.0,"rank":11,"service":"gke-gke-cluster-default-pool-2e1807ce-cx8g","severity_z":999.0},{"evidence_source":"none","onset_rel_s":null,"rank":12,"service":"productcatalogservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":13,"service":"currencyservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":14,"service":"loadgenerator","severity_z":0.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"currencyservice","caller":"checkoutservice"},{"callee":"emailservice","caller":"checkoutservice"},{"callee":"paymentservice","caller":"checkoutservice"},{"callee":"productcatalogservice","caller":"checkoutservice"},{"callee":"checkoutservice","caller":"frontend"},{"callee":"currencyservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"frontend"},{"callee":"recommendationservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"recommendationservice"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"high","reason":"Rank emailservice first because emailservice has direct container-cpu-system-seconds-total evidence (signed-z 999, persistence 16 bins); although checkoutservice is salient, the caller path checkoutservice -> emailservice means a disturbance in the callee can propagate back toward that caller-side symptom.","services":["emailservice","checkoutservice"]}
