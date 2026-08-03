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
opaque_id: INC-4ADE81F9C874
observation_window={"duration_rel_s":2340.0,"source_metric_rows":40}
selection_summary={"candidate_count":63,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":1542,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","adservice-grpc","adservice-http","adservice2","adservice2-0","cartservice-0","cartservice-1","cartservice-2","cartservice-grpc","cartservice2-0","checkoutservice-0","checkoutservice-1","checkoutservice-2","checkoutservice-grpc","checkoutservice2-0","currencyservice-0","currencyservice-1","currencyservice-2","currencyservice-grpc","currencyservice2-0","emailservice-0","emailservice-1","emailservice-2","emailservice-grpc","emailservice2-0","frontend-0","frontend-1","frontend-2","frontend-http","frontend2-0","istio-egressgateway-7bfdcc9d86-g2d4q","istio-ingressgateway-565bffd4d-rn678","node-1","node-2","node-3","node-4","node-5","node-6","paymentservice-0","paymentservice-1","paymentservice-2","paymentservice-grpc","paymentservice2-0","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","productcatalogservice-grpc","productcatalogservice2-0","recommendationservice-0","recommendationservice-1","recommendationservice-2","recommendationservice-grpc","recommendationservice2-0","redis-cart-0","redis-cart2-0","shippingservice-0","shippingservice-1","shippingservice-2","shippingservice-grpc","shippingservice2-0"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[18.281,54.844,91.406,127.969,164.531,201.094,237.656,274.219,310.781,347.344,383.906,420.469,457.031,493.594,530.156,566.719,603.281,639.844,676.406,712.969,749.531,786.094,822.656,859.219,895.781,932.344,968.906,1005.469,1042.031,1078.594,1115.156,1151.719,1188.281,1224.844,1261.406,1297.969,1334.531,1371.094,1407.656,1444.219,1480.781,1517.344,1553.906,1590.469,1627.031,1663.594,1700.156,1736.719,1773.281,1809.844,1846.406,1882.969,1919.531,1956.094,1992.656,2029.219,2065.781,2102.344,2138.906,2175.469,2212.031,2248.594,2285.156,2321.719]
[M1] rank=1 service=checkoutservice-0 metric=container_fs_inodes./dev/vda1 baseline=0.0 peak=20.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,20,-20,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M2] rank=2 service=checkoutservice-0 metric=container_fs_usage_MB./dev/vda1 baseline=9.196289 peak=632.226562 signed_z=999.0 onset_bin=44 onset_rel_s=1627.031 persistence_bins=13
values_compact=delta:9.167969,0.003906,0.003906,0.003907,0,0.003906,0.003906,0.003906,0,0.003906,0,0.003907,0.003906,0.003906,0,0.003907,0.003906,0.003906,0.003906,0,0.003906,0.003907,0,0.003906,0,0.003906,0,0.007813,0,0.003906,0,0.003906,0.003906,622.964844,0,0.003906,-600.582031,0.003907,0.003906,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M3] rank=3 service=checkoutservice-0 metric=container_fs_writes./dev/vda baseline=0.0 peak=32.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,32,-32,0,3,-3,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M4] rank=4 service=checkoutservice-0 metric=container_fs_writes_MB./dev/vda baseline=0.0 peak=0.226562 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.226562,-0.226562,0,0.027344,-0.027344,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M5] rank=5 service=checkoutservice-1 metric=container_fs_inodes./dev/vda1 baseline=0.0 peak=10.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,10,0,-10,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M6] rank=6 service=checkoutservice-1 metric=container_fs_usage_MB./dev/vda1 baseline=9.197363 peak=632.224609 signed_z=999.0 onset_bin=44 onset_rel_s=1627.031 persistence_bins=13
values_compact=delta:9.167969,0.005859,0.001953,0.003907,0.001953,0.003906,0.003906,0.001953,0.001953,0.001953,0.003907,0.003906,0.001953,0.001953,0.003907,0,0.003906,0.003906,0.001953,0.001953,0.00586,0.001953,0.001953,0.001953,0,0.005859,0.003907,0.001953,0.001953,0.001953,0.001953,0.001953,311.486328,311.484375,-300.291015,-300.291016,0.003906,0.003907,0.001953,0.001953
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M7] rank=7 service=checkoutservice-1 metric=container_fs_writes./dev/vda baseline=0.0 peak=33.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,33,-33,3,-3,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M8] rank=8 service=checkoutservice-1 metric=container_fs_writes_MB./dev/vda baseline=0.0 peak=0.226562 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.226562,-0.226562,0.027344,-0.027344,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M9] rank=9 service=checkoutservice-2 metric=container_fs_inodes./dev/vda1 baseline=0.0 peak=20.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,20,-20,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M10] rank=10 service=checkoutservice-2 metric=container_fs_usage_MB./dev/vda1 baseline=9.19668 peak=632.222656 signed_z=999.0 onset_bin=44 onset_rel_s=1627.031 persistence_bins=13
values_compact=delta:9.169922,0.001953,0.001953,0.003906,0.003907,0.003906,0.001953,0.001953,0.001953,0.003906,0.003907,0.001953,0.003906,0.001953,0.003907,0,0.003906,0.003906,0,0.003906,0.003906,0.003907,0.001953,0.001953,0,0.005859,0.001954,0.003906,0.001953,0.001953,0.001953,0.003906,0.001953,622.964844,-300.292968,-300.292969,0.003906,0.005859,0.001954,0.001953
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M11] rank=11 service=checkoutservice-2 metric=container_fs_writes./dev/vda baseline=0.0 peak=36.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,36,-36,4,-4,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M12] rank=12 service=checkoutservice-2 metric=container_fs_writes_MB./dev/vda baseline=0.0 peak=0.21875 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.21875,-0.21875,0.027344,-0.027344,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[1920.0,2160.0]

