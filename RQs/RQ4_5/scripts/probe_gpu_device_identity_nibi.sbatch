#!/usr/bin/env bash
#SBATCH --account=def-jacobsen_gpu
#SBATCH --partition=gpubase_bygpu_b1
#SBATCH --gpus=h100:1
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G
#SBATCH --time=00:03:00
#SBATCH --job-name=rq45-device-id-probe
#SBATCH --no-requeue
set -euo pipefail
cd /home/lglsj/CanvasRCA_20261018
source RQs/RQ4_5/scripts/runtime_environment_nibi.sh
"$python_bin" -B -u - <<'PROBE'
import torch,pynvml,os,time,json,uuid
from RQs.RQ4_5.src.utils import RESULTS,save
pynvml.nvmlInit()
prop=torch.cuda.get_device_properties(0);raw=prop.uuid;torch_id=str(raw)
handle=pynvml.nvmlDeviceGetHandleByUUID(torch_id);nvml_raw=pynvml.nvmlDeviceGetUUID(handle)
nvml_id=nvml_raw.decode() if isinstance(nvml_raw,bytes) else str(nvml_raw)
def normalize(s):return str(uuid.UUID(s.removeprefix('GPU-').removeprefix('gpu-')))
record={'status':'measured','job_id':os.environ['SLURM_JOB_ID'],'CUDA_VISIBLE_DEVICES':os.environ.get('CUDA_VISIBLE_DEVICES'),
 'torch_raw_repr':repr(raw),'torch_raw_type':type(raw).__name__,'torch_id':torch_id,
 'nvml_raw_repr':repr(nvml_raw),'nvml_raw_type':type(nvml_raw).__name__,'nvml_id':nvml_id,
 'raw_equal':torch_id==nvml_id,'canonical_equal':normalize(torch_id)==normalize(nvml_id),'GPU_name':prop.name,
 'normalized_torch':normalize(torch_id),'normalized_nvml':normalize(nvml_id),'model_calls':0,'unix':time.time()}
save(RESULTS/'qualification/device_uuid_probe_v1.json',record);print(json.dumps(record,indent=2),flush=True)
assert record['canonical_equal'],'Genuinely different CUDA and NVML devices'
PROBE
