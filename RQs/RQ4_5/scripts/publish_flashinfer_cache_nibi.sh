#!/usr/bin/env bash
# Publish the exact compiled GDN binary through FlashInfer's precompiled-cache
# package interface. No installed package, kernel, model or input is modified.
set -euo pipefail
build_job="${1:?Completed CPU dependency build job required}"
exec python3 - "$build_job" <<'PY'
import hashlib,json,os,subprocess,sys,time
from pathlib import Path
job=sys.argv[1]
rows=subprocess.run(['sacct','-n','-P','-j',job,'--format=JobIDRaw,State,ExitCode'],
    capture_output=True,text=True,check=True).stdout.splitlines()
state=next((r.split('|')[1:3] for r in rows if r.split('|')[0]==job),None)
if state!=['COMPLETED','0:0']:raise RuntimeError('CPU compiler is not successfully terminal: '+str(state))
shared=Path('/project/def-jacobsen/canvasrca_cache/shared/flashinfer')
build=shared/'0.6.12/90a/cached_ops/gdn_prefill_sm90'
binary=build/'gdn_prefill_sm90.so'
def sha(path):
    result=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda:stream.read(1048576),b''):result.update(chunk)
    return result.hexdigest()
binary_sha=sha(binary)
destination=shared/'precompiled_0.6.12_sm90a/gdn_prefill_sm90/gdn_prefill_sm90.so'
destination.parent.mkdir(parents=True,exist_ok=True)
if destination.exists():
    if sha(destination)!=binary_sha:raise RuntimeError('Different precompiled binary already published')
else:os.link(binary,destination)
if sha(destination)!=binary_sha:raise RuntimeError('Native binary identity changed')
package=shared/'cache_provider_0.6.12/flashinfer_jit_cache'
package.mkdir(parents=True,exist_ok=True)
source=('"""Local index for the exact installed FlashInfer 0.6.12 H100 GDN binary."""\n'
    '__version__ = "0.6.12"\n'
    'def get_jit_cache_dir():\n'
    '    return '+repr(str(destination.parent.parent.resolve()))+'\n')
module=package/'__init__.py'
if module.exists() and module.read_text()!=source:raise RuntimeError('Different cache provider exists')
module.write_text(source)
manifest={'schema':'RQ45SameKernelPrecompiledCacheV1','status':'passed','cpu_build_job':job,
    'published_unix':time.time(),'architecture':'sm90a (registered H100 only)',
    'flashinfer_version':'0.6.12','build_graph_sha256':sha(build/'build.ninja'),
    'native_binary':str(binary),'native_binary_sha256':binary_sha,
    'published_binary':str(destination),'published_binary_sha256':sha(destination),
    'provider_path':str(package.parent),'provider_sha256':sha(module),
    'mechanism':'Official flashinfer_jit_cache get_jit_cache_dir interface; identical .so, no JIT graph/path regeneration',
    'weights_precision_inputs_and_registered_worker_unchanged':True,'new_model_calls':0}
out=shared/'rq45_precompiled_manifest.json'
tmp=out.with_suffix('.tmp');tmp.write_text(json.dumps(manifest,indent=2)+'\n');tmp.replace(out)
print(json.dumps(manifest,indent=2))
PY
