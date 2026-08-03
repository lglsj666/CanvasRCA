# Causal SFT v2 base rollout — INC-A33D2AD85F48

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

[image: RQs/RQ0/results/causal_integration_sft_v1/data/cases/INC-A33D2AD85F48/dashboard.png]

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
opaque_id: INC-A33D2AD85F48
observation_window={"duration_rel_s":2340.0,"source_metric_rows":40}
selection_summary={"candidate_count":63,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":1459,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","adservice-grpc","adservice-http","adservice2","adservice2-0","cartservice-0","cartservice-1","cartservice-2","cartservice-grpc","cartservice2-0","checkoutservice-0","checkoutservice-1","checkoutservice-2","checkoutservice-grpc","checkoutservice2-0","currencyservice-0","currencyservice-1","currencyservice-2","currencyservice-grpc","currencyservice2-0","emailservice-0","emailservice-1","emailservice-2","emailservice-grpc","emailservice2-0","frontend-0","frontend-1","frontend-2","frontend-http","frontend2-0","istio-egressgateway-7bfdcc9d86-22q7z","istio-ingressgateway-565bffd4d-4nr6v","node-1","node-2","node-3","node-4","node-5","node-6","paymentservice-0","paymentservice-1","paymentservice-2","paymentservice-grpc","paymentservice2-0","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","productcatalogservice-grpc","productcatalogservice2-0","recommendationservice-0","recommendationservice-1","recommendationservice-2","recommendationservice-grpc","recommendationservice2-0","redis-cart-0","redis-cart2-0","shippingservice-0","shippingservice-1","shippingservice-2","shippingservice-grpc","shippingservice2-0"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[18.281,54.844,91.406,127.969,164.531,201.094,237.656,274.219,310.781,347.344,383.906,420.469,457.031,493.594,530.156,566.719,603.281,639.844,676.406,712.969,749.531,786.094,822.656,859.219,895.781,932.344,968.906,1005.469,1042.031,1078.594,1115.156,1151.719,1188.281,1224.844,1261.406,1297.969,1334.531,1371.094,1407.656,1444.219,1480.781,1517.344,1553.906,1590.469,1627.031,1663.594,1700.156,1736.719,1773.281,1809.844,1846.406,1882.969,1919.531,1956.094,1992.656,2029.219,2065.781,2102.344,2138.906,2175.469,2212.031,2248.594,2285.156,2321.719]
[M1] rank=1 service=cartservice2-0 metric=container_memory_mapped_file baseline=16384.0 peak=5461.333333 signed_z=-999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:16384,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-10922.666667
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M2] rank=2 service=cartservice2-0 metric=container_memory_max_usage_MB baseline=74.176367 peak=28.571615 signed_z=-999.0 onset_bin=36 onset_rel_s=1334.531 persistence_bins=18
values_compact=delta:74.175781,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.003907,0,0,0,0,0.425781,0,0,0.09375,0.089843,0.117188,0.050781,0,0.128907,0.01302,0.154948,0.001953,0.09961,0.115234,0.216797,0.007812,0,-47.123697
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M3] rank=3 service=istio-ingressgateway-565bffd4d-4nr6v metric=istio_agent_go_memstats_frees baseline=6484.425 peak=14383.5 signed_z=703.756 onset_bin=36 onset_rel_s=1334.531 persistence_bins=8
values_compact=delta:6480,15,-11.5,-8,14.5,-14.5,11.5,10.5,-20.5,-22.5,27.5,-1,-5,-6,32,-1,-12.5,0,-1,9,2494.5,19,-2041.5,-1.5,-465,-6,-8.5,-3,5,13.5,-25,5.5,11.5,-42,-5794.5,11707.5,-11749,13766.5,-13763,11720
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M4] rank=4 service=cartservice2-0 metric=container_memory_cache baseline=233472.0 peak=77824.0 signed_z=-658.128 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:233472,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-155648
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M5] rank=5 service=cartservice2-0 metric=container_memory_failures.hierarchy.pgfault baseline=37.883333 peak=10736.0 signed_z=549.083 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:29,7,15,-23.5,10.5,-1,-2.5,10.5,69,-83,5.5,-2,-5.5,-9.666667,29.333334,-12.166667,0,-9.5,7,-21.333333,22.666666,1.666667,27.5,-39,-13.5,35.666667,-9.333334,-5.333333,-12,0,15,-8,7.5,-11,8.5,3,-1,-10,-24,10735
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M6] rank=6 service=emailservice2-0 metric=container_memory_cache baseline=26476544.0 peak=17260544.0 signed_z=-343.624 onset_bin=36 onset_rel_s=1334.531 persistence_bins=18
values_compact=delta:26476544,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-428032,-2988032,-4410026.666667,-1267029.333333,-122880,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M7] rank=7 service=node-4 metric=system.io.rkb_s baseline=0.2 peak=262.0 signed_z=300.305 onset_bin=31 onset_rel_s=1151.719 persistence_bins=6
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,4,258,-258,6,104,-114,0,6,-6,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M8] rank=8 service=cartservice2-0 metric=container_memory_failures.container.pgfault baseline=37.883333 peak=5398.166667 signed_z=275.117 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:29,7,15,-23.5,10.5,-1,-2.5,10.5,69,-83,5.5,-2,-5.5,-9.666667,29.333334,-12.166667,0,-9.5,7,-21.333333,22.666666,1.666667,27.5,-39,-13.5,35.666667,-9.333334,-5.333333,-12,0,15,-8,7.5,-11,8.5,3,-1,-10,-24,5397.166667
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M9] rank=9 service=cartservice2-0 metric=container_file_descriptors baseline=168.0 peak=64.0 signed_z=-241.401 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:168,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-104
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M10] rank=10 service=istio-ingressgateway-565bffd4d-4nr6v metric=istio_agent_process_resident_memory_bytes baseline=47555379.2 peak=48220160.0 signed_z=186.171 onset_bin=36 onset_rel_s=1334.531 persistence_bins=18
values_compact=delta:47570944,-16384,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,266240,399360,-458752,-591872,0,0,0,0,0,0,0,0,0,0,0,0,0,-229376,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M11] rank=11 service=cartservice2-0 metric=container_cpu_cfs_throttled_seconds baseline=0.001756 peak=1.039548 signed_z=135.591 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0.035118,-0.035118,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1.039548
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M12] rank=12 service=istio-ingressgateway-565bffd4d-4nr6v metric=istio_agent_go_memstats_heap_objects baseline=36899.55 peak=42700.0 signed_z=95.437 onset_bin=54 onset_rel_s=1992.656 persistence_bins=6
values_compact=delta:36869,70.5,7,-18.5,6,-71,-47.5,50.5,89,-96.5,-7,-24,14,-4.5,54.5,15.5,-10,10,71.5,99,316.5,432,-457.5,-539.5,120,21.5,-33,-72.5,-3,36.5,-136.5,0,186.5,-254.5,6006,-5835.5,5647,-7699,5664,-5823.5
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[1980.0,2340.0]

