"""Retrospective matched contrasts; evaluator-only, no inference or selection."""
import csv
import io
from collections import defaultdict
from statistics import mean
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from RQs.RQ3.src.utils import ROOT, read_json, write_json, atomic_write, sha_file
from vlmrca.paired_stats import paired_statistics, holm

BASE = ROOT/'RQs/RQ3/results/search_first_v1'
OUT = BASE/'retrospective_through39_20260912'
rows = read_json(OUT/'per_case.json')['rows']
groups = defaultdict(dict)
for r in rows:
    if r['evidence_status']=='train-only exploration':
        groups[r['batch'],r['variant']][r['case']] = r


def key(batch, fragment=None):
    keys = [k for k in groups if k[0]==batch+'_development_v1' or k[0]==batch]
    if fragment: keys=[k for k in keys if fragment in k[1]]
    assert len(keys)==1, (batch,fragment,keys)
    return keys[0]


contrasts=[]
def register(name, kind, a, b): contrasts.append((name,kind,key(*a),key(*b)))
for selector in ('ranked','coverage','local_contrast'):
    register('Grounding / '+selector,'prompt',('selection',selector+'_v1__inherited'),('selection',selector+'_v1__grounded'))
for prompt in ('inherited','grounded'):
    for selector in ('coverage','local_contrast'):
        register('Selection '+selector+' / '+prompt,'selection',('selection','ranked_v1__'+prompt),('selection',selector+'_v1__'+prompt))
register('Nonthinking recipe','request',('selection','ranked_v1__inherited'),('prompt_recipe','inherited'))
register('Concise / legacy','prompt',('selection','ranked_v1__inherited'),('prompt_recipe','concise_v1__legacy'))
register('Concise / nonthinking','prompt',('prompt_recipe','inherited'),('prompt_recipe','concise_v1__card'))
for recipe in ('legacy','card_nonthinking'):
    register('M24 coverage / '+recipe,'selection',('coverage24','ranked_v1__inherited_v1__'+recipe),('coverage24','coverage_v1__inherited_v1__'+recipe))
    parent=('selection','ranked_v1__inherited') if recipe=='legacy' else ('prompt_recipe','inherited')
    register('M8 to M24 / '+recipe,'selection+canvas',parent,('coverage24','ranked_v1__inherited_v1__'+recipe))
    register('Bound guide + candidate enum / '+recipe,'prompt+schema',parent,('evidence_bound','__'+recipe))
register('Trace microseconds to ms','unit repair',('evidence_bound','card_nonthinking'),('trace_units',None))
register('Low thinking','request',('trace_units',None),('thinking_low_development_v2',None))
register('All public hosting','facts+canvas',('hosting_axis','ranked_v1'),('hosting_axis','ranked_hosting'))
register('Cross-source selection','selection',('membership_contrast','ranked_membership'),('membership_contrast','cross_source'))
register('Field dictionary','prompt',('field_semantics','bound_membership'),('field_semantics','evidence_semantics'))
for selector in ('trace_only','trace_graph','trace_logs_graph'):
    register(selector,'selection',('field_semantics','bound_membership'),('trace_subset',selector))
register('Trace routing / A','selection',('signal_routing','ranked_membership_v1__evidence_bound'),('signal_routing','trace_strength_route_v1__evidence_bound'))
for selector in ('ranked_membership','trace_strength_route'):
    register('Reason-first / '+selector,'prompt+schema order',('signal_routing',selector+'_v1__evidence_bound'),('signal_routing',selector+'_v1__evidence_reason'))
register('Resource slot replacement','selection',('resource_balance','ranked_membership'),('resource_balance','resource_balance'))
register('Node overview / A','selection',('node_overview','ranked_membership'),('node_overview','node_overview'))
register('Zero-inclusive y-axis','encoding',('node_overview','node_overview'),('zero_origin',None))
register('Trace routing / B','selection',('wider_native','ranked_membership'),('wider_native','trace_strength'))
register('Node overview / B','selection',('wider_native','ranked_membership'),('wider_overview_development_v2',None))
register('Typed owner in image','labels',('wider_overview_development_v2',None),('typed_overview',None))
register('Balanced resource additions','selection',('typed_overview',None),('typed_balanced',None))
register('Larger owner label','labels',('typed_overview',None),('owner_header',None))
register('Whole-window guide','prompt',('owner_header',None),('whole_window',None))
register('Unanchored timeline','time+encoding',('whole_window',None),('unanchored',None))
register('Trace count per exposure','projection+guide',('owner_header',None),('trace_rates',None))
for selector in ('metz_overview','metz_coverage_overview'):
    register(selector,'selection',('owner_header',None),('metz',selector))
