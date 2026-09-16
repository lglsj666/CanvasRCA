# Focused reread: an estimated anomaly window is not the root's ground truth

2026-09-12. Question: can a public but inaccurate temporal guide distract the
visual Solver? This is a future hypothesis, not a change to SEARCH22.

Local observation: in train example INC-4BA2D386B400, NODE4609's CPU plateau
visibly precedes the pale estimated interval. Existing task guidance gives
less weight to events outside that interval. The plot uses a public heuristic,
not the private injection time; discrepancy is not label leakage. No claim
that this single pattern explains the complete error rate. Preserve all runs.

BARO (Pham,Ha,Zhang; FSE2024, DOI10.1145/3660805) explicitly studies
sensitivity to estimated anomaly timing. Its median/IQR scorer is intended
to be less sensitive than mean/std-based alternatives. The paper's setting
is metric-based RCA on three applications, not dashboard VLM evaluation;
it motivates a timing-sensitivity test here, not a promised accuracy gain.
[Paper, especially Sections3.4.2 and4.8](https://arxiv.org/html/2405.09330v1).

Important implementation distinction: paper Algorithm1 uses absolute
standardized deviation, whereas the pinned0.1.9 source uses the signed
maximum after RobustScaler. It also preprocesses periods separately. Neither
behavior is silently rewritten or described as identical. Any future native
component test must preserve/tag its actual implementation and use only a
public inferred split, never the argument's label-derived injection time.
[Official0.1.9 source](https://raw.githubusercontent.com/phamquiluan/baro/0.1.9/baro/root_cause_analysis.py).

AAAI2024's *Root Cause Analysis in Microservice Using Neural Granger Causal
Discovery* (Lin et al.) identifies temporal ordering as relevant to its causal
model. Only the proceedings abstract/metadata were checked in this focused
pass; no new implementation or effectiveness claim is taken from it.
[Official record](https://ojs.aaai.org/index.php/AAAI/article/view/27772).

Potential next bounded intervention: keep complete source time series but
remove or soften the single heuristic time anchor, with an explicit matching
static reading guide. Do not replace it by true onset, change processed data,
or assume that every pre-anchor anomaly is causal. First finish SEARCH22.
No shared guide edit, new library dependency, model call or policy promotion
results from this reading note.
