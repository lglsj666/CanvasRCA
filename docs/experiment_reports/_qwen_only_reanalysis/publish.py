"""Publish the offline Qwen report edition from audited staged tables."""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from narratives import TEXT

SPECS = [
 ('rq12','RQ1_1_RQ2_1_findings/findings.md','RQ1.1 / RQ2.1：表示、证据选择与视觉设计','RQ1_1_RQ2_1_findings/assets'),
 ('tournament','Tournament_Analysis_2026-09-15.md','Tournament：Qwen 的覆盖、失败机制与方法互补','Tournament_Analysis_2026-09-15_assets'),
 ('rq31','RQ3_1_Results_Analysis_2026-09-19.md','RQ3.1：竞争证据选择 X 的效果与机制','RQ3_1_Results_Analysis_2026-09-19_assets'),
 ('rq32','RQ3_2_Results_Analysis_2026-09-22.md','RQ3.2：SignalCover 的增益、损失与实现边界','RQ3_2_Results_Analysis_2026-09-22_assets'),
 ('rq33','RQ3_3_Results_Analysis_2026-09-24.md','RQ3.3：见证补充、预算与诊断利用','RQ3_3_Results_Analysis_2026-09-24_assets'),
 ('rq34','RQ3_4_Results_Analysis_2026-09-25.md','RQ3.4：证据组合、自动核验与视觉绑定','RQ3_4_Results_Analysis_2026-09-25_assets'),
 ('rq35','RQ3_5_Screen_Analysis_2026-09-26.md','RQ3.5 screen：证据、指令和联合信号','RQ3_5_Screen_Analysis_2026-09-26_assets'),
 ('rq36a','RQ3_6_Stage_A_Analysis_2026-09-26.md','RQ3.6-A：证据和指令拆分的复核','RQ3_6_Stage_A_Analysis_2026-09-26_assets'),
 ('cross','Cross_Experiment_Method_Profile_2026-09-26.md','跨实验画像：Qwen 的层次、故障与数据复杂度','Cross_Experiment_Method_Profile_2026-09-26_assets'),
 ('rq36b','RQ3_6_Mechanisms_Analysis_2026-09-28.md','RQ3.6-B：G 信息、故障范围与关系绑定机制','RQ3_6_Mechanisms_Analysis_2026-09-28_assets'),
 ('rq37','RQ3_7_Results_Analysis_2026-09-28.md','RQ3.7 A/B：数值和关系的受控视觉融合','RQ3_7_Results_Analysis_2026-09-28_assets'),
]


def fmt(x):
    if x is None or (isinstance(x,float) and np.isnan(x)):return '—'
    if isinstance(x,(float,np.floating)):
        if 0<abs(x)<.0001:return f'{x:.3g}'
        return f'{x:.4f}'
    return str(x).replace('|',' / ').replace('\n',' ')


def table(d,cols=None):
    if cols:d=d[[c for c in cols if c in d]]
    if d.empty:return '此范围没有可用记录。\n'
    return '| '+' | '.join(d.columns)+' |\n|'+'---|'*len(d.columns)+'\n'+'\n'.join('| '+' | '.join(fmt(x) for x in row)+' |' for row in d.itertuples(index=False,name=None))+'\n'


def read(d,f):return pd.read_csv(d/f,low_memory=False)


