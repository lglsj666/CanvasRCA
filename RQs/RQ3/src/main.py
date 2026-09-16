"""RQ3 local entry points; no implicit full training after qualification."""
from __future__ import annotations

import argparse
import os
from dataclasses import asdict
from pathlib import Path

import yaml
from unified_scripts import stable_hash
from unified_scripts.vllm_inference import VLLMInferenceConfig
from vlmrca.run_state import physical_cpu_ids, smoke_server_ready, _stop_search_process, pinned_process_map, pin_process_to_core as _pin_render_worker
from .utils import (ROOT, RQ3SegmentationAdapter, read_json, write_json, atomic_write,
                    catalogue_contract,owned_gpu_process,preparation_identity_matches)

DEFAULT_CONFIG = ROOT / "RQs/RQ3/configs/rq3.yaml"


def load_config(path=DEFAULT_CONFIG, _seen=()):
    if Path(path).resolve() in _seen:raise ValueError('cyclic RQ config inheritance')
    config = yaml.safe_load(Path(path).read_text())
    if "extends" in config:
        from unified_scripts import deep_merge
        base = load_config(ROOT/config.pop('extends'),(*_seen,Path(path).resolve()))
        config = deep_merge(base, config)
    os.environ["CANVASRCA_ROOT"] = str(ROOT)
    os.environ["CANVASRCA_PROCESSED_ROOT"] = str(ROOT / config["processed_root"])
    if config.get('search',{}).get('selection_only_suite'):
        validate_selection_only_config(config)
    return config


def validate_selection_only_config(config):
    """Only the selector/method identity may change after the round-16 anchor."""
    from copy import deepcopy
    from .exps import SELECTION_ONLY_POLICIES
    from .utils import sha_file
    suite=yaml.safe_load((ROOT/config['search']['selection_only_suite']).read_text())
    if suite.get('execution_authorized', True) is not True:
        raise ValueError('selection suite is implementation/static-only; user resume authorization required')
    anchor=load_config(ROOT/suite['anchor_config'])
    if stable_hash(anchor)!=suite['anchor_config_hash']: raise ValueError('selection-only anchor config drift')
    paths=sorted((ROOT/'RQs/RQ3/src/renderer').rglob('*.py'))+sorted((ROOT/'RQs/RQ3/configs/prompts').glob('tournament*.txt'))+[ROOT/'configs/vllm_inference_local.yaml']
    if stable_hash({str(p.relative_to(ROOT)):sha_file(p) for p in paths})!=suite['display_prompt_runtime_tree_hash']:
        raise ValueError('selection-only display/prompt/runtime drift')
    proposed=deepcopy(config); proposed['search'].pop('selection_only_suite')
    policies=proposed['search']['selectors']
    if len(policies)!=1 or policies[0] not in SELECTION_ONLY_POLICIES or policies[0] not in suite['pending_policies']:
        raise ValueError('not a registered selection-only policy')
    proposed['search']['selectors']=anchor['search']['selectors']
    proposed['tournament']['method_id']=anchor['tournament']['method_id']
    if proposed!=anchor: raise ValueError('selection-only config changed a non-selection setting')
    return suite


def audit_selection_suite(config, source, output):
    """All remaining public pools, streamed once each; no model call or label read."""
    import time
    from itertools import combinations
    from collections import Counter, defaultdict
    from .exps import selection_only_context,select_diagnostic_evidence,project_log_summaries,compact_evidence_text
    from .utils import tournament_register,sha_file
    suite=validate_selection_only_config(config); state=tournament_register(config).state()
    ids=sorted(set().union(*(set(v['eligible']) for v in state['models'].values())))
    pools={r['opaque_incident_id']:source/r['public'] for r in read_json(source/'index.json')['cases']}
    rows=[]; timing=[]; pairwise=defaultdict(list); changed=Counter();counts=Counter(); start=time.monotonic()
    native={str(p.relative_to(ROOT)):sha_file(p) for p in sorted((ROOT/'packages/rq3_selection_native/adapted').glob('*.py'))}
    # Audit results are written back into the suite after passage.  Exclude
    # those mutable status fields from the identity to avoid a circular hash
    # that would make a completed audit impossible to resume or reproduce.
    suite_contract={k:v for k,v in suite.items() if k not in ('status','cpu_audit')}
    identity=stable_hash([suite_contract,ids,sha_file(ROOT/'RQs/RQ3/src/exps.py'),native])
    for i,case in enumerate(ids):
        target=output/'cases'/f'{case}.json'
        if target.exists():
            entry=read_json(target)
            if entry['audit_identity']!=identity:raise ValueError('existing selection audit differs; preserve it')
        else:
            begin=time.monotonic();pool=read_json(pools[case])['pool'];ctx=selection_only_context(pool)
            def signature(packet):
                projected,_=project_log_summaries(packet)
                return {'ids':sorted(f['fact_id'] for f in packet['facts']),
                    'text_sha256':stable_hash(compact_evidence_text(projected))}
            signatures={'anchor':signature(ctx['anchor'])}; audits={}
            for policy in suite['pending_policies']:
                packet,audit=select_diagnostic_evidence(pool,policy,ctx)
                source_facts={f['fact_id']:f for f in pool['facts']}
                if any(f!=source_facts.get(f['fact_id']) for f in packet['facts']):raise ValueError('selector changed a public fact')
                if packet['candidates']!=pool['candidates']:raise ValueError('selector changed candidates')
                if any(sum(f['field']==key for f in packet['facts'])!=n for key,n in audit['budgets'].items()):raise ValueError('selector budget mismatch')
                signatures[policy]=signature(packet)
                audits[policy]={k:v for k,v in audit.items() if k!='scores'}
                audits[policy]['score_hash']=stable_hash(audit['scores'])
                audits[policy]['selected_score_components']={key:value for key,value in audit['scores'].items() if key in audit['selected_ids']}
            if stable_hash(pool['facts'])!=ctx['source_hash']:raise ValueError('selector mutated pool')
            entry={'case':case,'audit_identity':identity,'signatures':signatures,'audits':audits,
                   'seconds':time.monotonic()-begin,'source_hash':ctx['source_hash']}
            write_json(target,entry)
            del pool,ctx,packet,audit,source_facts
        rows.append(entry['case']);timing.append(entry['seconds']); sig=entry['signatures']
        for policy in suite['pending_policies']:
            if sig[policy]['ids']!=sig['anchor']['ids']:changed[policy]+=1
            if sig[policy]['text_sha256']!=sig['anchor']['text_sha256']:counts[policy]+=1
        for a,b in combinations(sig,2):
            aa=set(sig[a]['ids']);bb=set(sig[b]['ids']);pairwise[a+' / '+b].append(len(aa&bb)/len(aa|bb) if aa|bb else 1.)
        if (i+1)%20==0:print({'selector_audit_cases':i+1,'total':len(ids)},flush=True)
    result={'status':'passed','model_calls':0,'cases':len(rows),'case_ids':rows,'audit_identity':identity,
        'cohort_sizes':{k:len(v['eligible']) for k,v in state['models'].items()},'rounds_completed':state['rounds'],
        'changed_fact_sets':dict(changed),'changed_text_inputs':dict(counts),
        'mean_pairwise_jaccard':{k:sum(v)/len(v) for k,v in pairwise.items()},
        'sum_case_cpu_seconds':sum(timing),'wall_seconds':time.monotonic()-start}
    write_json(output/'summary.json',result);return result


def preview_selection_suite(config, source, output):
    """CPU-only input review; this subset is never an inference cohort."""
    source=source.resolve();output=output.resolve()
    from .utils import tournament_register, partition_rows
    suite=validate_selection_only_config(config);state=tournament_register(config).state()
    allowed=set().union(*(set(v['eligible']) for v in state['models'].values()))
    rows=partition_rows(config,RQ3SegmentationAdapter(config).build(),'tournament')
    chosen=[min((r for r in rows if r['dataset']==ds and r['opaque_incident_id'] in allowed),
                key=lambda r:stable_hash([42,r['opaque_incident_id']])) for ds in ('aegislab','aiops2022','aiops2025')]
    index={r['opaque_incident_id']:r for r in read_json(source/'index.json')['cases']}
    jobs=[(load_config(ROOT/path),source,output,r,index[r['opaque_incident_id']],'tournament')
          for r in chosen for path in suite['method_configs'].values()]
    attempts=[a for batch in pinned_process_map(_search_gallery_case,jobs) for a in batch]
    result={'attempts':attempts,'model_calls':0,'purpose':'CPU visual inspection only',
        'sampling':'hash42 one per primary from remaining union',
        'cases':[{'opaque_incident_id':r['opaque_incident_id'],'dataset':r['dataset']} for r in chosen]}
    write_json(output/'summary.json',result);return result


def review_selection_preview(output):
    """Audit rendered inputs against round 16; private identities only check leakage."""
    from PIL import Image, ImageChops
    from .exps import validate_tournament_parts
    from .gates import audit_public_pool
    from .renderer.card_families import audit_family_geometry
    from RQs.RQ2.src.utils import audit_visible
    from .utils import sha_file
    output=output.resolve(); summary=read_json(output/'summary.json')
    parent=ROOT/'RQs/RQ3/results/tournament_v1/round_0016_full_candidate_binding_v3/gallery'
    refs={a['case']:a for a in read_json(parent/'summary.json')['attempts']}; rows=[]
    for a in summary['attempts']:
        if a['status']!='rendered':raise ValueError(f"selection preview failed: {a}")
        stem=output/a['case']/a['family'];ref=refs[a['case']];old=parent/a['case']/ref['family']
        packet=read_json(stem.with_suffix('.packet.json'));parts=read_json(stem.with_suffix('.prompt.json'))
        manifest=read_json(stem.with_suffix('.manifest.json'))
        assert parts==read_json(old.with_suffix('.prompt.json')),'fixed prompt/candidates changed'
        assert validate_tournament_parts(parts)[1]==packet['candidates']
        audit_public_pool(packet);audit_family_geometry(manifest)
        assert manifest['source_packet_fact_inventory_hash']==packet['fact_inventory_hash']==stable_hash(packet['facts'])
        assert manifest['manifest_sha256']==stable_hash({k:v for k,v in manifest.items() if k!='manifest_sha256'})
        facts={f['fact_id']:f for f in packet['facts'] if f['region']!='C'}
        mapping={f['fact_id']:f for f in manifest['fact_mapping']}
        assert len(mapping)==len(manifest['fact_mapping']) and facts.keys()==mapping.keys()
        assert all(f['primitive_geometry'] for f in mapping.values())
        assert manifest['clipping_audit']['status']=='passed'
        assert sha_file(stem.with_suffix('.png'))==a['png_sha256']
        with Image.open(stem.with_suffix('.png')) as im, Image.open(old.with_suffix('.png')) as before:
            im.load();before.load();assert im.size==tuple(manifest['canvas_size'])
            # Compare decoded pixels, not PNG metadata or file hashes alone.
            pixels_changed=im.size!=before.size or ImageChops.difference(im.convert('RGB'),before.convert('RGB')).getbbox() is not None
        private=read_json(ROOT/a['private'])
        audit_visible([parts,list(facts.values()),manifest['fact_mapping'],manifest['cards']],
                      [private['case_id'],*private['numeric_to_natural'].values()])
        assert sha_file(ROOT/a['source'])==a['source_file_hash']==ref['source_file_hash']
        old_packet=read_json(old.with_suffix('.packet.json'))
        changed={f['fact_id'] for f in old_packet['facts']}!={f['fact_id'] for f in packet['facts']}
        if changed and not pixels_changed:raise ValueError('changed evidence did not reach image')
        rows.append({'case':a['case'],'selector':a['selection']['policy'],'fact_set_changed':changed,
                     'decoded_pixels_changed':pixels_changed,'prompt_unchanged':True,'png_sha256':a['png_sha256']})
    result={'status':'passed','model_calls':0,'reviewed_renders':len(rows),'rows':rows}
    write_json(output/'input_audit.json',result);return result


def rca_scorer(config):
    """Unified metric definitions with the already-validated standalone matcher."""
    from unified_scripts.rca_scorer import RCAScorer, RCAScorerConfig
    from RQs.RQ2_1.src.utils import is_granularity_aware_hit
    return RCAScorer(RCAScorerConfig.load(config['unified']['scorer']),
                     hit=is_granularity_aware_hit)


def _prepare_lane(config, output, partition, rows, split_hash, contract, cpu, pools_only=False, reuse=None):
    """CPU-only lane. A crash preserves each fully written prior case."""
    from .exps import build_pool
    from .gates import audit_catalog, audit_public_pool, audit_catalog_inventory
    from .utils import pool_contract, sha_file
    os.sched_setaffinity(0, {cpu})
    output = Path(output)
    index = []
    for row in rows:
        opaque = row["opaque_incident_id"]
        target = output / "public" / f"{opaque}.json"
        private_path = output / "private" / f"{opaque}.json"
        if target.exists():
            payload = read_json(target)
            contract_name='pool_contract' if pools_only else 'catalog_contract'
            if payload["split_hash"] != split_hash or not preparation_identity_matches(payload.get(contract_name),contract,'pool' if pools_only else 'catalogue'):
                raise ValueError("existing prepared case contract differs; do not overwrite")
            if not private_path.is_file():
                raise ValueError("prepared public case lacks its private counterpart")
            private=read_json(private_path)
            if (private.get('opaque_incident_id'),private.get('dataset'),private.get('case_id')) != (
                    opaque,row['dataset'],row['case_id']):
                raise ValueError('prepared private identity mismatch')
            if pools_only:
                audit_public_pool(payload['pool'])
                if (stable_hash(payload['pool'])!=payload['pool_hash'] or pool_contract(config)!=contract
                        or payload.get('private_sha256')!=sha_file(private_path)):
                    raise ValueError('pool content/compiler changed')
            else:audit_catalog(payload, config)
        else:
            print(f"[prepare] {partition} {opaque} starting", flush=True)
            prior=(reuse or {}).get(opaque)
            if prior:
                old=read_json(prior['public']);private=read_json(prior['private'])
                audit_public_pool(old['pool'])
                if old['split_hash']!=split_hash:raise ValueError('source pool partition changed')
                if 'catalog_audit' in old:audit_catalog_inventory(old)
                elif not preparation_identity_matches(old.get('pool_contract'),pool_contract(config),'pool') or old['pool_hash']!=stable_hash(old['pool']):
                    raise ValueError('source pool is not current/complete')
                pool=old['pool']
                if private['opaque_incident_id']!=opaque or private['dataset']!=row['dataset'] or private['case_id']!=row['case_id']:
                    raise ValueError('source pool private identity mismatch')
                provenance={'reused_public':prior['public'],'pool_hash':stable_hash(pool)}
            else:
                pool, private = build_pool(row["dataset"],row["case_id"],opaque,config)
                provenance={'compiled_from':'canonical_v3_public_case'}
            if pools_only:
                if pool_contract(config)!=contract:raise ValueError('pool compiler changed while running')
                payload={'pool':pool,'pool_hash':stable_hash(pool),'pool_contract':contract,
                         'split_hash':split_hash,'provenance':provenance}
            else:payload = materialize_catalog(pool, config, split_hash, contract)
            write_json(private_path,private)
            if pools_only:payload['private_sha256']=sha_file(private_path)
            write_json(target,payload)
        index.append({"opaque_incident_id":opaque,"public":str(target.relative_to(output)),"private":f"private/{opaque}.json"})
        detail=(f"{len(payload['pool']['facts'])} complete-pool facts" if pools_only else
                f"{len(payload['observation']['cards'])}/{len(payload['cards'])} directory/pool cards")
        print(f"[prepare] {partition} {opaque} complete: {detail}",flush=True)
    return index


def prepare(config, output, partition="validation", count=2, workers=2, pools_only=False, reuse_sources=(), cohort=None):
    from .gates import audit_split, parent_integrity
    from concurrent.futures import ProcessPoolExecutor, as_completed
    import multiprocessing as mp
    if partition not in {"train","validation","eval","tournament"} or count < 0 or workers not in range(1,9):
        raise ValueError("preparation requires a permitted partition/count/worker setting")
    parent_integrity()
    split = RQ3SegmentationAdapter(config).build()
    audit_split(split)
    from .utils import pool_contract
    contract = pool_contract(config) if pools_only else catalogue_contract(config)
    private_root = output / "private"
    split_path = private_root / "split.json"
    if split_path.exists() and read_json(split_path).get("split_hash") != split["split_hash"]:
        raise ValueError("prepared root belongs to a different split; preserve it and choose a successor root")
    if (output / "index.json").exists():
        old_index=read_json(output / "index.json")
        if old_index["partition"] != partition or old_index.get('layout','catalogue') != (
                'full_pool' if pools_only else 'catalogue'):
            raise ValueError("prepared root belongs to a different partition/layout")
    write_json(private_root / "split.json", split)
    from .utils import partition_rows
    if partition in ('eval','tournament') and count:raise ValueError('eval/tournament preparation must retain all 480 cases')
    if partition=='tournament' and not pools_only:raise ValueError('tournament preparation is CPU full-pool only')
    rows = sorted(partition_rows(config,split,partition), key=lambda r: stable_hash([config["seed"], r["opaque_incident_id"]]))
    if cohort is not None:
        requested=read_json(cohort);ids=[r['opaque_incident_id'] for r in requested['cases']]
        if partition!='train' or requested['split_hash']!=split['split_hash'] or len(ids)!=len(set(ids)) or not set(ids)<={r['opaque_incident_id'] for r in rows}:raise ValueError('cohort is not a unique current training subset')
        if count!=len(ids):raise ValueError('explicit cohort count must retain every registered case')
        rows=[r for r in rows if r['opaque_incident_id'] in ids]
    # AIOPS-only smoke selection, one case from each training dataset first.
    chosen = []
    for dataset in ("aiops2022","aiops2025"):
        row = next((r for r in rows if r["dataset"] == dataset), None)
        if row:
            chosen.append(row)
    chosen.extend(r for r in rows if r not in chosen)
    chosen = chosen[:count] if count else chosen
    reuse={}
    for source in reuse_sources:
        source=Path(source).resolve();old_index=read_json(source/'index.json')
        if old_index['partition']!=partition or old_index['split_hash']!=split['split_hash']:
            raise ValueError('pool reuse source is not the same registered partition')
        for row in old_index['cases']:
            if row['opaque_incident_id'] in reuse:raise ValueError('duplicate pool reuse identity')
            paths={key:str((source/row[key]).resolve()) for key in ('public','private')}
            if any(not Path(p).is_relative_to(source) for p in paths.values()):
                raise ValueError('pool reuse source path escape')
            reuse[row['opaque_incident_id']]=paths
    # Static process lanes never share a physical core, including SMT siblings.
    cores = physical_cpu_ids()
    workers = min(workers,len(chosen),len(cores))
    if not workers:
        raise ValueError("no eligible cases/cores")
    index = []
    with ProcessPoolExecutor(max_workers=workers,mp_context=mp.get_context("spawn")) as pool:
        futures = [pool.submit(_prepare_lane,config,str(output),partition,chosen[i::workers],
                              split["split_hash"],contract,cores[i],pools_only,reuse) for i in range(workers)]
        for future in as_completed(futures):
            index.extend(future.result())
    by_id = {r["opaque_incident_id"]:r for r in index}
    index = [by_id[r["opaque_incident_id"]] for r in chosen]
    write_json(output / "index.json",{"partition":partition,"cases":index,"split_hash":split["split_hash"],
                                      "workers":workers,"physical_cpus":cores[:workers],
                                      "layout":"full_pool" if pools_only else "catalogue"})


