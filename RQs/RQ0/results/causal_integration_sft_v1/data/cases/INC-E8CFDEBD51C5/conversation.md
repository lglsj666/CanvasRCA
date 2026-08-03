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
opaque_id: INC-E8CFDEBD51C5
observation_window={"duration_rel_s":2340.0,"source_metric_rows":40}
selection_summary={"candidate_count":63,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":1421,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","adservice-grpc","adservice-http","adservice2","adservice2-0","cartservice-0","cartservice-1","cartservice-2","cartservice-grpc","cartservice2-0","checkoutservice-0","checkoutservice-1","checkoutservice-2","checkoutservice-grpc","checkoutservice2-0","currencyservice-0","currencyservice-1","currencyservice-2","currencyservice-grpc","currencyservice2-0","emailservice-0","emailservice-1","emailservice-2","emailservice-grpc","emailservice2-0","frontend-0","frontend-1","frontend-2","frontend-http","frontend2-0","istio-egressgateway-7bfdcc9d86-zpjpg","istio-ingressgateway-565bffd4d-6bl7m","node-1","node-2","node-3","node-4","node-5","node-6","paymentservice-0","paymentservice-1","paymentservice-2","paymentservice-grpc","paymentservice2-0","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","productcatalogservice-grpc","productcatalogservice2-0","recommendationservice-0","recommendationservice-1","recommendationservice-2","recommendationservice-grpc","recommendationservice2-0","redis-cart-0","redis-cart2-0","shippingservice-0","shippingservice-1","shippingservice-2","shippingservice-grpc","shippingservice2-0"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[18.281,54.844,91.406,127.969,164.531,201.094,237.656,274.219,310.781,347.344,383.906,420.469,457.031,493.594,530.156,566.719,603.281,639.844,676.406,712.969,749.531,786.094,822.656,859.219,895.781,932.344,968.906,1005.469,1042.031,1078.594,1115.156,1151.719,1188.281,1224.844,1261.406,1297.969,1334.531,1371.094,1407.656,1444.219,1480.781,1517.344,1553.906,1590.469,1627.031,1663.594,1700.156,1736.719,1773.281,1809.844,1846.406,1882.969,1919.531,1956.094,1992.656,2029.219,2065.781,2102.344,2138.906,2175.469,2212.031,2248.594,2285.156,2321.719]
[M1] rank=1 service=frontend-2 metric=istio_request_bytes.http.0. baseline=0.0 peak=167.5 signed_z=999.0 onset_bin=36 onset_rel_s=1334.531 persistence_bins=2
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,167.5,0,-167.5,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M2] rank=2 service=frontend-2 metric=istio_request_duration_milliseconds.http.0. baseline=0.0 peak=30250.0 signed_z=999.0 onset_bin=36 onset_rel_s=1334.531 persistence_bins=2
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,30250,0,-30250,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M3] rank=3 service=frontend-2 metric=istio_requests.http.0. baseline=0.0 peak=1.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,-1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M4] rank=4 service=node-2 metric=system.disk.pct_usage baseline=41.44 peak=41.45 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:41.44,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.01,0,-0.01,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M5] rank=5 service=node-3 metric=system.disk.pct_usage baseline=41.9 peak=41.89 signed_z=-999.0 onset_bin=41 onset_rel_s=1517.344 persistence_bins=15
values_compact=delta:41.9,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-0.01,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M6] rank=6 service=node-6 metric=system.disk.free baseline=1418870071.4655 peak=2033398198.86 signed_z=999.0 onset_bin=41 onset_rel_s=1517.344 persistence_bins=15
values_compact=delta:1418971648,-30720,-4864,-16298.67,-18944,15018.67,-28842.67,-23552,-16725.33,-27562.67,88490.67,-2560,-33024,-31402.67,-29866.66,38400,-18005.34,-20224,-17408,-14677.33,-1365.33,-5546.67,-21162.67,-22442.66,30378.66,614639457.53,-189147.43,-215478.86,-175396.57,34523.43,-614442544.76,-20480,-25173.34,28586.67,-29269.33,-22272,-26282.67,85162.67,28501.33,-12117.33
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M7] rank=7 service=node-6 metric=system.disk.pct_usage baseline=18.1865 peak=26.91 signed_z=999.0 onset_bin=41 onset_rel_s=1517.344 persistence_bins=5
values_compact=delta:18.18,0,0,0,0,0,0,0.01,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,8.72,0,0,0,0,-8.72,0,0,0,0,0,0.01,-0.01,0.01,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M8] rank=8 service=node-6 metric=system.disk.total baseline=5101719893.33 peak=8303560996.57 signed_z=999.0 onset_bin=41 onset_rel_s=1517.344 persistence_bins=5
values_compact=delta:5101719893.33,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,3201841103.24,0,0,0,0,-3201841103.24,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M9] rank=9 service=node-6 metric=system.disk.used baseline=3661714551.4675 peak=6252627090.29 signed_z=999.0 onset_bin=41 onset_rel_s=1517.344 persistence_bins=15
values_compact=delta:3661612714.67,31061.33,5120,16042.67,18773.33,-15018.67,29013.34,23552,16725.33,27648,-88405.33,2389.33,32768,31744,29696,-38570.67,18090.67,20138.67,17408,14677.33,1706.67,5461.33,21162.67,22186.66,-30037.33,2590221165.71,188416,215917.72,175542.86,-34523.43,-2590418017.53,20138.67,25600,-28672,29013.33,22528,26282.67,-84992,-28672,11946.67
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M10] rank=10 service=node-6 metric=system.fs.inodes.free baseline=3846916846.933 peak=6566331538.29 signed_z=999.0 onset_bin=41 onset_rel_s=1517.344 persistence_bins=15
values_compact=delta:3847280981.33,-130048,-29696,-38570.66,-86016,86698.66,-124928,-69290.66,-77141.34,-86698.66,344405.33,-18773.33,-107861.34,-135509.33,-95573.33,143360,-48469.34,-91136,-45397.33,-65536,18432,-38570.67,-60757.33,-100010.67,146090.67,2719761554.29,-764196.58,-841435.42,-709193.15,159158.86,-2718985557.33,-30720,-108885.34,140288,-127317.33,-97280,-81237.33,333141.33,136874.67,-57344
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M11] rank=11 service=node-6 metric=system.fs.inodes.in_use baseline=1.17 peak=1.01 signed_z=-999.0 onset_bin=41 onset_rel_s=1517.344 persistence_bins=5
values_compact=delta:1.17,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-0.16,0,0,0,0,0.16,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M12] rank=12 service=node-6 metric=system.fs.inodes.total baseline=3848489062.401 peak=6568633490.29 signed_z=999.0 onset_bin=41 onset_rel_s=1517.344 persistence_bins=15
values_compact=delta:3848853162.67,-130048,-29696,-38570.67,-86016,86698.67,-124928,-69290.67,-77141.33,-86698.67,344405.33,-18773.33,-107861.33,-135168,-95914.67,143360,-48469.33,-90794.67,-45738.67,-65536,18432,-38570.66,-60416,-100352,146090.66,2720491324.96,-764196.58,-841435.42,-709193.15,159158.86,-2719714986.67,-30720,-108885.33,140288,-127317.33,-97280,-81237.34,332800,136874.67,-57002.67
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[1260.0,1440.0]

