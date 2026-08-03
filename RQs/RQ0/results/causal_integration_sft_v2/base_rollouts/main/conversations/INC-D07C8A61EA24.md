# Causal SFT v2 base rollout — INC-D07C8A61EA24

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

[image: RQs/RQ0/results/causal_integration_sft_v1/data/cases/INC-D07C8A61EA24/dashboard.png]

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
opaque_id: INC-D07C8A61EA24
observation_window={"duration_rel_s":2340.0,"source_metric_rows":40}
selection_summary={"candidate_count":63,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":1562,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","adservice-grpc","adservice-http","adservice2","adservice2-0","cartservice-0","cartservice-1","cartservice-2","cartservice-grpc","cartservice2-0","checkoutservice-0","checkoutservice-1","checkoutservice-2","checkoutservice-grpc","checkoutservice2-0","currencyservice-0","currencyservice-1","currencyservice-2","currencyservice-grpc","currencyservice2-0","emailservice-0","emailservice-1","emailservice-2","emailservice-grpc","emailservice2-0","frontend-0","frontend-1","frontend-2","frontend-http","frontend2-0","istio-egressgateway-7bfdcc9d86-22q7z","istio-ingressgateway-565bffd4d-4nr6v","node-1","node-2","node-3","node-4","node-5","node-6","paymentservice-0","paymentservice-1","paymentservice-2","paymentservice-grpc","paymentservice2-0","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","productcatalogservice-grpc","productcatalogservice2-0","recommendationservice-0","recommendationservice-1","recommendationservice-2","recommendationservice-grpc","recommendationservice2-0","redis-cart-0","redis-cart2-0","shippingservice-0","shippingservice-1","shippingservice-2","shippingservice-grpc","shippingservice2-0"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[18.281,54.844,91.406,127.969,164.531,201.094,237.656,274.219,310.781,347.344,383.906,420.469,457.031,493.594,530.156,566.719,603.281,639.844,676.406,712.969,749.531,786.094,822.656,859.219,895.781,932.344,968.906,1005.469,1042.031,1078.594,1115.156,1151.719,1188.281,1224.844,1261.406,1297.969,1334.531,1371.094,1407.656,1444.219,1480.781,1517.344,1553.906,1590.469,1627.031,1663.594,1700.156,1736.719,1773.281,1809.844,1846.406,1882.969,1919.531,1956.094,1992.656,2029.219,2065.781,2102.344,2138.906,2175.469,2212.031,2248.594,2285.156,2321.719]
[M1] rank=1 service=frontend-1 metric=istio_request_duration_milliseconds.http.200. baseline=548.45 peak=143556.75 signed_z=999.0 onset_bin=36 onset_rel_s=1334.531 persistence_bins=18
values_compact=delta:184.25,500,-219.75,112.75,-66.75,158.5,-127.75,11.75,26.25,-104.5,158,-187.25,-38,125.25,-22,101.5,175.75,-82.5,-146.75,-21.5,2411.75,-1699,61500,80806.75,-140823,-88.25,387.25,-60,630.5,-531.25,-537.5,415.75,-0.25,-222.75,235.5,47,-447.5,190.25,-58.25,178.25
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M2] rank=2 service=node-3 metric=system.net.udp.in_errors baseline=0.0 peak=0.23 signed_z=999.0 onset_bin=36 onset_rel_s=1334.531 persistence_bins=2
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.03,0.07,0.13,-0.16,-0.07,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M3] rank=3 service=node-5 metric=system.net.udp.in_errors baseline=0.0 peak=0.69 signed_z=999.0 onset_bin=36 onset_rel_s=1334.531 persistence_bins=2
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.16,0.39,0.14,-0.29,-0.4,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M4] rank=4 service=emailservice2-0 metric=container_network_receive_MB.eth0 baseline=0.0214 peak=0.542747 signed_z=223.826 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.023916,-0.005633,0.003899,-0.001623,0.004497,-0.002436,-0.004534,0.006599,-0.00414,-0.000314,0.001042,0.003294,-0.004626,-0.003758,0.005088,0.002318,-0.003877,0.002034,-0.001547,0.003154,-0.003436,0.002389,-0.002364,-0.001115,0.004642,-0.000982,0.52026,-0.519632,0.000498,-0.003807,0.005161,-0.003205,-0.006096,0.009941,-0.007167,0.004991,0.001768,-0.00307,-0.001533,0.000443
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M5] rank=5 service=adservice2 metric=java_lang_Threading_TotalStartedThreadCount baseline=937.995833 peak=942.0 signed_z=220.469 onset_bin=41 onset_rel_s=1517.344 persistence_bins=15
values_compact=delta:937.916667,0.083333,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1.833333,0.166667,0,0,0,0,0,0,0,0,0,0.583333,0.416667,0.25,0.75,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M6] rank=6 service=adservice2 metric=java_lang_OperatingSystem_FreePhysicalMemorySize baseline=90058905.6 peak=89933824.0 signed_z=-186.821 onset_bin=36 onset_rel_s=1334.531 persistence_bins=7
values_compact=delta:90061824,-3072,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,20480,36864,0,0,-52565.333333,-4778.666667,0,0,0,0,0,0,0,0,0,-66901.333333,-58026.666667,58368,-4096,70656
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M7] rank=7 service=paymentservice-1 metric=container_network_receive_MB.eth0 baseline=0.020328 peak=0.540441 signed_z=183.191 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.02477,-0.003944,-0.003469,0.000756,-0.000802,0.007205,-0.00558,-0.003213,0.006698,-0.000064,0.003772,-0.010635,0.002643,0.002886,0.000144,-0.000051,-0.00038,0.000374,-0.002854,0.002805,0.000962,-0.000726,-0.00219,-0.000364,0.521698,-0.515928,-0.004277,-0.007102,0.007949,0.000011,-0.001693,0.004922,-0.002708,0.000428,0.004615,-0.011913,0.00343,0.00104,0.00239,-0.001197
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M8] rank=8 service=currencyservice-0 metric=container_memory_mapped_file baseline=6267153.066667 peak=6410240.0 signed_z=154.519 onset_bin=31 onset_rel_s=1151.719 persistence_bins=21
values_compact=delta:6266880,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1365.333333,2730.666667,0,0,0,139264,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M9] rank=9 service=paymentservice2-0 metric=container_network_receive_MB.eth0 baseline=0.019076 peak=0.280314 signed_z=118.652 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.017728,0.002265,-0.001385,-0.00068,0.005849,-0.005768,-0.001143,0.005608,-0.005015,0.000795,0.000613,-0.003287,0.002114,0.007065,-0.006272,-0.000496,0.000299,0.001045,0.000769,-0.000779,0.260989,-0.00275,-0.258529,-0.000494,0.000945,-0.003515,0.005848,-0.004654,0.00409,-0.001099,-0.000857,-0.005394,0.005921,0.003566,-0.004686,-0.001458,-0.002167,0.006758,-0.001305,0.002259
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M10] rank=10 service=currencyservice-2 metric=container_memory_mapped_file baseline=446464.0 peak=491520.0 signed_z=113.656 onset_bin=36 onset_rel_s=1334.531 persistence_bins=18
values_compact=delta:446464,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,22528,22528,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M11] rank=11 service=productcatalogservice2-0 metric=container_cpu_cfs_throttled_seconds baseline=0.000386 peak=0.129677 signed_z=111.193 onset_bin=59 onset_rel_s=2175.469 persistence_bins=3
values_compact=delta:0,0,0,0,0,0,0.000083,0.003103,-0.003186,0,0,0,0,0,0,0,0,0,0,0.004457,-0.004457,0,0,0,0,0,0,0,0,0.000967,0,-0.000967,0,0.003701,0,-0.003701,0.079057,-0.013721,0.064341,-0.129677
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M12] rank=12 service=adservice2 metric=java_lang_Threading_ThreadCount baseline=16.995833 peak=15.0 signed_z=-109.89 onset_bin=36 onset_rel_s=1334.531 persistence_bins=7
values_compact=delta:16.916667,0.083333,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-0.666667,-1.333333,0,0,1.833333,0.166667,0,0,0,0,0,0,0,0,0,0.583333,0.166667,-0.5,0.5,-0.75
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[1200.0,1440.0]

