"""Export frozen local facts for Nibi; no raw preparation or model calls.

Private scoring records are copied separately after compilation, never supplied
to the renderer. Only repository-owned trusted caches are unpickled.
"""
import argparse
import concurrent.futures as cf
import hashlib
import multiprocessing as mp
import pickle
import time

from RQs.RQ3_8.src.utils import ROOT, DATA, read, save, digest

PARENT=ROOT/'RQs/RQ3_7/results/fusion_v2_pruned'
SOURCE=ROOT/'RQs/RQ3_4/results/integrated_v1'


def export(row):
    oid=row['opaque_incident_id']; target=DATA/'public'/f'{oid}.json'
    flag=DATA/'flags'/f'{oid}.json'
    if flag.exists():
        return read(flag)
    started=time.monotonic()
    views=list((PARENT/'public_cache').glob('*/'+oid+'.pkl'))
    if len(views)!=1:
        # A few early dev cases have two caches. They must agree on public facts.
        candidates=[pickle.loads(p.read_bytes())['view'] for p in views]
        if not candidates or len({digest([v.parts,v.metric_facts,v.relations]) for v in candidates})!=1:
            raise ValueError('Missing/ambiguous frozen view '+oid)
        view=candidates[0]
    else:
        view=pickle.loads(views[0].read_bytes())['view']
    source=next((p for p in (SOURCE/'contexts'/f'{oid}.pkl',PARENT/'contexts'/f'{oid}.pkl') if p.exists()),None)
    if source is None:
        raise FileNotFoundError('No cached context '+oid)
    context=pickle.loads(source.read_bytes())
    if context['prepared'].private:
        raise ValueError('Private metadata in source public cache')
    from renderer.topology import development_topology
    cards,audit=development_topology(row,context)
    relations=set(tuple(r) for r in view.relations)
    for card in cards:
        if card['kind']=='graph':
            relations.update((e['source'],e['target'],e['kind']) for e in card['data']['edges'])
    public={'system':view.system,'parts':[{'type':'text','text':p['text']} for p in view.parts],
            'metrics':list(view.metric_facts),'candidates':list(view.candidates),
            'selected_relations':[list(r) for r in view.relations],
            'full_relations':[list(r) for r in sorted(relations)]}
    # No row identity, case path, dataset or evaluator-private object in DTO.
    from RQs.RQ3_8.src.exps import evidence
    evidence(public,'LINE_BOUND')
    save(target,public)
    private_path=next(p for p in (SOURCE/'private'/f'{oid}.json',PARENT/'private'/f'{oid}.json') if p.exists())
    save(DATA/'private'/f'{oid}.json',read(private_path))
    save(DATA/'audit'/f'{oid}.json',{'topology':audit,'view_sources':[str(p) for p in views],
         'source_context':str(source),'context_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
         'public_sha256':digest(public)})
    result={'status':'done','case':oid,'seconds':time.monotonic()-started,'public_hash':digest(public),
            'relations_selected':len(view.relations),'relations_full':len(relations)}
    save(flag,result)
    return result


def export_main():
    p=argparse.ArgumentParser();p.add_argument('--workers',type=int,default=8);p.add_argument('--limit',type=int)
    args=p.parse_args()
    if not 1<=args.workers<=8:raise ValueError('workers 1..8')
    reg=read(PARENT/'registration.json');rows=reg['rosters']['eval']
    from RQs.RQ3_3.src.main import interleaved_sources
    rows=interleaved_sources(rows)
    # Exactly the same public identity/source split; balanced shard round robin.
    groups={};shards={}
    for dataset in sorted({r['dataset'] for r in rows}):
        ds=sorted((r for r in rows if r['dataset']==dataset),key=lambda r:digest(['42',r['opaque_incident_id']]))
        for i,r in enumerate(ds):shards[r['opaque_incident_id']]=i%3
    minimal=[{k:r[k] for k in ('dataset','opaque_incident_id','leakage_group','source')}|
             {'shard':shards[r['opaque_incident_id']]} for r in rows]
    smoke=[min((r for r in reg['rosters']['development'] if r['dataset']==d),
               key=lambda r:r['opaque_incident_id'])['opaque_incident_id']
           for d in ('aiops2022','aiops2025','aegislab')]
    save(DATA/'roster.json',{'cases':minimal,'smoke':smoke,'scope':'repeated-exposed eval480'})
    if args.limit:
        rows=[r for r in rows if r['opaque_incident_id'] in smoke][:args.limit]
    from vlmrca.run_state import physical_cpu_ids,pin_process_to_core
    ctx=mp.get_context('spawn');queue=ctx.Queue();cores=physical_cpu_ids()[:min(args.workers,len(rows))]
    for core in cores:queue.put(core)
    with cf.ProcessPoolExecutor(len(cores),mp_context=ctx,initializer=pin_process_to_core,initargs=(queue,)) as pool:
        for value in pool.map(export,rows):print(value,flush=True)


def gpu_device(out):
    import torch
    if torch.cuda.device_count()!=1:raise RuntimeError('Exactly one assigned full GPU required')
    props=torch.cuda.get_device_properties(0)
    result={'name':props.name,'total_memory':props.total_memory,'torch':torch.__version__}
    save(out,result)
    if 'H100' not in props.name or props.total_memory < 75*1024**3:
        raise RuntimeError('Requires full 80-GB H100; 40-GB MIG is not sufficient')


def ready(model,pid,out):
    import os
    import requests
    from unified_scripts.vllm_inference import VLLMInferenceConfig
    config=VLLMInferenceConfig.load();spec=config.model(model)
    deadline=time.monotonic()+1200
    while time.monotonic()<deadline:
        os.kill(pid,0)
        try:
            response=requests.get(spec['base_url']+'/models',timeout=5)
            if response.ok and spec['served_model_name'] in {x['id'] for x in response.json()['data']}:
                record={'status':'ready','model':model,'time':time.time(),'pid':pid,
                        'effective_runtime':spec,'config':config.audit_record()}
                save(out,record);print('SERVER_READY',model,flush=True);return
        except requests.RequestException:
            pass
        time.sleep(5)
    raise TimeoutError('Server did not become ready')


def main():
    import sys
    if len(sys.argv)<2 or sys.argv[1].startswith('--'):
        export_main();return
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='command',required=True)
    d=sub.add_parser('gpu-device');d.add_argument('--out',required=True)
    r=sub.add_parser('ready');r.add_argument('--model',required=True);r.add_argument('--pid',type=int,required=True);r.add_argument('--out',required=True)
    args=p.parse_args()
    if args.command=='gpu-device':gpu_device(args.out)
    else:ready(args.model,args.pid,args.out)


if __name__=='__main__':main()
