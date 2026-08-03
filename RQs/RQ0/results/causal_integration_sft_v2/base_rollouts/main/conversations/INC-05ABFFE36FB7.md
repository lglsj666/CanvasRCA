# Causal SFT v2 base rollout — INC-05ABFFE36FB7

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

[image: RQs/RQ0/results/causal_integration_sft_v1/data/cases/INC-05ABFFE36FB7/dashboard.png]

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
opaque_id: INC-05ABFFE36FB7
observation_window={"duration_rel_s":2340.0,"source_metric_rows":40}
selection_summary={"candidate_count":63,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":1428,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","adservice-grpc","adservice-http","adservice2","adservice2-0","cartservice-0","cartservice-1","cartservice-2","cartservice-grpc","cartservice2-0","checkoutservice-0","checkoutservice-1","checkoutservice-2","checkoutservice-grpc","checkoutservice2-0","currencyservice-0","currencyservice-1","currencyservice-2","currencyservice-grpc","currencyservice2-0","emailservice-0","emailservice-1","emailservice-2","emailservice-grpc","emailservice2-0","frontend-0","frontend-1","frontend-2","frontend-http","frontend2-0","istio-egressgateway-7bfdcc9d86-22q7z","istio-ingressgateway-565bffd4d-4nr6v","node-1","node-2","node-3","node-4","node-5","node-6","paymentservice-0","paymentservice-1","paymentservice-2","paymentservice-grpc","paymentservice2-0","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","productcatalogservice-grpc","productcatalogservice2-0","recommendationservice-0","recommendationservice-1","recommendationservice-2","recommendationservice-grpc","recommendationservice2-0","redis-cart-0","redis-cart2-0","shippingservice-0","shippingservice-1","shippingservice-2","shippingservice-grpc","shippingservice2-0"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[18.281,54.844,91.406,127.969,164.531,201.094,237.656,274.219,310.781,347.344,383.906,420.469,457.031,493.594,530.156,566.719,603.281,639.844,676.406,712.969,749.531,786.094,822.656,859.219,895.781,932.344,968.906,1005.469,1042.031,1078.594,1115.156,1151.719,1188.281,1224.844,1261.406,1297.969,1334.531,1371.094,1407.656,1444.219,1480.781,1517.344,1553.906,1590.469,1627.031,1663.594,1700.156,1736.719,1773.281,1809.844,1846.406,1882.969,1919.531,1956.094,1992.656,2029.219,2065.781,2102.344,2138.906,2175.469,2212.031,2248.594,2285.156,2321.719]
[M1] rank=1 service=adservice2 metric=java_lang_Memory_ObjectPendingFinalizationCount baseline=0.0 peak=0.083333 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.083333,-0.083333,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M2] rank=2 service=adservice2 metric=jvm_threads_started baseline=0.0 peak=0.75 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.25,0.5,-0.75,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M3] rank=3 service=istio-ingressgateway-565bffd4d-4nr6v metric=istio_agent_go_gc_duration_seconds.0.0 baseline=4.2e-05 peak=4.2e-05 signed_z=999.0 onset_bin=0 onset_rel_s=18.281 persistence_bins=40
values_compact=delta:0.000042,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M4] rank=4 service=node-6 metric=system.io.avg_q_sz baseline=0.0025 peak=63.59 signed_z=999.0 onset_bin=36 onset_rel_s=1334.531 persistence_bins=4
values_compact=delta:0,0,0,0,0,0,0,0.01,-0.01,0,0.01,0.01,-0.02,0,0,0.01,-0.01,0,0,0,61.96,1.55,-1.52,-0.11,1.71,-63.59,0.01,0.04,-0.05,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M5] rank=5 service=node-6 metric=system.disk.pct_usage baseline=52.8395 peak=57.07 signed_z=717.653 onset_bin=36 onset_rel_s=1334.531 persistence_bins=18
values_compact=delta:52.83,0,0,0.01,-0.01,0.01,0,0,0,0,0,0,0,0,0,0,0,0.01,0,0,0.88,0.83,0.84,0.84,0.83,-4.21,0,0,0,0,0,0,0.01,-0.01,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M6] rank=6 service=node-6 metric=system.io.w_await baseline=0.3965 peak=127.93 signed_z=327.017 onset_bin=36 onset_rel_s=1334.531 persistence_bins=3
values_compact=delta:0,0,0,0,0.6,-0.6,0,0.58,-0.58,0.5,1,-0.79,-0.21,0.19,0.03,-0.09,-0.02,-0.36,0.39,-0.64,43.44,84.49,-90.44,9.13,72.82,-119.01,0.07,0.4,-0.9,0,0.55,-0.55,0.58,-0.58,0,0.64,-0.64,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M7] rank=7 service=node-6 metric=system.io.await baseline=0.3965 peak=127.43 signed_z=325.735 onset_bin=36 onset_rel_s=1334.531 persistence_bins=3
values_compact=delta:0,0,0,0,0.6,-0.6,0,0.58,-0.58,0.5,1,-0.79,-0.21,0.19,0.03,-0.09,-0.02,-0.36,0.39,-0.64,43.44,83.99,-89.94,9.02,72.35,-118.43,0.07,0.4,-0.9,0.5,0.05,-0.55,0.58,-0.58,0,0.63,-0.63,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M8] rank=8 service=node-6 metric=system.io.util baseline=0.1225 peak=50.0 signed_z=317.886 onset_bin=36 onset_rel_s=1334.531 persistence_bins=3
values_compact=delta:0,0,0,0,0.15,-0.15,0,0.1,-0.1,0.1,0.5,-0.45,-0.1,0.25,0.1,-0.3,0.1,-0.15,0.2,-0.25,50,0,0,0,0,-49.85,-0.1,0.2,-0.25,0.05,0.15,-0.2,0.15,-0.15,0,0.2,-0.2,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M9] rank=9 service=frontend2-0 metric=container_memory_mapped_file baseline=12288.0 peak=16384.0 signed_z=245.926 onset_bin=59 onset_rel_s=2175.469 persistence_bins=4
values_compact=delta:12288,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,4096,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M10] rank=10 service=node-6 metric=system.io.w_s baseline=3.1 peak=827.0 signed_z=212.271 onset_bin=36 onset_rel_s=1334.531 persistence_bins=4
values_compact=delta:0,0,0,0,2.5,-2.5,0,9,-9,3.5,-0.5,10,-11.5,2.5,0.5,7.5,-7.5,-3.5,2.5,-3.5,780.5,-528,574.5,-146.5,-433.5,-243.5,6.5,13.5,-22.5,-1,5.5,-5.5,3,-3,0.5,3,-3.5,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M11] rank=11 service=paymentservice2-0 metric=container_network_receive_MB.eth0 baseline=0.018963 peak=0.295808 signed_z=153.655 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.019683,-0.002573,0.002722,-0.000783,-0.000874,0.002298,-0.000584,-0.004454,0.003359,0.005048,-0.005224,0.002618,-0.003557,0.000163,-0.000678,0,0.003228,-0.00058,-0.000193,-0.002175,0.002305,0.000825,-0.0021,0.00033,-0.004572,0.00595,0.275626,-0.007538,-0.265346,-0.002914,0.001794,-0.002186,-0.002521,0.003756,-0.003641,0.003219,-0.003151,0.002895,-0.000528,-0.003148
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M12] rank=12 service=paymentservice-0 metric=container_network_receive_MB.eth0 baseline=0.020736 peak=0.284657 signed_z=138.683 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.021966,-0.001669,0.000632,-0.001307,0.002053,-0.000223,0.000555,0.000667,-0.002217,0.001423,0.002904,-0.004451,-0.004456,0.000797,0.004139,0,0.000916,-0.002878,0.002108,-0.000041,-0.000541,0.005404,-0.000745,-0.009426,0.263303,0.005744,-0.265582,0.003392,-0.000737,0.005567,-0.001948,-0.011127,0.004938,0.006015,-0.005817,0.002123,-0.001697,-0.002334,0.009194,-0.007463
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[1140.0,2340.0]

