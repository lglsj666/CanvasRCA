# Causal SFT v2 base rollout — INC-0FAC1A2DD9E9

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

[image: RQs/RQ0/results/causal_integration_sft_v1/data/cases/INC-0FAC1A2DD9E9/dashboard.png]

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
opaque_id: INC-0FAC1A2DD9E9
observation_window={"duration_rel_s":2340.0,"source_metric_rows":40}
selection_summary={"candidate_count":63,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":1440,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","adservice-grpc","adservice-http","adservice2","adservice2-0","cartservice-0","cartservice-1","cartservice-2","cartservice-grpc","cartservice2-0","checkoutservice-0","checkoutservice-1","checkoutservice-2","checkoutservice-grpc","checkoutservice2-0","currencyservice-0","currencyservice-1","currencyservice-2","currencyservice-grpc","currencyservice2-0","emailservice-0","emailservice-1","emailservice-2","emailservice-grpc","emailservice2-0","frontend-0","frontend-1","frontend-2","frontend-http","frontend2-0","istio-egressgateway-7bfdcc9d86-zpjpg","istio-ingressgateway-565bffd4d-6bl7m","node-1","node-2","node-3","node-4","node-5","node-6","paymentservice-0","paymentservice-1","paymentservice-2","paymentservice-grpc","paymentservice2-0","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","productcatalogservice-grpc","productcatalogservice2-0","recommendationservice-0","recommendationservice-1","recommendationservice-2","recommendationservice-grpc","recommendationservice2-0","redis-cart-0","redis-cart2-0","shippingservice-0","shippingservice-1","shippingservice-2","shippingservice-grpc","shippingservice2-0"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[18.281,54.844,91.406,127.969,164.531,201.094,237.656,274.219,310.781,347.344,383.906,420.469,457.031,493.594,530.156,566.719,603.281,639.844,676.406,712.969,749.531,786.094,822.656,859.219,895.781,932.344,968.906,1005.469,1042.031,1078.594,1115.156,1151.719,1188.281,1224.844,1261.406,1297.969,1334.531,1371.094,1407.656,1444.219,1480.781,1517.344,1553.906,1590.469,1627.031,1663.594,1700.156,1736.719,1773.281,1809.844,1846.406,1882.969,1919.531,1956.094,1992.656,2029.219,2065.781,2102.344,2138.906,2175.469,2212.031,2248.594,2285.156,2321.719]
[M1] rank=1 service=adservice2 metric=java_lang_Memory_ObjectPendingFinalizationCount baseline=0.0 peak=1.333333 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.083333,-0.083333,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1.333333,-1.333333,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M2] rank=2 service=adservice metric=java_lang_Memory_ObjectPendingFinalizationCount baseline=0.0 peak=0.083333 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.083333,-0.083333,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M3] rank=3 service=node-2 metric=system.disk.pct_usage baseline=41.45 peak=41.46 signed_z=999.0 onset_bin=49 onset_rel_s=1809.844 persistence_bins=8
values_compact=delta:41.45,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.01,0,0,0,-0.01,0,0.01,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M4] rank=4 service=node-6 metric=system.disk.pct_usage baseline=26.92 peak=26.93 signed_z=999.0 onset_bin=36 onset_rel_s=1334.531 persistence_bins=18
values_compact=delta:26.92,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.01,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M5] rank=5 service=paymentservice-2 metric=container_cpu_system_seconds baseline=0.0 peak=0.01 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.01,-0.01,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M6] rank=6 service=productcatalogservice-0 metric=container_fs_inodes./dev/vda1 baseline=0.0 peak=1.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,-1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M7] rank=7 service=productcatalogservice-1 metric=container_fs_inodes./dev/vda1 baseline=0.0 peak=1.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,-1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M8] rank=8 service=productcatalogservice-2 metric=container_fs_inodes./dev/vda1 baseline=0.0 peak=1.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,-1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M9] rank=9 service=productcatalogservice2-0 metric=container_fs_inodes./dev/vda1 baseline=0.0 peak=1.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,-1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M10] rank=10 service=adservice metric=jvm_memory_pool_MB_used.Tenured_Gen baseline=54.426256 peak=54.619286 signed_z=845.895 onset_bin=49 onset_rel_s=1809.844 persistence_bins=10
values_compact=delta:54.425884,0.000017,0.000056,0.000056,0.00003,0.000036,0,0.000012,0.000153,0.000041,0,0.00004,0.000082,0,0.00002,0.000041,0.000051,0.00001,0.000061,0,0,0.000076,0,0,0.000016,0.000076,0.00003,0.000061,0.15957,0.03221,0.000031,0.00003,0.000031,0,0,0.000032,0.000044,0,0.000097,0.000392
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M11] rank=11 service=adservice metric=java_lang_GarbageCollector_LastGcInfo_memoryUsageAfterGc_used.Tenured_Gen.Copy baseline=57070063.333333 peak=57272456.0 signed_z=841.1 onset_bin=49 onset_rel_s=1809.844 persistence_bins=10
values_compact=delta:57069664,24,64,58.666667,32,37.333333,0,0,168,48,0,32,96,0,21.333333,42.666667,53.333333,10.666667,58.666667,5.333333,0,73.333333,6.666667,0,10.666667,80,37.333333,58.666667,167318,33772.666666,42.666667,26.666667,37.333333,0,0,26.666667,53.333333,0,90.666667,405.333333
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M12] rank=12 service=adservice metric=jvm_memory_pool_allocated_MB_total.Tenured_Gen baseline=124.385084 peak=124.578087 signed_z=840.953 onset_bin=49 onset_rel_s=1809.844 persistence_bins=10
values_compact=delta:124.384705,0.000022,0.000062,0.00005,0.000031,0.000041,0,0,0.00016,0.000046,0,0.00003,0.000092,0,0.000015,0.000046,0.000045,0.000016,0.000056,0.000005,0,0.00007,0.000006,0,0.00001,0.000077,0.000035,0.000056,0.143601,0.048174,0.000041,0.000025,0.000036,0,0,0.000025,0.000051,0,0.000081,0.000377
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[1740.0,2040.0]

