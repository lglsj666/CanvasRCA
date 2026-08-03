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
opaque_id: INC-D9216A2935D3
observation_window={"duration_rel_s":1440.0,"source_metric_rows":1441}
selection_summary={"candidate_count":17,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":264,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","cartservice","checkoutservice","currencyservice","emailservice","frontend","frontend-external","gke-gke-cluster-default-pool-2e1807ce-0e4z","gke-gke-cluster-default-pool-2e1807ce-cx8g","gke-gke-cluster-default-pool-2e1807ce-w819","gke-gke-cluster-default-pool-2e1807ce-xte3","loadgenerator","paymentservice","productcatalogservice","recommendationservice","redis","shippingservice"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[11.25,33.75,56.25,78.75,101.25,123.75,146.25,168.75,191.25,213.75,236.25,258.75,281.25,303.75,326.25,348.75,371.25,393.75,416.25,438.75,461.25,483.75,506.25,528.75,551.25,573.75,596.25,618.75,641.25,663.75,686.25,708.75,731.25,753.75,776.25,798.75,821.25,843.75,866.25,888.75,911.25,933.75,956.25,978.75,1001.25,1023.75,1046.25,1068.75,1091.25,1113.75,1136.25,1158.75,1181.25,1203.75,1226.25,1248.75,1271.25,1293.75,1316.25,1338.75,1361.25,1383.75,1406.25,1428.75]
[M1] rank=1 service=currencyservice metric=container-memory-mapped-file baseline=0.0 peak=2207744.0 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=rle:0*33,2207744*31
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M2] rank=2 service=cartservice metric=istio-latency-95 baseline=0.008585 peak=0.3025 signed_z=999.0 onset_bin=36 onset_rel_s=821.25 persistence_bins=7
values_compact=raw:[0.008614,0.008473,0.008216,0.00839,0.008373,0.008629,0.008963,0.008725,0.00837,0.008165,0.008474,0.008904,0.008728,0.00854,0.008306,0.00857,0.008955,0.009041,0.008836,0.008721,0.008724,0.008515,0.008182,0.008243,0.008661,0.008714,0.008825,0.008942,0.008397,0.008306,0.008636,0.008559,0.00857,0.009427,0.009236,0.008191,0.009884,0.009916,0.008526,0.008488,0.008318,0.008714,0.008834,0.009124,0.009659,0.009056,0.008462,0.008459,0.009225,0.019346,0.009286,0.008299,0.00861,0.095,0.20625,0.009255,0.008473,0.008389,0.008599,0.00931,0.009927,0.009212,0.00799,0.008374]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M3] rank=3 service=currencyservice metric=container-sockets baseline=3.0 peak=8.0 signed_z=625.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=rle:3*33,8*31
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M4] rank=4 service=currencyservice metric=container-memory-cache baseline=0.0 peak=2207744.0 signed_z=514.336 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=rle:0*33,2207744*31
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M5] rank=5 service=recommendationservice metric=container-sockets baseline=4.0 peak=6.0 signed_z=333.333 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=rle:4*32,6*1,4*31
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M6] rank=6 service=currencyservice metric=istio-latency-99 baseline=0.097264 peak=0.149564 signed_z=115.005 onset_bin=33 onset_rel_s=753.75 persistence_bins=4
values_compact=raw:[0.096945,0.097396,0.097246,0.098067,0.098141,0.097978,0.098049,0.096825,0.096463,0.096559,0.096613,0.097419,0.097543,0.097444,0.097144,0.097091,0.097837,0.097715,0.097122,0.097199,0.097605,0.097407,0.09704,0.096771,0.097158,0.097104,0.097122,0.097232,0.096346,0.097549,0.097455,0.096732,0.097032,0.146406,0.149085,0.0972,0.097952,0.097153,0.096527,0.097298,0.097543,0.098203,0.097902,0.097237,0.097281,0.0976,0.097347,0.096528,0.096566,0.096116,0.096735,0.097199,0.097407,0.097401,0.096955,0.096958,0.096805,0.099281,0.099303,0.097623,0.097557,0.0979,0.097875,0.098191]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M7] rank=7 service=recommendationservice metric=istio-latency-95 baseline=0.009822 peak=0.01309 signed_z=81.468 onset_bin=33 onset_rel_s=753.75 persistence_bins=4
values_compact=raw:[0.009866,0.009844,0.009848,0.009865,0.009845,0.009849,0.009851,0.009823,0.009789,0.009765,0.009788,0.00979,0.009794,0.009801,0.009807,0.009819,0.009883,0.00992,0.00984,0.009833,0.00987,0.009832,0.009797,0.009775,0.009831,0.009852,0.009831,0.009811,0.009792,0.009793,0.009739,0.009734,0.009844,0.011158,0.009953,0.009781,0.009913,0.009932,0.009781,0.009759,0.009797,0.009849,0.009858,0.009832,0.009866,0.00988,0.009843,0.009813,0.009836,0.009935,0.009857,0.009782,0.009853,0.009984,0.009985,0.009883,0.009829,0.009818,0.009815,0.009844,0.00987,0.009825,0.009806,0.009805]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M8] rank=8 service=cartservice metric=container-memory-failures-total baseline=0.569096 peak=23.203972 signed_z=41.144 onset_bin=48 onset_rel_s=1091.25 persistence_bins=2
values_compact=raw:[0.140305,0.252107,0.224744,0.725671,0.796099,0.678196,0.717764,2.360915,0.234443,0.079381,0.0,0.283688,0.38192,0.184946,0.120579,1.064042,1.140776,0.70174,0.536193,0.558084,0.506842,0.564943,0.361109,0.101158,0.41744,0.624149,1.096121,0.805374,0.305737,0.303022,0.420679,0.238015,1.917486,1.585465,0.320034,0.319625,0.438933,0.87053,0.173089,0.096416,0.457571,0.993542,0.861951,0.416605,0.232693,0.215652,0.278547,0.225398,16.741296,19.488372,0.449787,0.315119,0.751756,0.803661,0.603024,0.440467,0.334632,0.382196,0.67217,0.735424,0.317696,0.609224,0.857854,0.591366]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M9] rank=9 service=adservice metric=istio-latency-99 baseline=0.004986 peak=0.006886 signed_z=33.75 onset_bin=52 onset_rel_s=1181.25 persistence_bins=2
values_compact=delta:0.00499,-0.000013,0.000012,0.000001,-0.000006,0.000005,-0.000012,-0.000006,-0.000011,0,0.000018,0,-0.000018,0,0.000006,0.000194,-0.00002,-0.000174,-0.000006,0,0.000012,0.000011,-0.000011,0.000012,0.000005,-0.000023,0.000018,-0.000001,-0.000023,0,0,0,0.000029,0,-0.000023,0.000012,0,-0.000012,0.000006,0,0,0.000006,-0.000006,-0.000012,0.000011,0.000001,0.000006,0,-0.000012,0.000011,0.000001,-0.000012,0.001128,0.000692,-0.001797,-0.000012,-0.000017,0,0.000017,0.000001,-0.000012,0,-0.000006,0
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M10] rank=10 service=shippingservice metric=istio-latency-99 baseline=0.004964 peak=0.0053 signed_z=31.522 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.004956,-0.000001,0,0,0,0.000002,0.000001,-0.000001,0.000015,0,0.000022,-0.000003,-0.000011,0.000001,-0.000024,0.000001,0.000012,0.000001,-0.000014,-0.000002,0.000001,0,0.000001,0.000013,0,-0.000012,0,-0.000002,0,0.000014,-0.000001,-0.000011,0.000012,0.000028,-0.000012,-0.000029,0.000024,0,-0.000023,-0.000001,-0.000002,0.000001,0,0,0.000001,0,0,0,0.000011,0.000001,0.000001,-0.000003,0.000001,0.000002,0,0,-0.000013,0,0,-0.000002,0.000012,0.000001,-0.000012,0.000026
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M11] rank=11 service=shippingservice metric=container-network-receive-bytes-total baseline=2635.222817 peak=9590.928833 signed_z=20.72 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:2179.786627,528.415568,286.184836,-165.402054,-136.29201,172.629032,21.086019,-188.49259,-263.817502,-33.589587,247.083594,293.740997,-137.837771,-5.040381,44.908037,-72.078525,-141.855719,-1.247935,-25.233575,178.447102,265.018271,-168.777012,-231.227049,34.153513,149.43426,37.297225,-424.576947,-207.863205,-375.811649,785.277068,260.468587,183.109273,-411.751795,-225.007179,-137.35241,332.223995,67.987466,2.642307,169.380614,11.224354,-302.566266,156.804574,-241.756325,-76.57457,83.201668,174.730208,76.731265,23.032874,234.224891,-499.93393,-51.059676,399.790122,-392.375887,-133.570672,44.275292,362.272805,-139.879213,-108.289414,17.116111,497.262601,3.485956,-190.738542,59.769681,4671.887487
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M12] rank=12 service=redis metric=container-network-receive-bytes-total baseline=3497.584885 peak=8530.629552 signed_z=13.808 onset_bin=48 onset_rel_s=1091.25 persistence_bins=2
values_compact=delta:3451.875982,324.469309,51.29677,-213.971279,-853.422175,1111.25361,-1078.312698,891.892782,-126.473491,-113.951465,22.48074,348.178757,-9.769943,-209.596357,131.322185,-71.553983,-97.046599,19.501693,-37.588099,22.983034,286.778792,-49.854376,-264.963376,109.261356,97.645462,-206.013533,-86.382751,-3.230569,-18.435644,209.271299,152.535967,3.81615,-226.277077,-169.836073,-161.541464,-10.872643,262.535955,-7.347614,187.460574,56.47215,-120.471222,-106.391212,-12.910742,41.743843,-63.21963,111.336077,-36.110061,21.688122,4705.481424,-1185.858722,-3591.655072,314.082408,-55.427545,-339.324657,69.322373,163.619594,-122.920099,67.359246,19.815642,183.284439,62.578687,-103.14054,-106.253951,-69.186982
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[722.0,1440.0]

