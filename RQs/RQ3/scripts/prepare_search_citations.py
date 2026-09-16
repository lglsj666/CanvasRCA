"""SEARCH40 actual-input parity, qualification commit and immutable source copy."""
import tarfile
import xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw
from RQs.RQ3.src.main import load_config, prepare_search_batch
from RQs.RQ3.src.gates import source_audit
from RQs.RQ3.src.utils import ROOT,read_json,write_json,sha_file,stable_hash
from RQs.RQ3.scripts.audit_search_citations import self_test, citation_references

base=ROOT/'RQs/RQ3/results/search_first_v1'
gallery=base/'citations_gallery_v1';reference=base/'expanded_native24_gallery_v1'
out=base/'citations_development_v1';config=ROOT/'RQs/RQ3/configs/search_citations_v1.yaml'
assert not out.exists(), 'never overwrite committed results'
summary=read_json(gallery/'summary.json');old=read_json(reference/'summary.json')
assert summary['cohort']==old['cohort'] and len(summary['attempts'])==24
old_by={a['case']:a for a in old['attempts']};rows=[];self_test()
guide=(ROOT/'RQs/RQ3/configs/prompts/citations_guide_v1.txt').read_text()
for a in summary['attempts']:
    prior=old_by[a['case']];stem=gallery/a['case']/a['family'];oldstem=reference/a['case']/prior['family']
    assert a['status']=='rendered' and a['partition']=='train'
    assert a['source']==prior['source'] and a['source_file_hash']==prior['source_file_hash']==sha_file(ROOT/a['source'])
    assert a['selection']==prior['selection'] and a['projection']==prior['projection']
    assert stem.with_suffix('.packet.json').read_bytes()==oldstem.with_suffix('.packet.json').read_bytes()
    p=read_json(stem.with_suffix('.packet.json'));m=read_json(stem.with_suffix('.manifest.json'))
    oldm=read_json(oldstem.with_suffix('.manifest.json'))
    assert m['cards']==oldm['cards'] and m['fact_mapping']==oldm['fact_mapping']
    assert m['visual_fact_inventory_hash']==oldm['visual_fact_inventory_hash']
    ids=[c['card']['card_id'] for c in m['cards']]
    assert len(ids)==len(set(ids)) and m['spec']['card_label_policy']=='visible_id_v1'
    for c in ids:assert citation_references('['+c+']',p,m)[0]['status']=='valid_address'
    before=Image.open(oldstem.with_suffix('.png')).convert('RGB');after=Image.open(stem.with_suffix('.png')).convert('RGB')
    assert before.size==after.size==(3996,4088)
    diff=ImageChops.difference(before,after);assert diff.getbbox()
    draw=ImageDraw.Draw(diff)
    for c in m['cards']:draw.rectangle(c['heading_bbox'],fill=0)
    assert diff.getbbox() is None, 'diagnostic pixels changed outside headings'
    pp=read_json(stem.with_suffix('.prompt.json'));op=read_json(oldstem.with_suffix('.prompt.json'))
    assert pp[:3]==op[:3] and len(pp)==len(op) and pp[4:]==op[4:] and pp[3]['text']==op[3]['text']+'\n'+guide
    assert a['request_profile']==prior['request_profile']=='card_nonthinking_v1'
    rows.append({'case':a['case'],'png_sha256':sha_file(stem.with_suffix('.png')),
                 'reference_png_sha256':sha_file(oldstem.with_suffix('.png')),'card_ids':ids,
                 'diagnostic_pixels_unchanged':True,'packet_bytes_unchanged':True})
xml=ET.parse(base/'citations_cpu_v2.xml')
assert len(xml.findall('.//testcase'))==367 and not xml.findall('.//failure') and not xml.findall('.//error')
viewed=['INC-7CE00360E043','INC-F9112289109A','INC-B324546FFC06']
assert all(c in old_by for c in viewed)
review={'status':'passed','summary_hash':stable_hash(summary),'rows':rows,'cpu_tests':367,
    'source':source_audit(),'actual_pngs_viewed':viewed,
    'notes':'Main agent opened these PNGs before commit; source IDs legible in headings, no new diagnostic marks or changed data. Text contains only candidates and static guidance.'}
write_json(gallery/'review.json',review)
prepare_search_batch(gallery,out,config)
path=out/'private/work_spec.json';spec=read_json(path);cfg=load_config(config)
prior=read_json(base/'expanded_native24_development_v1/private/work_spec.json')
for rel in (cfg['unified']['inference'],'configs/rca_scorer.yaml','src/vlmrca/vlm/client.py','src/vlmrca/vlm/configs.py'):
    assert spec['artifact_hashes'][rel]==prior['artifact_hashes'][rel]
for p in (Path(__file__),ROOT/'RQs/RQ3/scripts/audit_search_citations.py',base/'review_citations.py',
          base/'citations_cpu_v2.xml',gallery/'preflight_notes.md',
          ROOT/'RQs/RQ3/descriptions/RQ3_citations_20260912.md',ROOT/'RQs/RQ3/descriptions/RQ3_experiments.md'):
    spec['artifact_hashes'][str(p.resolve().relative_to(ROOT))]=sha_file(p)
snapshot=out/'private/source_snapshot.tar.gz'
with tarfile.open(snapshot,'w:gz') as archive:
    for rel in sorted(spec['artifact_hashes']):
        if Path(rel).suffix in {'.py','.yaml','.sh','.txt','.md'}:archive.add(ROOT/rel,arcname=rel,recursive=False)
spec['artifact_hashes'][str(snapshot.relative_to(ROOT))]=sha_file(snapshot)
spec['spec_hash']=stable_hash({k:v for k,v in spec.items() if k!='spec_hash'})
write_json(path,spec)
print({'tasks':24,'spec_hash':spec['spec_hash'],'source_files':len(spec['artifact_hashes'])},flush=True)
