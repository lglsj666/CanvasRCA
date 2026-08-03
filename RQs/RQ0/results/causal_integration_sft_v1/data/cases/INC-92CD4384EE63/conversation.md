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
opaque_id: INC-92CD4384EE63
observation_window={"duration_rel_s":2340.0,"source_metric_rows":40}
selection_summary={"candidate_count":63,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":1403,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","adservice-grpc","adservice-http","adservice2","adservice2-0","cartservice-0","cartservice-1","cartservice-2","cartservice-grpc","cartservice2-0","checkoutservice-0","checkoutservice-1","checkoutservice-2","checkoutservice-grpc","checkoutservice2-0","currencyservice-0","currencyservice-1","currencyservice-2","currencyservice-grpc","currencyservice2-0","emailservice-0","emailservice-1","emailservice-2","emailservice-grpc","emailservice2-0","frontend-0","frontend-1","frontend-2","frontend-http","frontend2-0","istio-egressgateway-7bfdcc9d86-zpjpg","istio-ingressgateway-565bffd4d-6bl7m","node-1","node-2","node-3","node-4","node-5","node-6","paymentservice-0","paymentservice-1","paymentservice-2","paymentservice-grpc","paymentservice2-0","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","productcatalogservice-grpc","productcatalogservice2-0","recommendationservice-0","recommendationservice-1","recommendationservice-2","recommendationservice-grpc","recommendationservice2-0","redis-cart-0","redis-cart2-0","shippingservice-0","shippingservice-1","shippingservice-2","shippingservice-grpc","shippingservice2-0"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[18.281,54.844,91.406,127.969,164.531,201.094,237.656,274.219,310.781,347.344,383.906,420.469,457.031,493.594,530.156,566.719,603.281,639.844,676.406,712.969,749.531,786.094,822.656,859.219,895.781,932.344,968.906,1005.469,1042.031,1078.594,1115.156,1151.719,1188.281,1224.844,1261.406,1297.969,1334.531,1371.094,1407.656,1444.219,1480.781,1517.344,1553.906,1590.469,1627.031,1663.594,1700.156,1736.719,1773.281,1809.844,1846.406,1882.969,1919.531,1956.094,1992.656,2029.219,2065.781,2102.344,2138.906,2175.469,2212.031,2248.594,2285.156,2321.719]
[M1] rank=1 service=node-1 metric=system.net.tcp.retrans_segs baseline=0.018 peak=36.69 signed_z=806.807 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0.02,-0.02,0.02,-0.02,0,0,0,0,0.19,-0.19,0.03,-0.03,0.1,-0.1,0,0,0.02,-0.02,0.02,-0.02,0,0.02,0.05,5.3,-5.32,-0.02,0.05,-0.06,0,0,0.03,0,-0.03,36.67,-36.69,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M2] rank=2 service=node-5 metric=system.io.avg_q_sz baseline=0.0035 peak=7.14 signed_z=467.779 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0.07,-0.07,0,0,0,0,0,0,0,0,7.14,-0.63,-6.51,0,0,0,0,0.06,-0.06,0,0.01,-0.01,0,0,0,0,0.02,-0.02,0.04,-0.04
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M3] rank=3 service=currencyservice-2 metric=container_fs_usage_MB./dev/vda1 baseline=679.768359 peak=632.46875 signed_z=-386.225 onset_bin=44 onset_rel_s=1627.031 persistence_bins=13
values_compact=delta:679.564453,0.021485,0.021484,0.021484,0.021485,0.021484,0.021484,0.023438,0.023437,0.021485,0.021484,0.019531,0.021485,0.019531,0.019531,0.021485,0.019531,0.021484,0.021485,0.019531,0.021484,0.021485,0.019531,0.019531,0.023438,0.023437,0.021485,0.023437,0.019531,-23.845703,-23.845703,0.021484,0.023438,0.021484,0.021485,0.021484,0.021484,0.021485,0.021484,0.021484
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M4] rank=4 service=paymentservice2-0 metric=container_network_receive_MB.eth0 baseline=0.023903 peak=0.608503 signed_z=281.487 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.023685,0.003089,-0.004745,0.000491,0.00414,-0.002246,-0.002103,0,0.003364,-0.001455,-0.000607,-0.000253,0.003197,-0.006183,0.006914,-0.0039,-0.000145,0.001025,0.00167,-0.006514,0.589079,-0.585783,0.000477,0.004306,-0.000447,-0.005662,0.002748,0.000525,-0.001197,0.002014,-0.001033,-0.000489,-0.000077,0.000814,-0.003088,0.001857,0.001328,0.00087,-0.002014,0.00005
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M5] rank=5 service=paymentservice-1 metric=container_network_receive_MB.eth0 baseline=0.021768 peak=0.360064 signed_z=239.461 onset_bin=44 onset_rel_s=1627.031 persistence_bins=2
values_compact=delta:0.020661,0.001081,0.000158,-0.000447,-0.001758,0.003518,-0.00037,0,-0.001666,-0.000866,0.000073,0.002042,0.001725,-0.001578,0.000134,-0.001296,-0.002809,0.005784,-0.002388,-0.001118,0.001106,-0.002458,0.003269,-0.000538,0.002293,-0.004717,0.003154,0.337075,-0.002277,-0.334039,-0.001593,-0.000817,-0.000196,0.000125,0.000003,0.001129,-0.000707,0.001277,-0.002155,0.000691
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M6] rank=6 service=frontend-1 metric=container_network_receive_MB.eth0 baseline=0.022228 peak=0.594768 signed_z=210.172 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.026705,0.000766,-0.007703,0.000941,0.003863,-0.003974,0.000322,0,0.00469,-0.001174,-0.003115,-0.001011,-0.000152,0.003755,-0.006642,0.00452,0.003849,-0.002625,-0.002018,-0.002572,0.002216,0.574127,-0.573319,0.007047,-0.009747,-0.002146,0.00761,0.002085,-0.004844,0.002068,-0.000887,-0.001811,0.001356,0.00037,-0.000909,-0.000183,-0.000458,0.000589,-0.005443,0.006418
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M7] rank=7 service=istio-egressgateway-7bfdcc9d86-zpjpg metric=istio_agent_go_memstats_frees baseline=6094.4 peak=9216.5 signed_z=185.062 onset_bin=44 onset_rel_s=1627.031 persistence_bins=4
values_compact=delta:6073,17,-17.5,2.5,-2.5,21.5,11,0,9,9,11,-37.5,4,-24.5,18,-2,19,-20.5,-9,6.5,-17,6,0,32.5,-28.5,24,257.5,2854,-333,-2755.5,-31.5,22,-27,6,-7,-28,21,66.5,18,-102
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M8] rank=8 service=redis-cart-0 metric=container_network_receive_MB.eth0 baseline=0.039088 peak=0.639142 signed_z=172.303 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.03871,-0.000441,-0.001765,0.00727,-0.003272,-0.003006,0.003463,0,0.000748,-0.009763,0.009655,-0.002014,-0.003981,0.001005,0.002694,0.00188,-0.002069,-0.002508,-0.003128,0.014373,-0.010363,0.601654,-0.601075,0.000665,-0.003326,0.006373,-0.00606,0.009954,-0.009358,0.004248,-0.00329,-0.001639,0.001998,0.003198,0.001353,-0.0017,-0.008427,0.008478,0.000756,-0.002169
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M9] rank=9 service=node-5 metric=system.io.util baseline=0.145 peak=45.85 signed_z=145.647 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.45,-0.45,0,0.2,-0.2,0.2,-0.2,0,0,0.15,1.25,-1.4,0,0.25,-0.25,0,0,0.25,-0.25,0,45.85,-6.3,-39.55,0,0,0,0.25,1.5,-1.75,0,0.55,-0.55,0,0,0,0,0.75,-0.75,1.3,-1.3
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M10] rank=10 service=node-5 metric=system.io.w_await baseline=0.19 peak=39.92 signed_z=119.627 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.56,-0.56,0,1.25,-1.25,0.3,-0.3,0,0,0,0.63,-0.63,0,0.49,-0.49,0,0,0.57,-0.57,0,39.92,-11.41,-28.51,0,0,0,0,0.56,-0.56,0,0.51,-0.51,0,0,0,0,1.47,-1.47,0.54,-0.54
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M11] rank=11 service=node-5 metric=system.io.await baseline=0.215 peak=39.92 signed_z=118.285 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.56,-0.56,0,1.25,-1.25,0.3,-0.3,0,0,0.5,0.13,-0.63,0,0.49,-0.49,0,0,0.57,-0.57,0,39.92,-11.41,-28.51,0,0,0,1,-0.44,-0.56,0,0.51,-0.51,0,0,0,0,1.44,-1.44,0.54,-0.54
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M12] rank=12 service=cartservice-1 metric=container_network_receive_MB.eth0 baseline=0.034749 peak=0.340973 signed_z=79.033 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.034496,0.000943,0.002583,-0.002616,-0.005663,0.012329,-0.005771,0,-0.00933,0.006806,0.003941,0.003074,-0.007856,-0.001019,0.003168,-0.003846,0.008759,-0.010527,0.007071,-0.005786,0.008034,-0.006626,0.008916,-0.011467,0.008426,-0.00578,0.00609,-0.004166,0.30679,-0.008007,-0.304405,0.007449,-0.001358,0.001223,0.001137,-0.00107,0.003046,-0.00482,0.001346,-0.006862
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[1680.0,2340.0]