def materialize_catalog(pool, config, split_hash, contract=None):
    from .exps import evidence_cards, build_catalog
    from .gates import audit_catalog
    cards = evidence_cards(pool, config)
    obs, audit = build_catalog(pool, cards, config)
    payload = {"pool": pool, "cards": [asdict(c) for c in cards], "observation": asdict(obs),
               "catalog_audit": audit, "catalog_contract": contract or catalogue_contract(config),
               "config_hash": stable_hash(config), "split_hash": split_hash}
    audit_catalog(payload, config)
    return payload


def prepare_fixed_baselines(config, prepared, output):
    """Parent controls on an authorized partition; eval requires frozen policies."""
    from .exps import build_fixed_baseline, fixed_baseline_parts, CaseRenderView
    from .gates import audit_split, audit_fixed_baseline, audit_public_pool, parent_integrity
    from .utils import sha_file,partition_rows
    from vlmrca.processed import load_processed_case
    from dataclasses import replace
    parent_integrity()
    index = read_json(prepared/"index.json")
    split = RQ3SegmentationAdapter(config).build(); audit_split(split)
    if index["split_hash"] != split["split_hash"]:
        raise ValueError("baseline preparation requires the current isolated split")
    allowed = {r["opaque_incident_id"]:r for r in partition_rows(config,split,index['partition'])}
    if prepared.resolve() == output.resolve():
        raise ValueError("fixed baselines cannot overwrite Composer preparation")
    rows = []
    for row in index["cases"]:
        opaque = row["opaque_incident_id"]
        identity = allowed[opaque]
        source = read_json(prepared/row["public"])
        audit_public_pool(source["pool"])
        if source["pool"]["opaque_incident_id"] != opaque:
            raise ValueError("baseline source case identity mismatch")
        target = output/"public"/f"{opaque}.json"
        image_path = output/"renders"/f"{opaque}_parent.png"
        if target.exists():
            baseline = read_json(target); png = image_path.read_bytes()
            if baseline["split_hash"] != split["split_hash"] or baseline["seed"] != config["seed"]:
                raise ValueError("fixed baseline registration changed; preserve prior artifact")
        else:
            view = replace(CaseRenderView.from_case(load_processed_case(identity["dataset"],identity["case_id"])),case_id=opaque)
            packet,png,manifest = build_fixed_baseline(view,config)
            baseline = {"packet":packet,"manifest":manifest,"split_hash":split["split_hash"],"seed":config["seed"]}
            atomic_write(image_path,png)
            write_json(target,baseline)
        packet,manifest = baseline["packet"],baseline["manifest"]
        audit = audit_fixed_baseline(packet,png,manifest)
        if packet["candidates"] != source["pool"]["candidates"]:
            raise ValueError("strong baseline and learned pool candidate universe/order differ")
        private = read_json(prepared/row["private"])
        if sorted(private["numeric_to_natural"]) != packet["candidates"]:
            raise ValueError("baseline candidate mapping differs from shared private evaluator")
        atomic_write(output/row["private"],(prepared/row["private"]).read_bytes())
        arms = {}
        for arm in ("T_FIXED","C_FIXED","TPV_FIXED"):
            parts = fixed_baseline_parts(packet,png,manifest,arm)
            stored = []; images = []
            for i,part in enumerate(parts):
                part = dict(part)
                if "png" in part:
                    value = part.pop("png"); path = output/"renders"/f"{opaque}_{arm}_{i}.png"
                    atomic_write(path,value); images.append(str(path.relative_to(output)))
                    part.update(image_path=str(path.relative_to(output)),image_sha256=sha_file(path))
                stored.append(part)
            path = output/"prompts"/f"{opaque}_{arm}.json"
            write_json(path,{"parts":stored,"fact_inventory_hash":packet["fact_inventory_hash"],
                             "uses_smoke_harness":False,"images":images})
            arms[arm] = {"path":str(path.relative_to(output)),"sha256":sha_file(path)}
        rows.append({**row,"arms":arms,"audit":audit,"public_sha256":sha_file(target),
                     "parent_image_sha256":sha_file(image_path),"private_sha256":sha_file(output/row["private"])})
        print(f"[fixed] {opaque}: {len(packet['facts'])} facts, {len(packet['candidates'])} candidates; T/C/TPV ready",flush=True)
    write_json(output/"index.json",{"schema_version":"RQ3FixedBaselineIndexV1","partition":index["partition"],
                                    "split_hash":split["split_hash"],"cases":rows,"model_calls":0})


def refresh_catalog(config, prepared, output):
    """Reuse immutable compiled pools; no raw processing or model call."""
    from .gates import audit_catalog, parent_integrity, audit_split
    parent_integrity()
    if prepared.resolve() == output.resolve():
        raise ValueError("catalogue successor must not overwrite its source")
    index = read_json(prepared / "index.json")
    partition = index["partition"]
    split = RQ3SegmentationAdapter(config).build(); audit_split(split)
    from .utils import partition_rows
    eligible = {r["opaque_incident_id"] for r in partition_rows(config,split,partition)}
    if index["split_hash"] != split["split_hash"] or any(r["opaque_incident_id"] not in eligible for r in index["cases"]):
        raise ValueError("prepared source is not the isolated RQ3 partition")
    contract = catalogue_contract(config)
    rows = []
    for row in index["cases"]:
        source = read_json(prepared / row["public"])
        target = output / row["public"]
        source_hash = stable_hash(source["pool"])
        if target.exists():
            payload = read_json(target)
            if not preparation_identity_matches(payload.get("catalog_contract"),contract,'catalogue') or stable_hash(payload["pool"]) != source_hash:
                raise ValueError("catalogue successor differs; choose a new output, never overwrite")
            audit_catalog(payload, config)
        else:
            payload = materialize_catalog(source["pool"], config, split["split_hash"], contract)
            if stable_hash(payload["pool"]) != source_hash:
                raise ValueError("directory optimization changed the evidence pool")
            # Preserve physical label isolation and source bytes.
            atomic_write(output / row["private"], (prepared / row["private"]).read_bytes())
            write_json(target, payload)
        audit = payload["catalog_audit"]
        rows.append(row)
        print(f"[catalog] {row['opaque_incident_id']}: {audit['input_tokens']}/{audit['input_budget']} input tokens; "
              f"{len(payload['observation']['cards'])}/{len(payload['cards'])} cards", flush=True)
    write_json(output / "private/split.json", split)
    write_json(output / "index.json", {**index, "cases": rows, "layout":"catalogue", "catalog_contract": contract})


def hydrate(payload, *, available_only=True):
    from .exps import EvidenceCardV1
    cards = []
    for source in payload["cards"]:
        value = dict(source)
        for k in ("fact_ids","entity_ids","allowed_encodings"):
            value[k] = tuple(value[k])
        value["footprint_options"] = tuple(tuple(x) for x in value["footprint_options"])
        cards.append(EvidenceCardV1(**value))
    if available_only:
        from .gates import audit_catalog_inventory
        audit_catalog_inventory(payload)
        allowed = {row["card_id"] for row in payload["observation"]["cards"]}
        cards = [card for card in cards if card.card_id in allowed]
    return payload["pool"],tuple(cards)


def format_examples(config, prepared, output, *, qualification=False, workers=4):
    """Materialize deterministic legal teacher-forcing targets from train only."""
    from .gates import audit_split
    from concurrent.futures import ProcessPoolExecutor,as_completed
    import multiprocessing as mp
    split = RQ3SegmentationAdapter(config).build(); audit_split(split)
    index = read_json(prepared / "index.json")
    if index["partition"] != "train" or index["split_hash"] != split["split_hash"]:
        raise ValueError("SFT examples require the current isolated training preparation")
    members = {r["opaque_incident_id"]:r for r in split["train"]}
    if qualification and (len(index["cases"]) != 2 or
         {members[r["opaque_incident_id"]]["dataset"] for r in index["cases"]} != {"aiops2022","aiops2025"}):
        raise ValueError("optimizer qualification needs exactly two AIOPS train cases")
    if not qualification and {r["opaque_incident_id"] for r in index["cases"]} != set(members):
        raise ValueError("formal SFT examples must cover the complete registered training set")
    if workers not in range(1,9):raise ValueError('format workers must be between one and eight')
    stop=output/'format_stop_requested'
    if stop.exists():stop.unlink()  # owned runtime flag, never an example/result
    cores=[];seen=set()
    for cpu in sorted(os.sched_getaffinity(0)):
        folder=Path(f'/sys/devices/system/cpu/cpu{cpu}/topology')
        pair=tuple((folder/name).read_text().strip() for name in ('physical_package_id','core_id'))
        if pair not in seen:seen.add(pair);cores.append(cpu)
    workers=min(workers,len(index['cases']),len(cores));collected={};file_map={}
    def collect(result):
        rows,files=result
        for row in rows:collected.setdefault(row['opaque_incident_id'],[]).append(row)
        file_map.update({r['path']:r for r in files})
    if workers==1:
        affinity=os.sched_getaffinity(0)
        try:collect(_format_lane(config,prepared,output,index['cases'],members,split['split_hash'],qualification,cores[0]))
        finally:os.sched_setaffinity(0,affinity)
    else:
        with ProcessPoolExecutor(max_workers=workers,mp_context=mp.get_context('spawn')) as pool:
            futures=[pool.submit(_format_lane,config,prepared,output,index['cases'][i::workers],members,
                                 split['split_hash'],qualification,cores[i]) for i in range(workers)]
            for future in as_completed(futures):
                try:collect(future.result())
                except BaseException as exc:
                    atomic_write(stop,b'worker failure; preserve committed examples\n')
                    print(f'[format failure] {type(exc).__name__}: {exc}',flush=True)
                    raise
    rows=[e for row in index['cases'] for e in collected[row['opaque_incident_id']]]
    files=[file_map[f"private/{row['opaque_incident_id']}.json"] for row in index['cases']]
    write_json(output / "index.json",{"split_hash":split["split_hash"],"qualification_only":qualification,
                                     "cases":len(index["cases"]),"examples":len(rows),"examples_hash":stable_hash(rows),"files":files})
    return rows


def _format_lane(config,prepared,output,cases,members,split_hash,qualification,cpu):
    from .exps import legal_sft_examples
    from .gates import audit_catalog,audit_training_rows
    os.sched_setaffinity(0,{cpu});rows=[];files=[]
    for row in cases:
        if (output/'format_stop_requested').exists():break
        identity = members[row["opaque_incident_id"]]
        payload = read_json(prepared / row["public"]); audit_catalog(payload,config)
        contract = stable_hash([payload["catalog_contract"],split_hash,config["sft"],qualification])
        path = output / "private" / f"{row['opaque_incident_id']}.json"
        if path.exists():
            saved = read_json(path)
            if saved["contract"] != contract or saved["examples_hash"] != stable_hash(saved["examples"]):
                raise ValueError("format examples changed or incomplete; do not overwrite")
            examples = saved["examples"]
        else:
            # Example construction rebuilds the identical catalogue, then
            # samples only advertised cards. Its source must be the full pool,
            # not the already-filtered shortlist returned by ordinary hydrate.
            pool,cards = hydrate(payload,available_only=False)
            seed = int(stable_hash([config["seed"],row["opaque_incident_id"]])[:16],16)
            examples = legal_sft_examples(pool,cards,config,seed,limit=1 if qualification else None)
            examples = [{**example,"dataset":identity["dataset"],"case_id":identity["case_id"],
                         "partition":"train","opaque_incident_id":row["opaque_incident_id"]} for example in examples]
            write_json(path,{"contract":contract,"examples":examples,"examples_hash":stable_hash(examples)})
        audit_training_rows(config,examples)
        rows.extend(examples)
        from .utils import sha_file
        files.append({"path":str(path.relative_to(output)),"sha256":sha_file(path)})
        print(f"[format] {row['opaque_incident_id']} examples={len(examples)}",flush=True)
    return rows,files


def composer_adapter(config):
    """Bind a rollout to verified checkpoint bytes, not an arbitrary version tag."""
    from .utils import sha_file
    spec = config.get("composer_active_adapter")
    if not spec:
        return None
    if set(spec) != {"checkpoint", "name"}:
        raise ValueError("unexpected Composer adapter fields")
    name = spec["name"]
    if not name or name == "BASE" or not all(c.isalnum() or c in "_-" for c in name):
        raise ValueError("invalid Composer adapter name")
    checkpoint = (ROOT / spec["checkpoint"]).resolve()
    if not checkpoint.is_relative_to((ROOT / "RQs/RQ3/results").resolve()):
        raise ValueError("Composer adapter must be an RQ3-owned checkpoint")
    state = read_json(checkpoint / "checkpoint.json")
    if state.get("complete") is not True:
        raise ValueError("uncommitted Composer checkpoint")
    relative_files = ("policy/adapter_config.json", "policy/adapter_model.safetensors")
    hashes = {}
    for relative in relative_files:
        path = checkpoint / relative
        digest = sha_file(path)
        if digest != state["files"].get(relative):
            raise ValueError("Composer adapter checkpoint hash mismatch")
        hashes[relative] = digest
    adapter_config = read_json(checkpoint / relative_files[0])
    if adapter_config.get("r") != config["sft"]["lora_rank"] or adapter_config.get("lora_alpha") != config["sft"]["lora_alpha"]:
        raise ValueError("Composer LoRA recipe mismatch")
    return {"name":name,"path":str(checkpoint / "policy"),"files":hashes,
            "checkpoint_state_hash":stable_hash(state)}


def composer_recipe(config):
    source = config["composer"]
    tag = "rq3-composer-9b"
    adapter = {"models":{tag:{
        "model_path":source["model_path"],"model_path_env":source["model_path_env"],
        "served_model_name":source["served_model_name"],"max_model_len":source["max_model_len"],
        "max_tokens":source["max_tokens"], "temperature":1.,"top_p":1.,
        "mm_processor_kwargs":None,"enable_chunked_prefill":True,
        "default_chat_template_kwargs":{"enable_thinking":False},
        "structured_outputs_config":None,
        "extra_server_args":["--return-tokens-as-token-ids"],
    }}}
    active = composer_adapter(config)
    if active:
        import json
        adapter["models"][tag]["extra_server_args"].extend([
            "--enable-lora", "--max-lora-rank", str(config["sft"]["lora_rank"]),
            "--lora-modules", json.dumps({"name":active["name"],"path":active["path"],
                 "base_model_name":source["served_model_name"]},sort_keys=True)])
    return VLLMInferenceConfig.load(config["unified"]["inference"],adapter=adapter), tag


