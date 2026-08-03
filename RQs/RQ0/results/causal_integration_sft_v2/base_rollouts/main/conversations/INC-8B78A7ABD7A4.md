# Causal SFT v2 base rollout — INC-8B78A7ABD7A4

## System

You are an expert Site Reliability Engineer performing Root Cause Analysis (RCA) for a microservice application deployed on a Kubernetes cluster. A fault has occurred in the system. Your task is to identify the root cause of the incident.

Root causes can occur at three levels:
- Pod level: a specific container replica (e.g., "cartservice-0")
- Service level: a microservice type (e.g., "paymentservice") — predict any pod of that service
- Node level: an infrastructure host (e.g., "node-6") — nodes appear as isolated entities with system metrics (CPU, memory, network, disk) but no application logs or traces

The system consists of multiple services communicating over HTTP/gRPC, running on shared infrastructure nodes. A fault in one component (pod, service, or node) can propagate to dependent components, causing them to appear degraded even though they are not the root cause.

Node-level faults (e.g., host memory exhaustion, CPU saturation, disk I/O) often manifest as correlated anomalies across multiple pods. If several unrelated pods show simultaneous degradation and a node shows critical system-level metrics, the node is likely the root cause.

Focus on distinguishing the ORIGIN of the fault from its SYMPTOMS in downstream or co-located components.

## User