=== LOG SUMMARY ===
{"entries":[{"error_logs":14,"error_pct":0.07,"service":"frontend-0","total_logs":18720},{"error_logs":14,"error_pct":0.06,"service":"frontend-2","total_logs":22300},{"error_logs":10,"error_pct":0.07,"service":"productcatalogservice-0","total_logs":14875},{"error_logs":7,"error_pct":0.06,"service":"currencyservice-0","total_logs":11023},{"error_logs":6,"error_pct":0.05,"service":"currencyservice-1","total_logs":11072},{"error_logs":5,"error_pct":0.02,"service":"frontend-1","total_logs":20568},{"error_logs":4,"error_pct":0.04,"service":"currencyservice-2","total_logs":11053}],"mode":"errors","omitted_services":24,"service_count":31}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":128207.4,"error_pct":0.0,"p95_during_ms":59999.480599999995,"p95_pre_ms":46.762299999999996,"service":"frontend2-0","spans":7236},{"delta_pct":120887.3,"error_pct":0.0,"p95_during_ms":60000.0301,"p95_pre_ms":49.59199999999999,"service":"frontend-0","spans":13306},{"delta_pct":120109.7,"error_pct":0.0,"p95_during_ms":59999.7927,"p95_pre_ms":49.91259999999998,"service":"frontend-2","spans":15868},{"delta_pct":78.5,"error_pct":0.0,"p95_during_ms":0.15794999999999995,"p95_pre_ms":0.0885,"service":"shippingservice-0","spans":375},{"delta_pct":-59.7,"error_pct":0.0,"p95_during_ms":16.35444999999999,"p95_pre_ms":40.5954,"service":"checkoutservice-2","spans":622},{"delta_pct":-55.1,"error_pct":0.0,"p95_during_ms":18.75254999999999,"p95_pre_ms":41.742699999999985,"service":"checkoutservice2-0","spans":312},{"delta_pct":-47.7,"error_pct":0.0,"p95_during_ms":99.33759999999997,"p95_pre_ms":190.05275,"service":"checkoutservice-0","spans":628},{"delta_pct":-43.5,"error_pct":0.0,"p95_during_ms":23.089649999999978,"p95_pre_ms":40.8619,"service":"checkoutservice-1","spans":632}],"omitted_services":32,"service_count":40}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=14 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":1200.0,"rank":1,"service":"paymentservice2","severity_z":118.652},{"evidence_source":"trace","onset_rel_s":1243.2,"rank":2,"service":"frontend","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1260.0,"rank":3,"service":"node-5","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1320.0,"rank":4,"service":"node-3","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1320.0,"rank":5,"service":"shippingservice","severity_z":71.529},{"evidence_source":"metric","onset_rel_s":1320.0,"rank":6,"service":"cartservice","severity_z":61.994},{"evidence_source":"metric","onset_rel_s":1380.0,"rank":7,"service":"currencyservice","severity_z":154.519},{"evidence_source":"metric","onset_rel_s":1440.0,"rank":8,"service":"paymentservice","severity_z":183.191},{"evidence_source":"metric","onset_rel_s":1500.0,"rank":9,"service":"adservice2","severity_z":220.469},{"evidence_source":"metric","onset_rel_s":1560.0,"rank":10,"service":"emailservice2","severity_z":223.826},{"evidence_source":"metric","onset_rel_s":1560.0,"rank":11,"service":"redis-cart","severity_z":55.816},{"evidence_source":"trace","onset_rel_s":1633.2,"rank":12,"service":"currencyservice2","severity_z":9.562},{"evidence_source":"metric","onset_rel_s":1680.0,"rank":13,"service":"checkoutservice","severity_z":47.851},{"evidence_source":"metric","onset_rel_s":2160.0,"rank":14,"service":"productcatalogservice2","severity_z":111.193}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"cartservice","caller":"checkoutservice"},{"callee":"currencyservice","caller":"checkoutservice"},{"callee":"paymentservice","caller":"checkoutservice"},{"callee":"shippingservice","caller":"checkoutservice"},{"callee":"cartservice","caller":"frontend"},{"callee":"checkoutservice","caller":"frontend"},{"callee":"currencyservice","caller":"frontend"},{"callee":"shippingservice","caller":"frontend"}]

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
"node-3",
"paymentservice2",
"frontend",
"adservice2"
],
"reason": "The simultaneous onset of critical system-level UDP errors on node-5 and node-3 at the start of the fault window indicates a network infrastructure failure that propagated to co-located services like paymentservice2 and frontend.",
"confidence": "high"
}