def request(config, ledger, key, parts, role, output, seed=42, policy_version="BASE", *, retry=False, reuse=None):
    """One counted request; never hide retries inside the unified client."""
    import json, re
    from vlmrca.vlm.configs import VLMConfig, get_config
    from .exps import COMPOSER_SYSTEM, rca_schema, composer_parts, decode_candidate_ids
    from .gates import audit_call_artifacts
    from .utils import sha_file, AsyncWriter
    from urllib.parse import urlparse
    os.environ["CANVASRCA_SDK_MAX_RETRIES"] = "0"
    endpoint = os.environ.get("VLLM_BASE_URL", "http://127.0.0.1:8000/v1")
    if urlparse(endpoint).hostname not in {"127.0.0.1", "localhost", "::1"}:
        raise ValueError("RQ3 is local-only; remote endpoints are forbidden")
    if role not in {"composer", "solver"}:
        raise ValueError("unknown model role")
    attention_enabled = role == "solver" and config["solver"].get("attention") != "off"
    if role == "solver" and not attention_enabled and os.environ.get("CANVASRCA_ATTENTION_PROBE") != "0":
        raise ValueError("attention-off protocol requires a disabled client and server hook")
    if not key or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-" for c in key):
        raise ValueError("unsafe call key")
    if role == "composer":
        recipe, tag = composer_recipe(config)
        active_adapter = composer_adapter(config)
        expected_version = active_adapter["name"] if active_adapter else "BASE"
        if policy_version != expected_version:
            raise ValueError("Composer policy version is not the active verified adapter")
        cfg = VLMConfig(tag=tag,backend="openai",model_id=active_adapter["name"] if active_adapter else config["composer"]["served_model_name"],
                        max_tokens=config["composer"]["max_tokens"],temperature=1.,top_p=1.,seed=seed,
                        thinking=False,thinking_via_template=True,base_url_env="VLLM_BASE_URL",api_key_env="VLLM_API_KEY",
                        request_timeout_s=1800,extra={"logprobs":True,"extra_body":{"top_k":-1,"min_p":0.}})
        system, schema = COMPOSER_SYSTEM, None
        if len(parts) != 1 or parts[0].get("type") != "text":
            raise ValueError("Composer accepts the one budgeted observation, not arbitrary telemetry")
        observed = json.loads(parts[0]["text"])
        if composer_parts(observed) != parts:
            raise ValueError("Composer input bypasses the canonical catalogue serializer")
        from vlmrca.vlm.client import _openai_messages
        from .gates import validate_composer_input
        prompt_ids = validate_composer_input(_openai_messages(parts, system), config)
    else:
        tag=config['solver'].get('model_tag','qwen3.8-27b')
        if tag!='qwen3.8-27b' and tag not in config.get('tournament',{}).get('models',[]):raise ValueError('unregistered Solver')
        cfg = get_config(tag,max_tokens=8192)
        request_profile=config['solver'].get('request_profile','legacy_v1')
        if tag!='qwen3.8-27b' and request_profile!='legacy_v1':raise ValueError('Qwen adapter cannot change Gemma sampling')
        if request_profile in ('card_nonthinking_v1','card_thinking_low_v1','card_nonthinking_reason_first_v1','card_nonthinking_unpenalized_v1') and config.get('search',{}).get('enabled'):
            # Explicit RQ3 request adapter, not a change to the unified base recipe.
            thinking=request_profile=='card_thinking_low_v1'
            if cfg.thinking!=thinking:raise ValueError('request profile and selected server thinking mode disagree')
            cfg.extra={'temperature':1. if thinking else .7,'top_p':.95 if thinking else .8,'presence_penalty':0. if thinking or request_profile=='card_nonthinking_unpenalized_v1' else 1.5,
                       'extra_body':{'top_k':20,'min_p':0.,'repetition_penalty':1.}}
            if thinking:cfg.extra['extra_body']['chat_template_kwargs']={'enable_thinking':True,'preserve_thinking':False,'reasoning_effort':'low'}
        elif request_profile!='legacy_v1':raise ValueError('unknown/unauthorized RQ3 request profile')
        recipe = VLLMInferenceConfig.load(config["unified"]["inference"])
        system, schema = "You are an expert Site Reliability Engineer.", rca_schema()
        frozen_template=config['solver'].get('prompt_template')=='rq21_visual_structure_v1'
        if frozen_template:
            from .exps import validate_tournament_parts
            system,candidates=validate_tournament_parts(parts)
        binding=config['solver'].get('candidate_binding','legacy_v1')
        if binding=='enum_top5_v1' and config.get('search',{}).get('enabled'):
            if not frozen_template:candidates=decode_candidate_ids(parts[1]['text'])
            services=schema['json_schema']['schema']['properties']['services']
            services.update(minItems=min(5,len(candidates)),maxItems=min(5,len(candidates)),items={'type':'string','enum':candidates})
        elif binding!='legacy_v1':raise ValueError('unknown/unauthorized candidate binding')
        if request_profile=='card_nonthinking_reason_first_v1':
            ordered=schema['json_schema']['schema'];order=['reason','services','confidence']
            if set(ordered['properties'])!=set(order):raise ValueError('reason-first schema fields changed')
            ordered['properties']={k:ordered['properties'][k] for k in order};ordered['required']=order
    from vlmrca.run_state import persisted_model_call
    from .utils import archive_response_attention, archive_derived_attention
    prompt_ids = prompt_ids if role == "composer" else None
    envelope = {"system":system,"model":asdict(cfg),"schema":schema,"policy_version":policy_version,
        "effective_server": recipe.model(tag), "runtime_config_hash": recipe.source_sha256}
    if role=='solver' and cfg.extra:
        envelope['request_adapter']={'name':request_profile,'effective_sampling':{
            'temperature':cfg.extra['temperature'],'top_p':cfg.extra['top_p'],'seed':cfg.seed,
            'presence_penalty':cfg.extra['presence_penalty'],**cfg.extra['extra_body']}}
    if role == "composer" and active_adapter:
        envelope["composer_adapter"] = active_adapter
    if role == "solver" and not attention_enabled: envelope["diagnostic_projection"] = "rq3_attention_off_v1"
    if reuse is not None:
        if role!='solver' or config.get('search',{}).get('stage')!='tournament' or retry:
            raise ValueError('exact request reuse is tournament-only, not a retry')
        from .utils import reuse_tournament_call
        return reuse_tournament_call(reuse,parts,envelope,output)
    def complete_record(record,response):
        files=[];artifact_key=record['artifact_key']
        if role == "composer":
            tokens = (response.raw or {}).get("sampled_logprobs",[])
            if any(not x["token"].startswith("token_id:") for x in tokens):
                raise ValueError("server did not return actual sampled token IDs")
            record["completion_ids"] = [int(x["token"].removeprefix("token_id:")) for x in tokens]
            record["sampled_logprobs"] = [float(x["logprob"]) for x in tokens]
            record["sampling"] = {"temperature":1.,"top_p":1.,"top_k":-1,"min_p":0.,"grammar":None}
            record["prompt_ids"] = prompt_ids
            from .gates import validate_rollout_probability
            validate_rollout_probability(record,policy_version)
        elif attention_enabled:
            from RQs.RQ2_1.src.utils import persist_attention
            summary, attention_files = persist_attention((response.raw or {}).get("attention_probe"),
                parts, system, tag, recipe, output / "attention" / artifact_key, response_text=response.text)
            record["attention"] = summary
            files.extend(archive_derived_attention(attention_files))
        if role == "solver" and not attention_enabled: record["attention"] = {"status": "disabled_by_protocol"}
        return files
    return persisted_model_call(cfg,parts,envelope,ledger,key,role,output,retry=retry,
        prompt_ids=prompt_ids,writer_factory=AsyncWriter,artifact_audit=audit_call_artifacts,
        raw_processor=archive_response_attention if attention_enabled else lambda raw,*_: (raw,[]),
        record_hook=complete_record)


def search_worker(config, source, output):
    """Bounded, pre-rendered train-case search; no training/eval lifecycle."""
    from unified_scripts.rca_scorer import score_bound_response
    from concurrent.futures import ThreadPoolExecutor
    from .utils import CallLedger, sha_file
    from .gates import audit_call_artifacts
    from .exps import rca_schema, decode_candidate_ids, validate_tournament_parts
    spec=read_json(source);output=Path(output).resolve()
    tournament=config.get('search',{}).get('stage')=='tournament'
    owner=ROOT/'RQs/RQ3/results'/('tournament_v1' if tournament else 'search_first_v1')
    if not output.is_relative_to(owner):raise ValueError('search output outside successor')
    if not config.get('search',{}).get('enabled') or config['solver']['attention']!='off':
        raise PermissionError('search requires explicit authorization and attention off')
    if stable_hash({k:v for k,v in spec.items() if k!='spec_hash'})!=spec.get('spec_hash'):
        raise ValueError('search specification hash changed')
    if spec['config_hash']!=stable_hash(config) or spec['review_status']!='passed':raise ValueError('unreviewed search')
    split=RQ3SegmentationAdapter(config).build();members={r['opaque_incident_id'] for r in split['train']}
    model=spec.get('model_tag','qwen3.8-27b')
    if tournament:
        from .utils import tournament_register
        r=tournament_register(config).rounds()[-1]
        if r['hash']!=spec.get('tournament_round_hash') or r['method']['config_hash']!=stable_hash(config):raise ValueError('unregistered tournament round')
        members=set(r['cohorts'][model])
        if len(spec['tasks'])!=len(members) or {t['case'] for t in spec['tasks']}!=members:raise ValueError('tournament batch does not cover its registered cohort')
    if not 1<=len(spec['tasks'])<=config['search']['max_batch_calls'] or any(t['case'] not in members for t in spec['tasks']):
        raise ValueError('search exceeds registered train population/batch bound')
    if len({(t['case'],t['variant']) for t in spec['tasks']})!=len(spec['tasks']):raise ValueError('duplicate search target')
    if any(t[k] not in spec['artifact_hashes'] for t in spec['tasks'] for k in ('parts','private')):raise ValueError('unhashed search input')
    for relative,digest in spec['artifact_hashes'].items():
        if sha_file(ROOT/relative)!=digest:raise ValueError('search input artifact changed')
    ledger=CallLedger(output.parent/'search_calls.sqlite',None,scope=output.name,scope_limit=None if tournament else config['search']['max_batch_calls'])
    scorer=rca_scorer(config)
    def run(task):
        key=stable_hash([spec['batch_id'],{k:v for k,v in task.items() if k!='retry'}]);parts=[]
        for source_part in read_json(ROOT/task['parts']):
            p=dict(source_part)
            if 'image_path' in p:
                if p['image_path'] not in spec['artifact_hashes']:raise ValueError('unhashed search PNG')
                p['png']=(ROOT/p.pop('image_path')).read_bytes()
            parts.append(p)
        if sum('png' in p for p in parts)!=1:raise ValueError('search requires exactly one image')
        if config['solver'].get('prompt_template')=='rq21_visual_structure_v1':
            _,bound_candidates=validate_tournament_parts(parts)
        else:
            bound_candidates=decode_candidate_ids(parts[1]['text'])
        if bound_candidates!=task['candidates']:raise ValueError('prompt/candidate binding mismatch')
        profile=config.get('tournament',{}).get('model_request_profiles',{}).get(model,task.get('request_profile','legacy_v1'))
        task_config={**config,'solver':{**config['solver'],'model_tag':model,'request_profile':profile}}
        record=request(task_config,ledger,key,parts,'solver',output,seed=config['seed'],retry=task.get('retry',False),reuse=task.get('reuse'))
        audit_call_artifacts(record,output);private=read_json(ROOT/task['private'])
        if private['opaque_incident_id']!=task['case']:raise ValueError('private case identity mismatch')
        scored=score_bound_response(record['response'],task['candidates'],private['numeric_to_natural'],private['accepted'],rca_schema()['json_schema']['schema'],scorer)
        row={'task':task,'record_hash':record['record_hash'],'record_path':f"trajectories/{record['artifact_key']}.json",
             **scored,
             'input_tokens':record['input_tokens'],'output_tokens':record['output_tokens']}
        if task.get('reuse'):row.update(reused_from=task['reuse'],new_model_calls=0)
        write_json(output/'outcomes'/f'{key}.json',row)
        print(task['case'],task['variant'],row['status'],flush=True);return row
    with ThreadPoolExecutor(max_workers=config['search']['concurrency']) as executor:rows=list(executor.map(run,spec['tasks']))
    write_json(output/'summary.json',{'status':'complete','spec_hash':spec['spec_hash'],'outcomes':rows,'accounting':ledger.summary()})


def preview(config, prepared, output):
    raise PermissionError("Completed predecessor qualification is archived; use the search-first route")


def smoke_worker(*args,**kwargs): return preview(None,None,None)


def qualification_reference(path, payload, config):
    """Explicit reuse of an actual BASE program, only to exercise interventions."""
    from .exps import parse_program, composer_parts, COMPOSER_SYSTEM
    from .gates import audit_call_artifacts
    path = Path(path).resolve()
    if not path.is_relative_to((ROOT / 'RQs/RQ3/results').resolve()) or path.parent.name != 'programs':
        raise ValueError('qualification program must belong to an RQ3 result')
    result = read_json(path); root = path.parent.parent
    record = read_json(root / 'trajectories' / (result['call_key']+'.json'))
    envelope = read_json(root / 'prompts' / (result['call_key']+'.json'))
    audit_call_artifacts(record, root)
    if (result.get('status') != 'valid' or result['case'] != payload['pool']['opaque_incident_id'] or
        result['response_record_hash'] != record['record_hash'] or record['policy_version'] != 'BASE' or
        envelope['system'] != COMPOSER_SYSTEM or envelope['parts'] != composer_parts(payload['observation'])):
        raise ValueError('qualification reference is not the same isolated case/input and BASE policy')
    _, cards = hydrate(payload)
    program = parse_program(record['response'], cards, config)
    if asdict(program) != result['program']:
        # JSON stores the selection tuple as a list.
        if stable_hash(asdict(program)) != stable_hash(result['program']):
            raise ValueError('qualification reference program differs from its response')
    return result


def _formal_program_artifacts(config, prepared, response, output, key):
    """CPU process: validate one proposal, preserve its exact selected facts."""
    from .exps import execute_composer_program
    from .gates import audit_catalog_inventory, audit_public_pool
    from .utils import sha_file
    payload=read_json(prepared);audit_public_pool(payload['pool']);audit_catalog_inventory(payload)
    pool,cards=hydrate(payload)
    result,artifacts=execute_composer_program(response,pool,cards,config)
    if artifacts:
        packet,png,manifest=artifacts;output=Path(output);stem=Path('program_artifacts')/key
        paths={'packet':str(stem.with_suffix('.packet.json')),
               'image':str(stem.with_suffix('.png')),'manifest':str(stem.with_suffix('.manifest.json'))}
        write_json(output/paths['packet'],packet);atomic_write(output/paths['image'],png)
        write_json(output/paths['manifest'],manifest)
        result.update(render=paths,render_hashes={p:sha_file(output/p) for p in paths.values()})
    return result


def formal_worker(config, source, output):
    # One model phase with concurrent requests and separate CPU renderers.
    # Only the exclusive supervisor reconciles interrupted requests. Invalid
    # proposals remain failures; this worker never substitutes a good design.
    import json
    import multiprocessing as mp
    import jsonschema
    from concurrent.futures import ThreadPoolExecutor,ProcessPoolExecutor,as_completed
    from .utils import CallLedger,sha_file,registered_schedule,formal_phase_plan,verify_work_spec
    from .gates import assert_formal_authorized,audit_catalog,audit_call_artifacts
    from .exps import composer_parts,rca_schema
    assert_formal_authorized(config)
    output=Path(output).resolve();split=RQ3SegmentationAdapter(config).build()
    spec=read_json(source)
    entries=verify_work_spec(spec,split,registered_schedule(split,config),formal_phase_plan(split,config),output)
    role=spec['role'];policy=(composer_adapter(config) or {}).get('name','BASE')
    if role=='composer' and policy!=spec['policy_version']:raise ValueError('phase checkpoint differs from active adapter')
    recipe,tag=(composer_recipe(config) if role=='composer' else
                (VLLMInferenceConfig.load(config['unified']['inference']),'qwen3.8-27b'))
    active=composer_adapter(config) if role=='composer' else None
    if role=='composer':
        from .utils import composer_tokenizer
        composer_tokenizer(config)  # Initialize lazy imports/cache before request threads race.
    request_projection={'server':recipe.model(tag),'output_limit':config['composer']['max_tokens'] if role=='composer' else 8192,
                        'adapter':{'name':active['name'],'files':active['files']} if active else None}
    ledger=CallLedger(ROOT/'RQs/RQ3/results/calls.sqlite',config['budget']['hard_limit'],scope=output.name)
    scorer=rca_scorer(config) if role=='solver' else None;retries=set(spec.get('reconciled_retry_keys',[]))
    def load_part(part):
        part=dict(part)
        if 'image_path' in part:
            path=(ROOT/part.pop('image_path')).resolve()
            if sha_file(path)!=part.pop('image_sha256'):raise ValueError('formal image changed')
            part['png']=path.read_bytes()
        return part
    def persist(row,path):
        row['outcome_hash']=stable_hash(row);write_json(path,row);return row
    def execute(entry,cpu_pool):
        task=entry['task'];key=task['call_key'];path=output/'outcomes'/f'{key}.json'
        dependencies={p:spec['artifact_hashes'][p] for p in
                      (entry.get('prepared_public'),entry.get('prepared_private'),entry.get('parts_path')) if p}
        if entry.get('parts_path'):
            for part in read_json(ROOT/entry['parts_path'])['parts']:
                if 'image_path' in part:dependencies[part['image_path']]=spec['artifact_hashes'][part['image_path']]
        binding=stable_hash([entry,dependencies,request_projection])
        if path.exists():
            old=read_json(path)
            if (old.get('outcome_hash')!=stable_hash({k:v for k,v in old.items() if k!='outcome_hash'})
                    or old['task']!=task or old['work_item_hash']!=binding):
                raise ValueError('formal outcome differs from committed input')
            if old.get('record_path'):audit_call_artifacts(read_json(output/old['record_path']),output)
            for p,digest in old.get('render_hashes',{}).items():
                if sha_file(output/p)!=digest:raise ValueError('completed program artifact changed')
            return old
        common={'task':task,'case':entry['case'],'work_item_hash':binding,
                'partition':spec['partition'],'phase_id':spec['phase_id']}
        if role=='composer':
            payload=read_json(ROOT/entry['prepared_public']);audit_catalog(payload,config)
            record=request(config,ledger,key,composer_parts(payload['observation']),role,output,
                           seed=entry['sampling_seed'],policy_version=policy,retry=key in retries)
            result=cpu_pool.submit(_formal_program_artifacts,config,str(ROOT/entry['prepared_public']),
                                   record['response'],str(output),key).result()
            common.update(result,observation_hash=stable_hash(payload['observation']))
        else:
            common['composer_record_hash']=entry.get('composer_record_hash')
            if entry.get('uncalled_status'):
                common.update(status=entry['uncalled_status'],record_path=None,record_hash=None,
                              error=entry.get('error'),metrics=scorer.score([],[]).as_dict(),input_tokens=0,output_tokens=0)
                return persist(common,path)
            bundle=read_json(ROOT/entry['parts_path']);parts=[load_part(p) for p in bundle['parts']]
            try:
                record=request(config,ledger,key,parts,role,output,seed=entry['sampling_seed'],retry=key in retries)
            except ValueError as exc:
                if not str(exc).startswith('input exceeds context:'):raise
                common.update(status='design_infeasible',failure_stage='context',record_path=None,
                              record_hash=None,error=str(exc),metrics=scorer.score([],[]).as_dict(),input_tokens=0,output_tokens=0)
                return persist(common,path)
            private=read_json(ROOT/entry['prepared_private']);parsed=None;predictions=[];error=None
            try:
                parsed=json.loads(record['response']);jsonschema.validate(parsed,rca_schema()['json_schema']['schema'])
                ids=parsed['services']
                if len(ids)!=len(set(ids)) or any(x not in bundle['candidates'] for x in ids):
                    raise ValueError('unknown/duplicate candidate')
                predictions=[private['numeric_to_natural'][x] for x in ids]
            except (ValueError,KeyError,jsonschema.ValidationError) as exc:error=str(exc)
            common.update(status='model_failure' if error else 'complete',parsed=parsed,parse_error=error,
                          metrics=scorer.score(predictions,private['accepted']).as_dict(),
                          fact_inventory_hash=bundle['fact_inventory_hash'])
        common.update(record_path=f"trajectories/{record['artifact_key']}.json",record_hash=record['record_hash'],
                      input_tokens=record['input_tokens'],output_tokens=record['output_tokens'])
        return persist(common,path)
    context=mp.get_context('spawn');core_queue=context.Queue();cores=physical_cpu_ids()
    if len(cores)<4:raise RuntimeError('formal rendering requires four available physical cores')
    for core in cores[:4]:core_queue.put(core)
    with ProcessPoolExecutor(max_workers=4,mp_context=context,initializer=_pin_render_worker,
                             initargs=(core_queue,)) as cpu_pool:
        with ThreadPoolExecutor(max_workers=36) as requests:
            pending={};iterator=iter(entries);done=0;outcomes=[]
            def refill():
                while len(pending)<36:
                    entry=next(iterator,None)
                    if entry is None:return
                    pending[requests.submit(execute,entry,cpu_pool)]=entry
            refill()
            try:
                while pending:
                    future=next(as_completed(pending));entry=pending.pop(future)
                    row=future.result();done+=1;outcomes.append(row['task']['call_key'])
                    print(f"[formal] {spec['phase_id']} {done}/{len(entries)} {entry['case']} {row['status']}",flush=True)
                    refill()
            except BaseException:
                for future in pending:future.cancel()
                raise
    write_json(output/'phase_results'/f"{spec['phase_id']}.json",{
        'status':'complete','phase_id':spec['phase_id'],'spec_hash':spec['spec_hash'],
        'outcomes':sorted(outcomes),'cases':len({r['case'] for r in entries})})


