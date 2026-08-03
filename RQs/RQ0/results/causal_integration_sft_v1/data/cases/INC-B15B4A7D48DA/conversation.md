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
opaque_id: INC-B15B4A7D48DA
observation_window={"duration_rel_s":478.941,"source_metric_rows":1077}
selection_summary={"candidate_count":104,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":1012,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["loadgenerator","loadgenerator-77dc8db659-xdl5d","mysql","mysql-0","rabbitmq","rabbitmq-0","ts-admin-basic-info-service","ts-admin-basic-info-service-8489f5b9dd-6wr68","ts-admin-order-service","ts-admin-order-service-5b6c548fb5-xmljv","ts-admin-route-service","ts-admin-route-service-6b7fcc6f9b-rt7ts","ts-admin-travel-service","ts-admin-travel-service-7d4bb8dcb9-9qz9w","ts-admin-user-service","ts-admin-user-service-5bff4bdf86-2hzg5","ts-assurance-service","ts-assurance-service-5597965598-2kq8r","ts-auth-service","ts-auth-service-6d87cc4dc7-cbrh7","ts-avatar-service","ts-avatar-service-7c465d78b5-bj94l","ts-basic-service","ts-basic-service-6968d4ccd5-6ss64","ts-cancel-service","ts-cancel-service-6cf95f89fc-fscwk","ts-config-service","ts-config-service-5d4b464d85-sckkk","ts-consign-price-service","ts-consign-price-service-7d59bdd47d-6gsk2","ts-consign-service","ts-consign-service-848b6d5bcd-m9j8g","ts-contacts-service","ts-contacts-service-55cfbdfdc8-22s8m","ts-delivery-service","ts-delivery-service-d66597c7f-s999n","ts-execute-service","ts-execute-service-6687b7f74d-x47hv","ts-food-delivery-service","ts-food-delivery-service-bcb844d44-ntpnd","ts-food-service","ts-food-service-55f49f6b59-blt4n","ts-gateway-service","ts-gateway-service-7cc7b478fc-ljp6f","ts-inside-payment-service","ts-inside-payment-service-6d88d7f6b4-7hvr8","ts-news-service","ts-news-service-6d6c6d7855-lhxq6","ts-notification-service","ts-notification-service-596b87f8f6-rpxsm","ts-order-other-service","ts-order-other-service-5fc6774cd8-zl8c5","ts-order-service","ts-order-service-668587b48c-267k4","ts-payment-service","ts-payment-service-7679c6959c-fvj4q","ts-preserve-other-service","ts-preserve-other-service-6bf648d676-gb9cv","ts-preserve-service","ts-preserve-service-5d979f4b55-qgsqr","ts-price-service","ts-price-service-55957b666-nzzb7","ts-rebook-service","ts-rebook-service-79d845d787-hj9gm","ts-route-plan-service","ts-route-plan-service-6865bfcc6d-x962l","ts-route-service","ts-route-service-586ffc746-8z5ql","ts-seat-service","ts-seat-service-7b7c5f5d7d-6wqz5","ts-security-service","ts-security-service-5454c847f7-xjpgs","ts-station-food-service","ts-station-food-service-cb9656f7b-zqhrx","ts-station-service","ts-station-service-685fd4985f-vpnch","ts-ticket-office-service","ts-ticket-office-service-9c7b9d55b-zbz94","ts-train-food-service","ts-train-food-service-bdd545d98-rrjnw","ts-train-service","ts-train-service-7b96f444bf-xlb8h","ts-travel-plan-service","ts-travel-plan-service-b49559b55-tgld7","ts-travel-service","ts-travel-service-56c9999f79-shqq5","ts-travel2-service","ts-travel2-service-8557fd66df-vknjq","ts-ui-dashboard","ts-ui-dashboard-68fff76764-pt8b5","ts-user-service","ts-user-service-644dc6f8fb-r6fvs","ts-verification-code-service","ts-verification-code-service-595bc8dd8d-wn4s7","ts-voucher-service","ts-voucher-service-c745bfccb-d5lm9","ts-wait-order-service","ts-wait-order-service-779f77459-4tj7b","worker1","worker2","worker3","worker4","worker5","worker6"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[3.742,11.225,18.709,26.192,33.676,41.159,48.642,56.126,63.609,71.093,78.576,86.06,93.543,101.027,108.51,115.994,123.477,130.961,138.444,145.927,153.411,160.894,168.378,175.861,183.345,190.828,198.312,205.795,213.279,220.762,228.245,235.729,243.212,250.696,258.179,265.663,273.146,280.63,288.113,295.597,303.08,310.564,318.047,325.53,333.014,340.497,347.981,355.464,362.948,370.431,377.915,385.398,392.882,400.365,407.849,415.332,422.815,430.299,437.782,445.266,452.749,460.233,467.716,475.2]
[M1] rank=1 service=ts-order-service metric=hubble_http_request_duration_p90_seconds baseline=0.012004 peak=9.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.019,-0.0055,0.001075,-0.004848,-0.000053,-0.000332,0.000182,0.001163,0.026813,0,0.0275,8.935,-8.9795,-0.011,0,-0.0005
missing_mask_bits=1011101110111011101110111011101110111011101110111011101110111011
observed_counts_compact=csv:0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0
[M2] rank=2 service=ts-order-service metric=hubble_http_request_duration_p95_seconds baseline=0.014735 peak=9.5 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.022,-0.00275,0.000537,-0.009225,-0.000134,-0.000718,0.002341,0.002043,0.029656,0,0.03875,9.4175,-9.47725,-0.013,0,-0.00025
missing_mask_bits=1101110111011101110111011101110111011101110111011101110111011101
observed_counts_compact=csv:0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0
[M3] rank=3 service=ts-station-food-service metric=hubble_http_request_duration_p99_seconds baseline=0.024827 peak=0.0995 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.02485,0,0,-0.000021,0,-0.000016,0.000037,-0.0001,0.07475,-0.04975,-0.0398
missing_mask_bits=1101110111011101110111011101110111011111111111111110111111101111
observed_counts_compact=rle:0*2,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*16,1*1,0*7,1*1,0*4
[M4] rank=4 service=ts-seat-service metric=hubble_http_request_duration_p50_seconds baseline=0.01463 peak=2.093958 signed_z=507.934 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.025383,-0.01224,-0.000122,0.000103,-0.00036,-0.000081,-0.00005,0.001652,2.076548,-0.203708,0.122042,0.084791,-0.214875,-0.000333,0,0
missing_mask_bits=1110111011101110111011101110111011101110111011101110111011101110
observed_counts_compact=csv:0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1
[M5] rank=5 service=ts-ui-dashboard metric=hubble_http_request_duration_p90_seconds baseline=0.108156 peak=10.0 signed_z=498.758 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.140543,-0.030911,0.001185,-0.000259,-0.019163,-0.023413,0.045587,0.007181,0.08425,9.795,-9.45075,-0.4195,9.87025,-9.885
missing_mask_bits=1011101110111011101110111011101111111011111110111011101110111011
observed_counts_compact=rle:0*1,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*7,1*1,0*7,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*2
[M6] rank=6 service=ts-travel-service metric=hubble_http_request_duration_p50_seconds baseline=0.047231 peak=6.770833 signed_z=434.929 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.060096,-0.037313,0.024571,-0.019984,0.016156,0.00071,0.019911,0.004186,1.648334,-0.029167,5.083333,-4.770833,-1.959062,0.034062,1.5,-1.535
missing_mask_bits=1110111011101110111011101110111011101110111011101110111011101110
observed_counts_compact=csv:0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1
[M7] rank=7 service=loadgenerator metric=hubble_http_request_duration_p90_seconds baseline=0.215872 peak=7.5 signed_z=374.709 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.243684,-0.010559,-0.013681,-0.025244,-0.01045,0.01875,0.029239,-0.013202,-0.009251,0.240714,-0.2375,1.9875,-1.988571,7.288571,-7.285,0.035
missing_mask_bits=1110111011101110111011101110111011101110111011101110111011101110
observed_counts_compact=csv:0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1
[M8] rank=8 service=ts-delivery-service metric=k8s.pod.cpu_limit_utilization baseline=0.00204 peak=0.152279 signed_z=351.497 onset_bin=52 onset_rel_s=392.882 persistence_bins=3
values_compact=delta:0.003358,-0.000449,-0.000448,0.000119,0,-0.000092,-0.000093,-0.000158,-0.000159,-0.00009,-0.00009,0,-0.000164,0,-0.000111,0,0.000486,0,-0.000467,0,-0.000076,0,0.000038,0,0,0.000189,0,0.000122,0.000121,0.000082,0.000083,0.000222,0.000178,0,0,0.000515,-0.000498,0,0,0.000498,0,-0.00018,-0.00018,-0.000622,0.000365,0,0.000086,-0.000051,-0.000052,0,-0.000019,0,0.149816,0,0,-0.150352,0.000511,-0.000478,-0.000479,0.000022,0,-0.000054,0,0.00015
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M9] rank=9 service=ts-delivery-service metric=k8s.pod.cpu.node.utilization baseline=8e-05 peak=0.005948 signed_z=351.497 onset_bin=52 onset_rel_s=392.882 persistence_bins=3
values_compact=delta:0.000131,-0.000017,-0.000018,0.000005,0,-0.000004,-0.000003,-0.000007,-0.000006,-0.000003,-0.000004,0,-0.000006,0,-0.000005,0,0.000019,0,-0.000018,0,-0.000003,0,0.000002,0,0,0.000007,0,0.000005,0.000005,0.000003,0.000003,0.000009,0.000007,0,0,0.00002,-0.00002,0,0,0.00002,0,-0.000007,-0.000007,-0.000025,0.000015,0,0.000003,-0.000002,-0.000002,0,-0.000001,0,0.005852,0,0,-0.005873,0.00002,-0.000018,-0.000019,0.000001,0,-0.000002,0,0.000005
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M10] rank=10 service=ts-delivery-service metric=k8s.pod.cpu.usage baseline=0.010202 peak=0.761397 signed_z=351.497 onset_bin=52 onset_rel_s=392.882 persistence_bins=3
values_compact=delta:0.016788,-0.002243,-0.002242,0.000596,0,-0.000461,-0.000461,-0.000793,-0.000793,-0.000451,-0.000451,0,-0.000817,0,-0.000559,0,0.002434,0,-0.002337,0,-0.00038,0,0.000192,0,0,0.000944,0,0.000607,0.000606,0.000412,0.000412,0.001112,0.00089,0,0,0.002577,-0.00249,0,0,0.00249,0,-0.0009,-0.0009,-0.003114,0.001827,0,0.000428,-0.000255,-0.000256,0,-0.000095,0,0.74908,0,0,-0.751764,0.002557,-0.002392,-0.002392,0.000111,0,-0.00027,0,0.000747
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M11] rank=11 service=ts-delivery-service metric=container.cpu.usage baseline=0.010346 peak=0.66219 signed_z=309.268 onset_bin=51 onset_rel_s=385.398 persistence_bins=3
values_compact=delta:0.018702,-0.005647,0,-0.000284,-0.000284,-0.000219,-0.000218,-0.001319,0,-0.000966,-0.000966,0,0.000199,0,-0.000506,0.001328,0.001327,-0.001343,-0.001344,-0.000313,0,-0.000293,0,0.000578,0.000578,0.001698,0,-0.001081,-0.001081,0.002164,0,0.002152,0,-0.000793,0,0.00312,0,0.00002,0.000021,0.000482,0.000482,-0.003358,-0.000994,0,0,0.000246,0,0.00102,0,-0.001482,0,0.650564,0,-0.3269,-0.326901,0.00269,0,-0.000592,-0.000592,-0.001107,-0.001107,0,0.0001,0
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M12] rank=12 service=ts-seat-service metric=hubble_http_request_duration_p90_seconds baseline=0.028332 peak=4.385625 signed_z=210.021 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.08225,-0.053063,-0.00563,-0.005058,-0.000321,-0.00145,0.004517,-0.004232,2.377987,0.00275,0.023679,-0.007262,1.971458,-2.005762,-0.000113,0
missing_mask_bits=1011101110111011101110111011101110111011101110111011101110111011
observed_counts_compact=csv:0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[231.81536865234375,441.81536865234375]

