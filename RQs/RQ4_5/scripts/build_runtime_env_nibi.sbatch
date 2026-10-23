#!/usr/bin/env bash
# Reproducible Alliance-wheel environment; no GPU or model invocation.
#SBATCH --account=def-jacobsen_cpu
#SBATCH --partition=cpubase_bycore_b1
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --hint=nomultithread
#SBATCH --mem=32G
#SBATCH --time=00:30:00
#SBATCH --job-name=rq45-runtime-env
#SBATCH --no-requeue
set -euo pipefail
repo="${CANVASRCA_NIBI_REPO:-/home/lglsj/CanvasRCA_20261018}"
cd "$repo"
module load StdEnv/2023 python/3.11.5 cuda/12.9 arrow/18.1.0 opencv/4.13.0
cache_root=/project/def-jacobsen/canvasrca_cache/RQ4_5
env_root="$cache_root/runtime_env/infer_20261019_v2"
mkdir -p "$cache_root/runtime_env"
[[ ! -e "$env_root" ]] || { echo 'Environment already exists; inspect its receipt instead of overwriting.' >&2; exit 1; }
module -t list >"$cache_root/runtime_env/modules_v2.txt" 2>&1
virtualenv --no-download "$env_root"
source "$env_root/bin/activate"
export PYTHONNOUSERSITE=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
export PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
python - "$cache_root" <<'PY'
import sys
from pathlib import Path
root=Path(sys.argv[1]);requirements=(root/'runtime_requirements_before.txt').read_text().splitlines()
# Pillow-SIMD metadata is stale: the actual qualified PIL import is Pillow 12.1.
# Keep that actual implementation, every other pin and every Alliance wheel URL.
requirements=[r for r in requirements if not r.lower().startswith(('canvasrca ', 'pillow_simd==','numpy==','scipy==','xgrammar=='))]
requirements.append('opencv-python-headless==4.9999')
(root/'runtime_env/requirements_v2.txt').write_text('\n'.join(requirements)+'\n')
PY
python -m pip install --no-index --upgrade pip
python -m pip install --no-index --ignore-installed --no-deps -r "$cache_root/runtime_env/requirements_v2.txt"
python - "$cache_root" <<'PY'
import csv,hashlib,json,shutil,sys,sysconfig
from pathlib import Path
old=Path('/scratch/lglsj/CanvasRCA/.venv-inference');source=old/'lib/python3.11/site-packages'
new=Path(sys.prefix);retained={}
# Exact old versions are absent from today's wheelhouse. Preserve their actual
# qualified binaries instead of changing numerical or grammar implementations.
# Copy every installed RECORD entry, including private shared-library folders.
for name,version in (('numpy','2.3.5'),('scipy','1.16.3'),('xgrammar','0.2.3')):
    info=source/(name+'-'+version+'.dist-info');rows=list(csv.reader((info/'RECORD').read_text().splitlines()));files=[]
    for relative,*_ in rows:
        original=(source/relative).resolve()
        if not original.is_relative_to(old.resolve()):raise RuntimeError('Package RECORD escapes old environment')
        if not original.is_file():raise RuntimeError('Missing qualified package file '+str(original))
        target=new/original.relative_to(old.resolve());target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(original,target)
        sha=hashlib.sha256(original.read_bytes()).hexdigest()
        if hashlib.sha256(target.read_bytes()).hexdigest()!=sha:raise RuntimeError('Runtime package copy differs')
        files.append({'path':str(original.relative_to(old.resolve())),'sha256':sha})
    retained[name]={'version':version,'reason':'exact version unavailable in current Alliance wheelhouse','files':files}
(Path(sys.argv[1])/'runtime_env/exact_package_carry_v2.json').write_text(json.dumps(retained,indent=2))
PY
python -m pip install --no-index --no-build-isolation --no-deps .
# Project namespace/source packages and the exact native cache provider use a
# .pth file; retain the Python module's own initialization paths unmodified.
python - "$repo" <<'PY'
import sys,sysconfig
from pathlib import Path
paths=[sys.argv[1]+'/src',sys.argv[1],'/project/def-jacobsen/canvasrca_cache/shared/flashinfer/cache_provider_0.6.12']
(Path(sysconfig.get_paths()['purelib'])/'canvasrca_rq45_runtime.pth').write_text('\n'.join(paths)+'\n')
PY
python -m pip check
python - "$cache_root" <<'PY'
import hashlib,importlib,importlib.metadata as md,json,os,sys,time
from pathlib import Path
root=Path(sys.argv[1]);records={}
for name in ('torch','transformers','vllm','flashinfer','xgrammar','cv2','PIL','scorer'):
    began=time.monotonic();module=importlib.import_module(name)
    records[name]={'seconds':time.monotonic()-began,'file':str(module.__file__),'version':str(getattr(module,'__version__',None))}
requirements=root/'runtime_env/requirements_v2.txt'
result={'schema':'RQ45AllianceRuntimeEnvironmentV1','status':'passed','new_model_calls':0,
    'python':sys.executable,'prefix':sys.prefix,'modules':os.environ.get('LOADEDMODULES'),
    'imports':records,'requirements_sha256':hashlib.sha256(requirements.read_bytes()).hexdigest(),
    'packages':{d.metadata['Name']:d.version for d in md.distributions()},'pip_check':'passed',
    'scientific_note':'Weights, prompts, PNGs, decoding and post-merger token operations are unchanged; targeted packet equivalence and GPU speed qualification remain pending.'}
(root/'runtime_env/build_v2.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2),flush=True)
PY
