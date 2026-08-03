# Causal SFT v2 base rollout — INC-A04B2F05C57A

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

[image: RQs/RQ0/results/causal_integration_sft_v1/data/cases/INC-A04B2F05C57A/dashboard.png]

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
opaque_id: INC-A04B2F05C57A
observation_window={"duration_rel_s":2340.0,"source_metric_rows":40}
selection_summary={"candidate_count":63,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":1368,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","adservice-grpc","adservice-http","adservice2","adservice2-0","cartservice-0","cartservice-1","cartservice-2","cartservice-grpc","cartservice2-0","checkoutservice-0","checkoutservice-1","checkoutservice-2","checkoutservice-grpc","checkoutservice2-0","currencyservice-0","currencyservice-1","currencyservice-2","currencyservice-grpc","currencyservice2-0","emailservice-0","emailservice-1","emailservice-2","emailservice-grpc","emailservice2-0","frontend-0","frontend-1","frontend-2","frontend-http","frontend2-0","istio-egressgateway-7bfdcc9d86-22q7z","istio-ingressgateway-565bffd4d-4nr6v","node-1","node-2","node-3","node-4","node-5","node-6","paymentservice-0","paymentservice-1","paymentservice-2","paymentservice-grpc","paymentservice2-0","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","productcatalogservice-grpc","productcatalogservice2-0","recommendationservice-0","recommendationservice-1","recommendationservice-2","recommendationservice-grpc","recommendationservice2-0","redis-cart-0","redis-cart2-0","shippingservice-0","shippingservice-1","shippingservice-2","shippingservice-grpc","shippingservice2-0"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[18.281,54.844,91.406,127.969,164.531,201.094,237.656,274.219,310.781,347.344,383.906,420.469,457.031,493.594,530.156,566.719,603.281,639.844,676.406,712.969,749.531,786.094,822.656,859.219,895.781,932.344,968.906,1005.469,1042.031,1078.594,1115.156,1151.719,1188.281,1224.844,1261.406,1297.969,1334.531,1371.094,1407.656,1444.219,1480.781,1517.344,1553.906,1590.469,1627.031,1663.594,1700.156,1736.719,1773.281,1809.844,1846.406,1882.969,1919.531,1956.094,1992.656,2029.219,2065.781,2102.344,2138.906,2175.469,2212.031,2248.594,2285.156,2321.719]
[M1] rank=1 service=adservice2 metric=jvm_classes_loaded baseline=4480.0 peak=0.0 signed_z=-999.0 onset_bin=36 onset_rel_s=1334.531 persistence_bins=18
values_compact=delta:4480,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-4480,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M2] rank=2 service=adservice metric=jvm_classes_loaded baseline=5181.0 peak=0.0 signed_z=-999.0 onset_bin=36 onset_rel_s=1334.531 persistence_bins=18
values_compact=delta:5181,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-5181,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M3] rank=3 service=cartservice-0 metric=container_fs_inodes./dev/vda1 baseline=0.0 peak=2.0 signed_z=999.0 onset_bin=49 onset_rel_s=1809.844 persistence_bins=2
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,0,-2,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M4] rank=4 service=cartservice-0 metric=container_memory_failures.container.pgmajfault baseline=0.0 peak=1.0 signed_z=999.0 onset_bin=49 onset_rel_s=1809.844 persistence_bins=3
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.25,0.25,0,-0.5,0,0,0,0,0,0,1
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M5] rank=5 service=cartservice-0 metric=container_memory_failures.hierarchy.pgmajfault baseline=0.0 peak=1.0 signed_z=999.0 onset_bin=49 onset_rel_s=1809.844 persistence_bins=3
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.25,0.25,0,-0.5,0,0,0,0,0,0,1
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M6] rank=6 service=cartservice-0 metric=container_memory_mapped_file baseline=2981888.0 peak=7503872.0 signed_z=999.0 onset_bin=49 onset_rel_s=1809.844 persistence_bins=10
values_compact=delta:2981888,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,2160640,2320384,32768,2048,2048,0,0,0,0,0,4096
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M7] rank=7 service=cartservice-0 metric=istio_request_bytes.grpc.200.14.0 baseline=0.0 peak=327.5 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,327.5,0,-327.5,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M8] rank=8 service=cartservice-0 metric=istio_request_duration_milliseconds.grpc.200.14.0 baseline=0.0 peak=241.125 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,241.125,0,-241.125,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M9] rank=9 service=cartservice-0 metric=istio_requests.grpc.200.14.0 baseline=0.0 peak=0.5 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.5,0,-0.5,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M10] rank=10 service=cartservice-0 metric=istio_response_bytes.grpc.200.14.0 baseline=0.0 peak=625.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,625,0,-625,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M11] rank=11 service=emailservice-1 metric=container_cpu_usage_seconds baseline=0.017941 peak=19.197607 signed_z=999.0 onset_bin=36 onset_rel_s=1334.531 persistence_bins=6
values_compact=delta:0.014379,0.003949,0.002506,-0.00162,-0.007426,0.008192,0.0001,-0.00466,0.002772,0.001968,0.000335,-0.003158,-0.001972,0.001538,-0.000162,0.001646,0.000562,-0.000559,-0.003973,0.009048,-0.009539,19.183681,0,-9.10538,5.517518,-12.953359,-2.638316,-0.000262,-0.00403,0.015898,-0.013758,0.002243,-0.001491,-0.000862,0.005718,-0.002943,-0.00899,0.012127,-0.003491,-0.000598
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M12] rank=12 service=emailservice-1 metric=container_cpu_user_seconds baseline=0.005583 peak=19.18 signed_z=999.0 onset_bin=36 onset_rel_s=1334.531 persistence_bins=4
values_compact=delta:0.005,0,0,0.005,-0.01,0.01,-0.01,0,0.01,0,-0.003333,-0.003334,0.001667,0,0,0,0.005,0,-0.01,0.006667,-0.003334,19.176667,0,-9.115,5.52,-12.94,-2.64,-0.005,0.005,0.006667,-0.008334,0.003334,-0.003334,-0.003333,0.013333,-0.006666,-0.006667,0.01,-0.003333,-0.003334
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[1200.0,2340.0]

