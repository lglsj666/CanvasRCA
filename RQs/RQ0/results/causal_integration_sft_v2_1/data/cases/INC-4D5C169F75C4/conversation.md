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
opaque_id: INC-4D5C169F75C4
observation_window={"duration_rel_s":2340.0,"source_metric_rows":40}
selection_summary={"candidate_count":63,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":1438,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","adservice-grpc","adservice-http","adservice2","adservice2-0","cartservice-0","cartservice-1","cartservice-2","cartservice-grpc","cartservice2-0","checkoutservice-0","checkoutservice-1","checkoutservice-2","checkoutservice-grpc","checkoutservice2-0","currencyservice-0","currencyservice-1","currencyservice-2","currencyservice-grpc","currencyservice2-0","emailservice-0","emailservice-1","emailservice-2","emailservice-grpc","emailservice2-0","frontend-0","frontend-1","frontend-2","frontend-http","frontend2-0","istio-egressgateway-7bfdcc9d86-zpjpg","istio-ingressgateway-565bffd4d-6bl7m","node-1","node-2","node-3","node-4","node-5","node-6","paymentservice-0","paymentservice-1","paymentservice-2","paymentservice-grpc","paymentservice2-0","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","productcatalogservice-grpc","productcatalogservice2-0","recommendationservice-0","recommendationservice-1","recommendationservice-2","recommendationservice-grpc","recommendationservice2-0","redis-cart-0","redis-cart2-0","shippingservice-0","shippingservice-1","shippingservice-2","shippingservice-grpc","shippingservice2-0"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[18.281,54.844,91.406,127.969,164.531,201.094,237.656,274.219,310.781,347.344,383.906,420.469,457.031,493.594,530.156,566.719,603.281,639.844,676.406,712.969,749.531,786.094,822.656,859.219,895.781,932.344,968.906,1005.469,1042.031,1078.594,1115.156,1151.719,1188.281,1224.844,1261.406,1297.969,1334.531,1371.094,1407.656,1444.219,1480.781,1517.344,1553.906,1590.469,1627.031,1663.594,1700.156,1736.719,1773.281,1809.844,1846.406,1882.969,1919.531,1956.094,1992.656,2029.219,2065.781,2102.344,2138.906,2175.469,2212.031,2248.594,2285.156,2321.719]
[M1] rank=1 service=adservice metric=jvm_threads_started baseline=0.0 peak=0.833333 signed_z=999.0 onset_bin=62 onset_rel_s=2285.156 persistence_bins=2
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.166667,0.666666
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M2] rank=2 service=recommendationservice-2 metric=container_cpu_cfs_throttled_seconds baseline=0.00117 peak=6.865597 signed_z=999.0 onset_bin=31 onset_rel_s=1151.719 persistence_bins=4
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.023408,2.044126,-2.067534,0,0,0,1.763414,5.102183,-6.865597,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M3] rank=3 service=node-1 metric=system.net.tcp.retrans_segs baseline=0.0195 peak=22.02 signed_z=604.457 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0.13,-0.13,0.02,0,-0.02,0.02,-0.02,0.12,-0.1,-0.02,0.02,0,-0.02,0,0,0.02,-0.02,0,0.02,-0.02,0,0.03,-0.03,0,0.05,21.97,-22.02,0,0.02,-0.02,0.02,0.01,-0.01,0,-0.02,0.02,-0.02
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M4] rank=4 service=recommendationservice-2 metric=container_cpu_cfs_throttled_periods baseline=0.025 peak=36.5 signed_z=334.718 onset_bin=31 onset_rel_s=1151.719 persistence_bins=4
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.5,14,-14.5,0,0,0,13.5,23,-36.5,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M5] rank=5 service=emailservice-2 metric=container_network_receive_MB.eth0 baseline=0.024641 peak=0.610206 signed_z=307.672 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.024393,-0.000692,0.000628,0.002536,-0.003678,0.002576,-0.001224,-0.003467,0.00515,-0.002664,0.002082,-0.001765,0.000312,0.001583,-0.003471,0.000949,0.006426,-0.002294,-0.004529,0.001423,-0.001656,0.006642,0.580946,-0.586991,-0.000129,0.000742,0.001636,0.000423,-0.002207,0.000878,0.000089,-0.002907,0.004281,-0.001126,-0.000624,0.001179,-0.003696,0.005466,-0.00493,0.002578
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M6] rank=6 service=recommendationservice-1 metric=container_cpu_usage_seconds baseline=0.089879 peak=2.176423 signed_z=287.125 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.08374,0.002729,0.000708,0.009125,-0.012876,0.016768,-0.020363,0.013938,-0.009938,0.011361,-0.017137,0.031029,-0.021211,0.003647,-0.001695,0.00431,0.002217,-0.010621,-0.001787,0.007189,0.689339,-0.680581,0.000144,-0.003877,-0.008391,-0.018429,2.107085,-2.080383,-0.008298,0.002195,0.003359,0.003254,-0.003571,-0.003928,0.018086,-0.026928,0.010373,-0.004064,0.002782,0.002597
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M7] rank=7 service=paymentservice2-0 metric=container_network_receive_MB.eth0 baseline=0.022446 peak=0.602429 signed_z=269.326 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.023232,-0.000011,-0.001331,-0.004305,0.009274,-0.002795,-0.002599,-0.002246,0.004012,-0.00043,0.000194,-0.000467,-0.002623,0.003159,0.002971,-0.006568,0.003586,0.000336,0.00034,-0.002538,0.000201,-0.000292,0.00253,-0.001157,0.000866,-0.00124,-0.000472,-0.004085,0.010383,0.574504,-0.581597,0.00258,-0.002033,-0.000877,0.002083,0.002296,-0.003824,0.002185,-0.001484,-0.000599
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M8] rank=8 service=recommendationservice-1 metric=container_cpu_user_seconds baseline=0.0675 peak=2.005 signed_z=258.333 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.07,0,-0.01,0.015,-0.01,0.01,-0.025,0.02,-0.01,0.005,-0.005,0.02,-0.015,0.005,0,0,0.01,-0.025,0.015,0,0.57,-0.565,-0.01,0.005,0.01,-0.025,1.95,-1.925,-0.015,0.01,-0.01,0.005,-0.005,0.005,0.015,-0.025,0.005,0,0,0.005
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M9] rank=9 service=adservice-0 metric=container_network_receive_MB.eth0 baseline=0.043501 peak=0.63423 signed_z=218.212 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.03996,0.004889,0.000422,-0.003344,0.000688,0.002976,-0.006243,0.006893,0.001903,-0.009977,0.003906,0.00441,0.000519,-0.000738,-0.002275,-0.003556,0.001149,0.002922,-0.001218,-0.001001,-0.00198,0.006378,-0.00315,0.002559,0.588138,-0.587388,-0.001593,-0.007596,0.007292,0.000142,-0.002314,-0.003158,0.006912,-0.007122,0.007188,-0.005331,0.007188,-0.012146,0.00738,0.001032
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M10] rank=10 service=shippingservice2-0 metric=container_network_receive_MB.eth0 baseline=0.029776 peak=0.612909 signed_z=207.299 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.029294,-0.004202,0.008389,-0.004808,0.00619,-0.008388,0.004587,-0.000395,-0.006098,0.009247,-0.001676,-0.003243,-0.000261,0.002011,-0.003229,0.006135,-0.004259,0.001387,-0.003926,0.002753,0.003592,-0.005945,0.003331,-0.000709,-0.002544,0.585676,-0.579837,-0.010683,0.014302,-0.011909,0.011012,-0.011421,0.008079,-0.002045,0.003741,-0.003602,-0.003626,0.000959,0.007668,-0.004757
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M11] rank=11 service=cartservice-2 metric=container_fs_usage_MB./dev/vda1 baseline=46.670605 peak=0.097656 signed_z=-205.6 onset_bin=49 onset_rel_s=1809.844 persistence_bins=10
values_compact=delta:46.287109,0.056641,0.039062,0.019532,0.058594,0.035156,0.039062,0.035156,0.042969,0.039063,0.039062,0.039063,0.039062,0.039063,0.039062,0.042969,0.035156,0.019531,0.066407,0.035156,0.039063,0.039062,0.019531,0.041016,0.060547,0.021484,0.052734,0.019532,0.0625,0.039062,0.019532,0.058593,0.019531,0.058594,0.035156,0.042969,0.035157,0.023437,0.058594,-47.695313
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M12] rank=12 service=paymentservice-2 metric=container_network_receive_MB.eth0 baseline=0.022916 peak=0.373892 signed_z=201.735 onset_bin=49 onset_rel_s=1809.844 persistence_bins=2
values_compact=delta:0.020753,0.003509,-0.000238,-0.004894,0.007652,-0.005389,0.001149,0.003388,-0.004157,0.001124,-0.000365,0.000304,-0.000919,0.000775,0.001285,-0.001264,0.002524,-0.003204,-0.00051,0.001852,-0.001674,0.000156,0.00141,-0.000403,-0.000598,0.005483,-0.006314,0.00298,-0.003164,0.002547,0.350094,-0.001541,-0.350907,0.001074,0.000285,0.00149,-0.002402,0.002042,-0.001969,0.000333
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[1440.0,1620.0]