@owned_gpu_process
def run_model_phase(config, spec_path, output, *, _gpu_lease_fd):
    """Own one server/worker under supervisor lease; drain safely, never kill unrelated work or hide retries."""
    import socket
    import signal
    import subprocess
    import sys
    import time
    from urllib.parse import urlparse
    from .gates import assert_formal_authorized
    from .utils import CallLedger,sha_file
    assert_formal_authorized(config)
    output=Path(output).resolve();spec=read_json(spec_path);role=spec['role']
    split=RQ3SegmentationAdapter(config).build()
    from .utils import registered_schedule,formal_phase_plan,verify_work_spec
    verify_work_spec(spec,split,registered_schedule(split,config),formal_phase_plan(split,config),output)
    recipe,tag=(composer_recipe(config) if role=='composer' else
                (VLLMInferenceConfig.load(config['unified']['inference']),'qwen3.8-27b'))
    base_url=recipe.model(tag)['base_url'];address=urlparse(base_url)
    if address.hostname not in {'127.0.0.1','localhost'}:raise ValueError('nonlocal formal endpoint')
    with socket.socket() as probe:
        if probe.connect_ex((address.hostname,address.port or 80))==0:
            raise RuntimeError('formal endpoint already occupied; inspect its owner before recovery')
    from .utils import reconcile_phase_calls
    recovered,recovery=reconcile_phase_calls(config,spec,output)
    if recovered!=spec:
        spec=recovered;spec_path=output/'private/work_specs'/f"{spec['phase_id']}__resume_{spec['spec_hash'][:12]}.json"
        if spec_path.exists() and read_json(spec_path)!=spec:raise ValueError('recovery specification changed')
        if not spec_path.exists():write_json(spec_path,spec)
        write_json(output/'runtime'/f"{spec['phase_id']}__resume_{spec['spec_hash'][:12]}.json",recovery)
    logs=output/'logs';logs.mkdir(parents=True,exist_ok=True)
    cfg_path=output/'private'/'effective_configs'/f"{spec['phase_id']}.yaml"
    data=yaml.safe_dump(config,sort_keys=True).encode()
    if cfg_path.exists() and cfg_path.read_bytes()!=data:raise ValueError('formal phase configuration changed')
    if not cfg_path.exists():atomic_write(cfg_path,data)
    env={**os.environ,'RQ3_CONFIG_PATH':str(cfg_path),'CANVASRCA_STANDALONE':'1',
         'CANVASRCA_SDK_MAX_RETRIES':'0','VLLM_BASE_URL':base_url,'VLLM_API_KEY':'EMPTY',
         'CANVASRCA_VLLM_CONFIG':str(ROOT/config['unified']['inference']),
         'CANVASRCA_CACHE_ROOT':str(ROOT/'build/cache/rq3'),
         'CANVASRCA_ATTENTION_DIR':str(output/'sidecars'/spec['phase_id']),
         'CANVASRCA_ATTENTION_MODE':'on' if role=='solver' and config['solver'].get('attention')!='off' else 'off',
         'CANVASRCA_ATTENTION_PROBE':'1' if role=='solver' and config['solver'].get('attention')!='off' else '0',
         'CANVASRCA_ATTENTION_PROBE_REQUIRED':'1' if role=='solver' and config['solver'].get('attention')!='off' else '0'}
    command=(['bash','RQs/RQ3/scripts/serve_composer.sh'] if role=='composer' else
             ['bash','scripts/vllm_vlm/serve_canvasrca_local.sh','qwen3.8-27b'])
    server=worker=None;started=time.time()
    def stop(process):
        if process is None or process.poll() is not None:return
        try:os.killpg(process.pid,signal.SIGTERM)
        except ProcessLookupError:return
        try:process.wait(timeout=30)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid,signal.SIGKILL);process.wait(timeout=10)
    # Convert ordinary termination into cleanup; a reboot is reconciled from
    # the durable request/phase records, not from these operational PIDs.
    def terminate(*_):raise KeyboardInterrupt('formal model phase interrupted')
    previous=signal.signal(signal.SIGTERM,terminate)
    try:
        with (logs/f"{spec['phase_id']}.server.log").open('ab') as stream:
            server=subprocess.Popen(command,cwd=ROOT,env=env,stdout=stream,
                                    stderr=subprocess.STDOUT,start_new_session=True,pass_fds=(_gpu_lease_fd,))
        active=composer_adapter(config) if role=='composer' else None
        deadline=time.monotonic()+1800
        while not smoke_server_ready(base_url,'EMPTY',recipe.model(tag)['served_model_name'],
                                      active['name'] if active else None):
            if server.poll() is not None:raise RuntimeError('formal server exited before readiness')
            if time.monotonic()>=deadline:raise TimeoutError('formal server readiness timeout')
            time.sleep(2)
        write_json(output/'runtime'/f"{spec['phase_id']}.json",{
            'role':role,'started_epoch':started,'server_pid':server.pid,'server_command':command,
            'effective_config_sha256':sha_file(cfg_path),'server_recipe':recipe.model(tag),
            'adapter':active,'state':'ready'})
        with (logs/f"{spec['phase_id']}.worker.log").open('ab') as stream:
            worker=subprocess.Popen([sys.executable,'-u','-m','RQs.RQ3.src.main','formal-worker',
                '--source',str(spec_path),'--output',str(output)],cwd=ROOT,env=env,
                stdout=stream,stderr=subprocess.STDOUT,start_new_session=True,pass_fds=(_gpu_lease_fd,))
        if worker.wait()!=0:raise RuntimeError('formal phase worker failed; completed outcomes are retained')
        result=read_json(output/'phase_results'/f"{spec['phase_id']}.json")
        if result['spec_hash']!=spec['spec_hash'] or result['status']!='complete':
            raise ValueError('formal phase did not publish its matching completion')
        return result
    finally:
        signal.signal(signal.SIGTERM,previous)
        stop(worker);stop(server)
        CallLedger(ROOT/'RQs/RQ3/results/calls.sqlite',config['budget']['hard_limit'],
                   scope=output.name).interrupt_scope('owned_model_phase_stopped')


def training_work_spec(config, phase, prepared, output, *, policy_version):
    """Bind isolated catalogues, actual proposals/fixed designs and validation-frozen eval policies."""
    from .utils import registered_schedule,formal_phase_plan,sha_file,verify_work_spec,partition_rows
    from .exps import ComposerProgramV1, fixed_designs,fixed_selection,solver_parts,render_program,render_capacity_failure
    from .gates import audit_catalog,audit_render
    split=RQ3SegmentationAdapter(config).build();schedule=registered_schedule(split,config)
    plan=formal_phase_plan(split,config);output=Path(output).resolve();prepared=Path(prepared).resolve()
    if phase not in plan['phases'] or phase['kind'] not in {'composer','solver'}:
        raise ValueError('unregistered training model phase')
    partition=phase['details']['partition']
    identities={(r['dataset'],r['case_id']):r['opaque_incident_id'] for r in partition_rows(config,split,partition)}
    index=read_json(prepared/'index.json')
    if index['partition']!=partition or index['split_hash']!=split['split_hash']:
        raise ValueError('training work has a different prepared split')
    by_opaque={r['opaque_incident_id']:r for r in index['cases']}
    tasks={t['call_key']:t for t in schedule['tasks']};inventory={};entries=[]
    def include(path):
        path=Path(path).resolve()
        if not path.is_relative_to(ROOT/'RQs/RQ3/results'):raise ValueError('phase dependency outside RQ3')
        relative=str(path.relative_to(ROOT));inventory.setdefault(relative,sha_file(path));return relative
    for key in phase['call_keys']:
        task=tasks[key];opaque=identities[task['dataset'],task['case_id']];row=by_opaque[opaque]
        public=prepared/row['public'];payload=read_json(public);audit_catalog(payload,config)
        entry={'task':task,'case':opaque,'prepared_public':include(public),
               'prepared_private':include(prepared/row['private'])}
        seed=config['rl']['branches'].get(task['policy'],config['seed'])
        entry['sampling_seed']=(int(stable_hash([seed,task['stage'],task['dataset'],task['case_id'],
                task.get('traversal',0),task.get('sample',0)])[:8],16) if phase['kind']=='composer' else 42)
        if partition=='eval':
            parts,packet=_evaluation_input(config,task,entry,payload,output,include,tasks)
            if phase['kind']=='solver' and not entry.get('uncalled_status'):
                entry['parts_path']=_commit_solver_parts(parts,packet,key,output,include,inventory)
            entries.append(entry);continue
        if phase['kind']=='solver':
            if task['stage']=='fixed_validation':
                pool,cards=hydrate(payload)
                design=next(d['design'] for d in fixed_designs() if d['id']==task['policy'])
                program=ComposerProgramV1(fixed_selection(cards),design)
                try:
                    packet,png,manifest=render_program(pool,cards,program)
                    audit_render(pool,cards,program,manifest)
                except ValueError as exc:
                    if not render_capacity_failure(exc):raise
                    entry.update(uncalled_status='design_infeasible',error=str(exc))
            else:
                identity={k:v for k,v in task.items() if k not in {'call_key','max_new_calls'}}
                identity['role']='composer';composer_key=stable_hash(identity)
                if composer_key not in tasks:raise ValueError('no registered matching Composer request')
                outcome_path=output/'outcomes'/f'{composer_key}.json';include(outcome_path)
                outcome=read_json(outcome_path)
                if (outcome.get('outcome_hash')!=stable_hash({k:v for k,v in outcome.items() if k!='outcome_hash'})
                        or outcome['task']!=tasks[composer_key] or outcome['case']!=opaque
                        or outcome['observation_hash']!=stable_hash(payload['observation'])):
                    raise ValueError('Solver proposal input binding mismatch')
                include(output/outcome['record_path'])
                entry['composer_record_hash']=outcome['record_hash']
                if outcome['status']=='program_failure':
                    entry.update(uncalled_status='not_called_invalid_program',error=outcome['error'])
                elif outcome['status']=='valid':
                    for p,digest in outcome['render_hashes'].items():
                        if sha_file(output/p)!=digest:raise ValueError('Composer render changed before Solver')
                        include(output/p)
                    packet=read_json(output/outcome['render']['packet']);png=(output/outcome['render']['image']).read_bytes()
                    manifest=read_json(output/outcome['render']['manifest'])
                else:raise ValueError('unfinished Composer proposal cannot be evaluated')
            if not entry.get('uncalled_status'):
                entry['parts_path']=_commit_solver_parts(solver_parts(packet,png,manifest),packet,key,output,include,inventory)
        entries.append(entry)
    result={'schema_version':'RQ3PhaseWorkV1','phase_id':phase['id'],'role':phase['kind'],
            'partition':partition,'policy_version':policy_version,'split_hash':split['split_hash'],
            'plan_hash':plan['plan_hash'],'entries':entries,'artifact_hashes':inventory}
    result['spec_hash']=stable_hash(result);verify_work_spec(result,split,schedule,plan,output)
    path=output/'private'/'work_specs'/f"{phase['id']}.json"
    if path.exists() and read_json(path)!=result:raise ValueError('published training work specification changed')
    if not path.exists():write_json(path,result)
    return path


def _commit_solver_parts(parts,packet,key,output,include,inventory):
    stored=[]
    for i,part in enumerate(parts):
        part=dict(part)
        if 'png' in part:
            image=part.pop('png');path=output/'inputs'/f'{key}_{i}.png'
            if path.exists() and path.read_bytes()!=image:raise ValueError('phase PNG changed on resume')
            if not path.exists():atomic_write(path,image)
            relative=include(path);part.update(image_path=relative,image_sha256=inventory[relative])
        stored.append(part)
    bundle={'parts':stored,'candidates':packet['candidates'],'fact_inventory_hash':packet['fact_inventory_hash']}
    path=output/'inputs'/f'{key}.json'
    if path.exists() and read_json(path)!=bundle:raise ValueError('phase input changed on resume')
    if not path.exists():write_json(path,bundle)
    return include(path)


def _evaluation_input(config,task,entry,payload,output,include,tasks):
    """Actual fixed/learned/intervention inputs, never a replacement proposal."""
    from .exps import (ComposerProgramV1,fixed_selection,render_program,solver_parts,
                      render_capacity_failure,parse_program)
    from .gates import audit_call_artifacts,audit_render
    from .utils import sha_file
    def outcome(policy,role='composer',case=None,stage='eval'):
        identity={'stage':stage,'role':role,'dataset':task['dataset'],'case_id':case or task['case_id'],'policy':policy}
        key=stable_hash(identity);path=output/'outcomes'/f'{key}.json';include(path);row=read_json(path)
        if row['task']!=tasks[key] or row['outcome_hash']!=stable_hash({k:v for k,v in row.items() if k!='outcome_hash'}):
            raise ValueError('intervention source outcome changed')
        if row.get('record_path'):
            p=output/row['record_path'];include(p);record=read_json(p);audit_call_artifacts(record,output)
            if record['record_hash']!=row['record_hash']:raise ValueError('intervention source record changed')
        for p,digest in row.get('render_hashes',{}).items():
            if sha_file(output/p)!=digest:raise ValueError('intervention source rendering changed')
            include(output/p)
        return row
    policy=task['policy'];local=task['stage']=='local_intervention'
    if local and policy in {'reanonymize','composer_reanonymize'}:
        folder=output/'prepared_reanonymized';public=folder/'public'/f"{entry['case']}.json";private=folder/'private'/public.name
        if not public.exists():
            from .exps import reanonymized_catalog
            changed,labels=reanonymized_catalog(payload,read_json(ROOT/entry['prepared_private']),config)
            write_json(private,labels);write_json(public,changed)
        changed=read_json(public)
        if changed['reanonymization']['source_pool_hash']!=stable_hash(payload['pool']):raise ValueError('reanonymization source changed')
        entry.update(prepared_public=include(public),prepared_private=include(private));payload=changed
    if task['role']=='composer':return None,None
    pool,cards=hydrate(payload);fixed=read_json(output/'private/frozen_fixed_design.json')
    include(output/'private/frozen_fixed_design.json')
    baseline=ComposerProgramV1(fixed_selection(cards),fixed['design']);kind='canvas'
    if task['stage']=='eval' and policy in {'T_FIXED','C_FIXED','TPV_FIXED'}:
        folder=output/'fixed_baselines';path=folder/'prompts'/f"{entry['case']}_{policy}.json"
        source=read_json(path);include(path);parts=[]
        for part in source['parts']:
            part=dict(part)
            if 'image_path' in part:
                p=folder/part.pop('image_path')
                if sha_file(p)!=part.pop('image_sha256'):raise ValueError('fixed control image changed')
                include(p);part['png']=p.read_bytes()
            parts.append(part)
        return parts,{'candidates':pool['candidates'],'fact_inventory_hash':source['fact_inventory_hash']}
    if policy=='D_FIXED':program=baseline
    else:
        source_policy=policy if task['stage']=='eval' else 'RL_COST_42'
        source=outcome('composer_reanonymize',stage='local_intervention') if policy=='composer_reanonymize' else outcome(source_policy)
        entry['composer_record_hash']=source['record_hash']
        if source['status']=='program_failure':
            entry.update(uncalled_status='not_called_invalid_program',error=source['error']);return None,None
        if source['status']!='valid':raise ValueError('unfinished proposal cannot enter eval/attribution')
        original=read_json(output/source['render']['manifest'])['rq3_program']
        learned=parse_program(original,cards,config);program=learned
        if policy in {'U10','U01'}:
            program=ComposerProgramV1(learned.selection if policy=='U10' else baseline.selection,
                                      baseline.design if policy=='U10' else learned.design)
        elif policy in {'TextTwin','ScreenshotTwin'}:kind='text' if policy=='TextTwin' else 'screenshot'
        elif local and policy in {'encoding','layout','resolution','wrong_case_design','hash_random'}:
            program=local_design_intervention(policy,learned,baseline,task,tasks,outcome)
            if program is None:
                entry.update(uncalled_status='intervention_infeasible',error='registered partner emitted no legal design');return None,None
        if policy not in {'U10','U01','encoding','layout','resolution','wrong_case_design','hash_random','reanonymize'}:
            packet=read_json(output/source['render']['packet']);manifest=read_json(output/source['render']['manifest'])
            png=(output/source['render']['image']).read_bytes()
            try:return solver_parts(packet,png,manifest,kind),packet
            except ValueError as exc:
                if 'ScreenshotTwin requires exactly one image' not in str(exc):raise
                entry.update(uncalled_status='design_infeasible',error=str(exc));return None,None
    try:
        packet,png,manifest=render_program(pool,cards,program);audit_render(pool,cards,program,manifest)
    except ValueError as exc:
        if not render_capacity_failure(exc):raise
        entry.update(uncalled_status='intervention_infeasible' if task['stage']!='eval' else 'design_infeasible',error=str(exc))
        return None,None
    path=output/'inputs'/f"{task['call_key']}_manifest.json"
    if path.exists() and read_json(path)!=manifest:raise ValueError('intervention changed on resume')
    if not path.exists():write_json(path,manifest)
    include(path)
    return solver_parts(packet,png,manifest),packet


