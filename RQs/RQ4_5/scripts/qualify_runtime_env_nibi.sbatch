#!/usr/bin/env bash
# Targeted old/new processor-byte equivalence, not a new population regression.
#SBATCH --account=def-jacobsen_cpu
#SBATCH --partition=cpubase_bycore_b1
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --hint=nomultithread
#SBATCH --mem=16G
#SBATCH --time=00:15:00
#SBATCH --job-name=rq45-env-equivalence
#SBATCH --no-requeue
set -euo pipefail
repo="${CANVASRCA_NIBI_REPO:-/home/lglsj/CanvasRCA_20261018}"
cd "$repo"
module load StdEnv/2023 python/3.11.5 cuda/12.9 arrow/18.1.0 opencv/4.13.0
export CANVASRCA_RQ45_ROOT=/project/def-jacobsen/canvasrca_cache/RQ4_5/cpu_v1
export CANVASRCA_RQ45_SOURCE_ROOT=/project/def-jacobsen/canvasrca_cache/RQ4_5/source_dependencies
export CANVASRCA_QWEN_MODEL=/scratch/lglsj/CanvasRCA/models/Qwen3.8-27B
export CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false
export PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
old_python=/scratch/lglsj/CanvasRCA/.venv-inference/bin/python
new_python=/project/def-jacobsen/canvasrca_cache/RQ4_5/runtime_env/infer_20261019_v2/bin/python
[[ -f /project/def-jacobsen/canvasrca_cache/RQ4_5/runtime_env/build_v2.json ]]
module_pythonpath="${PYTHONPATH:-}"
for version in old new; do
  if [[ "$version" == old ]]; then
    interpreter="$old_python"
    export PYTHONPATH="$repo/src:$repo"
  else
    interpreter="$new_python"
    export PYTHONPATH="$module_pythonpath"
  fi
  "$interpreter" -B - "$version" <<'PY'
import hashlib,json,sys,time
from RQs.RQ4_5.src.utils import RESULTS,MODEL,read,save,vllm_prompt_packet,stable
from transformers import AutoProcessor
version=sys.argv[1];processor=AutoProcessor.from_pretrained(MODEL,local_files_only=True)
rows=[];seen=set();qa_cases=set()
for entry in read(RESULTS/'frozen/smoke_queue.json'):
    request=entry['request'];arm=entry['item']['arm']
    if request['task']=='RCA':
        if arm in seen:continue
        seen.add(arm)
    else:
        if entry['item']['id'] in qa_cases:continue
        qa_cases.add(entry['item']['id'])
    began=time.monotonic();packet=vllm_prompt_packet(request,processor)
    tensors={k:{'shape':list(v.shape),'dtype':str(v.dtype),
        'sha256':hashlib.sha256(v.contiguous().view(__import__('torch').uint8).numpy().tobytes()).hexdigest()}
        for k,v in packet['batch'].items()}
    meta={k:v for k,v in packet.items() if k!='batch'}
    rows.append({'key':entry['item']['key'],'request_identity':request['identity'],
        'tensor_hashes':tensors,'packet_metadata_sha256':stable(meta),'seconds':time.monotonic()-began})
if len(seen)!=6 or len(qa_cases)!=3:raise RuntimeError('All six arms and three QA cases must be represented')
save(RESULTS/'qualification'/f'runtime_env_{version}_packets.json',{'status':'passed','new_model_calls':0,'rows':rows})
if version=='new':
    previous=read(RESULTS/'qualification/runtime_env_old_packets.json')['rows']
    strip=lambda rs:[{k:v for k,v in r.items() if k!='seconds'} for r in rs]
    if strip(previous)!=strip(rows):raise RuntimeError('Environment changes actual processor inputs')
    save(RESULTS/'qualification/runtime_env_equivalence.json',{
        'status':'passed','scope':'six fixed RCA inputs and three QA inputs, covering every arm and all three fixed datasets',
        'byte_identical_processor_packets':True,'new_model_calls':0,'rows':rows,
        'unchanged_full_population_CPU_evidence_reused':True,
        'new_environment':'/project/def-jacobsen/canvasrca_cache/RQ4_5/runtime_env/infer_20261019_v2'})
print(json.dumps({'version':version,'verified_packets':len(rows),'new_model_calls':0}),flush=True)
PY
done
