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
opaque_id: INC-41ED569A7F14
observation_window={"duration_rel_s":1440.0,"source_metric_rows":1441}
selection_summary={"candidate_count":17,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":264,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","cartservice","checkoutservice","currencyservice","emailservice","frontend","frontend-external","gke-gke-cluster-default-pool-2e1807ce-0e4z","gke-gke-cluster-default-pool-2e1807ce-cx8g","gke-gke-cluster-default-pool-2e1807ce-w819","gke-gke-cluster-default-pool-2e1807ce-xte3","loadgenerator","paymentservice","productcatalogservice","recommendationservice","redis","shippingservice"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[11.25,33.75,56.25,78.75,101.25,123.75,146.25,168.75,191.25,213.75,236.25,258.75,281.25,303.75,326.25,348.75,371.25,393.75,416.25,438.75,461.25,483.75,506.25,528.75,551.25,573.75,596.25,618.75,641.25,663.75,686.25,708.75,731.25,753.75,776.25,798.75,821.25,843.75,866.25,888.75,911.25,933.75,956.25,978.75,1001.25,1023.75,1046.25,1068.75,1091.25,1113.75,1136.25,1158.75,1181.25,1203.75,1226.25,1248.75,1271.25,1293.75,1316.25,1338.75,1361.25,1383.75,1406.25,1428.75]
[M1] rank=1 service=shippingservice metric=istio-latency-99 baseline=0.004967 peak=0.056625 signed_z=999.0 onset_bin=38 onset_rel_s=866.25 persistence_bins=6
values_compact=delta:0.004958,-0.000001,0.000024,-0.000001,-0.000022,0.000012,0,-0.000013,0,0.000014,0.000002,-0.000015,0.000034,0,-0.000034,0.000001,-0.000001,0,0,0,-0.000001,0.000001,0,0.000001,0,0.000012,0.000014,-0.000012,0.000012,-0.000005,-0.000022,0,0.000013,0.000013,-0.000003,-0.00001,-0.000012,-0.000001,0.000567,0.000905,-0.001448,-0.000011,0.000001,0.000014,0.004331,-0.001137,-0.003181,-0.000015,-0.000026,0,0,0.000001,0,0,0.000014,0.00001,-0.000013,-0.000012,0,0.000012,0.000029,-0.000015,-0.000013,0.000001
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M2] rank=2 service=checkoutservice metric=container-memory-mapped-file baseline=126976.0 peak=3260416.0 signed_z=961.055 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=rle:126976*32,3260416*32
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M3] rank=3 service=adservice metric=container-memory-rss baseline=110377875.911111 peak=138948608.0 signed_z=580.562 onset_bin=34 onset_rel_s=776.25 persistence_bins=30
values_compact=delta:110297088,0,0,8192,12288,98304,0,-49152,-40960,4096,0,110592,0,-81920,90112,-12288,0,-81920,94208,0,12288,-81920,0,-4096,0,0,0,0,0,0,0,0,0,94208,28479488,-28123136,0,8192,-180224,0,12288,4096,241664,-8192,4096,-184320,8192,4096,0,0,-4096,-8192,16384,24576,-28672,-12288,200704,0,0,-184320,0,0,0,32768
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M4] rank=4 service=adservice metric=container-memory-working-set-bytes baseline=111710082.844444 peak=140345344.0 signed_z=449.476 onset_bin=34 onset_rel_s=776.25 persistence_bins=30
values_compact=delta:111616000,4096,-4096,143360,-122880,118784,8192,-67584,-51200,0,4096,135168,-4096,-106496,110592,-8192,0,-102400,114688,4096,8192,-102400,0,-8192,4096,0,-4096,4096,-4096,0,4096,-4096,4096,114688,28536832,-28151808,-4096,8192,-225280,0,16384,0,290816,-12288,0,-217088,4096,0,4096,4096,-12288,-4096,40960,24576,-49152,-16384,241664,-4096,4096,-229376,4096,0,4096,28672
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M5] rank=5 service=adservice metric=container-memory-usage-bytes baseline=112538982.4 peak=141180928.0 signed_z=445.485 onset_bin=34 onset_rel_s=776.25 persistence_bins=30
values_compact=delta:112439296,4096,-4096,143360,-122880,118784,8192,-63488,-51200,0,4096,135168,-4096,-106496,110592,-8192,0,-102400,114688,8192,8192,-102400,0,-8192,4096,0,0,4096,-4096,0,4096,-4096,4096,114688,28536832,-28147712,-4096,8192,-225280,0,16384,0,290816,-12288,0,-212992,4096,0,4096,4096,-12288,0,40960,24576,-49152,-16384,241664,-4096,4096,-229376,4096,4096,4096,28672
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M6] rank=6 service=emailservice metric=istio-latency-95 baseline=0.004884 peak=0.073125 signed_z=418.778 onset_bin=34 onset_rel_s=776.25 persistence_bins=7
values_compact=rle:0.0048*2,0.004893*1,0.004879*1,0.0048*1,0.004912*1,0.004895*1,0.0048*3,0.004919*1,0.0049*1,0.0048*4,0.004909*2,0.0048*3,0.004915*1,0.005125*1,0.004909*1,0.0048*1,0.005*1,0.0055*1,0.0048*3,0.0049*1,0.004897*1,0.0048*1,0.0049*1,0.006167*1,0.007*1,0.006*1,0.004886*1,0.0048*1,0.00525*1,0.004949*1,0.004878*1,0.004946*1,0.0048*1,0.004897*1,0.004878*1,0.0725*1,0.073125*1,0.005667*1,0.006083*1,0.004909*1,0.0048*11,0.004973*1,0.004981*1
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M7] rank=7 service=checkoutservice metric=container-sockets baseline=9.0 peak=13.0 signed_z=307.692 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=rle:9*32,11*21,13*1,11*10
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M8] rank=8 service=checkoutservice metric=container-cpu-usage-seconds-total baseline=0.383277 peak=20.04323 signed_z=254.262 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=delta:0.408005,-0.00226,0.013819,0.073406,-0.081646,-0.033782,-0.012467,0.076894,0.060479,-0.211481,0.08745,0.130142,-0.091888,0.012606,0.032505,-0.035132,-0.085301,0.012987,0.008706,-0.034592,-0.034395,-0.017986,0.095678,0.015278,-0.012552,0.001028,-0.01126,-0.057102,0.139903,-0.017558,-0.11496,0.200113,1.402145,8.592634,9.490078,-0.011949,0.025213,-0.0235,-0.007685,0.02678,0.01122,-0.021941,-0.01406,-0.006527,0.026709,0.014197,-0.031468,-0.008942,0.02433,0.028105,-0.02057,-0.032174,0.030444,-3.315212,3.308396,-0.001991,0.009835,-0.007326,-0.003272,-0.032635,0.03758,0.040179,-0.056208,-0.004221
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M9] rank=9 service=checkoutservice metric=container-memory-cache baseline=1986560.0 peak=4194304.0 signed_z=225.484 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=rle:1986560*32,4194304*32
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M10] rank=10 service=checkoutservice metric=container-cpu-user-seconds-total baseline=0.300959 peak=20.00901 signed_z=211.027 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=raw:[0.408007,0.405745,0.419566,0.492968,0.411324,0.37754,0.365072,0.441971,0.50245,0.282152,0.266342,0.328179,0.284157,0.31874,0.315278,0.273563,0.207812,0.23107,0.251768,0.230769,0.19558,0.18411,0.261487,0.260548,0.257948,0.248764,0.237104,0.20379,0.29605,0.294683,0.226151,0.346755,1.759115,10.364803,19.925464,19.95744,19.992676,19.913153,19.890026,19.853777,19.840071,19.906921,19.927629,19.898119,19.896537,19.907612,19.904527,19.878891,19.907769,19.958956,19.942561,19.8791,19.902395,16.625264,19.930975,19.930678,19.915071,19.911665,19.866286,19.836559,19.869502,19.865844,19.832499,19.840101]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M11] rank=11 service=recommendationservice metric=istio-latency-95 baseline=0.009865 peak=0.019405 signed_z=182.693 onset_bin=34 onset_rel_s=776.25 persistence_bins=4
values_compact=raw:[0.009989,0.009961,0.009876,0.009852,0.009873,0.009897,0.009901,0.009852,0.009807,0.00982,0.009811,0.009814,0.009883,0.009891,0.009969,0.00995,0.009801,0.009839,0.009839,0.009798,0.00983,0.009853,0.009838,0.009806,0.009781,0.009828,0.009888,0.009862,0.009849,0.009887,0.00996,0.009925,0.009856,0.009866,0.016477,0.016851,0.009944,0.009905,0.009781,0.009792,0.009872,0.009894,0.009874,0.009829,0.009834,0.009871,0.009826,0.009809,0.009828,0.00994,0.009925,0.00982,0.00982,0.009799,0.009863,0.019096,0.018617,0.00994,0.009946,0.009891,0.009835,0.009822,0.009803,0.00981]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M12] rank=12 service=productcatalogservice metric=istio-latency-99 baseline=0.004953 peak=0.005439 signed_z=108.033 onset_bin=34 onset_rel_s=776.25 persistence_bins=4
values_compact=delta:0.004951,0,0.000003,0.000001,0.000001,0.000004,-0.000001,-0.000004,-0.000005,-0.000003,0,0,0.000003,0.000003,0.000004,-0.000003,-0.000003,0.000009,0.000001,-0.000008,-0.000003,0.000001,0,0,-0.000001,0.000004,0.000002,-0.000005,-0.000002,0,0.000005,0.000009,-0.000005,-0.000006,0.000019,-0.000003,-0.000016,0.000001,-0.000003,0,0.000007,-0.000001,-0.000005,0.000001,0.000008,-0.000001,-0.00001,0.000003,0.000001,0.000001,-0.000001,-0.000004,0.000002,0,0.000002,0.000466,-0.000376,-0.000089,0,-0.000006,-0.000001,0.000004,0.000004,-0.000002
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[701.0,1440.0]

