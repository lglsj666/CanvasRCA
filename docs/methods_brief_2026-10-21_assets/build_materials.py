"""Read-only experiment synthesis and exact-input export for the group meeting.

Writes only this documentation bundle. No model, scorer, renderer or processor runs.
"""
from pathlib import Path
import csv
import hashlib
import html
import json
import os
import shutil
import statistics

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
CASE = 'INC-058FC5DD18AD'
ARMS = ['T_FULL', 'H_TOPOLOGY', 'MARGINAL_FIVE', 'H_MARGINAL', 'A_UNIFORM_E50']
B41 = ROOT / 'RQs/RQ4_1/results/comparison_coding_v1'
B45 = ROOT / 'RQs/RQ4_5/results/exclusive_spatial_v1'
B16 = ROOT / 'RQs/RQ3_16/results/marginal_coverage_v1'
A45 = ROOT / 'docs/experiment_reports/artifacts/RQ4_5_2026-10-19'

def read(p):
    return json.loads(Path(p).read_text())

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def dump(name, obj):
    p = OUT / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n')
    return p

def rows(p):
    with open(p, newline='') as f:
        return list(csv.DictReader(f))

def table(name, data):
    with (OUT / name).open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(data[0]))
        w.writeheader()
        w.writerows(data)

def avg(rs, key):
    return statistics.mean(float(r[key]) for r in rs)

raw16 = rows(B16 / 'analysis_detailed_v1/case_metrics.csv')
meta = {r['case']: r for r in raw16 if r['arm'] == 'PAIR_FIVE'}
assert len(meta) == 220
all_rows = []
for r in rows(B41 / 'final_analysis_v1/calls.csv'):
    if r['arm'] in ['T_FULL', 'A_UNIFORM_E50', 'V_FULL'] and r['kind'] == 'development' and r['variant'] == 'BASE':
        all_rows.append(dict(id=r['id'], dataset=r['dataset'], arm=r['arm'],
            mrr=float(r['mrr']), tolerant_mrr=float(r['tolerant_mrr']),
            ac1=float(r['ac@1']), ac3=float(r['ac@3']), ac5=float(r['ac@5']),
            input=float(r['input']), output=float(r['output']), total=float(r['total']),
            text=float(r['text_tokens']), image_original=float(r['image_original']),
            image_retained=float(r['image_retained']), invalid=int(r['invalid']),
            wall=float(r['online_wall']), timing='RQ4.1 HF batch=1 processor+model online',
            record=str((B41 / 'formal_v28/completed' / (r['key']+'.json')).relative_to(ROOT))))
for r in rows(A45 / 'per_case.csv'):
    if r['arm'] in ['H_TOPOLOGY', 'H_MARGINAL']:
        all_rows.append(dict(id=r['id'], dataset=r['dataset'], arm=r['arm'],
            mrr=float(r['standard_mrr']), tolerant_mrr=float(r['tolerant_mrr']),
            ac1=float(r['ac@1']), ac3=float(r['ac@3']), ac5=float(r['ac@5']),
            input=float(r['input_tokens']), output=float(r['output_tokens']), total=float(r['total_tokens']),
            text=float(r['text_tokens']), image_original=float(r['image_original']),
            image_retained=float(r['image_retained']), invalid=int(r['invalid']=='True'),
            wall=float(r['input_to_validation']), timing='RQ4.5 vLLM concurrency=8 cached-input-to-validation',
            record=str((B45 / r['record']).relative_to(ROOT))))
for r in raw16:
    if r['arm'] in ['MARGINAL_FIVE', 'PAIR_FIVE', 'MARKLESS_FIVE']:
        all_rows.append(dict(id=r['case'], dataset=r['dataset'], arm=r['arm'],
            mrr=float(r['mrr']), tolerant_mrr=None,
            ac1=float(r['ac@1']), ac3=float(r['ac@3']), ac5=float(r['ac@5']),
            input=float(r['input_tokens']), output=float(r['output_tokens']), total=float(r['total_tokens']),
            text=float(r['text_tokens']), image_original=float(r['image_tokens']),
            image_retained=float(r['image_tokens']), invalid=int(r['score_status']!='complete'),
            wall=float(r['wall_time_s']), timing='RQ3.16 provider request wall incl. queue; original concurrency',
            record=str((B16 / 'formal/outputs' / (r['call_key']+'.json')).relative_to(ROOT))))