=== LOG SUMMARY ===
{"entries":[{"error_logs":3,"error_pct":0.1,"service":"recommendationservice-2","total_logs":2974},{"error_logs":1,"error_pct":0.01,"service":"frontend-2","total_logs":7896}],"mode":"errors","omitted_services":29,"service_count":31}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":53130.5,"error_pct":0.0,"p95_during_ms":1640.11175,"p95_pre_ms":3.0811499999999996,"service":"recommendationservice-2","spans":1628},{"delta_pct":-100.0,"error_pct":0.0,"p95_during_ms":0.0,"p95_pre_ms":1.0,"service":"cartservice-2","spans":2347},{"delta_pct":-24.6,"error_pct":0.0,"p95_during_ms":0.09079999999999995,"p95_pre_ms":0.12049999999999988,"service":"shippingservice-1","spans":328},{"delta_pct":19.7,"error_pct":0.0,"p95_during_ms":0.031549999999999995,"p95_pre_ms":0.026350000000000023,"service":"adservice-0","spans":704},{"delta_pct":19.5,"error_pct":0.0,"p95_during_ms":0.2162,"p95_pre_ms":0.18084999999999998,"service":"paymentservice-1","spans":47},{"delta_pct":-17.3,"error_pct":0.0,"p95_during_ms":0.08929999999999999,"p95_pre_ms":0.108,"service":"shippingservice-0","spans":324},{"delta_pct":-13.7,"error_pct":0.0,"p95_during_ms":44.71189999999998,"p95_pre_ms":51.78494999999988,"service":"checkoutservice-1","spans":544},{"delta_pct":-12.7,"error_pct":0.0,"p95_during_ms":0.01919999999999999,"p95_pre_ms":0.022,"service":"adservice-2","spans":705}],"omitted_services":32,"service_count":40}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=16 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":1200.0,"rank":1,"service":"adservice2","severity_z":54.467},{"evidence_source":"metric","onset_rel_s":1260.0,"rank":2,"service":"emailservice","severity_z":275.977},{"evidence_source":"trace","onset_rel_s":1291.8,"rank":3,"service":"recommendationservice","severity_z":60.205},{"evidence_source":"metric","onset_rel_s":1320.0,"rank":4,"service":"frontend","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1500.0,"rank":5,"service":"node-3","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1500.0,"rank":6,"service":"node-6","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1500.0,"rank":7,"service":"cartservice","severity_z":142.799},{"evidence_source":"metric","onset_rel_s":1500.0,"rank":8,"service":"node-5","severity_z":102.407},{"evidence_source":"metric","onset_rel_s":1560.0,"rank":9,"service":"currencyservice","severity_z":142.857},{"evidence_source":"metric","onset_rel_s":1680.0,"rank":10,"service":"node-2","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1680.0,"rank":11,"service":"paymentservice","severity_z":101.483},{"evidence_source":"trace","onset_rel_s":1681.8,"rank":12,"service":"cartservice2","severity_z":30.0},{"evidence_source":"metric","onset_rel_s":2220.0,"rank":13,"service":"node-1","severity_z":106.336},{"evidence_source":"trace","onset_rel_s":2315.4,"rank":14,"service":"adservice","severity_z":5.608}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"adservice","caller":"frontend"},{"callee":"cartservice","caller":"frontend"},{"callee":"currencyservice","caller":"frontend"},{"callee":"recommendationservice","caller":"frontend"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"high","reason":"Rank recommendationservice-2 first because recommendationservice-2 has direct trace evidence; although frontend-0 is salient, the caller path frontend -> recommendationservice means a disturbance in the callee can propagate back toward that caller-side symptom.","services":["recommendationservice-2","frontend-0"]}
