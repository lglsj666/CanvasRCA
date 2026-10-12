"""Seal reviewed SEARCH31 inputs and archive the exact dependent source bytes."""
import tarfile
from pathlib import Path
from RQs.RQ3.src.main import prepare_search_batch,load_config
from RQs.RQ3.src.utils import ROOT,read_json,write_json,sha_file,stable_hash

base=ROOT/'RQs/RQ3/results/search_first_v1'
out=base/'observations_development_v1';gallery=base/'observations_gallery_v1'
config=ROOT/'RQs/RQ3/configs/search_observations_v1.yaml'
assert not out.exists(),'existing batch must resume, not be recommitted'
assert read_json(gallery/'cpu_review.json')['status']=='passed'
prepare_search_batch(gallery,out,config)
path=out/'private/work_spec.json';spec=read_json(path);assert len(spec['tasks'])==24
old=read_json(base/'unanchored_development_v1/private/work_spec.json');cfg=load_config(config)
for name in (cfg['unified']['inference'],'configs/rca_scorer.yaml'):
    assert spec['artifact_hashes'][name]==old['artifact_hashes'][name]
for p in (Path(__file__),gallery/'cpu_review.json',base/'cpu_observations_full_v1.xml',
          ROOT/'RQs/RQ3/scripts/review_observations.py',
          ROOT/'RQs/RQ3/descriptions/RQ3_observations_20260912.md'):
    spec['artifact_hashes'][str(p.resolve().relative_to(ROOT))]=sha_file(p)
snapshot=out/'private/source_snapshot.tar.gz'
with tarfile.open(snapshot,'w:gz') as tar:
    for relative in sorted(spec['artifact_hashes']):
        if Path(relative).suffix in {'.py','.yaml','.sh','.txt','.md'}:
            tar.add(ROOT/relative,arcname=relative,recursive=False)
spec['artifact_hashes'][str(snapshot.relative_to(ROOT))]=sha_file(snapshot)
spec['spec_hash']=stable_hash({k:v for k,v in spec.items() if k!='spec_hash'})
write_json(path,spec)
print({'tasks':24,'spec_hash':spec['spec_hash'],'snapshot':str(snapshot.relative_to(ROOT))},flush=True)
