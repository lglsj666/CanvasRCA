#!/bin/bash
CANVASRCA_ROOT="${CANVASRCA_ROOT:-/home/lglsj/CanvasRCA}"
JOB=$(cat "$CANVASRCA_ROOT/.bakeoff_jobid")
cd "$CANVASRCA_ROOT"
while squeue -j "$JOB" -h 2>/dev/null | grep -q "$JOB"; do sleep 120; done
echo "=== array $JOB left the queue at $(date) ==="
sacct -j "$JOB" --format=JobID,JobName,State,Elapsed,ExitCode -n 2>/dev/null | grep -vE '\.(ba|ex)' | head
echo ""
source scripts/env.sh >/dev/null 2>&1
python - <<'PY'
import json, glob, os
def row(p):
    d=json.load(open(p))
    return (d.get('model','?'), d.get('mrr',0), d.get('top1',0), d.get('parse_rate',0),
            d.get('avg_total_tokens',0), d.get('avg_wall_clock_s',0))
print(f"{'model':<26}{'MRR':>7}{'Top1':>7}{'parse':>7}{'tok':>9}{'s/case':>8}")
print("-- thinking (default, first run) --")
for tag in ('qwen3.5-9b','qwen3.5-4b','qwen3.6-27b'):
    p=f"RQs/RQ3/results/bakeoff_{tag}/summary.json"
    if os.path.exists(p):
        m,mrr,t1,pr,tok,s=row(p); print(f"{m:<26}{mrr:>7.3f}{t1:>7.3f}{pr:>7.3f}{tok:>9.0f}{s:>8.1f}")
print("-- no-thinking (enable_thinking=False, presence_penalty=1.5) --")
for tag in ('qwen3.5-9b','qwen3.5-4b','qwen3.6-27b'):
    p=f"RQs/RQ3/results/bakeoff_nothink_{tag}/summary.json"
    if os.path.exists(p):
        m,mrr,t1,pr,tok,s=row(p); print(f"{'nothink_'+m:<26}{mrr:>7.3f}{t1:>7.3f}{pr:>7.3f}{tok:>9.0f}{s:>8.1f}")
    else:
        print(f"{'nothink_'+tag:<26}  NO SUMMARY (check logs)")
print("\nreference gemma-4-e4b (thinking-free): MRR 0.508 parse 1.00 5.7 s/case | sonnet-5 0.797")
PY
if ! ls RQs/RQ3/results/bakeoff_nothink_qwen*/summary.json >/dev/null 2>&1; then
  SRV=$(ls -t RQs/RQ3/results/sbatch_logs/bakeoff_nothink_*_${JOB}_*.server.log 2>/dev/null | head -1)
  echo ""; echo "=== first server-log errors ($SRV) ==="
  grep -niE "error|runtimeerror|could not|no module|failed|not found|traceback|out of memory|connection" "$SRV" 2>/dev/null | grep -viE "gpu-memory|error_stack|log-error" | tail -15
fi
