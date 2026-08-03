# Causal SFT v2 base rollout — INC-C4FE1AA9F04D

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

[image: RQs/RQ0/results/causal_integration_sft_v1/data/cases/INC-C4FE1AA9F04D/dashboard.png]

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
opaque_id: INC-C4FE1AA9F04D
observation_window={"duration_rel_s":2340.0,"source_metric_rows":40}
selection_summary={"candidate_count":63,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":1455,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","adservice-grpc","adservice-http","adservice2","adservice2-0","cartservice-0","cartservice-1","cartservice-2","cartservice-grpc","cartservice2-0","checkoutservice-0","checkoutservice-1","checkoutservice-2","checkoutservice-grpc","checkoutservice2-0","currencyservice-0","currencyservice-1","currencyservice-2","currencyservice-grpc","currencyservice2-0","emailservice-0","emailservice-1","emailservice-2","emailservice-grpc","emailservice2-0","frontend-0","frontend-1","frontend-2","frontend-http","frontend2-0","istio-egressgateway-7bfdcc9d86-zpjpg","istio-ingressgateway-565bffd4d-6bl7m","node-1","node-2","node-3","node-4","node-5","node-6","paymentservice-0","paymentservice-1","paymentservice-2","paymentservice-grpc","paymentservice2-0","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","productcatalogservice-grpc","productcatalogservice2-0","recommendationservice-0","recommendationservice-1","recommendationservice-2","recommendationservice-grpc","recommendationservice2-0","redis-cart-0","redis-cart2-0","shippingservice-0","shippingservice-1","shippingservice-2","shippingservice-grpc","shippingservice2-0"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[18.281,54.844,91.406,127.969,164.531,201.094,237.656,274.219,310.781,347.344,383.906,420.469,457.031,493.594,530.156,566.719,603.281,639.844,676.406,712.969,749.531,786.094,822.656,859.219,895.781,932.344,968.906,1005.469,1042.031,1078.594,1115.156,1151.719,1188.281,1224.844,1261.406,1297.969,1334.531,1371.094,1407.656,1444.219,1480.781,1517.344,1553.906,1590.469,1627.031,1663.594,1700.156,1736.719,1773.281,1809.844,1846.406,1882.969,1919.531,1956.094,1992.656,2029.219,2065.781,2102.344,2138.906,2175.469,2212.031,2248.594,2285.156,2321.719]
[M1] rank=1 service=cartservice-1 metric=istio_request_duration_milliseconds.grpc.200.0.0 baseline=54.4925 peak=29325.0 signed_z=999.0 onset_bin=49 onset_rel_s=1809.844 persistence_bins=7
values_compact=delta:55.8125,-4.825,-0.075,-0.525,1.9875,1.6625,-2.8875,20.6,0,-15.8625,-1.8375,-1.9375,1.3875,-0.3125,-3.8625,3.175,3.3125,-3.05,-1.3125,-1.35,-0.8875,3.775,0.275,0.2375,0.55,-3.425,3.375,1.5625,0.3125,1461.05,22099.7625,4992.0625,148.75,567.5,-1432.5,463.0875,-22242.425,-6059.6375,-3.4125,2.075
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M2] rank=2 service=adservice2 metric=java_lang_GarbageCollector_LastGcInfo_memoryUsageAfterGc_used.Tenured_Gen.Copy baseline=52056656.733333 peak=52259304.0 signed_z=976.948 onset_bin=31 onset_rel_s=1151.719 persistence_bins=21
values_compact=delta:52056560,0,0,0,0,0,0,58.666667,5.333333,0,0,0,0,0,0,0,0,0,208,692,324,0,42.666667,21.333333,10.666667,53.333333,0,0,0,0,0,0,0,0,37.333333,100,14.666667,0,0,201176
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M3] rank=3 service=adservice2 metric=jvm_memory_pool_MB_used.Tenured_Gen baseline=49.6451 peak=49.838356 signed_z=923.822 onset_bin=31 onset_rel_s=1151.719 persistence_bins=21
values_compact=delta:49.645004,0,0,0,0,0,0,0.000061,0,0,0,0,0,0,0,0,0,0,0.000214,0.000696,0.000258,0,0.000045,0.000016,0.000015,0.000046,0,0,0,0,0,0,0,0,0.00004,0.000098,0.000007,0,0,0.191856
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M4] rank=4 service=adservice2 metric=jvm_memory_pool_allocated_MB_total.Tenured_Gen baseline=108.294212 peak=108.471485 signed_z=901.517 onset_bin=31 onset_rel_s=1151.719 persistence_bins=21
values_compact=delta:108.294121,0,0,0,0,0,0,0.000056,0.000005,0,0,0,0,0,0,0,0,0,0.000168,0.00069,0.000309,0,0.000041,0.00002,0.00001,0.000051,0,0,0,0,0,0,0,0,0.000036,0.000095,0.000014,0,0,0.175869
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M5] rank=5 service=adservice2 metric=java_lang_MemoryPool_Usage_used.Tenured_Gen baseline=52056656.733333 peak=52242539.333333 signed_z=896.127 onset_bin=31 onset_rel_s=1151.719 persistence_bins=21
values_compact=delta:52056560,0,0,0,0,0,0,58.666667,5.333333,0,0,0,0,0,0,0,0,0,208,692,324,0,42.666667,21.333333,10.666667,53.333333,0,0,0,0,0,0,0,0,37.333333,100,14.666667,0,0,184411.333333
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M6] rank=6 service=adservice2 metric=java_lang_GarbageCollector_LastGcInfo_memoryUsageBeforeGc_used.Tenured_Gen.Copy baseline=52056633.666667 peak=52175480.666667 signed_z=825.826 onset_bin=31 onset_rel_s=1151.719 persistence_bins=21
values_compact=delta:52056560,0,0,0,0,0,0,37.333333,26.666667,0,0,0,0,0,0,0,0,0,48,572,604,0,21.333333,42.666667,0,53.333333,10.666667,0,0,0,0,0,0,0,16,92,44,0,0,117352.666667
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M7] rank=7 service=paymentservice2-0 metric=container_network_receive_MB.eth0 baseline=0.022436 peak=0.598527 signed_z=345.737 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.022984,0.000475,-0.001151,0.001064,-0.00085,-0.003593,0.006147,-0.003248,0.000081,0.000744,-0.001955,0.004107,-0.003342,0.000744,0.002895,-0.003444,-0.002632,0.004371,0.000555,-0.002575,0.002988,-0.000479,-0.001899,-0.000135,-0.000771,0.001588,0.000596,-0.005163,0.005583,-0.002633,0.004445,0.57303,-0.575353,-0.001141,-0.002604,0.00593,-0.003894,0.000544,0.001663,-0.002727
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M8] rank=8 service=shippingservice2-0 metric=istio_request_duration_milliseconds.grpc.200.0.0 baseline=0.18375 peak=58.2875 signed_z=309.949 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.525,-0.525,0,0,0,0,0.525,-0.525,0.2625,0,0,0,0.2625,-0.525,0,0,0.2625,0,0,0,0,1.025,-1.025,58.025,-58.025,0,0,0,-0.2625,0,0.2625,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M9] rank=9 service=paymentservice-1 metric=container_network_receive_MB.eth0 baseline=0.023141 peak=0.604707 signed_z=307.847 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.024933,-0.001467,-0.002529,0.001678,-0.00032,0.000472,0.000899,-0.001124,0.000393,0.000983,-0.001271,0.000706,-0.000906,-0.000288,0.00735,-0.006619,-0.00101,-0.00227,0.005622,-0.002214,-0.001881,0.003449,-0.000487,-0.003538,0.584146,-0.583968,0.004183,-0.002734,-0.00057,0.000579,0.001873,0.000029,-0.004234,0.003667,-0.000694,0.000424,-0.002889,0.006402,-0.005333,0.003118
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M10] rank=10 service=paymentservice-2 metric=container_network_receive_MB.eth0 baseline=0.023933 peak=0.602537 signed_z=281.025 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.023947,0.003454,-0.006346,0.003093,-0.000052,-0.00039,0.001292,-0.003833,0.006468,-0.007488,0.004244,-0.001525,0.000976,0.002902,-0.004272,0.002709,-0.000034,-0.004216,0.004822,-0.002698,-0.001407,0.005025,-0.004517,0.002816,0.577567,-0.577022,0.000459,-0.003008,0.000438,0.000601,0.00011,-0.002047,0.000222,0.004462,-0.004819,0.001699,-0.001141,0.002552,0.00034,-0.003463
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M11] rank=11 service=shippingservice-0 metric=container_memory_rss baseline=9993216.0 peak=17774592.0 signed_z=249.047 onset_bin=31 onset_rel_s=1151.719 persistence_bins=4
values_compact=delta:9986048,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,143360,143360,0,7501824,-7747584,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M12] rank=12 service=node-4 metric=system.net.tcp.retrans_segs baseline=0.004 peak=1.7 signed_z=212.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0.02,0,-0.02,0,0,0,0,0.02,-0.02,0,0,0,0.02,-0.02,0,0,0,0,1.7,-1.7,0,0,0,0.02,-0.02,0,0,0,0.02,-0.02,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[1740.0,2160.0]

