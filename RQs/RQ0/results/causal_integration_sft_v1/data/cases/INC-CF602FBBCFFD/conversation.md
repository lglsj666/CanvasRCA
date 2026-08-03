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
opaque_id: INC-CF602FBBCFFD
observation_window={"duration_rel_s":2340.0,"source_metric_rows":40}
selection_summary={"candidate_count":63,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":1465,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","adservice-grpc","adservice-http","adservice2","adservice2-0","cartservice-0","cartservice-1","cartservice-2","cartservice-grpc","cartservice2-0","checkoutservice-0","checkoutservice-1","checkoutservice-2","checkoutservice-grpc","checkoutservice2-0","currencyservice-0","currencyservice-1","currencyservice-2","currencyservice-grpc","currencyservice2-0","emailservice-0","emailservice-1","emailservice-2","emailservice-grpc","emailservice2-0","frontend-0","frontend-1","frontend-2","frontend-http","frontend2-0","istio-egressgateway-7bfdcc9d86-22q7z","istio-ingressgateway-565bffd4d-4nr6v","node-1","node-2","node-3","node-4","node-5","node-6","paymentservice-0","paymentservice-1","paymentservice-2","paymentservice-grpc","paymentservice2-0","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","productcatalogservice-grpc","productcatalogservice2-0","recommendationservice-0","recommendationservice-1","recommendationservice-2","recommendationservice-grpc","recommendationservice2-0","redis-cart-0","redis-cart2-0","shippingservice-0","shippingservice-1","shippingservice-2","shippingservice-grpc","shippingservice2-0"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[18.281,54.844,91.406,127.969,164.531,201.094,237.656,274.219,310.781,347.344,383.906,420.469,457.031,493.594,530.156,566.719,603.281,639.844,676.406,712.969,749.531,786.094,822.656,859.219,895.781,932.344,968.906,1005.469,1042.031,1078.594,1115.156,1151.719,1188.281,1224.844,1261.406,1297.969,1334.531,1371.094,1407.656,1444.219,1480.781,1517.344,1553.906,1590.469,1627.031,1663.594,1700.156,1736.719,1773.281,1809.844,1846.406,1882.969,1919.531,1956.094,1992.656,2029.219,2065.781,2102.344,2138.906,2175.469,2212.031,2248.594,2285.156,2321.719]
[M1] rank=1 service=emailservice2-0 metric=container_memory_mapped_file baseline=0.0 peak=12288.0 signed_z=999.0 onset_bin=54 onset_rel_s=1992.656 persistence_bins=7
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,12288,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M2] rank=2 service=frontend-0 metric=container_cpu_cfs_throttled_seconds baseline=0.0 peak=0.003983 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.003983,-0.003983,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M3] rank=3 service=istio-ingressgateway-565bffd4d-4nr6v metric=istio_agent_go_gc_duration_seconds.1.0 baseline=0.000117 peak=0.000117 signed_z=-999.0 onset_bin=0 onset_rel_s=18.281 persistence_bins=40
values_compact=delta:0.000117,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M4] rank=4 service=paymentservice-0 metric=container_network_receive_MB.eth0 baseline=0.022389 peak=0.538944 signed_z=145.006 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.024764,-0.005658,0.004994,-0.003107,0.001902,0.004522,-0.007136,-0.002133,0.008126,-0.001712,-0.009012,0.011504,0.001321,-0.009065,0.001342,-0.001366,-0.001361,0.003122,0.002838,0.002278,0.00057,0.512211,-0.512854,-0.00452,-0.000755,0.003727,-0.003777,-0.002124,0.003274,0.003688,0.000855,-0.004555,0.001457,-0.005958,-0.001118,0.006511,-0.002401,0.006467,-0.006361,0.003005
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M5] rank=5 service=emailservice-1 metric=container_network_receive_MB.eth0 baseline=0.025401 peak=0.549872 signed_z=129.587 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.023953,-0.000414,0.008101,-0.004939,-0.012179,0.017423,-0.006803,-0.003003,0.004167,0.001426,0.000251,-0.003721,-0.00091,-0.001937,0.006026,-0.001333,-0.002613,0.008121,-0.003631,-0.007236,0.001553,0.00105,0.002756,0.003701,-0.003248,-0.009973,0.008073,0.525211,-0.524106,0.000833,-0.000334,-0.002394,0.002721,0.004409,-0.000258,-0.000564,0.00836,-0.003625,-0.017751,0.025001
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M6] rank=6 service=checkoutservice-1 metric=container_memory_mapped_file baseline=233472.0 peak=237568.0 signed_z=107.395 onset_bin=41 onset_rel_s=1517.344 persistence_bins=15
values_compact=delta:233472,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,4096,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M7] rank=7 service=node-2 metric=system.udp.connect.num baseline=10.0 peak=11.0 signed_z=90.909 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:10,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,-1,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M8] rank=8 service=checkoutservice-0 metric=container_network_receive_MB.eth0 baseline=0.052099 peak=0.584159 signed_z=71.443 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.056067,-0.01599,-0.004701,0.021391,-0.004905,-0.005578,0.019798,-0.009733,-0.015679,0.018019,-0.009271,0.002742,0.001528,0.007253,-0.01409,0.009931,0.002075,-0.001948,-0.008714,0.001762,0.014032,-0.012783,-0.008912,0.02181,0.005502,-0.029905,0.016311,-0.022096,0.550243,-0.530099,0.000999,-0.014252,0.017164,-0.001758,-0.002301,0.010718,-0.013961,-0.016334,0.021162,-0.00124
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M9] rank=9 service=cartservice2-0 metric=container_network_receive_MB.eth0 baseline=0.07184 peak=0.592762 signed_z=70.194 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.0601,0.017024,-0.00911,0.009058,0.000927,-0.008279,0.00435,-0.00278,0.005768,-0.012283,0.014239,-0.009999,-0.006364,0.012254,-0.01011,0.000455,0.028757,-0.022389,-0.005349,0.005793,0.008874,-0.005443,-0.013615,0.014623,0.516261,-0.529544,0.013118,-0.007099,0.005038,-0.004255,-0.009708,0.021003,-0.01053,0.00452,-0.010247,0.000379,-0.003034,0.012889,0.01128,-0.023031
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M10] rank=10 service=node-6 metric=system.io.avg_q_sz baseline=0.0 peak=0.01 signed_z=64.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.01,-0.01,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M11] rank=11 service=checkoutservice2-0 metric=container_memory_mapped_file baseline=401408.0 peak=405504.0 signed_z=62.918 onset_bin=44 onset_rel_s=1627.031 persistence_bins=13
values_compact=delta:401408,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,2730.666667,1365.333333,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M12] rank=12 service=node-4 metric=system.io.util baseline=0.025 peak=3.15 signed_z=55.902 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0.05,-0.05,0,0,0.2,-0.1,-0.1,0.15,-0.15,0,0,0,0,0,0,0,0,0,0,0,0.15,-0.15,0,0,0.15,-0.15,0,0.1,-0.1,0,0,0,0,0,0,0,0,3.15,-3.15
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[1860.0,2340.0]

