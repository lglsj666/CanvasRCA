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
opaque_id: INC-A22F7ACF47C5
observation_window={"duration_rel_s":1440.0,"source_metric_rows":1441}
selection_summary={"candidate_count":17,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":267,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","cartservice","checkoutservice","currencyservice","emailservice","frontend","frontend-external","gke-gke-cluster-default-pool-2e1807ce-0e4z","gke-gke-cluster-default-pool-2e1807ce-cx8g","gke-gke-cluster-default-pool-2e1807ce-w819","gke-gke-cluster-default-pool-2e1807ce-xte3","loadgenerator","paymentservice","productcatalogservice","recommendationservice","redis","shippingservice"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[11.25,33.75,56.25,78.75,101.25,123.75,146.25,168.75,191.25,213.75,236.25,258.75,281.25,303.75,326.25,348.75,371.25,393.75,416.25,438.75,461.25,483.75,506.25,528.75,551.25,573.75,596.25,618.75,641.25,663.75,686.25,708.75,731.25,753.75,776.25,798.75,821.25,843.75,866.25,888.75,911.25,933.75,956.25,978.75,1001.25,1023.75,1046.25,1068.75,1091.25,1113.75,1136.25,1158.75,1181.25,1203.75,1226.25,1248.75,1271.25,1293.75,1316.25,1338.75,1361.25,1383.75,1406.25,1428.75]
[M1] rank=1 service=currencyservice metric=container-memory-mapped-file baseline=0.0 peak=2207744.0 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=rle:0*33,2207744*31
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M2] rank=2 service=currencyservice metric=istio-latency-50 baseline=0.004034 peak=0.051924 signed_z=356.515 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.00386,0.003825,0.003933,0.00406,0.004187,0.004135,0.004154,0.004061,0.004118,0.004241,0.004101,0.004065,0.004117,0.003942,0.003805,0.003927,0.004023,0.004018,0.004035,0.004056,0.003989,0.003944,0.003983,0.004157,0.004283,0.004128,0.003776,0.003724,0.003995,0.004164,0.004195,0.004106,0.004067,0.005472,0.042127,0.049058,0.045625,0.045312,0.04194,0.034565,0.023067,0.028878,0.03661,0.034532,0.04502,0.047688,0.048701,0.051597,0.047833,0.042478,0.043099,0.038846,0.034274,0.02831,0.032716,0.03311,0.033208,0.040364,0.04293,0.043059,0.046761,0.049174,0.05163,0.051046]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M3] rank=3 service=currencyservice metric=container-memory-cache baseline=12288.0 peak=2248704.0 signed_z=276.141 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=rle:12288*33,2248704*31
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M4] rank=4 service=currencyservice metric=istio-latency-99 baseline=0.095242 peak=0.228045 signed_z=133.268 onset_bin=34 onset_rel_s=776.25 persistence_bins=30
values_compact=raw:[0.093262,0.093192,0.093863,0.094647,0.0954,0.095467,0.09632,0.096141,0.09671,0.09692,0.095417,0.095706,0.095697,0.09528,0.09462,0.094056,0.095473,0.095375,0.094884,0.094715,0.093623,0.094236,0.095608,0.095851,0.096725,0.096391,0.093691,0.095472,0.096629,0.095337,0.095412,0.095623,0.095674,0.098216,0.153089,0.196453,0.185125,0.175446,0.176339,0.161743,0.099712,0.099116,0.0996,0.099705,0.112706,0.154733,0.121522,0.132698,0.099661,0.099676,0.099683,0.099774,0.187938,0.099956,0.099157,0.099208,0.099402,0.099619,0.187804,0.174297,0.099553,0.110565,0.099989,0.099595]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M5] rank=5 service=emailservice metric=istio-latency-95 baseline=0.004818 peak=0.008833 signed_z=91.601 onset_bin=30 onset_rel_s=686.25 persistence_bins=11
values_compact=rle:0.0048*6,0.004884*1,0.004875*1,0.0048*12,0.004862*1,0.00489*1,0.0048*8,0.004981*1,0.004977*1,0.0048*6,0.006*1,0.0055*1,0.0048*3,0.004931*1,0.004884*1,0.0048*1,0.004915*1,0.006*1,0.004993*1,0.004872*1,0.0048*7,0.004878*1,0.006583*1,0.00825*1,0.006625*1,0.004881*1,0.0055*1,0.005583*1
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M6] rank=6 service=adservice metric=istio-bytes-90 baseline=0.450574 peak=0.244464 signed_z=-62.887 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=raw:[0.447768,0.451326,0.449545,0.451078,0.452869,0.446429,0.448214,0.452679,0.451339,0.451941,0.451695,0.451539,0.449561,0.448333,0.45125,0.452232,0.45,0.447727,0.449561,0.45339,0.452193,0.446296,0.448182,0.455263,0.448707,0.449576,0.451316,0.450682,0.450909,0.449537,0.450439,0.453289,0.405952,0.249746,0.269231,0.248554,0.248689,0.249471,0.265909,0.30625,0.332353,0.313814,0.305769,0.26,0.259091,0.309615,0.345833,0.42619,0.439205,0.4375,0.400893,0.391667,0.3975,0.249893,0.247737,0.249252,0.325,0.311667,0.283333,0.24903,0.245172,0.246589,0.249516,0.249843]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M7] rank=7 service=emailservice metric=container-network-receive-bytes-total baseline=830.342078 peak=6726.35514 signed_z=57.091 onset_bin=38 onset_rel_s=866.25 persistence_bins=2
values_compact=delta:865.769676,-21.150443,-28.568399,66.743597,-60.804707,-71.510511,7.735906,-15.404689,66.277791,-198.492302,225.534387,45.118293,40.525798,-40.616248,-108.306092,-22.846678,37.779161,-24.178355,51.456478,177.983193,0,-250.8461,53.06683,130.575447,-37.939058,80.075148,-111.718463,-120.580088,-24.343766,231.707498,-86.099444,23.551991,-21.227614,-81.975539,76.908688,-50.366744,-106.821165,-48.322748,4062.339194,899.662201,-4910.176966,-98.993332,-22.777596,164.7967,44.024647,-63.25754,-6.220594,209.034766,-141.789667,179.026281,-153.254803,-64.260953,19.80824,38.464344,-22.435741,12.524646,95.66611,-8.307039,-82.014566,5.488859,51.918614,51.869982,83.129337,-78.391584
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M8] rank=8 service=checkoutservice metric=istio-latency-90 baseline=0.225024 peak=0.75 signed_z=48.902 onset_bin=34 onset_rel_s=776.25 persistence_bins=30
values_compact=raw:[0.220652,0.225062,0.222609,0.216732,0.221364,0.233382,0.24413,0.243182,0.240526,0.239853,0.233044,0.229431,0.234423,0.228875,0.2175,0.22475,0.2302,0.224425,0.229706,0.22615,0.20725,0.209125,0.22,0.227895,0.237609,0.227618,0.199545,0.217757,0.225357,0.223871,0.211176,0.209,0.217857,0.227362,0.402273,0.425,0.475,0.483333,0.625,0.716667,0.475,0.425,0.425,0.43125,0.725,0.625,0.453571,0.467708,0.434091,0.396329,0.369444,0.276875,0.29375,0.35,0.4875,0.45625,0.320833,0.357857,0.426786,0.406818,0.421875,0.426471,0.391071,0.389583]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M9] rank=9 service=paymentservice metric=container-network-receive-bytes-total baseline=769.551782 peak=6400.486387 signed_z=41.749 onset_bin=61 onset_rel_s=1383.75 persistence_bins=2
values_compact=delta:864.503051,-30.332518,-12.010448,51.096074,-36.991547,-125.921869,236.278879,-1.457917,-311.826046,62.792703,85.617819,-9.947212,95.157241,-37.792162,-211.725228,44.281723,90.130732,-24.049232,22.005698,172.439264,-1.515547,-141.091223,-82.761277,176.581187,-24.813862,95.143338,-142.432457,-213.791787,-133.687404,485.505774,-113.38478,-198.305736,164.937081,-172.792146,200.797208,-14.235251,-134.580066,-115.555412,96.937799,13.021597,-96.341553,6.726535,-14.394914,97.93895,120.217885,-118.993473,50.948287,206.414562,40.935843,-89.516202,-74.847263,-117.613471,0,67.495756,60.305273,-46.668851,6.020496,46.947838,-22.400246,-13.103355,76.843196,4588.945886,435.452913,-5179.129823
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M10] rank=10 service=recommendationservice metric=istio-latency-90 baseline=0.009582 peak=0.011636 signed_z=35.742 onset_bin=34 onset_rel_s=776.25 persistence_bins=5
values_compact=raw:[0.009615,0.0096,0.009543,0.009565,0.009611,0.009579,0.009583,0.009654,0.009613,0.009583,0.009563,0.00965,0.00972,0.009598,0.009531,0.009539,0.009525,0.009558,0.009561,0.009547,0.009568,0.009538,0.009523,0.009573,0.009605,0.009552,0.009541,0.009563,0.009536,0.009517,0.009611,0.009748,0.009635,0.009585,0.009981,0.010446,0.009692,0.009644,0.009739,0.009811,0.009696,0.00963,0.00957,0.009624,0.009862,0.009792,0.009629,0.009707,0.00967,0.009604,0.00964,0.009674,0.009689,0.009643,0.009723,0.009722,0.009684,0.009686,0.009638,0.009645,0.009625,0.009633,0.009684,0.009676]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M11] rank=11 service=emailservice metric=istio-latency-90 baseline=0.004617 peak=0.006 signed_z=33.304 onset_bin=30 onset_rel_s=686.25 persistence_bins=11
values_compact=rle:0.0046*6,0.00468*1,0.004671*1,0.0046*12,0.004659*1,0.004686*1,0.0046*8,0.004771*1,0.004767*1,0.0046*6,0.00484*1,0.004812*1,0.0046*3,0.004724*1,0.00468*1,0.0046*1,0.004709*1,0.00484*1,0.004783*1,0.004668*1,0.0046*7,0.004673*1,0.004884*1,0.004989*1,0.004845*1,0.004677*1,0.004812*1,0.004816*1
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M12] rank=12 service=frontend metric=istio-latency-50 baseline=0.050857 peak=0.174279 signed_z=32.988 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.046981,0.046962,0.048855,0.053512,0.059309,0.052332,0.050692,0.051329,0.055283,0.055069,0.050962,0.052876,0.05067,0.048839,0.046882,0.04857,0.056186,0.054236,0.04984,0.04966,0.049159,0.048663,0.049278,0.051842,0.053304,0.050565,0.045896,0.04454,0.045286,0.048277,0.056515,0.055238,0.048652,0.067582,0.168039,0.172525,0.15539,0.157871,0.161667,0.162358,0.14962,0.154321,0.156791,0.152581,0.170401,0.166434,0.161688,0.169196,0.164245,0.156856,0.155691,0.15659,0.144035,0.136477,0.152002,0.152181,0.145624,0.149473,0.149031,0.154545,0.159257,0.156663,0.159799,0.161294]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[711.0,1440.0]

