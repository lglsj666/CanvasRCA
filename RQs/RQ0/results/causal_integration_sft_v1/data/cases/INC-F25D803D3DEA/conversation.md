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
opaque_id: INC-F25D803D3DEA
observation_window={"duration_rel_s":1440.0,"source_metric_rows":1441}
selection_summary={"candidate_count":17,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":268,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","cartservice","checkoutservice","currencyservice","emailservice","frontend","frontend-external","gke-gke-cluster-default-pool-2e1807ce-0e4z","gke-gke-cluster-default-pool-2e1807ce-cx8g","gke-gke-cluster-default-pool-2e1807ce-w819","gke-gke-cluster-default-pool-2e1807ce-xte3","loadgenerator","paymentservice","productcatalogservice","recommendationservice","redis","shippingservice"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[11.25,33.75,56.25,78.75,101.25,123.75,146.25,168.75,191.25,213.75,236.25,258.75,281.25,303.75,326.25,348.75,371.25,393.75,416.25,438.75,461.25,483.75,506.25,528.75,551.25,573.75,596.25,618.75,641.25,663.75,686.25,708.75,731.25,753.75,776.25,798.75,821.25,843.75,866.25,888.75,911.25,933.75,956.25,978.75,1001.25,1023.75,1046.25,1068.75,1091.25,1113.75,1136.25,1158.75,1181.25,1203.75,1226.25,1248.75,1271.25,1293.75,1316.25,1338.75,1361.25,1383.75,1406.25,1428.75]
[M1] rank=1 service=currencyservice metric=container-memory-mapped-file baseline=0.0 peak=2211840.0 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=rle:0*33,2211840*31
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M2] rank=2 service=cartservice metric=istio-latency-95 baseline=0.008687 peak=0.60121 signed_z=999.0 onset_bin=34 onset_rel_s=776.25 persistence_bins=29
values_compact=raw:[0.009817,0.009421,0.00845,0.008192,0.008652,0.009018,0.009228,0.008949,0.008506,0.008371,0.009003,0.008986,0.008127,0.008037,0.008176,0.008574,0.008835,0.008675,0.008317,0.008343,0.008496,0.008673,0.008952,0.009011,0.008677,0.00816,0.008122,0.008532,0.009309,0.009609,0.008803,0.008465,0.008842,0.009946,0.015322,0.015312,0.018587,0.187083,0.24625,0.023971,0.016882,0.014658,0.009993,0.01342,0.016092,0.017286,0.015649,0.02125,0.110568,0.49375,0.496591,0.019794,0.014565,0.019105,0.022115,0.01856,0.021079,0.424107,0.558929,0.117045,0.019371,0.019886,0.024958,0.207143]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M3] rank=3 service=recommendationservice metric=istio-latency-95 baseline=0.009826 peak=0.067182 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.009911,0.009801,0.009795,0.009804,0.009888,0.009888,0.009871,0.00985,0.009793,0.009785,0.009826,0.009815,0.009775,0.009809,0.009803,0.009806,0.009843,0.009811,0.009788,0.009839,0.009823,0.009795,0.009828,0.009833,0.009816,0.009802,0.00983,0.009872,0.009848,0.009856,0.009834,0.009828,0.00984,0.023392,0.066909,0.060755,0.02449,0.02359,0.02281,0.023108,0.024547,0.037796,0.024057,0.022899,0.022987,0.023905,0.023657,0.023493,0.024221,0.048633,0.044375,0.023336,0.02261,0.023684,0.024601,0.024421,0.024159,0.024032,0.023946,0.023672,0.023318,0.022857,0.02283,0.024232]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M4] rank=4 service=currencyservice metric=istio-latency-99 baseline=0.09761 peak=2.313123 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.097871,0.097019,0.096948,0.096526,0.098622,0.098643,0.098332,0.098619,0.098015,0.098527,0.09814,0.097565,0.097355,0.097322,0.096655,0.096627,0.096824,0.096618,0.097657,0.098179,0.097848,0.097125,0.097998,0.098013,0.097093,0.096888,0.098615,0.098577,0.097505,0.098087,0.098033,0.09686,0.099594,2.14125,2.260224,2.200332,2.270648,2.287513,2.272168,2.227818,2.188986,2.136905,2.024105,2.098718,2.13328,2.060909,2.155882,2.25262,2.21529,2.108602,2.110763,2.155224,2.221416,2.304688,2.29641,2.18,2.162853,2.167222,2.138809,2.202143,2.197094,2.228266,2.301217,2.304805]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M5] rank=5 service=currencyservice metric=istio-latency-95 baseline=0.085046 peak=1.565613 signed_z=802.799 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.084583,0.083549,0.083153,0.082629,0.087864,0.088738,0.086935,0.085927,0.084875,0.085451,0.086626,0.086262,0.08553,0.085302,0.082443,0.081353,0.082544,0.083069,0.085954,0.088096,0.087074,0.08405,0.08703,0.086868,0.08443,0.083686,0.085484,0.085267,0.084055,0.085558,0.085037,0.083567,0.088811,0.816883,1.301119,1.002941,1.353238,1.437563,1.360842,1.139091,0.985577,0.932741,0.852646,0.893817,0.931188,0.896154,0.952607,1.263102,1.076452,0.917922,0.917217,0.951456,1.107078,1.523438,1.482051,0.976617,0.957609,0.962563,0.947119,1.010714,0.996292,1.141329,1.506087,1.524026]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M6] rank=6 service=currencyservice metric=istio-latency-50 baseline=0.004241 peak=0.133679 signed_z=779.063 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.004574,0.0043,0.004104,0.00409,0.004356,0.004443,0.0043,0.004159,0.004077,0.004074,0.0043,0.004344,0.004205,0.004092,0.003927,0.00396,0.004089,0.004087,0.004121,0.00447,0.004444,0.004185,0.004539,0.004511,0.004339,0.00428,0.004298,0.004278,0.004244,0.004318,0.004158,0.004095,0.004342,0.039967,0.089319,0.090716,0.101777,0.114254,0.093178,0.086153,0.088686,0.088313,0.083237,0.084113,0.08419,0.083602,0.091413,0.100352,0.089472,0.086556,0.087466,0.087595,0.091498,0.114593,0.124117,0.090541,0.085338,0.086636,0.091705,0.09801,0.095871,0.101025,0.115753,0.099747]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M7] rank=7 service=productcatalogservice metric=istio-latency-99 baseline=0.004969 peak=0.018545 signed_z=699.793 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.004997,0.004987,0.004979,0.00496,0.00496,0.004963,0.004961,0.004959,0.004954,0.004957,0.004988,0.00498,0.004963,0.004967,0.004967,0.004963,0.004971,0.004974,0.00496,0.004955,0.004959,0.00496,0.004963,0.004967,0.004967,0.004967,0.004966,0.004969,0.004965,0.004972,0.004971,0.004964,0.00497,0.008128,0.009212,0.008282,0.008273,0.008431,0.007725,0.008789,0.009182,0.010198,0.009567,0.007206,0.007553,0.010937,0.009462,0.008602,0.009923,0.01624,0.009138,0.007965,0.008878,0.009037,0.008832,0.00859,0.007794,0.008077,0.008702,0.009549,0.009071,0.00912,0.009377,0.009082]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M8] rank=8 service=currencyservice metric=container-memory-failures-total baseline=408.152988 peak=51062.366738 signed_z=636.509 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=delta:498.136808,-17.859792,-69.497382,-41.538985,41.705883,15.100359,36.420996,157.825764,-240.730812,-7.479706,0.143627,16.943601,13.314617,-38.970178,-5.306378,23.546224,-6.414368,-22.758231,37.986663,148.596885,29.753156,-94.190276,-111.7379,14.462557,-2.346043,12.844177,-14.058353,-0.653648,-2.37521,3.106147,-66.138161,175.178976,-85.077684,21787.329918,14098.123295,11984.350744,1482.132502,-1041.733493,205.999538,826.453963,-1631.852844,-641.330632,754.537067,-379.971304,1362.231597,958.586547,-1110.265823,-545.506864,228.486491,-184.76689,-70.815421,364.950995,-7133.498047,6783.204229,714.526467,-101.305751,-63.797138,-23.683923,-8655.400811,8293.990307,-5881.028115,5697.454279,-244.342499,-243.30153
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M9] rank=9 service=currencyservice metric=container-memory-rss baseline=41217507.555556 peak=263385088.0 signed_z=447.421 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=delta:41074688,-679936,425984,0,307200,454656,-536576,368640,-647168,315392,221184,-536576,-241664,221184,573440,-380928,245760,897024,-1175552,157696,92160,360448,-208896,188416,-368640,466944,-679936,315392,1183744,-1167360,311296,-616448,149504,222232576,-39714816,19871744,-19486720,-40091648,79421440,49152,-16461824,-158535680,77606912,-58200064,315392,-17842176,72597504,-68919296,160636928,8810496,-151171072,-27992064,80883712,98250752,-202088448,176091136,3661824,22366208,-2048,-24576,-16384,-50917376,50950144,-150822912
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M10] rank=10 service=recommendationservice metric=istio-latency-90 baseline=0.009557 peak=0.023757 signed_z=442.96 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.009641,0.009535,0.009532,0.009543,0.009622,0.00961,0.009592,0.009577,0.009521,0.009515,0.009555,0.009547,0.009513,0.009543,0.009536,0.009533,0.009567,0.009539,0.009515,0.009565,0.009554,0.009528,0.00956,0.009569,0.009552,0.009538,0.009564,0.009605,0.009583,0.009586,0.009562,0.009561,0.009574,0.018516,0.023714,0.023109,0.022104,0.021448,0.02043,0.020411,0.021687,0.021981,0.020629,0.019343,0.019723,0.021262,0.021176,0.020934,0.021323,0.022945,0.022739,0.020529,0.019361,0.020676,0.022206,0.02214,0.021764,0.021526,0.021504,0.020882,0.020053,0.020104,0.020527,0.022]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M11] rank=11 service=currencyservice metric=container-memory-usage-bytes baseline=44938968.177778 peak=268439552.0 signed_z=430.81 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=delta:44740608,-675840,421888,0,335872,561152,-532480,249856,-647168,315392,462848,-786432,-245760,225280,569344,-376832,249856,1019904,-1167360,26624,88064,454656,-286720,184320,-364544,458752,-667648,307200,1298432,-1171456,204800,-567296,100352,223633408,-39710720,19861504,-19517440,-40042496,79425536,0,-16187392,-159137792,77754368,-58126336,143360,-17811456,72673280,-68907008,160796672,8806400,-151449600,-28020736,81055744,98398208,-202346496,202350592,-22237184,22241280,-4096,8192,-24576,-38522880,38543360,-151105536
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M12] rank=12 service=currencyservice metric=container-memory-working-set-bytes baseline=44938968.177778 peak=268439552.0 signed_z=430.81 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=delta:44740608,-675840,421888,0,335872,561152,-532480,249856,-647168,315392,462848,-786432,-245760,225280,569344,-376832,249856,1019904,-1167360,26624,88064,454656,-286720,184320,-364544,458752,-667648,307200,1298432,-1171456,204800,-567296,100352,223633408,-39710720,19861504,-19517440,-40042496,79425536,0,-16187392,-159137792,77754368,-58126336,143360,-17811456,72673280,-68907008,160796672,8806400,-151449600,-28020736,81055744,98398208,-202346496,202350592,-22237184,22241280,-4096,8192,-24576,-38522880,38543360,-151105536
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[716.0,1440.0]

