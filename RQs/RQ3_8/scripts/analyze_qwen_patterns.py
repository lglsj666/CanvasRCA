"""Offline pattern/grounding supplement; consumes the completed audit CSV only."""
import importlib.util
import json
import re
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image
from scipy.stats import binomtest, spearmanr
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

spec=importlib.util.spec_from_file_location('audit',Path(__file__).with_name('analyze_qwen_completed.py'))
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
OUT=a.OUT


def main():
    f=pd.read_csv(OUT/'per_case.csv',keep_default_na=False)
    for k in a.METRICS+['input_tokens','image_tokens','text_tokens','output_tokens','wall_time_s','candidate_count']:
        f[k]=pd.to_numeric(f[k],errors='coerce')
    f['rq']=f.rq.astype(str)
    profiles=[];claims=[];confusions=[];size_rows=[];association=[];samples=[]
    for rq,block,ff in a.blocks(f):
        new,old=('LOCAL_LINK','T_MATCH') if rq=='37' else ('FULL','TEXT')
        if block=='B':continue
        pair=ff[ff.arm.isin([new,old])&ff.dataset.isin(a.MAIN)].pivot(index='case',columns='arm',values='mrr').dropna()
        sub=ff[ff.case.isin(pair.index)&ff.arm.isin([new,old])]
        for field in ['level','fault_type','root_metric_exact','root_trace_exact','trace_cards','call_edges','deployment_edges']:
            tags=sub.copy()
            if field in ['trace_cards','call_edges','deployment_edges']:tags[field]=tags[field].gt(0)
            for scope,members in [('primary',a.MAIN)]+[(x,[x]) for x in a.MAIN]:
                for val,g in tags[tags.dataset.isin(members)].groupby(field):
                    x=g[g.arm==new].set_index('case');y=g[g.arm==old].set_index('case')
                    if len(x)!=len(y):raise AssertionError('pair loss')
                    d=x.mrr-y.mrr
                    profiles.append(dict(rq=rq,block=block,scope=scope,field=field,stratum=str(val),
                        new_mrr=x.mrr.mean(),old_mrr=y.mrr.mean(),**a.test(d)))
        for (arm,level,predicted),g in sub.groupby(['arm','level','top1_level']):
            confusions.append(dict(rq=rq,block=block,arm=arm,root_level=level,predicted_level=predicted,
                n=len(g),correct=int(g['ac@1'].sum())))
    for r in f[f.status.eq('done')].itertuples():
        private=a.read(a.PREP/'private'/(r.case+'.json'))
        if r.rq=='37' and r.arm=='TPV_REF':private=private.get('historical_calibration_private',private)
        bad=[];found=[]
        for kind,oid in re.findall(r'\b(service|pod|node)\s+(\d{3,5})\b',r.reason,flags=re.I):
            expected=private['entity_granularity'].get(private['numeric_to_natural'].get(oid))
            found.append((kind.lower(),oid,expected))
            if expected and kind.lower()!=expected:bad.append((kind.lower(),oid,expected))
        claims.append(dict(rq=r.rq,phase=r.phase,cohort=r.cohort,case=r.case,arm=r.arm,
            explicit_typed_claims=len(found),type_mismatch=len(bad),any_mismatch=bool(bad),
            details=json.dumps(bad),mrr=r.mrr))
    pd.DataFrame(claims).to_csv(OUT/'explicit_type_audit.csv',index=False)
    cc=pd.DataFrame(claims)
    cc.groupby(['rq','phase','cohort','arm']).agg(n=('case','size'),cases_with_typed_claim=('explicit_typed_claims',lambda s:int((s>0).sum())),
        mismatch_cases=('any_mismatch','sum'),mismatch_count=('type_mismatch','sum')).to_csv(OUT/'explicit_type_summary.csv')
    pr=a.holm(pd.DataFrame(profiles),['rq','block'])
    pr.to_csv(OUT/'subgroup_profiles.csv',index=False)
    pd.DataFrame(confusions).to_csv(OUT/'root_prediction_levels.csv',index=False)
    # No-op checks compare actual saved PNG bytes' recorded hashes, not nominal arm names.
    noops=[]
    for rq,block,ff in a.blocks(f):
        if rq!='38':continue
        for name,w,family in a.contrasts(rq,block):
            if sorted(w.values())!=[-1,1]:continue
            new=next(k for k,v in w.items() if v==1);old=next(k for k,v in w.items() if v==-1)
            x=ff[(ff.arm==new)&ff.status.eq('done')].set_index('case')
            y=ff[(ff.arm==old)&ff.status.eq('done')].set_index('case');ix=x.index.intersection(y.index)
            for oid in ix:
                noops.append(dict(block=block,contrast=name,case=oid,dataset=x.loc[oid,'dataset'],
                    same_png=x.loc[oid,'image_hashes']==y.loc[oid,'image_hashes'],
                    same_call=x.loc[oid,'call_key']==y.loc[oid,'call_key'],
                    same_request=x.loc[oid,'request_hash']==y.loc[oid,'request_hash']))
    pd.DataFrame(noops).to_csv(OUT/'noop_audit.csv',index=False)
    # Corruption versus repeat flips: common four-arm mask, paired exact McNemar.
    fliptests=[]
    b=f[(f.rq=='38')&f.cohort.eq('eval')&f.mechanism&f.arm.isin(a.B38+['FULL'])]
    ids=b.groupby('case').filter(lambda g:len(g)==4 and g.mrr.notna().all()).case.unique()
    for scope,members in [('primary',a.MAIN),('pooled',a.DATASETS)]:
        z=b[b.case.isin(ids)&b.dataset.isin(members)]
        base=z[z.arm=='FULL'].set_index('case');rep=z[z.arm=='FULL_REPEAT'].set_index('case').loc[base.index]
        for arm in a.B38[:2]:
            var=z[z.arm==arm].set_index('case').loc[base.index]
            for measure,col in [('top1','top1'),('ranking','predictions')]:
                v=(var[col]!=base[col]);r=(rep[col]!=base[col]);u=int((v&~r).sum());d=int((~v&r).sum())
                fliptests.append(dict(scope=scope,arm=arm,measure=measure,n=len(base),variant_flips=int(v.sum()),repeat_flips=int(r.sum()),
                    variant_only=u,repeat_only=d,p=binomtest(u,u+d).pvalue if u+d else 1.))
    a.holm(pd.DataFrame(fliptests),['scope']).to_csv(OUT/'flip_vs_repeat.csv',index=False)
    # Header reads only; do not decode/re-render all images or rerun the processor.
    for r in f[(f.rq=='38')&f.arm.eq('FULL')&f.status.eq('done')].itertuples():
        with Image.open(r.png_path) as image:w,h=image.size
        size_rows.append(dict(case=r.case,dataset=r.dataset,cohort=r.cohort,width=w,height=h,
            image_tokens=r.image_tokens,root_metric_exact=r.root_metric_exact,mrr=r.mrr))
    sz=pd.DataFrame(size_rows);sz.to_csv(OUT/'image_sizes.csv',index=False)
    for cohort in ['eval','test']:
        ff=f[(f.rq=='38')&f.cohort.eq(cohort)]
        pv=ff[ff.arm.isin(['FULL','TEXT'])].pivot(index='case',columns='arm',values='mrr').dropna()
        z=sz.set_index('case').loc[pv.index].copy();z['delta']=pv.FULL-pv.TEXT
        for dataset,g in z.groupby('dataset'):
            for feature in ['height','image_tokens']:
                stat=spearmanr(g[feature],g.delta)
                association.append(dict(cohort=cohort,dataset=dataset,feature=feature,n=len(g),rho=stat.statistic,p=stat.pvalue))
    a.holm(pd.DataFrame(association),['feature']).to_csv(OUT/'size_effect_associations.csv',index=False)
    # Copies of exactly delivered original PNGs for the report, never re-rendered.
    chosen=['INC-BA41A280E858','INC-37ABFB78A80E','INC-DABDFB89960F','INC-018AC5D486B5']
    sample=pd.read_csv(OUT/'balanced_60_cases.csv')
    for oid in chosen:
        row=sample[sample.case==oid].iloc[0]
        shutil.copyfile(row.new_png,OUT/(oid+'.png'))
        samples.append(dict(case=oid,source=row.new_png,copy=str(OUT/(oid+'.png')),
            sha256=a.hashlib.sha256(Path(row.new_png).read_bytes()).hexdigest()))
    a.save('figure_provenance',samples)
    # All incurred requests including stopped branches: never label their partial efficacy complete.
    ledger=[];active=pd.read_csv(OUT/'rq38_all_terminal_positions.csv')
    for shard in range(3):
        root=a.R38/f'{a.MODEL}_s{shard}';conn=a.sqlite3.connect(f'file:{root/"calls.sqlite"}?mode=ro',uri=True)
        keep=set(active[(active.shard==shard)&active.active].call_key.dropna())
        for call_key,state,started in conn.execute('SELECT call_key,state,started FROM calls'):
            call_key=call_key.rsplit('/',1)[-1]
            costpath=root/'cost'/(call_key+'.json');cost=a.read(costpath) if costpath.exists() else {}
            ledger.append(dict(shard=shard,call_key=call_key,state=state,started=started,active=call_key in keep,
                input_tokens=cost.get('input_tokens'),output_tokens=cost.get('output_tokens'),image_tokens=cost.get('image_tokens'),
                wall_time_s=cost.get('wall_time_s'),cost_artifact_present=costpath.exists()))
        conn.close()
    pd.DataFrame(ledger).to_csv(OUT/'rq38_incurred_calls.csv',index=False)
    prep_times=[]
    for c in a.read(a.PREP/'roster_formal4_q3g1.json')['cases']:
        oid=c['opaque_incident_id'];exp=a.read(a.PREP/'export_flags'/(oid+'.json'))
        render=a.read(a.PREP/'render_flags'/(oid+'.json')).get('arms',{}).get('FULL',{})
        prep_times.append(dict(case=oid,dataset=c['dataset'],cohort=c['cohort'],
            export_seconds=exp.get('seconds'),full_renderer_seconds=render.get('renderer_seconds')))
    pd.DataFrame(prep_times).to_csv(OUT/'recorded_preparation_cost.csv',index=False)
    authorities=[a.ROOT/'RQs/RQ3_8/configs/ops_components_v7.json',
        a.PREP/'roster_formal4_q3g1.json',a.R37/'registration.json',
        a.ROOT/'RQs/RQ3_8/descriptions/RQ3_8_experiments.md',
        a.ROOT/'RQs/RQ3_7/descriptions/RQ3_7_experiments.md',
        Path(__file__),Path(__file__).with_name('analyze_qwen_completed.py')]
    a.save('source_authorities',[dict(path=str(x),sha256=a.hashlib.sha256(x.read_bytes()).hexdigest()) for x in authorities])
    # Charts for root granularity and corruption/repeat sensitivity.
    plt.rcParams.update({'font.family':'DejaVu Sans','figure.dpi':150})
    fig,axs=plt.subplots(1,2,figsize=(12,4),sharey=True)
    for ax,rq in zip(axs,['37','38']):
        for i,(block,color) in enumerate((['C_eval','#278c85'],['C_test','#c7853c']) if rq=='37' else (['A','#278c85'],['C','#c7853c'])):
            g=pr[(pr.rq==rq)&pr.block.eq(block)&pr.scope.eq('primary')&pr.field.eq('level')].set_index('stratum').reindex(['node','pod','service','pod/service'])
            ax.bar(np.arange(4)+i*.36,g.delta,width=.36,label=block,color=color)
            for j,r in enumerate(g.itertuples()):ax.text(j+i*.36,r.delta,f'n={r.n}',ha='center',va='bottom' if r.delta>0 else 'top',fontsize=8)
        ax.axhline(0,color='black',lw=.7);ax.set(xticks=np.arange(4)+.18,xticklabels=['node','pod','service','mixed'],title='RQ3.'+rq[-1]);ax.legend()
    axs[0].set_ylabel('Paired MRR difference versus matched text');fig.tight_layout();fig.savefig(OUT/'05_granularity.png');plt.close(fig)
    ft=pd.DataFrame(fliptests);g=ft[(ft.scope=='primary')&(ft.measure=='top1')]
    fig,ax=plt.subplots(figsize=(8,4));ax.bar(['FULL repeat','Metric time permutation','Trace length neutral'],[g.iloc[0].repeat_flips,*g.variant_flips],color=['#aaaaaa','#278c85','#c7853c']);ax.set(ylabel='Top-1 flips from original FULL',title='Same 53 primary-dataset cases; one repeat only');fig.tight_layout();fig.savefig(OUT/'06_graphic_vs_repeat.png');plt.close(fig)
    print('Pattern supplement complete:',OUT)


if __name__=='__main__':main()