[image: RQs/RQ0/results/causal_integration_sft_v1/data/cases/INC-8B78A7ABD7A4/dashboard.png]

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
opaque_id: INC-8B78A7ABD7A4
observation_window={"duration_rel_s":2340.0,"source_metric_rows":40}
selection_summary={"candidate_count":63,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":1561,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","adservice-grpc","adservice-http","adservice2","adservice2-0","cartservice-0","cartservice-1","cartservice-2","cartservice-grpc","cartservice2-0","checkoutservice-0","checkoutservice-1","checkoutservice-2","checkoutservice-grpc","checkoutservice2-0","currencyservice-0","currencyservice-1","currencyservice-2","currencyservice-grpc","currencyservice2-0","emailservice-0","emailservice-1","emailservice-2","emailservice-grpc","emailservice2-0","frontend-0","frontend-1","frontend-2","frontend-http","frontend2-0","istio-egressgateway-7bfdcc9d86-zpjpg","istio-ingressgateway-565bffd4d-6bl7m","node-1","node-2","node-3","node-4","node-5","node-6","paymentservice-0","paymentservice-1","paymentservice-2","paymentservice-grpc","paymentservice2-0","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","productcatalogservice-grpc","productcatalogservice2-0","recommendationservice-0","recommendationservice-1","recommendationservice-2","recommendationservice-grpc","recommendationservice2-0","redis-cart-0","redis-cart2-0","shippingservice-0","shippingservice-1","shippingservice-2","shippingservice-grpc","shippingservice2-0"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[18.281,54.844,91.406,127.969,164.531,201.094,237.656,274.219,310.781,347.344,383.906,420.469,457.031,493.594,530.156,566.719,603.281,639.844,676.406,712.969,749.531,786.094,822.656,859.219,895.781,932.344,968.906,1005.469,1042.031,1078.594,1115.156,1151.719,1188.281,1224.844,1261.406,1297.969,1334.531,1371.094,1407.656,1444.219,1480.781,1517.344,1553.906,1590.469,1627.031,1663.594,1700.156,1736.719,1773.281,1809.844,1846.406,1882.969,1919.531,1956.094,1992.656,2029.219,2065.781,2102.344,2138.906,2175.469,2212.031,2248.594,2285.156,2321.719]
[M1] rank=1 service=cartservice-0 metric=container_fs_writes./dev/vda baseline=0.0 peak=16.5 signed_z=999.0 onset_bin=54 onset_rel_s=1992.656 persistence_bins=4
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,16.5,0,-15,0,-1.5,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M2] rank=2 service=cartservice-0 metric=container_fs_writes_MB./dev/vda baseline=0.0 peak=0.115234 signed_z=999.0 onset_bin=54 onset_rel_s=1992.656 persistence_bins=4
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.115234,0,-0.101562,0,-0.013672,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M3] rank=3 service=checkoutservice-1 metric=istio_request_bytes.grpc.0.2.0 baseline=0.0 peak=785.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,392.5,0,-392.5,785,-392.5,-392.5,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M4] rank=4 service=checkoutservice-1 metric=istio_request_duration_milliseconds.grpc.0.2.0 baseline=0.0 peak=59500.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,29750,0,-29750,59500,-29750,-29750,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M5] rank=5 service=checkoutservice-1 metric=istio_requests.grpc.0.2.0 baseline=0.0 peak=1.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.5,0,-0.5,1,-0.5,-0.5,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M6] rank=6 service=checkoutservice-2 metric=istio_request_bytes.grpc.0.2.0 baseline=0.0 peak=785.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,785,0,-785,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M7] rank=7 service=checkoutservice-2 metric=istio_request_duration_milliseconds.grpc.0.2.0 baseline=0.0 peak=59500.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,59500,0,-59500,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M8] rank=8 service=checkoutservice-2 metric=istio_requests.grpc.0.2.0 baseline=0.0 peak=1.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,-1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M9] rank=9 service=checkoutservice2-0 metric=istio_request_bytes.grpc.0.2.0 baseline=0.0 peak=4770.0 signed_z=999.0 onset_bin=36 onset_rel_s=1334.531 persistence_bins=3
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,397.5,2385,1987.5,-1987.5,-795,-1987.5,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M10] rank=10 service=checkoutservice2-0 metric=istio_request_duration_milliseconds.grpc.0.2.0 baseline=0.0 peak=357000.0 signed_z=999.0 onset_bin=36 onset_rel_s=1334.531 persistence_bins=3
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,30250,148250,178500,-148750,-59500,-148750,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M11] rank=11 service=checkoutservice2-0 metric=istio_requests.grpc.0.2.0 baseline=0.0 peak=6.0 signed_z=999.0 onset_bin=36 onset_rel_s=1334.531 persistence_bins=3
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.5,3,2.5,-3,-0.5,-2.5,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M12] rank=12 service=emailservice-0 metric=container_cpu_usage_seconds baseline=0.027201 peak=19.199911 signed_z=999.0 onset_bin=36 onset_rel_s=1334.531 persistence_bins=4
values_compact=delta:0.026504,-0.000962,0.005189,-0.007361,0,0.00733,-0.008783,0.010943,-0.004883,0.000086,0.000062,-0.002911,-0.00201,0.003834,0.002059,-0.003268,0.007121,-0.005867,0.001011,-0.001744,7.532973,7.312236,4.328352,-14.937992,-0.411197,-3.819082,0.003019,-0.007193,0.008952,-0.006667,0.001114,-0.003978,0.006381,-0.008375,0.006801,-0.001485,-0.00568,0.004815,0.00262,-0.001675
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[1920.0,2100.0]