def local_design_intervention(policy,learned,fixed,task,tasks,outcome):
    from .exps import ComposerProgramV1,ENCODINGS
    import random
    design=dict(learned.design)
    fields=([k for k in design if k.endswith('_encoding')] if policy=='encoding' else
            ['layout_family','entity_order','footprint_policy','grid_columns','grid_rows'] if policy=='layout' else
            ['raster_scale'] if policy=='resolution' else [])
    for field in fields:design[field]=fixed.design[field]
    if policy=='wrong_case_design':
        cases=sorted({t['case_id'] for t in tasks.values() if t['stage']=='eval' and t['dataset']==task['dataset']
                      and t['case_id']!=task['case_id']},key=lambda c:stable_hash([42,task['case_id'],c]))
        partner=outcome('RL_COST_42',case=cases[0])
        if partner['status']=='program_failure':return None
        if partner['status']!='valid':raise ValueError('wrong-case design source unfinished')
        design=partner['program']['design']
    if policy=='hash_random':
        rng=random.Random(int(stable_hash([42,task['dataset'],task['case_id'],'hash_random'])[:16],16))
        for field,values in ENCODINGS.items():design[field]=rng.choice(values)
        # Keep the learned legal grid/raster budget; randomization is only design.
    return ComposerProgramV1(learned.selection,design)


def train_registered_rloo_batch(config, source, output):
    """Recover a complete formal update from verified original call inventories, never unbound rewards."""
    from .utils import (verified_checkpoint, assemble_rloo_groups, rloo_batches,
                        registered_schedule, sha_file)
    from .gates import assert_formal_authorized, audit_call_artifacts, audit_training_rows
    from .exps import update_rloo_batch, training_contract
    assert_formal_authorized(config)
    source=Path(source).resolve();envelope=read_json(source)
    owner=(ROOT/'RQs/RQ3/results').resolve()
    if not source.is_relative_to(owner) or not Path(output).resolve().is_relative_to(owner):
        raise ValueError('RLOO input/output must be RQ3-owned')
    if envelope.get('envelope_hash')!=stable_hash({k:v for k,v in envelope.items() if k!='envelope_hash'}):
        raise ValueError('RLOO batch envelope hash mismatch')
    branch=envelope['branch'];batch_index=envelope['batch_index']
    if branch not in config['rl']['branches']:
        raise ValueError('unregistered RLOO training branch')
    split=RQ3SegmentationAdapter(config).build()
    batch=rloo_batches(split,config,branch)[batch_index]
    if batch['batch_hash']!=envelope['batch_hash']:
        raise ValueError('RLOO batch identity differs from registration')
    root=(ROOT/envelope['run_root']).resolve()
    if not root.is_relative_to(owner):raise ValueError('RLOO call root outside RQ3')
    for relative,digest in envelope['artifact_hashes'].items():
        path=(root/relative).resolve()
        if not path.is_relative_to(root) or not path.is_file() or sha_file(path)!=digest:
            raise ValueError('RLOO source artifact missing or changed')
    def read_member(relative):
        path=(root/relative).resolve()
        if not path.is_relative_to(root) or relative not in envelope['artifact_hashes']:
            raise ValueError('RLOO source is not in its committed envelope inventory')
        return read_json(path)
    role_rows={};adapter_identities=[]
    for role in ('composer','solver'):
        rows={}
        for key,relative in envelope[role+'_outcomes'].items():
            row=read_member(relative)
            if row.get('record_path') is not None:
                record=read_member(row['record_path']);audit_call_artifacts(record,root)
                if record['record_hash']!=row.get('record_hash'):
                    raise ValueError('RLOO outcome refers to a different response')
                if role=='composer':
                    prompt=read_json(root/'prompts'/f"{record['artifact_key']}.json")
                    adapter_identities.append(prompt.get('composer_adapter'))
                    row={**row,'record':record}
                else:
                    # Attention remains in the original verified call. Do not
                    # copy its large tensors into every optimizer envelope.
                    row={**row,'record':{k:record[k] for k in
                        ('call_key','role','record_hash','input_tokens','output_tokens')}}
            else:row={**row,'record':None}
            rows[key]=row
        role_rows[role]=rows
    composer_rows=role_rows['composer'];solver_rows=role_rows['solver']
    groups=assemble_rloo_groups(config,split,batch,registered_schedule(split,config),
        composer_rows,solver_rows,envelope['observations'],envelope['reference'],envelope['policy_version'])
    split_hash=audit_training_rows(config,groups)
    active={**config,'training_branch':branch,'training_seed':config['rl']['branches'][branch],
            'actual_train_counts':{d:sum(r['dataset']==d for r in split['train'])
                                   for d in config['data']['allowed_training_datasets']}}
    contract=training_contract(active,split_hash)
    reference=(ROOT/envelope['sft_reference']).resolve()
    policy=(ROOT/envelope['policy_checkpoint']).resolve()
    if not reference.is_relative_to(owner) or not policy.is_relative_to(owner):
        raise ValueError('RLOO checkpoint is outside RQ3 results')
    ref_state=verified_checkpoint(reference,stage='SFT')
    if ref_state.get('promotable') is False:
        raise ValueError('disposable qualification cannot be the RL reference')
    expected_ref=training_contract(config,split_hash)
    if ref_state.get('training_contract')!=expected_ref:
        raise ValueError('RLOO SFT reference has a different training recipe/split')
    policy_state=verified_checkpoint(policy)
    expected_adapter={name:policy_state['files'][name] for name in
                      ('policy/adapter_config.json','policy/adapter_model.safetensors')}
    if any(not identity or identity['name']!=envelope['policy_version'] or
           identity['files']!=expected_adapter for identity in adapter_identities):
        raise ValueError('RLOO rollout adapter bytes differ from its optimizer policy')
    previous=None
    if batch_index==0:
        if policy!=reference:raise ValueError('each RL branch starts from the identical SFT reference')
    else:
        if (policy_state.get('stage')!='RLOO' or policy_state.get('training_contract')!=contract
                or policy_state.get('batch_index')!=batch_index-1):
            raise ValueError('RL optimizer/policy is not this branch preceding batch')
        previous=policy
    expected={'stage':'RLOO','training_contract':contract,'group_hash':stable_hash(groups),
              'input_policy_version':envelope['policy_version'],'batch_index':batch_index,
              'source_envelope_hash':envelope['envelope_hash']}
    if (Path(output)/'checkpoint.json').exists():
        verified_checkpoint(output,**expected)
        return {'status':'already_complete','checkpoint':str(output),'new_optimizer_updates':0}
    active['rloo_checkpoint_provenance']={'batch_index':batch_index,'source_envelope_hash':envelope['envelope_hash']}
    result=update_rloo_batch(active,groups,policy/'policy',reference/'policy',output,
                             envelope['policy_version'],resume_optimizer=previous)
    verified_checkpoint(result,**expected)
    return {'status':'complete','checkpoint':str(result),'new_optimizer_updates':1}


def commit_rloo_batch_input(config, phase, prepared, output, policy_checkpoint, sft_reference, policy_version):
    """Publish the exact complete rollout batch consumed by the optimizer CLI."""
    from .utils import rloo_batches,registered_schedule,sha_file
    split=RQ3SegmentationAdapter(config).build();details=phase['details']
    branch=details['branch'];batch=rloo_batches(split,config,branch)[details['batch_index']]
    if details['batch_hash']!=batch['batch_hash']:raise ValueError('batch registration changed')
    output=Path(output).resolve();prepared=Path(prepared).resolve()
    index=read_json(prepared/'index.json');source={r['opaque_incident_id']:r for r in index['cases']}
    if index['partition']!='train' or index['split_hash']!=split['split_hash']:
        raise ValueError('RLOO optimizer input requires the registered train partition')
    identities={(r['dataset'],r['case_id'],r['traversal']) for r in batch['cases']}
    tasks=[t for t in registered_schedule(split,config)['tasks'] if t['stage']=='rl' and t['policy']==branch
           and (t['dataset'],t['case_id'],t['traversal']) in identities]
    result={'schema_version':'RQ3RLOOBatchInputV1','branch':branch,'batch_index':batch['index'],
            'batch_hash':batch['batch_hash'],'run_root':str(output.relative_to(ROOT)),
            'policy_version':policy_version,'policy_checkpoint':str(Path(policy_checkpoint).resolve().relative_to(ROOT)),
            'sft_reference':str(Path(sft_reference).resolve().relative_to(ROOT)),
            'reference':read_json(output/'private/frozen_cost_reference.json'),'observations':{},
            'composer_outcomes':{},'solver_outcomes':{},'artifact_hashes':{}}
    for row in batch['cases']:
        payload=read_json(prepared/source[row['opaque_incident_id']]['public'])
        result['observations'][row['opaque_incident_id']]=payload['observation']
    for task in tasks:
        key=task['call_key'];path=output/'outcomes'/f'{key}.json';row=read_json(path)
        if row['task']!=task or row.get('outcome_hash')!=stable_hash({k:v for k,v in row.items() if k!='outcome_hash'}):
            raise ValueError('RLOO source outcome changed')
        relative=str(path.relative_to(output));result[task['role']+'_outcomes'][key]=relative
        result['artifact_hashes'][relative]=sha_file(path)
        if row.get('record_path'):
            result['artifact_hashes'][row['record_path']]=sha_file(output/row['record_path'])
    result['envelope_hash']=stable_hash(result)
    path=output/'private'/'rloo_inputs'/f"{branch}_batch_{batch['index']:03d}.json"
    if path.exists() and read_json(path)!=result:raise ValueError('committed optimizer input changed')
    if not path.exists():write_json(path,result)
    return path


def validation_pipeline_rows(config, output, policy, *, checkpoint, fraction=None, reference=None):
    """Aggregate complete paired pipelines, preserving invalid/no-call outcomes."""
    from .utils import registered_schedule,validate_validation_population,cost_reward
    from .gates import audit_call_artifacts
    output=Path(output);split=RQ3SegmentationAdapter(config).build()
    tasks=[t for t in registered_schedule(split,config)['tasks'] if t['stage']=='validation'
           and t['policy']==policy and t.get('fraction')==fraction]
    grouped={};rows=[]
    for task in tasks:
        outcome=read_json(output/'outcomes'/f"{task['call_key']}.json")
        if outcome['task']!=task or outcome.get('outcome_hash')!=stable_hash({k:v for k,v in outcome.items() if k!='outcome_hash'}):
            raise ValueError('validation source outcome changed')
        if outcome.get('record_path'):
            record=read_json(output/outcome['record_path']);audit_call_artifacts(record,output)
            if record['record_hash']!=outcome['record_hash']:raise ValueError('validation response binding mismatch')
        else:record=None
        grouped.setdefault((task['dataset'],task['case_id']),{})[task['role']]=(outcome,record)
    for (dataset,case_id),pair in grouped.items():
        if set(pair)!={'composer','solver'}:raise ValueError('validation pipeline is incomplete')
        c,cr=pair['composer'];s,sr=pair['solver']
        if cr is None or s['composer_record_hash']!=cr['record_hash']:
            raise ValueError('validation Solver belongs to another proposal')
        if c['status']=='program_failure':
            if s['status']!='not_called_invalid_program' or sr is not None:raise ValueError('invalid validation proposal was substituted')
            valid=False
        elif c['status']=='valid':
            valid=s['status'] in {'complete','model_failure'}
            if not valid and (s['status']!='design_infeasible' or s.get('failure_stage')!='context'):
                raise ValueError('validation infrastructure failure cannot supply zero reward')
            if valid and sr is None:raise ValueError('missing validation Solver response')
        else:raise ValueError('incomplete validation Composer result')
        tokens={'composer_input':cr['input_tokens'],'composer_output':cr['output_tokens'],
                'solver_input':sr['input_tokens'] if sr else 0,'solver_output':sr['output_tokens'] if sr else 0}
        rr=float(s['metrics']['mrr']) if valid else 0.
        row={'dataset':dataset,'case_id':case_id,'partition':'validation','policy':policy,
             'checkpoint':checkpoint,'tokens':tokens,'reciprocal_rank':rr,'program_valid':valid,
             'infrastructure_error':False,'composer_record_hash':cr['record_hash'],
             'solver_record_hash':sr['record_hash'] if sr else None}
        if reference:
            reward=cost_reward(rr,tokens,reference['means'],rr_only=policy=='RL_RR_42')['reward']
            row['objective']=reward if valid else config['rl']['invalid_program_reward']
        else:row['objective']=rr
        rows.append(row)
    validate_validation_population(rows,split,checkpoint=checkpoint)
    return sorted(rows,key=lambda r:(r['dataset'],r['case_id']))


def verified_phase_outcomes(config, phase, output):
    """Load terminal outcomes by registered keys, including uncalled failures."""
    from .utils import registered_schedule
    from .gates import audit_call_artifacts
    tasks={t['call_key']:t for t in registered_schedule(RQ3SegmentationAdapter(config).build(),config)['tasks']}
    rows=[]
    for key in phase['call_keys']:
        row=read_json(output/'outcomes'/f'{key}.json')
        if row.get('outcome_hash')!=stable_hash({k:v for k,v in row.items() if k!='outcome_hash'}) or row['task']!=tasks[key]:
            raise ValueError('registered outcome changed after phase completion')
        if row.get('record_path'):
            record=read_json(output/row['record_path']);audit_call_artifacts(record,output)
            if record['record_hash']!=row['record_hash']:raise ValueError('phase response identity mismatch')
        elif row['status'] not in {'design_infeasible','intervention_infeasible','not_called_invalid_program'}:
            raise ValueError('terminal phase lacks its required response')
        rows.append(row)
    return rows


def materialize_imitation(config, output):
    """Distil legal winners from the committed COST-42 feedback, without calls."""
    from .utils import rloo_batches,sha_file,imitation_examples,assemble_rloo_groups,registered_schedule
    from .gates import audit_call_artifacts,audit_training_rows
    split=RQ3SegmentationAdapter(config).build();schedule=registered_schedule(split,config)
    examples=[];sources={}
    for batch in rloo_batches(split,config,'RL_COST_42'):
        path=output/'private/rloo_inputs'/f"RL_COST_42_batch_{batch['index']:03d}.json"
        envelope=read_json(path)
        if envelope['envelope_hash']!=stable_hash({k:v for k,v in envelope.items() if k!='envelope_hash'}):
            raise ValueError('imitation feedback envelope changed')
        sources[str(path.relative_to(output))]=sha_file(path);roles={}
        for role in ('composer','solver'):
            roles[role]={}
            for key,relative in envelope[role+'_outcomes'].items():
                if sha_file(output/relative)!=envelope['artifact_hashes'].get(relative):raise ValueError('imitation outcome changed')
                row=read_json(output/relative);record=None
                if row.get('record_path'):
                    record_path=output/row['record_path']
                    if sha_file(record_path)!=envelope['artifact_hashes'].get(row['record_path']):raise ValueError('imitation reply changed')
                    record=read_json(record_path);audit_call_artifacts(record,output)
                    if role=='solver':record={k:record[k] for k in ('call_key','role','record_hash','input_tokens','output_tokens')}
                roles[role][key]={**row,'record':record}
        groups=assemble_rloo_groups(config,split,batch,schedule,roles['composer'],roles['solver'],
                                   envelope['observations'],envelope['reference'],envelope['policy_version'])
        examples.extend(imitation_examples(groups))
    audit_training_rows(config,examples)
    if {r['dataset'] for r in examples}!=set(config['data']['allowed_training_datasets']):
        raise ValueError('no legal imitation targets for one training dataset; cannot invent targets')
    destination=output/'imitation_examples';path=destination/'private/winners.json'
    body={'examples':examples,'examples_hash':stable_hash(examples),'sources':sources,'new_model_calls':0}
    if path.exists() and read_json(path)!=body:raise ValueError('imitation target changed on resume')
    if not path.exists():write_json(path,body)
    write_json(destination/'index.json',{'split_hash':split['split_hash'],'qualification_only':False,
        'cases':len({(r['dataset'],r['case_id']) for r in examples}),'examples':len(examples),
        'examples_hash':stable_hash(examples),'files':[{'path':'private/winners.json','sha256':sha_file(path)}]})
    return destination