def metrics(key,d):
    if key=='rq12':
        a=read(d,'rq11_performance_cost_runtime_all_arms_datasets.csv');a=a[(a.scope=='rq1_rca')&(a.dataset=='headline')].copy();a['section']='RQ1.1 main300 pooled';a=a.rename(columns={'input':'input_tokens','output':'output_tokens'})
        b=read(d,'rq21_dataset_macros.csv').copy();b['section']=b.experiment+' five-dataset macro'
        return pd.concat([a,b],ignore_index=True)
    if key=='tournament':
        a=read(d,'coverage.csv');a['section']='累计跨轮覆盖（非单方法）';return a
    if key=='rq31':
        a=read(d,'final_arm_metrics.csv');a=a[a.dataset.eq('pooled360')].copy();a['section']='test360 pooled'
        return a.rename(columns={'MRR':'mrr','AC1':'ac@1','AC3':'ac@3','AC5':'ac@5','AVG3':'avg@3','AVG5':'avg@5'})
    if key=='rq32':
        a=read(d,'arm_metrics.csv');a=a[a.denominator.eq('whole_case')&a.scope.eq('primary_macro')].copy();a['section']=a.phase+' primary macro';return a
    if key in ['rq33','rq34']:
        a=read(d,'paired_arm_metrics.csv');a=a[a.population.eq('primary_macro')].copy();a['section']=a.stage+' primary macro';return a
    if key=='rq35':
        a=read(d,'paired_arm_metrics.csv');a=a[a.scope.eq('macro')].copy();a['section']=a.experiment+' primary macro';return a
    if key=='rq36a':
        a=read(d,'arm_metrics.csv');a=a[a.population.eq('common')&a.scope.eq('macro')].copy();a['section']='check120 common primary macro';return a
    if key=='rq36b':
        a=read(d,'arm_metrics.csv');a=a[a.population.eq('common')&a.scope.eq('macro')&a.split.eq('all')].copy();a['section']=a.family+' common primary macro';return a
    if key=='rq37':
        a=read(d,'all_metrics.csv');a=a[a.subset.eq('pooled')].copy();a['section']=a.experiment+' '+a.encoding+' pooled';return a
    if key=='cross':
        a=read(d,'method_profiles.csv');a=a[a.scope.eq('main_three')&a.dimension.eq('overall')].copy();a['section']=a.study+' / '+a.stage+' main-three pooled';return a
    raise KeyError(key)


def stats_tables(key,d):
    files={
      'rq12':['rq11_rq1_registered_primary.csv','rq11_factorial_effects.csv','extra_paired_contrasts.csv','rq21_paired_comparisons.csv'],
      'tournament':['paired_round_tests.csv','feature_tests.csv'],
      'rq31':['final_pairwise_holm.csv'], 'rq32':['paired_statistics.csv'],
      'rq33':['registered_paired_tests.csv','registered_event_group_tests.csv'],
      'rq34':['registered_comparisons.csv','factorial_effects.csv'],
      'rq35':['registered_tests.csv','conditional_contrasts.csv'],
      'rq36a':['registered_tests.csv','paired_contrasts.csv'],
      'rq36b':['paired_tests.csv','carrier_global_holm.csv'],
      'rq37':['registered_comparisons.csv','registered_robustness_statistics.csv','exploratory_flip_vs_repeat.csv'],
      'cross':['paired_profiles.csv']}
    out=[]
    for f in files[key]:
        a=read(d,f)
        if key=='rq12':
            if f=='rq11_rq1_registered_primary.csv':a=a[a.metric.eq('mrr')&a.dataset.eq('headline')]
            elif f=='rq11_factorial_effects.csv':a=a[a.metric.eq('mrr')&a.dataset.eq('headline')]
            elif f=='extra_paired_contrasts.csv':a=a[a.scope.eq('rq1_rca')]
            else:a=a[a.subset.eq('all')&a.dataset.eq('pooled_descriptive')]
        elif key=='tournament':a=a[a.dataset.eq('all')] if 'all'in set(a.dataset) else a[a.dataset.eq('pooled480')]
        elif key=='rq32':a=a[a.scope.eq('primary')]
        elif key=='rq33' and 'population'in a:a=a[a.population.eq('primary_pooled')]
        elif key=='rq36a' and f=='paired_contrasts.csv':a=a[a.scope.eq('all')]
        elif key=='cross':a=a[a.scope.eq('main_three')&a.dimension.eq('overall')]
        out.append((f,a))
    return out