=== LOG SUMMARY ===
{"entries":[{"error_logs":24,"error_pct":6.65,"service":"emailservice-1","total_logs":361},{"error_logs":23,"error_pct":6.02,"service":"emailservice-0","total_logs":382},{"error_logs":14,"error_pct":5.11,"service":"emailservice-2","total_logs":274},{"error_logs":6,"error_pct":0.01,"service":"frontend-1","total_logs":47662},{"error_logs":5,"error_pct":0.39,"service":"checkoutservice-1","total_logs":1296},{"error_logs":2,"error_pct":0.15,"service":"checkoutservice-2","total_logs":1313},{"error_logs":1,"error_pct":0.08,"service":"checkoutservice-0","total_logs":1305},{"error_logs":1,"error_pct":0.0,"service":"frontend-2","total_logs":25513}],"mode":"errors","omitted_services":23,"service_count":31}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":230.5,"error_pct":0.0,"p95_during_ms":0.6081999999999996,"p95_pre_ms":0.184,"service":"paymentservice-2","spans":78},{"delta_pct":37.6,"error_pct":0.0,"p95_during_ms":0.12929999999999992,"p95_pre_ms":0.094,"service":"shippingservice-1","spans":553},{"delta_pct":16.5,"error_pct":0.0,"p95_during_ms":0.09199999999999998,"p95_pre_ms":0.079,"service":"shippingservice-2","spans":553},{"delta_pct":-13.4,"error_pct":0.0,"p95_during_ms":42.51895,"p95_pre_ms":49.06979999999999,"service":"checkoutservice-0","spans":912},{"delta_pct":-12.0,"error_pct":0.0,"p95_during_ms":0.26975000000000005,"p95_pre_ms":0.3065,"service":"emailservice2-0","spans":217},{"delta_pct":-11.9,"error_pct":0.0,"p95_during_ms":0.15375,"p95_pre_ms":0.17459999999999995,"service":"paymentservice-1","spans":79},{"delta_pct":11.8,"error_pct":0.0,"p95_during_ms":0.031299999999999994,"p95_pre_ms":0.028,"service":"adservice-0","spans":1223},{"delta_pct":-11.7,"error_pct":0.0,"p95_during_ms":43.32465,"p95_pre_ms":49.06674999999994,"service":"checkoutservice-1","spans":916}],"omitted_services":32,"service_count":40}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=15 omitted_edges=1
[{"evidence_source":"metric","onset_rel_s":1200.0,"rank":1,"service":"checkoutservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1260.0,"rank":2,"service":"checkoutservice2","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1260.0,"rank":3,"service":"emailservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1260.0,"rank":4,"service":"frontend2","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1380.0,"rank":5,"service":"frontend","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1500.0,"rank":6,"service":"emailservice2","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1620.0,"rank":7,"service":"shippingservice","severity_z":123.305},{"evidence_source":"metric","onset_rel_s":1980.0,"rank":8,"service":"cartservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1980.0,"rank":9,"service":"adservice","severity_z":794.588},{"evidence_source":"metric","onset_rel_s":1980.0,"rank":10,"service":"node-3","severity_z":77.902},{"evidence_source":"metric","onset_rel_s":2040.0,"rank":11,"service":"paymentservice","severity_z":166.042},{"evidence_source":"metric","onset_rel_s":2040.0,"rank":12,"service":"recommendationservice","severity_z":88.596},{"evidence_source":"metric","onset_rel_s":2040.0,"rank":13,"service":"node-1","severity_z":50.454},{"evidence_source":"metric","onset_rel_s":2340.0,"rank":14,"service":"adservice2","severity_z":209.692}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"cartservice","caller":"checkoutservice"},{"callee":"emailservice","caller":"checkoutservice"},{"callee":"paymentservice","caller":"checkoutservice"},{"callee":"shippingservice","caller":"checkoutservice"},{"callee":"emailservice2","caller":"checkoutservice2"},{"callee":"adservice","caller":"frontend"},{"callee":"cartservice","caller":"frontend"},{"callee":"checkoutservice","caller":"frontend"},{"callee":"recommendationservice","caller":"frontend"},{"callee":"shippingservice","caller":"frontend"},{"callee":"adservice2","caller":"frontend2"},{"callee":"checkoutservice2","caller":"frontend2"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

## Assistant

{
"services": [
"checkoutservice",
"checkoutservice2",
"emailservice",
"frontend2",
"frontend"
],
"reason": "The root cause is the checkoutservice (and checkoutservice2) because they exhibit the earliest anomaly onset (rank 1 and 2) with massive latency spikes (up to 357s) and request volume anomalies, which propagate downstream to emailservice and frontend services as indicated by the call topology and later onset times.",
"confidence": "high"
}