for batch,kind in [('period','annotation'),('metric_facets','layout'),('owner_groups','grouping')]:
    register(batch,kind,('owner_header',None),(batch,None))
register('Observed-values only','fields+guide',('unanchored',None),('observations',None))
register('Typed candidate rows','candidate format',('typed_overview',None),('candidate_types_development_v2',None))
register('Native M24 / C','selection',('expanded_overview',None),('expanded_native24',None))
for batch,kind in [('expanded_coverage24','selection'),('axis_span','encoding'),('shape_diversity','selection'),('unpenalized','request'),('peer_shift','selection')]:
    register(batch,kind,('expanded_native24',None),(batch,None))

tables=[]; failures=[]
for name,kind,ka,kb in contrasts:
    a,b=groups[ka],groups[kb]
    assert set(a)==set(b), ('unpaired cohort',name)
    for ds in ('aiops2022','aiops2025'):
        ids=sorted(c for c in a if a[c]['dataset']==ds)
        assert all(b[c]['dataset']==ds for c in ids)
        aa=[a[c]['mrr'] for c in ids];bb=[b[c]['mrr'] for c in ids]
        stats=paired_statistics(aa,bb)
        tables.append(dict(contrast=name,kind=kind,dataset=ds,n=len(ids),reference=' / '.join(ka),method=' / '.join(kb),
            reference_mrr=mean(aa),new_mrr=mean(bb),delta_mrr=mean(y-x for x,y in zip(aa,bb)),
            repair=sum(y>x for x,y in zip(aa,bb)),breaks=sum(y<x for x,y in zip(aa,bb)),tie=sum(y==x for x,y in zip(aa,bb)),
            reference_input=mean(a[c]['input_tokens'] for c in ids),new_input=mean(b[c]['input_tokens'] for c in ids),
            reference_output=mean(a[c]['output_tokens'] for c in ids),new_output=mean(b[c]['output_tokens'] for c in ids),**stats))
        for c in ids:
            if a[c]['mrr']!=b[c]['mrr']:
                failures.append(dict(contrast=name,case=c,dataset=ds,fault_type=a[c]['fault_type'],
                    old_rr=a[c]['mrr'],new_rr=b[c]['mrr'],old_record=a[c]['source_record'],new_record=b[c]['source_record']))
for r,p in zip(tables,holm([r['p'] for r in tables])):r['retrospective_global_holm_p']=p


def csv_write(path, rows):
    stream=io.StringIO();writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    atomic_write(path,stream.getvalue().encode())


csv_write(OUT/'matched_contrasts.csv',tables)
write_json(OUT/'changed_cases.json',{'scope':'private offline review links; never model input','rows':failures})
write_json(OUT/'matched_contrasts.json',{'scope':'retrospective exploratory, not new confirmatory families','rows':tables})
lines=['# All registered-reference retrospective contrasts','',
    'Matched case IDs. Compound interventions are labeled. Counts of repairs/breaks are not independent across rows.',
    'Tests use cases; global Holm is an additional retrospective sensitivity, not replacement of original preregistration.','',
    '| Intervention | Dataset | n | Reference MRR | New MRR | Delta | Repair / break / tie | Input old → new | Output old → new |',
    '|---|---|---:|---:|---:|---:|---|---|---|']
for r in tables:
    lines.append(f"| {r['contrast']} ({r['kind']}) | {r['dataset']} | {r['n']} | {r['reference_mrr']:.4f} | {r['new_mrr']:.4f} | {r['delta_mrr']:+.4f} | {r['repair']}/{r['breaks']}/{r['tie']} | {r['reference_input']:.0f} → {r['new_input']:.0f} | {r['reference_output']:.1f} → {r['new_output']:.1f} |")