def plots(key,m,tests,out):
    pics=[]
    if key=='tournament':
        g=m[m.dataset.isin(['aiops2022','aiops2025','aegislab','re2_ob','re2_tt'])]
        fig,ax=plt.subplots(figsize=(10,4));x=np.arange(len(g))
        for offset,col,label in [(-.24,'covered','Ever top-1'),(0,'ever_top3','Ever top-3'),(.24,'ever_top5','Ever top-5')]:
            ax.bar(x+offset,g[col]/g.n,width=.24,label=label)
        ax.set_xticks(x,g.dataset);ax.set_ylim(0,1);ax.set_title('Qwen: multi-attempt coverage, NOT one-shot accuracy');ax.legend();fig.tight_layout();fig.savefig(out/'qwen_coverage.png',dpi=160);plt.close(fig);return ['qwen_coverage.png']
    if key=='cross':return pics
    for num,(sec,g) in enumerate(m.groupby('section',sort=False),1):
        g=g.sort_values('mrr',ascending=True)
        fig,ax=plt.subplots(figsize=(11,max(3,len(g)*.27+1.4)))
        ax.barh(g.arm,g.mrr,color='#2d729b');ax.set_xlim(0,min(1,max(.55,g.mrr.max()+.08)))
        for i,r in enumerate(g.itertuples()):ax.text(r.mrr+.005,i,f'{r.mrr:.3f}',va='center',fontsize=8)
        ax.set_title('Qwen | '+sec);ax.set_xlabel('MRR (population stated in title)');fig.tight_layout()
        name=f'qwen_mrr_{num:02}.png';fig.savefig(out/name,dpi=150);plt.close(fig);pics.append(name)
    return pics