=== LOG SUMMARY ===
{"entries":[{"change_pct":-33.3,"n_during":10,"n_pre":15,"service":"redis"},{"change_pct":-3.6,"n_during":1016,"n_pre":1054,"service":"checkoutservice"},{"change_pct":-3.4,"n_during":339,"n_pre":351,"service":"emailservice"},{"change_pct":-3.4,"n_during":678,"n_pre":702,"service":"paymentservice"},{"change_pct":-3.2,"n_during":6630,"n_pre":6850,"service":"recommendationservice"},{"change_pct":-2.0,"n_during":9151,"n_pre":9333,"service":"cartservice"},{"change_pct":-1.9,"n_during":5353,"n_pre":5459,"service":"adservice"},{"change_pct":-1.7,"n_during":5342,"n_pre":5436,"service":"shippingservice"}],"mode":"volume","omitted_services":2,"service_count":10}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":30.1,"error_pct":0.0,"p95_during_ms":0.4143999999999998,"p95_pre_ms":0.31849999999999934,"service":"paymentservice","spans":978},{"delta_pct":5.2,"error_pct":0.0,"p95_during_ms":0.44539999999999985,"p95_pre_ms":0.4232,"service":"emailservice","spans":1266},{"delta_pct":-4.0,"error_pct":0.0,"p95_during_ms":0.024,"p95_pre_ms":0.025,"service":"productcatalogservice","spans":103194},{"delta_pct":-3.7,"error_pct":0.0,"p95_during_ms":0.232,"p95_pre_ms":0.241,"service":"currencyservice","spans":56931},{"delta_pct":3.0,"error_pct":0.0,"p95_during_ms":82.7546,"p95_pre_ms":80.35569999999997,"service":"frontend","spans":207152},{"delta_pct":1.5,"error_pct":0.0,"p95_during_ms":100.8971999999997,"p95_pre_ms":99.411,"service":"checkoutservice","spans":9374},{"delta_pct":-0.5,"error_pct":0.0,"p95_during_ms":5.005949999999999,"p95_pre_ms":5.030949999999999,"service":"recommendationservice","spans":27536}],"omitted_services":0,"service_count":7}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=3 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":723.0,"rank":1,"service":"recommendationservice","severity_z":333.333},{"evidence_source":"metric","onset_rel_s":739.8,"rank":2,"service":"frontend","severity_z":13.516},{"evidence_source":"metric","onset_rel_s":745.8,"rank":3,"service":"currencyservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":763.8,"rank":4,"service":"shippingservice","severity_z":31.522},{"evidence_source":"metric","onset_rel_s":1083.0,"rank":5,"service":"redis","severity_z":13.808},{"evidence_source":"metric","onset_rel_s":1174.8,"rank":6,"service":"adservice","severity_z":33.75},{"evidence_source":"metric","onset_rel_s":1204.8,"rank":7,"service":"cartservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1330.2,"rank":8,"service":"gke-gke-cluster-default-pool-2e1807ce-0e4z","severity_z":12.511},{"evidence_source":"none","onset_rel_s":null,"rank":9,"service":"emailservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":10,"service":"checkoutservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":11,"service":"productcatalogservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":12,"service":"frontend-external","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":13,"service":"loadgenerator","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":14,"service":"paymentservice","severity_z":0.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"currencyservice","caller":"checkoutservice"},{"callee":"emailservice","caller":"checkoutservice"},{"callee":"paymentservice","caller":"checkoutservice"},{"callee":"productcatalogservice","caller":"checkoutservice"},{"callee":"checkoutservice","caller":"frontend"},{"callee":"currencyservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"frontend"},{"callee":"recommendationservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"recommendationservice"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"high","reason":"Rank currencyservice first because currencyservice has direct container-memory-mapped-file evidence (signed-z 999, persistence 31 bins); although frontend is salient, the caller path frontend -> currencyservice means a disturbance in the callee can propagate back toward that caller-side symptom.","services":["currencyservice","frontend"]}