for r in all_rows:
    m = meta[r['id']]
    assert r['dataset'] == m['dataset']
    r['fault'] = m['fault_type']
    r['granularity'] = ','.join(sorted(json.loads(m['granularity'])))
    r['event_group'] = m['event_group']
lookup = {(r['arm'], r['id']): r for r in all_rows}
assert len(lookup) == len(all_rows)
for arm in ARMS:
    rs = [r for r in all_rows if r['arm'] == arm]
    assert len(rs) == 220 and {r['id'] for r in rs} == set(meta)
    assert all((ROOT/r['record']).exists() for r in rs)
table('per_case.csv', all_rows)

summary = []
for arm in ARMS + ['V_FULL', 'PAIR_FIVE', 'MARKLESS_FIVE']:
    for ds in ['all', 'aiops2022', 'aiops2025', 'aegislab']:
        rs = [r for r in all_rows if r['arm']==arm and (ds=='all' or r['dataset']==ds)]
        ref = [lookup['T_FULL',r['id']] for r in rs]
        x = dict(arm=arm, dataset=ds, n=len(rs))
        for key in ['mrr','ac1','ac3','ac5','text','image_original','image_retained','input','output','total','wall']:
            x[key] = avg(rs,key)
        x['tolerant_mrr'] = avg(rs,'tolerant_mrr') if all(r['tolerant_mrr'] is not None for r in rs) else None
        x['invalid'] = sum(r['invalid'] for r in rs)
        x['delta_mrr_vs_T_FULL'] = x['mrr'] - avg(ref,'mrr')
        x['cost_ratio_vs_T_FULL'] = x['total'] / avg(ref,'total')
        summary.append(x)
table('summary.csv', summary)
strata = []
for field in ['granularity','fault']:
    groups = sorted({(r['dataset'] if field=='fault' else 'all', r[field]) for r in all_rows})
    for ds, value in groups:
        for arm in ARMS:
            rs = [r for r in all_rows if r['arm']==arm and r[field]==value and (ds=='all' or r['dataset']==ds)]
            if not rs: continue
            ref = [lookup['T_FULL',r['id']] for r in rs]
            strata.append(dict(field=field,dataset=ds,value=value,arm=arm,n=len(rs),mrr=avg(rs,'mrr'),
                baseline_mrr=avg(ref,'mrr'),delta=avg(rs,'mrr')-avg(ref,'mrr'),ac5=avg(rs,'ac5')))
table('strata.csv',strata)
changes=[]
for arm,base in [(a,'T_FULL') for a in ARMS if a!='T_FULL'] + [('A_UNIFORM_E50','V_FULL'),('MARGINAL_FIVE','PAIR_FIVE')]:
    ids=sorted(meta)
    diffs=[lookup[arm,i]['mrr']-lookup[base,i]['mrr'] for i in ids]
    changes.append(dict(arm=arm,reference=base,n=220,delta=statistics.mean(diffs),
        improved=sum(d>1e-12 for d in diffs),worsened=sum(d< -1e-12 for d in diffs),tied=sum(abs(d)<=1e-12 for d in diffs),
        top1_repair=sum(lookup[arm,i]['ac1']>lookup[base,i]['ac1'] for i in ids),
        top1_break=sum(lookup[arm,i]['ac1']<lookup[base,i]['ac1'] for i in ids),
        top5_repair=sum(lookup[arm,i]['ac5']>lookup[base,i]['ac5'] for i in ids),
        top5_break=sum(lookup[arm,i]['ac5']<lookup[base,i]['ac5'] for i in ids)))
table('paired_changes.csv',changes)

