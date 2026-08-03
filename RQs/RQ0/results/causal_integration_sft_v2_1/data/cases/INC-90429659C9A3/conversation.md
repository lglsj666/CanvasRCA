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
opaque_id: INC-90429659C9A3
observation_window={"duration_rel_s":1920.0,"source_metric_rows":33}
selection_summary={"candidate_count":60,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":513,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","cartservice","cartservice-0","cartservice-1","cartservice-2","checkoutservice","checkoutservice-0","checkoutservice-1","checkoutservice-2","currencyservice","currencyservice-0","currencyservice-1","currencyservice-2","emailservice","emailservice-0","emailservice-1","emailservice-2","example-ant-10-29168160-4j82d","example-ant-29168160-pkvws","frontend","frontend-0","frontend-1","frontend-2","hipstershop","k8s-master1","k8s-master2","k8s-master3","node-1","node-2","node-3","node-4","node-5","node-6","node-7","node-8","paymentservice","paymentservice-0","paymentservice-1","paymentservice-2","productcatalogservice","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","recommendationservice","recommendationservice-0","recommendationservice-1","recommendationservice-2","redis","redis-cart","redis-cart-0","shippingservice","shippingservice-0","shippingservice-1","shippingservice-2","tidb-pd","tidb-tidb","tidb-tikv"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[15.0,45.0,75.0,105.0,135.0,165.0,195.0,225.0,255.0,285.0,315.0,345.0,375.0,405.0,435.0,465.0,495.0,525.0,555.0,585.0,615.0,645.0,675.0,705.0,735.0,765.0,795.0,825.0,855.0,885.0,915.0,945.0,975.0,1005.0,1035.0,1065.0,1095.0,1125.0,1155.0,1185.0,1215.0,1245.0,1275.0,1305.0,1335.0,1365.0,1395.0,1425.0,1455.0,1485.0,1515.0,1545.0,1575.0,1605.0,1635.0,1665.0,1695.0,1725.0,1755.0,1785.0,1815.0,1845.0,1875.0,1905.0]
[M1] rank=1 service=adservice-0 metric=pod_fs_reads_bytes baseline=0.0 peak=9583783.19 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,382543.73,-382543.73,0,0,0,16472.77,-13663.66,-2809.11,0,278.7,326431.49,9257073,-9583783.19,894.39,279913.47,-280807.86,0
missing_mask_bits=0101010101010101010101010101010101010101010101010101010101010100
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M2] rank=2 service=node-3 metric=node_sockstat_TCP_inuse baseline=0.0 peak=0.07 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.07,-0.07,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0101010101010101010101010101010101010101010101010101010101010100
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M3] rank=3 service=node-7 metric=node_network_receive_bytes_total baseline=164.071875 peak=146.47 signed_z=-999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:164.1,-0.03,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-17.6,17.6,0,-0.03,0.03,0,0,0,0,0,0
missing_mask_bits=0101010101010101010101010101010101010101010101010101010101010100
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M4] rank=4 service=recommendationservice-1 metric=pod_fs_reads_bytes baseline=0.0 peak=241572.44 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,241572.44,-241572.44,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0101010101010101010101010101010101010101010101010101010101010100
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M5] rank=5 service=adservice-0 metric=pod_memory_working_set_bytes baseline=49282.110625 peak=25795068.79 signed_z=753.65 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:1130.37,-1039.44,8588.64,-8511.81,-44.16,25351.68,46142.5,-342.22,7100.63,247.66,-7889.62,3066.07,2155.14,-1815.89,1605.45,6833.36,135051.15,-144250.76,7206.84,-7478.15,5236.93,4052.3,-5944.34,6222.2,-6782.3,25719176.56,-9898372.76,-15877739.53,2116386.28,546332.6,994134.04,-3404395.15,-269934.68
missing_mask_bits=0101010101010101010101010101010101010101010101010101010101010100
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M6] rank=6 service=adservice-0 metric=pod_cpu_usage baseline=0.000625 peak=0.6 signed_z=247.613 onset_bin=62 onset_rel_s=1875.0 persistence_bins=2
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0.01,-0.01,0,0,0,0.01,-0.01,0,0.01,0,-0.01,0.01,-0.01,0,0,0,0.02,0.58,0,0,-0.59,0
missing_mask_bits=0101010101010101010101010101010101010101010101010101010101010100
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M7] rank=7 service=paymentservice-1 metric=rrt_max baseline=2182.25 peak=57442.0 signed_z=85.657 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:1912,-56,-287,1065,-941,-3,2426,-2104,282,1028,-1199,-218,-13,210,-255,102,2020,-2000,470,-557,468,-131,148,789,186,-484,-547,-493,331,595,-1101,55799,-55225
missing_mask_bits=0101010101010101010101010101010101010101010101010101010101010100
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M8] rank=8 service=tidb-tikv metric=write_wal_mbps baseline=59.148125 peak=7796.11 signed_z=45.919 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:11.49,-1.05,1.05,-1.05,16.4,-15.35,0,21.44,-21.44,15.35,683.89,-699.24,-1.05,0,-8.35,34.15,-25.8,23.54,7762.13,-6602.93,-484.49,-569.02,-128.18,570.98,-427.63,-143.35,0,21.44,-21.44,40.51,-50.96,24.03,-13.58
missing_mask_bits=0101010101010101010101010101010101010101010101010101010101010100
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M9] rank=9 service=k8s-master2 metric=node_filesystem_free_bytes baseline=9426772736.0 peak=9447059456.0 signed_z=44.559 onset_bin=62 onset_rel_s=1875.0 persistence_bins=2
values_compact=delta:9425715200,0,1785856,-475136,12288,-212992,0,0,266240,0,-352256,-45056,0,0,0,499712,-503808,-258048,4358144,20480,-208896,167936,-503808,0,16793600,-16777216,356352,0,-749568,-1048576,0,0,143360
missing_mask_bits=0101010101010101010101010101010101010101010101010101010101010100
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M10] rank=10 service=tidb-tidb metric=block_cache_size baseline=49611760.0 peak=51867280.0 signed_z=43.486 onset_bin=62 onset_rel_s=1875.0 persistence_bins=2
values_compact=delta:49611760,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,2255520,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0101010101010101010101010101010101010101010101010101010101010100
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M11] rank=11 service=paymentservice-1 metric=rrt baseline=1494.573125 peak=10746.08 signed_z=42.514 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:1386.64,217.06,-376.91,317.46,-393.67,72.09,537.4,-388.17,334.41,268.59,-448.9,35,-199.71,-2.67,61.5,318.21,-237.58,-336.37,306.34,-271.97,243,85.75,-359.88,450.38,-151.64,20.94,-28.36,-53.06,79.62,32.5,-338.07,9566.15,-9157.83
missing_mask_bits=0101010101010101010101010101010101010101010101010101010101010100
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M12] rank=12 service=paymentservice metric=rrt_max baseline=3676.5 peak=57442.0 signed_z=37.281 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:2240,1520,-1555,4561,-2648,-961,959,105,-1172,3989,-4336,-341,1434,-1693,2407,-1824,1964,-2680,1009,-701,1097,1732,-1673,-277,186,1337,-2161,3174,-3116,1777,-1127,54216,-55225
missing_mask_bits=0101010101010101010101010101010101010101010101010101010101010100
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[1560.0,1680.0]