@owned_gpu_process
def run_training_process(config, command, args, output, phase_id, *, _gpu_lease_fd):
    """One owned trainer; preserve full checkpoints and drain on termination."""
    import signal
    import subprocess
    import shutil
    import time
    from .gates import assert_formal_authorized
    assert_formal_authorized(config)
    if shutil.disk_usage(output).free<8*1024**3:raise RuntimeError('less than 8 GiB free before training')
    live=subprocess.run(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader,nounits'],
                        check=True,capture_output=True,text=True)
    if live.stdout.strip():raise RuntimeError('GPU compute processes remain; inspect ownership before loading trainer')
    path=output/'private/training_configs'/f'{phase_id}.yaml';data=yaml.safe_dump(config,sort_keys=True).encode()
    if path.exists() and path.read_bytes()!=data:raise ValueError('training phase recipe changed')
    if not path.exists():atomic_write(path,data)
    (output/'logs').mkdir(parents=True,exist_ok=True)
    process=None;started=time.time();start_clock=time.monotonic()
    def terminate(*_):raise KeyboardInterrupt('formal training interrupted')
    previous=signal.signal(signal.SIGTERM,terminate)
    try:
        with (output/'logs'/f'{phase_id}.train.log').open('ab') as stream:
            process=subprocess.Popen(['bash','RQs/RQ3/scripts/train_local.sh','--config',str(path),
                command,*map(str,args)],cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True,
                pass_fds=(_gpu_lease_fd,))
            write_json(output/'runtime'/f'{phase_id}.trainer.json',{'pid':process.pid,'state':'running',
                'command':command,'started':started,'config_path':str(path.relative_to(output))})
            if process.wait()!=0:raise RuntimeError('trainer failed; committed checkpoints are preserved')
    finally:
        if process is not None and process.poll() is None:
            os.killpg(process.pid,signal.SIGTERM)
            try:process.wait(timeout=60)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid,signal.SIGKILL);process.wait(timeout=10)
        signal.signal(signal.SIGTERM,previous)
        if process is not None:
            write_json(output/'runtime'/f'{phase_id}.trainer.json',{'pid':process.pid,'state':'stopped',
                'exit_code':process.returncode,'command':command,'started':started,
                'elapsed_seconds':time.monotonic()-start_clock,'config_path':str(path.relative_to(output))})


class LearningLifecycle:
    # Training prefix: ends with validation-frozen policies, not a completed
    # RQ3. The full evaluation/attribution controller consumes these outputs.
    def __init__(self,config,output,pools):
        from .utils import formal_phase_plan
        self.config=config;self.output=Path(output).resolve();self.pools=Path(pools).resolve()
        self.split=RQ3SegmentationAdapter(config).build();self.plan=formal_phase_plan(self.split,config)
        if not self.output.is_relative_to(ROOT/'RQs/RQ3/results'):raise ValueError('formal owner outside RQ3')
        if config['sft'].get('effective_attention_implementation')!='flash_attention_2':
            raise ValueError('formal training must explicitly bind the live-qualified FlashAttention kernel')

    def publish(self,relative,body):
        path=self.output/relative
        if path.exists() and read_json(path)!=body:raise ValueError(f'committed lifecycle output changed: {relative}')
        if not path.exists():write_json(path,body)
        return path

    def checkpoint(self,policy,batch=None):
        from .utils import verified_checkpoint
        path=(self.output/'models'/policy/f'batch-{batch:03d}' if batch is not None else
              ROOT/read_json(self.output/'private/policies'/f'{policy}.json')['checkpoint'])
        verified_checkpoint(path)
        return path

    def prepared(self,partition):
        reference=self.output/'private/preparation_sources.json'
        return ROOT/read_json(reference)[partition]['path'] if partition!='eval' and reference.exists() else self.output/'prepared'/partition

    def examples(self):
        reference=self.output/'private/format_source.json'
        return ROOT/read_json(reference)['path'] if reference.exists() else self.output/'format_examples'

    def phase_policy(self,phase):
        from .utils import rloo_batches
        detail=phase['details'];policy=detail.get('branch',detail.get('policy'))
        if 'branch' in detail:
            index=detail['batch_index'];checkpoint=self.checkpoint(policy,index-1) if index else self.checkpoint('SFT')
            return f'{policy}_v{index:03d}',checkpoint
        if policy in self.config['rl']['branches']:
            batch=next(b for b in rloo_batches(self.split,self.config,policy)
                       if b['validation_fraction']==detail['fraction'])
            return f"{policy}_v{batch['index']+1:03d}",self.checkpoint(policy,batch['index'])
        if policy in {'SFT','IMITATION'}:return policy,self.checkpoint(policy)
        return 'BASE',None

    def execute(self,phase):
        from .utils import (sha_file,read_format_examples,sft_resume_checkpoint,verified_checkpoint,
            frozen_cost_reference,select_fixed_validation,select_validation_checkpoint,rloo_batches)
        from .exps import fixed_designs
        config=self.config;out=self.output;kind=phase['kind'];pid=phase['id'];detail=phase['details'];artifacts=[]
        if kind=='prepare':
            if detail['partitions']!=['train','validation']:raise ValueError('learning cannot open eval')
            references={}
            for partition in detail['partitions']:
                source=self.pools/partition;index=read_json(source/'index.json')
                if (index['layout']!='full_pool' or index['split_hash']!=self.split['split_hash'] or
                    {r['opaque_incident_id'] for r in index['cases']}!={r['opaque_incident_id'] for r in self.split[partition]}):
                    raise ValueError('full immutable preparation has not completed the registered population')
                target=(ROOT/config['prepared_catalogues_root']/partition if config.get('prepared_catalogues_root') else out/'prepared'/partition)
                if config.get('prepared_catalogues_root'):
                    from .gates import audit_catalog
                    catalog=read_json(target/'index.json')
                    if catalog['partition']!=partition or catalog['split_hash']!=self.split['split_hash'] or catalog['cases']!=index['cases']:
                        raise ValueError('reusable catalogue population differs from full pools')
                    inventory={}
                    for row in catalog['cases']:
                        public=target/row['public'];payload=read_json(public);audit_catalog(payload,config)
                        original=read_json(source/row['public'])
                        if stable_hash(payload['pool'])!=original['pool_hash'] or (target/row['private']).read_bytes()!=(source/row['private']).read_bytes():
                            raise ValueError('reusable catalogue changed its immutable source')
                        for name in ('public','private'):inventory[str((target/row[name]).relative_to(ROOT))]=sha_file(target/row[name])
                else:
                    refresh_catalog(config,source,target);inventory={}
                references[partition]={'path':str(target.relative_to(ROOT)),'index_sha256':sha_file(target/'index.json'),'artifact_hashes':inventory}
            artifacts.append(self.publish('private/preparation_sources.json',references))
        elif kind=='format_examples':
            target=ROOT/config['prepared_format_examples'] if config.get('prepared_format_examples') else out/'format_examples'
            if not config.get('prepared_format_examples'):format_examples(config,self.prepared('train'),target)
            index,rows=read_format_examples(target)
            from .gates import audit_training_rows
            if index['qualification_only'] or index['split_hash']!=audit_training_rows(config,rows) or index['cases']!=len(self.split['train']):
                raise ValueError('reusable format targets are not the complete isolated training set')
            artifacts.append(self.publish('private/format_source.json',{'path':str(target.relative_to(ROOT)),
                'index_sha256':sha_file(target/'index.json'),'examples_hash':index['examples_hash']}))
        elif kind in {'sft_update','imitation_update'}:
            policy='SFT' if kind=='sft_update' else 'IMITATION';active=dict(config)
            examples=self.examples() if policy=='SFT' else materialize_imitation(config,out)
            if policy=='IMITATION':
                initial=self.checkpoint('SFT');state=verified_checkpoint(initial,stage='SFT')
                active.update(training_stage='IMITATION',training_initial_checkpoint=str(initial.relative_to(ROOT)),
                    training_initializer_hashes={k:state['files'][k] for k in ('policy/adapter_config.json','policy/adapter_model.safetensors')})
            modelroot=out/'models'/policy
            run_training_process(active,'train-sft',['--examples',examples,'--output',modelroot],out,pid)
            _,rows=read_format_examples(examples)
            checkpoint,done=sft_resume_checkpoint(modelroot,rows,active,self.split['split_hash'])
            if not done:raise ValueError('trainer exited without completing its registered traversal')
            artifacts.append(self.publish(f'private/policies/{policy}.json',{'policy':policy,
                'checkpoint':str(checkpoint.relative_to(ROOT)),'checkpoint_sha256':sha_file(checkpoint/'checkpoint.json')}))
            artifacts.append(checkpoint/'checkpoint.json')
        elif kind in {'composer','solver'}:
            version,checkpoint=self.phase_policy(phase);active=dict(config)
            if checkpoint:active['composer_active_adapter']={'checkpoint':str(checkpoint.relative_to(ROOT)),'name':version}
            spec=training_work_spec(active,phase,self.prepared(detail['partition']),out,policy_version=version)
            run_model_phase(active,spec,out)
            verified_phase_outcomes(config,phase,out)
            artifacts.extend([spec,out/'phase_results'/f'{pid}.json'])
            if kind=='solver' and pid.startswith('validation_'):
                policy=detail['policy'];label=policy if detail['fraction'] is None else version
                reference=read_json(out/'private/frozen_cost_reference.json') if policy.startswith('RL_') else None
                rows=validation_pipeline_rows(config,out,policy,checkpoint=label,fraction=detail['fraction'],reference=reference)
                artifacts.append(self.publish(f'private/validation/{label}.json',{'rows':rows,
                    'checkpoint':str(checkpoint.relative_to(ROOT)),'checkpoint_sha256':sha_file(checkpoint/'checkpoint.json')}))
        elif kind=='freeze_cost_reference':
            rows=read_json(out/'private/validation/SFT.json')['rows']
            artifacts.append(self.publish('private/frozen_cost_reference.json',frozen_cost_reference(rows,self.split)))
        elif kind=='freeze_fixed_design':
            modelphase=next(p for p in self.plan['phases'] if p['id']=='fixed_validation');rows=[]
            for row in verified_phase_outcomes(config,modelphase,out):
                task=row['task'];status=row['status']
                if status not in {'complete','model_failure','design_infeasible'}:raise ValueError('fixed-validation infrastructure hole')
                rows.append({'dataset':task['dataset'],'case_id':task['case_id'],'partition':'validation',
                    'design':task['policy'],'checkpoint':task['policy'],'infrastructure_error':False,
                    'reciprocal_rank':float(row['metrics']['mrr']),'total_tokens':row['input_tokens']+row['output_tokens'],
                    'executable':int(status!='design_infeasible')})
            result=select_fixed_validation(rows,self.split,[d['id'] for d in fixed_designs()])
            result['design']=next(d['design'] for d in fixed_designs() if d['id']==result['selected'])
            artifacts.append(self.publish('private/frozen_fixed_design.json',result))
            artifacts.append(self.publish('private/validation/fixed_designs.json',{'rows':rows}))
        elif kind=='rloo_update':
            version,checkpoint=self.phase_policy(phase);target=out/'models'/detail['branch']/f"batch-{detail['batch_index']:03d}"
            source=commit_rloo_batch_input(config,phase,self.prepared('train'),out,checkpoint,self.checkpoint('SFT'),version)
            run_training_process(config,'train-rloo-batch',['--source',source,'--output',target],out,pid)
            verified_checkpoint(target,stage='RLOO',batch_index=detail['batch_index'])
            artifacts.extend([source,target/'checkpoint.json'])
        elif kind=='freeze_policies':
            policies={'BASE':{'checkpoint':None}}
            for policy in ('SFT','IMITATION'):
                policies[policy]=read_json(out/'private/policies'/f'{policy}.json')
            for policy in config['rl']['branches']:
                rows=[];candidates={}
                for batch in rloo_batches(self.split,config,policy):
                    if batch['validation_fraction'] is None:continue
                    label=f"{policy}_v{batch['index']+1:03d}";saved=read_json(out/'private/validation'/f'{label}.json')
                    rows.extend(saved['rows']);candidates[label]=saved
                best=select_validation_checkpoint(rows,'objective');saved=candidates[best]
                selected=out/'models'/policy/'best-for-eval'/Path(saved['checkpoint']).name
                state=verified_checkpoint(selected,allow_inference_only=True)
                if state.get('parent_checkpoint_sha256')!=saved['checkpoint_sha256']:
                    raise ValueError('selected inference weights differ from validation checkpoint')
                policies[policy]={'checkpoint':str(selected.relative_to(ROOT)),'checkpoint_sha256':sha_file(selected/'checkpoint.json'),
                                  'validation_checkpoint':best,'objective':'RR' if policy=='RL_RR_42' else 'RR_cost'}
            for spec in policies.values():
                if spec['checkpoint']:
                    path=ROOT/spec['checkpoint'];verified_checkpoint(path,allow_inference_only=True)
                    if sha_file(path/'checkpoint.json')!=spec['checkpoint_sha256']:raise ValueError('selected policy checkpoint changed')
            artifacts.append(self.publish('private/frozen_policies.json',{'split_hash':self.split['split_hash'],
                'plan_hash':self.plan['plan_hash'],'policies':policies,'evaluation_used':False}))
        else:raise ValueError('not a registered learning lifecycle phase')
        return artifacts,{'kind':kind,'committed_artifacts':len(artifacts)}

    def run(self):
        from .utils import PhaseJournal
        from .gates import assert_formal_authorized,parent_integrity
        assert_formal_authorized(self.config);parent_integrity()
        with PhaseJournal(self.output,self.plan) as journal:
            for phase in self.plan['phases']:
                if phase['id']=='prepare_eval':break
                if not journal.begin(phase['id']):continue
                print(f"[formal] begin {phase['id']}",flush=True)
                artifacts,summary=self.execute(phase);journal.finish(phase['id'],artifacts,summary)
                from .utils import retain_rl_checkpoints
                retain_rl_checkpoints(self.config,self.output)
                print(f"[formal] committed {phase['id']}",flush=True)
        return {'status':'learning_complete_evaluation_pending','rq3_complete':False,
                'policies':str(self.output/'private/frozen_policies.json')}


class FormalLifecycle(LearningLifecycle):
    """Complete registered learning, locked eval, interventions and reports."""
    def execute(self,phase):
        if phase['id']=='prepare_eval':
            self.config={**self.config,'evaluation_freeze':str((self.output/'private/frozen_policies.json').relative_to(ROOT))}
            prepare(self.config,self.prepared('eval'),partition='eval',count=0,workers=4)
            prepare_fixed_baselines(self.config,self.prepared('eval'),self.output/'fixed_baselines')
            return [self.prepared('eval')/'index.json',self.output/'fixed_baselines/index.json'],{'cases':480}
        if phase.get('details',{}).get('partition')=='eval':
            active={**self.config,'evaluation_freeze':str((self.output/'private/frozen_policies.json').relative_to(ROOT))}
            frozen=read_json(self.output/'private/frozen_policies.json')['policies']
            policy=phase['details'].get('policy','BASE');checkpoint=frozen.get(policy,{}).get('checkpoint')
            version=policy if checkpoint else 'BASE'
            if checkpoint:active['composer_active_adapter']={'checkpoint':checkpoint,'name':version}
            spec=training_work_spec(active,phase,self.prepared('eval'),self.output,policy_version=version)
            run_model_phase(active,spec,self.output);verified_phase_outcomes(active,phase,self.output)
            return [spec,self.output/'phase_results'/f"{phase['id']}.json"],{'kind':phase['kind']}
        if phase['kind']=='analysis':
            from .utils import analyze_formal
            return analyze_formal(self.config,self.output,self.plan),{'status':'all_registered_tasks_analyzed'}
        return super().execute(phase)

    def run(self):
        from .utils import PhaseJournal
        from .gates import assert_formal_authorized,parent_integrity
        assert_formal_authorized(self.config);parent_integrity()
        with PhaseJournal(self.output,self.plan) as journal:
            for phase in self.plan['phases']:
                if not journal.begin(phase['id']):continue
                print(f"[formal] begin {phase['id']}",flush=True)
                artifacts,summary=self.execute(phase);journal.finish(phase['id'],artifacts,summary)
                from .utils import retain_rl_checkpoints
                retain_rl_checkpoints(self.config,self.output)
                print(f"[formal] committed {phase['id']}",flush=True)
            if not all(journal.completed(p['id']) for p in self.plan['phases']):raise ValueError('incomplete formal lifecycle')
        return {'status':'registered_execution_complete','manual_final_audit_required':True}


