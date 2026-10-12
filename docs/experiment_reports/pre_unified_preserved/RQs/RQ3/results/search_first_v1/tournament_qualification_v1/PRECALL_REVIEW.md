# Tournament qualification — 2026-09-12 local date

This is one logical six-call smoke: three training cases, Qwen then Gemma,
one frozen-template typed-overview method. At most nine attempts per model
and eighteen overall, one shared 600-second deadline. No training, no new
attention, no tournament/eval retirement. Candidate entities remain text.

CPU/renderer regression: 375 passed in 78.73 seconds. Local inference imports
pass using the existing infer environment; no package was installed or changed.
Three actual PNGs were opened and checked. Their source SHA256, prompt SHA256,
public-pool audits, numeric candidates and clipping results are recorded in
the sibling tournament_qualification_gallery_v1/cpu_review.json and review.json.
The static template clarification names optional SERVICE/NODE/POD label words
and asks for the final JSON based on the evidence, not before reading it.
No PNG or selected fact changed in that clarification.

New request tests separately exercise both model recipes with identical parts;
Gemma does not inherit Qwen's sampling adapter. The request worker and vLLM
server both use infer. Tools handles preparation. Torch-dependent CPU unit
tests ran with CUDA disabled in train and never touched real checkpoints.

The generic recovery register now consults the latest state of each request,
while retaining earlier failure attempts. Separate model success sets, frozen
cohorts, no repeated retired cases, threshold transitions and interrupted
request history have synthetic CPU tests. These are not RCA efficacy results.
