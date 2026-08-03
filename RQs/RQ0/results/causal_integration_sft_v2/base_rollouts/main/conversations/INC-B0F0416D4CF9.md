# Causal SFT v2 base rollout — INC-B0F0416D4CF9

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

[image: RQs/RQ0/results/causal_integration_sft_v1/data/cases/INC-B0F0416D4CF9/dashboard.png]

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
opaque_id: INC-B0F0416D4CF9
observation_window={"duration_rel_s":2220.0,"source_metric_rows":38}
selection_summary={"candidate_count":60,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":494,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","cartservice","cartservice-0","cartservice-1","cartservice-2","checkoutservice","checkoutservice-0","checkoutservice-1","checkoutservice-2","currencyservice","currencyservice-0","currencyservice-1","currencyservice-2","emailservice","emailservice-0","emailservice-1","emailservice-2","example-ant-10-29162400-r2drh","example-ant-29162400-cdnr4","frontend","frontend-0","frontend-1","frontend-2","hipstershop","k8s-master1","k8s-master2","k8s-master3","node-1","node-2","node-3","node-4","node-5","node-6","node-7","node-8","paymentservice","paymentservice-0","paymentservice-1","paymentservice-2","productcatalogservice","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","recommendationservice","recommendationservice-0","recommendationservice-1","recommendationservice-2","redis","redis-cart","redis-cart-0","shippingservice","shippingservice-0","shippingservice-1","shippingservice-2","tidb-pd","tidb-tidb","tidb-tikv"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[17.344,52.031,86.719,121.406,156.094,190.781,225.469,260.156,294.844,329.531,364.219,398.906,433.594,468.281,502.969,537.656,572.344,607.031,641.719,676.406,711.094,745.781,780.469,815.156,849.844,884.531,919.219,953.906,988.594,1023.281,1057.969,1092.656,1127.344,1162.031,1196.719,1231.406,1266.094,1300.781,1335.469,1370.156,1404.844,1439.531,1474.219,1508.906,1543.594,1578.281,1612.969,1647.656,1682.344,1717.031,1751.719,1786.406,1821.094,1855.781,1890.469,1925.156,1959.844,1994.531,2029.219,2063.906,2098.594,2133.281,2167.969,2202.656]
[M1] rank=1 service=adservice-1 metric=client_error baseline=0.0 peak=6.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,6,-6,0,0,0,0,6,-6,0,0,0,0,0,0
missing_mask_bits=0010100101010010101001010010101001010100101001010100101010010100
observed_counts_compact=csv:1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1
[M2] rank=2 service=adservice-1 metric=client_error_ratio baseline=0.0 peak=0.64 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.64,-0.64,0,0,0,0,0.6,-0.6,0,0,0,0,0,0
missing_mask_bits=0010100101010010101001010010101001010100101001010100101010010100
observed_counts_compact=csv:1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1
[M3] rank=3 service=adservice-1 metric=error baseline=0.0 peak=6.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,6,-6,0,0,0,0,6,-6,0,0,0,0,0,0
missing_mask_bits=0010100101010010101001010010101001010100101001010100101010010100
observed_counts_compact=csv:1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1
[M4] rank=4 service=adservice-1 metric=error_ratio baseline=0.0 peak=0.64 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.64,-0.64,0,0,0,0,0.6,-0.6,0,0,0,0,0,0
missing_mask_bits=0010100101010010101001010010101001010100101001010100101010010100
observed_counts_compact=csv:1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1
[M5] rank=5 service=adservice-1 metric=pod_fs_reads_bytes baseline=0.0 peak=28749.42 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,28749.42,-28749.42,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010100101010010101001010010101001010100101001010100101010010100
observed_counts_compact=csv:1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1
[M6] rank=6 service=adservice metric=client_error baseline=0.0 peak=6.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,6,-6,0,0,0,0,6,-6,0,0,0,0,0,0
missing_mask_bits=0010100101010010101001010010101001010100101001010100101010010100
observed_counts_compact=csv:1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1
[M7] rank=7 service=adservice metric=client_error_ratio baseline=0.0 peak=0.58 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.58,-0.58,0,0,0,0,0.55,-0.55,0,0,0,0,0,0
missing_mask_bits=0010100101010010101001010010101001010100101001010100101010010100
observed_counts_compact=csv:1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1
[M8] rank=8 service=adservice metric=error baseline=0.0 peak=6.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,6,-6,0,0,0,0,6,-6,0,0,0,0,0,0
missing_mask_bits=0010100101010010101001010010101001010100101001010100101010010100
observed_counts_compact=csv:1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1
[M9] rank=9 service=adservice metric=error_ratio baseline=0.0 peak=0.58 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.58,-0.58,0,0,0,0,0.55,-0.55,0,0,0,0,0,0
missing_mask_bits=0010100101010010101001010010101001010100101001010100101010010100
observed_counts_compact=csv:1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1
[M10] rank=10 service=currencyservice-0 metric=pod_cpu_usage baseline=0.01 peak=0.02 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.01,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.01,0,-0.01,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010100101010010101001010010101001010100101001010100101010010100
observed_counts_compact=csv:1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1
[M11] rank=11 service=hipstershop metric=client_error baseline=0.0 peak=6.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,6,-6,0,0,0,0,6,-6,0,0,0,0,0,0
missing_mask_bits=0010100101010010101001010010101001010100101001010100101010010100
observed_counts_compact=csv:1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1
[M12] rank=12 service=hipstershop metric=client_error_ratio baseline=0.0 peak=0.02 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.02,-0.02,0,0,0,0,0.02,-0.02,0,0,0,0,0,0
missing_mask_bits=0010100101010010101001010010101001010100101001010100101010010100
observed_counts_compact=csv:1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[1380.0,1500.0]

=== LOG SUMMARY ===
{"entries":[{"change_pct":-94.6,"n_during":21,"n_pre":387,"service":"checkoutservice-2"},{"change_pct":-94.4,"n_during":445,"n_pre":7954,"service":"adservice-1"},{"change_pct":-94.4,"n_during":4653,"n_pre":82575,"service":"cartservice-2"},{"change_pct":-94.4,"n_during":3512,"n_pre":62439,"service":"currencyservice-1"},{"change_pct":-94.4,"n_during":1060,"n_pre":19085,"service":"frontend-1"},{"change_pct":-94.4,"n_during":536,"n_pre":9535,"service":"recommendationservice-2"},{"change_pct":-94.3,"n_during":10,"n_pre":175,"service":"emailservice-0"},{"change_pct":-94.3,"n_during":553,"n_pre":9762,"service":"frontend-0"}],"mode":"volume","omitted_services":15,"service_count":23}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":14.2,"error_pct":0.0,"p95_during_ms":0.514,"p95_pre_ms":0.45025000000000004,"service":"shippingservice","spans":3812},{"delta_pct":-13.9,"error_pct":0.0,"p95_during_ms":114.1245,"p95_pre_ms":132.48329999999999,"service":"checkoutservice","spans":6413},{"delta_pct":-13.5,"error_pct":0.0,"p95_during_ms":0.9154,"p95_pre_ms":1.0578499999999997,"service":"emailservice","spans":547},{"delta_pct":-5.3,"error_pct":0.0,"p95_during_ms":77.9885,"p95_pre_ms":82.36340000000001,"service":"frontend","spans":160120},{"delta_pct":-2.8,"error_pct":0.0,"p95_during_ms":13.078799999999998,"p95_pre_ms":13.452199999999982,"service":"productcatalogservice","spans":73952},{"delta_pct":-1.7,"error_pct":0.0,"p95_during_ms":4.9567,"p95_pre_ms":5.042,"service":"recommendationservice","spans":19710},{"delta_pct":-1.3,"error_pct":0.0,"p95_during_ms":2.717,"p95_pre_ms":2.753699999999993,"service":"redis","spans":14216},{"delta_pct":-0.6,"error_pct":0.0,"p95_during_ms":4.368,"p95_pre_ms":4.392899999999992,"service":"cartservice","spans":13048}],"omitted_services":0,"service_count":8}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=8 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":1140.0,"rank":1,"service":"tidb-tidb","severity_z":17.75},{"evidence_source":"metric","onset_rel_s":1260.0,"rank":2,"service":"node-1","severity_z":21.906},{"evidence_source":"metric","onset_rel_s":1260.0,"rank":3,"service":"node-6","severity_z":18.252},{"evidence_source":"metric","onset_rel_s":1320.0,"rank":4,"service":"node-8","severity_z":24.6},{"evidence_source":"metric","onset_rel_s":1440.0,"rank":5,"service":"adservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1440.0,"rank":6,"service":"currencyservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1440.0,"rank":7,"service":"hipstershop","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1500.0,"rank":8,"service":"paymentservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1800.0,"rank":9,"service":"cartservice","severity_z":17.56},{"evidence_source":"none","onset_rel_s":null,"rank":10,"service":"redis-cart","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":11,"service":"shippingservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":12,"service":"k8s-master1","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":13,"service":"k8s-master2","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":14,"service":"frontend","severity_z":0.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"cartservice","caller":"frontend"},{"callee":"shippingservice","caller":"frontend"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

## Assistant

{
"services": [
"node-8",
"node-1",
"node-6",
"adservice",
"currencyservice"
],
"reason": "Node-8 is the most likely root cause as it is the earliest infrastructure component to show a critical anomaly (z=24.6) immediately preceding the simultaneous failure of multiple unrelated services (adservice, currencyservice, hipstershop), indicating a host-level resource exhaustion or network fault.",
"confidence": "high"
}