# Validate against the previously audited historical aggregates; do not rescore.
checks=[]
for h in rows(A45/'historical.csv'):
    if h['arm'] not in ARMS:continue
    s=next(s for s in summary if s['arm']==h['arm'] and s['dataset']==h['dataset'])
    for k in ['mrr','input','output','total']:
        assert abs(s[k]-float(h[k])) < 1e-9,(h['arm'],h['dataset'],k)
    checks.append(h['arm']+'/'+h['dataset'])

def copy_exact(path, name, expected=None):
    path=Path(path)
    if not path.is_absolute():path=ROOT/path
    digest=sha(path)
    if expected:assert digest==expected,(path,digest,expected)
    dst=OUT/name;dst.parent.mkdir(parents=True,exist_ok=True)
    if not dst.exists():
        try:os.link(path,dst)
        except OSError:shutil.copyfile(path,dst)
    assert sha(dst)==digest
    return dict(file=str(dst.relative_to(OUT)),sha256=digest,source=str(path.relative_to(ROOT)))

# Split only for display. Every character of every original text part survives.
INSTRUCTION_PREFIXES = (
    'A fault has occurred','Source reading:','Literal reading','Exact compact sequences:',
    'G: calls A -> B','Service names, pod names, and node names are represented',
    'Common evidence; field=evidence_legends;', 'Additional observations use',
    'Additional component facts not already present','Reference operands AUX01',
    'Full-window observations:', 'Observed request pairs:', 'Pair fields:',
    'Continuous pair fields:', 'Output cardinality for this request:',
    'Based on the above', 'Evidence ownership:',
)

def split_part(text):
    if text.startswith(('A fault has occurred','Diagnose the initiating component')):
        return [dict(kind='instruction',start=0,end=len(text),text=text)]
    chunks=[]; pos=0;last='instruction'
    # RQ4.5 coalesces all parts; its leading static task ends at the G legend.
    if text.startswith('Identify the original faulty component'):
        cut=text.index('\nG: calls A -> B')
        chunks.append(dict(kind='instruction',start=0,end=cut,text=text[:cut]));pos=cut
    for line in text[pos:].splitlines(keepends=True):
        kind='instruction' if line.lstrip().startswith(INSTRUCTION_PREFIXES) else ('evidence' if line.strip() else last)
        if chunks and chunks[-1]['kind']==kind and chunks[-1]['end']==pos:
            chunks[-1]['end']+=len(line);chunks[-1]['text']+=line
        else:chunks.append(dict(kind=kind,start=pos,end=pos+len(line),text=line))
        pos+=len(line);last=kind
    assert ''.join(c['text'] for c in chunks)==text
    assert all(text[c['start']:c['end']]==c['text'] for c in chunks)
    return chunks