=== LOG SUMMARY ===
{"entries":[{"change_pct":-86.5,"n_during":5,"n_pre":37,"service":"redis-cart-0"},{"change_pct":-77.0,"n_during":486,"n_pre":2116,"service":"checkoutservice-0"},{"change_pct":-77.0,"n_during":85,"n_pre":370,"service":"emailservice-2"},{"change_pct":-76.9,"n_during":84,"n_pre":363,"service":"emailservice-1"},{"change_pct":-76.4,"n_during":90,"n_pre":381,"service":"paymentservice-1"},{"change_pct":-76.2,"n_during":10187,"n_pre":42749,"service":"frontend-1"},{"change_pct":-76.1,"n_during":90,"n_pre":377,"service":"paymentservice-0"},{"change_pct":-75.9,"n_during":502,"n_pre":2082,"service":"checkoutservice-2"}],"mode":"volume","omitted_services":23,"service_count":31}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":22.9,"error_pct":0.0,"p95_during_ms":0.213,"p95_pre_ms":0.17325000000000002,"service":"paymentservice2-0","spans":147},{"delta_pct":9.7,"error_pct":0.0,"p95_during_ms":0.16665,"p95_pre_ms":0.15184999999999998,"service":"paymentservice-2","spans":154},{"delta_pct":-9.5,"error_pct":0.0,"p95_during_ms":0.019,"p95_pre_ms":0.021,"service":"adservice-1","spans":2314},{"delta_pct":6.0,"error_pct":0.0,"p95_during_ms":0.08159999999999991,"p95_pre_ms":0.077,"service":"shippingservice2-0","spans":1030},{"delta_pct":5.1,"error_pct":0.0,"p95_during_ms":0.124,"p95_pre_ms":0.118,"service":"currencyservice2-0","spans":11234},{"delta_pct":5.0,"error_pct":0.0,"p95_during_ms":0.15974999999999998,"p95_pre_ms":0.15219999999999997,"service":"paymentservice-0","spans":155},{"delta_pct":4.5,"error_pct":0.0,"p95_during_ms":0.023,"p95_pre_ms":0.022,"service":"adservice-2","spans":2314},{"delta_pct":4.1,"error_pct":0.0,"p95_during_ms":0.14964999999999998,"p95_pre_ms":0.14375,"service":"paymentservice-1","spans":156}],"omitted_services":32,"service_count":40}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=16 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":1200.0,"rank":1,"service":"frontend","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1260.0,"rank":2,"service":"paymentservice","severity_z":145.006},{"evidence_source":"metric","onset_rel_s":1260.0,"rank":3,"service":"node-5","severity_z":43.116},{"evidence_source":"metric","onset_rel_s":1380.0,"rank":4,"service":"checkoutservice","severity_z":107.395},{"evidence_source":"metric","onset_rel_s":1440.0,"rank":5,"service":"cartservice2","severity_z":70.194},{"evidence_source":"metric","onset_rel_s":1560.0,"rank":6,"service":"checkoutservice2","severity_z":62.918},{"evidence_source":"metric","onset_rel_s":1620.0,"rank":7,"service":"emailservice","severity_z":129.587},{"evidence_source":"metric","onset_rel_s":1620.0,"rank":8,"service":"cartservice","severity_z":40.786},{"evidence_source":"metric","onset_rel_s":1800.0,"rank":9,"service":"redis-cart2","severity_z":53.49},{"evidence_source":"metric","onset_rel_s":1920.0,"rank":10,"service":"emailservice2","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1920.0,"rank":11,"service":"node-6","severity_z":64.0},{"evidence_source":"metric","onset_rel_s":2160.0,"rank":12,"service":"istio-ingressgateway","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":2160.0,"rank":13,"service":"node-2","severity_z":90.909},{"evidence_source":"metric","onset_rel_s":2280.0,"rank":14,"service":"node-4","severity_z":55.902}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"cartservice","caller":"checkoutservice"},{"callee":"emailservice","caller":"checkoutservice"},{"callee":"paymentservice","caller":"checkoutservice"},{"callee":"cartservice2","caller":"checkoutservice2"},{"callee":"emailservice2","caller":"checkoutservice2"},{"callee":"cartservice","caller":"frontend"},{"callee":"checkoutservice","caller":"frontend"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"medium","reason":"Rank node-5 first because node-5 has metric evidence at propagation rank 3; frontend-0 is second despite propagation rank 1 because onset ordering alone does not establish the causal origin.","services":["node-5","frontend-0"]}