atomic_write(OUT/'matched_contrasts.md','\n'.join(lines).encode())

# Full cohort matrices include every executed method, not only top performers.
# Historical incompatible runtime and interface qualification were excluded above.
cohorts=defaultdict(list)
for k,rr in groups.items():cohorts[tuple(sorted(rr))].append(k)
oracle=[]
for gi,(ids,kk) in enumerate(sorted(cohorts.items(),key=lambda x:(len(x[0]),x[0]))):
    label='A' if len(ids)==12 else ('C' if any(k[0]=='expanded_native24_development_v1' for k in kk) else 'B')
    kk=sorted(kk)
    for ds in ('aiops2022','aiops2025'):
        cs=[c for c in ids if groups[kk[0]][c]['dataset']==ds]
        mat=np.array([[groups[k][c]['mrr'] for c in cs] for k in kk])
        best=mat.max(axis=0); fixed=float(mat.mean(axis=1).max())
        oracle.append(dict(cohort=label,dataset=ds,cases=len(cs),methods=len(kk),best_observed_fixed=fixed,
            hindsight_oracle=float(best.mean()),all_zero=[c for j,c in enumerate(cs) if best[j]==0],
            warning='Training-only optimistic hindsight; changing identity/prompt/recipe and sampling noise included. Not deployable.'))
        for start in range(0,len(kk),16):
            end=min(start+16,len(kk)); fig,ax=plt.subplots(figsize=(12,2+.42*(end-start)))
            im=ax.imshow(mat[start:end],vmin=0,vmax=1,cmap='YlGnBu',aspect='auto')
            labels=[k[0].replace('_development','')+' / '+k[1].replace('evidence_bound_membership_v1','bound').replace('card_nonthinking_v1','nt') for k in kk[start:end]]
            ax.set_yticks(range(end-start),labels,fontsize=7)
            ax.set_xticks(range(len(cs)),[c[-6:] for c in cs],rotation=45,ha='right',fontsize=8)
            for i in range(end-start):
                for j in range(len(cs)):
                    v=mat[start+i,j];ax.text(j,i,f'{v:.2f}',ha='center',va='center',fontsize=7,color='white' if v>.65 else 'black')
            ax.set_title(f'Cohort {label} / {ds} / per-case reciprocal rank (part {start//16+1})')
            fig.colorbar(im,ax=ax,label='RR');fig.tight_layout()
            fig.savefig(OUT/f'case_matrix_{label}_{ds}_{start//16+1}.png',dpi=150);plt.close(fig)
write_json(OUT/'hindsight_headroom.json',{'rows':oracle})

# Compact paired effects; one point per dataset, separate panels avoid crowding.
for start in range(0,len(contrasts),14):
    names=[c[0] for c in contrasts[start:start+14]]
    fig,ax=plt.subplots(figsize=(11,2+.42*len(names)))
    for offset,ds,color in [(-.12,'aiops2022','#1764ab'),(.12,'aiops2025','#cb4b16')]:
        selected=[next(r for r in tables if r['contrast']==n and r['dataset']==ds) for n in names]
        ax.scatter([r['delta_mrr'] for r in selected],np.arange(len(names))+offset,color=color,label=ds)
    ax.axvline(0,color='gray',linewidth=1);ax.set_yticks(range(len(names)),names,fontsize=9);ax.invert_yaxis()
    ax.set_xlabel('Paired MRR change (each against its own documented reference)');ax.legend();fig.tight_layout()
    fig.savefig(OUT/f'paired_effects_{start//14+1}.png',dpi=150);plt.close(fig)

sources=[OUT/'per_case.json',BASE/'strategy_inventory_20260912.json',Path(__file__)]
write_json(OUT/'analysis_sources.json',{'sha256':{str(p.relative_to(ROOT)):sha_file(p) for p in sources},
    'contrast_count':len(contrasts),'dataset_contrasts':len(tables),'changed_comparisons':len(failures),
    'record_sources':sorted({r['source_record'] for r in rows}),
    'zero_call_attempts':'See recap_20260912/README.md and dated protocols; no invented efficacy rows.'})
print({'contrasts':len(contrasts),'dataset_rows':len(tables),'oracle':oracle},flush=True)