def qualify_reanonymization(config,prepared,output):
    from .exps import reanonymized_catalog
    from .utils import sha_file
    index=read_json(prepared/'index.json');split=RQ3SegmentationAdapter(config).build()
    allowed={r['opaque_incident_id']:r for r in split['validation']};rows=[]
    for dataset in ('aiops2022','aiops2025'):
        row=next(r for r in index['cases'] if allowed[r['opaque_incident_id']]['dataset']==dataset)
        source=prepared/row['public'];before=sha_file(source);payload=read_json(source)
        transformed,private=reanonymized_catalog(payload,read_json(prepared/row['private']),config)
        if sha_file(source)!=before:raise ValueError('qualification mutated its source')
        write_json(output/row['public'],transformed);write_json(output/row['private'],private)
        rows.append({'case':row['opaque_incident_id'],'source_sha256':before,'facts':len(payload['pool']['facts']),
                     'cards':len(payload['cards']),'catalogue_membership_preserved':True,'input_tokens':transformed['catalog_audit']['input_tokens']})
        print({'reanonymization':rows[-1]},flush=True)
    result={'status':'passed','new_model_calls':0,'cases':rows};write_json(output/'qualification.json',result)
    return result


def qualify_storage(source,output):
    raise PermissionError("Completed predecessor qualification is archived; use the search-first route")




def smoke_execution_shape(experiment, repair=False):
    roles,maximum={
        'exp_composer_learning':(('optimizer','composer','solver'),10),
        'exp_frozen_solver_generalization':(('composer','probability','solver'),10),
        'exp_selection_design_attribution':(('composer','solver'),9),
    }[experiment]
    return (('solver',),1 if experiment=='exp_selection_design_attribution' else 2) if repair else (roles,maximum)


SEARCH_CONFIG=ROOT/"RQs/RQ3/configs/search_first_v1.yaml"


def search_cohort_rows(config, split):
    n=config['search']['cases_per_dataset'];offset=config['search'].get('case_offset',0)
    if type(n) is not int or type(offset) is not int or n<1 or offset<0:raise ValueError('invalid search cohort size/offset')
    chosen=[]
    for dataset in ('aiops2022','aiops2025'):
        rows=sorted([r for r in split['train'] if r['dataset']==dataset],key=lambda r:stable_hash([42,r['opaque_incident_id']]))
        groups=set();sources=set()
        for i in range(offset+n):
            eligible=[r for r in rows if r['leakage_group'] not in groups]
            if not eligible:raise ValueError('insufficient distinct training groups')
            row=min(eligible,key=lambda r:(r['source'] in sources,stable_hash([42,r['opaque_incident_id']])))
            groups.add(row['leakage_group']);sources.add(row['source'])
            if i>=offset:chosen.append(row)
    return chosen


def search_gallery(config, source, output):
    """Commit the authorized cohort, then independently render its public cases."""
    if config['search'].get('selection_only_suite'):validate_selection_only_config(config)
    source=source.resolve();output=output.resolve();split=RQ3SegmentationAdapter(config).build()
    index=read_json(source/'index.json');lookup={r['opaque_incident_id']:r for r in index['cases']}
    tournament=config['search']['stage']=='tournament'
    if index['partition']!=('tournament' if tournament else 'train') or index['split_hash']!=split['split_hash']:raise ValueError('stale/unregistered pool partition')
    if tournament:
        from .utils import tournament_register,partition_rows
        r=tournament_register(config).rounds()[-1]
        if r['method']['config_hash']!=stable_hash(config):raise ValueError('tournament method changed')
        ids=set().union(*(set(v) for v in r['cohorts'].values()))
        chosen=[v for v in partition_rows(config,split,'tournament') if v['opaque_incident_id'] in ids]
    else:chosen=search_cohort_rows(config,split)[:config['search'].get('cohort_total')]
    if any(r['opaque_incident_id'] not in lookup for r in chosen):raise ValueError('selected train case lacks full pool')
    cohort={'split_hash':split['split_hash'],'policy':'registered_tournament_round' if tournament else 'hash42_source_coverage_distinct_groups','cases':chosen}
    if (output/'cohort.json').exists() and read_json(output/'cohort.json')!=cohort:raise ValueError('cohort changed')
    write_json(output/'cohort.json',cohort)
    jobs=[(config,source,output,row,lookup[row['opaque_incident_id']],index['partition']) for row in chosen]
    attempts=[a for batch in pinned_process_map(_search_gallery_case,jobs) for a in batch]
    write_json(output/'summary.json',{'attempts':attempts,'cohort':cohort,'model_calls':0})


def _search_gallery_case(job):
    from .exps import search_select, project_log_summaries, search_solver_parts, source_metric_geometry, project_trace_ms, project_whole_window, project_trace_rates, project_trace_status, tournament_visual_packet
    from .renderer.owner_groups import render_search_family
    from .renderer.designs import DashboardSpecV3
    from .utils import sha_file
    config,source,output,row,entry,partition=job;attempts=[]
    if config['search'].get('selection_only_suite'):validate_selection_only_config(config)
    case=row['opaque_incident_id'];path=source/entry['public']
    pool=read_json(path)['pool']
    if pool.get('pool_coverage',{}).get('entity_identity_policy','legacy_v1')!=config['harness'].get('entity_identity_policy','legacy_v1'):raise ValueError('prepared pool identity policy differs from search config')
    if pool.get('pool_coverage',{}).get('public_hosting',False)!=config['harness'].get('public_hosting',False):raise ValueError('prepared pool hosting policy differs from search config')
    if pool.get('pool_coverage',{}).get('public_membership',False)!=config['harness'].get('public_membership',False):raise ValueError('prepared pool membership policy differs from search config')
    rate_policy=config['search'].get('trace_rate_projection')
    if rate_policy not in (None,'observed_span_rate_v1'):raise ValueError('unknown trace rate projection')
    native_policies=[p for p in config['search']['selectors'] if p in ('baro_native24_v1','sircl_ma24_v1','sircl_trace_sc8_v1','sircl_log_freq6_v1')]
    if len(native_policies)>1:raise ValueError('one native source policy per gallery')
    status_policy=config['search'].get('trace_status_projection')
    if status_policy not in (None,'public_status6_v1'):raise ValueError('unknown trace status projection')
    if status_policy and (rate_policy or config['search'].get('temporal_projection')):raise ValueError('status projection cannot change other trace/time projections')
    geometry=source_metric_geometry(case,with_trace_exposure=bool(rate_policy),native_metric_policy=native_policies[0] if native_policies else None,with_trace_status=bool(status_policy))
    for policy in config['search']['selectors']:
        selected,selection=search_select(pool,policy,config['search'].get('metric_limit',8),config['search'].get('relevance_weight',1.),native_selection=geometry.get('native_selection'));packet,projection=project_log_summaries(selected)
        if config['search'].get('trace_projection')=='jaeger_us_to_ms_v1':
            packet,projection['trace_units']=project_trace_ms(packet,row['dataset'])
        elif config['search'].get('trace_projection'):raise ValueError('unknown trace projection')
        if status_policy:
            packet,projection['trace_status']=project_trace_status(packet,geometry['trace_status'])
        if rate_policy:
            if any(c['prompt']!='evidence_rate_v1' for c in config['search']['conditions']) or config['search']['render_overrides'].get('trace_axis_policy')!='labeled_rate_axis_v1':raise ValueError('trace rates require matched visual/static guide')
            packet,projection['trace_rates']=project_trace_rates(packet,geometry['trace_exposure'])
        if config['search'].get('temporal_projection')=='whole_window_v1':
            if any(c['prompt'] not in ('evidence_whole_window_v1','evidence_observations_v1') for c in config['search'].get('conditions',[])):raise ValueError('unanchored evidence requires whole-window guide')
            packet,projection['temporal']=project_whole_window(packet)
        elif config['search'].get('temporal_projection'):raise ValueError('unknown temporal projection')
        render_options=dict(grid_rows=8,grid_columns=8,cell_edge_px=256,legibility_scale=1.25,
            metric_scale_policy='per_card_raw',topology_space_policy='content_adaptive',
            pixel_capacity_policy='measured',log_rate_chart_policy='capacity_safe')
        render_options={**render_options,**config['search'].get('render_overrides',{})}
        if status_policy and projection['trace_status']['applied']:render_options['trace_axis_policy']='observed_status_timeline_v1'
        transport=config['search'].get('diagnostic_transport','pure_visual_with_text_candidates')
        if transport=='pure_visual_with_text_candidates':
            visual_packet=packet
        elif transport=='metric_text_with_rlg_visual_v1':
            if any(c['prompt']!='tournament_hybrid_metric_v1' for c in config['search'].get('conditions',[])):
                raise ValueError('metric-text transport requires its fixed hybrid guide')
            visual_packet=tournament_visual_packet(packet,'M')
        elif transport=='trace_text_with_mlg_visual_v1':
            if any(c['prompt']!='tournament_hybrid_trace_v1' for c in config['search'].get('conditions',[])):
                raise ValueError('trace-text transport requires its fixed hybrid guide')
            visual_packet=tournament_visual_packet(packet,'R',require_text=False)
        elif transport=='log_text_with_mrg_visual_v1':
            if any(c['prompt']!='tournament_hybrid_log_v1' for c in config['search'].get('conditions',[])):
                raise ValueError('log-text transport requires its fixed hybrid guide')
            visual_packet=tournament_visual_packet(packet,'L',require_text=False)
        elif transport=='topology_text_with_mrl_visual_v1':
            if any(c['prompt']!='tournament_hybrid_topology_v1' for c in config['search'].get('conditions',[])):
                raise ValueError('topology-text transport requires its fixed hybrid guide')
            visual_packet=tournament_visual_packet(packet,'G',require_text=False)
        else:raise ValueError('unknown diagnostic transport')
        spec=DashboardSpecV3(**render_options,fact_inventory_hash=visual_packet['fact_inventory_hash'])
        try:
            png,manifest=render_search_family(visual_packet,spec,config['search'],geometry)
        except Exception as exc:
            # A selector may legitimately rank complete content whose card does
            # not fit the frozen layout.  This is a selector-admissibility issue,
            # not permission to truncate evidence or alter the renderer.  Fall
            # back explicitly to the registered anchor selection and preserve an
            # audit of the requested intervention.  Other failures remain
            # fail-closed.
            capacity_error=(type(exc) is ValueError and
                str(exc)=='complete card contents cannot fit this layout')
            if config['search'].get('stage')=='tournament' and capacity_error:
                requested=selection
                selected,anchor_selection=search_select(pool,'balanced_additive_v1',
                    config['search'].get('metric_limit',8))
                packet,projection=project_log_summaries(selected)
                if config['search'].get('trace_projection')!='jaeger_us_to_ms_v1' or any((
                        status_policy,rate_policy,config['search'].get('temporal_projection'))):
                    raise ValueError('capacity fallback requires the frozen selection-only projection') from exc
                packet,projection['trace_units']=project_trace_ms(packet,row['dataset'])
                visual_packet=packet
                selection={**anchor_selection,'policy':policy,
                    'capacity_fallback':{'applied':True,
                        'reason':'selected complete cards exceed the frozen layout capacity',
                        'fallback_policy':'balanced_additive_v1',
                        'requested_selected_ids_hash':stable_hash(requested['selected_ids'])}}
                spec=DashboardSpecV3(**render_options,
                    fact_inventory_hash=visual_packet['fact_inventory_hash'])
                png,manifest=render_search_family(visual_packet,spec,config['search'],geometry)
            else:
                error={'case':case,'family':policy,'status':'failed','error':f'{type(exc).__name__}: {exc}'}
                write_json(output/case/f'{policy}.failure.json',error);attempts.append(error);continue
        conditions=config['search'].get('conditions',[{'prompt':p} for p in config['search'].get('prompts',[])])
        for condition in conditions:
            prompt=condition['prompt'];profile=condition.get('request_profile','legacy_v1')
            variant=policy+'__'+prompt+('__'+profile if 'request_profile' in condition else '');stem=output/case/variant
            parts=search_solver_parts(packet,png,manifest,log_summary=True,prompt_policy=prompt)
            atomic_write(stem.with_suffix('.png'),png);write_json(stem.with_suffix('.manifest.json'),manifest)
            write_json(stem.with_suffix('.packet.json'),packet)
            if visual_packet is not packet:write_json(stem.with_suffix('.visual.packet.json'),visual_packet)
            write_json(stem.with_suffix('.prompt.json'),[{**p,'png':'adjacent PNG'} if 'png' in p else p for p in parts])
            attempt={'case':case,'family':variant,'status':'rendered','source':str(path.relative_to(ROOT)),
                'source_file_hash':sha_file(path),'private':str((source/entry['private']).relative_to(ROOT)),
                'selection':selection,'projection':projection,'spec':asdict(spec),'png_sha256':stable_hash(png),'partition':partition}
            attempt['diagnostic_transport']=transport
            if visual_packet is not packet:
                text_region={'metric_text_with_rlg_visual_v1':'M','trace_text_with_mlg_visual_v1':'R',
                             'log_text_with_mrg_visual_v1':'L','topology_text_with_mrl_visual_v1':'G'}[transport]
                serializer={'M':'tournament_metric_text_v1','R':'tournament_trace_text_v1',
                            'L':'tournament_log_text_v1','G':'tournament_topology_text_v1'}[text_region]
                attempt['text_evidence']={'region':text_region,'serializer':serializer,
                    'fact_ids':sorted(f['fact_id'] for f in packet['facts'] if f['region']==text_region),
                    'visual_fact_ids':sorted(f['fact_id'] for f in visual_packet['facts'] if f['region']!='C')}
            if 'request_profile' in condition:attempt['request_profile']=profile
            if status_policy:attempt['supplemental_sources']=geometry['supplemental_sources']
            write_json(stem.with_suffix('.attempt.json'),attempt);attempts.append(attempt)
        print(case,policy,'rendered',flush=True)
    return attempts


def prepare_search_batch(gallery, output, config_path=SEARCH_CONFIG, model_tag='qwen3.8-27b'):
    """Commit already reviewed CPU previews; selection/rendering are not redone here."""
    from .utils import sha_file
    cfg=load_config(config_path);gallery=gallery.resolve();output=output.resolve()
    if cfg['search']['stage'] in ('development','tournament'):
        review=read_json(gallery/'review.json')
        if review.get('status')!='passed' or review.get('summary_hash')!=stable_hash(read_json(gallery/'summary.json')):
            raise ValueError('development gallery lacks matching CPU/visual review')
    index=read_json(ROOT/'RQs/RQ3/results/qualification_balanced_v14/train/index.json')
    inputs=ROOT/'RQs/RQ3/results/qualification_balanced_v14/train'
    attempts=read_json(gallery/'summary.json')['attempts'];tasks=[];files={}
    def include(path):
        path=path.resolve();relative=str(path.relative_to(ROOT));files[relative]=sha_file(path);return relative
    if cfg['search']['stage'] in ('development','tournament'):include(gallery/'review.json');include(gallery/'cohort.json')
    reuse={}
    if cfg['search']['stage']=='tournament' and (gallery/'reuse.json').exists():
        include(gallery/'reuse.json');reuse=read_json(gallery/'reuse.json').get(model_tag,{})
    round_=None
    if cfg['search']['stage']=='tournament':
        from .utils import tournament_register
        register=tournament_register(cfg);round_=register.rounds()[-1]
        if register.completion_policy():
            include(register.root/'top1_completion_v2.json')
            include(register.root/round_['id']/'registration.json')
        attempts=[a for a in attempts if a['case'] in round_['cohorts'][model_tag]]
    for attempt in attempts:
        if attempt['status']!='rendered':raise ValueError('preview has unresolved render failure')
        case=attempt['case'];family=attempt['family'];stem=gallery/case/family
        parts=read_json(stem.with_suffix('.prompt.json'));image=stem.with_suffix('.png')
        if sha_file(image)!=attempt['png_sha256']:raise ValueError('reviewed image changed')
        image_path=include(image)
        parts=[{'type':'image','image_path':image_path} if 'png' in p else p for p in parts]
        target=output/'private/parts'/f'{case}_{family}.json'
        if target.exists() and read_json(target)!=parts:raise ValueError('committed prompt changed')
        if not target.exists():write_json(target,parts)
        private=ROOT/attempt['private'] if 'private' in attempt else inputs/next(r for r in index['cases'] if r['opaque_incident_id']==case)['private']
        packet=read_json(stem.with_suffix('.packet.json'))
        if packet.get('pool_coverage',{}).get('entity_identity_policy','legacy_v1')!=cfg['harness'].get('entity_identity_policy','legacy_v1'):raise ValueError('gallery identity policy differs from search config')
        if packet.get('pool_coverage',{}).get('public_hosting',False)!=cfg['harness'].get('public_hosting',False):raise ValueError('gallery hosting policy differs from search config')
        if packet.get('pool_coverage',{}).get('public_membership',False)!=cfg['harness'].get('public_membership',False):raise ValueError('gallery membership policy differs from search config')
        tasks.append({'case':case,'variant':family,'parts':include(target),
                      'private':include(private),'candidates':packet['candidates']})
        if 'request_profile' in attempt:tasks[-1]['request_profile']=attempt['request_profile']
        if case in reuse:
            reference=reuse[case];origin=ROOT/reference['record'];record=read_json(origin)
            if sha_file(origin)!=reference['sha256']:raise ValueError('reuse source changed')
            include(origin)
            for relative in record['artifact_hashes']:include(origin.parent.parent/relative)
            tasks[-1]['reuse']=reference
        for p in (stem.with_suffix('.manifest.json'),stem.with_suffix('.packet.json'),
                  stem.with_suffix('.attempt.json'),ROOT/attempt['source']):include(p)
        visual_packet=stem.with_suffix('.visual.packet.json')
        if visual_packet.exists():include(visual_packet)
        for relative,digest in attempt.get('supplemental_sources',{}).items():
            path=ROOT/relative
            if sha_file(path)!=digest:raise ValueError('supplemental public source changed after rendering')
            include(path)
    for pattern in ('RQs/RQ3/src/**/*.py','packages/rq21_native/**/*.py','RQs/RQ3/configs/prompts/*.txt','RQs/RQ1_1/src/*.py','RQs/RQ2/src/*.py',
                    'RQs/RQ2_1/src/*.py','src/vlmrca/vlm/*.py','src/unified_scripts/*.py'):
        for p in ROOT.glob(pattern):include(p)
    if cfg['search'].get('selection_only_suite'):
        suite=validate_selection_only_config(cfg);include(ROOT/cfg['search']['selection_only_suite'])
        include(ROOT/suite['anchor_config'])
        for p in (ROOT/'packages/rq3_selection_native').rglob('*'):
            if p.is_file() and (p.suffix in ('.py','.md') or p.name=='LICENSE'):include(p)
    for p in (config_path,ROOT/'RQs/RQ3/configs/rq3.yaml',Path(__file__),
              ROOT/'src/vlmrca/run_state.py',ROOT/'src/vlmrca/training.py',ROOT/'src/vlmrca/entity_identity.py',ROOT/'src/vlmrca/metric_calendar.py',ROOT/'src/vlmrca/peer_metrics.py',ROOT/'configs/rca_scorer.yaml',
              ROOT/cfg['unified']['inference'],ROOT/'scripts/vllm_vlm/enable_attention_probe.sh',
              ROOT/'scripts/vllm_vlm/serve_canvasrca_local.sh',ROOT/'scripts/env_local.sh',ROOT/'scripts/env.sh'):include(p)
    spec={'schema':'RQ3SearchBatchV1','batch_id':output.name,'config_hash':stable_hash(cfg),
          'review_status':'passed','purpose':cfg['search']['stage']+' train-only search',
          'tasks':tasks,'artifact_hashes':files}
    spec['model_tag']=model_tag
    if round_:spec.update(tournament_round_hash=round_['hash'],purpose='adaptive tournament; no training')
    spec['spec_hash']=stable_hash(spec);target=output/'private/work_spec.json'
    if target.exists() and read_json(target)!=spec:raise ValueError('existing search manifest changed')
    if not target.exists():write_json(target,spec)
    print({'tasks':len(tasks),'spec':str(target),'spec_hash':spec['spec_hash']},flush=True)




