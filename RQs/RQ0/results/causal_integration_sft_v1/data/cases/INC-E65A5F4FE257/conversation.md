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
opaque_id: INC-E65A5F4FE257
observation_window={"duration_rel_s":2340.0,"source_metric_rows":40}
selection_summary={"candidate_count":63,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":1626,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","adservice-grpc","adservice-http","adservice2","adservice2-0","cartservice-0","cartservice-1","cartservice-2","cartservice-grpc","cartservice2-0","checkoutservice-0","checkoutservice-1","checkoutservice-2","checkoutservice-grpc","checkoutservice2-0","currencyservice-0","currencyservice-1","currencyservice-2","currencyservice-grpc","currencyservice2-0","emailservice-0","emailservice-1","emailservice-2","emailservice-grpc","emailservice2-0","frontend-0","frontend-1","frontend-2","frontend-http","frontend2-0","istio-egressgateway-7bfdcc9d86-g2d4q","istio-ingressgateway-565bffd4d-rn678","node-1","node-2","node-3","node-4","node-5","node-6","paymentservice-0","paymentservice-1","paymentservice-2","paymentservice-grpc","paymentservice2-0","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","productcatalogservice-grpc","productcatalogservice2-0","recommendationservice-0","recommendationservice-1","recommendationservice-2","recommendationservice-grpc","recommendationservice2-0","redis-cart-0","redis-cart2-0","shippingservice-0","shippingservice-1","shippingservice-2","shippingservice-grpc","shippingservice2-0"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[18.281,54.844,91.406,127.969,164.531,201.094,237.656,274.219,310.781,347.344,383.906,420.469,457.031,493.594,530.156,566.719,603.281,639.844,676.406,712.969,749.531,786.094,822.656,859.219,895.781,932.344,968.906,1005.469,1042.031,1078.594,1115.156,1151.719,1188.281,1224.844,1261.406,1297.969,1334.531,1371.094,1407.656,1444.219,1480.781,1517.344,1553.906,1590.469,1627.031,1663.594,1700.156,1736.719,1773.281,1809.844,1846.406,1882.969,1919.531,1956.094,1992.656,2029.219,2065.781,2102.344,2138.906,2175.469,2212.031,2248.594,2285.156,2321.719]
[M1] rank=1 service=adservice2 metric=java_lang_Memory_ObjectPendingFinalizationCount baseline=0.0 peak=0.333333 signed_z=999.0 onset_bin=36 onset_rel_s=1334.531 persistence_bins=2
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.166667,0.166666,-0.333333,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M2] rank=2 service=adservice metric=java_lang_Memory_ObjectPendingFinalizationCount baseline=0.0 peak=0.25 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.25,-0.25,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M3] rank=3 service=istio-egressgateway-7bfdcc9d86-g2d4q metric=istio_agent_outgoing_latency.csr baseline=303.776487 peak=309.868966 signed_z=999.0 onset_bin=36 onset_rel_s=1334.531 persistence_bins=18
values_compact=delta:303.776487,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,3.04624,3.046239,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M4] rank=4 service=istio-egressgateway-7bfdcc9d86-g2d4q metric=istio_agent_pilot_proxy_convergence_time baseline=0.0 peak=0.112095 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.112095,0,-0.112095,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M5] rank=5 service=istio-egressgateway-7bfdcc9d86-g2d4q metric=istio_agent_pilot_proxy_queue_time baseline=0.0 peak=1.6e-05 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.000016,0,-0.000016,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M6] rank=6 service=istio-egressgateway-7bfdcc9d86-g2d4q metric=istio_agent_pilot_xds_push_time.sds baseline=0.0 peak=0.112074 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.112074,0,-0.112074,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M7] rank=7 service=istio-egressgateway-7bfdcc9d86-g2d4q metric=istio_agent_pilot_xds_send_time baseline=0.0 peak=1.7e-05 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.000017,0,-0.000017,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M8] rank=8 service=istio-ingressgateway-565bffd4d-rn678 metric=istio_agent_outgoing_latency.csr baseline=315.740828 peak=319.852868 signed_z=999.0 onset_bin=36 onset_rel_s=1334.531 persistence_bins=18
values_compact=delta:315.740828,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,2.05602,2.05602,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M9] rank=9 service=istio-ingressgateway-565bffd4d-rn678 metric=istio_agent_pilot_proxy_convergence_time baseline=0.0 peak=0.142987 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.142987,0,-0.142987,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M10] rank=10 service=istio-ingressgateway-565bffd4d-rn678 metric=istio_agent_pilot_proxy_queue_time baseline=0.0 peak=1.8e-05 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.000018,0,-0.000018,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M11] rank=11 service=istio-ingressgateway-565bffd4d-rn678 metric=istio_agent_pilot_xds_push_time.sds baseline=0.0 peak=0.142959 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.142959,0,-0.142959,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M12] rank=12 service=istio-ingressgateway-565bffd4d-rn678 metric=istio_agent_pilot_xds_send_time baseline=0.0 peak=1.1e-05 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.000011,0,-0.000011,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[1200.0,2340.0]

