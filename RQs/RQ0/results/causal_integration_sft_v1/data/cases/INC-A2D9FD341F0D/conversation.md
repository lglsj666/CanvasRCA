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
opaque_id: INC-A2D9FD341F0D
observation_window={"duration_rel_s":1440.0,"source_metric_rows":1441}
selection_summary={"candidate_count":17,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":267,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","cartservice","checkoutservice","currencyservice","emailservice","frontend","frontend-external","gke-gke-cluster-default-pool-2e1807ce-0e4z","gke-gke-cluster-default-pool-2e1807ce-cx8g","gke-gke-cluster-default-pool-2e1807ce-w819","gke-gke-cluster-default-pool-2e1807ce-xte3","loadgenerator","paymentservice","productcatalogservice","recommendationservice","redis","shippingservice"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[11.25,33.75,56.25,78.75,101.25,123.75,146.25,168.75,191.25,213.75,236.25,258.75,281.25,303.75,326.25,348.75,371.25,393.75,416.25,438.75,461.25,483.75,506.25,528.75,551.25,573.75,596.25,618.75,641.25,663.75,686.25,708.75,731.25,753.75,776.25,798.75,821.25,843.75,866.25,888.75,911.25,933.75,956.25,978.75,1001.25,1023.75,1046.25,1068.75,1091.25,1113.75,1136.25,1158.75,1181.25,1203.75,1226.25,1248.75,1271.25,1293.75,1316.25,1338.75,1361.25,1383.75,1406.25,1428.75]
[M1] rank=1 service=checkoutservice metric=container-memory-mapped-file baseline=0.0 peak=2207744.0 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=rle:0*33,2207744*31
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M2] rank=2 service=checkoutservice metric=container-cpu-user-seconds-total baseline=0.269316 peak=20.031263 signed_z=346.255 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.24436,0.284405,0.282746,0.23768,0.251471,0.269694,0.331946,0.313242,0.286438,0.288885,0.196244,0.222045,0.214018,0.217955,0.17806,0.217825,0.252686,0.231597,0.36616,0.434706,0.356201,0.261856,0.243464,0.257167,0.252871,0.253878,0.257985,0.246612,0.271253,0.294991,0.308399,0.253729,0.297445,11.657591,19.470569,16.318258,19.990395,15.936925,20.006026,20.00622,19.99821,20.003525,20.00305,19.966637,19.969954,20.014386,20.015871,19.98359,19.982859,20.027786,20.001394,16.246649,20.013149,14.071787,20.002003,18.498289,20.000718,20.009064,19.988612,19.974227,20.025425,20.031251,19.93854,19.85875]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M3] rank=3 service=checkoutservice metric=container-cpu-usage-seconds-total baseline=0.428854 peak=20.031263 signed_z=248.677 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=delta:0.393934,0.058479,-0.038531,-0.030033,0.034292,0.042167,0.053297,-0.040776,-0.045116,0.046223,-0.130114,0.025631,-0.008215,0.011762,-0.075485,0.103873,0.049484,-0.103173,0.171874,0.122034,-0.087566,-0.141536,0.009281,-0.023767,-0.004407,0.015871,-0.01077,0.015121,0.050362,0.01104,0.008255,-0.089741,0.080159,11.2829,7.726005,-3.164556,3.672137,-4.053467,4.069098,0.000192,-0.008008,0.005315,-0.000475,-0.036411,0.003315,0.04443,0.001487,-0.032281,-0.000731,0.044927,-0.026392,-3.754745,3.7665,-5.941362,5.930216,-1.503714,1.502429,0.008347,-0.020453,-0.014387,0.0512,0.005826,-0.036417,-0.000568
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M4] rank=4 service=checkoutservice metric=container-memory-cache baseline=24576.0 peak=2232320.0 signed_z=137.446 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=rle:24576*33,2232320*31
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M5] rank=5 service=gke-gke-cluster-default-pool-2e1807ce-w819 metric=node-disk-read-bytes-total baseline=39.822222 peak=11741.866667 signed_z=75.874 onset_bin=26 onset_rel_s=596.25 persistence_bins=4
values_compact=rle:0*26,637.155556*2,0*8,11741.866667*2,0*26
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M6] rank=6 service=checkoutservice metric=container-memory-failures-total baseline=2.190931 peak=115.674387 signed_z=69.815 onset_bin=32 onset_rel_s=731.25 persistence_bins=3
values_compact=raw:[0.833409,1.444401,1.760643,2.620734,4.518399,2.991879,2.683843,3.195768,3.481288,4.242247,5.808377,2.446437,0.160711,0.0,3.96198,5.721334,1.865382,1.224231,3.147675,2.930603,1.140027,1.068947,0.957376,0.824635,2.229654,2.256517,0.576535,0.764578,0.693521,0.693521,2.067485,3.884528,7.75463,106.603408,95.915595,1.206857,3.77206,2.768676,2.993197,1.659981,1.622484,2.424143,2.885084,1.815504,1.623005,3.450448,3.775656,3.511609,2.144924,0.612785,0.632898,2.566628,5.036412,1.602372,0.972515,4.220007,5.660711,3.013685,3.497523,3.67602,2.59643,2.887565,4.816308,3.096175]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M7] rank=7 service=gke-gke-cluster-default-pool-2e1807ce-0e4z metric=node-disk-written-bytes-total baseline=2778697.955556 peak=20606793.955556 signed_z=49.607 onset_bin=32 onset_rel_s=731.25 persistence_bins=6
values_compact=delta:2720836.266667,-107588.266667,59346.488889,-41870.222222,20571.022222,-49698.133333,359901.866666,-95118.222222,-303468.088889,189053.155556,91659.377777,-72908.8,-265875.911111,28854.044445,231560.533333,-28763.022222,240480.711111,14472.533333,-395400.533333,34315.377778,244212.622222,152462.222222,-75184.355555,-225280,-210625.422223,78188.088889,207530.666667,4551.111111,-182044.444444,-39139.555556,294912,-19205.688889,17709465.6,36590.933334,-18014208,-42507.377778,-22391.466667,40504.888889,92660.622222,110227.911111,1334021.688889,-156194.133333,-1472648.533333,172669.155555,163293.866667,-230377.244445,27579.733334,176401.066666,-63624.533333,-63078.4,-161564.444444,-17931.377778,222458.311111,37046.044444,1303438.222223,-33769.244445,-1530356.622222,100124.444444,866531.555556,-252222.577778,-570254.222222,85651.911111,-10558.577778,72362.666667
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M8] rank=8 service=emailservice metric=istio-latency-95 baseline=0.004825 peak=0.006312 signed_z=30.481 onset_bin=39 onset_rel_s=888.75 persistence_bins=5
values_compact=rle:0.0048*2,0.004919*1,0.004915*1,0.0048*8,0.004915*1,0.004897*1,0.0048*12,0.004886*1,0.00489*1,0.004886*1,0.004884*1,0.0048*2,0.004977*1,0.004949*1,0.0048*4,0.004873*1,0.006125*1,0.005333*1,0.0048*3,0.004919*1,0.004985*1,0.004973*2,0.00489*1,0.0048*5,0.004923*1,0.004946*1,0.0048*1,0.004881*1,0.004897*1,0.0048*5
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M9] rank=9 service=checkoutservice metric=container-memory-usage-bytes baseline=11723184.355556 peak=16846848.0 signed_z=27.362 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=delta:11706368,122880,-274432,241664,-217088,61440,159744,143360,-348160,135168,348160,-598016,0,0,348160,-360448,69632,106496,208896,-327680,86016,16384,57344,20480,192512,65536,-16384,53248,0,-499712,159744,262144,-217088,4718592,110592,4096,307200,-937984,8192,126976,4096,237568,73728,0,-253952,192512,155648,-225280,-4096,40960,4096,221184,229376,-512000,-8192,372736,-409600,40960,360448,12288,-217088,86016,245760,-393216
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M10] rank=10 service=checkoutservice metric=container-memory-working-set-bytes baseline=11723184.355556 peak=16846848.0 signed_z=27.362 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=delta:11706368,122880,-274432,241664,-217088,61440,159744,143360,-348160,135168,348160,-598016,0,0,348160,-360448,69632,106496,208896,-327680,86016,16384,57344,20480,192512,65536,-16384,53248,0,-499712,159744,262144,-217088,4718592,110592,4096,307200,-937984,8192,126976,4096,237568,73728,0,-253952,192512,155648,-225280,-4096,40960,4096,221184,229376,-512000,-8192,372736,-409600,40960,360448,12288,-217088,86016,245760,-393216
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M11] rank=11 service=frontend-external metric=istio-error-total baseline=0.001674 peak=0.2 signed_z=16.398 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=rle:0*7,0.067*1,0*56
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M12] rank=12 service=gke-gke-cluster-default-pool-2e1807ce-w819 metric=node-disk-reads-completed-total baseline=0.001389 peak=0.088889 signed_z=16.267 onset_bin=26 onset_rel_s=596.25 persistence_bins=4
values_compact=rle:0*26,0.022222*2,0*8,0.088889*2,0*26
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[710.0,1440.0]