examples=[]
for arm in ARMS:
    r=lookup[arm,CASE];record_path=ROOT/r['record'];record=read(record_path)
    if arm in ['T_FULL','A_UNIFORM_E50']:
        request_path=B41/'formal_v28/requests'/f'{CASE}__development__{arm}__BASE.json'
        original=read(request_path);req=original['request'];system=req['system'];parts=req['parts']
        imgs=[(req['png'],req['png_sha256'])] if req.get('png') else []
        raw_prompt=req['prompt'];response=record['response']
        token_indices=record.get('actual_retention',{});token_indices=token_indices.get('indices') if token_indices else None
    elif arm=='MARGINAL_FIVE':
        key=record['call_key'];request_path=B16/'formal/prompts'/f'{key}.json'
        original=read(request_path);system=original['system'];parts=original['parts']
        imgs=[(B16/'formal'/p['image_path'],p['image_sha256']) for p in parts if p['type']=='image']
        raw_prompt=None;response=record['response'];token_indices=None
    else:
        request_path=B45/'formal'/record['request_path'];original=read(request_path)
        system=original['messages'][0]['content'];parts=original['messages'][1]['content']
        imgs=list(zip(original['images'],original['image_sha256']));raw_prompt=original['prompt']
        response=record['response'];token_indices=original['retained_by_image']
    prefix='examples/'+arm
    request_copy=copy_exact(request_path,prefix+'/request.original.json')
    record_copy=copy_exact(record_path,prefix+'/result.original.json')
    images=[copy_exact(p,prefix+f'/dashboard_{i+1}.png',h) for i,(p,h) in enumerate(imgs)]
    split=[]
    for i,p in enumerate(parts):
        if p['type']=='text':
            split.extend(dict(part=i,**s) for s in split_part(p['text']))
    dump(prefix+'/text_spans.json',split)
    task=system+'\n\n'+ '\n\n'.join(s['text'] for s in split if s['kind']=='instruction')
    evidence='\n\n'.join(s['text'] for s in split if s['kind']=='evidence')
    for name,content in [('instructions.txt',task),('evidence.txt',evidence),('response.txt',response)]:
        (OUT/prefix/name).write_text(content)
    if raw_prompt is not None:(OUT/prefix/'prompt.serialized.txt').write_text(raw_prompt)
    if token_indices is not None:dump(prefix+'/retained_token_indices.json',token_indices)
    examples.append(dict(arm=arm,id=CASE,dataset=r['dataset'],mrr=r['mrr'],cost=r['total'],
        system=system,parts=parts,spans=split,instructions=task,evidence=evidence,response=response,
        images=images,request=request_copy,record=record_copy,token_indices=token_indices is not None))

dump('examples.json',examples)

# Standalone scientific plot, drawn from audited aggregate numbers.
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
colors=['#64748b','#2563eb','#8b5cf6','#08916f','#d97706']
names=['T_FULL','TPV / H_TOPOLOGY','MARGINAL_FIVE','H_MARGINAL','A_UNIFORM_E50']
overall={s['arm']:s for s in summary if s['dataset']=='all'}
fig,ax=plt.subplots(1,2,figsize=(12,4.5),layout='constrained')
for i,arm in enumerate(ARMS):
    s=overall[arm]
    ax[0].barh(i,s['mrr'],color=colors[i]);ax[0].text(s['mrr']+.008,i,f"{s['mrr']:.4f}",va='center')
    ax[1].barh(i,s['total']/1000,color=colors[i]);ax[1].text(s['total']/1000+.3,i,f"{s['total']/1000:.2f}k",va='center')
for a in ax:
    a.set_yticks(range(len(ARMS)),names);a.invert_yaxis();a.spines[['top','right']].set_visible(False)
    a.grid(axis='x',alpha=.18);a.set_axisbelow(True)
ax[0].set_xlim(0,.59);ax[0].set_xlabel('Standard MRR (220 exposed development cases)')
ax[1].set_xlim(0,27);ax[1].set_xlabel('Mean actual input + output tokens / diagnosis')
fig.suptitle('Historical system comparison: different rounds and inference backends',fontsize=13)
fig.savefig(OUT/'performance_cost.svg');fig.savefig(OUT/'performance_cost.png',dpi=170);plt.close(fig)