=== LOG SUMMARY ===
{"entries":[{"error_logs":286,"error_pct":17.13,"service":"ts-food-service","total_logs":1670},{"error_logs":96,"error_pct":25.0,"service":"ts-notification-service","total_logs":384},{"error_logs":95,"error_pct":25.0,"service":"ts-delivery-service","total_logs":380},{"error_logs":48,"error_pct":2.81,"service":"ts-preserve-service","total_logs":1710},{"error_logs":48,"error_pct":1.11,"service":"ts-order-service","total_logs":4334}],"mode":"errors","omitted_services":25,"service_count":30}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":9977.7,"error_pct":0.0,"p95_during_ms":2819.1308743,"p95_pre_ms":27.974039299999994,"service":"ts-seat-service","spans":9505},{"delta_pct":3224.4,"error_pct":0.0,"p95_during_ms":5581.7157366,"p95_pre_ms":167.90335899999994,"service":"ts-travel2-service","spans":3959},{"delta_pct":2691.5,"error_pct":0.0,"p95_during_ms":20860.3599664,"p95_pre_ms":747.2759070999999,"service":"ts-route-plan-service","spans":1200},{"delta_pct":2633.0,"error_pct":0.0,"p95_during_ms":5830.143959799995,"p95_pre_ms":213.32592760000017,"service":"ts-travel-service","spans":6210},{"delta_pct":2556.7,"error_pct":0.0,"p95_during_ms":27134.79808079998,"p95_pre_ms":1021.3897934999999,"service":"ts-travel-plan-service","spans":1565},{"delta_pct":1971.2,"error_pct":0.0,"p95_during_ms":11460.532684649997,"p95_pre_ms":553.315236199999,"service":"ts-preserve-service","spans":1077},{"delta_pct":1704.3,"error_pct":0.0,"p95_during_ms":6089.073387899972,"p95_pre_ms":337.4674729999998,"service":"ts-ui-dashboard","spans":5392},{"delta_pct":1702.2,"error_pct":1.75,"p95_during_ms":6137.78006834998,"p95_pre_ms":340.5669201999996,"service":"loadgenerator","spans":5391}],"omitted_services":22,"service_count":30}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=35 omitted_edges=7
[{"evidence_source":"trace","onset_rel_s":244.2,"rank":1,"service":"ts-seat-service","severity_z":607.778},{"evidence_source":"trace","onset_rel_s":244.2,"rank":2,"service":"ts-ui-dashboard","severity_z":72.998},{"evidence_source":"trace","onset_rel_s":244.2,"rank":3,"service":"ts-travel-service","severity_z":54.125},{"evidence_source":"trace","onset_rel_s":244.2,"rank":4,"service":"loadgenerator","severity_z":72.919},{"evidence_source":"trace","onset_rel_s":244.2,"rank":5,"service":"ts-travel-plan-service","severity_z":95.562},{"evidence_source":"trace","onset_rel_s":244.2,"rank":6,"service":"ts-route-plan-service","severity_z":47.666},{"evidence_source":"trace","onset_rel_s":254.4,"rank":7,"service":"ts-config-service","severity_z":999.0},{"evidence_source":"trace","onset_rel_s":254.4,"rank":8,"service":"ts-order-service","severity_z":7.96},{"evidence_source":"trace","onset_rel_s":254.4,"rank":9,"service":"ts-station-food-service","severity_z":13.256},{"evidence_source":"trace","onset_rel_s":264.6,"rank":10,"service":"ts-travel2-service","severity_z":27.898},{"evidence_source":"trace","onset_rel_s":264.6,"rank":11,"service":"ts-auth-service","severity_z":9.737},{"evidence_source":"trace","onset_rel_s":344.4,"rank":12,"service":"ts-assurance-service","severity_z":15.764},{"evidence_source":"trace","onset_rel_s":344.4,"rank":13,"service":"ts-station-service","severity_z":41.203},{"evidence_source":"metric","onset_rel_s":393.6,"rank":14,"service":"ts-delivery-service","severity_z":351.497}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"ts-ui-dashboard","caller":"loadgenerator"},{"callee":"ts-travel-service","caller":"ts-route-plan-service"},{"callee":"ts-travel2-service","caller":"ts-route-plan-service"},{"callee":"ts-config-service","caller":"ts-seat-service"},{"callee":"ts-order-service","caller":"ts-seat-service"},{"callee":"ts-route-plan-service","caller":"ts-travel-plan-service"},{"callee":"ts-seat-service","caller":"ts-travel-plan-service"},{"callee":"ts-seat-service","caller":"ts-travel-service"},{"callee":"ts-seat-service","caller":"ts-travel2-service"},{"callee":"ts-assurance-service","caller":"ts-ui-dashboard"},{"callee":"ts-auth-service","caller":"ts-ui-dashboard"},{"callee":"ts-order-service","caller":"ts-ui-dashboard"},{"callee":"ts-travel-plan-service","caller":"ts-ui-dashboard"},{"callee":"ts-travel-service","caller":"ts-ui-dashboard"},{"callee":"ts-travel2-service","caller":"ts-ui-dashboard"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

[excluded before optimizer]
