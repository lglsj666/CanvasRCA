"""Populate report tables from the independently aggregated CSV files."""
from pathlib import Path
import csv,re
P=Path(__file__).resolve().parent
REPORT=P.parent/'CanvasRCA_Visual_Token_Pruning_Review_2026-10-18.md'
def rows(name):return list(csv.DictReader((P/name).open()))
def fmt(x,n=4):return f'{float(x):.{n}f}'
def integer(x):return str(int(float(x)))
def table(headers,rs):
    return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join('---' for _ in headers)+' |']+['| '+' | '.join(map(str,r))+' |' for r in rs])
allrows=rows('all_methods_metrics.csv')
lookup={(r['experiment'],r['arm'],r['dataset']):r for r in allrows}
core=[f'{a}_E{q}' for a in ('A_UNIFORM','UNARY','CVC') for q in (25,50,75)]+['QUOTA_E50','REWIRED_E50','A_DIVERSITY_E50','DART_E50','S2PRUNE_E50','GPRUNE_E50','SCOPE_E50']
tables={}
tables['CORE_TABLE']=table(['条件','标准 MRR','宽容 MRR','AC@1','AC@3','AC@5','无效/220','总 token','在线秒'],[
    [arm]+[fmt(lookup['RQ4.1',arm,'ALL'][k]) for k in ('mrr','tolerant_mrr','ac@1','ac@3','ac@5')]+[
        integer(lookup['RQ4.1',arm,'ALL']['invalid']),fmt(lookup['RQ4.1',arm,'ALL']['total'],1),fmt(lookup['RQ4.1',arm,'ALL']['online_seconds'],2)]
    for arm in ['T_FULL','V_FULL']+core])
tables['DATASET_TABLE']=table(['条件','AIOPS-2022','AIOPS-2025','AegisLab','三集宏平均'],[
    [arm]+[fmt(lookup['RQ4.1',arm,ds]['mrr']) for ds in ('aiops2022','aiops2025','aegislab')]+[
        fmt(sum(float(lookup['RQ4.1',arm,ds]['mrr']) for ds in ('aiops2022','aiops2025','aegislab'))/3)]
    for arm in ['T_FULL','V_FULL']+core])
tables['MASK_TABLE']=table(['条件','保留 A 个数均值','锚点召回','完整保住 A 的病例','保留 E 个数均值','可选证据召回','保留位置中 A∪E 之外占比'],[
    [r['arm'],fmt(r['A_kept'],1),fmt(float(r['anchor_recall'])*100,2)+'%',integer(r['all_anchors_preserved_cases'])+'/220',
     fmt(r['E_kept'],1),fmt(float(r['optional_recall'])*100,2)+'%',fmt(float(r['outside_A_E_fraction'])*100,2)+'%']
    for r in rows('actual_mask_summary.csv') if r['dataset']=='ALL'])
tables['VALID_TABLE']=table(['对照','全220标准 ΔMRR','全220宽容 ΔMRR','双方合法 n','双方合法子集标准 ΔMRR'],[
    [r['b'],fmt(r['all_delta']),fmt(r['tolerant_all_delta']),r['both_valid_n'],fmt(r['both_valid_delta']) if r['both_valid_delta'] else '不适用']
    for r in rows('paired_valid_sensitivity.csv') if r['b'] in ('V_FULL','CVC_E50','SCOPE_E50','S2PRUNE_E50','DART_E50','GPRUNE_E50')])
arms3=['P_SOFT_IMAGE','C_LOCAL_FORWARD','P_LOCAL_BI','C_GLOBAL_BI','C_SHAM_BI','P_DUAL','S_JOINT','C_SOURCE_HASH',
       'R_PATCH_PACK','R_HORIZON','R_PACK_HORIZON','C_PACK_OFFSET','C_READ_GUIDE','C_PACK_BG_FILL','X_SP','X_SR','X_RP','X_SRP']
ext=[]
for rq,arms in [('RQ4.3',arms3),('RQ4.4',['SOURCE_ZOOM','REPEAT_VIEW','HASH_ZOOM'])]:
    for arm in arms:
        r=lookup[rq,arm,'ALL']
        ext.append([rq,arm,fmt(r['mrr']),fmt(r['tolerant_mrr']),fmt(r['ac@5']),integer(r['invalid']),fmt(r['total'],1)])
tables['EXTENSION_TABLE']=table(['实验','条件','标准MRR','宽容MRR','AC@5','无效/220','总token'],ext)
stat=[];ts=rows('retrospective_all_136_pairs.csv')
for b in ('V_FULL','A_UNIFORM_E25','A_UNIFORM_E75','UNARY_E50','CVC_E50','A_DIVERSITY_E50','DART_E50','S2PRUNE_E50','SCOPE_E50','GPRUNE_E50'):
    r=next(r for r in ts if {r['a'],r['b']}=={'A_UNIFORM_E50',b})
    sign=1 if r['a']=='A_UNIFORM_E50' else -1
    n1,n2=(r['improved'],r['worsened']) if sign==1 else (r['worsened'],r['improved'])
    stat.append([b,fmt(sign*float(r['delta'])),f'{n1}/{n2}/{r["tied"]}',fmt(sign*float(r['dz']),3),
                 f'{float(r["v11_holm_136"]):.4g}',f'{float(r["case_pratt_holm_136"]):.4g}',f'{float(r["group_pratt_holm_136"]):.4g}'])
tables['STATS_TABLE']=table(['U相对','ΔMRR','RR改善/破坏/相同','病例dz','v11 pH','病例Pratt pH','事件组Pratt pH'],stat)
text=REPORT.read_text()
for key,value in tables.items():
    block=f'<!-- GENERATED:{key} -->\n{value}\n<!-- END:{key} -->'
    if '@@'+key+'@@' in text:text=text.replace('@@'+key+'@@',block)
    else:
        text,n=re.subn(r'<!-- GENERATED:'+key+r' -->.*?<!-- END:'+key+r' -->',lambda _:block,text,flags=re.S)
        assert n==1,(key,n)
REPORT.write_text(text)
assert '@@' not in text
print('Populated',len(tables),'tables')
