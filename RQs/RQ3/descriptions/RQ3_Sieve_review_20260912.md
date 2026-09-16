# Sieve — transfer assessment, 2026-09-12

**Identity.** Jörg Thalheim, Antonio Rodrigues, Istemi Ekin Akkus, Pramod
Bhatotia, Ruichuan Chen, Bimal Viswanath, Lei Jiao, Christof Fetzer.
*Sieve: Actionable Insights from Monitored Metrics in Distributed Systems*.
Middleware 2017; DOI 10.1145/3135974.3135977.
[Official project](https://sieve-microservices.github.io/),
[paper](https://sieve-microservices.github.io/assets/sieve-middleware-2017.pdf).

**Read scope.** Main paper through conclusions, including methods, evaluation
and lessons; extended technical-report experiments not reviewed.

**Mechanism/evidence.** Controlled workloads, per-component k-Shape reduction
and dependency analysis support autoscaling and debugging. ShareLatex reduction
is 889 to 65 metrics, not VLM RCA accuracy. The main RCA example compares correct
and faulty OpenStack versions; Neutron appears third. Its similarity threshold
can remove useful networking evidence. Complex dependencies need not form a
tree or expose an obvious root. Application-specific signals remain important.

**Transfer decision.** Keep representative selection and relationship structure
as separate hypotheses. Current single-incident data do not recreate paired
software versions or controlled stress workloads. Do not import its performance
claims, treat predictive dependencies as physical causality, or call SEARCH29's
quantile heuristic a Sieve implementation. Our unchanged-scorer train experiment
must establish any benefit.

**Implementation status.** The [official analysis repository](https://github.com/sieve-microservices/scalegraph-scripts)
and rendered README were inspected; repository archived March 2022. It lists
preprocessing, clustering, dependency analysis and Redis workers. The initial
uppercase README raw URL failed; GitHub shows `Readme.md`. Source algorithms
are not yet audited or vendored; no runtime dependency was introduced.