@owned_gpu_process
def run_search_batch(output, *, retry_failed=False, config_path=SEARCH_CONFIG, wall_deadline=None, _gpu_lease_fd):
    import signal, socket, subprocess, sys, time
    from urllib.parse import urlparse
    from .utils import CallLedger, sha_file
    started=time.monotonic()
    output=output.resolve();cfg=load_config(config_path);spec=read_json(output/'private/work_spec.json')
    if not spec['tasks']:
        write_json(output/'summary.json',{'status':'complete','spec_hash':spec['spec_hash'],'outcomes':[],'accounting':{}});return
    model=spec.get('model_tag','qwen3.8-27b')
    recipe=VLLMInferenceConfig.load(ROOT/cfg['unified']['inference']).model(model)
    address=urlparse(recipe['base_url']);server=worker=None;errors=[];bounded_timeout=False
    if address.hostname not in ('localhost','127.0.0.1'):raise ValueError('non-local endpoint')
    with socket.socket() as probe:
        if probe.connect_ex((address.hostname,address.port or 80))==0:raise RuntimeError('endpoint already owned')
    for path,digest in spec['artifact_hashes'].items():
        if sha_file(ROOT/path)!=digest:raise ValueError('pre-committed input/code changed')
    ledger=CallLedger(output.parent/'search_calls.sqlite',None,scope=output.name,scope_limit=None if cfg['search']['stage']=='tournament' else cfg['search']['max_batch_calls'])
    recovery=ledger.recover_persisted(output);write_json(output/'recovery.json',recovery)
    failed={k for k,s in ledger.latest_states().items() if s in ('interrupted','infrastructure_failure')}
    if failed and not retry_failed:raise RuntimeError('inspect failed attempts, then use --retry-failed explicitly')
    for task in spec['tasks']:
        key=stable_hash([spec['batch_id'],{k:v for k,v in task.items() if k!='retry'}])
        if key in failed:task['retry']=True
    spec['spec_hash']=stable_hash({k:v for k,v in spec.items() if k!='spec_hash'})
    work=output/'private'/f"resume_{spec['spec_hash']}.json";write_json(work,spec)
    deadline=min(started+cfg['search']['wall_seconds'],wall_deadline or float('inf'))-35
    env={**os.environ,'CANVASRCA_STANDALONE':'1','CANVASRCA_ATTENTION_MODE':'off',
         'CANVASRCA_VLLM_CONFIG':str(ROOT/cfg['unified']['inference']),
         'CANVASRCA_ATTENTION_PROBE':'0','CANVASRCA_ATTENTION_PROBE_REQUIRED':'0',
         'CANVASRCA_SDK_MAX_RETRIES':'0','VLLM_BASE_URL':recipe['base_url'],'VLLM_API_KEY':'EMPTY',
         'RQ3_CONFIG_PATH':str(config_path.resolve()),'CANVASRCA_CACHE_ROOT':str(ROOT/'build/cache/rq3')}
    def interrupted(*_):raise KeyboardInterrupt('owner requested interruption')
    previous=signal.signal(signal.SIGTERM,interrupted)
    try:
        with (output/'server.log').open('ab') as log:
            server=subprocess.Popen(['bash','scripts/vllm_vlm/serve_canvasrca_local.sh',model],
                cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,pass_fds=(_gpu_lease_fd,))
        while not smoke_server_ready(recipe['base_url'],'EMPTY',recipe['served_model_name']):
            if server.poll() is not None:raise RuntimeError('server failed during startup')
            if time.monotonic()>=deadline:raise TimeoutError('bounded startup timeout')
            time.sleep(2)
        from vlmrca.run_state import verify_process_command
        live_argv=verify_process_command(server.pid,VLLMInferenceConfig.load(ROOT/cfg['unified']['inference']).server_argv(model))
        write_json(output/'runtime.json',{'recipe':recipe,'live_argv':live_argv,'attention':'off','server_pid':server.pid,
            'effective_config_hash':stable_hash(cfg),'started_epoch':time.time()})
        with (output/'worker.log').open('ab') as log:
            worker=subprocess.Popen([VLLMInferenceConfig.load(ROOT/cfg['unified']['inference']).data['deployment']['python'],'-u','-m','RQs.RQ3.src.main','search-worker',
                '--source',str(work),'--output',str(output)],cwd=ROOT,env=env,stdout=log,
                stderr=subprocess.STDOUT,start_new_session=True,pass_fds=(_gpu_lease_fd,))
        code=worker.wait(timeout=max(.01,deadline-time.monotonic()))
        if code:raise RuntimeError(f'search worker exited {code}')
    except (TimeoutError,subprocess.TimeoutExpired):bounded_timeout=True
    except BaseException as exc:errors.append(f'{type(exc).__name__}: {exc}')
    finally:
        signal.signal(signal.SIGTERM,previous);_stop_search_process(worker);_stop_search_process(server)
        ledger.recover_persisted(output)
        errors.extend(k for k,s in ledger.latest_states().items() if s=='infrastructure_failure')
        write_json(output/'qualification.json',{'status':'failed' if errors else 'passed',
            'errors':errors,'bounded_timeout':bounded_timeout,'seconds':time.monotonic()-started,
            'accounting':ledger.summary(),'note':'Only completed targets are live qualified.'})
    if errors:raise RuntimeError('; '.join(errors))


def bounded_smoke(*args, **kwargs):
    raise PermissionError("Predecessor supervisor retired; use the versioned search qualification route")


def qualify_tournament(config_path, output):
    import time
    cfg=load_config(config_path);deadline=time.monotonic()+600;phases=[]
    if cfg['search']['stage']!='qualification' or cfg['search']['max_batch_calls']>9:raise ValueError('unbounded two-model qualification')
    for model in cfg['tournament']['models']:
        if time.monotonic()>=deadline-35:break
        run_search_batch(output/model,config_path=config_path,wall_deadline=deadline)
        phases.append({'model':model,**read_json(output/model/'qualification.json')})
    write_json(output/'qualification.json',{'phases':phases,'status':'passed','bounded_timeout':len(phases)<2 or any(p['bounded_timeout'] for p in phases),
        'note':'Only persisted completed requests were exercised; no tournament retirement.'})


def manage_tournament(config, action, output=None):
    from .utils import tournament_register,sha_file
    from .gates import audit_call_artifacts
    from .exps import rca_schema
    from unified_scripts.rca_scorer import score_bound_response
    reg=tournament_register(config,allow_policy_migration=action=='adopt-policy')
    if action=='adopt-policy':return reg.state()
    if action=='status':return reg.state()
    if action=='register':
        if reg.completion_policy() and not config['tournament'].get('completion_policy'):
            raise ValueError('new rounds require the explicit AC@1-only successor config')
        return reg.register({'id':config['tournament'].get('method_id',config['tournament']['first_method']['id']),
                             'config_hash':stable_hash(config),'search':config['search']})
    spec=read_json(output/'private/work_spec.json');summary=read_json(output/'summary.json');r=reg.rounds()[-1]
    if action!='commit' or spec.get('tournament_round_hash')!=r['hash'] or summary['status']!='complete':
        raise ValueError('unregistered/incomplete tournament completion')
    if [{k:v for k,v in row['task'].items() if k!='retry'} for row in summary['outcomes']]!=spec['tasks']:
        raise ValueError('tournament summary targets changed')
    rows=[]
    for row in summary['outcomes']:
        record=read_json(output/row['record_path']);audit_call_artifacts(record,output)
        if record['record_hash']!=row['record_hash']:raise ValueError('outcome record changed')
        task=row['task'];private=read_json(ROOT/task['private'])
        if private['opaque_incident_id']!=task['case']:raise ValueError('private scoring identity changed')
        scored=score_bound_response(record['response'],task['candidates'],private['numeric_to_natural'],private['accepted'],rca_schema()['json_schema']['schema'],rca_scorer(config))
        if any(scored[k]!=row[k] for k in scored):raise ValueError('tournament score mismatch')
        paths=[output/row['record_path'],output/'summary.json',ROOT/task['private']]
        rows.append({'case':task['case'],'hits':{str(k):row['metrics'][f'ac@{k}']==1 for k in (1,3,5)},
                     'artifacts':{str(p.resolve().relative_to(ROOT)):sha_file(p) for p in paths}})
    return reg.commit(r['id'],spec['model_tag'],rows)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config",type=Path,default=os.environ.get("RQ3_CONFIG_PATH",DEFAULT_CONFIG))
    sub = parser.add_subparsers(dest="command",required=True)
    commands = {}
    for names, flags in [
        (("split","register","formal-plan","prepare"), ("output",)),
        (("preview","prepare-fixed","catalog-preflight","refresh-catalog","format-examples","qualify-reanonymization"), ("prepared","output")),
        (("train-rloo-batch","formal-worker","search-worker","qualify-storage","selection-audit","selection-preview"), ("source","output")),
        (("formal-learning","formal"), ("pools","output")),
        (("qualify-probabilities",), ("rollouts","output")),
        (("qualify-optimizer","train-sft"), ("examples","output")),
        (("composer-argv","check"), ()),
        (("tournament-status","tournament-register","tournament-adopt-policy"), ()),
        (("tournament-commit",), ("output",)),
    ]:
        for name in names:
            commands[name] = sub.add_parser(name)
            for flag in flags: commands[name].add_argument("--"+flag,type=Path,required=True)
    p = commands["prepare"]; p.add_argument("--count",type=int,default=2)
    p.add_argument("--partition",choices=("train","validation","eval","tournament"),default="validation")
    p.add_argument("--workers",type=int,default=2)
    p.add_argument("--pools-only",action="store_true")
    p.add_argument("--reuse-source",type=Path,action="append",default=[])
    p.add_argument("--cohort",type=Path)
    commands["format-examples"].add_argument("--qualification",action="store_true")
    commands["train-sft"].add_argument("--resume",type=Path)
    for name in ("smoke", "smoke-worker"):
        p = sub.add_parser(name)
        p.add_argument("--experiment", required=True)
        for flag in ("prepared", "controls", "output"):
            p.add_argument("--"+flag, type=Path, required=True)
        if name == "smoke-worker":
            p.add_argument("--role", choices=("composer", "solver"), required=True)
        else:
            p.add_argument("--optimizer-examples",type=Path)
            p.add_argument("--adapter-checkpoint",type=Path)
    args = parser.parse_args(argv)
    config = load_config(args.config)
    if args.command=='selection-audit':
        print(audit_selection_suite(config,args.source,args.output))
    elif args.command=='selection-preview':
        result=preview_selection_suite(config,args.source,args.output)
        print({'model_calls':0,'renders':len(result['attempts']),
               'cases':result['cases'],'summary':str(args.output/'summary.json')})
    elif args.command.startswith('tournament-'):
        result=manage_tournament(config,args.command.removeprefix('tournament-'),getattr(args,'output',None));print(result)
    elif args.command == "smoke":
        bounded_smoke(config,args.experiment,args.prepared,args.controls,args.output,args.optimizer_examples,args.adapter_checkpoint)
    elif args.command == "smoke-worker":
        smoke_worker(config,args.experiment,args.prepared,args.controls,args.output,args.role)
    elif args.command == "split":
        split = RQ3SegmentationAdapter(config).build(); write_json(args.output,split); print(split["counts"])
    elif args.command == "prepare":
        prepare(config,args.output,partition=args.partition,count=args.count,workers=args.workers,
                pools_only=args.pools_only,reuse_sources=args.reuse_source,cohort=args.cohort)
    elif args.command == "format-examples":
        format_examples(config,args.prepared,args.output,qualification=args.qualification)
    elif args.command == "qualify-probabilities":
        from .exps import qualify_probabilities
        print(qualify_probabilities(config,args.rollouts,args.output),flush=True)
    elif args.command == "train-rloo-batch":
        print(train_registered_rloo_batch(config,args.source,args.output),flush=True)
    elif args.command == "formal-worker":
        formal_worker(config,args.source,args.output)
    elif args.command == "search-worker":
        search_worker(config,args.source,args.output)
    elif args.command == "formal-learning":
        print(LearningLifecycle(config,args.output,args.pools).run(),flush=True)
    elif args.command == "formal":
        print(FormalLifecycle(config,args.output,args.pools).run(),flush=True)
    elif args.command == "qualify-storage":
        print(qualify_storage(args.source,args.output),flush=True)
    elif args.command == "qualify-reanonymization":
        print(qualify_reanonymization(config,args.prepared,args.output),flush=True)
    elif args.command in {"qualify-optimizer","train-sft"}:
        from .utils import read_format_examples
        index,rows = read_format_examples(args.examples)
        if args.command == "qualify-optimizer":
            if not index["qualification_only"]:
                raise ValueError("qualification cannot execute a formal optimizer schedule")
            from .exps import qualify_optimizer
            print(qualify_optimizer(config,rows,args.output),flush=True)
        else:
            if index["qualification_only"]:
                raise ValueError("disposable qualification samples are not formal SFT")
            from .gates import assert_formal_authorized, audit_training_rows
            from .utils import sft_resume_checkpoint
            assert_formal_authorized(config)
            split_hash=audit_training_rows(config,rows)
            checkpoint,completed=sft_resume_checkpoint(args.output,rows,config,split_hash)
            if args.resume is not None and (checkpoint is None or args.resume.resolve()!=checkpoint.resolve()):
                raise ValueError('explicit SFT resume is not the latest verified published checkpoint')
            if completed:
                print({'status':'already_complete','checkpoint':str(checkpoint),'new_optimizer_updates':0},flush=True)
                return
            from .exps import train_sft
            print(train_sft(config,rows,args.output,checkpoint),flush=True)
    elif args.command == "preview":
        preview(config,args.prepared,args.output)
    elif args.command == "prepare-fixed":
        prepare_fixed_baselines(config,args.prepared,args.output)
    elif args.command == "refresh-catalog":
        refresh_catalog(config, args.prepared, args.output)
    elif args.command == "composer-argv":
        recipe,tag = composer_recipe(config); print("\n".join(recipe.server_argv(tag)))
    elif args.command == "catalog-preflight":
        from .gates import catalog_preflight
        audit=catalog_preflight(config,args.prepared);write_json(args.output,audit);print(audit)
        if audit["status"]!="passed":raise SystemExit(2)
    elif args.command == "formal-plan":
        from .utils import formal_phase_plan
        plan=formal_phase_plan(RQ3SegmentationAdapter(config).build(),config)
        if args.output.exists() and read_json(args.output)!=plan:
            raise ValueError('preserve previous formal plan; choose a successor path')
        write_json(args.output,plan)
        print({'phases':len(plan['phases']),'planned_calls':plan['new_calls_max'],
               'plan_hash':plan['plan_hash'],'execution_started':False})
    elif args.command == "register":
        from .utils import registered_schedule, rloo_batches
        from .gates import audit_data_extension
        split=RQ3SegmentationAdapter(config).build()
        write_json(args.output/"private"/"data_audit.json",audit_data_extension(config,split))
        write_json(args.output/"private"/"split.json",split)
        schedule=registered_schedule(split,config)
        write_json(args.output/"private"/"schedule.json",schedule)
        for branch in config["rl"]["branches"]:
            write_json(args.output/"private"/f"{branch}.batches.json",rloo_batches(split,config,branch))
        write_json(args.output/"registration.json",{"split_hash":split["split_hash"],"counts":split["counts"],
                    "schedule_hash":stable_hash(schedule),"calls":schedule["new_calls_max"],"execution_enabled":False})
    elif args.command == "check":
        from .gates import parent_integrity, source_audit
        print({"parent":parent_integrity(),"source":source_audit()})


if __name__ == "__main__":
    main()
