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
opaque_id: INC-0D7DCFD04DFC
observation_window={"duration_rel_s":2340.0,"source_metric_rows":40}
selection_summary={"candidate_count":63,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":1415,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","adservice-grpc","adservice-http","adservice2","adservice2-0","cartservice-0","cartservice-1","cartservice-2","cartservice-grpc","cartservice2-0","checkoutservice-0","checkoutservice-1","checkoutservice-2","checkoutservice-grpc","checkoutservice2-0","currencyservice-0","currencyservice-1","currencyservice-2","currencyservice-grpc","currencyservice2-0","emailservice-0","emailservice-1","emailservice-2","emailservice-grpc","emailservice2-0","frontend-0","frontend-1","frontend-2","frontend-http","frontend2-0","istio-egressgateway-7bfdcc9d86-zpjpg","istio-ingressgateway-565bffd4d-6bl7m","node-1","node-2","node-3","node-4","node-5","node-6","paymentservice-0","paymentservice-1","paymentservice-2","paymentservice-grpc","paymentservice2-0","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","productcatalogservice-grpc","productcatalogservice2-0","recommendationservice-0","recommendationservice-1","recommendationservice-2","recommendationservice-grpc","recommendationservice2-0","redis-cart-0","redis-cart2-0","shippingservice-0","shippingservice-1","shippingservice-2","shippingservice-grpc","shippingservice2-0"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[18.281,54.844,91.406,127.969,164.531,201.094,237.656,274.219,310.781,347.344,383.906,420.469,457.031,493.594,530.156,566.719,603.281,639.844,676.406,712.969,749.531,786.094,822.656,859.219,895.781,932.344,968.906,1005.469,1042.031,1078.594,1115.156,1151.719,1188.281,1224.844,1261.406,1297.969,1334.531,1371.094,1407.656,1444.219,1480.781,1517.344,1553.906,1590.469,1627.031,1663.594,1700.156,1736.719,1773.281,1809.844,1846.406,1882.969,1919.531,1956.094,1992.656,2029.219,2065.781,2102.344,2138.906,2175.469,2212.031,2248.594,2285.156,2321.719]
[M1] rank=1 service=istio-egressgateway-7bfdcc9d86-zpjpg metric=istio_agent_go_gc_duration_seconds.0.75 baseline=0.000105 peak=0.000105 signed_z=999.0 onset_bin=0 onset_rel_s=18.281 persistence_bins=40
values_compact=delta:0.000105,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-0.000001,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M2] rank=2 service=node-2 metric=system.disk.pct_usage baseline=41.43 peak=41.42 signed_z=-999.0 onset_bin=59 onset_rel_s=2175.469 persistence_bins=2
values_compact=delta:41.43,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-0.01,0.01,0,0,0,-0.01,0,0.01,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M3] rank=3 service=productcatalogservice-2 metric=container_fs_inodes./dev/vda1 baseline=0.0 peak=1.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,-1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M4] rank=4 service=productcatalogservice-2 metric=container_fs_usage_MB./dev/vda1 baseline=27.867188 peak=628.453125 signed_z=999.0 onset_bin=36 onset_rel_s=1334.531 persistence_bins=3
values_compact=delta:27.867188,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,600.585937,0,0,0,0,-600.585937,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M5] rank=5 service=node-1 metric=system.net.tcp.retrans_segs baseline=0.016 peak=16.18 signed_z=959.157 onset_bin=41 onset_rel_s=1517.344 persistence_bins=4
values_compact=delta:0,0,0,0,0.02,-0.02,0.02,0.01,-0.03,0,0.03,-0.01,0.05,-0.05,0,0,0,0.01,-0.03,0.02,0,-0.02,0.03,-0.03,0.03,0.07,0.18,-0.28,0,16.18,-16.16,-0.02,0,0,0,0,0.08,-0.08,0,0.02
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M6] rank=6 service=emailservice-1 metric=container_network_receive_MB.eth0 baseline=0.023855 peak=0.601845 signed_z=261.74 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.026141,-0.004833,0.005795,-0.003799,-0.000426,0.002741,-0.003612,0.001114,-0.002527,0.004019,0.002779,-0.008178,0.007205,-0.002449,0.002985,-0.005142,0.002376,0.000024,-0.001048,-0.000084,-0.000168,0.006827,-0.004118,-0.000973,-0.00636,0.583556,-0.578217,0.00625,-0.01318,0.008626,0.005903,-0.010091,0.003401,-0.001802,0.000159,0.000387,0.00195,-0.004688,0.006504,-0.005119
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M7] rank=7 service=cartservice-1 metric=container_fs_usage_MB./dev/vda1 baseline=47.360742 peak=0.0625 signed_z=-212.935 onset_bin=36 onset_rel_s=1334.531 persistence_bins=18
values_compact=delta:46.996094,0.039062,0.039063,0.035156,0.039063,0.035156,0.042968,0.039063,0.035156,0.039063,0.039062,0.035156,0.042969,0.039063,0.039062,0.042969,0.035156,0.039063,0.035156,0.035156,0.035156,-47.695312,0.039062,0.042969,0.042969,0.03125,0.039062,0.035157,0.039062,0.035157,0.039062,0.042969,0.039062,0.039063,0.039062,0.039063,0.039062,0.03125,0.060547,0.021484
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M8] rank=8 service=adservice-0 metric=container_network_receive_MB.eth0 baseline=0.043756 peak=0.342725 signed_z=159.664 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.045125,0.000358,-0.004575,0.003691,-0.004693,0.003421,0.002437,-0.000347,-0.003239,0.001818,-0.000262,-0.000594,0.002662,-0.005714,0.00568,-0.001093,-0.001787,0.002892,-0.003901,0.002777,-0.000138,-0.006208,0.007186,0.002807,-0.00955,0.009308,-0.007736,0.001457,-0.002663,0.298239,0.005367,-0.299396,-0.004194,0.009361,-0.003839,0.001225,-0.007895,0.009317,-0.00585,0.003759
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M9] rank=9 service=node-1 metric=system.cpu.iowait baseline=0.3405 peak=45.22 signed_z=134.461 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.19,0.06,-0.08,0.02,0,0.04,0.19,-0.32,0,0.17,-0.14,0.1,0.37,-0.43,0.31,-0.02,-0.25,1.44,-1.09,-0.35,0,0.24,0.95,-1.13,0.11,44.84,-45.14,0.02,0,6.76,-6.82,0.09,0.12,-0.02,-0.1,0.02,0.1,-0.15,-0.02,0.21
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M10] rank=10 service=cartservice-1 metric=container_network_receive_MB.eth0 baseline=0.042183 peak=0.621728 signed_z=124.304 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.045061,-0.008697,0.004844,-0.001728,0.010523,-0.007317,0.000726,-0.00089,-0.007256,0.00597,0.007295,-0.014415,0.014214,0.00056,-0.011202,0.010429,-0.006705,0.000698,-0.00229,-0.002415,0.007668,-0.003361,-0.002109,0.008009,0.574116,-0.579133,-0.011261,0.017754,-0.00737,0.00076,-0.002244,0.002185,-0.000728,0.002553,0.006451,-0.018981,0.013835,0.001246,-0.009251,0.010283
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M11] rank=11 service=paymentservice-2 metric=container_memory_usage_MB baseline=44.683594 peak=44.234375 signed_z=-76.354 onset_bin=62 onset_rel_s=2285.156 persistence_bins=2
values_compact=delta:44.683594,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-0.449219,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M12] rank=12 service=currencyservice-2 metric=container_network_receive_MB.eth0 baseline=0.06364 peak=0.37359 signed_z=74.777 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.061827,-0.004419,0.011516,-0.005116,0.001107,-0.006724,0.011829,-0.009165,0.000913,0.002925,-0.000549,-0.000365,-0.000243,0.009148,-0.012185,-0.00057,0.011906,-0.010669,-0.000088,0.000671,-0.005563,0.013242,-0.003476,0.28349,0.024148,-0.309896,-0.002911,-0.008182,0.014596,-0.00307,0.009939,-0.019985,0.019065,-0.013694,0.011687,-0.013693,0.011552,-0.012962,0.017475,-0.015385
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[1140.0,1620.0]

