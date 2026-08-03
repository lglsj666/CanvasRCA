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
opaque_id: INC-5603C0CCA7A7
observation_window={"duration_rel_s":2280.0,"source_metric_rows":39}
selection_summary={"candidate_count":60,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":492,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","cartservice","cartservice-0","cartservice-1","cartservice-2","checkoutservice","checkoutservice-0","checkoutservice-1","checkoutservice-2","currencyservice","currencyservice-0","currencyservice-1","currencyservice-2","emailservice","emailservice-0","emailservice-1","emailservice-2","example-ant-10-29155200-sh4b9","example-ant-29155200-tblqb","frontend","frontend-0","frontend-1","frontend-2","hipstershop","k8s-master1","k8s-master2","k8s-master3","node-1","node-2","node-3","node-4","node-5","node-6","node-7","node-8","paymentservice","paymentservice-0","paymentservice-1","paymentservice-2","productcatalogservice","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","recommendationservice","recommendationservice-0","recommendationservice-1","recommendationservice-2","redis","redis-cart","redis-cart-0","shippingservice","shippingservice-0","shippingservice-1","shippingservice-2","tidb-pd","tidb-tidb","tidb-tikv"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[17.812,53.438,89.062,124.688,160.312,195.938,231.562,267.188,302.812,338.438,374.062,409.688,445.312,480.938,516.562,552.188,587.812,623.438,659.062,694.688,730.312,765.938,801.562,837.188,872.812,908.438,944.062,979.688,1015.312,1050.938,1086.562,1122.188,1157.812,1193.438,1229.062,1264.688,1300.312,1335.938,1371.562,1407.188,1442.812,1478.438,1514.062,1549.688,1585.312,1620.938,1656.562,1692.188,1727.812,1763.438,1799.062,1834.688,1870.312,1905.938,1941.562,1977.188,2012.812,2048.438,2084.062,2119.688,2155.312,2190.938,2226.562,2262.188]
[M1] rank=1 service=adservice-2 metric=pod_memory_working_set_bytes baseline=5.447368 peak=7897570.33 signed_z=999.0 onset_bin=47 onset_rel_s=1692.188 persistence_bins=2
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,103.5,-103.5,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,101.24,7897469.09,-7897570.33,0,0,0,0,0,0,0,0
missing_mask_bits=0010100101001010010100101001010100101001010010100101001010010100
observed_counts_compact=csv:1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1
[M2] rank=2 service=paymentservice-2 metric=pod_memory_working_set_bytes baseline=496.428333 peak=777392.8 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:986.96,-749.59,528.49,-403.72,-362.14,996.26,-647.55,309.87,-201.98,-107.45,-349.15,796.34,-274.11,120.62,-176.71,-49.02,-102.29,299.74,-614.57,1009.34,-1009.34,1370.97,-1370.97,837.74,-837.74,632.81,-632.81,632.08,-148.97,-261.81,442.88,-78.67,-328.59,777135.88,-776699.95,152.16,-664.05,-180.96
missing_mask_bits=0010100101001010010100101011010100101001010010100101001010010100
observed_counts_compact=csv:1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,0,0,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1
[M3] rank=3 service=recommendationservice-2 metric=pod_cpu_usage baseline=0.01 peak=0.0 signed_z=-999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.01,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-0.01,0.01,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010100101001010010100101001010100101001010010100101001010010100
observed_counts_compact=csv:1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1
[M4] rank=4 service=tidb-tidb metric=connection_count baseline=2.0 peak=3.0 signed_z=333.333 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,-1,0,0,0,0,1,-1
missing_mask_bits=0010100101001010010100101001010100101001010010100101001010010100
observed_counts_compact=csv:1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1
[M5] rank=5 service=paymentservice-2 metric=rrt_max baseline=2284.578947 peak=69324.0 signed_z=124.925 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:2610,-403,682,-429,156,-1837,2088,-1928,1379,-290,182,321,-138,-131,59,149,-243,413,0,-402,0,1006,-752,729,-645,-67,-244,169,-72,575,-905,67292,-66411,599,-1249,-922,1191,-577,286
missing_mask_bits=0010100101001010010100101001010100101001010010100101001010010100
observed_counts_compact=csv:1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1
[M6] rank=6 service=paymentservice-2 metric=rrt baseline=1976.188947 peak=36108.75 signed_z=71.18 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:2506,-439.5,-77.5,330.5,-294.5,-1277,1777.5,-1617.5,633,424.5,-167.5,440.25,-486,423.25,-440.5,623,-332.75,410.42,0,-454,0,394.83,-16.5,387,-319.5,-128.25,-156.25,-63.75,166.75,321.5,-675.5,34216.75,-33318.25,258.25,-1148.75,-603.5,1021.5,-488.25,278.25
missing_mask_bits=0010100101001010010100101001010100101001010010100101001010010100
observed_counts_compact=csv:1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1
[M7] rank=7 service=paymentservice metric=rrt_max baseline=3262.526316 peak=69324.0 signed_z=49.876 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:2880,74,-65,-429,646,1085,-1324,-527,3444,-2759,4807,-5301,721,-659,-250,223,497,-287,-240,1065,-1468,4505,-4146,2384,-2300,329,1656,-1259,-940,575,-705,67092,-66411,599,1421,-2065,498,2517,-3176
missing_mask_bits=0010100101001010010100101001010100101001010010100101001010010100
observed_counts_compact=csv:1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1
[M8] rank=8 service=paymentservice metric=rrt baseline=2190.822632 peak=12017.64 signed_z=31.303 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:1826.9,318.2,-268.85,39.75,307.93,591.9,-836.54,-529.62,988.9,24.6,46.25,-267.99,191.34,-180.27,-343.4,36.9,508.2,-61.95,-39,-85.44,-260.31,549.94,-197.44,99.71,-539.71,312.5,-75,95,-316.33,352.43,-448,10177.04,-9711.81,115.63,367.04,-708.4,199.98,784.82,-1134.78
missing_mask_bits=0010100101001010010100101001010100101001010010100101001010010100
observed_counts_compact=csv:1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1
[M9] rank=9 service=node-5 metric=node_disk_write_time_seconds_total baseline=0.0 peak=0.06 signed_z=11.942 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.06,-0.06,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010100101001010010100101001010100101001010010100101001010010100
observed_counts_compact=csv:1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1
[M10] rank=10 service=currencyservice metric=rrt_max baseline=6727.631579 peak=62351.0 signed_z=11.721 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:4566,-1015,1938,-2519,2549,297,18571,-20182,3765,2868,-5174,-1117,2665,4865,-7455,-4,21,715,-1573,2047,4405,19063,-20543,-3347,1334,8815,-10898,-1394,512,1393,57183,-56633,-1696,2297,1519,-528,-164,-1715,-1307
missing_mask_bits=0010100101001010010100101001010100101001010010100101001010010100
observed_counts_compact=csv:1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1
[M11] rank=11 service=currencyservice-0 metric=rrt_max baseline=5583.368421 peak=62351.0 signed_z=11.68 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:4566,-1771,99,-102,2727,297,18571,-20182,-356,-899,2714,-1117,-1026,8556,-7455,-133,-1072,776,-412,498,-990,26007,-24991,-823,221,1022,-68,-1579,-400,2490,57183,-59458,312,39,215,-106,3793,-2726,-1231
missing_mask_bits=0010100101001010010100101001010100101001010010100101001010010100
observed_counts_compact=csv:1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1
[M12] rank=12 service=cartservice-1 metric=rrt baseline=1891.129474 peak=3488.18 signed_z=9.355 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:2481.11,-504.84,-166.3,-58.25,68.72,122.27,-131.71,-49.69,-5.48,-30.28,21.3,247.34,-84.07,36.36,-180.08,22.83,159.91,-20.88,136.62,1423.3,-1737.32,117.76,189.53,-90.36,-100.03,114.53,-80.41,63.79,-191.32,123.28,-37.68,-49.13,-49.77,182.05,-68.88,-105.89,198.43,-288.33,-85.73
missing_mask_bits=0010100101001010010100101001010100101001010010100101001010010100
observed_counts_compact=csv:1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[1680.0,1800.0]

=== LOG SUMMARY ===
{"entries":[{"change_pct":-100.0,"n_during":0,"n_pre":30,"service":"redis-cart-0"},{"change_pct":-96.9,"n_during":2,"n_pre":64,"service":"emailservice-2"},{"change_pct":-96.9,"n_during":4,"n_pre":128,"service":"paymentservice-1"},{"change_pct":-96.1,"n_during":10,"n_pre":254,"service":"shippingservice-1"},{"change_pct":-95.8,"n_during":24,"n_pre":567,"service":"checkoutservice-2"},{"change_pct":-95.6,"n_during":16,"n_pre":362,"service":"currencyservice-2"},{"change_pct":-95.2,"n_during":54,"n_pre":1125,"service":"cartservice-0"},{"change_pct":-95.2,"n_during":3,"n_pre":63,"service":"emailservice-0"}],"mode":"volume","omitted_services":15,"service_count":23}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":-22.6,"error_pct":0.0,"p95_during_ms":0.3962,"p95_pre_ms":0.512,"service":"shippingservice","spans":1316},{"delta_pct":-16.1,"error_pct":0.0,"p95_during_ms":117.00985000000001,"p95_pre_ms":139.469,"service":"checkoutservice","spans":2238},{"delta_pct":-15.0,"error_pct":0.0,"p95_during_ms":0.96565,"p95_pre_ms":1.136449999999999,"service":"emailservice","spans":190},{"delta_pct":3.9,"error_pct":0.0,"p95_during_ms":5.4535,"p95_pre_ms":5.246899999999999,"service":"recommendationservice","spans":6814},{"delta_pct":1.0,"error_pct":0.0,"p95_during_ms":14.993149999999998,"p95_pre_ms":14.844249999999995,"service":"productcatalogservice","spans":25628},{"delta_pct":-0.6,"error_pct":0.0,"p95_during_ms":4.861199999999998,"p95_pre_ms":4.888749999999999,"service":"cartservice","spans":4539},{"delta_pct":0.4,"error_pct":0.0,"p95_during_ms":93.35355000000001,"p95_pre_ms":92.95329999999989,"service":"frontend","spans":55518},{"delta_pct":0.1,"error_pct":0.0,"p95_during_ms":3.2885,"p95_pre_ms":3.2859999999999925,"service":"redis","spans":4909}],"omitted_services":0,"service_count":8}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=6 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":1380.0,"rank":1,"service":"node-5","severity_z":11.942},{"evidence_source":"metric","onset_rel_s":1560.0,"rank":2,"service":"recommendationservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1740.0,"rank":3,"service":"adservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1800.0,"rank":4,"service":"currencyservice","severity_z":11.721},{"evidence_source":"metric","onset_rel_s":1860.0,"rank":5,"service":"tidb-tidb","severity_z":333.333},{"evidence_source":"metric","onset_rel_s":2040.0,"rank":6,"service":"paymentservice","severity_z":999.0},{"evidence_source":"none","onset_rel_s":null,"rank":7,"service":"cartservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":8,"service":"emailservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":9,"service":"shippingservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":10,"service":"checkoutservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":11,"service":"tidb-tikv","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":12,"service":"frontend","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":13,"service":"hipstershop","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":14,"service":"tidb-pd","severity_z":0.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"cartservice","caller":"checkoutservice"},{"callee":"emailservice","caller":"checkoutservice"},{"callee":"shippingservice","caller":"checkoutservice"},{"callee":"cartservice","caller":"frontend"},{"callee":"checkoutservice","caller":"frontend"},{"callee":"recommendationservice","caller":"frontend"},{"callee":"shippingservice","caller":"frontend"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

[excluded before optimizer]