=== LOG SUMMARY ===
{"entries":[{"error_logs":23,"error_pct":7.21,"service":"emailservice-1","total_logs":319}],"mode":"errors","omitted_services":30,"service_count":31}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":13.7,"error_pct":0.0,"p95_during_ms":0.09519999999999985,"p95_pre_ms":0.08375,"service":"shippingservice-2","spans":481},{"delta_pct":11.1,"error_pct":0.0,"p95_during_ms":0.02,"p95_pre_ms":0.018,"service":"adservice-0","spans":1029},{"delta_pct":7.0,"error_pct":0.0,"p95_during_ms":0.1485,"p95_pre_ms":0.13879999999999995,"service":"paymentservice-1","spans":68},{"delta_pct":-6.9,"error_pct":0.0,"p95_during_ms":0.01675,"p95_pre_ms":0.018,"service":"adservice-1","spans":1028},{"delta_pct":-5.2,"error_pct":0.0,"p95_during_ms":0.07679999999999998,"p95_pre_ms":0.081,"service":"shippingservice-0","spans":481},{"delta_pct":4.7,"error_pct":0.0,"p95_during_ms":41.6621,"p95_pre_ms":39.80964999999999,"service":"checkoutservice-1","spans":810},{"delta_pct":3.1,"error_pct":0.0,"p95_during_ms":0.23745,"p95_pre_ms":0.23039999999999997,"service":"emailservice-0","spans":69},{"delta_pct":-2.8,"error_pct":0.0,"p95_during_ms":0.14825,"p95_pre_ms":0.15249999999999997,"service":"paymentservice-0","spans":67}],"omitted_services":22,"service_count":30}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=16 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":1260.0,"rank":1,"service":"adservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1260.0,"rank":2,"service":"adservice2","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1260.0,"rank":3,"service":"emailservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1260.0,"rank":4,"service":"node-5","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1380.0,"rank":5,"service":"emailservice2","severity_z":188.018},{"evidence_source":"metric","onset_rel_s":1440.0,"rank":6,"service":"frontend2","severity_z":214.955},{"evidence_source":"metric","onset_rel_s":1500.0,"rank":7,"service":"recommendationservice","severity_z":226.234},{"evidence_source":"metric","onset_rel_s":1500.0,"rank":8,"service":"currencyservice","severity_z":221.586},{"evidence_source":"metric","onset_rel_s":1740.0,"rank":9,"service":"cartservice2","severity_z":293.06},{"evidence_source":"metric","onset_rel_s":1740.0,"rank":10,"service":"shippingservice","severity_z":214.342},{"evidence_source":"trace","onset_rel_s":1779.6,"rank":11,"service":"cartservice","severity_z":10.763},{"evidence_source":"metric","onset_rel_s":1800.0,"rank":12,"service":"paymentservice2","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":2220.0,"rank":13,"service":"frontend","severity_z":999.0},{"evidence_source":"trace","onset_rel_s":2315.4,"rank":14,"service":"paymentservice","severity_z":30.61}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"adservice","caller":"frontend"},{"callee":"cartservice","caller":"frontend"},{"callee":"currencyservice","caller":"frontend"},{"callee":"recommendationservice","caller":"frontend"},{"callee":"shippingservice","caller":"frontend"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

## Assistant

{
"services": [
"node-5",
"adservice",
"adservice2",
"emailservice",
"cartservice-0"
],
"reason": "Node-5 is the root cause because it appears in the earliest onset propagation list (rank 4) alongside the affected services, indicating a shared infrastructure failure that triggered the simultaneous JVM crashes in adservice/adservice2 and CPU spikes in emailservice.",
"confidence": "high"
}
