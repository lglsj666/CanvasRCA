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
opaque_id: INC-8A7061E2EB11
observation_window={"duration_rel_s":2160.0,"source_metric_rows":37}
selection_summary={"candidate_count":60,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":456,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","cartservice","cartservice-0","cartservice-1","cartservice-2","checkoutservice","checkoutservice-0","checkoutservice-1","checkoutservice-2","currencyservice","currencyservice-0","currencyservice-1","currencyservice-2","emailservice","emailservice-0","emailservice-1","emailservice-2","example-ant-10-29184000-wx4rn","example-ant-29184000-cgbbl","frontend","frontend-0","frontend-1","frontend-2","hipstershop","k8s-master1","k8s-master2","k8s-master3","node-1","node-2","node-3","node-4","node-5","node-6","node-7","node-8","paymentservice","paymentservice-0","paymentservice-1","paymentservice-2","productcatalogservice","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","recommendationservice","recommendationservice-0","recommendationservice-1","recommendationservice-2","redis","redis-cart","redis-cart-0","shippingservice","shippingservice-0","shippingservice-1","shippingservice-2","tidb-pd","tidb-tidb","tidb-tikv"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[16.875,50.625,84.375,118.125,151.875,185.625,219.375,253.125,286.875,320.625,354.375,388.125,421.875,455.625,489.375,523.125,556.875,590.625,624.375,658.125,691.875,725.625,759.375,793.125,826.875,860.625,894.375,928.125,961.875,995.625,1029.375,1063.125,1096.875,1130.625,1164.375,1198.125,1231.875,1265.625,1299.375,1333.125,1366.875,1400.625,1434.375,1468.125,1501.875,1535.625,1569.375,1603.125,1636.875,1670.625,1704.375,1738.125,1771.875,1805.625,1839.375,1873.125,1906.875,1940.625,1974.375,2008.125,2041.875,2075.625,2109.375,2143.125]
[M1] rank=1 service=tidb-tikv metric=raft_apply_wait baseline=0.0 peak=0.02 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.02,-0.02,0,0
missing_mask_bits=0011101001010101001010100101010100101010010101010010101001010100
observed_counts_compact=csv:1,1,0,0,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1
[M2] rank=2 service=frontend-0 metric=pod_network_transmit_bytes baseline=58.412353 peak=8656.45 signed_z=484.148 onset_bin=55 onset_rel_s=1873.125 persistence_bins=6
values_compact=delta:79.71,-41.95,30.86,-28.18,12.4,-18.27,30.92,-20.19,18.69,-2.74,7.65,-27.26,51.32,-57.44,54.48,-26.55,-12.88,18.97,-22.47,-10.49,15.17,1.96,-14.65,29.34,-28.83,2.67,27.14,2888.77,2594.26,-1719.61,1695.77,-2070.22,2928.45,561.05,1708.6,-5597.47
missing_mask_bits=0011101001010101001010100101010100101010010101010010101001010100
observed_counts_compact=csv:1,1,0,0,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1
[M3] rank=3 service=currencyservice-2 metric=request baseline=9.777778 peak=158.0 signed_z=67.377 onset_bin=48 onset_rel_s=1636.875 persistence_bins=10
values_compact=delta:10,0,0,0,-2,2,0,2,-4,0,2,4,-10,8,-4,4,0,-4,4,-6,10,-12,6,0,2,-4,4,112,-42,42,-60,80,-82,88,-66,30,44
missing_mask_bits=0010101001010101001010100101010100101010010101010010101001010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1
[M4] rank=4 service=currencyservice-2 metric=response baseline=9.777778 peak=154.0 signed_z=65.559 onset_bin=48 onset_rel_s=1636.875 persistence_bins=10
values_compact=delta:10,0,0,0,-2,2,0,2,-4,0,2,4,-10,8,-4,4,0,-4,4,-6,10,-12,6,0,2,-4,4,111,-41,41,-59,78,-80,84,-62,30,40
missing_mask_bits=0010101001010101001010100101010100101010010101010010101001010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1
[M5] rank=5 service=frontend-0 metric=pod_network_receive_bytes baseline=61.385882 peak=1494.43 signed_z=64.76 onset_bin=55 onset_rel_s=1873.125 persistence_bins=6
values_compact=delta:92.99,-55.23,30.86,-28.18,12.4,-18.27,30.92,-20.19,18.69,-2.74,19.89,-39.5,61.93,-68.05,68.9,-40.97,-12.88,18.97,-22.47,-10.49,15.17,1.96,-14.65,41.5,-40.99,2.67,27.14,567.21,299.13,-134.93,167.57,-227.76,370.15,353.52,30.16,-857.25
missing_mask_bits=0011101001010101001010100101010100101010010101010010101001010100
observed_counts_compact=csv:1,1,0,0,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1
[M6] rank=6 service=frontend-0 metric=pod_network_transmit_packets baseline=0.882941 peak=14.87 signed_z=60.081 onset_bin=55 onset_rel_s=1873.125 persistence_bins=6
values_compact=delta:1.11,-0.52,0.47,-0.41,0.2,-0.33,0.51,-0.29,0.23,-0.04,0.04,-0.3,0.67,-0.78,0.68,-0.25,-0.2,0.28,-0.36,-0.14,0.23,0.01,-0.2,0.35,-0.34,0.06,0.39,5.44,3.03,-1.66,1.83,-2.39,4.04,2.99,0.52,-8.46
missing_mask_bits=0011101001010101001010100101010100101010010101010010101001010100
observed_counts_compact=csv:1,1,0,0,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1
[M7] rank=7 service=frontend-0 metric=pod_network_receive_packets baseline=0.888824 peak=11.53 signed_z=44.845 onset_bin=55 onset_rel_s=1873.125 persistence_bins=6
values_compact=delta:1.16,-0.57,0.47,-0.41,0.2,-0.33,0.51,-0.29,0.23,-0.04,0.09,-0.35,0.67,-0.78,0.68,-0.25,-0.2,0.28,-0.36,-0.14,0.23,0.01,-0.2,0.4,-0.39,0.06,0.39,3.85,2.77,-1.55,1.61,-1.87,2.63,3.02,-0.02,-6.49
missing_mask_bits=0011101001010101001010100101010100101010010101010010101001010100
observed_counts_compact=csv:1,1,0,0,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1
[M8] rank=8 service=shippingservice-2 metric=request baseline=13.333333 peak=44.0 signed_z=10.842 onset_bin=48 onset_rel_s=1636.875 persistence_bins=9
values_compact=delta:12,4,-4,0,4,-6,2,2,2,-8,8,0,-8,8,-4,2,4,-6,2,-6,8,-12,12,0,-2,-6,12,-16,40,-36,22,-6,6,-6,8,-8,4
missing_mask_bits=0010101001010101001010100101010100101010010101010010101001010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1
[M9] rank=9 service=shippingservice-2 metric=response baseline=13.333333 peak=44.0 signed_z=10.842 onset_bin=48 onset_rel_s=1636.875 persistence_bins=9
values_compact=delta:12,4,-4,0,4,-6,2,2,2,-8,8,0,-8,8,-4,2,4,-6,2,-6,8,-12,12,0,-2,-6,12,-16,40,-36,22,-6,6,-6,8,-8,4
missing_mask_bits=0010101001010101001010100101010100101010010101010010101001010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1
[M10] rank=10 service=redis-cart-0 metric=timeout baseline=0.0 peak=1.0 signed_z=10.733 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,-1,1,-1,0,1,-1,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010101001010101001010100101010100101010010101010010101001010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1
[M11] rank=11 service=redis-cart metric=timeout baseline=0.0 peak=1.0 signed_z=10.733 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,-1,1,-1,0,1,-1,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010101001010101001010100101010100101010010101010010101001010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1
[M12] rank=12 service=example-ant-29184000-cgbbl metric=pod_network_receive_packets baseline=0.0 peak=2.71 signed_z=10.444 onset_bin=55 onset_rel_s=1873.125 persistence_bins=6
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.54,0.32,-0.47,1.79,-0.91,1.36,-0.29,0.37,-0.18
missing_mask_bits=0011101001010101001010100101010100101010010101010010101001010100
observed_counts_compact=csv:1,1,0,0,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[1560.0,2160.0]

=== LOG SUMMARY ===
{"entries":[{"change_pct":5616.7,"n_during":343,"n_pre":6,"service":"frontend-0"},{"change_pct":220.4,"n_during":865,"n_pre":270,"service":"currencyservice-2"},{"change_pct":-75.0,"n_during":5,"n_pre":20,"service":"redis-cart-0"},{"change_pct":-60.4,"n_during":568,"n_pre":1436,"service":"adservice-1"},{"change_pct":-59.8,"n_during":2910,"n_pre":7244,"service":"frontend-2"},{"change_pct":-59.2,"n_during":6405,"n_pre":15688,"service":"currencyservice-1"},{"change_pct":-58.6,"n_during":11484,"n_pre":27729,"service":"cartservice-1"},{"change_pct":-57.4,"n_during":652,"n_pre":1530,"service":"shippingservice-0"}],"mode":"volume","omitted_services":15,"service_count":23}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":11.8,"error_pct":0.0,"p95_during_ms":1.152,"p95_pre_ms":1.0305,"service":"emailservice","spans":187},{"delta_pct":-9.3,"error_pct":0.0,"p95_during_ms":0.42969999999999997,"p95_pre_ms":0.4735,"service":"shippingservice","spans":1303},{"delta_pct":3.7,"error_pct":0.0,"p95_during_ms":2.9386999999999994,"p95_pre_ms":2.8327999999999993,"service":"redis","spans":4902},{"delta_pct":-1.7,"error_pct":0.0,"p95_during_ms":5.152099999999999,"p95_pre_ms":5.2415,"service":"recommendationservice","spans":6780},{"delta_pct":1.0,"error_pct":0.0,"p95_during_ms":4.314200000000002,"p95_pre_ms":4.269399999999997,"service":"cartservice","spans":4529},{"delta_pct":-1.0,"error_pct":0.0,"p95_during_ms":135.63115000000002,"p95_pre_ms":137.00254999999999,"service":"checkoutservice","spans":2194},{"delta_pct":-0.4,"error_pct":0.0,"p95_during_ms":14.7267,"p95_pre_ms":14.781,"service":"productcatalogservice","spans":25484},{"delta_pct":-0.3,"error_pct":0.0,"p95_during_ms":92.70224999999999,"p95_pre_ms":92.96799999999988,"service":"frontend","spans":55431}],"omitted_services":0,"service_count":8}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=5 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":1080.0,"rank":1,"service":"redis-cart","severity_z":10.733},{"evidence_source":"metric","onset_rel_s":1680.0,"rank":2,"service":"shippingservice","severity_z":10.842},{"evidence_source":"metric","onset_rel_s":1980.0,"rank":3,"service":"tidb-tikv","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1980.0,"rank":4,"service":"frontend","severity_z":484.148},{"evidence_source":"metric","onset_rel_s":1980.0,"rank":5,"service":"currencyservice","severity_z":67.377},{"evidence_source":"metric","onset_rel_s":1980.0,"rank":6,"service":"example-ant","severity_z":10.444},{"evidence_source":"none","onset_rel_s":null,"rank":7,"service":"tidb-tidb","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":8,"service":"recommendationservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":9,"service":"adservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":10,"service":"productcatalogservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":11,"service":"k8s-master1","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":12,"service":"paymentservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":13,"service":"hipstershop","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":14,"service":"cartservice","severity_z":0.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"cartservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"frontend"},{"callee":"recommendationservice","caller":"frontend"},{"callee":"shippingservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"recommendationservice"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

[excluded before optimizer]
