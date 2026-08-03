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
opaque_id: INC-93F314C71A1F
observation_window={"duration_rel_s":2340.0,"source_metric_rows":40}
selection_summary={"candidate_count":63,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":1498,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","adservice-grpc","adservice-http","adservice2","adservice2-0","cartservice-0","cartservice-1","cartservice-2","cartservice-grpc","cartservice2-0","checkoutservice-0","checkoutservice-1","checkoutservice-2","checkoutservice-grpc","checkoutservice2-0","currencyservice-0","currencyservice-1","currencyservice-2","currencyservice-grpc","currencyservice2-0","emailservice-0","emailservice-1","emailservice-2","emailservice-grpc","emailservice2-0","frontend-0","frontend-1","frontend-2","frontend-http","frontend2-0","istio-egressgateway-7bfdcc9d86-g2d4q","istio-ingressgateway-565bffd4d-rn678","node-1","node-2","node-3","node-4","node-5","node-6","paymentservice-0","paymentservice-1","paymentservice-2","paymentservice-grpc","paymentservice2-0","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","productcatalogservice-grpc","productcatalogservice2-0","recommendationservice-0","recommendationservice-1","recommendationservice-2","recommendationservice-grpc","recommendationservice2-0","redis-cart-0","redis-cart2-0","shippingservice-0","shippingservice-1","shippingservice-2","shippingservice-grpc","shippingservice2-0"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[18.281,54.844,91.406,127.969,164.531,201.094,237.656,274.219,310.781,347.344,383.906,420.469,457.031,493.594,530.156,566.719,603.281,639.844,676.406,712.969,749.531,786.094,822.656,859.219,895.781,932.344,968.906,1005.469,1042.031,1078.594,1115.156,1151.719,1188.281,1224.844,1261.406,1297.969,1334.531,1371.094,1407.656,1444.219,1480.781,1517.344,1553.906,1590.469,1627.031,1663.594,1700.156,1736.719,1773.281,1809.844,1846.406,1882.969,1919.531,1956.094,1992.656,2029.219,2065.781,2102.344,2138.906,2175.469,2212.031,2248.594,2285.156,2321.719]
[M1] rank=1 service=checkoutservice-0 metric=container_fs_inodes./dev/vda1 baseline=0.0 peak=1.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,-1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M2] rank=2 service=paymentservice-2 metric=container_network_receive_MB.eth0 baseline=0.022219 peak=0.55332 signed_z=418.804 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.021246,0.000946,-0.001953,0.00038,0.003526,-0.001123,-0.001493,0.001563,-0.000571,-0.00269,0.000761,0.003509,-0.00284,0.00054,0.00026,0.000838,0.000377,0.000415,0,-0.001119,-0.002012,-0.000293,0.004991,-0.005689,0.003344,0.530407,-0.529383,-0.002919,0.001189,-0.00105,-0.000813,0.000634,0.002574,-0.003769,0.004123,-0.002246,0.001689,-0.001236,-0.001061,0.002421
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M3] rank=3 service=checkoutservice-0 metric=container_memory_mapped_file baseline=73728.0 peak=10207232.0 signed_z=413.55 onset_bin=36 onset_rel_s=1334.531 persistence_bins=6
values_compact=delta:73728,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,10133504,-5474304,-4732928,0,0,0,0,4096,8192,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M4] rank=4 service=redis-cart2-0 metric=container_network_receive_MB.eth0 baseline=0.040682 peak=0.565856 signed_z=181.881 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.041216,0.001337,-0.003306,-0.000273,0.003551,-0.004894,-0.000135,0.005593,-0.004168,0.001438,-0.000128,0.000199,0.005718,-0.013535,0.007322,0.003001,-0.001829,0.000203,0,0.004299,-0.00785,0.005762,0.522335,-0.527247,-0.00292,0.00796,-0.003433,0.001842,-0.003643,-0.004349,0.01222,-0.0071,0.00705,-0.010097,0.007258,-0.005257,0.001831,-0.009139,0.012729,-0.000405
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M5] rank=5 service=checkoutservice-0 metric=container_fs_usage_MB./dev/vda1 baseline=31.746289 peak=34.589844 signed_z=171.83 onset_bin=36 onset_rel_s=1334.531 persistence_bins=18
values_compact=delta:31.71875,0.003906,0.003906,0,0.003907,0.003906,0,0.003906,0.003907,0.003906,0,0.003906,0.003906,0.003906,0,0.003907,0.003906,0.003906,0,0.003907,2.761718,0.003906,0.003907,0,0.003906,0.003906,0.003907,0,0.003906,0.003906,0,0.003906,0.003906,0.003907,0,0.003906,0.003906,0.003907,0,0.003906
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M6] rank=6 service=cartservice-1 metric=container_network_receive_MB.eth0 baseline=0.082364 peak=0.608409 signed_z=72.651 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.086407,-0.006886,0.005656,-0.001921,-0.001656,-0.009406,0.003363,0.021375,-0.014386,-0.002834,0.015191,-0.021266,0.014799,-0.000781,0.002487,-0.021336,0.01864,-0.011215,0,0.004663,0.005899,0.521616,-0.517704,-0.017605,0.022409,-0.007438,-0.021926,0.034934,-0.020203,-0.006876,0.00604,0.006374,-0.001558,0.000373,-0.015277,0.015713,0.002723,-0.014751,0.010993,-0.002993
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M7] rank=7 service=checkoutservice-1 metric=container_memory_mapped_file baseline=167936.0 peak=196608.0 signed_z=60.748 onset_bin=36 onset_rel_s=1334.531 persistence_bins=18
values_compact=delta:167936,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,20480,8192,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M8] rank=8 service=node-2 metric=system.net.tcp.out_segs baseline=1867.644 peak=15983.8 signed_z=57.068 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:1672.35,121.76,-6.86,11.48,198.42,345.97,-664.01,48.13,36.31,89.17,-145.42,635.06,-649.78,63.29,-100.42,220.53,-133.23,159.11,-196.93,853.54,-880.94,93.93,-154.36,14366.7,-10213.45,-4088.71,16.53,29.81,90.05,20.35,-122.15,114.87,573.9,-322.97,-480.45,124.04,-96.87,65.84,5.63,87.48
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M9] rank=9 service=node-4 metric=system.net.tcp.in_segs baseline=550.239 peak=1073.92 signed_z=50.281 onset_bin=36 onset_rel_s=1334.531 persistence_bins=3
values_compact=delta:536.55,-10.14,29.06,2.55,-2.29,-22.18,11.94,12.19,-10.91,8.71,-8.18,7.21,1.64,0.15,-13.14,14.65,6.61,4.86,-25.18,-3.5,12.83,-5.76,316.61,209.64,-504.51,-3.24,-25.19,17.84,-22.06,10.39,-4.78,18.71,-16.49,-11.12,17.25,14.36,-6.27,-18.78,3.62,218.33
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M10] rank=10 service=cartservice-2 metric=container_network_receive_MB.eth0 baseline=0.082641 peak=0.351041 signed_z=44.626 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.079948,-0.003643,0.015026,-0.003577,-0.00928,0.004367,-0.001344,-0.000977,-0.010893,0.025201,-0.011477,-0.006694,0.007804,-0.006309,0.00903,-0.007891,0.007588,0.002025,0,-0.012993,0.007162,-0.006967,0.009111,-0.00841,0.010936,-0.002599,0.265897,-0.004118,-0.264938,-0.006207,0.002074,0.00034,0.003477,-0.000466,0.005542,-0.008531,-0.004287,0.010899,0.004646,-0.028531
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M11] rank=11 service=shippingservice-2 metric=istio_request_duration_milliseconds.http.202. baseline=0.0525 peak=10.1 signed_z=43.906 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,1.05,-1.05,0,0,0,0,0,0,0,0,10.1,-10.1,0,0,0,0,1.05,-0.525,0,-0.525,0,0,1.05,-1.05,0,0,1.05,-1.05
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M12] rank=12 service=node-4 metric=system.net.tcp.out_segs baseline=1366.661 peak=10370.79 signed_z=42.804 onset_bin=36 onset_rel_s=1334.531 persistence_bins=3
values_compact=delta:1210.2,-60.4,168.98,42.17,-53.77,-47,352.74,169.18,-583.38,16.6,80.09,61.03,631.29,-756.66,104.13,1.77,224.91,-144.75,-258.11,77.2,75.83,-21.07,4555.19,4524.62,-8852.47,463.58,-720.5,193.88,-270.16,32.3,131.5,313.98,-495.22,-10.88,293.78,177.76,649.61,-1079.93,136.16,275.59
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[1200.0,1380.0]

