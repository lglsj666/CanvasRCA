"""Explicit source-bound organization exports; ordinary components are unchanged."""
from pathlib import Path
import json,os,subprocess
from ..utils import ROOT,RENDERER
from ..main import node_runtime

MODES={'audit','local','key','marginal_direct','marginal_markless','topology_local','topology_key','density_pack','qa_isolate','qa_swap','qa_stat'}


def export(source,destination,spec):
    source=Path(source);destination=Path(destination)
    if spec.get('mode') not in MODES:raise ValueError('Unregistered study-view operation')
    if set(spec)-{'mode','cards','captions','swap','labels','label_cards','provenance','markless_cards','fixed_indices'}:
        raise ValueError('Unknown study-view operation fields')
    if destination.exists():raise FileExistsError('Immutable renderer export already exists')
    destination.mkdir(parents=True)
    job={'source':str(source.resolve()),'out':str(destination.resolve()),'spec':spec}
    path=destination/'operation.json';path.write_text(json.dumps(job,ensure_ascii=False))
    env=dict(os.environ,PLAYWRIGHT_BROWSERS_PATH=str(ROOT/'build/renderer_tooling/browsers'))
    result=subprocess.run([str(node_runtime()),str(RENDERER/'web/dist/studyView.mjs'),str(path)],
        cwd=RENDERER/'web',env=env,capture_output=True,text=True,timeout=120)
    if result.returncode:raise RuntimeError('Study view export failed: '+result.stderr[-3500:])
    return json.loads((destination/'manifest.json').read_text())
