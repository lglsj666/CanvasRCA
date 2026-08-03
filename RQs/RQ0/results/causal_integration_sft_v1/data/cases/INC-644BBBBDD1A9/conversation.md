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
opaque_id: INC-644BBBBDD1A9
observation_window={"duration_rel_s":2340.0,"source_metric_rows":40}
selection_summary={"candidate_count":63,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":1490,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","adservice-grpc","adservice-http","adservice2","adservice2-0","cartservice-0","cartservice-1","cartservice-2","cartservice-grpc","cartservice2-0","checkoutservice-0","checkoutservice-1","checkoutservice-2","checkoutservice-grpc","checkoutservice2-0","currencyservice-0","currencyservice-1","currencyservice-2","currencyservice-grpc","currencyservice2-0","emailservice-0","emailservice-1","emailservice-2","emailservice-grpc","emailservice2-0","frontend-0","frontend-1","frontend-2","frontend-http","frontend2-0","istio-egressgateway-7bfdcc9d86-g2d4q","istio-ingressgateway-565bffd4d-rn678","node-1","node-2","node-3","node-4","node-5","node-6","paymentservice-0","paymentservice-1","paymentservice-2","paymentservice-grpc","paymentservice2-0","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","productcatalogservice-grpc","productcatalogservice2-0","recommendationservice-0","recommendationservice-1","recommendationservice-2","recommendationservice-grpc","recommendationservice2-0","redis-cart-0","redis-cart2-0","shippingservice-0","shippingservice-1","shippingservice-2","shippingservice-grpc","shippingservice2-0"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[18.281,54.844,91.406,127.969,164.531,201.094,237.656,274.219,310.781,347.344,383.906,420.469,457.031,493.594,530.156,566.719,603.281,639.844,676.406,712.969,749.531,786.094,822.656,859.219,895.781,932.344,968.906,1005.469,1042.031,1078.594,1115.156,1151.719,1188.281,1224.844,1261.406,1297.969,1334.531,1371.094,1407.656,1444.219,1480.781,1517.344,1553.906,1590.469,1627.031,1663.594,1700.156,1736.719,1773.281,1809.844,1846.406,1882.969,1919.531,1956.094,1992.656,2029.219,2065.781,2102.344,2138.906,2175.469,2212.031,2248.594,2285.156,2321.719]
[M1] rank=1 service=istio-egressgateway-7bfdcc9d86-g2d4q metric=istio_agent_go_gc_duration_seconds.0.0 baseline=5.8e-05 peak=5.8e-05 signed_z=-999.0 onset_bin=0 onset_rel_s=18.281 persistence_bins=40
values_compact=delta:0.000058,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M2] rank=2 service=paymentservice-1 metric=container_network_receive_MB.eth0 baseline=0.022026 peak=0.551797 signed_z=332.712 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.023207,0.0005,-0.001388,-0.001338,-0.00068,0.00317,-0.002686,0.000414,0,0.000998,0.00271,-0.006397,0.005607,-0.002134,0.000677,-0.001693,0.002901,-0.001532,0.000112,-0.003083,0.002953,-0.000099,0.00112,-0.002082,0.53054,-0.52812,-0.002482,0.000659,-0.001252,0.001868,0.000769,-0.002559,0.003983,-0.003841,0.000861,-0.002534,0.003402,0.001116,0.001662,-0.003715
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M3] rank=3 service=node-1 metric=system.net.tcp.retrans_segs baseline=0.546 peak=46.43 signed_z=274.927 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.43,0.07,-0.02,0.11,0.06,-0.26,0.06,-0.02,0.13,-0.11,0.02,-0.08,0.13,-0.07,0.7,-0.42,-0.05,-0.09,-0.14,0.11,-0.04,0.08,0.4,-0.45,0.58,-0.54,45.84,-45.91,0,-0.04,0.05,0.03,0.09,-0.17,0.24,-0.09,-0.04,-0.17,0,0.01
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M4] rank=4 service=emailservice-0 metric=container_network_receive_MB.eth0 baseline=0.025443 peak=0.555687 signed_z=249.408 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.025128,-0.000343,-0.001219,0.000836,0.000586,0.003019,-0.000642,-0.000087,0,0.000927,-0.003172,-0.002913,0.007211,-0.006935,0.004513,-0.001526,-0.00008,-0.003135,0.004732,-0.004585,0.00353,0.529842,-0.530051,-0.001849,0.002989,-0.004097,0.002653,0.000846,-0.002543,0.007968,-0.009442,0.006155,-0.005702,0.001853,0.003335,-0.003457,0.000916,0.000312,0.000062,0.000256
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M5] rank=5 service=paymentservice-0 metric=container_network_receive_MB.eth0 baseline=0.022005 peak=0.294655 signed_z=197.262 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.025242,-0.004309,-0.00105,0.004489,-0.003122,0.001613,0.000128,-0.001297,0,0.000821,0.000386,-0.001229,0.000154,0.000736,-0.002527,0.000161,0.003501,-0.002621,-0.00034,0.001221,-0.001515,0.00316,-0.003222,0.274275,-0.007353,-0.266557,0.000593,0.000441,0.001675,-0.002378,-0.000109,0.002343,-0.002962,-0.000045,0.001943,0.000037,0.000127,0.001559,-0.004617,0.001366
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M6] rank=6 service=emailservice-2 metric=container_network_receive_MB.eth0 baseline=0.02556 peak=0.58145 signed_z=157.933 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.024506,0.002901,-0.004603,0.006148,-0.00344,-0.001827,0.007579,-0.004406,0,-0.004435,0.005664,-0.003836,-0.000353,0.000571,0.003171,-0.0073,0.009463,-0.009185,0.011951,-0.013311,0.011101,-0.007444,0.002221,-0.00148,0.002056,0.001266,-0.003191,0.004766,-0.003642,0.556539,-0.554317,-0.001617,0.000525,0.00303,-0.006309,0.001122,0.007866,-0.012687,0.010555,-0.007636
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M7] rank=7 service=shippingservice-2 metric=container_network_receive_MB.eth0 baseline=0.039348 peak=0.307608 signed_z=96.265 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.043267,-0.003524,-0.000718,0.001003,-0.00109,-0.00264,0.005399,-0.000027,0,-0.001744,-0.001736,-0.000823,0.002019,-0.002954,0.007253,-0.00993,0.006507,-0.004914,0.008734,-0.0079,0.003208,0.268218,-0.007374,-0.258114,-0.005124,-0.001116,0.002145,0.002464,-0.002629,0.004015,-0.001289,-0.002017,0.001805,-0.002744,0.002898,-0.000253,-0.002379,0.004069,-0.005218,0.001533
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M8] rank=8 service=checkoutservice-2 metric=container_network_receive_MB.eth0 baseline=0.051432 peak=0.584544 signed_z=65.083 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.057838,-0.005321,0.009376,-0.023267,0.020474,-0.014842,0.012148,-0.001153,0,-0.01415,0.017873,-0.015956,0.022649,-0.029751,0.021922,-0.011604,0.007416,-0.005315,0.006479,-0.012889,0.018374,-0.016451,0.014963,-0.011163,0.004777,0.000193,-0.008929,0.008768,0.532085,-0.536022,0.013593,-0.015202,-0.000341,0.00479,-0.007757,0.010945,-0.003174,-0.011355,0.021283,-0.01524
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M9] rank=9 service=cartservice2-0 metric=container_network_receive_MB.eth0 baseline=0.057317 peak=0.591659 signed_z=59.655 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.057968,0.002498,-0.017653,0.011345,0.019499,-0.021617,0.007227,-0.004199,0,0.004176,-0.005123,-0.003733,0.022089,-0.031351,0.006883,0.022651,-0.008038,-0.003976,0.010848,-0.020452,-0.003826,0.003631,0.023892,-0.000947,-0.014455,0.534322,-0.543168,0.009755,-0.012316,0.019585,0.001098,-0.009103,-0.016788,0.011798,0.006452,-0.006717,0.019963,-0.003866,-0.030668,0.028594
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M10] rank=10 service=checkoutservice-1 metric=container_network_receive_MB.eth0 baseline=0.052497 peak=0.565815 signed_z=58.378 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.058968,-0.007945,0.007574,-0.009132,0.00692,-0.005566,0.005407,0.001496,0,-0.018721,0.023598,-0.019196,0.011088,-0.008649,0.010691,-0.021444,0.029103,-0.018086,0.021888,-0.030233,0.021422,-0.02081,0.029581,-0.016772,-0.004624,0.013667,0.50559,-0.507129,-0.012366,0.01257,-0.010544,0.008826,-0.009929,0.004022,0.010682,-0.018472,0.016452,-0.015209,0.016714,-0.008145
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M11] rank=11 service=adservice metric=java_lang_Compilation_TotalCompilationTime baseline=43392.783333 peak=43416.0 signed_z=58.295 onset_bin=59 onset_rel_s=2175.469 persistence_bins=4
values_compact=delta:43392,0,0,0,0.666667,0.333333,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,19.166667,3.833333,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M12] rank=12 service=shippingservice-2 metric=istio_request_duration_milliseconds.http.202. baseline=0.155 peak=26.5 signed_z=53.64 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,2.05,-2.05,0,0,0,0,0,0,0,1.05,-1.05,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,26.5,-26.5,0,0.525,2.05,-2.575,0,0,0,3.05
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[1800.0,2340.0]

