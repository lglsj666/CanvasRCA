"""Validate published report artifacts, without any model or pipeline execution."""
from pathlib import Path
import hashlib
import json
import re
import sys

import numpy as np
import pandas as pd
from PIL import Image
from reanalyze import specs
from publish import SPECS

ROOT=Path(__file__).resolve().parents[3]
REPORTS=ROOT/'docs/experiment_reports'
WORK=REPORTS/'_qwen_only_reanalysis'


def main():
    manifest=json.loads((WORK/'backup_manifest.json').read_text())
    backup=Path(manifest['backup'])
    for f in manifest['files']:
        p=backup/f['path']
        assert p.is_file() and p.stat().st_size==f['bytes']
        assert hashlib.sha256(p.read_bytes()).hexdigest()==f['sha256'],p
    counts={'backup_files_verified':len(manifest['files']),'reports':0,'tables':0,'figures':0,'holm_rows_checked':0,'model_rows_checked':0,'raw_record_rows_unchanged':0,'broken_links':[]}
    for key,report,title,assets in SPECS:
        rp=REPORTS/report;txt=rp.read_text()
        assert not re.search('gemma',txt,re.I),rp
        counts['reports']+=1
        for link in re.findall(r'\]\(([^)]+)\)',txt):
            if '://' in link or link.startswith('#'):continue
            dest=(rp.parent/link.split('#')[0]).resolve()
            if not dest.exists():counts['broken_links'].append([str(rp),link])
        for p in (REPORTS/assets).glob('*.csv'):
            d=pd.read_csv(p,low_memory=False)
            counts['tables']+=1
            if 'model'in d:
                assert d.model.astype(str).str.contains('qwen',case=False).all(),p
                counts['model_rows_checked']+=len(d)
            assert not re.search('gemma',p.read_text(),re.I),p
            for groups,field,out in specs(p.stem,d):
                if out not in d:continue
                frames=[g for _,g in d.groupby(groups,dropna=False)] if groups else [d]
                for g in frames:
                    vals=g[field].dropna().sort_values(kind='stable')
                    bound=0.
                    for pos,(idx,v) in enumerate(vals.items()):
                        bound=max(bound,min(1.,float(v)*(len(vals)-pos)))
                        assert abs(float(d.at[idx,out])-bound)<1e-10,(p,idx,out)
                        if out+'_family_n'in d:assert int(d.at[idx,out+'_family_n'])==len(vals)
                    counts['holm_rows_checked']+=len(vals)
            if p.stem in ['per_record','final_call_records','logical_results','normalized_results','A_core_records','response_audit','qa_semantic_v2_per_record']:
                old=backup/'docs'/p.relative_to(ROOT/'docs')
                if not old.is_file():continue
                original=pd.read_csv(old,low_memory=False)
                if 'model'not in original:continue
                original=original[original.model.astype(str).str.contains('qwen',case=False)].reset_index(drop=True)
                assert len(d)==len(original),(p,len(d),len(original))
                for c in ['case','case_id','arm','status','call_key','mrr','ac@1','ac@3','ac@5','avg@3','avg@5','ac1','ac3','ac5','avg3','avg5','strict','step','complete']:
                    if c not in d or c not in original:continue
                    if pd.api.types.is_numeric_dtype(d[c]):
                        assert np.allclose(d[c],original[c],equal_nan=True,rtol=0,atol=1e-14),(p,c)
                    else:assert d[c].fillna('').tolist()==original[c].fillna('').tolist(),(p,c)
                counts['raw_record_rows_unchanged']+=len(d)
        for p in (REPORTS/assets).glob('qwen_*.png'):
            with Image.open(p) as im:im.verify()
            counts['figures']+=1
        if key=='rq37':
            d=pd.read_csv(REPORTS/assets/'case_artifact_index.csv')
            images=d[d.copied_png.notna()]
            for _,r in images.iterrows():
                p=Path(r.copied_png)
                assert 'qwen' in r.source_png.lower()
                assert hashlib.sha256(p.read_bytes()).hexdigest()==r.sha256
                with Image.open(p) as im:im.verify()
            counts['original_qwen_images_preserved']=len(images)
    assert not counts['broken_links'],counts['broken_links']
    counts['inference_calls']=0
    counts['status']='passed'
    (WORK/'verification.json').write_text(json.dumps(counts,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(counts,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