def esc(s):return html.escape(str(s))
def link(path,label):return f'<a href="{esc(path)}">{esc(label)}</a>'
def details(title,content,opened=False):return f'<details {"open" if opened else ""}><summary>{esc(title)}</summary>{content}</details>'
descriptions={
 'T_FULL':'完整强文本；所有诊断信息在文本中，无 dashboard。',
 'H_TOPOLOGY':'新版 TPV：调用与部署边在图中，指标、Trace、日志及耗时配对在文本中。',
 'MARGINAL_FIVE':'历史高分混合方案：完整文本＋重复呈现配对分布的原生边际图。',
 'H_MARGINAL':'独占边际图：配对样本与统计移交图像，其余诊断信息保留文本。',
 'A_UNIFORM_E50':'完整纯视觉原图；编码完成后保留全部锚点及一半可选证据 token。',
}
design_steps={
 'T_FULL':[
  '保留冻结的指标、Trace、日志、关系、窗口摘要及父子耗时配对，按原有组织写入文字。',
  '附上完整候选、单位与统计读法，以及检查根因和下游症状的任务说明。',
  '一次调用直接输出五个不同候选及简短理由；不发送图像。'],
 'H_TOPOLOGY':[
  '取出调用与部署关系，分别用实体节点和有向箭头绘制。',
  '从诊断文字中移除这些关系记录；其余指标、Trace、日志及耗时配对仍以文字提供。',
  '图像编码后保留全部登记锚点和证据支持；与剩余文字一起完成一次诊断。'],
 'MARGINAL_FIVE':[
  '保留完整 PAIR_FIVE 文字，包括已经存在的配对样本和统计。',
  '按父调用两阶段 p95 耗时变化选择最多两个合格关系，每阶段最多展示 32 个真实配对。',
  '将父、子各自的参考与当前耗时画成边际分布，再与完整文字一起输入。',
  '输出固定五候选。FIVE 指输出数量；图像重复部分文本事实，并不替代那部分文字。'],
 'H_MARGINAL':[
  '沿用最多两个关系的选择定义，将整组配对样本及其统计从文字移入图像。',
  '使用完整边际图组件，在分布旁呈现样本对应、原精度数值和统计；其余诊断证据保留在文字中。',
  '图像保留全部登记支持，与剩余文字完成一次诊断。无合格配对时执行历史登记的拓扑回退，并保留在分母中。'],
 'A_UNIFORM_E50':[
  '把全部诊断证据和候选目录放在完整 dashboard 中，图外仅保留静态任务说明。',
  '先对完整 PNG 做视觉编码，再保护所有身份、单位、阶段等锚点 token。',
  '在其余登记证据 token 内，依次填补最大的空间缺口，确定性地选择一半；不是随机删半张图片。',
  '按原顺序与位置编码收集保留特征，交给语言模型完成一次诊断。'],
}
sections=[]
for ex in examples:
    a=ex['arm'];s=overall[a];pre='examples/'+a
    visual=''
    if ex['images']:
        visual='<p>下列图片均为实际请求中的原始 PNG。一个病例可能发送两张图；两张均保留，未拼接成不存在的输入。</p>'
        for j,img in enumerate(ex['images']):
            visual+=f'<div class="image-controls">图 {j+1} · <button onclick="fit(this)">适应宽度</button><button onclick="native(this)">原始像素 / 滚动查看</button> {link(img["file"],"单独打开 PNG")}</div><div class="image-wrap"><img class="dashboard" src="{esc(img["file"])}" alt="{a} actual input image {j+1}" loading="lazy"></div>'
        if a=='A_UNIFORM_E50':
            if (OUT/pre/'anchor_optional_viewer.html').is_file():
                visual='<p>下方为实际保留集合的分析标注，未发送给模型。蓝框是全部 A，橙框是保留的 E；灰色虚线层可查看未保留的 E。底图仍为完整原 PNG。</p>'
                visual+=f'<iframe title="A_UNIFORM_E50 实际 token 集合标注" src="{pre}/anchor_optional_viewer.html" style="width:100%;height:900px;border:1px solid #c5d0df" loading="lazy"></iframe>'
                visual+='<p>'+link(pre+'/anchor_optional_viewer.html','单独打开交互标注图')+' · '+link(pre+'/dashboard_1.png','未标注的实际输入 PNG')+'</p>'
            else:
                visual+='<p class="note">浏览器展示编码器接收的完整 PNG。剪枝发生在视觉编码之后，因此没有一张“剪掉像素”的实际输入图。保留索引在下方附件中。</p>'
    else:visual='<div class="empty">T_FULL 实际没有图像输入；这里不生成或冒充一张文本 dashboard。</div>'
    raw=''
    for j,p in enumerate(ex['parts']):
        raw+=f'<h4>Part {j} · {esc(p["type"])}</h4>'
        raw+=f'<pre>{esc(p["text"])}</pre>' if p['type']=='text' else '<p>图像占位；对应上方实际 PNG。</p>'
    evidence=ex['evidence'] or '无图外诊断证据；候选、数值、实体和关系均在图像中。'
    downloads=' · '.join([link(pre+'/request.original.json','原始请求 JSON'),link(pre+'/result.original.json','原始结果 JSON'),link(pre+'/instructions.txt','任务与读图说明 TXT'),link(pre+'/evidence.txt','文本证据 TXT'),link(pre+'/text_spans.json','拆分字符位置与原顺序'),link(pre+'/response.txt','模型原回答')])
    if ex['token_indices']:downloads+=' · '+link(pre+'/retained_token_indices.json','实际 token 保留索引')
    design='<h3>这个 arm 怎样构造一次诊断</h3><ol>'+''.join('<li>'+esc(step)+'</li>' for step in design_steps[a])+'</ol>'
    sections.append(f'''<section id="{a}"><h2>{a}</h2><p>{descriptions[a]}</p>{design}<div class="chips"><span>总体 MRR {s['mrr']:.4f}</span><span>总 tokens {s['total']:,.1f} / 例</span><span>本例 RR {ex['mrr']:.4f}</span><span>本例 tokens {ex['cost']:,.0f}</span></div>
    {visual}<div class="columns"><div>{details('Prompt：系统、任务、读图及输出要求', '<pre>'+esc(ex['instructions'])+'</pre>',True)}</div><div>{details('其他文本输入：病例证据、候选与观察窗口', '<pre>'+esc(evidence)+'</pre>',True)}</div></div>
    {details('本例模型原回答（输出，不属于输入）','<pre>'+esc(ex['response'])+'</pre>')}
    {details('原请求顺序与全部文本：未经改写的完整 parts', '<h4>System</h4><pre>'+esc(ex['system'])+'</pre>'+raw)}
    <p class="downloads">{downloads}</p></section>''')
