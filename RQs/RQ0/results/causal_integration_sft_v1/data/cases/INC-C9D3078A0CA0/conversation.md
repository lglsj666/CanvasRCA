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
opaque_id: INC-C9D3078A0CA0
observation_window={"duration_rel_s":2340.0,"source_metric_rows":40}
selection_summary={"candidate_count":63,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":1445,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","adservice-grpc","adservice-http","adservice2","adservice2-0","cartservice-0","cartservice-1","cartservice-2","cartservice-grpc","cartservice2-0","checkoutservice-0","checkoutservice-1","checkoutservice-2","checkoutservice-grpc","checkoutservice2-0","currencyservice-0","currencyservice-1","currencyservice-2","currencyservice-grpc","currencyservice2-0","emailservice-0","emailservice-1","emailservice-2","emailservice-grpc","emailservice2-0","frontend-0","frontend-1","frontend-2","frontend-http","frontend2-0","istio-egressgateway-7bfdcc9d86-22q7z","istio-ingressgateway-565bffd4d-4nr6v","node-1","node-2","node-3","node-4","node-5","node-6","paymentservice-0","paymentservice-1","paymentservice-2","paymentservice-grpc","paymentservice2-0","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","productcatalogservice-grpc","productcatalogservice2-0","recommendationservice-0","recommendationservice-1","recommendationservice-2","recommendationservice-grpc","recommendationservice2-0","redis-cart-0","redis-cart2-0","shippingservice-0","shippingservice-1","shippingservice-2","shippingservice-grpc","shippingservice2-0"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[18.281,54.844,91.406,127.969,164.531,201.094,237.656,274.219,310.781,347.344,383.906,420.469,457.031,493.594,530.156,566.719,603.281,639.844,676.406,712.969,749.531,786.094,822.656,859.219,895.781,932.344,968.906,1005.469,1042.031,1078.594,1115.156,1151.719,1188.281,1224.844,1261.406,1297.969,1334.531,1371.094,1407.656,1444.219,1480.781,1517.344,1553.906,1590.469,1627.031,1663.594,1700.156,1736.719,1773.281,1809.844,1846.406,1882.969,1919.531,1956.094,1992.656,2029.219,2065.781,2102.344,2138.906,2175.469,2212.031,2248.594,2285.156,2321.719]
[M1] rank=1 service=adservice metric=java_lang_Memory_ObjectPendingFinalizationCount baseline=0.0 peak=0.083333 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.083333,-0.083333,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M2] rank=2 service=cartservice-1 metric=container_cpu_cfs_throttled_seconds baseline=0.0 peak=0.070941 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.070941,-0.070941,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M3] rank=3 service=cartservice2-0 metric=container_cpu_cfs_throttled_seconds baseline=0.0 peak=0.058741 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.058741,-0.058741,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M4] rank=4 service=currencyservice-2 metric=container_cpu_cfs_throttled_seconds baseline=0.565728 peak=1022.371061 signed_z=414.366 onset_bin=31 onset_rel_s=1151.719 persistence_bins=8
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,11.314562,747.889604,83.424826,51.385491,72.179418,-53.756996,109.934156,-522.155877,-500.215184,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M5] rank=5 service=paymentservice-2 metric=container_network_receive_MB.eth0 baseline=0.01931 peak=0.54213 signed_z=202.655 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.018605,0.001508,-0.001246,0.000319,0.001189,-0.001224,-0.003883,0.006456,-0.004686,0.005323,-0.005881,-0.001113,0.007991,0.000498,-0.008313,0.003555,0.003943,-0.004108,0.001521,-0.003081,0.001912,0.000462,-0.007603,0.009667,0.520319,-0.522763,0.00224,-0.006939,0.001099,0.008422,-0.001226,-0.004277,0.000065,0.000415,-0.000166,0.001448,-0.000998,-0.002471,0.0023,0.001342
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M6] rank=6 service=currencyservice-2 metric=container_cpu_cfs_throttled_periods baseline=0.8 peak=667.666667 signed_z=191.237 onset_bin=31 onset_rel_s=1151.719 persistence_bins=8
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,16,530.5,44.5,-4.5,44.5,-37,73.666667,-321.333334,-346.333333,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M7] rank=7 service=currencyservice-2 metric=container_cpu_user_seconds baseline=0.1045 peak=27.07 signed_z=189.577 onset_bin=31 onset_rel_s=1151.719 persistence_bins=8
values_compact=delta:0.07,0.01,0.006667,-0.023334,-0.013333,0.035,-0.015,0,0.01,0.001667,0.006666,-0.043333,0.01,0.015,-0.01,0,0.005,0.061667,-0.063334,0.656667,24.855,1.495,-3.31,1.68,-1.5,2.938333,-13.141666,-13.663334,0.013334,-0.031667,0,0.015,0.01,-0.01,0.02,-0.04,-0.01,0.035,0,-0.005
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M8] rank=8 service=currencyservice-2 metric=container_cpu_usage_seconds baseline=0.122402 peak=26.716913 signed_z=180.291 onset_bin=31 onset_rel_s=1151.719 persistence_bins=8
values_compact=delta:0.08126,0.008835,0.022818,-0.035341,-0.014906,0.0344,-0.003767,-0.014465,0.020409,-0.000442,0.011429,-0.053423,0.009401,0.031535,-0.018576,-0.002973,0.006837,0.068701,-0.075757,0.683221,21.17787,1.702166,-0.175281,1.780484,-1.494374,2.966852,-12.803584,-13.833931,0.025251,-0.040964,0.006327,0.014677,0.010708,0.001778,0.004545,-0.041022,-0.005961,0.037434,-0.006036,-0.002827
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M9] rank=9 service=paymentservice2-0 metric=container_network_receive_MB.eth0 baseline=0.019647 peak=0.539669 signed_z=175.539 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.016613,0.005256,0.001431,-0.00278,-0.006015,0.002211,0.006663,-0.000427,-0.006659,0.004769,-0.005856,0.004574,0.005863,-0.007079,-0.001722,0.003872,-0.000592,-0.000351,-0.00223,0.004,-0.001924,0.520052,-0.52052,0.002683,-0.005477,0.005282,-0.004971,0.003215,0.000527,-0.00091,-0.00005,-0.000263,-0.001461,0.002108,0.000223,-0.001317,-0.00263,0.002341,0.005142,-0.009799
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M10] rank=10 service=paymentservice-1 metric=container_network_receive_MB.eth0 baseline=0.020207 peak=0.539981 signed_z=161.948 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.013205,0.006004,0.00701,-0.00849,-0.000622,0.001263,0.007002,-0.002033,-0.005415,0.000132,-0.000775,0.007031,-0.005487,0.002675,0.001132,-0.003463,0.004531,-0.001942,-0.003511,0.001937,-0.000008,-0.00186,0.003548,-0.004662,0.005956,-0.00387,0.005229,-0.001214,-0.00698,0.001452,0.522206,-0.516462,-0.003968,0.002574,-0.001512,-0.000604,-0.000745,0.002062,-0.000757,-0.002884
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M11] rank=11 service=currencyservice2-0 metric=container_fs_usage_MB./dev/vda1 baseline=123.699414 peak=76.857422 signed_z=-161.799 onset_bin=44 onset_rel_s=1627.031 persistence_bins=13
values_compact=delta:123.220703,0.048828,0.046875,0.054688,0.054687,0.054688,0.05664,0.044922,0.046875,0.044922,0.013672,0.070312,0.074219,0.060547,0.046875,0.044922,0.046875,0.044922,0.046875,0.035156,0.046875,0.050781,0.046875,0.054688,0.048828,0.044922,0.046875,-23.822266,-23.818359,0.046875,0.017578,0.065104,0.061849,0.052734,0.052735,0.054687,0.056641,0.048828,0.046875,0.025391
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M12] rank=12 service=emailservice2-0 metric=container_network_receive_MB.eth0 baseline=0.022948 peak=0.548481 signed_z=143.415 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.012569,0.011502,0.001682,0.001848,-0.002486,-0.008165,0.006544,-0.000869,0.001589,-0.004801,0.005573,-0.003745,0.005451,-0.006067,0.008423,-0.008603,0.004177,-0.001245,0.000655,-0.001952,0.002271,-0.004675,0.009027,0.519778,-0.533211,0.007686,0.000189,-0.000651,0.001096,-0.002246,0.001327,0.00339,-0.006818,0.005536,-0.00105,0.004828,-0.009378,0.004227,-0.003556,0.003396
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[1140.0,1260.0]