def install(root,backup):
    reports=root/'docs/experiment_reports';work=reports/'_qwen_only_reanalysis';staged=work/'staged_assets'
    manifest=json.loads((work/'backup_manifest.json').read_text());hashes={x['path']:x['sha256'] for x in manifest['files']}
    moved_bytes=0;outputs=[]
    for key,report,title,assets in SPECS:
        target=reports/assets;source=staged/assets
        for p in target.rglob('*'):
            if not p.is_file():continue
            rel=str(p.relative_to(root))
            assert rel in hashes and hashlib.sha256(p.read_bytes()).hexdigest()==hashes[rel], f'Unbacked modification: {p}'
        # Full earlier edition remains outside the repository in the verified backup.
        for p in sorted(target.rglob('*'),reverse=True):
            if p.is_file():moved_bytes+=p.stat().st_size;p.unlink()
            elif p.is_dir():p.rmdir()
        for p in source.iterdir():shutil.copy2(p,target/p.name)
        restored_images=[]
        if key=='rq37':
            provenance=read(target,'case_artifact_index.csv')
            for _,row in provenance[provenance.copied_png.notna()].iterrows():
                destination=Path(row.copied_png)
                assert destination.parent==target
                assert 'qwen' in str(row.model).lower()
                original=backup/destination.relative_to(root)
                assert hashlib.sha256(original.read_bytes()).hexdigest()==row.sha256
                shutil.copy2(original,destination)
                restored_images.append(destination.name)
        m=metrics(key,target);tests=stats_tables(key,target)
        if m.empty:raise RuntimeError(f'Empty headline: {key}')
        m.to_csv(target/'qwen_headline_metrics.csv',index=False)
        images=plots(key,m,tests,target)
        prefix='assets' if key=='rq12' else assets
        text=f'# {title}\n\nQwen-only 修订版：2026-09-30。原文件日期标识所分析的历史批次，并非新增实验日期。\n\n'
        text+='本报告仅讨论 Qwen3.8-27B；结论由其自身病例和结果决定，不要求跨模型成立，也不推广为所有模型的性质。原始输出、分数、输入与实验状态未改；本轮新增推理调用为 0。\n\n'
        text+='统计按 Qwen-only 范围重新分析：保留原科学问题的全部正负比较、病例掩码及失败处理，重新计算 Holm；有逐病例记录或差值的主比较重新复算配对检验与 dz。原始 p 在样本未变时本来就不依赖其他模型。CSV 数值往返影响浮点并列时，保留原数值并列口径，另存重算敏感性。附表 `raw_statistic_source` 明确区分重新配对计算与沿用同一 Qwen 样本的原始统计。没有把事后分析改称预注册发现。\n\n'
        text+=TEXT[key].strip()+'\n\n## 完整主结果表\n\n'
        if key=='tournament':
            text+=table(m,['dataset','n','covered','ever_top3','ever_top5','remaining','first_mrr','oracle_mrr'])
        else:
            for sec,g in m.groupby('section',sort=False):
                text+='\n### '+sec+'\n\n'+table(g,['arm','n','mrr','ac@1','ac@3','ac@5','avg@3','avg@5','input_tokens','output_tokens'])
        for image in images:text+=f'\n![Qwen 结果：{image}]({prefix}/{image})\n'
        if restored_images:
            text+='\n### 原始 Qwen 输入示例\n\n原实验 PNG，未经本轮重渲染；SHA-256、完整输入及回答定位见 case_artifact_index.csv。案例用于解释，不替代全体统计。\n'
            for image in restored_images:text+=f'\n![Qwen 原输入：{image}]({prefix}/{image})\n'
        text+='\n## Qwen-only 配对统计\n\n以下保留指定范围的全部比较，不只保留显著项；其他数据集、层级、故障和敏感性分析见附件。Pratt-Wilcoxon 双侧及 paired dz 沿用原方法；分类、相关性和组间检验不改称 Wilcoxon。不报告置信区间。\n'
        for f,d in tests:
            text+='\n### '+f+'\n\n'
            cols=['stage','phase','experiment','family','stat_family','contrast','effect','region','arm','a','b','visual','control','baseline','round','feature','encoding','n','delta','delta_mrr','delta_rr','p','wilcoxon_p','p_exploratory','dz','paired_dz','cohen_dz','p_holm','holm_p','holm','p_adjusted','holm_exploratory','group_holm']
            text+=table(d,cols)
        if key=='rq37':
            text+='\n其中 `primary_four` 是四项病例级主比较；`group_sensitivity` 是对应四项事件组比较；`factorial_three` 是邻近、连接、交互三项。不能将组级显著性标成病例级显著性。\n'
        text+='\n## 分层、案例和复现附件\n\n所有保留的表均仅含 Qwen 结果或公共数据/CPU 基线。大型表用于完整审计，不能把其中最优分组当作预注册确认。\n\n'
        for p in sorted(target.glob('*.csv')):text+=f'- [{p.stem}]({prefix}/{p.name})\n'
        if key=='cross':
            profiles=read(target,'method_profiles.csv')
            for dim,name in [('root_level','all_method_root_tables.md'),('fault_family','all_method_fault_tables.md')]:
                sub=profiles[profiles.scope.eq('main_three')&profiles.dimension.eq(dim)]
                content=f'# Qwen：全部方法的 {dim} 画像\n\n三个主数据集、各阶段自身共同病例；不能跨阶段排名。完整五数据集与其他范围见 method_profiles.csv。\n\n'
                for (study,stage),g in sub.groupby(['study','stage']):
                    content+=f'\n## {study} / {stage}\n\n'+table(g,['arm','stratum','n','mrr','ac@1','ac@3','ac@5'])
                (target/name).write_text(content)
                text+=f'- [{dim} 全方法可读表]({prefix}/{name})\n'
        rel='../_qwen_only_reanalysis' if key=='rq12' else '_qwen_only_reanalysis'
        text+=f'\n分析口径、备份与复算说明见 [重分析说明]({rel}/README.md)。历史原始结果保持在对应 `RQs/` 下，本次没有调整实验队列、模型或评分器。\n'
        reportpath=reports/report
        assert str(reportpath.relative_to(root)) in hashes
        reportpath.write_text(text)
        outputs.append({'report':report,'tables':len(list(target.glob('*.csv'))),'figures':images,'restored_original_images':restored_images,'headline_rows':len(m)})
    index='# 实验报告：Qwen-only 版本\n\n更新：2026-09-30。当前研究限定为 Qwen3.8-27B；多模型验证是后续工作，不作为当前结论成立的必要条件。\n\n'
    for _,report,title,_ in SPECS:index+=f'- [{title}]({report})\n'
    index+='\n[重分析口径、可复现命令和备份](_qwen_only_reanalysis/README.md)。所有结果保持原阶段/批次范围，不把 screening 或 exposed test 重新称为独立验证。\n'
    (reports/'README.md').write_text(index)
    (work/'publication.json').write_text(json.dumps({'backup':str(backup),'replaced_asset_bytes':moved_bytes,'reports':outputs,'inference_calls':0},ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'reports':len(outputs),'tables':sum(x['tables'] for x in outputs),'figures':sum(len(x['figures']) for x in outputs),'backup':str(backup)},ensure_ascii=False))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--backup',type=Path,required=True);a=p.parse_args();install(a.root,a.backup)