=== LOG SUMMARY ===
{"entries":[{"change_pct":50.0,"n_during":15,"n_pre":10,"service":"redis"},{"change_pct":-8.0,"n_during":966,"n_pre":1050,"service":"checkoutservice"},{"change_pct":-8.0,"n_during":322,"n_pre":350,"service":"emailservice"},{"change_pct":-8.0,"n_during":644,"n_pre":700,"service":"paymentservice"},{"change_pct":-4.0,"n_during":5182,"n_pre":5398,"service":"shippingservice"},{"change_pct":-2.8,"n_during":31003,"n_pre":31910,"service":"frontend"},{"change_pct":-2.4,"n_during":9013,"n_pre":9236,"service":"cartservice"},{"change_pct":-1.6,"n_during":27637,"n_pre":28084,"service":"currencyservice"}],"mode":"volume","omitted_services":2,"service_count":10}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":140.5,"error_pct":0.0,"p95_during_ms":186.12680000000006,"p95_pre_ms":77.3996,"service":"checkoutservice","spans":9120},{"delta_pct":100.9,"error_pct":0.0,"p95_during_ms":138.09414999999993,"p95_pre_ms":68.74809999999992,"service":"frontend","spans":204720},{"delta_pct":15.7,"error_pct":0.0,"p95_during_ms":0.294,"p95_pre_ms":0.254,"service":"currencyservice","spans":56005},{"delta_pct":12.8,"error_pct":0.0,"p95_during_ms":5.064449999999999,"p95_pre_ms":4.488,"service":"recommendationservice","spans":27292},{"delta_pct":6.0,"error_pct":0.0,"p95_during_ms":0.44805000000000006,"p95_pre_ms":0.42260000000000036,"service":"emailservice","spans":1248},{"delta_pct":0.1,"error_pct":0.0,"p95_during_ms":0.37659999999999993,"p95_pre_ms":0.37629999999999986,"service":"paymentservice","spans":960},{"delta_pct":0.0,"error_pct":0.0,"p95_during_ms":0.023,"p95_pre_ms":0.023,"service":"productcatalogservice","spans":102197}],"omitted_services":0,"service_count":7}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=3 omitted_edges=1
[{"evidence_source":"metric","onset_rel_s":730.2,"rank":1,"service":"gke-gke-cluster-default-pool-2e1807ce-cx8g","severity_z":14.635},{"evidence_source":"trace","onset_rel_s":735.0,"rank":2,"service":"recommendationservice","severity_z":3.177},{"evidence_source":"trace","onset_rel_s":735.0,"rank":3,"service":"frontend","severity_z":16.564},{"evidence_source":"metric","onset_rel_s":739.2,"rank":4,"service":"adservice","severity_z":62.887},{"evidence_source":"trace","onset_rel_s":765.0,"rank":5,"service":"checkoutservice","severity_z":14.782},{"evidence_source":"metric","onset_rel_s":769.2,"rank":6,"service":"cartservice","severity_z":28.886},{"evidence_source":"metric","onset_rel_s":808.2,"rank":7,"service":"redis","severity_z":14.024},{"evidence_source":"trace","onset_rel_s":1185.0,"rank":8,"service":"currencyservice","severity_z":11.349},{"evidence_source":"metric","onset_rel_s":1239.0,"rank":9,"service":"shippingservice","severity_z":23.595},{"evidence_source":"metric","onset_rel_s":1267.8,"rank":10,"service":"gke-gke-cluster-default-pool-2e1807ce-0e4z","severity_z":31.667},{"evidence_source":"metric","onset_rel_s":1330.2,"rank":11,"service":"emailservice","severity_z":91.601},{"evidence_source":"metric","onset_rel_s":1378.2,"rank":12,"service":"paymentservice","severity_z":41.749},{"evidence_source":"none","onset_rel_s":null,"rank":13,"service":"gke-gke-cluster-default-pool-2e1807ce-w819","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":14,"service":"gke-gke-cluster-default-pool-2e1807ce-xte3","severity_z":0.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"currencyservice","caller":"checkoutservice"},{"callee":"emailservice","caller":"checkoutservice"},{"callee":"paymentservice","caller":"checkoutservice"},{"callee":"checkoutservice","caller":"frontend"},{"callee":"currencyservice","caller":"frontend"},{"callee":"recommendationservice","caller":"frontend"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"high","reason":"Rank currencyservice first because currencyservice has direct container-memory-mapped-file evidence (signed-z 999, persistence 31 bins); although frontend is salient, the caller path frontend -> currencyservice means a disturbance in the callee can propagate back toward that caller-side symptom.","services":["currencyservice","frontend"]}