=== LOG SUMMARY ===
{"entries":[{"change_pct":7.1,"n_during":1038,"n_pre":969,"service":"checkoutservice"},{"change_pct":7.1,"n_during":346,"n_pre":323,"service":"emailservice"},{"change_pct":7.1,"n_during":692,"n_pre":646,"service":"paymentservice"},{"change_pct":3.0,"n_during":5264,"n_pre":5109,"service":"adservice"},{"change_pct":3.0,"n_during":31059,"n_pre":30143,"service":"frontend"},{"change_pct":2.8,"n_during":5196,"n_pre":5056,"service":"shippingservice"},{"change_pct":2.7,"n_during":9008,"n_pre":8770,"service":"cartservice"},{"change_pct":2.6,"n_during":27728,"n_pre":27026,"service":"currencyservice"}],"mode":"volume","omitted_services":2,"service_count":10}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":31.6,"error_pct":0.0,"p95_during_ms":0.5453,"p95_pre_ms":0.41449999999999965,"service":"emailservice","spans":1245},{"delta_pct":-21.3,"error_pct":0.0,"p95_during_ms":0.40779999999999994,"p95_pre_ms":0.5179999999999998,"service":"paymentservice","spans":957},{"delta_pct":11.7,"error_pct":0.0,"p95_during_ms":240.2956499999999,"p95_pre_ms":215.1285,"service":"checkoutservice","spans":9238},{"delta_pct":4.2,"error_pct":0.0,"p95_during_ms":0.025,"p95_pre_ms":0.024,"service":"productcatalogservice","spans":99572},{"delta_pct":-2.7,"error_pct":0.0,"p95_during_ms":0.178,"p95_pre_ms":0.183,"service":"currencyservice","spans":55032},{"delta_pct":-0.7,"error_pct":0.0,"p95_during_ms":4.99,"p95_pre_ms":5.025899999999997,"service":"recommendationservice","spans":26434},{"delta_pct":-0.4,"error_pct":0.0,"p95_during_ms":194.9749999999997,"p95_pre_ms":195.803,"service":"frontend","spans":199519}],"omitted_services":0,"service_count":7}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=3 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":724.8,"rank":1,"service":"gke-gke-cluster-default-pool-2e1807ce-0e4z","severity_z":49.607},{"evidence_source":"metric","onset_rel_s":805.8,"rank":2,"service":"gke-gke-cluster-default-pool-2e1807ce-w819","severity_z":75.874},{"evidence_source":"metric","onset_rel_s":1191.0,"rank":3,"service":"shippingservice","severity_z":12.877},{"evidence_source":"trace","onset_rel_s":1215.0,"rank":4,"service":"checkoutservice","severity_z":6.085},{"evidence_source":"trace","onset_rel_s":1425.0,"rank":5,"service":"emailservice","severity_z":4.376},{"evidence_source":"none","onset_rel_s":null,"rank":6,"service":"frontend-external","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":7,"service":"frontend","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":8,"service":"paymentservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":9,"service":"recommendationservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":10,"service":"adservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":11,"service":"currencyservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":12,"service":"productcatalogservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":13,"service":"cartservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":14,"service":"redis","severity_z":0.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"currencyservice","caller":"checkoutservice"},{"callee":"emailservice","caller":"checkoutservice"},{"callee":"paymentservice","caller":"checkoutservice"},{"callee":"productcatalogservice","caller":"checkoutservice"},{"callee":"checkoutservice","caller":"frontend"},{"callee":"currencyservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"frontend"},{"callee":"recommendationservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"recommendationservice"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"high","reason":"Rank checkoutservice first because checkoutservice has direct container-memory-mapped-file evidence (signed-z 999, persistence 31 bins); although frontend is salient, the caller path frontend -> checkoutservice means a disturbance in the callee can propagate back toward that caller-side symptom.","services":["checkoutservice","frontend"]}