=== LOG SUMMARY ===
{"entries":[{"change_pct":-82.7,"n_during":434,"n_pre":2510,"service":"checkoutservice-0"},{"change_pct":-82.6,"n_during":10427,"n_pre":59917,"service":"frontend-0"},{"change_pct":-82.5,"n_during":76,"n_pre":434,"service":"emailservice-2"},{"change_pct":-82.5,"n_during":80,"n_pre":458,"service":"paymentservice-1"},{"change_pct":-82.3,"n_during":798,"n_pre":4502,"service":"adservice-1"},{"change_pct":-82.3,"n_during":870,"n_pre":4916,"service":"adservice-2"},{"change_pct":-82.3,"n_during":1517,"n_pre":8547,"service":"recommendationservice-1"},{"change_pct":-82.2,"n_during":802,"n_pre":4504,"service":"adservice-0"}],"mode":"volume","omitted_services":23,"service_count":31}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":55.5,"error_pct":0.0,"p95_during_ms":11.638649999999982,"p95_pre_ms":7.483449999999999,"service":"paymentservice2-0","spans":82},{"delta_pct":10.5,"error_pct":0.0,"p95_during_ms":0.021,"p95_pre_ms":0.019,"service":"adservice-0","spans":2652},{"delta_pct":-9.6,"error_pct":0.0,"p95_during_ms":0.1419,"p95_pre_ms":0.157,"service":"paymentservice-1","spans":179},{"delta_pct":-8.6,"error_pct":0.0,"p95_during_ms":40.930350000000004,"p95_pre_ms":44.77619999999995,"service":"checkoutservice2-0","spans":974},{"delta_pct":-6.0,"error_pct":0.0,"p95_during_ms":0.078,"p95_pre_ms":0.083,"service":"shippingservice2-0","spans":574},{"delta_pct":5.7,"error_pct":0.0,"p95_during_ms":0.25029999999999997,"p95_pre_ms":0.23689999999999997,"service":"emailservice-2","spans":179},{"delta_pct":5.3,"error_pct":0.0,"p95_during_ms":0.02,"p95_pre_ms":0.019,"service":"adservice-1","spans":2652},{"delta_pct":-4.5,"error_pct":0.0,"p95_during_ms":0.021,"p95_pre_ms":0.022,"service":"adservice-2","spans":2651}],"omitted_services":32,"service_count":40}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=15 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":1200.0,"rank":1,"service":"node-4","severity_z":300.305},{"evidence_source":"metric","onset_rel_s":1260.0,"rank":2,"service":"istio-egressgateway","severity_z":74.074},{"evidence_source":"metric","onset_rel_s":1260.0,"rank":3,"service":"checkoutservice2","severity_z":29.286},{"evidence_source":"metric","onset_rel_s":1320.0,"rank":4,"service":"emailservice2","severity_z":343.624},{"evidence_source":"metric","onset_rel_s":1440.0,"rank":5,"service":"cartservice","severity_z":61.306},{"evidence_source":"metric","onset_rel_s":1440.0,"rank":6,"service":"node-1","severity_z":26.439},{"evidence_source":"metric","onset_rel_s":1620.0,"rank":7,"service":"emailservice","severity_z":33.723},{"evidence_source":"metric","onset_rel_s":1740.0,"rank":8,"service":"checkoutservice","severity_z":63.137},{"evidence_source":"metric","onset_rel_s":1740.0,"rank":9,"service":"frontend2","severity_z":21.188},{"evidence_source":"metric","onset_rel_s":1920.0,"rank":10,"service":"node-2","severity_z":58.264},{"evidence_source":"metric","onset_rel_s":2040.0,"rank":11,"service":"istio-ingressgateway","severity_z":703.756},{"evidence_source":"trace","onset_rel_s":2120.4,"rank":12,"service":"cartservice2","severity_z":6.812},{"evidence_source":"trace","onset_rel_s":2266.8,"rank":13,"service":"adservice2","severity_z":17.098},{"evidence_source":"metric","onset_rel_s":2340.0,"rank":14,"service":"currencyservice2","severity_z":56.535}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"cartservice","caller":"checkoutservice"},{"callee":"emailservice","caller":"checkoutservice"},{"callee":"cartservice2","caller":"checkoutservice2"},{"callee":"currencyservice2","caller":"checkoutservice2"},{"callee":"emailservice2","caller":"checkoutservice2"},{"callee":"adservice2","caller":"frontend2"},{"callee":"cartservice2","caller":"frontend2"},{"callee":"checkoutservice2","caller":"frontend2"},{"callee":"currencyservice2","caller":"frontend2"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

## Assistant

{
"services": [
"node-4",
"cartservice2-0",
"emailservice2-0",
"istio-ingressgateway-565bffd4d-4nr6v"
],
"reason": "node-4 is the root cause because it exhibits the earliest anomaly onset (rank 1) with a massive spike in disk I/O (system.io.rkb_s), which precedes the memory exhaustion and page fault spikes observed in co-located pods like cartservice2-0 and emailservice2-0.",
"confidence": "high"
}
