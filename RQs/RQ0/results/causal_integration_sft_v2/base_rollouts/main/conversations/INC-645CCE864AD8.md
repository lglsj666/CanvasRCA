# Causal SFT v2 base rollout — INC-645CCE864AD8

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

[image: RQs/RQ0/results/causal_integration_sft_v1/data/cases/INC-645CCE864AD8/dashboard.png]

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
opaque_id: INC-645CCE864AD8
observation_window={"duration_rel_s":2340.0,"source_metric_rows":40}
selection_summary={"candidate_count":63,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":1576,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","adservice-grpc","adservice-http","adservice2","adservice2-0","cartservice-0","cartservice-1","cartservice-2","cartservice-grpc","cartservice2-0","checkoutservice-0","checkoutservice-1","checkoutservice-2","checkoutservice-grpc","checkoutservice2-0","currencyservice-0","currencyservice-1","currencyservice-2","currencyservice-grpc","currencyservice2-0","emailservice-0","emailservice-1","emailservice-2","emailservice-grpc","emailservice2-0","frontend-0","frontend-1","frontend-2","frontend-http","frontend2-0","istio-egressgateway-7bfdcc9d86-22q7z","istio-ingressgateway-565bffd4d-4nr6v","node-1","node-2","node-3","node-4","node-5","node-6","paymentservice-0","paymentservice-1","paymentservice-2","paymentservice-grpc","paymentservice2-0","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","productcatalogservice-grpc","productcatalogservice2-0","recommendationservice-0","recommendationservice-1","recommendationservice-2","recommendationservice-grpc","recommendationservice2-0","redis-cart-0","redis-cart2-0","shippingservice-0","shippingservice-1","shippingservice-2","shippingservice-grpc","shippingservice2-0"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[18.281,54.844,91.406,127.969,164.531,201.094,237.656,274.219,310.781,347.344,383.906,420.469,457.031,493.594,530.156,566.719,603.281,639.844,676.406,712.969,749.531,786.094,822.656,859.219,895.781,932.344,968.906,1005.469,1042.031,1078.594,1115.156,1151.719,1188.281,1224.844,1261.406,1297.969,1334.531,1371.094,1407.656,1444.219,1480.781,1517.344,1553.906,1590.469,1627.031,1663.594,1700.156,1736.719,1773.281,1809.844,1846.406,1882.969,1919.531,1956.094,1992.656,2029.219,2065.781,2102.344,2138.906,2175.469,2212.031,2248.594,2285.156,2321.719]
[M1] rank=1 service=shippingservice2-0 metric=container_memory_failcnt baseline=3331870.95 peak=3357721.0 signed_z=283.074 onset_bin=31 onset_rel_s=1151.719 persistence_bins=21
values_compact=delta:3331850,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,419,0,0,0,0,0,0,0,12403.5,11119,1929.5,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M2] rank=2 service=paymentservice-0 metric=container_network_receive_MB.eth0 baseline=0.022099 peak=0.544332 signed_z=249.569 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.02316,-0.001361,0.000981,-0.001186,-0.000328,0.000095,-0.000846,0.000617,0,0.002274,-0.002471,0.00705,-0.004974,-0.005927,0.003197,0.004109,-0.003302,0.000912,0.000393,0.002287,-0.00303,-0.000174,-0.000113,0.522969,-0.525289,0.005064,-0.001444,0.005385,-0.00757,0.000054,0.004788,0.003615,-0.006333,-0.004701,-0.002508,0.006373,0.00072,0.001989,-0.003801,-0.000221
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M3] rank=3 service=paymentservice-1 metric=container_network_receive_MB.eth0 baseline=0.021786 peak=0.544999 signed_z=178.903 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.026107,-0.003858,-0.005976,0.002698,0.004804,-0.001976,-0.002435,0.002723,0,0.000446,0.003802,-0.006105,-0.001876,0.004089,-0.002525,0.008557,-0.005463,-0.005465,0.004289,0.000483,0.004906,-0.007454,-0.001629,-0.000228,0.003295,0.005145,0.518645,-0.523895,0.00222,-0.002168,-0.000127,0.001471,-0.002837,0.004575,-0.004619,0.001604,0.000609,-0.001936,-0.000721,0.002133
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M4] rank=4 service=paymentservice2-0 metric=container_memory_usage_MB baseline=127.951107 peak=124.246094 signed_z=-170.499 onset_bin=36 onset_rel_s=1334.531 persistence_bins=4
values_compact=delta:127.972656,-0.027344,0.009766,-0.009766,0.027344,-0.009765,-0.082032,0.064453,0,0.041016,-0.029297,-0.011719,0.026042,-0.026042,-0.02539,0.052734,-0.027344,0,0.00586,0.005859,-0.011719,0.014323,-0.088541,-1.890625,1.992187,-0.027344,0.025391,-0.025391,0,0,0.027344,-3.726562,3.699218,0.011719,0.013672,-0.025391,-0.5,0.541016,-0.041016,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M5] rank=5 service=checkoutservice-0 metric=container_network_receive_MB.eth0 baseline=0.050871 peak=0.568471 signed_z=71.907 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.05458,-0.007542,0.017312,-0.022059,0.010143,-0.009074,0.003346,0.005829,0,-0.004433,0.02335,-0.026825,0.001512,0.002795,0.000799,0.010501,-0.017021,0.003308,0.002856,0.003878,0.011112,0.504104,-0.51881,-0.005442,0.022724,-0.021179,-0.005261,0.00835,0.002741,0.002744,0.002771,-0.015321,-0.000934,0.003818,0.013857,-0.009345,0.000814,0.013745,-0.020935,-0.000994
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M6] rank=6 service=shippingservice-1 metric=istio_request_duration_milliseconds.grpc.200.0.0 baseline=0.34125 peak=16.9 signed_z=57.346 onset_bin=44 onset_rel_s=1627.031 persistence_bins=3
values_compact=delta:0,0.525,-0.525,0.525,0.2625,0,-0.2625,0,0,-0.525,0,0.525,-0.525,0.525,-0.525,0.525,-0.525,0.525,-0.525,0.525,-0.525,0,0,0.525,-0.525,0.525,-0.525,16.9,-0.525,-15.85,-0.525,0,0,0.525,-0.525,2.575,-2.05,0,-0.525,0.525
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M7] rank=7 service=istio-egressgateway-7bfdcc9d86-22q7z metric=istio_agent_go_memstats_mallocs baseline=6353.075 peak=11832.5 signed_z=56.659 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:6362,24.5,-71,-21,181.5,-239,150,42,0,156.5,-376,161.5,-137.5,93.5,67.5,-62.5,48.5,70.5,-280.5,119.5,377.5,-336.5,-126.5,138.5,-117,102,-15,51.5,5468,-4997.5,-342.5,-300.5,127.5,91.5,-66,188,-282.5,53.5,57.5,30
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M8] rank=8 service=istio-egressgateway-7bfdcc9d86-22q7z metric=istio_agent_go_memstats_heap_inuse_bytes baseline=10824704.0 peak=12312576.0 signed_z=54.895 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:10850304,0,-69632,57344,8192,-8192,-16384,-24576,28672,32768,-40960,49152,-40960,-32768,-32768,86016,-8192,-8192,-36864,24576,-69632,45056,-4096,32768,-8192,-12288,-32768,4096,1540096,-606208,-733184,-110592,-110592,118784,-20480,-20480,-61440,73728,-28672,-24576
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M9] rank=9 service=istio-egressgateway-7bfdcc9d86-22q7z metric=istio_agent_go_memstats_heap_idle_bytes baseline=54315622.4 peak=52797440.0 signed_z=-50.011 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:54259712,16384,86016,-57344,-8192,8192,16384,24576,-28672,-32768,40960,-49152,40960,32768,32768,-86016,8192,8192,36864,-24576,69632,-28672,-12288,-32768,8192,28672,16384,-4096,-1572864,606208,700416,159744,159744,-102400,-61440,36864,77824,-57344,12288,40960
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M10] rank=10 service=checkoutservice2-0 metric=container_network_receive_MB.eth0 baseline=0.077836 peak=0.588593 signed_z=49.312 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.083346,-0.005122,-0.004265,0.011905,-0.011409,-0.004143,0.001102,0.009817,0,0.004195,0.01487,-0.025834,-0.003979,-0.004859,0.026609,-0.03725,0.010001,0.02212,-0.014657,0.016205,-0.016078,0.024244,0.491775,-0.516868,-0.001479,0.009303,-0.010038,0.038001,-0.037834,-0.018481,0.030664,0.008688,0.00969,-0.013388,-0.041991,0.053949,-0.031872,-0.001699,0.005475,0.020162
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M11] rank=11 service=istio-ingressgateway-565bffd4d-4nr6v metric=istio_agent_go_memstats_heap_objects baseline=37128.75 peak=43262.5 signed_z=43.793 onset_bin=62 onset_rel_s=2285.156 persistence_bins=2
values_compact=delta:37267,61.5,-99,-38,281.5,-226,-61,56.5,-162.5,35,20,-65,-25,-28.5,6.5,-2.5,-43.5,131,-160.5,-75,-185.5,209.5,39.5,-213.5,-6,44,-54.5,172.5,-113,381.5,-431.5,10.5,33,28,-56.5,-80.5,-45,105,-40,6592.5
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M12] rank=12 service=paymentservice2-0 metric=container_memory_working_set_MB baseline=102.787565 peak=98.953125 signed_z=-42.807 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:102.626953,0.070313,0.203125,-0.072266,-0.173828,0.134765,0.091797,0.064453,-0.164062,-0.025391,0.085938,0.052734,-0.127604,-0.005208,-0.007813,0.138672,-0.269531,0.208984,-0.099609,0.060547,-0.199219,0.095052,0.172526,-2.074219,1.914063,0.134766,0.060546,-0.269531,0.044922,0.164063,-0.119141,-3.763672,3.789063,0.091796,-0.042968,-0.103516,-0.373047,0.607422,-0.179687,-0.013672
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[1560.0,2340.0]

