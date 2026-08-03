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
opaque_id: INC-11749196C5E7
observation_window={"duration_rel_s":477.48,"source_metric_rows":951}
selection_summary={"candidate_count":104,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":902,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["loadgenerator","loadgenerator-7db95c8ddc-g4vfv","mysql","mysql-0","rabbitmq","rabbitmq-0","ts-admin-basic-info-service","ts-admin-basic-info-service-579748f6fc-j24n6","ts-admin-order-service","ts-admin-order-service-655fd7b7cb-tkxng","ts-admin-route-service","ts-admin-route-service-58bfb4cc97-m8gpm","ts-admin-travel-service","ts-admin-travel-service-57f4669564-lk94z","ts-admin-user-service","ts-admin-user-service-788fb9f775-vr6mv","ts-assurance-service","ts-assurance-service-858c47f787-mzlb7","ts-auth-service","ts-auth-service-7f7b9f74b4-lqpsx","ts-avatar-service","ts-avatar-service-7859d9b6f8-mzj85","ts-basic-service","ts-basic-service-6d57966576-cn26h","ts-cancel-service","ts-cancel-service-5979858c6-wzrvl","ts-config-service","ts-config-service-795d7b9cc6-m269m","ts-consign-price-service","ts-consign-price-service-56db65bff9-mq589","ts-consign-service","ts-consign-service-7f98cd6b79-wz4gr","ts-contacts-service","ts-contacts-service-c67494dcf-jxhsk","ts-delivery-service","ts-delivery-service-fb75484cd-wwgq6","ts-execute-service","ts-execute-service-6d87555bd5-q54xz","ts-food-delivery-service","ts-food-delivery-service-7c7dd959c-x54hc","ts-food-service","ts-food-service-74f7b88bfd-xjfw4","ts-gateway-service","ts-gateway-service-98ffc48c6-lrfg4","ts-inside-payment-service","ts-inside-payment-service-6558cd9645-pj6hj","ts-news-service","ts-news-service-7869d45c45-7zvcb","ts-notification-service","ts-notification-service-b89747469-44hh9","ts-order-other-service","ts-order-other-service-57b5486dcc-fk4w6","ts-order-service","ts-order-service-bcc5cc698-w565k","ts-payment-service","ts-payment-service-9ff84b9b8-z6vw5","ts-preserve-other-service","ts-preserve-other-service-7797845cfc-89zmp","ts-preserve-service","ts-preserve-service-6d6b5f4cbb-pr6wl","ts-price-service","ts-price-service-c696df855-flrr9","ts-rebook-service","ts-rebook-service-77567cc6bb-5sh82","ts-route-plan-service","ts-route-plan-service-6f74db974f-whrjc","ts-route-service","ts-route-service-6dcf9c5ccf-gb6l2","ts-seat-service","ts-seat-service-6d77945967-g9s7l","ts-security-service","ts-security-service-6945c7f648-pc794","ts-station-food-service","ts-station-food-service-86ccc7545-9grls","ts-station-service","ts-station-service-745fb4b4fd-s7bbv","ts-ticket-office-service","ts-ticket-office-service-7d58848599-2r6xc","ts-train-food-service","ts-train-food-service-5f748fdf99-2xhwr","ts-train-service","ts-train-service-786fb85d88-h7npz","ts-travel-plan-service","ts-travel-plan-service-f946cdc66-pbv7p","ts-travel-service","ts-travel-service-f48bb6c74-pldxw","ts-travel2-service","ts-travel2-service-5dfc5d8c56-hbkck","ts-ui-dashboard","ts-ui-dashboard-bd467f7cf-6w4qt","ts-user-service","ts-user-service-6cbf658657-9lbtz","ts-verification-code-service","ts-verification-code-service-779d78bd9-wspb7","ts-voucher-service","ts-voucher-service-7bbb9f7895-srmrz","ts-wait-order-service","ts-wait-order-service-5875864b5d-cvk6j","worker1","worker2","worker3","worker4","worker5","worker6"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[3.73,11.191,18.652,26.112,33.573,41.033,48.494,55.955,63.415,70.876,78.337,85.797,93.258,100.718,108.179,115.64,123.1,130.561,138.021,145.482,152.943,160.403,167.864,175.325,182.785,190.246,197.706,205.167,212.628,220.088,227.549,235.01,242.47,249.931,257.391,264.852,272.313,279.773,287.234,294.694,302.155,309.616,317.076,324.537,331.998,339.458,346.919,354.379,361.84,369.301,376.761,384.222,391.683,399.143,406.604,414.064,421.525,428.986,436.446,443.907,451.367,458.828,466.289,473.749]
[M1] rank=1 service=ts-station-food-service-86ccc7545-9grls metric=k8s.container.restarts baseline=0.0 peak=1.0 signed_z=999.0 onset_bin=33 onset_rel_s=249.931 persistence_bins=23
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0001000100010001000100010001000100010001000100010010001000100010
observed_counts_compact=csv:1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1
[M2] rank=2 service=ts-station-food-service metric=container.filesystem.usage baseline=466944.0 peak=69632.0 signed_z=-850.877 onset_bin=32 onset_rel_s=242.47 persistence_bins=13
values_compact=rle:466944*32,268288*1,69632*3,256000*1,442368*6,446464*1,456704*1,466944*19
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2
[M3] rank=3 service=ts-station-food-service metric=container.memory.working_set baseline=749764096.0 peak=211271680.0 signed_z=-370.39 onset_bin=32 onset_rel_s=242.47 persistence_bins=32
values_compact=delta:746614784,1024000,278528,278528,135168,0,120832,120832,266240,0,-65536,282624,0,0,532480,0,413696,266240,0,0,110592,0,503808,0,954368,0,-307200,-307200,204800,204800,0,212992,-270286848,-245649408,9191424,0,0,50397184,0,234684416,0,49790976,0,86601728,32581632,32581632,26748928,26748928,-30720,-30720,0,4825088,903168,903168,0,118784,0,315392,315392,67584,67584,299008,0,57344
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2
[M4] rank=4 service=ts-station-food-service metric=container.memory.rss baseline=739040938.666667 peak=237502464.0 signed_z=-362.272 onset_bin=34 onset_rel_s=257.391 persistence_bins=30
values_compact=delta:735961088,995328,282624,282624,131072,0,120832,120832,262144,0,-36864,282624,0,0,532480,0,413696,266240,0,0,110592,0,499712,0,184320,0,77824,77824,219136,219136,0,208896,0,-503709696,0,0,49926144,0,233590784,0,48738304,0,86065152,31932416,31932416,27164672,27164672,215040,215040,0,4825088,157696,157696,0,1601536,0,329728,329728,67584,67584,299008,0,49152
missing_mask_bits=0000000000000000000000000000000001000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,0,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2
[M5] rank=5 service=ts-station-food-service metric=k8s.pod.memory.rss baseline=738983082.666667 peak=203804672.0 signed_z=-353.746 onset_bin=33 onset_rel_s=249.931 persistence_bins=31
values_compact=delta:735092736,0,2236416,233472,0,221184,0,372736,-12288,-12288,14336,14336,405504,405504,163840,163840,55296,55296,0,299008,45056,45056,292864,292864,34816,34816,0,110592,0,0,569344,118784,0,-537448448,0,35057664,0,54575104,113811456,113811456,0,48689152,0,92766208,0,0,111132672,0,745472,4759552,0,0,229376,0,1470464,0,0,364544,0,806912,0,174080,174080,0
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2
[M6] rank=6 service=ts-station-food-service metric=k8s.pod.memory.node.utilization baseline=0.00556 peak=0.001575 signed_z=-348.843 onset_bin=33 onset_rel_s=249.931 persistence_bins=31
values_compact=rle:0.00553*2,0.005547*1,0.005549*2,0.005551*2,0.005553*5,0.005556*1,0.005559*1,0.005564*1,0.005569*1,0.005566*1,0.005562*2,0.005565*3,0.005567*1,0.00557*4,0.005571*3,0.005575*1,0.005576*2,0.001575*2,0.001839*2,0.002278*1,0.003109*1,0.003941*2,0.004411*2,0.004998*3,0.005821*2,0.005827*1,0.005862*3,0.005864*2,0.005875*3,0.005877*2,0.005883*2,0.005885*1,0.005886*2
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2
[M7] rank=7 service=ts-station-food-service metric=k8s.pod.memory_limit_utilization baseline=0.233055 peak=0.066027 signed_z=-348.843 onset_bin=33 onset_rel_s=249.931 persistence_bins=31
values_compact=delta:0.231818,0,0.000712,0.000071,0,0.00007,0,0.000115,-0.000007,-0.000007,0.000004,0.000004,0.000128,0.000128,0.000204,0.000204,-0.000138,-0.000138,0,0.000093,0.000014,0.000014,0.000092,0.000091,0.00001,0.000011,0,0.000026,0,0,0.000177,0.000038,0,-0.167707,0,0.011067,0,0.018378,0.034873,0.034873,0,0.019698,0,0.024599,0,0,0.034506,0,0.000244,0.001478,0,0,0.000071,0,0.000456,0,0,0.0001,0,0.000257,0,0.000057,0.000057,-0.000004
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2
[M8] rank=8 service=ts-station-food-service metric=k8s.pod.memory.usage baseline=750723413.333333 peak=212688896.0 signed_z=-348.843 onset_bin=33 onset_rel_s=249.931 persistence_bins=31
values_compact=delta:746737664,0,2293760,229376,0,225280,0,368640,-22528,-22528,14336,14336,411648,411648,657408,657408,-444416,-444416,0,299008,45056,45056,294912,294912,32768,32768,0,86016,0,0,569344,122880,0,-540221440,0,35647488,0,59199488,112334848,112334848,0,63451136,0,79237120,0,0,111153152,0,786432,4759552,0,0,229376,0,1470464,0,0,319488,0,827392,0,184320,184320,-12288
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2
[M9] rank=9 service=ts-station-food-service metric=k8s.pod.memory.available baseline=2470887082.666667 peak=3008888832.0 signed_z=348.822 onset_bin=33 onset_rel_s=249.931 persistence_bins=31
values_compact=delta:2474872832,0,-2293760,-229376,0,-225280,0,-368640,22528,22528,-14336,-14336,-411648,-411648,-657408,-657408,444416,444416,0,-299008,-45056,-45056,-294912,-294912,-32768,-32768,0,-86016,0,0,-569344,-122880,0,540188672,0,-35647488,0,-58847232,-112334848,-112334848,0,-63451136,0,-79237120,0,0,-111153152,0,-786432,-4759552,0,0,-229376,0,-1470464,0,0,-319488,0,-827392,0,-184320,-184320,12288
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2
[M10] rank=10 service=ts-station-food-service metric=k8s.pod.memory.working_set baseline=750338389.333333 peak=212336640.0 signed_z=-348.822 onset_bin=33 onset_rel_s=249.931 persistence_bins=31
values_compact=delta:746352640,0,2293760,229376,0,225280,0,368640,-22528,-22528,14336,14336,411648,411648,657408,657408,-444416,-444416,0,299008,45056,45056,294912,294912,32768,32768,0,86016,0,0,569344,122880,0,-540188672,0,35647488,0,58847232,112334848,112334848,0,63451136,0,79237120,0,0,111153152,0,786432,4759552,0,0,229376,0,1470464,0,0,319488,0,827392,0,184320,184320,-12288
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2
[M11] rank=11 service=ts-station-food-service metric=container.memory.usage baseline=750149120.0 peak=245133312.0 signed_z=-347.364 onset_bin=34 onset_rel_s=257.391 persistence_bins=30
values_compact=delta:746999808,1024000,278528,278528,135168,0,120832,120832,266240,0,-65536,282624,0,0,532480,0,413696,266240,0,0,110592,0,503808,0,954368,0,-307200,-307200,204800,204800,0,212992,0,-507097088,0,0,50749440,0,234684416,0,49790976,0,86601728,32581632,32581632,26748928,26748928,-30720,-30720,0,4825088,903168,903168,0,118784,0,315392,315392,67584,67584,299008,0,57344
missing_mask_bits=0000000000000000000000000000000001000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,0,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2
[M12] rank=12 service=ts-station-food-service metric=container.memory.available baseline=2471461376.0 peak=2976124928.0 signed_z=347.122 onset_bin=34 onset_rel_s=257.391 persistence_bins=30
values_compact=delta:2474610688,-1024000,-278528,-278528,-135168,0,-120832,-120832,-266240,0,65536,-282624,0,0,-532480,0,-413696,-266240,0,0,-110592,0,-503808,0,-954368,0,307200,307200,-204800,-204800,0,-212992,0,506744832,0,0,-50397184,0,-234684416,0,-49790976,0,-86601728,-32581632,-32581632,-26748928,-26748928,30720,30720,0,-4825088,-903168,-903168,0,-118784,0,-315392,-315392,-67584,-67584,-299008,0,-57344
missing_mask_bits=0000000000000000000000000000000001000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,0,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[240.56866145133972,470.5680162906647]

=== LOG SUMMARY ===
{"entries":[{"error_logs":1929,"error_pct":19.41,"service":"ts-seat-service","total_logs":9936},{"error_logs":245,"error_pct":18.07,"service":"ts-food-service","total_logs":1356},{"error_logs":96,"error_pct":25.0,"service":"ts-notification-service","total_logs":384},{"error_logs":96,"error_pct":25.0,"service":"ts-delivery-service","total_logs":384},{"error_logs":26,"error_pct":0.75,"service":"ts-order-service","total_logs":3488},{"error_logs":26,"error_pct":2.25,"service":"ts-preserve-service","total_logs":1158},{"error_logs":22,"error_pct":0.51,"service":"ts-ui-dashboard","total_logs":4286},{"error_logs":14,"error_pct":8.7,"service":"ts-station-food-service","total_logs":161}],"mode":"errors","omitted_services":24,"service_count":32}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":-80.3,"error_pct":0.0,"p95_during_ms":29.34080165,"p95_pre_ms":149.30626285,"service":"ts-consign-price-service","spans":90},{"delta_pct":61.0,"error_pct":0.0,"p95_during_ms":73.84699700000004,"p95_pre_ms":45.857066599999925,"service":"ts-inside-payment-service","spans":695},{"delta_pct":60.8,"error_pct":0.0,"p95_during_ms":1087.2389562499843,"p95_pre_ms":676.2203611999994,"service":"ts-route-plan-service","spans":1043},{"delta_pct":-44.2,"error_pct":0.0,"p95_during_ms":26.338029100000007,"p95_pre_ms":47.20276794999985,"service":"ts-security-service","spans":730},{"delta_pct":-35.6,"error_pct":0.0,"p95_during_ms":7.750582599999999,"p95_pre_ms":12.026597449999997,"service":"ts-price-service","spans":2495},{"delta_pct":-29.8,"error_pct":0.0,"p95_during_ms":16.099390800000002,"p95_pre_ms":22.94579465,"service":"ts-assurance-service","spans":616},{"delta_pct":-25.3,"error_pct":0.0,"p95_during_ms":11.401773899999998,"p95_pre_ms":15.263546,"service":"ts-contacts-service","spans":1793},{"delta_pct":21.1,"error_pct":0.0,"p95_during_ms":153.61550359999993,"p95_pre_ms":126.82265839999998,"service":"ts-travel2-service","spans":3191}],"omitted_services":22,"service_count":30}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=35 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":245.4,"rank":1,"service":"ts-contacts-service","severity_z":35.682},{"evidence_source":"metric","onset_rel_s":250.8,"rank":2,"service":"ts-station-food-service","severity_z":999.0},{"evidence_source":"trace","onset_rel_s":253.8,"rank":3,"service":"ts-verification-code-service","severity_z":6.936},{"evidence_source":"metric","onset_rel_s":255.6,"rank":4,"service":"ts-config-service","severity_z":11.585},{"evidence_source":"metric","onset_rel_s":337.2,"rank":5,"service":"ts-avatar-service","severity_z":10.202},{"evidence_source":"metric","onset_rel_s":362.4,"rank":6,"service":"loadgenerator","severity_z":255.383},{"evidence_source":"trace","onset_rel_s":363.0,"rank":7,"service":"ts-security-service","severity_z":18.783},{"evidence_source":"metric","onset_rel_s":385.8,"rank":8,"service":"ts-payment-service","severity_z":332.584},{"evidence_source":"metric","onset_rel_s":440.4,"rank":9,"service":"ts-food-service","severity_z":17.915},{"evidence_source":"trace","onset_rel_s":452.4,"rank":10,"service":"ts-travel2-service","severity_z":5.087},{"evidence_source":"metric","onset_rel_s":462.0,"rank":11,"service":"ts-news-service","severity_z":33.527},{"evidence_source":"metric","onset_rel_s":472.2,"rank":12,"service":"mysql","severity_z":28.822},{"evidence_source":"metric","onset_rel_s":475.2,"rank":13,"service":"ts-rebook-service","severity_z":10.984},{"evidence_source":"none","onset_rel_s":null,"rank":14,"service":"ts-basic-service","severity_z":0.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"ts-station-food-service","caller":"ts-food-service"},{"callee":"ts-basic-service","caller":"ts-travel2-service"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"high","reason":"Rank ts-station-food-service first because ts-station-food-service has direct k8s.container.restarts evidence (signed-z 999, persistence 23 bins); although ts-food-service is salient, the caller path ts-food-service -> ts-station-food-service means a disturbance in the callee can propagate back toward that caller-side symptom.","services":["ts-station-food-service","ts-food-service"]}
