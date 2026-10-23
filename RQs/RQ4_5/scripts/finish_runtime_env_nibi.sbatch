#!/usr/bin/env bash
# Complete import qualification of the already installed environment; no reinstall.
#SBATCH --account=def-jacobsen_cpu
#SBATCH --partition=cpubase_bycore_b1
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --hint=nomultithread
#SBATCH --mem=16G
#SBATCH --time=00:10:00
#SBATCH --job-name=rq45-env-imports
#SBATCH --no-requeue
set -euo pipefail
repo="${CANVASRCA_NIBI_REPO:-/home/lglsj/CanvasRCA_20261018}"
cd "$repo"
module load StdEnv/2023 python/3.11.5 cuda/12.9 arrow/18.1.0 opencv/4.13.0
export PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
cache_root=/project/def-jacobsen/canvasrca_cache/RQ4_5
source "$cache_root/runtime_env/infer_20261019_v2/bin/activate"
python -B - "$cache_root" <<'PY'
import hashlib,importlib,importlib.metadata as md,json,os,subprocess,sys,time
from pathlib import Path
root=Path(sys.argv[1]);records={}
if not (root/'runtime_env/exact_package_carry_v2.json').is_file():raise RuntimeError('Exact package transfer incomplete')
check=subprocess.run([sys.executable,'-m','pip','check'],capture_output=True,text=True)
lines=set((check.stdout+check.stderr).strip().splitlines())
expected={
 'opencv-python-headless 4.9999+dummy.computecanada requires opencv-noinstall, which is not installed.',
 'torchvision 0.26.0+computecanada requires pillow-simd, which is not installed.'}
if check.returncode!=1 or lines!=expected:raise RuntimeError('Unexpected dependency audit: '+repr(lines))
# Do not fake distributions, replace PIL pixels, or claim pip check succeeded.
# Alliance OpenCV's dummy wheel explicitly asks for the module, loaded above.
# Preserve qualified Pillow 12.1 rather than overwrite it with Pillow-SIMD;
# actual processor-byte equivalence remains an independent mandatory gate.
for name in ('torch','transformers','vllm','flashinfer','xgrammar','cv2','PIL','scorer'):
 began=time.monotonic();module=importlib.import_module(name)
 records[name]={'seconds':time.monotonic()-began,'file':str(module.__file__),
                'version':str(getattr(module,'__version__',None))}
if records['cv2']['version']!='4.13.0' or '/opencv/4.13.0/' not in records['cv2']['file']:
 raise RuntimeError('Actual OpenCV must come from the loaded Alliance module')
if records['PIL']['version']!='12.1.0':raise RuntimeError('Qualified PIL implementation changed')
requirements=root/'runtime_env/requirements_v2.txt'
result={'schema':'RQ45AllianceRuntimeEnvironmentV2','status':'passed','new_model_calls':0,
 'python':sys.executable,'prefix':sys.prefix,'modules':os.environ.get('LOADEDMODULES'),
 'imports':records,'requirements_sha256':hashlib.sha256(requirements.read_bytes()).hexdigest(),
 'packages':{d.metadata['Name']:d.version for d in md.distributions()},
 'pip_check':{'status':'documented_module_metadata_exceptions','exit_code':check.returncode,
              'raw_stdout':check.stdout,'raw_stderr':check.stderr,'exceptions':sorted(expected),
              'not_a_claim_of_dependency_metadata_consistency':True},
 'prior_build_job':'24585572','build_resume':'packages already installed; only import audit resumed',
 'scientific_note':'Imports passed; actual old/new processor-byte equivalence and GPU qualification remain mandatory.'}
(root/'runtime_env/build_v2.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2),flush=True)
PY