=== LOG SUMMARY ===
{"entries":[{"error_logs":5126,"error_pct":9.01,"service":"adservice-0","total_logs":56888},{"error_logs":918,"error_pct":1.3,"service":"frontend-2","total_logs":70632},{"error_logs":914,"error_pct":1.3,"service":"frontend-0","total_logs":70404},{"error_logs":731,"error_pct":1.29,"service":"frontend-1","total_logs":56536}],"mode":"errors","omitted_services":27,"service_count":31}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":2459.4,"error_pct":0.0,"p95_during_ms":1462.7349999999965,"p95_pre_ms":57.15069999999978,"service":"checkoutservice-0","spans":1996},{"delta_pct":-33.3,"error_pct":0.0,"p95_during_ms":57.352250000000005,"p95_pre_ms":86.01635000000002,"service":"checkoutservice2-0","spans":1178},{"delta_pct":-19.0,"error_pct":0.0,"p95_during_ms":0.017,"p95_pre_ms":0.021,"service":"adservice2-0","spans":1527},{"delta_pct":10.0,"error_pct":0.0,"p95_during_ms":0.022,"p95_pre_ms":0.02,"service":"adservice-2","spans":2562},{"delta_pct":6.8,"error_pct":5.59,"p95_during_ms":80.51814999999989,"p95_pre_ms":75.37899999999964,"service":"frontend2-0","spans":27937},{"delta_pct":5.3,"error_pct":0.0,"p95_during_ms":0.14639999999999997,"p95_pre_ms":0.139,"service":"paymentservice-1","spans":172},{"delta_pct":4.6,"error_pct":0.0,"p95_during_ms":0.15279999999999996,"p95_pre_ms":0.14609999999999998,"service":"paymentservice-2","spans":172},{"delta_pct":-4.3,"error_pct":0.0,"p95_during_ms":0.22035,"p95_pre_ms":0.23015000000000002,"service":"emailservice-2","spans":172}],"omitted_services":32,"service_count":40}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=16 omitted_edges=1
[{"evidence_source":"trace","onset_rel_s":1243.2,"rank":1,"service":"checkoutservice","severity_z":37.635},{"evidence_source":"metric","onset_rel_s":1260.0,"rank":2,"service":"cartservice","severity_z":72.651},{"evidence_source":"metric","onset_rel_s":1260.0,"rank":3,"service":"currencyservice","severity_z":38.213},{"evidence_source":"metric","onset_rel_s":1260.0,"rank":4,"service":"node-5","severity_z":26.975},{"evidence_source":"metric","onset_rel_s":1320.0,"rank":5,"service":"redis-cart2","severity_z":181.881},{"evidence_source":"metric","onset_rel_s":1320.0,"rank":6,"service":"node-4","severity_z":50.281},{"evidence_source":"metric","onset_rel_s":1320.0,"rank":7,"service":"shippingservice","severity_z":43.906},{"evidence_source":"metric","onset_rel_s":1320.0,"rank":8,"service":"frontend","severity_z":38.967},{"evidence_source":"metric","onset_rel_s":1380.0,"rank":9,"service":"node-2","severity_z":57.068},{"evidence_source":"metric","onset_rel_s":1680.0,"rank":10,"service":"istio-egressgateway","severity_z":32.973},{"evidence_source":"metric","onset_rel_s":1680.0,"rank":11,"service":"recommendationservice","severity_z":28.673},{"evidence_source":"trace","onset_rel_s":1730.4,"rank":12,"service":"paymentservice","severity_z":38.992},{"evidence_source":"metric","onset_rel_s":1740.0,"rank":13,"service":"adservice2","severity_z":28.923},{"evidence_source":"metric","onset_rel_s":2100.0,"rank":14,"service":"node-3","severity_z":35.12}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"cartservice","caller":"checkoutservice"},{"callee":"currencyservice","caller":"checkoutservice"},{"callee":"paymentservice","caller":"checkoutservice"},{"callee":"shippingservice","caller":"checkoutservice"},{"callee":"cartservice","caller":"frontend"},{"callee":"checkoutservice","caller":"frontend"},{"callee":"currencyservice","caller":"frontend"},{"callee":"recommendationservice","caller":"frontend"},{"callee":"shippingservice","caller":"frontend"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"high","reason":"Rank checkoutservice-0 first because checkoutservice-0 has direct container_fs_inodes./dev/vda1 evidence (signed-z 999, persistence 0 bins); although frontend-0 is salient, the caller path frontend -> checkoutservice means a disturbance in the callee can propagate back toward that caller-side symptom.","services":["checkoutservice-0","frontend-0"]}
