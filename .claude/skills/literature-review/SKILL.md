---
name: literature-review
description: Find, verify, read, compare, and synthesize primary research for CanvasRCA. Use when searching for papers or code, checking a citation or venue claim, preparing related work, mapping literature to an RQ or implementation module, updating the project reference guide, or deriving an evidence-backed research or experiment decision from the literature.
---

# CanvasRCA literature review

Treat the project guide as a search map, not as proof. Verify every paper,
status, result, and code link against a primary source before citing it.

## Establish the question

1. Read `Codex.md`, the target RQ description, and its latest applicable plan.
2. Consult
   [`references/reference-guide.md`](references/reference-guide.md).
   For a focused request, read sections 0, 9, and 10 plus the relevant keyword,
   P0/P1, and “迷茫时查哪篇” entries. For a project-wide review or guide update,
   read the guide completely.
3. State the question, decision it informs, claims needing evidence, date range,
   and inclusion/exclusion criteria before searching.
4. If RQ numbering or status conflicts across artifacts, report the conflict and
   search against the question text; do not silently choose a numbering scheme.

## Search and qualify sources

- Derive queries from the guide's seven keyword families: reward/judge,
  process reward, credit assignment, multi-agent/co-evolution, dashboard/chart,
  RCA/observability, and component contribution/scorer fidelity.
- Prefer 2025–2026 work, then add older papers only when they provide a
  foundational definition, method, benchmark, or measurement tool.
- Search primary sources only for technical claims: official proceedings or
  publisher pages, the authors' paper/project page, arXiv, and the official
  repository. Do not cite search-result snippets, aggregators, or secondary
  summaries as evidence.
- Verify title, authors, version date, venue/status, DOI or canonical paper URL,
  and official code independently. If acceptance cannot be verified from an
  authoritative source, label the work `preprint`; never infer a venue from a
  repository, filename, or guide entry.
- Keep a rejected-source note when a result is only name-similar, lacks a
  relevant experiment, has untraceable metadata, or cannot support the intended
  claim.

## Read each paper for transferable evidence

Read the abstract, introduction, method, experimental setup, main results,
ablations, limitations, and conclusion. Inspect the official code or README
when the task concerns implementation or reproducibility. Extract:

- exact research question and claimed contribution;
- model, modality, agent roles, inputs, outputs, and supervision;
- objective, reward, process/step target, credit unit, and intervention;
- datasets, partitions, baselines, budgets, metrics, and statistical design;
- central result with its comparison context, not an isolated headline number;
- failure modes, limitations, and what the paper does not establish;
- official code availability and implementation-relevant modules;
- CanvasRCA module/RQ mapping and the conditions required for transfer.

Use [`references/paper-record.md`](references/paper-record.md) when reviewing
several papers, creating durable notes, or making a load-bearing design choice.

## Synthesize rather than enumerate

Organize the review by mechanism or decision, not by a sequence of paper
summaries. Build a comparison matrix when three or more papers differ along
repeated dimensions such as:

- outcome reward versus process reward;
- absolute score versus pairwise or group-relative credit;
- scorer training versus policy optimization;
- static collaboration versus genuine co-evolution;
- added information versus alternative encoding or arrangement;
- in-distribution performance versus unseen-partner or cross-system transfer.

For every conclusion, distinguish:

1. what a source directly demonstrates;
2. what is an inference for CanvasRCA;
3. what still requires an experiment.

Map useful findings to Builder, Solver, Scorer/PRM, credit assignment,
co-evolution, verifier, or dashboard renderer. Describe rejected transfers too;
a method being relevant does not make its assumptions compatible.

## Preserve conceptual boundaries

- GiGPO/HGPO train policies; they are not scorer-training methods.
- VisualPRM step correctness is not dashboard-action correctness; use
  conditional promise/progress or downstream utility for dashboard actions.
- A Shapley value is not automatically causal. State the baseline, coalition
  distribution, budget reallocation, and intervention semantics.
- A learned or dynamic scorer is a surrogate, never the final truth; retain a
  frozen external RCA verifier.
- Joint training is not co-evolution without generated/snapshotted populations
  or data, selection, changing partners/distributions, and cross-play.
- Strong performance with a paired partner does not establish unseen-partner or
  cross-system generalization.
- Rendering the same telemetry as pixels changes representation and inductive
  bias; it does not by itself add information.
- For modality claims, preserve CanvasRCA's strict atomic-fact equality and
  prompt-composition rules. Literature cannot justify relaxing them.

## Report with a claim ledger

Return the decision first, followed by the minimum evidence needed to audit it.
Include:

- question and search scope;
- inclusion/exclusion criteria and queries when the search is substantial;
- a source-comparison or claim-to-source table;
- consensus, disagreements, gaps, and uncertainty;
- concrete implications for the target RQ, experiment, or module;
- references linked to canonical primary sources, with venue/preprint and code
  status stated accurately.

Place citations next to the claims they support. Prefer paraphrase and observe
source quotation limits. Do not cite a paper for a broader proposition than its
data and design establish.

If writing artifacts is requested, put RQ-specific literature notes under
`RQs/<rq>/descriptions/`; place a conclusion under `findings/` only after the RQ
is complete. Update the shared reference guide only when explicitly requested.
Do not write RQ material to project-root `docs/`, `plans/`, or `devlog/`.
