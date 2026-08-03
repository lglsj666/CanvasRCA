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
opaque_id: INC-2072E869C8A0
observation_window={"duration_rel_s":2040.0,"source_metric_rows":35}
selection_summary={"candidate_count":60,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":546,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","cartservice","cartservice-0","cartservice-1","cartservice-2","checkoutservice","checkoutservice-0","checkoutservice-1","checkoutservice-2","currencyservice","currencyservice-0","currencyservice-1","currencyservice-2","emailservice","emailservice-0","emailservice-1","emailservice-2","example-ant-10-29172480-4qwqp","example-ant-29172480-8w684","frontend","frontend-0","frontend-1","frontend-2","hipstershop","k8s-master1","k8s-master2","k8s-master3","node-1","node-2","node-3","node-4","node-5","node-6","node-7","node-8","paymentservice","paymentservice-0","paymentservice-1","paymentservice-2","productcatalogservice","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","recommendationservice","recommendationservice-0","recommendationservice-1","recommendationservice-2","redis","redis-cart","redis-cart-0","shippingservice","shippingservice-0","shippingservice-1","shippingservice-2","tidb-pd","tidb-tidb","tidb-tikv"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[15.938,47.812,79.688,111.562,143.438,175.312,207.188,239.062,270.938,302.812,334.688,366.562,398.438,430.312,462.188,494.062,525.938,557.812,589.688,621.562,653.438,685.312,717.188,749.062,780.938,812.812,844.688,876.562,908.438,940.312,972.188,1004.062,1035.938,1067.812,1099.688,1131.562,1163.438,1195.312,1227.188,1259.062,1290.938,1322.812,1354.688,1386.562,1418.438,1450.312,1482.188,1514.062,1545.938,1577.812,1609.688,1641.562,1673.438,1705.312,1737.188,1769.062,1800.938,1832.812,1864.688,1896.562,1928.438,1960.312,1992.188,2024.062]
[M1] rank=1 service=adservice-0 metric=pod_memory_working_set_bytes baseline=7.484118 peak=8545351.82 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,127.23,-127.23,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,8545351.82,-8545351.82,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010101010101010010101010101010100101010101010100101010101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M2] rank=2 service=adservice-2 metric=pod_memory_working_set_bytes baseline=4.069412 peak=12067857.54 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,69.18,-69.18,0,0,0,9000418.45,-9000418.45,0,0,0,0,0,0,0,0,12067857.54,-12067857.54,6831012.71,-6831012.71,0,0,0,0
missing_mask_bits=0010101010101010010101010101010100101010101010100101010101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M3] rank=3 service=tidb-pd metric=store_unhealth_count baseline=0.0 peak=1.0 signed_z=999.0 onset_bin=47 onset_rel_s=1514.062 persistence_bins=10
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010101010101010010101010101010100101010101010100101010101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M4] rank=4 service=tidb-tidb metric=memory_usage baseline=1024651986.823529 peak=618508288.0 signed_z=-163.508 onset_bin=32 onset_rel_s=1035.938 persistence_bins=18
values_compact=delta:1020805120,0,0,0,0,5201920,270336,0,0,0,0,0,0,0,0,0,0,-173293568,1073152,-223412224,1077248,-7938048,1613824,1245184,0,-8134656,0,536576,536576,0,0,1077248,0,0,0
missing_mask_bits=0010101010101010010101010101010100101010101010100101010101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M5] rank=5 service=tidb-tidb metric=duration_avg baseline=0.054118 peak=20.13 signed_z=92.742 onset_bin=32 onset_rel_s=1035.938 persistence_bins=18
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.92,18.75,0.46,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010101010101010010101010101010100101010101010100101010101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M6] rank=6 service=node-6 metric=node_network_transmit_bytes_total baseline=3303.007647 peak=3371.27 signed_z=28.92 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:3307,-4,5,-6.33,-0.5,-0.37,-1.33,4.6,-1.14,0.74,-2.47,-0.6,0.13,2,1.23,2.84,-3.47,-2.53,2,0,0.27,1.4,-1.6,-2.87,71.27,-68.54,-2.13,4,-1.6,-1.87,3.2,-5.7,2.57,-1.67,0.87
missing_mask_bits=0010101010101010010101010101010100101010101010100101010101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M7] rank=7 service=hipstershop metric=client_error_ratio baseline=0.034706 peak=3.09 signed_z=22.817 onset_bin=47 onset_rel_s=1514.062 persistence_bins=5
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0.02,-0.02,0,0.57,-0.57,0,3.09,-3.09,0,1.42,-1.42,1.79,-1.18,-0.04,-0.57,0,0,0.58,0.92,-1.5,2.28,-2.24
missing_mask_bits=0010101010101010010101010101010100101010101010100101010101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M8] rank=8 service=node-5 metric=node_memory_MemAvailable_bytes baseline=10375874198.588236 peak=12228939776.0 signed_z=21.224 onset_bin=62 onset_rel_s=1992.188 persistence_bins=2
values_compact=delta:10418155520,-16723968,-6553600,107753472,-4993024,-258510848,30371840,-26800128,228610048,-21356544,-113274880,-6553600,-44625920,-3088384,204791808,-86876160,-20025344,-16396288,12984320,150470656,-122720256,-3825664,-13058048,75653120,7450624,43171840,1714909184,-14917632,-528384,10895360,-12808192,4481024,-4464640,-11190272,7839744
missing_mask_bits=0010101010101010010101010101010100101010101010100101010101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M9] rank=9 service=node-5 metric=node_memory_usage_rate baseline=36.174706 peak=25.13 signed_z=-21.224 onset_bin=62 onset_rel_s=1992.188 persistence_bins=2
values_compact=delta:35.92,0.1,0.04,-0.64,0.03,1.54,-0.18,0.16,-1.36,0.12,0.68,0.04,0.26,0.02,-1.22,0.52,0.12,0.1,-0.08,-0.9,0.73,0.03,0.07,-0.45,-0.04,-0.26,-10.22,0.08,0.01,-0.07,0.08,-0.03,0.03,0.07,-0.05
missing_mask_bits=0010101010101010010101010101010100101010101010100101010101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M10] rank=10 service=currencyservice-2 metric=rrt baseline=1329.077059 peak=3012.0 signed_z=16.458 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:1536.16,-343.33,214.97,-167.62,151.65,-262.73,227.65,8.5,-135.43,105.85,-103.86,231.69,-240.24,149.92,-0.79,0,0,0,0,14.61,0,-263,-69.75,0,0,-42.75,65.5,-8.25,0,265.75,-660.5,613,0,1725,-1578.5
missing_mask_bits=0010101010101010010101010101010100101010101010100101010101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M11] rank=11 service=cartservice-1 metric=client_error_ratio baseline=0.0 peak=38.71 signed_z=16.306 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,35.29,-35.29,0,35.29,-35.29,38.71,-38.71,0,0,0,0,0,37.5,-37.5,28.57,-28.57
missing_mask_bits=0010101010101010010101010101010100101010101010100101010101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M12] rank=12 service=cartservice metric=client_error_ratio baseline=0.0 peak=9.09 signed_z=16.306 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,7.89,-7.89,0,8.57,-8.57,8.89,-8.89,0,0,0,0,0,9.09,-9.09,7.79,-7.79
missing_mask_bits=0010101010101010010101010101010100101010101010100101010101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[1440.0,2040.0]

