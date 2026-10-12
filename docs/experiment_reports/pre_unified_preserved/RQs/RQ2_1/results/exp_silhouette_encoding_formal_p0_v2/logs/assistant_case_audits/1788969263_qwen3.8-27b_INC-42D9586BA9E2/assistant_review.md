# Assistant recovery-time case audit — 2026-09-09 15:55 UTC

Randomly selected a previously unaudited complete case from the records saved
since the prior audit. This does not retroactively claim monitoring while WSL
was disconnected. All 12 arm outputs, ordered input fragments and all 12 actual
submitted dashboard PNGs were reviewed. Machine checks verified conversation
completeness, actual request image hashes, candidate identity and both prefill
and answer-token attention arrays. All arms use P0/D0, with S0 request reuse.

Every answer stops normally, parses, uses permitted candidate IDs and contains
139–220 output tokens. The images contain twelve metric series, six trace rows,
two LT9537 observations at different relative bins, and the selected directed
edges. Overlay legends distinguish the compatible series; matrix and layered
graph alternatives retain the directed edges and selected isolated nodes.
No wrong-case image, blank/missing region, or demonstrated persistence defect
was found. Private labels and accuracy scores were not opened.

Public reasons sometimes conflate M1's 955 with M2's 402, reverse a temporal
comparison (12.3 versus 12.2 minutes), or invent a conversion-error event even
though the supplied template says successful. These are model-reading/reasoning
errors; the corresponding evidence is present in the input. Do not change the
registered prompt or resample those answers. Continue the run. This case-level
review cannot prove correctness for the entire corpus.
