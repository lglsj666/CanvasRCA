# Causal SFT pilot evaluation — INC-C327E972C4F1 — adapter

Private evaluator case id: `aiops2025_6add78b2-480`

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

[image: RQs/RQ0/results/causal_integration_sft_v1/data/cases/INC-C327E972C4F1/dashboard.png]

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
opaque_id: INC-C327E972C4F1
observation_window={"duration_rel_s":1860.0,"source_metric_rows":32}
selection_summary={"candidate_count":60,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":472,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","cartservice","cartservice-0","cartservice-1","cartservice-2","checkoutservice","checkoutservice-0","checkoutservice-1","checkoutservice-2","currencyservice","currencyservice-0","currencyservice-1","currencyservice-2","emailservice","emailservice-0","emailservice-1","emailservice-2","example-ant-10-29178240-fgnjt","example-ant-29178240-wkc4g","frontend","frontend-0","frontend-1","frontend-2","hipstershop","k8s-master1","k8s-master2","k8s-master3","node-1","node-2","node-3","node-4","node-5","node-6","node-7","node-8","paymentservice","paymentservice-0","paymentservice-1","paymentservice-2","productcatalogservice","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","recommendationservice","recommendationservice-0","recommendationservice-1","recommendationservice-2","redis","redis-cart","redis-cart-0","shippingservice","shippingservice-0","shippingservice-1","shippingservice-2","tidb-pd","tidb-tidb","tidb-tikv"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[14.531,43.594,72.656,101.719,130.781,159.844,188.906,217.969,247.031,276.094,305.156,334.219,363.281,392.344,421.406,450.469,479.531,508.594,537.656,566.719,595.781,624.844,653.906,682.969,712.031,741.094,770.156,799.219,828.281,857.344,886.406,915.469,944.531,973.594,1002.656,1031.719,1060.781,1089.844,1118.906,1147.969,1177.031,1206.094,1235.156,1264.219,1293.281,1322.344,1351.406,1380.469,1409.531,1438.594,1467.656,1496.719,1525.781,1554.844,1583.906,1612.969,1642.031,1671.094,1700.156,1729.219,1758.281,1787.344,1816.406,1845.469]
[M1] rank=1 service=adservice-2 metric=client_error baseline=0.0 peak=6.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,6,-6,6,-6,0,0,0,0,0,6,-6
missing_mask_bits=0101010101010101010101010101010110101010101010101010101010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1
[M2] rank=2 service=adservice-2 metric=client_error_ratio baseline=0.0 peak=1.83 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1.83,-1.83,1.74,-1.74,0,0,0,0,0,1.56,-1.56
missing_mask_bits=0101010101010101010101010101010110101010101010101010101010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1
[M3] rank=3 service=adservice-2 metric=error baseline=0.0 peak=6.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,6,-6,6,-6,0,0,0,0,0,6,-6
missing_mask_bits=0101010101010101010101010101010110101010101010101010101010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1
[M4] rank=4 service=adservice-2 metric=error_ratio baseline=0.0 peak=1.83 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1.83,-1.83,1.74,-1.74,0,0,0,0,0,1.56,-1.56
missing_mask_bits=0101010101010101010101010101010110101010101010101010101010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1
[M5] rank=5 service=adservice metric=client_error baseline=0.0 peak=6.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,6,-6,6,-6,0,0,0,0,0,6,-6
missing_mask_bits=0101010101010101010101010101010110101010101010101010101010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1
[M6] rank=6 service=adservice metric=client_error_ratio baseline=0.0 peak=1.42 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1.42,-1.42,1.36,-1.36,0,0,0,0,0,1.27,-1.27
missing_mask_bits=0101010101010101010101010101010110101010101010101010101010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1
[M7] rank=7 service=adservice metric=error baseline=0.0 peak=6.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,6,-6,6,-6,0,0,0,0,0,6,-6
missing_mask_bits=0101010101010101010101010101010110101010101010101010101010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1
[M8] rank=8 service=adservice metric=error_ratio baseline=0.0 peak=1.42 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1.42,-1.42,1.36,-1.36,0,0,0,0,0,1.27,-1.27
missing_mask_bits=0101010101010101010101010101010110101010101010101010101010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1
[M9] rank=9 service=hipstershop metric=client_error baseline=0.0 peak=6.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,6,-6,6,-6,0,0,0,0,0,6,-6
missing_mask_bits=0101010101010101010101010101010110101010101010101010101010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1
[M10] rank=10 service=hipstershop metric=client_error_ratio baseline=0.0 peak=0.07 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.07,-0.07,0.06,-0.06,0,0,0,0,0,0.06,-0.06
missing_mask_bits=0101010101010101010101010101010110101010101010101010101010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1
[M11] rank=11 service=hipstershop metric=error baseline=0.0 peak=6.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,6,-6,6,-6,0,0,0,0,0,6,-6
missing_mask_bits=0101010101010101010101010101010110101010101010101010101010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1
[M12] rank=12 service=hipstershop metric=error_ratio baseline=0.0 peak=0.07 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.07,-0.07,0.06,-0.06,0,0,0,0,0,0.06,-0.06
missing_mask_bits=0101010101010101010101010101010110101010101010101010101010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[1200.0,1320.0]

=== LOG SUMMARY ===
{"entries":[{"change_pct":-100.0,"n_during":0,"n_pre":25,"service":"redis-cart-0"},{"change_pct":-94.6,"n_during":429,"n_pre":7877,"service":"currencyservice-1"},{"change_pct":-94.5,"n_during":16,"n_pre":292,"service":"currencyservice-0"},{"change_pct":-94.1,"n_during":54,"n_pre":909,"service":"cartservice-2"},{"change_pct":-94.1,"n_during":27,"n_pre":456,"service":"checkoutservice-1"},{"change_pct":-94.1,"n_during":3,"n_pre":51,"service":"emailservice-0"},{"change_pct":-94.1,"n_during":3,"n_pre":51,"service":"emailservice-2"},{"change_pct":-94.1,"n_during":6,"n_pre":102,"service":"paymentservice-0"}],"mode":"volume","omitted_services":14,"service_count":22}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":28.2,"error_pct":0.0,"p95_during_ms":7.0642499999999995,"p95_pre_ms":5.511749999999995,"service":"recommendationservice","spans":5720},{"delta_pct":-25.2,"error_pct":0.0,"p95_during_ms":0.7602,"p95_pre_ms":1.016,"service":"emailservice","spans":158},{"delta_pct":21.4,"error_pct":0.0,"p95_during_ms":4.184,"p95_pre_ms":3.4466499999999938,"service":"redis","spans":4121},{"delta_pct":19.2,"error_pct":0.0,"p95_during_ms":0.5070999999999996,"p95_pre_ms":0.4253999999999996,"service":"shippingservice","spans":1109},{"delta_pct":13.9,"error_pct":0.0,"p95_during_ms":5.85445,"p95_pre_ms":5.140399999999992,"service":"cartservice","spans":3805},{"delta_pct":9.4,"error_pct":0.0,"p95_during_ms":190.2156999999999,"p95_pre_ms":173.82294999999993,"service":"checkoutservice","spans":1858},{"delta_pct":-1.8,"error_pct":0.0,"p95_during_ms":14.433499999999999,"p95_pre_ms":14.692,"service":"productcatalogservice","spans":21512},{"delta_pct":-0.5,"error_pct":0.0,"p95_during_ms":95.0668,"p95_pre_ms":95.5516,"service":"frontend","spans":46454}],"omitted_services":0,"service_count":8}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=8 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":1080.0,"rank":1,"service":"emailservice","severity_z":21.646},{"evidence_source":"metric","onset_rel_s":1260.0,"rank":2,"service":"adservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1260.0,"rank":3,"service":"hipstershop","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1260.0,"rank":4,"service":"node-5","severity_z":24.529},{"evidence_source":"metric","onset_rel_s":1320.0,"rank":5,"service":"paymentservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1440.0,"rank":6,"service":"redis-cart","severity_z":20.471},{"evidence_source":"metric","onset_rel_s":1620.0,"rank":7,"service":"currencyservice","severity_z":15.699},{"evidence_source":"metric","onset_rel_s":1740.0,"rank":8,"service":"node-3","severity_z":16.604},{"evidence_source":"metric","onset_rel_s":1860.0,"rank":9,"service":"node-1","severity_z":999.0},{"evidence_source":"none","onset_rel_s":null,"rank":10,"service":"productcatalogservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":11,"service":"shippingservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":12,"service":"cartservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":13,"service":"tidb-tikv","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":14,"service":"tidb-tidb","severity_z":0.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

## Assistant

{"confidence":"high","reason":"The earliest anomaly onset (1080s) is observed in emailservice, which precedes the simultaneous degradation of adservice, hipstershop, and node-5 (1260s), indicating that emailservice is the origin of the fault that propagated to downstream services and co-located infrastructure.","services":["emailservice","adservice","hipstershop","node-5","paymentservice"]}

## Result

```json
{
  "record_type": "episode",
  "dataset": "aiops2025",
  "case_id": "aiops2025_6add78b2-480",
  "opaque_incident_id": "INC-C327E972C4F1",
  "stage_partition": "development_heldout_v2",
  "condition": "adapter",
  "status": "ok",
  "error": null,
  "parse_ok": true,
  "predicted": [
    "emailservice",
    "adservice",
    "hipstershop",
    "node-5",
    "paymentservice"
  ],
  "rank": 5,
  "mrr": 0.2,
  "ac1": 0.0,
  "ac3": 0.0,
  "ac5": 1.0,
  "avg3": 0.0,
  "avg5": 0.2,
  "input_tokens": 8982,
  "output_tokens": 90,
  "total_tokens": 9072,
  "preflight_input_tokens": 8982,
  "server_token_count_match": true,
  "wall_time_s": 10.524044275283813,
  "gpu_active_time_s_sampled": 0.25,
  "peak_gpu_memory_mib_sampled": 67621.0,
  "gpu_samples": 1,
  "gpu_sampling_interval_s": 0.25
}
```