=== LOG SUMMARY ===
{"entries":[{"change_pct":-100.0,"n_during":0,"n_pre":2,"service":"frontend-1"},{"change_pct":-90.6,"n_during":12,"n_pre":128,"service":"paymentservice-0"},{"change_pct":-87.2,"n_during":15,"n_pre":117,"service":"emailservice-2"},{"change_pct":-86.3,"n_during":150,"n_pre":1093,"service":"shippingservice-0"},{"change_pct":-85.9,"n_during":1333,"n_pre":9480,"service":"cartservice-2"},{"change_pct":-85.9,"n_during":357,"n_pre":2523,"service":"recommendationservice-1"},{"change_pct":-85.8,"n_during":96,"n_pre":677,"service":"checkoutservice-0"},{"change_pct":-85.8,"n_during":3679,"n_pre":25892,"service":"frontend-2"}],"mode":"volume","omitted_services":23,"service_count":31}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":-100.0,"error_pct":0.0,"p95_during_ms":0.0,"p95_pre_ms":1.0,"service":"cartservice-2","spans":2254},{"delta_pct":-99.1,"error_pct":0.0,"p95_during_ms":5.938399999999999,"p95_pre_ms":688.207,"service":"productcatalogservice2-0","spans":6558},{"delta_pct":-98.8,"error_pct":0.0,"p95_during_ms":5.93325,"p95_pre_ms":492.86,"service":"productcatalogservice-0","spans":6412},{"delta_pct":-98.8,"error_pct":0.0,"p95_during_ms":5.8923999999999985,"p95_pre_ms":492.47269999999986,"service":"productcatalogservice-1","spans":6411},{"delta_pct":-98.8,"error_pct":0.0,"p95_during_ms":6.176,"p95_pre_ms":495.20349999999996,"service":"productcatalogservice-2","spans":6412},{"delta_pct":-98.4,"error_pct":0.0,"p95_during_ms":3.0526999999999997,"p95_pre_ms":186.05444999999997,"service":"recommendationservice-1","spans":1614},{"delta_pct":-97.0,"error_pct":0.0,"p95_during_ms":2.8634999999999997,"p95_pre_ms":95.18874999999997,"service":"recommendationservice-0","spans":1616},{"delta_pct":-96.7,"error_pct":0.0,"p95_during_ms":3.0566999999999998,"p95_pre_ms":92.99335,"service":"recommendationservice-2","spans":1614}],"omitted_services":31,"service_count":39}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=16 omitted_edges=1
[{"evidence_source":"metric","onset_rel_s":1200.0,"rank":1,"service":"productcatalogservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1200.0,"rank":2,"service":"productcatalogservice2","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1260.0,"rank":3,"service":"frontend2","severity_z":139.273},{"evidence_source":"metric","onset_rel_s":1320.0,"rank":4,"service":"node-6","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1320.0,"rank":5,"service":"paymentservice2","severity_z":171.598},{"evidence_source":"metric","onset_rel_s":1320.0,"rank":6,"service":"redis-cart","severity_z":106.877},{"evidence_source":"metric","onset_rel_s":1380.0,"rank":7,"service":"checkoutservice2","severity_z":87.615},{"evidence_source":"metric","onset_rel_s":1440.0,"rank":8,"service":"paymentservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1440.0,"rank":9,"service":"shippingservice2","severity_z":169.912},{"evidence_source":"metric","onset_rel_s":1560.0,"rank":10,"service":"adservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1560.0,"rank":11,"service":"frontend","severity_z":157.416},{"evidence_source":"metric","onset_rel_s":1620.0,"rank":12,"service":"node-1","severity_z":225.859},{"evidence_source":"metric","onset_rel_s":1800.0,"rank":13,"service":"node-2","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":2220.0,"rank":14,"service":"adservice2","severity_z":999.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"paymentservice2","caller":"checkoutservice2"},{"callee":"productcatalogservice2","caller":"checkoutservice2"},{"callee":"shippingservice2","caller":"checkoutservice2"},{"callee":"adservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"frontend"},{"callee":"adservice2","caller":"frontend2"},{"callee":"checkoutservice2","caller":"frontend2"},{"callee":"productcatalogservice2","caller":"frontend2"},{"callee":"shippingservice2","caller":"frontend2"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

## Assistant

{
"services": [
"productcatalogservice",
"productcatalogservice2"
],
"reason": "productcatalogservice and productcatalogservice2 show the earliest anomaly onset (rank 1 and 2) with significant trace latency degradation, indicating they are the origin of the fault before it propagates to downstream services like checkoutservice2 and frontend2.",
"confidence": "high"
}
