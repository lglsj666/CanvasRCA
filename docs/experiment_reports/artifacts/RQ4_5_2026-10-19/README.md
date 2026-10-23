# RQ4.5 final analysis artifacts

These are offline, label-bearing analysis outputs, never model inputs. Original
responses and registered scores remain unchanged. The main report is
`../../RQ4_5_Qwen_Analysis_2026-10-19.md`.

Reproduction from the repository root, using the existing inference environment
for NumPy/SciPy/Matplotlib (no model loading or inference):

```bash
/home/lglsj/CanvasRCA/venvs/infer/bin/python docs/experiment_reports/artifacts/RQ4_5_2026-10-19/supplement.py
/home/lglsj/CanvasRCA/venvs/infer/bin/python docs/experiment_reports/artifacts/RQ4_5_2026-10-19/plots.py
/home/lglsj/CanvasRCA/venvs/infer/bin/python docs/experiment_reports/artifacts/RQ4_5_2026-10-19/write_report.py
```

`supplement.py` also executes `analyze.py`; it is unnecessary to run the latter
first. The CSV/JSON tables retain full precision. Unit-alias sensitivity is
post-hoc, separate from the registered tolerant score. All 180 QA/RCA pairs have
structured analysis; the actual full-response manual review covers the disclosed
54 pairs in nine cases, not all 1,320 RCA outputs. Historical comparisons are not
contemporary randomized controls. Attention covers layer 3's last-prompt and
first-decode queries, not final-decision attention.

The report classifies H_TOPOLOGY and H_TOPO_MARGINAL by their actual payload:
topology is carried by images. The stale generic reading sentence is an
unmeasured wording caveat, not evidence that topology remained in text.

`delivery_verification.json` records final links, provenance, preserved status
predecessors, and storage accounting including this directory. Rerunning analysis
changes derived file hashes, so an old delivery receipt describes its original
snapshot. No experimental response needs to be regenerated.