=== LOG SUMMARY ===
{"entries":[{"change_pct":200.0,"n_during":2,"n_pre":0,"service":"frontend-0"},{"change_pct":20.0,"n_during":12,"n_pre":10,"service":"redis-cart-0"},{"change_pct":-18.8,"n_during":65,"n_pre":80,"service":"paymentservice-2"},{"change_pct":16.7,"n_during":77,"n_pre":66,"service":"paymentservice-0"},{"change_pct":-6.7,"n_during":70,"n_pre":75,"service":"emailservice-0"},{"change_pct":-6.3,"n_during":384,"n_pre":410,"service":"checkoutservice-1"},{"change_pct":-5.5,"n_during":69,"n_pre":73,"service":"emailservice-1"},{"change_pct":4.2,"n_during":398,"n_pre":382,"service":"checkoutservice-2"}],"mode":"volume","omitted_services":23,"service_count":31}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":-15.7,"error_pct":0.0,"p95_during_ms":0.13885,"p95_pre_ms":0.1648,"service":"paymentservice-1","spans":48},{"delta_pct":13.3,"error_pct":0.0,"p95_during_ms":0.09734999999999994,"p95_pre_ms":0.0859,"service":"shippingservice-0","spans":327},{"delta_pct":10.5,"error_pct":0.0,"p95_during_ms":0.086,"p95_pre_ms":0.07784999999999999,"service":"shippingservice2-0","spans":433},{"delta_pct":9.8,"error_pct":0.0,"p95_during_ms":0.15039999999999998,"p95_pre_ms":0.137,"service":"paymentservice-0","spans":47},{"delta_pct":9.7,"error_pct":0.0,"p95_during_ms":0.1755,"p95_pre_ms":0.16,"service":"paymentservice2-0","spans":62},{"delta_pct":-8.7,"error_pct":0.0,"p95_during_ms":0.021,"p95_pre_ms":0.023,"service":"adservice-2","spans":698},{"delta_pct":-7.4,"error_pct":0.0,"p95_during_ms":0.018849999999999964,"p95_pre_ms":0.020349999999999965,"service":"adservice-0","spans":698},{"delta_pct":-5.0,"error_pct":0.0,"p95_during_ms":0.019,"p95_pre_ms":0.02,"service":"adservice-1","spans":698}],"omitted_services":31,"service_count":39}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=16 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":1200.0,"rank":1,"service":"istio-ingressgateway","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1200.0,"rank":2,"service":"node-6","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1260.0,"rank":3,"service":"frontend","severity_z":62.326},{"evidence_source":"metric","onset_rel_s":1440.0,"rank":4,"service":"paymentservice","severity_z":138.683},{"evidence_source":"metric","onset_rel_s":1440.0,"rank":5,"service":"emailservice2","severity_z":85.561},{"evidence_source":"metric","onset_rel_s":1500.0,"rank":6,"service":"checkoutservice","severity_z":133.674},{"evidence_source":"metric","onset_rel_s":1560.0,"rank":7,"service":"paymentservice2","severity_z":153.655},{"evidence_source":"metric","onset_rel_s":1560.0,"rank":8,"service":"adservice","severity_z":97.973},{"evidence_source":"trace","onset_rel_s":1584.6,"rank":9,"service":"shippingservice","severity_z":13.087},{"evidence_source":"metric","onset_rel_s":1620.0,"rank":10,"service":"cartservice","severity_z":63.131},{"evidence_source":"metric","onset_rel_s":1680.0,"rank":11,"service":"checkoutservice2","severity_z":86.798},{"evidence_source":"metric","onset_rel_s":2160.0,"rank":12,"service":"frontend2","severity_z":245.926},{"evidence_source":"metric","onset_rel_s":2220.0,"rank":13,"service":"adservice2","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":2220.0,"rank":14,"service":"node-5","severity_z":56.481}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"cartservice","caller":"checkoutservice"},{"callee":"paymentservice","caller":"checkoutservice"},{"callee":"shippingservice","caller":"checkoutservice"},{"callee":"emailservice2","caller":"checkoutservice2"},{"callee":"paymentservice2","caller":"checkoutservice2"},{"callee":"adservice","caller":"frontend"},{"callee":"cartservice","caller":"frontend"},{"callee":"checkoutservice","caller":"frontend"},{"callee":"shippingservice","caller":"frontend"},{"callee":"adservice2","caller":"frontend2"},{"callee":"checkoutservice2","caller":"frontend2"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

## Assistant

{
"services": [
"node-6",
"istio-ingressgateway-565bffd4d-4nr6v",
"frontend-0",
"paymentservice-0",
"paymentservice2-0"
],
"reason": "Node-6 is the root cause, evidenced by simultaneous, extreme spikes in system-level disk I/O metrics (avg_q_sz, w_await, util) starting at t=1334s, which precedes the degradation of co-located services like the ingress gateway and frontend.",
"confidence": "high"
}