=== LOG SUMMARY ===
{"entries":[{"change_pct":-33.3,"n_during":10,"n_pre":15,"service":"redis"},{"change_pct":-13.7,"n_during":4698,"n_pre":5445,"service":"adservice"},{"change_pct":-13.4,"n_during":24570,"n_pre":28365,"service":"currencyservice"},{"change_pct":-12.5,"n_during":27705,"n_pre":31648,"service":"frontend"},{"change_pct":-12.2,"n_during":5869,"n_pre":6687,"service":"recommendationservice"},{"change_pct":-12.0,"n_during":8035,"n_pre":9129,"service":"cartservice"},{"change_pct":-8.6,"n_during":4680,"n_pre":5120,"service":"shippingservice"},{"change_pct":-4.4,"n_during":909,"n_pre":951,"service":"checkoutservice"}],"mode":"volume","omitted_services":2,"service_count":10}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":980.6,"error_pct":0.0,"p95_during_ms":881.4233000000003,"p95_pre_ms":81.571,"service":"frontend","spans":193296},{"delta_pct":638.5,"error_pct":0.0,"p95_during_ms":701.60675,"p95_pre_ms":95.00800000000001,"service":"checkoutservice","spans":8512},{"delta_pct":81.3,"error_pct":0.0,"p95_during_ms":9.251249999999999,"p95_pre_ms":5.103099999999999,"service":"recommendationservice","spans":25688},{"delta_pct":9.1,"error_pct":0.0,"p95_during_ms":0.3969999999999999,"p95_pre_ms":0.364,"service":"paymentservice","spans":908},{"delta_pct":-3.0,"error_pct":0.0,"p95_during_ms":0.223,"p95_pre_ms":0.23,"service":"currencyservice","spans":53213},{"delta_pct":1.8,"error_pct":0.0,"p95_during_ms":0.4644,"p95_pre_ms":0.456,"service":"emailservice","spans":1196},{"delta_pct":0.0,"error_pct":0.0,"p95_during_ms":0.025,"p95_pre_ms":0.025,"service":"productcatalogservice","spans":96271}],"omitted_services":0,"service_count":7}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=3 omitted_edges=3
[{"evidence_source":"trace","onset_rel_s":735.0,"rank":1,"service":"recommendationservice","severity_z":84.692},{"evidence_source":"trace","onset_rel_s":735.0,"rank":2,"service":"frontend","severity_z":123.965},{"evidence_source":"trace","onset_rel_s":735.0,"rank":3,"service":"checkoutservice","severity_z":125.054},{"evidence_source":"trace","onset_rel_s":735.0,"rank":4,"service":"paymentservice","severity_z":8.758},{"evidence_source":"metric","onset_rel_s":739.8,"rank":5,"service":"currencyservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":751.8,"rank":6,"service":"emailservice","severity_z":81.015},{"evidence_source":"metric","onset_rel_s":759.0,"rank":7,"service":"gke-gke-cluster-default-pool-2e1807ce-xte3","severity_z":86.35},{"evidence_source":"metric","onset_rel_s":822.0,"rank":8,"service":"adservice","severity_z":94.11},{"evidence_source":"metric","onset_rel_s":927.0,"rank":9,"service":"productcatalogservice","severity_z":699.793},{"evidence_source":"metric","onset_rel_s":1101.0,"rank":10,"service":"cartservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1378.8,"rank":11,"service":"shippingservice","severity_z":20.353},{"evidence_source":"none","onset_rel_s":null,"rank":12,"service":"gke-gke-cluster-default-pool-2e1807ce-w819","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":13,"service":"gke-gke-cluster-default-pool-2e1807ce-0e4z","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":14,"service":"gke-gke-cluster-default-pool-2e1807ce-cx8g","severity_z":0.0}]
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