=== LOG SUMMARY ===
{"entries":[{"error_logs":5008,"error_pct":9.01,"service":"adservice-0","total_logs":55568},{"error_logs":906,"error_pct":1.3,"service":"frontend-0","total_logs":69860},{"error_logs":902,"error_pct":1.3,"service":"frontend-2","total_logs":69548},{"error_logs":696,"error_pct":1.29,"service":"frontend-1","total_logs":53920}],"mode":"errors","omitted_services":27,"service_count":31}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":158.1,"error_pct":0.0,"p95_during_ms":94.92019999999998,"p95_pre_ms":36.7831,"service":"checkoutservice-0","spans":1974},{"delta_pct":156.4,"error_pct":0.0,"p95_during_ms":93.6031499999999,"p95_pre_ms":36.5065,"service":"checkoutservice-2","spans":1992},{"delta_pct":148.5,"error_pct":0.0,"p95_during_ms":91.5482,"p95_pre_ms":36.8382,"service":"checkoutservice-1","spans":1992},{"delta_pct":104.2,"error_pct":0.0,"p95_during_ms":127.19634999999981,"p95_pre_ms":62.293,"service":"checkoutservice2-0","spans":1158},{"delta_pct":-99.5,"error_pct":0.0,"p95_during_ms":2.6618,"p95_pre_ms":584.38405,"service":"recommendationservice-0","spans":6024},{"delta_pct":-99.5,"error_pct":0.0,"p95_during_ms":2.689699999999998,"p95_pre_ms":584.39405,"service":"recommendationservice-1","spans":6022},{"delta_pct":-99.5,"error_pct":0.0,"p95_during_ms":2.64785,"p95_pre_ms":584.38305,"service":"recommendationservice-2","spans":6022},{"delta_pct":-99.5,"error_pct":0.0,"p95_during_ms":3.2052500000000004,"p95_pre_ms":584.82095,"service":"recommendationservice2-0","spans":3598}],"omitted_services":32,"service_count":40}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=15 omitted_edges=1
[{"evidence_source":"metric","onset_rel_s":1200.0,"rank":1,"service":"paymentservice2","severity_z":20.814},{"evidence_source":"metric","onset_rel_s":1260.0,"rank":2,"service":"node-6","severity_z":311.373},{"evidence_source":"metric","onset_rel_s":1260.0,"rank":3,"service":"recommendationservice","severity_z":57.452},{"evidence_source":"metric","onset_rel_s":1320.0,"rank":4,"service":"redis-cart2","severity_z":111.516},{"evidence_source":"metric","onset_rel_s":1800.0,"rank":5,"service":"cartservice","severity_z":79.305},{"evidence_source":"metric","onset_rel_s":1860.0,"rank":6,"service":"node-1","severity_z":64.715},{"evidence_source":"metric","onset_rel_s":1860.0,"rank":7,"service":"node-3","severity_z":31.245},{"evidence_source":"metric","onset_rel_s":1860.0,"rank":8,"service":"istio-egressgateway","severity_z":30.59},{"evidence_source":"metric","onset_rel_s":1920.0,"rank":9,"service":"node-5","severity_z":792.269},{"evidence_source":"metric","onset_rel_s":1920.0,"rank":10,"service":"adservice","severity_z":76.59},{"evidence_source":"metric","onset_rel_s":1920.0,"rank":11,"service":"frontend","severity_z":20.432},{"evidence_source":"trace","onset_rel_s":1925.4,"rank":12,"service":"checkoutservice","severity_z":23.581},{"evidence_source":"trace","onset_rel_s":1925.4,"rank":13,"service":"checkoutservice2","severity_z":8.872},{"evidence_source":"metric","onset_rel_s":2040.0,"rank":14,"service":"frontend2","severity_z":89.477}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"cartservice","caller":"checkoutservice"},{"callee":"paymentservice2","caller":"checkoutservice2"},{"callee":"adservice","caller":"frontend"},{"callee":"cartservice","caller":"frontend"},{"callee":"checkoutservice","caller":"frontend"},{"callee":"recommendationservice","caller":"frontend"},{"callee":"checkoutservice2","caller":"frontend2"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"high","reason":"Rank recommendationservice-0 first because recommendationservice-0 has direct trace evidence; although frontend-0 is salient, the caller path frontend -> recommendationservice means a disturbance in the callee can propagate back toward that caller-side symptom. The remaining entries preserve evidence-supported alternatives so the ranking retains calibrated uncertainty instead of collapsing to one answer.","services":["recommendationservice-0","node-6","paymentservice2-0","redis-cart2-0","cartservice-0"]}