=== LOG SUMMARY ===
{"entries":[{"error_logs":2,"error_pct":50.0,"service":"adservice-0","total_logs":4},{"error_logs":1,"error_pct":0.01,"service":"frontend-1","total_logs":14985},{"error_logs":1,"error_pct":0.0,"service":"frontend-2","total_logs":28335}],"mode":"errors","omitted_services":21,"service_count":24}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":20.2,"error_pct":0.0,"p95_during_ms":3.5061999999999975,"p95_pre_ms":2.9165,"service":"redis","spans":14939},{"delta_pct":19.6,"error_pct":0.0,"p95_during_ms":5.225699999999995,"p95_pre_ms":4.3684999999999885,"service":"cartservice","spans":13811},{"delta_pct":-17.9,"error_pct":0.0,"p95_during_ms":0.89875,"p95_pre_ms":1.0952499999999998,"service":"emailservice","spans":576},{"delta_pct":-5.6,"error_pct":0.0,"p95_during_ms":0.45239999999999964,"p95_pre_ms":0.479,"service":"shippingservice","spans":4013},{"delta_pct":5.2,"error_pct":0.0,"p95_during_ms":16.054549999999995,"p95_pre_ms":15.256199999999998,"service":"productcatalogservice","spans":77699},{"delta_pct":-3.0,"error_pct":0.0,"p95_during_ms":5.9365499999999995,"p95_pre_ms":6.118699999999997,"service":"recommendationservice","spans":20632},{"delta_pct":-0.5,"error_pct":0.0,"p95_during_ms":82.912,"p95_pre_ms":83.31700000000001,"service":"frontend","spans":168272},{"delta_pct":-0.4,"error_pct":0.0,"p95_during_ms":125.76439999999998,"p95_pre_ms":126.21439999999998,"service":"checkoutservice","spans":6835}],"omitted_services":0,"service_count":8}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=9 omitted_edges=1
[{"evidence_source":"metric","onset_rel_s":960.0,"rank":1,"service":"node-3","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":960.0,"rank":2,"service":"recommendationservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":960.0,"rank":3,"service":"tidb-tidb","severity_z":43.486},{"evidence_source":"metric","onset_rel_s":1080.0,"rank":4,"service":"tidb-tikv","severity_z":45.919},{"evidence_source":"metric","onset_rel_s":1140.0,"rank":5,"service":"node-5","severity_z":11.038},{"evidence_source":"metric","onset_rel_s":1200.0,"rank":6,"service":"tidb-pd","severity_z":20.394},{"evidence_source":"metric","onset_rel_s":1320.0,"rank":7,"service":"node-7","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1440.0,"rank":8,"service":"k8s-master2","severity_z":44.559},{"evidence_source":"trace","onset_rel_s":1579.8,"rank":9,"service":"cartservice","severity_z":10.229},{"evidence_source":"trace","onset_rel_s":1579.8,"rank":10,"service":"redis","severity_z":7.345},{"evidence_source":"metric","onset_rel_s":1620.0,"rank":11,"service":"adservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1860.0,"rank":12,"service":"paymentservice","severity_z":85.657},{"evidence_source":"metric","onset_rel_s":1920.0,"rank":13,"service":"emailservice","severity_z":23.988},{"evidence_source":"none","onset_rel_s":null,"rank":14,"service":"redis-cart","severity_z":0.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"redis","caller":"cartservice"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"medium","reason":"Rank node-3 first because node-3 has direct node_sockstat_TCP_inuse evidence (signed-z 999, persistence 0 bins); recommendationservice is second despite propagation rank 2 because onset ordering alone does not establish the causal origin. The remaining entries preserve evidence-supported alternatives so the ranking retains calibrated uncertainty instead of collapsing to one answer.","services":["node-3","recommendationservice","adservice-0","tidb-tidb","tidb-tikv"]}