=== LOG SUMMARY ===
{"entries":[{"error_logs":602,"error_pct":100.0,"service":"productcatalogservice-2","total_logs":602},{"error_logs":554,"error_pct":3.46,"service":"frontend-2","total_logs":16031},{"error_logs":328,"error_pct":100.0,"service":"productcatalogservice-1","total_logs":328},{"error_logs":315,"error_pct":3.71,"service":"frontend-1","total_logs":8491},{"error_logs":24,"error_pct":3.5,"service":"frontend-0","total_logs":685},{"error_logs":3,"error_pct":100.0,"service":"productcatalogservice-0","total_logs":3}],"mode":"errors","omitted_services":21,"service_count":27}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":283284.1,"error_pct":70.67,"p95_during_ms":40290.1383,"p95_pre_ms":14.2175,"service":"productcatalogservice","spans":38061},{"delta_pct":44043.3,"error_pct":16.35,"p95_during_ms":40287.93965,"p95_pre_ms":91.26619999999998,"service":"frontend","spans":85255},{"delta_pct":-48.8,"error_pct":0.0,"p95_during_ms":78.41829999999999,"p95_pre_ms":153.258,"service":"checkoutservice","spans":3525},{"delta_pct":17.7,"error_pct":0.0,"p95_during_ms":0.5467500000000001,"p95_pre_ms":0.46459999999999996,"service":"shippingservice","spans":1981},{"delta_pct":-14.4,"error_pct":0.0,"p95_during_ms":2.9835999999999996,"p95_pre_ms":3.4865000000000004,"service":"cartservice","spans":6911},{"delta_pct":-13.4,"error_pct":0.0,"p95_during_ms":0.8548999999999999,"p95_pre_ms":0.9874999999999998,"service":"emailservice","spans":311},{"delta_pct":-5.5,"error_pct":0.0,"p95_during_ms":1.726099999999998,"p95_pre_ms":1.8262999999999994,"service":"redis","spans":7455},{"delta_pct":-0.2,"error_pct":0.0,"p95_during_ms":5.004749999999999,"p95_pre_ms":5.015,"service":"recommendationservice","spans":10156}],"omitted_services":0,"service_count":8}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=7 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":1140.0,"rank":1,"service":"tidb-tidb","severity_z":163.508},{"evidence_source":"metric","onset_rel_s":1140.0,"rank":2,"service":"hipstershop","severity_z":22.817},{"evidence_source":"metric","onset_rel_s":1260.0,"rank":3,"service":"adservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1440.0,"rank":4,"service":"node-6","severity_z":28.92},{"evidence_source":"metric","onset_rel_s":1440.0,"rank":5,"service":"cartservice","severity_z":16.306},{"evidence_source":"metric","onset_rel_s":1500.0,"rank":6,"service":"tidb-pd","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1560.0,"rank":7,"service":"node-5","severity_z":21.224},{"evidence_source":"metric","onset_rel_s":1920.0,"rank":8,"service":"paymentservice","severity_z":15.407},{"evidence_source":"metric","onset_rel_s":1920.0,"rank":9,"service":"k8s-master1","severity_z":11.712},{"evidence_source":"metric","onset_rel_s":1980.0,"rank":10,"service":"currencyservice","severity_z":16.458},{"evidence_source":"trace","onset_rel_s":2019.0,"rank":11,"service":"shippingservice","severity_z":10.477},{"evidence_source":"none","onset_rel_s":null,"rank":12,"service":"frontend","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":13,"service":"checkoutservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":14,"service":"recommendationservice","severity_z":0.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"cartservice","caller":"checkoutservice"},{"callee":"shippingservice","caller":"checkoutservice"},{"callee":"cartservice","caller":"frontend"},{"callee":"checkoutservice","caller":"frontend"},{"callee":"recommendationservice","caller":"frontend"},{"callee":"shippingservice","caller":"frontend"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

[excluded before optimizer]
