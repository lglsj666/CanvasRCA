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
opaque_id: INC-7297B9BA8FC0
observation_window={"duration_rel_s":479.564,"source_metric_rows":856}
selection_summary={"candidate_count":103,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":913,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["loadgenerator","loadgenerator-77d5b896cb-866b2","mysql","mysql-0","rabbitmq","rabbitmq-0","ts-admin-basic-info-service","ts-admin-basic-info-service-66cdcc94bc-g9vx6","ts-admin-order-service","ts-admin-order-service-5b6dc77d7d-jc99d","ts-admin-route-service","ts-admin-route-service-f9c84f85f-7mrsv","ts-admin-travel-service","ts-admin-travel-service-659b5c9df4-k6v9g","ts-admin-user-service","ts-admin-user-service-5bfc8844b9-r8s67","ts-assurance-service","ts-assurance-service-75c854dc5c-zvjqh","ts-auth-service","ts-auth-service-69bdd5df8-cvzgm","ts-avatar-service","ts-avatar-service-845b64df6-8fsmz","ts-basic-service","ts-basic-service-7c6d59d5c4-rntlz","ts-cancel-service","ts-cancel-service-7ffd988fdb-gfmll","ts-config-service","ts-config-service-55cffbf48b-rpk7t","ts-consign-price-service","ts-consign-price-service-654cb4fc65-2wsnf","ts-consign-service","ts-consign-service-9954fddf-fzpz4","ts-contacts-service","ts-contacts-service-6d745b6c8f-2767h","ts-delivery-service","ts-delivery-service-694895c6cb-phknb","ts-execute-service","ts-execute-service-8457c56cb7-l29bp","ts-food-delivery-service","ts-food-delivery-service-96d856899-jlstt","ts-food-service","ts-food-service-64d454885b-b4476","ts-gateway-service","ts-gateway-service-7f988fb8c4-zwb7q","ts-inside-payment-service","ts-inside-payment-service-5ccb8ccb87-jdz76","ts-news-service","ts-news-service-6d6c6d7855-9hh7k","ts-notification-service","ts-notification-service-58f6c468d7-m8pb4","ts-order-other-service","ts-order-other-service-5d6878687f-46zps","ts-order-service","ts-order-service-6794d6f564-28m6l","ts-payment-service","ts-payment-service-58854d694-mghb2","ts-preserve-other-service","ts-preserve-other-service-64fd9c88cf-mqw24","ts-preserve-service","ts-preserve-service-696df489d4-x9q79","ts-price-service","ts-price-service-67c895b45-wc2rk","ts-rebook-service","ts-rebook-service-7c7644bbdd-sg98d","ts-route-plan-service","ts-route-plan-service-556cddc5c9-d5ptc","ts-route-service","ts-route-service-cfc6dbcf7-lfqm6","ts-seat-service","ts-seat-service-6c78b7d797-gtcz4","ts-security-service","ts-security-service-55f5b777bb-ktg4p","ts-station-food-service","ts-station-food-service-746f6779d7-5ws7d","ts-station-service","ts-station-service-65986cc944-r7nd6","ts-ticket-office-service","ts-ticket-office-service-d7c58b8c7-r6g8s","ts-train-food-service","ts-train-food-service-d5485c677-gmwxn","ts-train-service","ts-train-service-9b56d75b6-trbh2","ts-travel-plan-service","ts-travel-plan-service-7875c49896-k4p59","ts-travel-service","ts-travel-service-c7b5c6d9b-cp7wv","ts-travel2-service","ts-travel2-service-7ff5bbbf54-5b7tz","ts-ui-dashboard","ts-ui-dashboard-57867cb85c-5fjcj","ts-user-service","ts-user-service-54dd6b48c-gt9qq","ts-verification-code-service","ts-verification-code-service-85785c4f79-hvx2v","ts-voucher-service","ts-voucher-service-689c4fc885-4hfdq","ts-wait-order-service","ts-wait-order-service-7cf6bc9468-28n6d","worker1","worker2","worker3","worker4","worker6"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[3.747,11.24,18.733,26.226,33.719,41.213,48.706,56.199,63.692,71.185,78.679,86.172,93.665,101.158,108.651,116.144,123.638,131.131,138.624,146.117,153.61,161.104,168.597,176.09,183.583,191.076,198.57,206.063,213.556,221.049,228.542,236.036,243.529,251.022,258.515,266.008,273.502,280.995,288.488,295.981,303.474,310.968,318.461,325.954,333.447,340.94,348.433,355.927,363.42,370.913,378.406,385.899,393.393,400.886,408.379,415.872,423.365,430.859,438.352,445.845,453.338,460.831,468.325,475.818]
[M1] rank=1 service=ts-avatar-service metric=container.filesystem.available baseline=26976871509.333332 peak=14148448256.0 signed_z=-747.908 onset_bin=40 onset_rel_s=303.474 persistence_bins=15
values_compact=delta:27008565248,-9437184,-1069056,-509952,-509952,-1208320,-9375744,-499712,-499712,-970752,-1069056,-518144,-518144,-530432,-530432,-9490432,-1105920,-563200,-563200,-1069056,-17956864,-552960,-552960,-1122304,-1097728,-528384,-528384,40927232,-1110016,-563200,-563200,-9478144,-1142784,-327680,-327680,-626688,-8941568,-266240,-266240,-614400,-125345792,-646684672,-646684672,-1327771648,-1293623296,-645687296,-645687296,-1191428096,-1310363648,-659179520,-659179520,-1276956672,-1169059840,-608393216,-608393216,12782571520,-479232,26513408,26513408,12701696,-10584064,-466944,-466944,-2060288
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M2] rank=2 service=ts-avatar-service metric=k8s.pod.filesystem.available baseline=26976871509.333332 peak=14148448256.0 signed_z=-747.908 onset_bin=40 onset_rel_s=303.474 persistence_bins=15
values_compact=delta:27008565248,-9437184,-1069056,-509952,-509952,-1208320,-9375744,-499712,-499712,-970752,-1069056,-518144,-518144,-530432,-530432,-9490432,-1105920,-563200,-563200,-1069056,-17956864,-552960,-552960,-1122304,-1097728,-528384,-528384,40927232,-1110016,-563200,-563200,-9478144,-1142784,-327680,-327680,-626688,-8941568,-266240,-266240,-614400,-125345792,-646684672,-646684672,-1327771648,-1293623296,-645687296,-645687296,-1191428096,-1310363648,-659179520,-659179520,-1276956672,-1169059840,-608393216,-608393216,12782571520,-479232,26513408,26513408,12701696,-10584064,-466944,-466944,-2060288
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M3] rank=3 service=ts-consign-price-service metric=container.filesystem.available baseline=26976871509.333332 peak=14148448256.0 signed_z=-747.908 onset_bin=40 onset_rel_s=303.474 persistence_bins=15
values_compact=delta:27008565248,-9437184,-1069056,-509952,-509952,-1208320,-9375744,-499712,-499712,-970752,-1069056,-518144,-518144,-530432,-530432,-9490432,-1105920,-563200,-563200,-1069056,-17956864,-552960,-552960,-1122304,-1097728,-528384,-528384,40927232,-1110016,-563200,-563200,-9478144,-1142784,-327680,-327680,-626688,-8941568,-266240,-266240,-614400,-125345792,-646684672,-646684672,-1327771648,-1293623296,-645687296,-645687296,-1191428096,-1310363648,-659179520,-659179520,-1276956672,-1169059840,-608393216,-608393216,12782571520,-479232,26513408,26513408,12701696,-10584064,-466944,-466944,-2060288
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M4] rank=4 service=ts-consign-price-service metric=k8s.pod.filesystem.available baseline=26976871509.333332 peak=14148448256.0 signed_z=-747.908 onset_bin=40 onset_rel_s=303.474 persistence_bins=15
values_compact=delta:27008565248,-9437184,-1069056,-509952,-509952,-1208320,-9375744,-499712,-499712,-970752,-1069056,-518144,-518144,-530432,-530432,-9490432,-1105920,-563200,-563200,-1069056,-17956864,-552960,-552960,-1122304,-1097728,-528384,-528384,40927232,-1110016,-563200,-563200,-9478144,-1142784,-327680,-327680,-626688,-8941568,-266240,-266240,-614400,-125345792,-646684672,-646684672,-1327771648,-1293623296,-645687296,-645687296,-1191428096,-1310363648,-659179520,-659179520,-1276956672,-1169059840,-608393216,-608393216,12782571520,-479232,26513408,26513408,12701696,-10584064,-466944,-466944,-2060288
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M5] rank=5 service=ts-food-service metric=container.filesystem.available baseline=26976871509.333332 peak=14148448256.0 signed_z=-747.908 onset_bin=40 onset_rel_s=303.474 persistence_bins=15
values_compact=delta:27008565248,-9437184,-1069056,-509952,-509952,-1208320,-9375744,-499712,-499712,-970752,-1069056,-518144,-518144,-530432,-530432,-9490432,-1105920,-563200,-563200,-1069056,-17956864,-552960,-552960,-1122304,-1097728,-528384,-528384,40927232,-1110016,-563200,-563200,-9478144,-1142784,-327680,-327680,-626688,-8941568,-266240,-266240,-614400,-125345792,-646684672,-646684672,-1327771648,-1293623296,-645687296,-645687296,-1191428096,-1310363648,-659179520,-659179520,-1276956672,-1169059840,-608393216,-608393216,12782571520,-479232,26513408,26513408,12701696,-10584064,-466944,-466944,-2060288
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M6] rank=6 service=ts-food-service metric=k8s.pod.filesystem.available baseline=26976871509.333332 peak=14148448256.0 signed_z=-747.908 onset_bin=40 onset_rel_s=303.474 persistence_bins=15
values_compact=delta:27008565248,-9437184,-1069056,-509952,-509952,-1208320,-9375744,-499712,-499712,-970752,-1069056,-518144,-518144,-530432,-530432,-9490432,-1105920,-563200,-563200,-1069056,-17956864,-552960,-552960,-1122304,-1097728,-528384,-528384,40927232,-1110016,-563200,-563200,-9478144,-1142784,-327680,-327680,-626688,-8941568,-266240,-266240,-614400,-125345792,-646684672,-646684672,-1327771648,-1293623296,-645687296,-645687296,-1191428096,-1310363648,-659179520,-659179520,-1276956672,-1169059840,-608393216,-608393216,12782571520,-479232,26513408,26513408,12701696,-10584064,-466944,-466944,-2060288
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M7] rank=7 service=ts-news-service metric=container.filesystem.available baseline=26976871509.333332 peak=14148448256.0 signed_z=-747.908 onset_bin=40 onset_rel_s=303.474 persistence_bins=15
values_compact=delta:27008565248,-9437184,-1069056,-509952,-509952,-1208320,-9375744,-499712,-499712,-970752,-1069056,-518144,-518144,-530432,-530432,-9490432,-1105920,-563200,-563200,-1069056,-17956864,-552960,-552960,-1122304,-1097728,-528384,-528384,40927232,-1110016,-563200,-563200,-9478144,-1142784,-327680,-327680,-626688,-8941568,-266240,-266240,-614400,-125345792,-646684672,-646684672,-1327771648,-1293623296,-645687296,-645687296,-1191428096,-1310363648,-659179520,-659179520,-1276956672,-1169059840,-608393216,-608393216,12782571520,-479232,26513408,26513408,12701696,-10584064,-466944,-466944,-2060288
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M8] rank=8 service=ts-news-service metric=k8s.pod.filesystem.available baseline=26976871509.333332 peak=14148448256.0 signed_z=-747.908 onset_bin=40 onset_rel_s=303.474 persistence_bins=15
values_compact=delta:27008565248,-9437184,-1069056,-509952,-509952,-1208320,-9375744,-499712,-499712,-970752,-1069056,-518144,-518144,-530432,-530432,-9490432,-1105920,-563200,-563200,-1069056,-17956864,-552960,-552960,-1122304,-1097728,-528384,-528384,40927232,-1110016,-563200,-563200,-9478144,-1142784,-327680,-327680,-626688,-8941568,-266240,-266240,-614400,-125345792,-646684672,-646684672,-1327771648,-1293623296,-645687296,-645687296,-1191428096,-1310363648,-659179520,-659179520,-1276956672,-1169059840,-608393216,-608393216,12782571520,-479232,26513408,26513408,12701696,-10584064,-466944,-466944,-2060288
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M9] rank=9 service=ts-notification-service metric=container.filesystem.available baseline=26976871509.333332 peak=14148448256.0 signed_z=-747.908 onset_bin=40 onset_rel_s=303.474 persistence_bins=15
values_compact=delta:27008565248,-9437184,-1069056,-509952,-509952,-1208320,-9375744,-499712,-499712,-970752,-1069056,-518144,-518144,-530432,-530432,-9490432,-1105920,-563200,-563200,-1069056,-17956864,-552960,-552960,-1122304,-1097728,-528384,-528384,40927232,-1110016,-563200,-563200,-9478144,-1142784,-327680,-327680,-626688,-8941568,-266240,-266240,-614400,-125345792,-646684672,-646684672,-1327771648,-1293623296,-645687296,-645687296,-1191428096,-1310363648,-659179520,-659179520,-1276956672,-1169059840,-608393216,-608393216,12782571520,-479232,26513408,26513408,12701696,-10584064,-466944,-466944,-2060288
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M10] rank=10 service=ts-notification-service metric=k8s.pod.filesystem.available baseline=26976871509.333332 peak=14148448256.0 signed_z=-747.908 onset_bin=40 onset_rel_s=303.474 persistence_bins=15
values_compact=delta:27008565248,-9437184,-1069056,-509952,-509952,-1208320,-9375744,-499712,-499712,-970752,-1069056,-518144,-518144,-530432,-530432,-9490432,-1105920,-563200,-563200,-1069056,-17956864,-552960,-552960,-1122304,-1097728,-528384,-528384,40927232,-1110016,-563200,-563200,-9478144,-1142784,-327680,-327680,-626688,-8941568,-266240,-266240,-614400,-125345792,-646684672,-646684672,-1327771648,-1293623296,-645687296,-645687296,-1191428096,-1310363648,-659179520,-659179520,-1276956672,-1169059840,-608393216,-608393216,12782571520,-479232,26513408,26513408,12701696,-10584064,-466944,-466944,-2060288
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M11] rank=11 service=ts-preserve-service metric=container.filesystem.available baseline=26976871509.333332 peak=14148448256.0 signed_z=-747.908 onset_bin=40 onset_rel_s=303.474 persistence_bins=15
values_compact=delta:27008565248,-9437184,-1069056,-509952,-509952,-1208320,-9375744,-499712,-499712,-970752,-1069056,-518144,-518144,-530432,-530432,-9490432,-1105920,-563200,-563200,-1069056,-17956864,-552960,-552960,-1122304,-1097728,-528384,-528384,40927232,-1110016,-563200,-563200,-9478144,-1142784,-327680,-327680,-626688,-8941568,-266240,-266240,-614400,-125345792,-646684672,-646684672,-1327771648,-1293623296,-645687296,-645687296,-1191428096,-1310363648,-659179520,-659179520,-1276956672,-1169059840,-608393216,-608393216,12782571520,-479232,26513408,26513408,12701696,-10584064,-466944,-466944,-2060288
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M12] rank=12 service=ts-preserve-service metric=k8s.pod.filesystem.available baseline=26976871509.333332 peak=14148448256.0 signed_z=-747.908 onset_bin=40 onset_rel_s=303.474 persistence_bins=15
values_compact=delta:27008565248,-9437184,-1069056,-509952,-509952,-1208320,-9375744,-499712,-499712,-970752,-1069056,-518144,-518144,-530432,-530432,-9490432,-1105920,-563200,-563200,-1069056,-17956864,-552960,-552960,-1122304,-1097728,-528384,-528384,40927232,-1110016,-563200,-563200,-9478144,-1142784,-327680,-327680,-626688,-8941568,-266240,-266240,-614400,-125345792,-646684672,-646684672,-1327771648,-1293623296,-645687296,-645687296,-1191428096,-1310363648,-659179520,-659179520,-1276956672,-1169059840,-608393216,-608393216,12782571520,-479232,26513408,26513408,12701696,-10584064,-466944,-466944,-2060288
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[328.6605625152588,413.6527135372162]