head=''.join(f'<tr><td>{a}</td><td>{overall[a]["mrr"]:.4f}</td><td>{overall[a]["delta_mrr_vs_T_FULL"]:+.4f}</td><td>{overall[a]["total"]:,.1f}</td><td>{(overall[a]["cost_ratio_vs_T_FULL"]-1)*100:+.2f}%</td></tr>' for a in ARMS)
page='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>CanvasRCA · 四类代表方法与真实输入</title><style>
:root{color-scheme:light}*{box-sizing:border-box}body{margin:0;font:16px/1.75 system-ui,"Microsoft YaHei",sans-serif;background:#f4f6fa;color:#172337}header{padding:42px max(5vw,24px);background:#132437;color:white}h1{font-size:30px;margin:0 0 14px}h2{font-size:25px}main{max-width:1400px;margin:auto;padding:24px}nav{position:sticky;top:0;background:#fff;box-shadow:0 2px 8px #1232;padding:12px;z-index:1;display:flex;flex-wrap:wrap;gap:16px}nav a{font-size:14px}a{color:#1761a5}section{scroll-margin-top:80px;background:white;padding:26px;margin:24px 0;border-radius:12px;box-shadow:0 3px 18px #1231}.chips{display:flex;gap:10px;flex-wrap:wrap;margin:15px 0}.chips span{background:#edf2fa;padding:5px 12px;border-radius:20px;font-size:14px}.columns{display:grid;grid-template-columns:1fr 1fr;gap:16px}details{border:1px solid #d7e0ed;border-radius:6px;margin:16px 0;padding:12px}summary{cursor:pointer;font-weight:650}pre{white-space:pre-wrap;overflow-wrap:anywhere;max-height:630px;overflow:auto;font:13px/1.6 ui-monospace,Consolas,monospace;background:#f7f9fc;padding:14px}table{border-collapse:collapse;width:100%}th,td{border-bottom:1px solid #dce4ee;padding:10px;text-align:left}th{background:#edf2fa}.dashboard{width:100%;height:auto;display:block;max-width:none}.image-wrap{overflow:auto;max-height:760px;background:#0e1821;border:1px solid #c5d0df}.image-controls{padding:10px 0;display:flex;gap:10px;align-items:center;flex-wrap:wrap}button{padding:6px 12px;border:1px solid #b7c8df;background:white;cursor:pointer;border-radius:5px}.note,.empty{background:#fff4d8;padding:14px;border-left:4px solid #ca921b}.downloads{font-size:13px}footer{padding:20px;color:#53677a}@media(max-width:850px){.columns{grid-template-columns:1fr}main{padding:12px}section{padding:16px}}
</style></head><body><header><h1>CanvasRCA：四类代表方法与真实输入</h1><p>TPV · Marginal graphs（两种版本） · A_UNIFORM_E50 · T_FULL<br>组会材料 · 2026-10-21 · 220 个已暴露开发病例 · 无新增模型调用</p></header>'''
    
page+='<nav>'+''.join(f'<a href="#{a}">{a}</a>' for a in ARMS)+'</nav><main>'
page+='<section><h2>结果与成本</h2><p>跨轮结果仅用于工程比较；不能把差值全部归因于模态。标准 MRR 包含无效回答零分。成本是实际输入＋输出 token，含图像进入语言模型的 token，不能直接等价为美元或运行时间。</p><table><tr><th>Arm</th><th>MRR</th><th>Δ vs T_FULL</th><th>tokens / 例</th><th>成本变化</th></tr>'+head+'</table><img style="width:100%" src="performance_cost.svg" alt="MRR and total tokens comparison"></section>'
page+=f'<section><h2>展示口径</h2><p>统一示例：AegisLab <code>{CASE}</code>。选用已有报告中审查过的服务延迟案例，便于横向阅读；它是说明性样例，不能代表总体成功率。每个 arm 展示该病例的一份真实请求。T_FULL 无图；两个 RQ4.5 hybrid 的一次请求实际含两张图，均完整提供。</p><p class="note">左右两栏按说明/证据拆分，是展示层整理。历史输入中的混合段、旧措辞和重复都原样保留；拆分字符位置可验证重建，完整请求顺序可在每节底部展开。历史措辞冲突没有被悄悄修正。</p><p>'+link('../CanvasRCA_Representative_Methods_Group_Meeting_2026-10-21.md','详细 Markdown 报告')+'</p></section>'
page+=''.join(sections)
page+='''</main><footer>所有 dashboard 复用 src/renderer/ 生成的真实实验 PNG，按原哈希核验。U 的彩框是汇报用分析层，未进入模型；未重新渲染遥测或调用模型。无外部脚本、CDN 或网络依赖。</footer><script>
function native(b){const im=b.parentElement.nextElementSibling.querySelector('img');im.style.width=im.naturalWidth+'px';}
function fit(b){b.parentElement.nextElementSibling.querySelector('img').style.width='100%';}
</script></body></html>'''
(OUT/'index.html').write_text(page)
manifest=dict(analysis_only=True,new_model_calls=0,manual_images_opened=0,example_case=CASE,
    canonical_arms=ARMS,rows=len(all_rows),main_rows=1100,aggregate_matches=checks,
    source_tables={str(p.relative_to(ROOT)):sha(p) for p in [B41/'final_analysis_v1/calls.csv', B16/'analysis_detailed_v1/case_metrics.csv',A45/'per_case.csv',A45/'historical.csv']},
    examples=[{k:v for k,v in e.items() if k in ['arm','id','images','request','record']} for e in examples],
    text_split='Exact original part offsets; concatenation verified before display regrouping.',
    run_status_files=[str(p.relative_to(ROOT)) for p in [B41/'formal_v28/phase_complete.hf.json',B45/'formal/phase_complete.json',B16/'formal/phase_complete.qwen3.8-27b.json']])
assert all((ROOT/p).exists() for p in manifest['run_status_files'])
dump('provenance.json',manifest)
print(json.dumps(dict(status='built',path=str(OUT),rows=len(all_rows),examples=len(examples),images=sum(len(e['images']) for e in examples),historical_aggregates_verified=len(checks)),ensure_ascii=False))