=== LOG SUMMARY ===
{"entries":[{"change_pct":50.0,"n_during":15,"n_pre":10,"service":"redis"},{"change_pct":7.2,"n_during":6993,"n_pre":6524,"service":"recommendationservice"},{"change_pct":6.3,"n_during":9515,"n_pre":8955,"service":"cartservice"},{"change_pct":6.3,"n_during":5460,"n_pre":5136,"service":"shippingservice"},{"change_pct":6.1,"n_during":5601,"n_pre":5280,"service":"adservice"},{"change_pct":5.6,"n_during":29351,"n_pre":27782,"service":"currencyservice"},{"change_pct":5.6,"n_during":32903,"n_pre":31144,"service":"frontend"},{"change_pct":4.5,"n_during":969,"n_pre":927,"service":"checkoutservice"}],"mode":"volume","omitted_services":2,"service_count":10}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":166.5,"error_pct":0.0,"p95_during_ms":189.3065,"p95_pre_ms":71.03684999999999,"service":"checkoutservice","spans":8826},{"delta_pct":9.4,"error_pct":0.0,"p95_during_ms":58.17889999999996,"p95_pre_ms":53.175199999999954,"service":"frontend","spans":208518},{"delta_pct":5.2,"error_pct":0.0,"p95_during_ms":0.221,"p95_pre_ms":0.21,"service":"currencyservice","spans":57419},{"delta_pct":3.7,"error_pct":0.0,"p95_during_ms":4.951,"p95_pre_ms":4.775549999999999,"service":"recommendationservice","spans":27610},{"delta_pct":3.3,"error_pct":0.0,"p95_during_ms":0.031,"p95_pre_ms":0.03,"service":"productcatalogservice","spans":103710},{"delta_pct":2.5,"error_pct":0.0,"p95_during_ms":0.502,"p95_pre_ms":0.4895999999999989,"service":"paymentservice","spans":920},{"delta_pct":-2.4,"error_pct":0.0,"p95_during_ms":0.45739999999999986,"p95_pre_ms":0.4685,"service":"emailservice","spans":1208}],"omitted_services":0,"service_count":7}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=3 omitted_edges=1
[{"evidence_source":"trace","onset_rel_s":735.0,"rank":1,"service":"checkoutservice","severity_z":19.16},{"evidence_source":"metric","onset_rel_s":768.0,"rank":2,"service":"adservice","severity_z":580.562},{"evidence_source":"metric","onset_rel_s":850.8,"rank":3,"service":"gke-gke-cluster-default-pool-2e1807ce-xte3","severity_z":12.394},{"evidence_source":"metric","onset_rel_s":999.0,"rank":4,"service":"shippingservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1042.8,"rank":5,"service":"emailservice","severity_z":418.778},{"evidence_source":"metric","onset_rel_s":1149.0,"rank":6,"service":"redis","severity_z":18.294},{"evidence_source":"trace","onset_rel_s":1215.0,"rank":7,"service":"recommendationservice","severity_z":7.071},{"evidence_source":"metric","onset_rel_s":1234.8,"rank":8,"service":"productcatalogservice","severity_z":108.033},{"evidence_source":"metric","onset_rel_s":1234.8,"rank":9,"service":"frontend","severity_z":40.0},{"evidence_source":"trace","onset_rel_s":1335.0,"rank":10,"service":"paymentservice","severity_z":6.898},{"evidence_source":"metric","onset_rel_s":1377.0,"rank":11,"service":"gke-gke-cluster-default-pool-2e1807ce-cx8g","severity_z":10.647},{"evidence_source":"none","onset_rel_s":null,"rank":12,"service":"frontend-external","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":13,"service":"currencyservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":14,"service":"gke-gke-cluster-default-pool-2e1807ce-w819","severity_z":0.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"currencyservice","caller":"checkoutservice"},{"callee":"emailservice","caller":"checkoutservice"},{"callee":"paymentservice","caller":"checkoutservice"},{"callee":"productcatalogservice","caller":"checkoutservice"},{"callee":"checkoutservice","caller":"frontend"},{"callee":"currencyservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"frontend"},{"callee":"recommendationservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"recommendationservice"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"high","reason":"Rank checkoutservice first because checkoutservice has direct container-memory-mapped-file evidence (signed-z 961.05, persistence 32 bins); although frontend is salient, the caller path frontend -> checkoutservice means a disturbance in the callee can propagate back toward that caller-side symptom.","services":["checkoutservice","frontend"]}