=== LOG SUMMARY ===
{"entries":[{"error_logs":3321,"error_pct":19.1,"service":"ts-seat-service","total_logs":17385},{"error_logs":338,"error_pct":15.92,"service":"ts-food-service","total_logs":2123},{"error_logs":118,"error_pct":4.91,"service":"ts-preserve-service","total_logs":2405},{"error_logs":117,"error_pct":1.78,"service":"ts-order-service","total_logs":6571},{"error_logs":96,"error_pct":25.0,"service":"ts-notification-service","total_logs":384},{"error_logs":95,"error_pct":25.0,"service":"ts-delivery-service","total_logs":380},{"error_logs":6,"error_pct":5.17,"service":"ts-inside-payment-service","total_logs":116},{"error_logs":6,"error_pct":0.45,"service":"ts-travel-plan-service","total_logs":1326}],"mode":"errors","omitted_services":22,"service_count":30}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":10475.7,"error_pct":0.0,"p95_during_ms":2022.1368435,"p95_pre_ms":19.12055709999999,"service":"ts-seat-service","spans":13876},{"delta_pct":5538.5,"error_pct":0.0,"p95_during_ms":6735.210669050022,"p95_pre_ms":119.450514,"service":"ts-travel2-service","spans":5388},{"delta_pct":3852.3,"error_pct":0.0,"p95_during_ms":8233.882314999999,"p95_pre_ms":208.328801,"service":"ts-ui-dashboard","spans":7714},{"delta_pct":3836.1,"error_pct":1.23,"p95_during_ms":8235.0029884,"p95_pre_ms":209.2176015,"service":"loadgenerator","spans":7714},{"delta_pct":2771.2,"error_pct":0.0,"p95_during_ms":4102.074992,"p95_pre_ms":142.86839925000015,"service":"ts-travel-service","spans":9505},{"delta_pct":2458.0,"error_pct":0.0,"p95_during_ms":24460.520851600002,"p95_pre_ms":956.23289775,"service":"ts-travel-plan-service","spans":2333},{"delta_pct":2061.7,"error_pct":0.0,"p95_during_ms":12286.1764251,"p95_pre_ms":568.3443600999992,"service":"ts-route-plan-service","spans":1742},{"delta_pct":816.8,"error_pct":0.0,"p95_during_ms":4243.9101387,"p95_pre_ms":462.9137481999998,"service":"ts-preserve-service","spans":1549}],"omitted_services":22,"service_count":30}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=35 omitted_edges=2
[{"evidence_source":"trace","onset_rel_s":344.4,"rank":1,"service":"ts-basic-service","severity_z":42.521},{"evidence_source":"metric","onset_rel_s":353.4,"rank":2,"service":"ts-avatar-service","severity_z":747.908},{"evidence_source":"metric","onset_rel_s":353.4,"rank":3,"service":"ts-consign-price-service","severity_z":747.908},{"evidence_source":"metric","onset_rel_s":353.4,"rank":4,"service":"ts-food-service","severity_z":747.908},{"evidence_source":"metric","onset_rel_s":353.4,"rank":5,"service":"ts-news-service","severity_z":747.908},{"evidence_source":"metric","onset_rel_s":353.4,"rank":6,"service":"ts-notification-service","severity_z":747.908},{"evidence_source":"metric","onset_rel_s":353.4,"rank":7,"service":"ts-security-service","severity_z":747.908},{"evidence_source":"metric","onset_rel_s":353.4,"rank":8,"service":"ts-travel2-service","severity_z":747.908},{"evidence_source":"metric","onset_rel_s":353.4,"rank":9,"service":"ts-ui-dashboard","severity_z":747.908},{"evidence_source":"metric","onset_rel_s":353.4,"rank":10,"service":"ts-voucher-service","severity_z":747.908},{"evidence_source":"trace","onset_rel_s":354.6,"rank":11,"service":"ts-preserve-service","severity_z":3.761},{"evidence_source":"metric","onset_rel_s":378.0,"rank":12,"service":"ts-gateway-service","severity_z":209.001},{"evidence_source":"trace","onset_rel_s":454.8,"rank":13,"service":"ts-travel-service","severity_z":4.243},{"evidence_source":"trace","onset_rel_s":464.4,"rank":14,"service":"ts-station-service","severity_z":31.129}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"ts-station-service","caller":"ts-basic-service"},{"callee":"ts-travel-service","caller":"ts-food-service"},{"callee":"ts-basic-service","caller":"ts-preserve-service"},{"callee":"ts-food-service","caller":"ts-preserve-service"},{"callee":"ts-security-service","caller":"ts-preserve-service"},{"callee":"ts-travel-service","caller":"ts-preserve-service"},{"callee":"ts-basic-service","caller":"ts-travel-service"},{"callee":"ts-basic-service","caller":"ts-travel2-service"},{"callee":"ts-food-service","caller":"ts-ui-dashboard"},{"callee":"ts-preserve-service","caller":"ts-ui-dashboard"},{"callee":"ts-travel-service","caller":"ts-ui-dashboard"},{"callee":"ts-travel2-service","caller":"ts-ui-dashboard"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

[excluded before optimizer]
