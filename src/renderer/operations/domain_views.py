"""Explicit RQ4.10 exports: sample annotation policy and background/QA controls.

The normal component tree and defaults remain unchanged. This operation edits a
frozen, already rendered DOM; every edit is recorded before screenshotting.
"""
from pathlib import Path
import json,os,subprocess
from ..utils import ROOT,RENDERER
from ..main import node_runtime

MODES={'complete_readable','sample_glyph','sample_pack','sample_markless','background_plate','target_isolate','entity_rename'}


def export(source,destination,spec):
    source=Path(source);destination=Path(destination)
    allowed={'mode','cards','provenance','replacements','identity_allowlist'}
    if set(spec)-allowed or spec.get('mode') not in MODES:raise ValueError('Unknown domain-view specification')
    if spec['mode']=='entity_rename':
        mapping=spec.get('replacements',{})
        if len(mapping)<2 or set(mapping)!=set(mapping.values()) or any(k==v for k,v in mapping.items()):
            raise ValueError('Entity control requires a nonidentity closed bijection')
        if not set(mapping)<=set(spec.get('identity_allowlist',[])):raise ValueError('Entity mapping is not public')
    if destination.exists():raise FileExistsError('Immutable export destination exists')
    destination.mkdir(parents=True)
    job={'source':str(source.resolve()),'out':str(destination.resolve()),'spec':spec}
    target=destination/'operation.json';target.write_text(json.dumps(job,ensure_ascii=False))
    env=dict(os.environ,PLAYWRIGHT_BROWSERS_PATH=str(ROOT/'build/renderer_tooling/browsers'))
    result=subprocess.run([str(node_runtime()),str(RENDERER/'web/dist/domainView.mjs'),str(target)],
        cwd=RENDERER/'web',env=env,capture_output=True,text=True,timeout=120)
    if result.returncode:raise RuntimeError('Domain view export failed: '+result.stderr[-4000:])
    return json.loads((destination/'manifest.json').read_text())
