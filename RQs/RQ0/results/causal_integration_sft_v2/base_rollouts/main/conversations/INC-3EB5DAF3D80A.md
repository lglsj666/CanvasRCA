# Causal SFT v2 base rollout — INC-3EB5DAF3D80A

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

[image: RQs/RQ0/results/causal_integration_sft_v1/data/cases/INC-3EB5DAF3D80A/dashboard.png]

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
opaque_id: INC-3EB5DAF3D80A
observation_window={"duration_rel_s":2340.0,"source_metric_rows":40}
selection_summary={"candidate_count":63,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":1425,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","adservice-grpc","adservice-http","adservice2","adservice2-0","cartservice-0","cartservice-1","cartservice-2","cartservice-grpc","cartservice2-0","checkoutservice-0","checkoutservice-1","checkoutservice-2","checkoutservice-grpc","checkoutservice2-0","currencyservice-0","currencyservice-1","currencyservice-2","currencyservice-grpc","currencyservice2-0","emailservice-0","emailservice-1","emailservice-2","emailservice-grpc","emailservice2-0","frontend-0","frontend-1","frontend-2","frontend-http","frontend2-0","istio-egressgateway-7bfdcc9d86-22q7z","istio-ingressgateway-565bffd4d-4nr6v","node-1","node-2","node-3","node-4","node-5","node-6","paymentservice-0","paymentservice-1","paymentservice-2","paymentservice-grpc","paymentservice2-0","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","productcatalogservice-grpc","productcatalogservice2-0","recommendationservice-0","recommendationservice-1","recommendationservice-2","recommendationservice-grpc","recommendationservice2-0","redis-cart-0","redis-cart2-0","shippingservice-0","shippingservice-1","shippingservice-2","shippingservice-grpc","shippingservice2-0"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[18.281,54.844,91.406,127.969,164.531,201.094,237.656,274.219,310.781,347.344,383.906,420.469,457.031,493.594,530.156,566.719,603.281,639.844,676.406,712.969,749.531,786.094,822.656,859.219,895.781,932.344,968.906,1005.469,1042.031,1078.594,1115.156,1151.719,1188.281,1224.844,1261.406,1297.969,1334.531,1371.094,1407.656,1444.219,1480.781,1517.344,1553.906,1590.469,1627.031,1663.594,1700.156,1736.719,1773.281,1809.844,1846.406,1882.969,1919.531,1956.094,1992.656,2029.219,2065.781,2102.344,2138.906,2175.469,2212.031,2248.594,2285.156,2321.719]
[M1] rank=1 service=adservice2 metric=java_lang_Memory_ObjectPendingFinalizationCount baseline=0.0 peak=1.083333 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1.083333,-1.083333,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M2] rank=2 service=adservice2 metric=jvm_classes_loaded baseline=5163.0 peak=0.0 signed_z=-999.0 onset_bin=36 onset_rel_s=1334.531 persistence_bins=18
values_compact=delta:5163,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-5163,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M3] rank=3 service=adservice metric=jvm_classes_loaded baseline=5181.0 peak=0.0 signed_z=-999.0 onset_bin=36 onset_rel_s=1334.531 persistence_bins=18
values_compact=delta:5181,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-5181,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M4] rank=4 service=emailservice-1 metric=container_fs_inodes./dev/vda1 baseline=0.0 peak=1.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,-1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M5] rank=5 service=emailservice-1 metric=container_fs_usage_MB./dev/vda1 baseline=38.255664 peak=10662.640625 signed_z=999.0 onset_bin=41 onset_rel_s=1517.344 persistence_bins=15
values_compact=delta:38.253906,0,0,0,0,0,0,0,0,0,0,0.003906,0,0,0,0,0,0,0,0,10624.382813,-6109.934896,-3232.190104,-1282.257813,0,0.003907,0,0,0,0,0,0,0,0,0,0,0,0.001302,0.002604,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M6] rank=6 service=frontend-2 metric=container_cpu_cfs_throttled_seconds baseline=0.0 peak=0.004613 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.004613,-0.004613,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M7] rank=7 service=node-1 metric=system.disk.pct_usage baseline=40.69 peak=40.71 signed_z=999.0 onset_bin=41 onset_rel_s=1517.344 persistence_bins=15
values_compact=delta:40.69,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.01,0,0,0,0.01,0,-0.01,0,0,0,0,0,0.01,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M8] rank=8 service=node-5 metric=system.disk.total baseline=4067313956.570001 peak=5144867840.0 signed_z=999.0 onset_bin=36 onset_rel_s=1334.531 persistence_bins=6
values_compact=delta:4067313956.57,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1077553883.43,0,0,0,0,0,0,-1077553883.43,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M9] rank=9 service=node-5 metric=system.fs.inodes.free baseline=3193038438.3995 peak=4178191872.0 signed_z=999.0 onset_bin=36 onset_rel_s=1334.531 persistence_bins=18
values_compact=delta:3193403392,244589.71,-95085.71,-138678.86,-295497.14,-136630.86,255414.86,-107373.71,-118784,-54710.86,-413403.43,604452.57,-114102.86,-118491.42,-131657.15,311881.15,-115565.72,-137216,-288475.43,-134875.43,323876.58,985448813.71,-920320,-1092608,-1236480,-167680,-886016,-1118976,-984554276.57,-1147465.14,2032493.71,-132827.43,-118491.43,-227913.14,183734.86,-167058.29,-93037.71,-118784,213284.57,-145993.14
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M10] rank=10 service=node-5 metric=system.fs.inodes.in_use baseline=0.98 peak=0.86 signed_z=-999.0 onset_bin=36 onset_rel_s=1334.531 persistence_bins=6
values_compact=delta:0.98,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-0.12,0,0,0,0,0,0,0.12,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M11] rank=11 service=node-5 metric=system.fs.inodes.total baseline=3194500959.0855 peak=4179944960.0 signed_z=999.0 onset_bin=36 onset_rel_s=1334.531 persistence_bins=18
values_compact=delta:3194865956.57,244589.72,-95378.29,-138386.29,-295497.14,-136630.86,255414.86,-107373.71,-118784,-54710.86,-413403.43,604452.57,-114102.85,-118491.43,-131949.72,311881.15,-115273.15,-137216,-288475.43,-134875.42,323584,985739629.71,-921088,-1092096,-1236480,-167680,-886272,-1118464,-984844800,-1147465.14,2032493.71,-132827.43,-118491.43,-227913.14,183734.86,-167058.29,-93037.71,-118784,213284.57,-145993.14
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M12] rank=12 service=node-5 metric=system.fs.inodes.used baseline=1462516.3645 peak=1752795.0 signed_z=999.0 onset_bin=36 onset_rel_s=1334.531 persistence_bins=18
values_compact=delta:1462501.86,8.85,-3.14,10.86,4.71,-17.28,4,18.57,-9.43,-20.57,16,9.14,-1.14,-14.57,10.57,3,7.28,0.86,-15.71,9.85,-3.71,290194.13,-2.25,8,33.75,0.37,11.38,29.62,-290120,8.29,-1.86,-19,7.71,-2,11.72,0.85,-8.85,0.85,-4,10.72
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[1200.0,2340.0]