=== LOG SUMMARY ===
{"entries":[{"error_logs":5130,"error_pct":9.01,"service":"adservice-0","total_logs":56930},{"error_logs":932,"error_pct":1.3,"service":"frontend-0","total_logs":71818},{"error_logs":926,"error_pct":1.3,"service":"frontend-2","total_logs":71036},{"error_logs":707,"error_pct":1.29,"service":"frontend-1","total_logs":54742}],"mode":"errors","omitted_services":27,"service_count":31}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":-19.0,"error_pct":0.0,"p95_during_ms":0.017,"p95_pre_ms":0.021,"service":"adservice-1","spans":2561},{"delta_pct":13.3,"error_pct":0.0,"p95_during_ms":0.017,"p95_pre_ms":0.015,"service":"adservice-0","spans":2563},{"delta_pct":-11.6,"error_pct":5.36,"p95_during_ms":69.442,"p95_pre_ms":78.56429999999993,"service":"frontend2-0","spans":28116},{"delta_pct":11.1,"error_pct":0.0,"p95_during_ms":0.02,"p95_pre_ms":0.018,"service":"adservice-2","spans":2562},{"delta_pct":10.3,"error_pct":0.0,"p95_during_ms":0.24930000000000002,"p95_pre_ms":0.226,"service":"emailservice-0","spans":168},{"delta_pct":8.3,"error_pct":0.0,"p95_during_ms":0.14880000000000002,"p95_pre_ms":0.13745,"service":"paymentservice-1","spans":171},{"delta_pct":-8.0,"error_pct":0.0,"p95_during_ms":0.19259999999999997,"p95_pre_ms":0.20944999999999997,"service":"paymentservice2-0","spans":103},{"delta_pct":4.4,"error_pct":0.0,"p95_during_ms":37.36955,"p95_pre_ms":35.78085,"service":"checkoutservice-0","spans":1998}],"omitted_services":32,"service_count":40}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=13 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":1200.0,"rank":1,"service":"currencyservice2","severity_z":24.076},{"evidence_source":"metric","onset_rel_s":1260.0,"rank":2,"service":"emailservice","severity_z":249.408},{"evidence_source":"metric","onset_rel_s":1260.0,"rank":3,"service":"shippingservice","severity_z":96.265},{"evidence_source":"metric","onset_rel_s":1380.0,"rank":4,"service":"adservice2","severity_z":46.615},{"evidence_source":"metric","onset_rel_s":1440.0,"rank":5,"service":"paymentservice","severity_z":332.712},{"evidence_source":"metric","onset_rel_s":1500.0,"rank":6,"service":"cartservice2","severity_z":59.655},{"evidence_source":"metric","onset_rel_s":1560.0,"rank":7,"service":"node-1","severity_z":274.927},{"evidence_source":"metric","onset_rel_s":1620.0,"rank":8,"service":"paymentservice2","severity_z":24.008},{"evidence_source":"metric","onset_rel_s":1680.0,"rank":9,"service":"checkoutservice","severity_z":65.083},{"evidence_source":"metric","onset_rel_s":1800.0,"rank":10,"service":"redis-cart","severity_z":34.513},{"evidence_source":"metric","onset_rel_s":1860.0,"rank":11,"service":"istio-egressgateway","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":2040.0,"rank":12,"service":"adservice","severity_z":58.295},{"evidence_source":"metric","onset_rel_s":2100.0,"rank":13,"service":"productcatalogservice","severity_z":18.394},{"evidence_source":"metric","onset_rel_s":2280.0,"rank":14,"service":"node-3","severity_z":26.711}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"emailservice","caller":"checkoutservice"},{"callee":"paymentservice","caller":"checkoutservice"},{"callee":"productcatalogservice","caller":"checkoutservice"},{"callee":"shippingservice","caller":"checkoutservice"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

[excluded before optimizer]