=== LOG SUMMARY ===
{"entries":[{"change_pct":-77.7,"n_during":27,"n_pre":121,"service":"paymentservice-1"},{"change_pct":-77.5,"n_during":27,"n_pre":120,"service":"emailservice-2"},{"change_pct":-76.7,"n_during":147,"n_pre":632,"service":"checkoutservice-0"},{"change_pct":-76.7,"n_during":27,"n_pre":116,"service":"paymentservice-0"},{"change_pct":-76.5,"n_during":27,"n_pre":115,"service":"paymentservice-2"},{"change_pct":-76.4,"n_during":153,"n_pre":648,"service":"checkoutservice-2"},{"change_pct":-76.0,"n_during":4593,"n_pre":19168,"service":"frontend-1"},{"change_pct":-75.7,"n_during":152,"n_pre":625,"service":"checkoutservice-1"}],"mode":"volume","omitted_services":23,"service_count":31}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":127.0,"error_pct":0.0,"p95_during_ms":0.19525,"p95_pre_ms":0.086,"service":"shippingservice-0","spans":328},{"delta_pct":-100.0,"error_pct":0.0,"p95_during_ms":0.0,"p95_pre_ms":1.0,"service":"cartservice-0","spans":2373},{"delta_pct":30.4,"error_pct":0.0,"p95_during_ms":61.3595,"p95_pre_ms":47.05875,"service":"checkoutservice-1","spans":538},{"delta_pct":-26.9,"error_pct":0.0,"p95_during_ms":0.019,"p95_pre_ms":0.026,"service":"adservice-1","spans":713},{"delta_pct":-23.8,"error_pct":0.0,"p95_during_ms":0.022099999999999963,"p95_pre_ms":0.029,"service":"adservice-0","spans":713},{"delta_pct":-15.2,"error_pct":0.0,"p95_during_ms":0.267,"p95_pre_ms":0.315,"service":"emailservice-2","spans":48},{"delta_pct":14.4,"error_pct":0.0,"p95_during_ms":0.09359999999999997,"p95_pre_ms":0.08179999999999996,"service":"shippingservice-2","spans":328},{"delta_pct":11.6,"error_pct":0.0,"p95_during_ms":0.1828,"p95_pre_ms":0.1638,"service":"paymentservice-0","spans":46}],"omitted_services":32,"service_count":40}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=16 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":1200.0,"rank":1,"service":"istio-egressgateway","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1200.0,"rank":2,"service":"productcatalogservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1260.0,"rank":3,"service":"cartservice","severity_z":212.935},{"evidence_source":"metric","onset_rel_s":1380.0,"rank":4,"service":"currencyservice","severity_z":74.777},{"evidence_source":"metric","onset_rel_s":1500.0,"rank":5,"service":"emailservice","severity_z":261.74},{"evidence_source":"metric","onset_rel_s":1500.0,"rank":6,"service":"node-5","severity_z":71.127},{"evidence_source":"metric","onset_rel_s":1620.0,"rank":7,"service":"recommendationservice","severity_z":45.866},{"evidence_source":"metric","onset_rel_s":1740.0,"rank":8,"service":"node-1","severity_z":959.157},{"evidence_source":"metric","onset_rel_s":1740.0,"rank":9,"service":"adservice","severity_z":159.664},{"evidence_source":"metric","onset_rel_s":1800.0,"rank":10,"service":"node-4","severity_z":42.544},{"evidence_source":"metric","onset_rel_s":1860.0,"rank":11,"service":"node-2","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":2040.0,"rank":12,"service":"node-6","severity_z":30.513},{"evidence_source":"metric","onset_rel_s":2220.0,"rank":13,"service":"node-3","severity_z":45.654},{"evidence_source":"metric","onset_rel_s":2280.0,"rank":14,"service":"paymentservice","severity_z":76.354}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"productcatalogservice","caller":"recommendationservice"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"high","reason":"Rank productcatalogservice-2 first because productcatalogservice-2 has direct container_fs_inodes./dev/vda1 evidence (signed-z 999, persistence 0 bins); although recommendationservice-0 is salient, the caller path recommendationservice -> productcatalogservice means a disturbance in the callee can propagate back toward that caller-side symptom.","services":["productcatalogservice-2","recommendationservice-0"]}