=== LOG SUMMARY ===
{"entries":[{"error_logs":1,"error_pct":0.0,"service":"cartservice-0","total_logs":38941}],"mode":"errors","omitted_services":30,"service_count":31}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":2584.8,"error_pct":0.0,"p95_during_ms":1160.29835,"p95_pre_ms":43.21745,"service":"checkoutservice-0","spans":1928},{"delta_pct":2538.3,"error_pct":0.0,"p95_during_ms":1161.0235500000001,"p95_pre_ms":44.00595,"service":"checkoutservice-1","spans":1934},{"delta_pct":2454.4,"error_pct":0.0,"p95_during_ms":1161.04845,"p95_pre_ms":45.45314999999997,"service":"checkoutservice-2","spans":1904},{"delta_pct":126.8,"error_pct":0.0,"p95_during_ms":123.59049999999999,"p95_pre_ms":54.499,"service":"frontend-0","spans":66647},{"delta_pct":-100.0,"error_pct":0.0,"p95_during_ms":0.0,"p95_pre_ms":1.0,"service":"cartservice-0","spans":8058},{"delta_pct":56.9,"error_pct":0.0,"p95_during_ms":87.90499999999894,"p95_pre_ms":56.02059999999998,"service":"frontend-2","spans":61629},{"delta_pct":19.4,"error_pct":0.0,"p95_during_ms":66.95164999999996,"p95_pre_ms":56.085100000000004,"service":"frontend-1","spans":5475},{"delta_pct":-15.2,"error_pct":0.0,"p95_during_ms":0.0195,"p95_pre_ms":0.023,"service":"adservice-2","spans":2426}],"omitted_services":32,"service_count":40}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=16 omitted_edges=1
[{"evidence_source":"metric","onset_rel_s":1260.0,"rank":1,"service":"checkoutservice2","severity_z":117.273},{"evidence_source":"metric","onset_rel_s":1320.0,"rank":2,"service":"shippingservice","severity_z":249.047},{"evidence_source":"metric","onset_rel_s":1320.0,"rank":3,"service":"node-1","severity_z":69.07},{"evidence_source":"metric","onset_rel_s":1380.0,"rank":4,"service":"shippingservice2","severity_z":309.949},{"evidence_source":"metric","onset_rel_s":1380.0,"rank":5,"service":"node-4","severity_z":212.0},{"evidence_source":"metric","onset_rel_s":1380.0,"rank":6,"service":"adservice","severity_z":73.479},{"evidence_source":"metric","onset_rel_s":1440.0,"rank":7,"service":"paymentservice","severity_z":307.847},{"evidence_source":"metric","onset_rel_s":1440.0,"rank":8,"service":"emailservice","severity_z":132.634},{"evidence_source":"trace","onset_rel_s":1779.6,"rank":9,"service":"cartservice","severity_z":26.041},{"evidence_source":"trace","onset_rel_s":1779.6,"rank":10,"service":"checkoutservice","severity_z":262.267},{"evidence_source":"trace","onset_rel_s":1828.2,"rank":11,"service":"frontend","severity_z":200.066},{"evidence_source":"metric","onset_rel_s":1860.0,"rank":12,"service":"paymentservice2","severity_z":345.737},{"evidence_source":"metric","onset_rel_s":1920.0,"rank":13,"service":"currencyservice","severity_z":60.156},{"evidence_source":"metric","onset_rel_s":2340.0,"rank":14,"service":"adservice2","severity_z":976.948}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"cartservice","caller":"checkoutservice"},{"callee":"currencyservice","caller":"checkoutservice"},{"callee":"emailservice","caller":"checkoutservice"},{"callee":"paymentservice","caller":"checkoutservice"},{"callee":"shippingservice","caller":"checkoutservice"},{"callee":"paymentservice2","caller":"checkoutservice2"},{"callee":"shippingservice2","caller":"checkoutservice2"},{"callee":"adservice","caller":"frontend"},{"callee":"cartservice","caller":"frontend"},{"callee":"checkoutservice","caller":"frontend"},{"callee":"currencyservice","caller":"frontend"},{"callee":"shippingservice","caller":"frontend"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

## Assistant

{
"services": [
"adservice2",
"shippingservice-0",
"node-4",
"checkoutservice2",
"paymentservice2-0"
],
"reason": "adservice2 is the root cause, evidenced by the earliest onset of severe JVM memory anomalies (z=976) at t=1151s, which precedes the degradation of downstream services like checkoutservice2 and shippingservice2.",
"confidence": "high"
}
