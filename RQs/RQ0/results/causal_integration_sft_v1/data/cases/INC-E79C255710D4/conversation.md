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
opaque_id: INC-E79C255710D4
observation_window={"duration_rel_s":2340.0,"source_metric_rows":40}
selection_summary={"candidate_count":63,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":1404,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","adservice-grpc","adservice-http","adservice2","adservice2-0","cartservice-0","cartservice-1","cartservice-2","cartservice-grpc","cartservice2-0","checkoutservice-0","checkoutservice-1","checkoutservice-2","checkoutservice-grpc","checkoutservice2-0","currencyservice-0","currencyservice-1","currencyservice-2","currencyservice-grpc","currencyservice2-0","emailservice-0","emailservice-1","emailservice-2","emailservice-grpc","emailservice2-0","frontend-0","frontend-1","frontend-2","frontend-http","frontend2-0","istio-egressgateway-7bfdcc9d86-22q7z","istio-ingressgateway-565bffd4d-4nr6v","node-1","node-2","node-3","node-4","node-5","node-6","paymentservice-0","paymentservice-1","paymentservice-2","paymentservice-grpc","paymentservice2-0","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","productcatalogservice-grpc","productcatalogservice2-0","recommendationservice-0","recommendationservice-1","recommendationservice-2","recommendationservice-grpc","recommendationservice2-0","redis-cart-0","redis-cart2-0","shippingservice-0","shippingservice-1","shippingservice-2","shippingservice-grpc","shippingservice2-0"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[18.281,54.844,91.406,127.969,164.531,201.094,237.656,274.219,310.781,347.344,383.906,420.469,457.031,493.594,530.156,566.719,603.281,639.844,676.406,712.969,749.531,786.094,822.656,859.219,895.781,932.344,968.906,1005.469,1042.031,1078.594,1115.156,1151.719,1188.281,1224.844,1261.406,1297.969,1334.531,1371.094,1407.656,1444.219,1480.781,1517.344,1553.906,1590.469,1627.031,1663.594,1700.156,1736.719,1773.281,1809.844,1846.406,1882.969,1919.531,1956.094,1992.656,2029.219,2065.781,2102.344,2138.906,2175.469,2212.031,2248.594,2285.156,2321.719]
[M1] rank=1 service=cartservice-1 metric=container_cpu_cfs_throttled_seconds baseline=0.0 peak=0.031297 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.031297,-0.031297,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M2] rank=2 service=node-4 metric=system.net.bytes_rcvd baseline=444609.8 peak=2687144.0 signed_z=703.485 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:434859.45,11390.9,-1186.6,-336.7,-4296.15,4596.55,3954.6,-3948.9,202.1,-127,2802.5,-6474.25,5208.3,960.65,-4464,3973.05,-5372.35,3924.4,-3327.35,5537.8,2558.05,-7009.55,-1203.95,1088.95,-2366,-1868.15,6596.65,3195.55,-5894.05,221.25,3605.3,-2420.2,-7542.95,10128.55,1573.8,-5575.05,3132.8,-7808.9,-625.8,2249480.7
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M3] rank=3 service=istio-ingressgateway-565bffd4d-4nr6v metric=istio_agent_go_gc_duration_seconds baseline=3.2e-05 peak=0.009126 signed_z=292.145 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.000023,-0.000001,0,0.000018,0,-0.000002,0,0.000006,0,-0.000044,0.00014,-0.00014,0.000046,-0.000046,0.000044,-0.000044,0.000046,-0.000046,0.000046,-0.000046,0.000079,-0.000079,0.000083,-0.000083,0.000045,-0.000045,0.000079,-0.000079,0.000073,-0.000073,0.000074,-0.000074,0.000044,-0.000044,0.009126,-0.009126,0.000057,-0.000057,0.00008,-0.00008
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M4] rank=4 service=adservice-2 metric=istio_request_duration_milliseconds.http.200. baseline=102.66125 peak=562.9 signed_z=263.137 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:102.5,1.45,-1.225,-0.95,-1.225,0.225,0.275,0.725,-0.5,1.95,-2.45,-0.225,3.9,0.5,-1.725,-1.45,0.95,1.05,-0.05,3.95,-6.9,4.95,-2.5,3.45,-0.225,0.95,-4.675,-2.175,2.45,-1.225,-1.95,2.675,0,0.5,0.95,-1.675,460.625,-458.9,-0.5,0.55
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M5] rank=5 service=paymentservice-2 metric=container_network_receive_MB.eth0 baseline=0.019422 peak=0.370497 signed_z=183.561 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.021191,0.001668,-0.006869,0.004752,-0.003127,0.001021,-0.000545,0.002483,-0.00279,0.000065,0.005919,-0.001746,-0.002,-0.002049,0.002075,-0.002037,0.00097,0.000192,-0.001019,0.000813,-0.003387,0.174232,0.180685,-0.351643,0.000445,-0.000132,-0.002207,0.006341,-0.005591,0.001241,-0.000097,-0.000113,-0.002752,0.005418,-0.002982,-0.000978,0.000965,0.000957,0.000392,-0.001294
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M6] rank=6 service=cartservice-1 metric=container_memory_failures.container.pgfault baseline=15.25 peak=685.5 signed_z=181.257 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:16,-3.5,1.5,2,-2,4.5,-3.5,-2,4,-8.5,12.5,-7,3.5,-8,14.5,-7,-5.5,2.833333,5.333334,-7.666667,3,1,5.5,664,-673,-1.5,2.5,1.5,-1.5,7,-9.5,10,-9,-4,3.5,6,-3,3,5.5,-11
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M7] rank=7 service=cartservice-1 metric=container_memory_failures.hierarchy.pgfault baseline=15.25 peak=685.5 signed_z=181.257 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:16,-3.5,1.5,2,-2,4.5,-3.5,-2,4,-8.5,12.5,-7,3.5,-8,14.5,-7,-5.5,2.833333,5.333334,-7.666667,3,1,5.5,664,-673,-1.5,2.5,1.5,-1.5,7,-9.5,10,-9,-4,3.5,6,-3,3,5.5,-11
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M8] rank=8 service=node-4 metric=system.net.packets_out.count baseline=242.303 peak=940.29 signed_z=173.61 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:235.98,10.09,-2.06,-1.84,-7.54,9.04,-1.5,1.23,-2.65,-2.45,9.28,-8.86,1.46,4.75,-5.23,9.59,-10.58,3.83,0.37,7.44,-3.85,-4.39,0.46,4.25,-10.28,1.8,5.29,3.65,-7.09,3.14,2.5,-0.84,-8.76,7.96,-0.63,-2.77,3,0.68,-8.6,704.42
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M9] rank=9 service=node-4 metric=system.net.packets_in.count baseline=255.3755 peak=960.72 signed_z=163.882 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:248.07,10.23,-0.8,-3.9,-6.41,8.66,0.67,-0.61,-1.96,-1.88,9.39,-9.69,2.6,3.39,-4.72,10.46,-11.67,3.72,-0.5,9.17,-4.57,-3.89,-0.99,5.3,-11.18,1.99,6.86,4.23,-8.82,3.18,2.35,-0.62,-9.85,8.47,0.02,-3.17,2.08,2.21,-10.77,713.67
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M10] rank=10 service=istio-ingressgateway-565bffd4d-4nr6v metric=istio_agent_go_memstats_gc_cpu_fraction baseline=2e-06 peak=2e-06 signed_z=104.4 onset_bin=0 onset_rel_s=18.281 persistence_bins=40
values_compact=delta:0.000002,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M11] rank=11 service=node-4 metric=system.net.bytes_sent baseline=512479.0825 peak=2761177.4 signed_z=100.504 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:475794.6,17466.15,14674.35,-14381.45,-10372.45,20105.4,10421.15,-6224.55,5805.1,-11319.25,19926.5,-11527.05,13297.55,-10277.9,-5664.8,54519.85,-53629.95,9650.4,-4576.9,62586.25,-47367.55,-7178.1,-46.05,158009.4,-163651.8,-11288.85,39479.1,-24033.35,-3200.8,13390.05,27384.4,-35819,34666.95,-51847.35,-9264.3,-3711.4,2729.8,20916.15,-26836.5,2272573.6
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M12] rank=12 service=cartservice-0 metric=container_network_receive_MB.eth0 baseline=0.031209 peak=0.552331 signed_z=99.872 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.026949,0.000911,0.002879,0.00667,-0.003999,-0.007886,-0.002045,0.012692,0.000148,-0.008449,0.008034,-0.007328,0.007319,-0.00016,-0.013168,0.010818,-0.010565,0.011067,0.006562,-0.011221,0.000094,0.523009,-0.517537,-0.001348,-0.004204,0.007215,-0.00977,0.004209,0.004244,-0.002486,-0.002308,-0.003765,0.003296,0.00357,-0.002616,-0.005445,0.017468,-0.01779,-0.000098,0.010888
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[1320.0,1440.0]