=== LOG SUMMARY ===
{"entries":[{"change_pct":-68.8,"n_during":10,"n_pre":32,"service":"redis-cart-0"},{"change_pct":-55.7,"n_during":18258,"n_pre":41261,"service":"frontend-2"},{"change_pct":-54.0,"n_during":813,"n_pre":1768,"service":"checkoutservice-0"},{"change_pct":-53.4,"n_during":1466,"n_pre":3146,"service":"adservice-1"},{"change_pct":-53.4,"n_during":10232,"n_pre":21978,"service":"currencyservice-2"},{"change_pct":-53.3,"n_during":1468,"n_pre":3146,"service":"adservice-0"},{"change_pct":-53.3,"n_during":1622,"n_pre":3474,"service":"adservice-2"},{"change_pct":-53.2,"n_during":10251,"n_pre":21902,"service":"currencyservice-0"}],"mode":"volume","omitted_services":23,"service_count":31}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":-100.0,"error_pct":0.0,"p95_during_ms":0.0,"p95_pre_ms":1.0,"service":"cartservice-2","spans":7678},{"delta_pct":-53.8,"error_pct":0.0,"p95_during_ms":46.166399999999996,"p95_pre_ms":100.02,"service":"frontend2-0","spans":82053},{"delta_pct":-51.5,"error_pct":0.0,"p95_during_ms":48.484399999999994,"p95_pre_ms":99.886,"service":"frontend-1","spans":38737},{"delta_pct":-51.4,"error_pct":0.0,"p95_during_ms":48.5786,"p95_pre_ms":99.90035,"service":"frontend-0","spans":45427},{"delta_pct":-51.2,"error_pct":0.0,"p95_during_ms":48.781,"p95_pre_ms":99.958,"service":"frontend-2","spans":42933},{"delta_pct":-11.8,"error_pct":0.0,"p95_during_ms":4.456199999999999,"p95_pre_ms":5.053099999999999,"service":"productcatalogservice-1","spans":22629},{"delta_pct":-11.8,"error_pct":0.0,"p95_during_ms":4.416,"p95_pre_ms":5.0058,"service":"productcatalogservice-2","spans":22625},{"delta_pct":-10.7,"error_pct":0.0,"p95_during_ms":4.968,"p95_pre_ms":5.560599999999998,"service":"productcatalogservice-0","spans":22631}],"omitted_services":32,"service_count":40}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=15 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":1200.0,"rank":1,"service":"node-5","severity_z":22.757},{"evidence_source":"metric","onset_rel_s":1260.0,"rank":2,"service":"checkoutservice","severity_z":71.907},{"evidence_source":"metric","onset_rel_s":1260.0,"rank":3,"service":"recommendationservice","severity_z":23.233},{"evidence_source":"metric","onset_rel_s":1320.0,"rank":4,"service":"checkoutservice2","severity_z":49.312},{"evidence_source":"metric","onset_rel_s":1320.0,"rank":5,"service":"node-6","severity_z":39.795},{"evidence_source":"metric","onset_rel_s":1380.0,"rank":6,"service":"paymentservice","severity_z":249.569},{"evidence_source":"metric","onset_rel_s":1500.0,"rank":7,"service":"cartservice","severity_z":36.369},{"evidence_source":"metric","onset_rel_s":1620.0,"rank":8,"service":"shippingservice","severity_z":57.346},{"evidence_source":"metric","onset_rel_s":1680.0,"rank":9,"service":"shippingservice2","severity_z":283.074},{"evidence_source":"metric","onset_rel_s":1680.0,"rank":10,"service":"istio-egressgateway","severity_z":56.659},{"evidence_source":"metric","onset_rel_s":1800.0,"rank":11,"service":"currencyservice","severity_z":25.786},{"evidence_source":"metric","onset_rel_s":1860.0,"rank":12,"service":"paymentservice2","severity_z":170.499},{"evidence_source":"metric","onset_rel_s":2280.0,"rank":13,"service":"node-1","severity_z":34.73},{"evidence_source":"metric","onset_rel_s":2340.0,"rank":14,"service":"istio-ingressgateway","severity_z":43.793}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"cartservice","caller":"checkoutservice"},{"callee":"currencyservice","caller":"checkoutservice"},{"callee":"paymentservice","caller":"checkoutservice"},{"callee":"shippingservice","caller":"checkoutservice"},{"callee":"paymentservice2","caller":"checkoutservice2"},{"callee":"shippingservice2","caller":"checkoutservice2"}]

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
"checkoutservice",
"paymentservice",
"shippingservice",
"cartservice"
],
"reason": "node-5 is the root cause as it is the earliest anomaly in the propagation chain (rank 1, onset 1200s), preceding the degradation of checkoutservice and other dependent microservices.",
"confidence": "high"
}