=== LOG SUMMARY ===
{"entries":[{"change_pct":-96.5,"n_during":5,"n_pre":141,"service":"paymentservice-2"},{"change_pct":-95.8,"n_during":6,"n_pre":143,"service":"paymentservice-1"},{"change_pct":-95.7,"n_during":6,"n_pre":141,"service":"emailservice-0"},{"change_pct":-95.7,"n_during":6,"n_pre":140,"service":"emailservice-1"},{"change_pct":-95.6,"n_during":34,"n_pre":767,"service":"checkoutservice-0"},{"change_pct":-95.5,"n_during":34,"n_pre":760,"service":"checkoutservice-2"},{"change_pct":-95.3,"n_during":1094,"n_pre":23134,"service":"frontend-0"},{"change_pct":-95.2,"n_during":373,"n_pre":7793,"service":"frontend-2"}],"mode":"volume","omitted_services":23,"service_count":31}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":152.8,"error_pct":0.0,"p95_during_ms":104.93609999999994,"p95_pre_ms":41.5057,"service":"checkoutservice-0","spans":562},{"delta_pct":150.1,"error_pct":0.0,"p95_during_ms":104.56384999999993,"p95_pre_ms":41.8083,"service":"checkoutservice-2","spans":568},{"delta_pct":92.2,"error_pct":0.0,"p95_during_ms":96.30824999999999,"p95_pre_ms":50.103,"service":"frontend-0","spans":17207},{"delta_pct":86.1,"error_pct":0.0,"p95_during_ms":93.4975,"p95_pre_ms":50.25,"service":"frontend-2","spans":5727},{"delta_pct":83.3,"error_pct":0.0,"p95_during_ms":91.62044999999993,"p95_pre_ms":49.98025,"service":"frontend-1","spans":17146},{"delta_pct":50.0,"error_pct":0.0,"p95_during_ms":0.11850000000000001,"p95_pre_ms":0.079,"service":"shippingservice-1","spans":337},{"delta_pct":39.4,"error_pct":0.0,"p95_during_ms":0.1255,"p95_pre_ms":0.09,"service":"shippingservice-2","spans":337},{"delta_pct":-27.4,"error_pct":0.0,"p95_during_ms":0.07339999999999999,"p95_pre_ms":0.10110000000000026,"service":"shippingservice-0","spans":337}],"omitted_services":32,"service_count":40}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=15 omitted_edges=1
[{"evidence_source":"trace","onset_rel_s":1194.6,"rank":1,"service":"frontend","severity_z":12.796},{"evidence_source":"trace","onset_rel_s":1194.6,"rank":2,"service":"checkoutservice","severity_z":28.935},{"evidence_source":"metric","onset_rel_s":1200.0,"rank":3,"service":"adservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1200.0,"rank":4,"service":"currencyservice","severity_z":414.366},{"evidence_source":"metric","onset_rel_s":1260.0,"rank":5,"service":"cartservice2","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1260.0,"rank":6,"service":"paymentservice2","severity_z":175.539},{"evidence_source":"metric","onset_rel_s":1260.0,"rank":7,"service":"shippingservice","severity_z":71.215},{"evidence_source":"metric","onset_rel_s":1380.0,"rank":8,"service":"emailservice2","severity_z":143.415},{"evidence_source":"metric","onset_rel_s":1500.0,"rank":9,"service":"recommendationservice2","severity_z":29.931},{"evidence_source":"trace","onset_rel_s":1535.4,"rank":10,"service":"paymentservice","severity_z":35.928},{"evidence_source":"metric","onset_rel_s":1560.0,"rank":11,"service":"redis-cart2","severity_z":91.703},{"evidence_source":"metric","onset_rel_s":1680.0,"rank":12,"service":"currencyservice2","severity_z":161.799},{"evidence_source":"metric","onset_rel_s":1860.0,"rank":13,"service":"emailservice","severity_z":128.404},{"evidence_source":"metric","onset_rel_s":1980.0,"rank":14,"service":"cartservice","severity_z":999.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"cartservice","caller":"checkoutservice"},{"callee":"currencyservice","caller":"checkoutservice"},{"callee":"emailservice","caller":"checkoutservice"},{"callee":"paymentservice","caller":"checkoutservice"},{"callee":"shippingservice","caller":"checkoutservice"},{"callee":"adservice","caller":"frontend"},{"callee":"cartservice","caller":"frontend"},{"callee":"checkoutservice","caller":"frontend"},{"callee":"currencyservice","caller":"frontend"},{"callee":"shippingservice","caller":"frontend"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"high","reason":"Rank currencyservice-2 first because currencyservice-2 has direct container_cpu_cfs_throttled_seconds evidence (signed-z 414.37, persistence 8 bins); although frontend-0 is salient, the caller path frontend -> currencyservice means a disturbance in the callee can propagate back toward that caller-side symptom.","services":["currencyservice-2","frontend-0"]}