=== LOG SUMMARY ===
{"entries":[{"change_pct":-93.8,"n_during":48,"n_pre":771,"service":"checkoutservice-2"},{"change_pct":-93.7,"n_during":48,"n_pre":764,"service":"checkoutservice-0"},{"change_pct":-93.6,"n_during":9,"n_pre":140,"service":"paymentservice-2"},{"change_pct":-93.4,"n_during":9,"n_pre":137,"service":"paymentservice-0"},{"change_pct":-93.0,"n_during":87,"n_pre":1241,"service":"shippingservice-1"},{"change_pct":-92.9,"n_during":10,"n_pre":140,"service":"emailservice-0"},{"change_pct":-92.9,"n_during":88,"n_pre":1233,"service":"shippingservice-2"},{"change_pct":-92.6,"n_during":10,"n_pre":135,"service":"emailservice-1"}],"mode":"volume","omitted_services":23,"service_count":31}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":46.5,"error_pct":0.0,"p95_during_ms":69.2089,"p95_pre_ms":47.24715,"service":"checkoutservice-1","spans":560},{"delta_pct":20.8,"error_pct":0.0,"p95_during_ms":0.029,"p95_pre_ms":0.024,"service":"adservice-0","spans":726},{"delta_pct":20.0,"error_pct":0.0,"p95_during_ms":0.024,"p95_pre_ms":0.02,"service":"adservice-2","spans":728},{"delta_pct":-19.8,"error_pct":0.0,"p95_during_ms":0.02325,"p95_pre_ms":0.029,"service":"adservice-1","spans":728},{"delta_pct":-19.5,"error_pct":0.0,"p95_during_ms":37.80574999999998,"p95_pre_ms":46.944,"service":"checkoutservice-0","spans":572},{"delta_pct":-18.1,"error_pct":0.0,"p95_during_ms":0.07859999999999999,"p95_pre_ms":0.096,"service":"shippingservice-2","spans":339},{"delta_pct":-17.3,"error_pct":0.0,"p95_during_ms":0.08195000000000001,"p95_pre_ms":0.09914999999999999,"service":"shippingservice-1","spans":340},{"delta_pct":-16.4,"error_pct":0.0,"p95_during_ms":0.14759999999999998,"p95_pre_ms":0.17659999999999998,"service":"paymentservice2-0","spans":60}],"omitted_services":32,"service_count":40}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=15 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":1260.0,"rank":1,"service":"shippingservice","severity_z":181.245},{"evidence_source":"metric","onset_rel_s":1320.0,"rank":2,"service":"emailservice","severity_z":307.672},{"evidence_source":"metric","onset_rel_s":1380.0,"rank":3,"service":"checkoutservice","severity_z":74.167},{"evidence_source":"metric","onset_rel_s":1440.0,"rank":4,"service":"redis-cart","severity_z":84.945},{"evidence_source":"metric","onset_rel_s":1500.0,"rank":5,"service":"shippingservice2","severity_z":207.299},{"evidence_source":"trace","onset_rel_s":1535.4,"rank":6,"service":"recommendationservice2","severity_z":187.356},{"evidence_source":"metric","onset_rel_s":1560.0,"rank":7,"service":"recommendationservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1560.0,"rank":8,"service":"checkoutservice2","severity_z":80.103},{"evidence_source":"metric","onset_rel_s":1680.0,"rank":9,"service":"node-1","severity_z":604.457},{"evidence_source":"metric","onset_rel_s":1740.0,"rank":10,"service":"paymentservice2","severity_z":269.326},{"evidence_source":"metric","onset_rel_s":1800.0,"rank":11,"service":"paymentservice","severity_z":201.735},{"evidence_source":"metric","onset_rel_s":2220.0,"rank":12,"service":"node-4","severity_z":137.42},{"evidence_source":"metric","onset_rel_s":2340.0,"rank":13,"service":"adservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":2340.0,"rank":14,"service":"cartservice","severity_z":205.6}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"cartservice","caller":"checkoutservice"},{"callee":"emailservice","caller":"checkoutservice"},{"callee":"paymentservice","caller":"checkoutservice"},{"callee":"shippingservice","caller":"checkoutservice"},{"callee":"paymentservice2","caller":"checkoutservice2"},{"callee":"shippingservice2","caller":"checkoutservice2"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"medium","reason":"Rank recommendationservice-0 first because recommendationservice-0 has metric evidence at propagation rank 7; shippingservice-0 is second despite propagation rank 1 because onset ordering alone does not establish the causal origin. The remaining entries preserve evidence-supported alternatives so the ranking retains calibrated uncertainty instead of collapsing to one answer.","services":["recommendationservice-0","recommendationservice-2","recommendationservice-1","node-1","shippingservice-0"]}
