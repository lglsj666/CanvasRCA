# Causal SFT pilot evaluation — INC-886954DD634B — adapter

Private evaluator case id: `aiops2025_8c1e905b-592`

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

[image: RQs/RQ0/results/causal_integration_sft_v1/data/cases/INC-886954DD634B/dashboard.png]

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
opaque_id: INC-886954DD634B
observation_window={"duration_rel_s":1800.0,"source_metric_rows":31}
selection_summary={"candidate_count":60,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":492,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","cartservice","cartservice-0","cartservice-1","cartservice-2","checkoutservice","checkoutservice-0","checkoutservice-1","checkoutservice-2","currencyservice","currencyservice-0","currencyservice-1","currencyservice-2","emailservice","emailservice-0","emailservice-1","emailservice-2","example-ant-10-29184000-wx4rn","example-ant-29184000-cgbbl","frontend","frontend-0","frontend-1","frontend-2","hipstershop","k8s-master1","k8s-master2","k8s-master3","node-1","node-2","node-3","node-4","node-5","node-6","node-7","node-8","paymentservice","paymentservice-0","paymentservice-1","paymentservice-2","productcatalogservice","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","recommendationservice","recommendationservice-0","recommendationservice-1","recommendationservice-2","redis","redis-cart","redis-cart-0","shippingservice","shippingservice-0","shippingservice-1","shippingservice-2","tidb-pd","tidb-tidb","tidb-tikv"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[14.062,42.188,70.312,98.438,126.562,154.688,182.812,210.938,239.062,267.188,295.312,323.438,351.562,379.688,407.812,435.938,464.062,492.188,520.312,548.438,576.562,604.688,632.812,660.938,689.062,717.188,745.312,773.438,801.562,829.688,857.812,885.938,914.062,942.188,970.312,998.438,1026.562,1054.688,1082.812,1110.938,1139.062,1167.188,1195.312,1223.438,1251.562,1279.688,1307.812,1335.938,1364.062,1392.188,1420.312,1448.438,1476.562,1504.688,1532.812,1560.938,1589.062,1617.188,1645.312,1673.438,1701.562,1729.688,1757.812,1785.938]
[M1] rank=1 service=adservice-2 metric=pod_memory_working_set_bytes baseline=6.268 peak=8650139.07 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,94.02,-94.02,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,8650139.07,-8650139.07,0,0,0,0,0
missing_mask_bits=0101010101010101101010101010101101010101010101011010101010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1
[M2] rank=2 service=frontend-1 metric=rrt baseline=12681.740667 peak=23402084.13 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:12374.56,123.07,498.93,-1117.66,1791.33,-1172.4,810.3,-1040.27,1289.38,-1604.78,1936.69,-2225.07,1614.41,-1144.91,125.83,108760.61,10650752.97,-1961277.05,-7610184.68,8160406.95,-3459775.45,-593242.47,-184748.49,-3072241.98,572755.82,2155704.85,18622913.64,-18354476.91,5675706.42,-5826673.24,-3236564.54
missing_mask_bits=0101010101010101101010101010101101010101010101011010101010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1
[M3] rank=3 service=frontend-2 metric=rrt baseline=12536.450667 peak=12646062.54 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:12407.27,88.17,146.01,-486.74,473.93,410.37,-266.16,-26.55,41.61,57.44,-670.07,925.67,-1328.84,1382.09,-1828.91,124561.75,3160063.86,1621652.21,7728459.43,-9943350.76,1046075.83,-2311197.12,2258381.42,-1350423.09,1898218.68,-2534499.81,-152581.25,191311.38,3382605.89,3700625.97,-7481278.04
missing_mask_bits=0101010101010101101010101010101101010101010101011010101010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1
[M4] rank=4 service=frontend metric=rrt baseline=12587.104 peak=6833574.21 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:12392.71,103.61,296.24,-753.61,980.49,-206.72,159.13,-433.43,555.55,-648.6,483.18,-485.36,-3.4,252.12,-991.1,115956.5,4829587.39,1695476.36,-4232043.5,2406060.81,-151268.26,-2172641.48,1730178.72,-2048383.19,1270374.69,-991825.76,894507.97,-922001.74,4397894.89,-195394.29,-5153698.76
missing_mask_bits=0101010101010101101010101010101101010101010101011010101010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1
[M5] rank=5 service=hipstershop metric=rrt baseline=7484.721333 peak=3153288.72 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:7428.39,-55.81,229.92,-354.83,297.64,176.1,-153.51,-174.46,518.06,-425.26,116.64,-124.33,-150.79,300.58,-671.99,84520.12,2140353.25,-513342.56,-412711.41,733407.52,-136292.33,-804268.17,412988.71,-466471.82,321475.54,-158705.84,478383.95,-567500.66,903107.51,1131388.56,-2552065.44
missing_mask_bits=0101010101010101101010101010101101010101010101011010101010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1
[M6] rank=6 service=node-2 metric=node_filesystem_usage_rate baseline=29.885 peak=29.89 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:29.885,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.005,0,0,0,0
missing_mask_bits=0101010101010101101010101010101101010101010101011010101010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1
[M7] rank=7 service=productcatalogservice-0 metric=rrt baseline=7193.383333 peak=3175209.13 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:7139.78,143.93,-266.29,-75.14,634.21,-118.01,-32.84,-286.52,-72.4,138.5,182.99,-137.4,-115.08,-76.99,-246.34,286266.05,1515611.34,722127.66,-737008.6,613176.01,328736.69,-1096236.24,871647.66,-401825.51,-220325.78,199061.12,215885.77,-231343.99,301198.66,801425.89,-2719381.9
missing_mask_bits=0101010101010101101010101010101101010101010101011010101010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1
[M8] rank=8 service=productcatalogservice-0 metric=rrt_max baseline=35680.466667 peak=32036735.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:29200,-2013,9906,-5993,37803,-12633,-30730,3336,1793,2227,4691,-1530,-8460,4990,1058,31513123,422664,2166,48208,-190635,123384,54897,-24175,53458,-169686,53115,47153,53729,-306250,320318,-6258
missing_mask_bits=0101010101010101101010101010101101010101010101011010101010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1
[M9] rank=9 service=productcatalogservice metric=rrt baseline=7185.852 peak=3175209.13 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:7135.11,150.22,-271.24,-74.65,614.38,-103.81,-37.9,-276.94,-72.42,133.69,187.42,-143.85,-114.13,-79.56,-238.88,267978.55,1533903.8,722127.66,-737008.6,613176.01,328736.69,-1096236.24,871647.66,-401825.51,-220325.78,199061.12,215885.77,-231343.99,301198.66,801425.89,-2719381.9
missing_mask_bits=0101010101010101101010101010101101010101010101011010101010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1
[M10] rank=10 service=productcatalogservice metric=rrt_max baseline=35680.466667 peak=32036735.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:29200,-2013,9906,-5993,37803,-12633,-30730,3336,1793,2227,4691,-1530,-8460,4990,1058,31513123,422664,2166,48208,-190635,123384,54897,-24175,53458,-169686,53115,47153,53729,-306250,320318,-6258
missing_mask_bits=0101010101010101101010101010101101010101010101011010101010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1
[M11] rank=11 service=tidb-tidb metric=qps baseline=0.0 peak=0.16 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.16
missing_mask_bits=0101010101010101101010101010101101111111111111111111111111111111
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
[M12] rank=12 service=cartservice metric=error_ratio baseline=0.0 peak=9.38 signed_z=857.698 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,9.38,-9.38,8.96,-8.96,0,0,0,0,0,0,0,0,0,3.4
missing_mask_bits=0101010101010101101010101010101101010101010101011010101010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[900.0,1140.0]

=== LOG SUMMARY ===
{"entries":[{"error_logs":1387,"error_pct":100.0,"service":"productcatalogservice-0","total_logs":1387},{"error_logs":530,"error_pct":4.82,"service":"frontend-2","total_logs":11005},{"error_logs":375,"error_pct":4.71,"service":"frontend-1","total_logs":7964},{"error_logs":365,"error_pct":4.98,"service":"frontend-0","total_logs":7328},{"error_logs":5,"error_pct":100.0,"service":"productcatalogservice-2","total_logs":5},{"error_logs":5,"error_pct":100.0,"service":"productcatalogservice-1","total_logs":5}],"mode":"errors","omitted_services":20,"service_count":26}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":835387.9,"error_pct":73.65,"p95_during_ms":130925.96664999999,"p95_pre_ms":15.670599999999999,"service":"productcatalogservice","spans":33901},{"delta_pct":62037.1,"error_pct":12.54,"p95_during_ms":59999.60995,"p95_pre_ms":96.56,"service":"frontend","spans":77489},{"delta_pct":-43.2,"error_pct":10.14,"p95_during_ms":73.8451,"p95_pre_ms":130.11494999999994,"service":"checkoutservice","spans":3248},{"delta_pct":-9.6,"error_pct":0.0,"p95_during_ms":0.4025999999999999,"p95_pre_ms":0.44554999999999995,"service":"shippingservice","spans":1754},{"delta_pct":-7.6,"error_pct":0.0,"p95_during_ms":0.88755,"p95_pre_ms":0.9609999999999999,"service":"emailservice","spans":289},{"delta_pct":7.1,"error_pct":0.0,"p95_during_ms":4.140349999999995,"p95_pre_ms":3.867199999999999,"service":"redis","spans":6719},{"delta_pct":-4.6,"error_pct":0.0,"p95_during_ms":5.27705,"p95_pre_ms":5.52925,"service":"recommendationservice","spans":9066},{"delta_pct":1.6,"error_pct":0.0,"p95_during_ms":5.357849999999999,"p95_pre_ms":5.275649999999999,"service":"cartservice","spans":6244}],"omitted_services":0,"service_count":8}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=10 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":900.0,"rank":1,"service":"tidb-tidb","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":900.0,"rank":2,"service":"recommendationservice","severity_z":35.135},{"evidence_source":"metric","onset_rel_s":900.0,"rank":3,"service":"redis-cart","severity_z":34.723},{"evidence_source":"metric","onset_rel_s":900.0,"rank":4,"service":"tidb-pd","severity_z":28.312},{"evidence_source":"metric","onset_rel_s":900.0,"rank":5,"service":"tidb-tikv","severity_z":23.28},{"evidence_source":"trace","onset_rel_s":918.6,"rank":6,"service":"productcatalogservice","severity_z":999.0},{"evidence_source":"trace","onset_rel_s":956.4,"rank":7,"service":"frontend","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":960.0,"rank":8,"service":"hipstershop","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1020.0,"rank":9,"service":"cartservice","severity_z":857.698},{"evidence_source":"metric","onset_rel_s":1440.0,"rank":10,"service":"adservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1560.0,"rank":11,"service":"node-2","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1560.0,"rank":12,"service":"node-1","severity_z":274.108},{"evidence_source":"metric","onset_rel_s":1560.0,"rank":13,"service":"node-8","severity_z":39.433},{"evidence_source":"metric","onset_rel_s":1740.0,"rank":14,"service":"shippingservice","severity_z":857.698}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"cartservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"frontend"},{"callee":"recommendationservice","caller":"frontend"},{"callee":"shippingservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"recommendationservice"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

## Assistant

{"confidence":"high","reason":"productcatalogservice-0 is the root cause because it exhibits 100% error logs and extreme latency spikes (p95 > 130s) that propagate to frontend and hipstershop, while the earlier onset of tidb-tidb is a benign anomaly (QPS rising from 0 to 0.16) unrelated to the application fault.","services":["productcatalogservice-0","productcatalogservice","frontend","hipstershop","cartservice"]}

## Result

```json
{
  "record_type": "episode",
  "dataset": "aiops2025",
  "case_id": "aiops2025_8c1e905b-592",
  "opaque_incident_id": "INC-886954DD634B",
  "stage_partition": "development_heldout",
  "condition": "adapter",
  "status": "ok",
  "error": null,
  "parse_ok": true,
  "predicted": [
    "productcatalogservice-0",
    "productcatalogservice",
    "frontend",
    "hipstershop",
    "cartservice"
  ],
  "rank": null,
  "mrr": 0.0,
  "ac1": 0.0,
  "ac3": 0.0,
  "ac5": 0.0,
  "avg3": 0.0,
  "avg5": 0.0,
  "input_tokens": 10564,
  "output_tokens": 107,
  "total_tokens": 10671,
  "preflight_input_tokens": 10564,
  "server_token_count_match": true,
  "wall_time_s": 11.870892524719238,
  "gpu_active_time_s_sampled": 0.25,
  "peak_gpu_memory_mib_sampled": 67460.0,
  "gpu_samples": 1,
  "gpu_sampling_interval_s": 0.25
}
```