=== LOG SUMMARY ===
{"entries":[{"change_pct":-16.7,"n_during":10,"n_pre":12,"service":"redis-cart-0"},{"change_pct":-11.7,"n_during":68,"n_pre":77,"service":"emailservice-0"},{"change_pct":-11.4,"n_during":11077,"n_pre":12508,"service":"frontend-2"},{"change_pct":-9.9,"n_during":676,"n_pre":750,"service":"adservice-1"},{"change_pct":-9.8,"n_during":902,"n_pre":1000,"service":"adservice-2"},{"change_pct":-9.7,"n_during":674,"n_pre":746,"service":"adservice-0"},{"change_pct":-9.6,"n_during":1435,"n_pre":1588,"service":"recommendationservice-2"},{"change_pct":-9.4,"n_during":5421,"n_pre":5983,"service":"cartservice-2"}],"mode":"volume","omitted_services":23,"service_count":31}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":49.5,"error_pct":0.0,"p95_during_ms":0.11599999999999727,"p95_pre_ms":0.07759999999999996,"service":"shippingservice-0","spans":335},{"delta_pct":29.9,"error_pct":0.0,"p95_during_ms":0.02,"p95_pre_ms":0.015399999999999976,"service":"adservice-0","spans":708},{"delta_pct":15.8,"error_pct":0.0,"p95_during_ms":0.17439999999999997,"p95_pre_ms":0.15059999999999998,"service":"paymentservice-0","spans":47},{"delta_pct":-12.5,"error_pct":0.0,"p95_during_ms":0.08859999999999996,"p95_pre_ms":0.1011999999999996,"service":"shippingservice-1","spans":334},{"delta_pct":-8.3,"error_pct":0.0,"p95_during_ms":0.077,"p95_pre_ms":0.084,"service":"shippingservice2-0","spans":434},{"delta_pct":7.6,"error_pct":0.0,"p95_during_ms":0.1689,"p95_pre_ms":0.157,"service":"paymentservice-2","spans":49},{"delta_pct":-5.5,"error_pct":0.0,"p95_during_ms":0.17049999999999998,"p95_pre_ms":0.1805,"service":"paymentservice2-0","spans":62},{"delta_pct":5.0,"error_pct":0.0,"p95_during_ms":0.021,"p95_pre_ms":0.02,"service":"adservice2-0","spans":919}],"omitted_services":31,"service_count":39}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=16 omitted_edges=1
[{"evidence_source":"metric","onset_rel_s":1200.0,"rank":1,"service":"emailservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1260.0,"rank":2,"service":"adservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1260.0,"rank":3,"service":"node-5","severity_z":999.0},{"evidence_source":"trace","onset_rel_s":1389.6,"rank":4,"service":"paymentservice","severity_z":33.421},{"evidence_source":"metric","onset_rel_s":1500.0,"rank":5,"service":"recommendationservice","severity_z":111.333},{"evidence_source":"trace","onset_rel_s":1535.4,"rank":6,"service":"adservice2","severity_z":4.35},{"evidence_source":"metric","onset_rel_s":1620.0,"rank":7,"service":"node-2","severity_z":26.269},{"evidence_source":"metric","onset_rel_s":1680.0,"rank":8,"service":"node-1","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1740.0,"rank":9,"service":"cartservice","severity_z":86.939},{"evidence_source":"metric","onset_rel_s":1740.0,"rank":10,"service":"checkoutservice","severity_z":44.608},{"evidence_source":"metric","onset_rel_s":1800.0,"rank":11,"service":"istio-egressgateway","severity_z":30.014},{"evidence_source":"metric","onset_rel_s":1860.0,"rank":12,"service":"frontend","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1860.0,"rank":13,"service":"paymentservice2","severity_z":392.803},{"evidence_source":"trace","onset_rel_s":2315.4,"rank":14,"service":"shippingservice","severity_z":3.076}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"cartservice","caller":"checkoutservice"},{"callee":"emailservice","caller":"checkoutservice"},{"callee":"paymentservice","caller":"checkoutservice"},{"callee":"shippingservice","caller":"checkoutservice"},{"callee":"adservice","caller":"frontend"},{"callee":"cartservice","caller":"frontend"},{"callee":"checkoutservice","caller":"frontend"},{"callee":"recommendationservice","caller":"frontend"},{"callee":"shippingservice","caller":"frontend"}]

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
"adservice",
"adservice2",
"emailservice",
"node-1"
],
"reason": "Node-5 is the root cause, evidenced by the earliest simultaneous onset of critical filesystem anomalies (disk total size and inode count jumps) at t=1334s, which coincides with the immediate JVM crash (classes_loaded dropping to 0) of the adservice pods hosted on that node.",
"confidence": "high"
}