=== LOG SUMMARY ===
{"entries":[{"error_logs":1680,"error_pct":8.86,"service":"adservice-0","total_logs":18964},{"error_logs":314,"error_pct":1.29,"service":"frontend-0","total_logs":24358},{"error_logs":310,"error_pct":1.28,"service":"frontend-2","total_logs":24180},{"error_logs":216,"error_pct":1.27,"service":"frontend-1","total_logs":17070}],"mode":"errors","omitted_services":27,"service_count":31}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":-23.9,"error_pct":0.0,"p95_during_ms":0.074,"p95_pre_ms":0.09730000000000001,"service":"adservice2-0","spans":617},{"delta_pct":-21.1,"error_pct":0.0,"p95_during_ms":0.015,"p95_pre_ms":0.019,"service":"adservice-2","spans":840},{"delta_pct":-17.2,"error_pct":0.0,"p95_during_ms":0.015449999999999988,"p95_pre_ms":0.018649999999999976,"service":"adservice-1","spans":840},{"delta_pct":13.2,"error_pct":0.0,"p95_during_ms":6.44375,"p95_pre_ms":5.6937999999999995,"service":"currencyservice2-0","spans":3149},{"delta_pct":7.0,"error_pct":0.0,"p95_during_ms":0.23305,"p95_pre_ms":0.21785,"service":"emailservice2-0","spans":42},{"delta_pct":6.8,"error_pct":0.0,"p95_during_ms":0.1855,"p95_pre_ms":0.1737,"service":"paymentservice2-0","spans":42},{"delta_pct":5.9,"error_pct":0.0,"p95_during_ms":0.2379,"p95_pre_ms":0.22465000000000002,"service":"emailservice-0","spans":55},{"delta_pct":-5.7,"error_pct":0.0,"p95_during_ms":0.1288,"p95_pre_ms":0.13665000000000002,"service":"paymentservice-1","spans":53}],"omitted_services":32,"service_count":40}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=15 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":1200.0,"rank":1,"service":"shippingservice","severity_z":115.137},{"evidence_source":"metric","onset_rel_s":1200.0,"rank":2,"service":"frontend2","severity_z":50.388},{"evidence_source":"metric","onset_rel_s":1200.0,"rank":3,"service":"cartservice","severity_z":28.63},{"evidence_source":"metric","onset_rel_s":1260.0,"rank":4,"service":"istio-egressgateway","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1260.0,"rank":5,"service":"istio-ingressgateway","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1260.0,"rank":6,"service":"recommendationservice2","severity_z":158.306},{"evidence_source":"metric","onset_rel_s":1320.0,"rank":7,"service":"adservice2","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1380.0,"rank":8,"service":"currencyservice","severity_z":90.425},{"evidence_source":"metric","onset_rel_s":1440.0,"rank":9,"service":"node-2","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1680.0,"rank":10,"service":"node-1","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1680.0,"rank":11,"service":"paymentservice","severity_z":145.119},{"evidence_source":"metric","onset_rel_s":1800.0,"rank":12,"service":"recommendationservice","severity_z":26.427},{"evidence_source":"metric","onset_rel_s":1980.0,"rank":13,"service":"node-6","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":2100.0,"rank":14,"service":"adservice","severity_z":999.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"adservice2","caller":"frontend2"},{"callee":"recommendationservice2","caller":"frontend2"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"medium","reason":"Rank node-6 first because node-6 has metric evidence at propagation rank 13; shippingservice-0 is second despite propagation rank 1 because onset ordering alone does not establish the causal origin.","services":["node-6","shippingservice-0"]}