=== LOG SUMMARY ===
{"entries":[{"change_pct":-100.0,"n_during":0,"n_pre":350,"service":"checkoutservice-1"},{"change_pct":-100.0,"n_during":0,"n_pre":62,"service":"emailservice-2"},{"change_pct":-100.0,"n_during":0,"n_pre":2,"service":"frontend-0"},{"change_pct":-100.0,"n_during":0,"n_pre":65,"service":"paymentservice-1"},{"change_pct":-100.0,"n_during":0,"n_pre":12,"service":"redis-cart-0"},{"change_pct":-95.3,"n_during":3,"n_pre":64,"service":"paymentservice-0"},{"change_pct":-95.2,"n_during":28,"n_pre":580,"service":"adservice-0"},{"change_pct":-95.1,"n_during":28,"n_pre":576,"service":"adservice-1"}],"mode":"volume","omitted_services":23,"service_count":31}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":96.7,"error_pct":0.0,"p95_during_ms":0.3029,"p95_pre_ms":0.154,"service":"paymentservice-2","spans":19},{"delta_pct":-76.5,"error_pct":0.0,"p95_during_ms":0.0708,"p95_pre_ms":0.30119999999999997,"service":"shippingservice-2","spans":142},{"delta_pct":-59.0,"error_pct":0.0,"p95_during_ms":0.08144999999999998,"p95_pre_ms":0.19849999999999998,"service":"shippingservice-1","spans":143},{"delta_pct":-42.3,"error_pct":0.0,"p95_during_ms":23.480599999999974,"p95_pre_ms":40.7295,"service":"checkoutservice-2","spans":238},{"delta_pct":-40.0,"error_pct":0.0,"p95_during_ms":0.5999999999999943,"p95_pre_ms":1.0,"service":"cartservice-2","spans":1015},{"delta_pct":-24.6,"error_pct":0.0,"p95_during_ms":31.680799999999984,"p95_pre_ms":42.023,"service":"checkoutservice-0","spans":238},{"delta_pct":24.6,"error_pct":0.0,"p95_during_ms":0.1791999999999999,"p95_pre_ms":0.14379999999999973,"service":"shippingservice-0","spans":141},{"delta_pct":22.1,"error_pct":0.0,"p95_during_ms":0.020749999999999998,"p95_pre_ms":0.017,"service":"adservice-1","spans":303}],"omitted_services":31,"service_count":39}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=14 omitted_edges=2
[{"evidence_source":"metric","onset_rel_s":1200.0,"rank":1,"service":"redis-cart","severity_z":50.854},{"evidence_source":"metric","onset_rel_s":1320.0,"rank":2,"service":"paymentservice","severity_z":183.561},{"evidence_source":"metric","onset_rel_s":1380.0,"rank":3,"service":"cartservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1440.0,"rank":4,"service":"checkoutservice","severity_z":87.669},{"evidence_source":"metric","onset_rel_s":1500.0,"rank":5,"service":"shippingservice","severity_z":57.973},{"evidence_source":"metric","onset_rel_s":1500.0,"rank":6,"service":"adservice2","severity_z":45.473},{"evidence_source":"metric","onset_rel_s":1500.0,"rank":7,"service":"frontend","severity_z":44.762},{"evidence_source":"metric","onset_rel_s":1500.0,"rank":8,"service":"currencyservice","severity_z":43.319},{"evidence_source":"metric","onset_rel_s":1800.0,"rank":9,"service":"productcatalogservice","severity_z":25.93},{"evidence_source":"metric","onset_rel_s":2040.0,"rank":10,"service":"istio-ingressgateway","severity_z":292.145},{"evidence_source":"metric","onset_rel_s":2040.0,"rank":11,"service":"node-2","severity_z":31.657},{"evidence_source":"metric","onset_rel_s":2160.0,"rank":12,"service":"adservice","severity_z":263.137},{"evidence_source":"metric","onset_rel_s":2340.0,"rank":13,"service":"node-4","severity_z":703.485},{"evidence_source":"metric","onset_rel_s":2340.0,"rank":14,"service":"node-5","severity_z":43.837}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"cartservice","caller":"checkoutservice"},{"callee":"currencyservice","caller":"checkoutservice"},{"callee":"paymentservice","caller":"checkoutservice"},{"callee":"productcatalogservice","caller":"checkoutservice"},{"callee":"shippingservice","caller":"checkoutservice"},{"callee":"adservice","caller":"frontend"},{"callee":"cartservice","caller":"frontend"},{"callee":"checkoutservice","caller":"frontend"},{"callee":"currencyservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"frontend"},{"callee":"shippingservice","caller":"frontend"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

[excluded before optimizer]
