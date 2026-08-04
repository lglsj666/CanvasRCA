#!/bin/bash
CANVASRCA_ROOT="${CANVASRCA_ROOT:-/home/lglsj/CanvasRCA}"
JOB=$(cat "$CANVASRCA_ROOT/.bakeoff_jobid")
cd "$CANVASRCA_ROOT"
while squeue -j "$JOB" -h 2>/dev/null | grep -q "$JOB"; do sleep 120; done
echo "=== job $JOB left the queue at $(date) ==="
sacct -j "$JOB" --format=JobID,JobName,State,Elapsed,ExitCode -n 2>/dev/null | head -3
echo "=== bake-off summaries ==="
source scripts/env.sh >/dev/null 2>&1
python - <<'PY'
import json, glob, os
rows=[]
for p in sorted(glob.glob("RQs/RQ3/results/bakeoff_*/summary.json")):
    try: d=json.load(open(p))
    except Exception: continue
    rows.append((d.get("model",os.path.basename(os.path.dirname(p))),d.get("mrr",0),d.get("top1",0),d.get("parse_rate",0),d.get("avg_total_tokens",0),d.get("avg_wall_clock_s",0)))
if rows:
    rows.sort(key=lambda r:-r[1])
    print(f"{'model':<18}{'MRR':>7}{'Top1':>7}{'parse':>7}{'tok':>9}{'s/case':>8}")
    for m,mrr,t1,pr,tok,s in rows: print(f"{m:<18}{mrr:>7.3f}{t1:>7.3f}{pr:>7.3f}{tok:>9.0f}{s:>8.1f}")
    print("\nreference: claude-sonnet-5 AegisLab n=20 = MRR 0.797 (text SOTA 0.679)")
else:
    print("NO SUMMARIES")
PY
# On failure, surface the main out + first server-log tail for immediate diagnosis.
if ! ls RQs/RQ3/results/bakeoff_*/summary.json >/dev/null 2>&1; then
  echo ""; echo "=== main out tail ==="; tail -20 RQs/RQ3/results/sbatch_logs/bakeoff_${JOB}.out 2>/dev/null
  SRV=$(ls -t RQs/RQ3/results/sbatch_logs/bakeoff_*_${JOB}.server.log 2>/dev/null | head -1)
  echo ""; echo "=== first server-log ERROR/root-cause lines ($SRV) ==="
  grep -niE "error|runtimeerror|could not|no module|failed|not found|traceback|out of memory|oom" "$SRV" 2>/dev/null | grep -viE "gpu-memory|error_stack|log-error" | tail -25
fi