=== LOG SUMMARY ===
{"entries":[{"change_pct":-100.0,"n_during":0,"n_pre":2,"service":"frontend-1"},{"change_pct":-100.0,"n_during":0,"n_pre":12,"service":"redis-cart-0"},{"change_pct":-73.8,"n_during":17,"n_pre":65,"service":"emailservice-1"},{"change_pct":-67.7,"n_during":21,"n_pre":65,"service":"paymentservice-1"},{"change_pct":-64.3,"n_during":119,"n_pre":333,"service":"checkoutservice-2"},{"change_pct":-62.9,"n_during":218,"n_pre":588,"service":"adservice-2"},{"change_pct":-62.7,"n_during":350,"n_pre":938,"service":"adservice-0"},{"change_pct":-62.7,"n_during":220,"n_pre":590,"service":"adservice-1"}],"mode":"volume","omitted_services":23,"service_count":31}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":-100.0,"error_pct":0.0,"p95_during_ms":0.0,"p95_pre_ms":1.0,"service":"cartservice-2","spans":1343},{"delta_pct":-40.0,"error_pct":0.0,"p95_during_ms":0.5999999999999659,"p95_pre_ms":1.0,"service":"cartservice-0","spans":1352},{"delta_pct":-28.4,"error_pct":0.0,"p95_during_ms":0.2164,"p95_pre_ms":0.30209999999999854,"service":"paymentservice-2","spans":26},{"delta_pct":-16.1,"error_pct":0.0,"p95_during_ms":45.953649999999996,"p95_pre_ms":54.75175,"service":"checkoutservice-0","spans":330},{"delta_pct":12.7,"error_pct":0.0,"p95_during_ms":0.1848,"p95_pre_ms":0.164,"service":"paymentservice-1","spans":28},{"delta_pct":-10.6,"error_pct":0.0,"p95_during_ms":0.25559999999999994,"p95_pre_ms":0.28600000000000003,"service":"shippingservice-1","spans":189},{"delta_pct":8.8,"error_pct":0.0,"p95_during_ms":0.021,"p95_pre_ms":0.01930000000000001,"service":"adservice-2","spans":403},{"delta_pct":-8.7,"error_pct":0.0,"p95_during_ms":0.261,"p95_pre_ms":0.286,"service":"shippingservice-0","spans":192}],"omitted_services":31,"service_count":39}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=15 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":1200.0,"rank":1,"service":"node-5","severity_z":467.779},{"evidence_source":"metric","onset_rel_s":1200.0,"rank":2,"service":"paymentservice2","severity_z":281.487},{"evidence_source":"metric","onset_rel_s":1260.0,"rank":3,"service":"frontend","severity_z":210.172},{"evidence_source":"metric","onset_rel_s":1260.0,"rank":4,"service":"redis-cart","severity_z":172.303},{"evidence_source":"metric","onset_rel_s":1380.0,"rank":5,"service":"adservice","severity_z":76.374},{"evidence_source":"metric","onset_rel_s":1440.0,"rank":6,"service":"recommendationservice","severity_z":71.74},{"evidence_source":"metric","onset_rel_s":1620.0,"rank":7,"service":"paymentservice","severity_z":239.461},{"evidence_source":"metric","onset_rel_s":1620.0,"rank":8,"service":"istio-egressgateway","severity_z":185.062},{"evidence_source":"metric","onset_rel_s":1680.0,"rank":9,"service":"cartservice","severity_z":79.033},{"evidence_source":"metric","onset_rel_s":1740.0,"rank":10,"service":"checkoutservice","severity_z":46.762},{"evidence_source":"metric","onset_rel_s":1800.0,"rank":11,"service":"currencyservice","severity_z":386.225},{"evidence_source":"trace","onset_rel_s":1925.4,"rank":12,"service":"adservice2","severity_z":6.251},{"evidence_source":"metric","onset_rel_s":2220.0,"rank":13,"service":"node-1","severity_z":806.807},{"evidence_source":"metric","onset_rel_s":2280.0,"rank":14,"service":"cartservice2","severity_z":27.157}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"cartservice","caller":"checkoutservice"},{"callee":"currencyservice","caller":"checkoutservice"},{"callee":"paymentservice","caller":"checkoutservice"},{"callee":"adservice","caller":"frontend"},{"callee":"cartservice","caller":"frontend"},{"callee":"checkoutservice","caller":"frontend"},{"callee":"currencyservice","caller":"frontend"},{"callee":"recommendationservice","caller":"frontend"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"medium","reason":"Rank node-5 first because node-5 has direct system.io.avg_q_sz evidence (signed-z 467.78, persistence 0 bins); paymentservice2-0 is second despite propagation rank 2 because onset ordering alone does not establish the causal origin.","services":["node-5","paymentservice2-0"]}
