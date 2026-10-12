"""CPU admission and a gated, not yet runtime-qualified single-call adapter.

Model dependencies load only after an independent execution credential passes.
"""
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
import math
import os

from .utils import ROOT, RESULTS, PREPARED, read, write, roster, public_packet, physical_cores


def canvas_options():
    return sorted(((w, h) for w in (3072, 4096) for h in (3072, 4096)),
                  key=lambda wh: (wh[0]*wh[1], wh[1], wh[0]))


def capacity_lower_bound(measurement):
    """Relax source bundles, header, gaps, packing: failure is conclusive.

    A lower bound passing is NOT admission. Real packing/readability and the
    processor still have to pass. This prevents an unnecessary all-arm build
    or GPU launch when even independent cards cannot fit.
    """
    by_width = {m['region_width']: m['cards'] for m in measurement['measurements']}
    strips = 1024 in by_width
    options = []
    for width, height in ([(4096, 3072), (4096, 4096)] if strips else canvas_options()):
        region_height = height if strips else height//2
        cards = by_width[width//4 if strips else width//2]
        area = sum(c['width']*c['height'] for c in cards)
        too_tall = [c['card'] for c in cards if c['height'] > region_height]
        options.append({'width': width, 'height': height, 'required_card_area': area,
                        'available_area': width*height, 'area_ratio': area/(width*height),
                        'oversized_cards': too_tall,
                        'necessary_capacity_pass': not too_tall and area <= width*height,
                        'min_font': min(c['min_font'] for c in cards),
                        'overflow_cards': [c['card'] for c in cards if c['overflow']]})
    return {'options': options, 'necessary_capacity_pass': any(o['necessary_capacity_pass'] for o in options)}


def measurement_worker(core, jobs, log):
    from renderer.measure import measure_jobs
    os.sched_setaffinity(0, {core})
    measure_jobs(jobs, log)
    return {'core': core, 'affinity': sorted(os.sched_getaffinity(0)), 'completed': True}


def measure_population(limit=None, workers=8):
    from renderer.utils import node_link_layout
    population = roster()
    if Counter(case['dataset'] for case in population) != {'aiops2022': 60, 'aiops2025': 60, 'aegislab': 100}:
        raise ValueError('Frozen population changed')
    if limit is not None:
        population = population[:limit]
    folder = RESULTS / ('capacity' if limit is None else 'capacity_probe')
    folder.mkdir(parents=True, exist_ok=True)
    # No labels, rankings or historic QA are read by packet compilation.
    jobs = []
    for case in population:
        packet = public_packet(case['base'])
        out = folder / case['oid']
        out.mkdir(parents=True, exist_ok=True)
        write(out/'packet.json', packet)
        cards = packet['evidence']['cards']
        inventories=[c for c in cards if c['kind']=='inventory' and c['title']=='Candidate IDs · exhaustive fixed order']
        if len(inventories)!=1:raise ValueError('Unique exhaustive candidate inventory absent')
        candidate_id=inventories[0]['id']
        jobs.append({'evidence': str(ROOT/case['base']/'evidence.json'),
                     'profile': 'source_scopes_v2',
                     'region_widths': [1024],
                     'output': str(out/'dom.json'), 'components': packet['components'],
                     'full_width_cards': [c['id'] for c in cards if c['kind'] == 'graph'] + [candidate_id],
                     'node_layouts': {str(w): {c['id']: node_link_layout(c, w, 18, tight=True) for c in cards if c['kind'] == 'graph'} for w in (1024,)}})
    cores = physical_cores(min(workers, len(jobs)))
    # All source files are frozen per-case exports; no cloudbed reads or shared
    # raw-source bottleneck. Interleave datasets across the physical workers.
    buckets = defaultdict(list)
    for case, job in zip(population, jobs, strict=True):
        buckets[case['dataset']].append(job)
    interleaved = []
    while any(buckets.values()):
        for name in sorted(buckets):
            if buckets[name]:
                interleaved.append(buckets[name].pop(0))
    with ProcessPoolExecutor(max_workers=len(cores)) as pool:
        futures = []
        for i, core in enumerate(cores):
            job_file = folder/f'jobs_{i}.json'
            write(job_file, interleaved[i::len(cores)])
            futures.append(pool.submit(measurement_worker, core, job_file, folder/f'worker_{i}.log'))
        completed = [f.result() for f in as_completed(futures)]
    rows = []
    for case in population:
        dom = read(folder/case['oid']/'dom.json')
        packet = read(folder/case['oid']/'packet.json')
        expected = set(packet['expected_bindings'])
        for measurement in dom['measurements']:
            originals = {c['id']: c['data'].get('details', []) for c in packet['evidence']['cards']}
            for card in measurement['cards']:
                restored = [{'name': c['name'], 'value': c['value']} for c in card['captions']]
                if restored != originals[card['card']]:
                    raise ValueError('Source caption content/order lost')
            actual = [b for c in measurement['cards'] for b in c['bindings']]
            if len(actual) != len(set(actual)) or set(actual) != expected:
                raise ValueError('DOM/source occurrence binding mismatch: '+case['oid'])
        rows.append({**case, **capacity_lower_bound(dom),
                     'fact_bindings_verified': len(expected), 'evidence_hash': packet['evidence_hash']})
    totals = {}
    for dataset in sorted({r['dataset'] for r in rows}):
        subset = [r for r in rows if r['dataset'] == dataset]
        ratios = sorted(r['options'][-1]['area_ratio'] for r in subset)
        totals[dataset] = {'n': len(subset), 'necessary_pass': sum(r['necessary_capacity_pass'] for r in subset),
                           'max_canvas_ratio_min': ratios[0], 'max_canvas_ratio_median': ratios[len(ratios)//2],
                           'max_canvas_ratio_max': ratios[-1]}
    result = {'schema': 'CapacityAdmissionV1', 'cases': rows, 'datasets': totals, 'workers': completed,
              'whole_population': limit is None, 'status': 'necessary_only_pass' if all(r['necessary_capacity_pass'] for r in rows) else 'capacity_failed',
              'model_calls': 0, 'gpu_started': False,
              'relaxations_for_lower_bound': ['no header area', 'no inter-card spacing', 'no source-bundle coupling', 'no fragmentation']}
    write(folder/'report.json', result)
    return result


def co_membership_distance(a, b, masses=None):
    if set(a) != set(b):
        raise ValueError('Different unit inventories')
    keys = sorted(a)
    masses = masses or {k: 1 for k in keys}
    changed = total = 0.
    for i, u in enumerate(keys):
        for v in keys[i+1:]:
            weight = masses[u]*masses[v]
            total += weight
            changed += weight*((a[u] == a[v]) != (b[u] == b[v]))
    return changed/total if total else 0.


def fill_background(original, protected, assignments, max_fraction=.05):
    """Equal merged-cell groups, minimum changes versus ORIGINAL GEOM."""
    n = len(original)
    if n % 4 or set(original) != {0, 1, 2, 3}:
        raise ValueError('Not four equal-able groups')
    capacity = n//4
    if Counter(original) != {g: capacity for g in range(4)}:
        raise ValueError('GEOM must have exactly equal groups')
    result = list(original)
    occupied = set()
    foreground = Counter()
    for unit, cells in protected.items():
        if occupied.intersection(cells) or len(cells) != len(set(cells)):
            raise ValueError('Source units overlap')
        group = assignments[unit]
        if group not in range(4) or any(c < 0 or c >= n for c in cells):
            raise ValueError('Invalid cell/group')
        occupied.update(cells)
        foreground[group] += len(cells)
        for cell in cells:
            result[cell] = group
    if any(foreground[g] > capacity for g in range(4)):
        return None
    available = {g: [i for i, old in enumerate(original) if i not in occupied and old == g] for g in range(4)}
    free = []
    missing = {}
    for g in range(4):
        need = capacity - foreground[g]
        free.extend(available[g][need:])
        missing[g] = max(0, need-len(available[g]))
    free.sort()
    cursor = 0
    for g in range(4):
        for cell in free[cursor:cursor+missing[g]]:
            result[cell] = g
        cursor += missing[g]
    if cursor != len(free) or Counter(result) != {g: capacity for g in range(4)}:
        raise AssertionError('Capacity conservation')
    moved = sum(result[i] != original[i] for i in range(n) if i not in occupied)
    return result if moved <= math.floor(max_fraction*n+1e-9) else None


def optimize_groups(initial, edges, original_cells, protected, max_moves=100, escape_cycles=False):
    """Same registered enumeration, with O(4) feasibility per proposal."""
    import numpy as np
    keys = sorted(initial); n = len(original_cells); cap = n//4
    sizes = np.array([len(protected[k]) for k in keys], dtype=np.int64)
    pos = {k: i for i, k in enumerate(keys)}
    weights = np.zeros((len(keys), len(keys)))
    for u, v, w in edges:
        if u != v:
            weights[pos[u], pos[v]] += w
            weights[pos[v], pos[u]] += w
    group = np.array([initial[k] for k in keys])
    occupied = {c for cells in protected.values() for c in cells}
    bg = np.bincount([original_cells[c] for c in range(n) if c not in occupied], minlength=4)
    def loads(g):
        return np.bincount(g, weights=sizes, minlength=4).astype(np.int64)
    def possible(load):
        return bool(np.all(load <= cap) and np.maximum(bg-(cap-load), 0).sum() <= math.floor(.05*n+1e-9))
    if not possible(loads(group)) or fill_background(original_cells, protected, initial) is None:
        raise ValueError('GEOM source closure invalid')
    def cut(g):
        return float(np.sum(weights * (g[:, None] != g[None, :]))/2)
    baseline = cut(group); history = []
    for _ in range(max_moves):
        scores = weights @ np.eye(4)[group]
        load = loads(group); best = None; gain = 0.
        for i, _ in enumerate(keys):
            old = group[i]
            for target in range(4):
                if target == old: continue
                improvement = round(float(scores[i, target]-scores[i, old]), 12)
                if improvement <= gain: continue
                trial = load.copy(); trial[old] -= sizes[i]; trial[target] += sizes[i]
                if possible(trial): best, gain = (i, target, None), improvement
        for i in range(len(keys)):
            for j in range(i+1, len(keys)):
                left, right = group[i], group[j]
                if left == right: continue
                improvement = round(float(scores[i,right]-scores[i,left]+scores[j,left]-scores[j,right]-2*weights[i,j]), 12)
                if improvement <= gain: continue
                trial = load.copy(); change = sizes[j]-sizes[i]
                trial[left] += change; trial[right] -= change
                if possible(trial): best, gain = (i, right, j), improvement
        if best is None and escape_cycles:
            # Equal-capacity heterogeneous source units can require a three-way
            # exchange to escape a two-swap local optimum. This still optimizes
            # ONLY the registered relation cut, never the admission distance.
            from itertools import combinations
            triples=np.array([(i,j,k) for i,j,k in combinations(range(len(keys)),3)
                              if len({group[i],group[j],group[k]})==3],dtype=np.int64)
            if len(triples):
                candidate_indices=np.repeat(triples,2,axis=0)
                oldgroups=group[candidate_indices]
                newgroups=np.empty_like(oldgroups)
                newgroups[0::2]=oldgroups[0::2][:,[1,2,0]]
                newgroups[1::2]=oldgroups[1::2][:,[2,0,1]]
                gains=(scores[candidate_indices,newgroups]-scores[candidate_indices,oldgroups]).sum(axis=1)
                a,b,c=candidate_indices.T
                gains-=weights[a,b]+weights[a,c]+weights[b,c]
                gains=np.round(gains,12)
                trial=np.repeat(load[None,:],len(candidate_indices),axis=0)
                rowids=np.arange(len(candidate_indices))
                for col in range(3):
                    size=sizes[candidate_indices[:,col]]
                    trial[rowids,oldgroups[:,col]]-=size
                    trial[rowids,newgroups[:,col]]+=size
                eligible=(trial<=cap).all(axis=1)&(np.maximum(bg[None,:]-(cap-trial),0).sum(axis=1)<=math.floor(.05*n+1e-9))&(gains>0)
                candidates=np.flatnonzero(eligible)
                if len(candidates):
                    chosen=candidates[np.argmax(gains[candidates])]
                    group[candidate_indices[chosen]]=newgroups[chosen]
                    history.append({'gain':float(gains[chosen]),'cut':cut(group),'move':'three_group_cycle'})
                    continue
        if best is None: break
        i, target, j = best
        if j is not None: group[j] = group[i]
        group[i] = target
        history.append({'gain': gain, 'cut': cut(group)})
    assignment = dict(zip(keys, map(int, group), strict=True))
    mapping = fill_background(original_cells, protected, assignment)
    if mapping is None: raise AssertionError('Count feasibility disagrees with exact map')
    return {'assignments': assignment, 'cells': mapping, 'moves': history,
            'cut_before': baseline, 'cut_after': cut(group),
            'cut_reduction': (baseline-cut(group))/baseline if baseline else 0.}



def optimize_groups_refined(initial, edges, original_cells, protected, max_moves=100):
    """Capacity-constrained best-prefix refinement, without gate/ink inputs.

    A deterministic Kernighan--Lin-style pass locks moved source units and
    permits temporary non-improving steps. Only its best STRICTLY improving
    prefix is committed. Every intermediate assignment satisfies the original
    group capacity and background cap. No seed search or admission optimization.
    """
    import numpy as np
    keys=sorted(initial); pos={k:i for i,k in enumerate(keys)}
    n=len(original_cells);cap=n//4;limit=math.floor(.05*n+1e-9)
    sizes=np.array([len(protected[k]) for k in keys],dtype=np.int64)
    weights=np.zeros((len(keys),len(keys)),dtype=np.float64)
    for u,v,w in edges:
        if not math.isfinite(w) or w<0:raise ValueError('Invalid edge weight')
        if u!=v:weights[pos[u],pos[v]]+=w;weights[pos[v],pos[u]]+=w
    occupied={c for cells in protected.values() for c in cells}
    bg=np.bincount([original_cells[i] for i in range(n) if i not in occupied],minlength=4)
    group=np.array([initial[k] for k in keys],dtype=np.int64)
    if fill_background(original_cells,protected,initial) is None:raise ValueError('Infeasible initial map')
    fixed=np.array([k.startswith('HEADER') for k in keys])
    def cut(g):return float((weights*(g[:,None]!=g[None,:])).sum()/2)
    def feasible(load):return (load<=cap).all(axis=1)&(np.maximum(bg[None,:]-(cap-load),0).sum(axis=1)<=limit)
    baseline=cut(group);history=[];accepted_steps=0;pass_audit=[]
    # At most 100 accepted source moves/exchanges, and at most 8 passes.
    for pass_id in range(8):
        start=group.copy();start_cut=cut(start);trial=group.copy();locked=fixed.copy()
        best_gain=0.;best_prefix=0;best_group=None;steps=[]
        for step in range(min(len(keys),max_moves-accepted_steps)):
            free=np.flatnonzero(~locked)
            if not len(free):break
            score=weights@np.eye(4)[trial]
            load=np.bincount(trial,weights=sizes,minlength=4).astype(np.int64)
            proposals=[];targets=[];gains=[];loads=[]
            for i in free:
                old=trial[i]
                for target in range(4):
                    if target==old:continue
                    l=load.copy();l[old]-=sizes[i];l[target]+=sizes[i]
                    proposals.append((i,-1));targets.append(target)
                    gains.append(score[i,target]-score[i,old]);loads.append(l)
            for ii,i in enumerate(free):
                for j in free[ii+1:]:
                    left,right=trial[i],trial[j]
                    if left==right:continue
                    l=load.copy();change=sizes[j]-sizes[i];l[left]+=change;l[right]-=change
                    proposals.append((i,j));targets.append(right)
                    gains.append(score[i,right]-score[i,left]+score[j,left]-score[j,right]-2*weights[i,j]);loads.append(l)
            if not proposals:break
            gains=np.round(np.asarray(gains),12);valid=np.flatnonzero(feasible(np.asarray(loads)))
            if not len(valid):break
            choice=valid[np.argmax(gains[valid])];i,j=proposals[choice];old=int(trial[i]);target=int(targets[choice])
            if j>=0:trial[j]=old;locked[j]=True
            trial[i]=target;locked[i]=True
            steps.append({'units':[keys[i]]+([keys[j]] if j>=0 else []),'gain':float(gains[choice]),'cut':cut(trial)})
            improvement=round(start_cut-cut(trial),12)
            if improvement>best_gain:
                best_gain=improvement;best_prefix=len(steps);best_group=trial.copy()
        pass_audit.append({'pass':pass_id,'explored_steps':len(steps),'accepted_prefix':best_prefix,'gain':best_gain})
        if best_group is None:break
        group=best_group;accepted_steps+=best_prefix
        history.append({'gain':best_gain,'cut':cut(group),'move':'best_prefix','steps':steps[:best_prefix]})
        if accepted_steps>=max_moves:break
    assignment=dict(zip(keys,map(int,group),strict=True));mapping=fill_background(original_cells,protected,assignment)
    if mapping is None:raise AssertionError('Prefix feasibility mismatch')
    if any(assignment[k]!=initial[k] for k in keys if k.startswith('HEADER')):raise AssertionError('Header moved')
    return {'assignments':assignment,'cells':mapping,'moves':history,'passes':pass_audit,
            'accepted_steps':accepted_steps,'cut_before':baseline,'cut_after':cut(group),
            'cut_reduction':(baseline-cut(group))/baseline if baseline else 0.}



def refinement_worker(core, rows, output):
    from .utils import digest
    os.sched_setaffinity(0,{core});result=[]
    for row in rows:
        # Reuse already-qualified geometry; never reopen/rewrite all PNGs.
        old=read(PREPARED/'grouping'/row['oid']/'partition.json')
        packet=read(PREPARED/'capacity'/row['oid']/'packet.json')
        units=old['source_units'];initial={u['id']:u['group'] for u in units}
        for g in range(4):initial['HEADER'+str(g)]=g
        original=old['maps']['GEOM'];protected=old['protected'];ink=old['foreground_mass']
        edges=unit_edges(packet,units)
        sem=optimize_groups_refined(initial,edges,original,protected)
        wrong,replacement,rewire=rewire_edges(packet,int(digest(['RQ42_SHAM_FIXED_V1',row['oid']])[:16],16))
        sham=optimize_groups_refined(initial,unit_edges(wrong,units),original,protected)
        mass={u['id']:len(u['cards']) for u in units};base={k:initial[k] for k in mass}
        answer={k:sem['assignments'][k] for k in mass};control={k:sham['assignments'][k] for k in mass}
        metrics={'card_distance':co_membership_distance(base,answer,mass),
                 'foreground_distance':co_membership_distance(base,answer,ink),'cut_reduction':sem['cut_reduction'],
                 'sham_card_distance':co_membership_distance(answer,control,mass),
                 'sham_foreground_distance':co_membership_distance(answer,control,ink),'sham_replacement':replacement}
        data={**row,**metrics,'sem_pass':metrics['card_distance']>=.2 and metrics['foreground_distance']>=.2 and sem['cut_reduction']>=.15,
              'sham_pass':metrics['sham_card_distance']>=.2 and metrics['sham_foreground_distance']>=.2 and replacement>=.5}
        write(output/row['oid']/'audit.json',{'summary':data,'semantic':sem,'sham':sham,'sham_audit':rewire,
            'geometry_source':str(PREPARED/'grouping'/row['oid']/'partition.json'),'gate_used_by_optimizer':False})
        result.append(data);print(row['oid'],data['sem_pass'],round(metrics['foreground_distance'],3),flush=True)
    return result


def refinement_audit(workers=8,probe=True):
    from .utils import RQ
    rows=roster();output=RQ/'results/partition_v4'/('refinement_probe' if probe else 'grouping')
    if probe:
        selected={r['oid'] for r in read(PREPARED/'ink_weight_probe.json')}
        rows=[r for r in rows if r['oid'] in selected]
    cores=physical_cores(min(workers,len(rows)))
    buckets=defaultdict(list)
    for row in rows:buckets[row['dataset']].append(row)
    interleaved=[]
    while any(buckets.values()):
        for ds in sorted(buckets):
            if buckets[ds]:interleaved.append(buckets[ds].pop(0))
    with ProcessPoolExecutor(max_workers=len(cores)) as pool:
        futures=[pool.submit(refinement_worker,c,interleaved[i::len(cores)],output) for i,c in enumerate(cores)]
        out=[r for f in as_completed(futures) for r in f.result()]
    stats={}
    for ds in sorted({r['dataset'] for r in out}):
        sub=[r for r in out if r['dataset']==ds]
        stats[ds]={'n':len(sub),'sem_pass':sum(r['sem_pass'] for r in sub),'sham_pass':sum(r['sham_pass'] for r in sub)}
    report={'schema':'BestPrefixAuditV4','datasets':stats,'cases':out,'probe':probe,
            'sem_qualified':not probe and all(r['sem_pass']>=.5*r['n'] for r in stats.values()),
            'sham_qualified':not probe and all(r['sham_pass']>=.5*r['n'] for r in stats.values()),
            'thresholds_unchanged':True,'model_calls':0,'gpu_started':False}
    write(output/'report.json',report);return report


def adjusted_card_sizes(packet, measured):
    from renderer.utils import node_link_layout
    graphs={c['id']:c for c in packet['evidence']['cards'] if c['kind']=='graph'}
    return [{**m,'height':max(m['height'],32*math.ceil(node_link_layout(graphs[m['card']],m['width'],18,tight=True)['min_height']/32))} if m['card'] in graphs else m for m in measured]


def source_units(packet, measured):
    """Close exact source records, never close merely equal entity/value."""
    import re
    cards = packet['evidence']['cards']; by_id = {c['id']: c for c in cards}
    parent = {c['id']: c['id'] for c in cards}
    def find(k):
        while parent[k] != k: k = parent[k]
        return k
    sources = defaultdict(set)
    for row in packet['source_mapping']:
        if not row['binding']: continue
        cid = row['binding'].split('.')[0]
        # Aggregated graph cells carry cross-record links; the whole graph is
        # a separate public unit, not a union of every endpoint record.
        if by_id[cid]['kind'] == 'graph': continue
        # Pair packets contain multiple distinct request-parent observations.
        match = re.match(r'^/(PAIR[0-9]+)(/|$)', row['path'])
        key = (row['source'], match.group(1) if match else '')
        sources[key].add(cid)
    for members in sources.values():
        first = sorted(members)[0]
        for cid in sorted(members)[1:]: parent[find(cid)] = find(first)
    groups = defaultdict(list)
    for c in cards: groups[find(c['id'])].append(c['id'])
    measure = {c['card']: c for c in adjusted_card_sizes(packet,measured)}
    directories=[c for c in cards if c['kind']=='inventory' and c['title']=='Candidate IDs · exhaustive fixed order']
    if len(directories)!=1:raise ValueError('Exact candidate directory is required')
    candidates=list(directories[0]['data']['identities'])
    catalog_ids={directories[0]['id']}|{c['id'] for c in cards if c['kind']=='inventory' and c['title']=='Observed entities'}
    order = {c: i for i, c in enumerate(candidates)}
    units = []
    for ids in groups.values():
        owners = set()
        for cid in ids:
            c = by_id[cid]
            if c['entity']: owners.add(c['entity'])
            elif c['kind'] == 'trace_joint': owners.update([c['data']['parent'],c['data']['child']])
            elif c['kind'] == 'inventory' and cid not in catalog_ids:
                owners.update(c['data']['identities'])
        widths = {measure[c]['width'] for c in ids}
        if len(widths) != 1: raise ValueError('Closed source has incompatible panel widths')
        units.append({'id': min(ids), 'cards': ids, 'owners': sorted(owners),
                      'width': int(next(iter(widths))), 'height': sum(measure[c]['height'] for c in ids),
                      'order': (min((order.get(e,len(order)) for e in owners),default=-1),
                                min(next(i for i,c in enumerate(cards) if c['id']==cid) for cid in ids))})
    return sorted(units, key=lambda u:(u['order'],u['id']))


def pack_units(units, height, header=32):
    # Source unit and card rectangles are 32px aligned, no invisible scaling.
    heights = [[header,header] for _ in range(4)]; placed = []
    for unit in units:
        width = unit['width']; found = None
        for g in range(4):
            cols = [0] if width == 1024 else [0,1]
            for col in cols:
                y = max(heights[g]) if width == 1024 else heights[g][col]
                if y+unit['height'] <= height:
                    found = (g,col,y); break
            if found: break
        if found is None: return pack_units_exact(units,height,header)
        g,col,y = found
        heights[g][col] = y+unit['height']
        if width == 1024: heights[g][1] = y+unit['height']
        placed.append({**unit,'x':g*1024+col*512,'y':y,'group':g})
    return placed


def unit_edges(packet, units, masses=None):
    edges = sorted({(e['kind'],e['source'],e['target']) for c in packet['evidence']['cards']
                    if c['kind']=='graph' for e in c['data']['edges']})
    allowed = {'calls','request_parent','hosts','owns','has_instance'}
    if any(kind not in allowed for kind,_,_ in edges): raise ValueError('Unregistered relation type')
    degrees_out = Counter((k,s) for k,s,t in edges)
    degrees_in = Counter((k,t) for k,s,t in edges)
    raw = {(k,s,t):1/math.sqrt(degrees_out[k,s]*degrees_in[k,t]) for k,s,t in edges}
    total = Counter()
    for (k,s,t),w in raw.items(): total[k] += w
    owners = defaultdict(list)
    for u in units:
        for owner in u['owners']: owners[owner].append(u['id'])
    weighted = Counter()
    for (kind,s,t),w in raw.items():
        pairs = [(u,v) for u in owners[s] for v in owners[t] if u != v]
        weights=[(masses[u]*masses[v]) if masses else 1. for u,v in pairs]
        denom=sum(weights)
        for (u,v),mass in zip(pairs,weights,strict=True):weighted[u,v] += w/total[kind]*mass/denom
    return [(u,v,w) for (u,v),w in sorted(weighted.items())]


def layout_population():
    rows = []
    for case in roster():
        folder = RESULTS/'capacity'/case['oid']
        packet = read(folder/'packet.json')
        cards = read(folder/'dom.json')['measurements'][0]['cards']
        units = source_units(packet,cards)
        placed = None
        for height in (3072,4096):
            placed = pack_units(units,height)
            if placed: break
        row = {**case, 'status':'packed' if placed else 'packing_failed','units':len(units)}
        if placed:
            row.update(height=height, placements=placed)
        rows.append(row)
    result = {'schema':'SourcePackingV2','cases':rows,'datasets':{},'model_calls':0}
    for name in sorted({r['dataset'] for r in rows}):
        subset = [r for r in rows if r['dataset']==name]
        result['datasets'][name] = {'n':len(subset),'packed':sum(r['status']=='packed' for r in subset)}
    write(RESULTS/'packing/report.json',result)
    return result


def grouping_probe_worker(core, rows):
    os.sched_setaffinity(0, {core})
    result = []
    for row in rows:
        if row['status'] != 'packed':
            result.append({'oid':row['oid'],'dataset':row['dataset'],'status':row['status']}); continue
        units = row['placements']; height = row['height']; cols = 128
        original = [(i % cols)//32 for i in range(cols*(height//32))]
        protected = {u['id']:[y*cols+x for y in range(u['y']//32,(u['y']+u['height'])//32)
                    for x in range(u['x']//32,(u['x']+u['width'])//32)] for u in units}
        initial = {u['id']:u['group'] for u in units}
        # Header is fixed and never lends diagnostic/instruction pixels as filler.
        for g in range(4):
            uid = 'HEADER'+str(g); initial[uid]=g;protected[uid]=list(range(g*32,(g+1)*32))
        packet = read(PREPARED/'capacity'/row['oid']/'packet.json')
        edges = unit_edges(packet,units)
        optimized = optimize_groups(initial,edges,original,protected)
        masses = {u['id']:len(u['cards']) for u in units}
        diagnostic = {u['id']:u['group'] for u in units}
        answer = {k:optimized['assignments'][k] for k in diagnostic}
        distance = co_membership_distance(diagnostic,answer,masses)
        result.append({'oid':row['oid'],'dataset':row['dataset'],'status':'probe',
                       'card_distance':distance,'cut_reduction':optimized['cut_reduction'],
                       'moves':len(optimized['moves']),'edges':len(edges),
                       'necessary_intervention_pass':distance>=.2 and optimized['cut_reduction']>=.15})
        write(RESULTS/'grouping_probe'/row['oid']/ 'groups.json',optimized)
    return result


def grouping_probe(workers=8):
    rows=read(RESULTS/'packing/report.json')['cases'];cores=physical_cores(workers)
    with ProcessPoolExecutor(max_workers=len(cores)) as pool:
        futures=[pool.submit(grouping_probe_worker,core,rows[i::len(cores)]) for i,core in enumerate(cores)]
        out=[r for f in as_completed(futures) for r in f.result()]
    result={'schema':'InterventionNecessaryProbeV2','cases':out,'datasets':{},'model_calls':0,'gpu_started':False}
    for name in sorted({r['dataset'] for r in out}):
        sub=[r for r in out if r['dataset']==name]
        result['datasets'][name]={'n':len(sub),'necessary_pass':sum(r.get('necessary_intervention_pass',False) for r in sub),
                                 'foreground_weighted_gate':'not_yet_measured'}
    write(RESULTS/'grouping_probe/report.json',result)
    return result


def pack_units_exact(units,height,header=32):
    """Deterministic feasibility fallback, preserving source order within columns.

    Size search allocates columns only. It never ranks diagnostic content and
    never changes cards/values. A bounded search failing is a real admission
    failure, not permission to drop a source unit.
    """
    tops=[[header,header] for _ in range(4)];wide=[]
    for u in units:
        if u['width']!=1024:continue
        options=[(max(tops[g]),g) for g in range(4) if max(tops[g])+u['height']<=height]
        if not options:return None
        y,g=min(options);tops[g]=[y+u['height']]*2;wide.append({**u,'x':g*1024,'y':y,'group':g})
    narrow=[u for u in units if u['width']==512]
    capacity=[height-h for pair in tops for h in pair]
    if sum(capacity)<sum(u['height'] for u in narrow):return None
    order=sorted(range(len(narrow)),key=lambda i:(-narrow[i]['height'],i));choices={};seen=set();visited=0
    def search(k):
        nonlocal visited
        visited+=1
        if visited>100000:return False
        if k==len(order):return True
        key=(k,tuple(sorted(capacity)))
        if key in seen:return False
        i=order[k];size=narrow[i]['height'];symmetry=set()
        for col in sorted(range(8),key=lambda c:(capacity[c],c)):
            if capacity[col]<size or capacity[col] in symmetry:continue
            symmetry.add(capacity[col]);capacity[col]-=size;choices[i]=col
            if search(k+1):return True
            capacity[col]+=size
        seen.add(key);return False
    if not search(0):return None
    placed=list(wide)
    for i,u in enumerate(narrow):
        g,col=divmod(choices[i],2);y=tops[g][col];tops[g][col]+=u['height']
        placed.append({**u,'x':g*1024+col*512,'y':y,'group':g})
    return placed


def build_design(packet,placement,measured=None):
    from renderer.operations.evidence_regions import apply
    if measured is None:measured=read(PREPARED/'capacity'/placement['oid']/'dom.json')['measurements'][0]['cards']
    heights={c['card']:c['height'] for c in adjusted_card_sizes(packet,measured)};panels=[];boxes=[]
    for unit in placement['placements']:
        y=unit['y']
        for cid in unit['cards']:
            panel={'id':'P'+cid,'type':'panel','card':cid,'component':packet['components'][cid]}
            if panel['component']=='graph.node_link':panel['node_layout']='layered_grid'
            panels.append(panel);boxes.append({'x':unit['x'],'y':y,'width':unit['width'],'height':heights[cid]});y+=heights[cid]
    design={'schema':'DashboardDesignV1','viewport':{'width':4096,'height':placement['height']},
            'theme':'dark','font_size':18,'gap':0,'padding':0,'scale':1,'readable_cards':'source_scopes_v2',
            'bindings':[],'indexing':{'visible':False,'start':1},'graph':{'show_isolates':True}}
    apply(design,panels,boxes)
    return design


def render_worker(core,rows):
    from renderer.main import render
    os.sched_setaffinity(0,{core});result=[]
    for row in rows:
        folder=RESULTS/'renders'/row['oid']
        if (folder/'manifest.json').exists():
            result.append({'oid':row['oid'],'status':read(folder/'manifest.json')['status']});continue
        packet=read(PREPARED/'capacity'/row['oid']/'packet.json');design=build_design(packet,row)
        write(RESULTS/'designs'/(row['oid']+'.json'),design)
        try:
            report=render(ROOT/row['base']/'evidence.json',RESULTS/'designs'/(row['oid']+'.json'),folder)
            result.append({'oid':row['oid'],'status':report['status']})
        except Exception as exc:
            result.append({'oid':row['oid'],'status':'failed','error':str(exc)})
        print(result[-1],flush=True)
    return result


def render_population(limit=None,workers=8):
    rows=read(RESULTS/'packing/report.json')['cases']
    if any(r['status']!='packed' for r in rows):raise ValueError('Full-population packing pending')
    if limit:rows=rows[:limit]
    cores=physical_cores(min(workers,len(rows)))
    with ProcessPoolExecutor(max_workers=len(cores)) as pool:
        futures=[pool.submit(render_worker,c,rows[i::len(cores)]) for i,c in enumerate(cores)]
        out=[r for f in as_completed(futures) for r in f.result()]
    write(RESULTS/('render_probe.json' if limit else 'render_report.json'),out)
    return Counter(r['status'] for r in out)


def rewire_edges(packet, seed):
    """Exactly 100*m seeded proposals; directed type-specific degrees retained."""
    import random
    from copy import deepcopy
    out=deepcopy(packet);rng=random.Random(seed);audit=[]
    for card in out['evidence']['cards']:
        if card['kind']!='graph':continue
        original=card['data']['edges'];pairs=defaultdict(set)
        for e in original:pairs[e['kind']].add((e['source'],e['target']))
        replacements=[]
        for kind,edge_set in sorted(pairs.items()):
            old=set(edge_set);sequence=sorted(edge_set)
            for _ in range(100*len(sequence)):
                if len(sequence)<2:break
                i,j=rng.sample(range(len(sequence)),2);a,b=sequence[i];c,d=sequence[j]
                proposed=((a,d),(c,b))
                if a==c or b==d or a==d or c==b or any(e in edge_set for e in proposed):continue
                edge_set.remove(sequence[i]);edge_set.remove(sequence[j]);edge_set.update(proposed)
                sequence[i],sequence[j]=proposed
            if Counter(a for a,b in old)!=Counter(a for a,b in edge_set) or Counter(b for a,b in old)!=Counter(b for a,b in edge_set):
                raise AssertionError('SHAM changed directed degree')
            outdegree=Counter(a for a,b in old);indegree=Counter(b for a,b in old)
            weights={e:1/math.sqrt(outdegree[e[0]]*indegree[e[1]]) for e in old}
            audit.append({'card':card['id'],'kind':kind,'count':len(old),
                          'replacement_weight':sum(weights[e] for e in old-edge_set),
                          'total_weight':sum(weights.values())})
            replacements.extend({'id':'e'+str(len(replacements)+i),'kind':kind,'source':a,'target':b}
                                for i,(a,b) in enumerate(sorted(edge_set)))
        card['data']['edges']=replacements
    weighted=[a['replacement_weight']/a['total_weight'] for a in audit if a['total_weight']]
    return out,sum(weighted)/len(weighted) if weighted else 0.,audit


def qualify_render_worker(core,rows,weight_by_ink=False,subdir='grouping'):
    import numpy as np
    from PIL import Image
    from .utils import digest
    os.sched_setaffinity(0,{core});result=[]
    for row in rows:
        folder=RESULTS/'renders'/row['oid'];packet=read(PREPARED/'capacity'/row['oid']/'packet.json')
        manifest=read(folder/'manifest.json')
        if manifest['status']!='passed':raise ValueError('Unqualified render '+row['oid'])
        actual=np.asarray(Image.open(folder/'dashboard.png').convert('RGB'))
        for g in range(4):
            assert np.array_equal(actual[:,g*1024:(g+1)*1024],np.asarray(Image.open(folder/f'region_{g}.png').convert('RGB')))
        readable=read(folder/'readability.json')
        if readable['min_font']<17.999:raise ValueError('Local glyph below floor')
        expected={c['id']+'.detail.'+str(i):(d['name'],d['value']) for c in packet['evidence']['cards'] for i,d in enumerate(c['data'].get('details',[]))}
        restored={c['binding']:(c['name'],c['value']) for c in readable['prefixes']}
        if expected!=restored:raise ValueError('Rendered scope/value loss')
        alpha=np.asarray(Image.open(folder/'card_foreground.png').convert('RGBA'))[:,:,3].astype(np.float64)/255
        units=row['placements'];cols=128;n=cols*(row['height']//32)
        original=[(i%cols)//32 for i in range(n)]
        protected={u['id']:[y*cols+x for y in range(u['y']//32,(u['y']+u['height'])//32) for x in range(u['x']//32,(u['x']+u['width'])//32)] for u in units}
        initial={u['id']:u['group'] for u in units};cardmass={u['id']:len(u['cards']) for u in units}
        ink={u['id']:float(alpha[u['y']:u['y']+u['height'],u['x']:u['x']+u['width']].sum()) for u in units}
        if any(v<=0 for v in ink.values()):raise ValueError('Empty source-unit foreground')
        for g in range(4):
            key='HEADER'+str(g);protected[key]=list(range(g*32,(g+1)*32));initial[key]=g
        semantic=optimize_groups(initial,unit_edges(packet,units,ink if weight_by_ink else None),original,protected)
        wrong,replacement,rewire=rewire_edges(packet,int(digest(['RQ42_SHAM_FIXED_V1',row['oid']])[:16],16))
        sham=optimize_groups(initial,unit_edges(wrong,units,ink if weight_by_ink else None),original,protected)
        base={k:initial[k] for k in cardmass};sem={k:semantic['assignments'][k] for k in cardmass};sh={k:sham['assignments'][k] for k in cardmass}
        sem_card=co_membership_distance(base,sem,cardmass);sem_ink=co_membership_distance(base,sem,ink)
        sham_card=co_membership_distance(sem,sh,cardmass);sham_ink=co_membership_distance(sem,sh,ink)
        metrics={'card_distance':sem_card,'foreground_distance':sem_ink,'cut_reduction':semantic['cut_reduction'],
                 'sham_card_distance':sham_card,'sham_foreground_distance':sham_ink,'sham_replacement':replacement}
        maps={'GEOM':original,'SEM':semantic['cells'],'SHAM':sham['cells']}
        labels={}
        for arm,mapping in maps.items():
            canonical={};identity=digest([canonical.setdefault(g,len(canonical)) for g in mapping])
            labels[arm]=labels.setdefault(identity,arm)
        payload={'schema':'QualifiedPartitionCPUDataV2','oid':row['oid'],'height':row['height'],
                 'protected':protected,'source_units':units,'foreground_mass':ink,'metrics':metrics,
                 'maps':maps,'sem_steps':semantic['moves'],'sham_steps':sham['moves'],'sham_audit':rewire,
                 'aliases':{a:labels[a] for a in maps},'pixel_sha256':__import__('hashlib').sha256(actual.tobytes()).hexdigest()}
        write(RESULTS/subdir/row['oid']/'partition.json',payload)
        result.append({'oid':row['oid'],'dataset':row['dataset'],**metrics,
                       'sem_pass':sem_card>=.2 and sem_ink>=.2 and semantic['cut_reduction']>=.15,
                       'sham_pass':sham_card>=.2 and sham_ink>=.2 and replacement>=.5})
    return result


def qualify_render_population(workers=8,weight_by_ink=False):
    subdir='grouping_ink_weighted' if weight_by_ink else 'grouping'
    rows=read(RESULTS/'packing/report.json')['cases'];cores=physical_cores(workers)
    with ProcessPoolExecutor(max_workers=len(cores)) as pool:
        futures=[pool.submit(qualify_render_worker,c,rows[i::len(cores)],weight_by_ink,subdir) for i,c in enumerate(cores)]
        out=[r for f in as_completed(futures) for r in f.result()]
    stats={}
    for ds in sorted({r['dataset'] for r in out}):
        sub=[r for r in out if r['dataset']==ds]
        stats[ds]={'n':len(sub),'sem_pass':sum(r['sem_pass'] for r in sub),'sham_pass':sum(r['sham_pass'] for r in sub)}
    result={'schema':'PartitionPopulationAdmissionV2','cases':out,'datasets':stats,
            'sem_qualified':all(r['sem_pass']>=.5*r['n'] for r in stats.values()),
            'sham_qualified':all(r['sham_pass']>=.5*r['n'] for r in stats.values()),'model_calls':0,'gpu_started':False}
    result['relation_unit_weighting']='normalized_diagnostic_ink' if weight_by_ink else 'uniform_source_units'
    write(RESULTS/subdir/'report.json',result)
    return result


def qa_render_worker(core,rows):
    from renderer.main import render
    from .utils import qa_packet
    os.sched_setaffinity(0,{core});out=[]
    for row in rows:
        oid=row['oid'];packet=read(PREPARED/'capacity'/oid/'packet.json');qa=qa_packet(packet,oid)
        write(RESULTS/'qa'/oid/'audit.json',qa)
        if qa['status']!='ready':out.append({'oid':oid,'status':'not_applicable'});continue
        design=read(PREPARED/'designs'/(oid+'.json'));design['question_colors']=qa['targets']
        write(RESULTS/'qa'/oid/'design.json',design)
        try:
            report=render(ROOT/row['base']/'evidence.json',RESULTS/'qa'/oid/'design.json',RESULTS/'qa'/oid/'render')
            main=read(PREPARED/'renders'/oid/'manifest.json')
            if report['rectangles']!=main['rectangles']:raise ValueError('QA moved source units')
            out.append({'oid':oid,'status':report['status'],'questions':len(qa['applicable_questions'])})
        except Exception as exc:out.append({'oid':oid,'status':'failed','error':str(exc)})
    return out


def prepare_qa(workers=8):
    from .utils import mechanism_roster
    rows=mechanism_roster();cores=physical_cores(workers)
    write(RESULTS/'qa/cohort.json',rows)
    with ProcessPoolExecutor(max_workers=len(cores)) as pool:
        futures=[pool.submit(qa_render_worker,c,rows[i::len(cores)]) for i,c in enumerate(cores)]
        out=[r for f in as_completed(futures) for r in f.result()]
    report={'schema':'CPUQuestionInputsV2','cases':out,'counts':dict(Counter(r['status'] for r in out)),
            'question_count':sum(r.get('questions',0) for r in out),'model_calls':0}
    write(RESULTS/'qa/report.json',report);return report


def processor_worker(core,rows):
    import torch
    import numpy as np
    from PIL import Image
    from transformers import AutoProcessor
    from .utils import RQ,sha
    os.sched_setaffinity(0,{core});torch.set_num_threads(1)
    model_path='/home/lglsj/CanvasRCA/models/Qwen3.8-27B'
    processor=AutoProcessor.from_pretrained(model_path,local_files_only=True)
    prompts=read(RQ/'configs/prompts_v2.json');out=[]
    for row in rows:
        oid=row['oid'];records=[]
        jobs=[('RCA',PREPARED/'renders'/oid,prompts['rca'],prompts['system'])]
        qa_path=RESULTS/'qa'/oid/'audit.json'
        if qa_path.exists() and read(qa_path)['status']=='ready':
            jobs.append(('QA',RESULTS/'qa'/oid/'render',read(qa_path)['instruction'],prompts['qa_system']))
        for task,folder,instruction,system in jobs:
            totals={}
            for kind in ('FULL','NATIVE4'):
                paths=[folder/'dashboard.png'] if kind=='FULL' else [folder/f'region_{g}.png' for g in range(4)]
                images=[Image.open(p).convert('RGB') for p in paths]
                content=[{'type':'text','text':instruction}]+[{'type':'image','image':image} for image in images]
                messages=[{'role':'system','content':system},{'role':'user','content':content}]
                text=processor.apply_chat_template(messages,tokenize=False,add_generation_prompt=True,enable_thinking=False)
                batch=processor(text=[text],images=images,return_tensors='pt')
                grid=batch['image_grid_thw'];image_tokens=int((grid.prod(dim=1)//4).sum());input_tokens=int(batch['input_ids'].shape[1])
                for image,g in zip(images,grid.tolist(),strict=True):
                    if g[0]!=1 or image.size!=(g[2]*16,g[1]*16):raise ValueError('Unexpected resize or temporal grid')
                if image_tokens>16384 or input_tokens+8192>40960:raise ValueError('Registered context/image cap')
                # Every patch is present and the tensor has finite normalized RGB values.
                if batch['pixel_values'].shape[0]!=int(grid.prod(dim=1).sum()) or not torch.isfinite(batch['pixel_values']).all():
                    raise ValueError('Processor lost/corrupted patch values')
                totals[kind]=image_tokens
                records.append({'task':task,'representation':kind,'input_tokens':input_tokens,'image_tokens':image_tokens,
                                'grid_thw':grid.tolist(),'no_resize':True,'pixel_tensor_shape':list(batch['pixel_values'].shape),
                                'processor_config_sha256':sha(__import__('pathlib').Path(model_path)/'preprocessor_config.json')})
                del batch;[im.close() for im in images]
            if totals['FULL']!=totals['NATIVE4']:raise ValueError('Native four-image token budget differs')
        write(RESULTS/'processor'/oid/'tokens.json',records);out.append({'oid':oid,'dataset':row['dataset'],'records':records})
    return out


def processor_population(workers=8):
    rows=roster();cores=physical_cores(workers)
    with ProcessPoolExecutor(max_workers=len(cores)) as pool:
        futures=[pool.submit(processor_worker,c,rows[i::len(cores)]) for i,c in enumerate(cores)]
        out=[r for f in as_completed(futures) for r in f.result()]
    allrows=[r for case in out for r in case['records']]
    report={'schema':'ActualCPUProcessorAdmissionV2','status':'passed','cases':len(out),'requests':len(allrows),
            'max_input_tokens':max(r['input_tokens'] for r in allrows),'max_image_tokens':max(r['image_tokens'] for r in allrows),
            'no_resize':all(r['no_resize'] for r in allrows),'gpu_used':False,'model_weights_loaded':False,'model_calls':0}
    write(RESULTS/'processor/report.json',report);return report


class LocalSingleCallSolver:
    """Frozen local solver; constructor is unreachable under CPU-only authority."""
    def __init__(self, attention_folder, deadline=None):
        from .gates import require_execution_qualification
        require_execution_qualification()  # before importing or allocating a model
        import torch
        import xgrammar as xgr
        from transformers import AutoProcessor,Qwen3_5ForConditionalGeneration
        from vlmrca.vlm.passive_summary import AttentionStore,PassiveAttentionTap
        from .utils import rca_schema
        self.torch=torch;torch.set_num_threads(8);torch.cuda.set_per_process_memory_fraction(.75)
        path='/home/lglsj/CanvasRCA/models/Qwen3.8-27B'
        self.processor=AutoProcessor.from_pretrained(path,local_files_only=True)
        self.model=Qwen3_5ForConditionalGeneration.from_pretrained(path,dtype=torch.bfloat16,attn_implementation='sdpa',local_files_only=True).to('cuda').eval()
        compiler=xgr.GrammarCompiler(xgr.TokenizerInfo.from_huggingface(self.processor.tokenizer,vocab_size=self.model.config.text_config.vocab_size))
        self.grammar=compiler.compile_json_schema(rca_schema(True),any_whitespace=False)
        self.qa_grammar=compiler.compile_builtin_json_grammar()
        self.store=AttentionStore(attention_folder);self.tap=PassiveAttentionTap(self.store);self.tap.install(self.model)
        self.last_usage=None;self.deadline=deadline;self.partial_path=None
    def bind_transaction(self,path):self.partial_path=path
    def __call__(self,request):
        from contextlib import nullcontext
        from time import monotonic
        from PIL import Image
        from transformers import LogitsProcessorList,StoppingCriteriaList
        from xgrammar.contrib.hf import LogitsProcessor
        from vlmrca.vlm.passive_summary import RankingPrefixGreedy
        from vlmrca.vlm.vision_partition import partition_vision
        from .utils import digest
        if self.deadline is not None and monotonic()>=self.deadline:raise TimeoutError('Logical smoke deadline')
        torch=self.torch;images=[Image.open(p).convert('RGB') for p in request['images']]
        messages=[{'role':'system','content':request['system']},{'role':'user','content':
            [{'type':'text','text':request['instruction']}]+[{'type':'image','image':im} for im in images]}]
        began=monotonic()
        text=self.processor.apply_chat_template(messages,tokenize=False,add_generation_prompt=True,enable_thinking=False)
        batch=self.processor(text=[text],images=images,return_tensors='pt');[im.close() for im in images]
        n=batch['input_ids'].shape[1]
        if n+8192>40960:raise ValueError('Context contract changed')
        processors=[LogitsProcessor(self.grammar if request['task']=='RCA' else self.qa_grammar)]
        if request['task']=='RCA':processors.append(RankingPrefixGreedy(self.processor.tokenizer))
        context=partition_vision(self.model.model.visual,request['groups']) if request['operation']=='partition_blocks_0_22_v1' else nullcontext()
        batch={k:v.to('cuda') for k,v in batch.items()};torch.manual_seed(request['seed'])
        collection=request.get('attention_regions')
        if request.get('attention_manifest'):
            from .utils import attention_regions
            geometry=read(request['attention_manifest'])
            collection=attention_regions(batch['input_ids'][0].detach().cpu().numpy(),self.model.config.image_token_id,geometry,native=len(images)==4)
        if collection:
            ids,names=collection;self.tap.begin(request['identity'],torch.tensor(ids,device='cuda',dtype=torch.long),names,digest([list(map(int,ids)),names]))
        stream=PartialGeneration(self.processor.tokenizer,self.partial_path,n)
        stop=DeadlineStop(self.deadline)
        try:
            with torch.inference_mode(),context:
                output=self.model.generate(**batch,max_new_tokens=8192,do_sample=True,temperature=1.,top_p=.95,top_k=0,
                                          logits_processor=LogitsProcessorList(processors),streamer=stream,
                                          stopping_criteria=StoppingCriteriaList([stop]))
        finally:
            self.tap.end();stream.flush()
        if stop.expired or (self.deadline is not None and monotonic()>=self.deadline):
            raise TimeoutError('Logical smoke deadline during generation; partial is not a complete answer')
        generated=output[0,n:];response=self.processor.tokenizer.decode(generated,skip_special_tokens=True)
        self.last_usage={'input_tokens':n,'output_tokens':int(generated.numel()),'image_tokens':int(batch['image_grid_thw'].prod(dim=1).sum())//4,
                         'processor_and_model_seconds':monotonic()-began,'attention_error':self.tap.error,'attention_missed':self.tap.missed,
                         'maximum_gpu_allocated_bytes':torch.cuda.max_memory_allocated(),
                         'stop_reason':'length' if int(generated.numel())==8192 else 'eos'}
        return response
    def close(self):
        self.tap.close();self.store.close();del self.model


def cold_materialize(item,out_root):
    """Actual deployment cold path: read public package through answer validation.

    The caller starts its continuous clock before invoking this function. No
    incident render/token cache is used. Registration artifacts bind identity,
    not a shortcut around the registered deployment work.
    """
    from pathlib import Path
    from renderer.main import render
    from .utils import RQ,digest,input_identity,attention_regions
    oid=item['oid'];case=next(r for r in roster() if r['oid']==oid)
    packet=public_packet(case['base'])
    registered=read(PREPARED/'capacity'/oid/'packet.json')
    if packet['evidence_hash']!=registered['evidence_hash']:raise ValueError('Frozen public facts changed')
    folder=Path(out_root)/item['key'];folder.mkdir(parents=True,exist_ok=False)
    placement,measured=cold_compile_geometry(packet,case,folder)
    design=build_design(packet,placement,measured);prompts=read(RQ/'configs/prompts_v2.json')
    task=item['task'];instruction=prompts['rca'];system=prompts['system']
    if task=='QA':
        from .utils import qa_packet
        qa=qa_packet(packet,oid);design['question_colors']=qa['targets'];instruction=qa['instruction'];system=prompts['qa_system']
    write(folder/'design.json',design)
    manifest=render(ROOT/case['base']/'evidence.json',folder/'design.json',folder/'render')
    units=placement['placements'];cols=128;height=placement['height']
    original=[(i%cols)//32 for i in range(cols*(height//32))]
    protected={u['id']:[y*cols+x for y in range(u['y']//32,(u['y']+u['height'])//32) for x in range(u['x']//32,(u['x']+u['width'])//32)] for u in units}
    initial={u['id']:u['group'] for u in units}
    for g in range(4):protected['HEADER'+str(g)]=list(range(g*32,(g+1)*32));initial['HEADER'+str(g)]=g
    groups=[]
    if item['arm']=='GEOM':groups=original
    elif item['arm'] in {'SEM','SHAM'}:
        objective=packet
        if item['arm']=='SHAM':objective=rewire_edges(packet,int(digest(['RQ42_SHAM_FIXED_V1',oid])[:16],16))[0]
        groups=optimize_groups_refined(initial,unit_edges(objective,units),original,protected)['cells']
    identity=input_identity(item['arm'],manifest,groups,[system,instruction],task)
    if identity!=item['identity']:raise ValueError('Cold input differs from frozen request')
    paths=[folder/'render/dashboard.png'] if item['arm']!='NATIVE4' else [folder/f'render/region_{g}.png' for g in range(4)]
    from .utils import mechanism_roster
    measured_oids={r['oid'] for r in mechanism_roster()}
    return {'identity':identity,'system':system,'instruction':instruction,'images':list(map(str,paths)),
            **({'attention_manifest':str(folder/'render/manifest.json')} if oid in measured_oids else {}),
            'operation':'partition_blocks_0_22_v1' if item['arm'] in {'GEOM','SEM','SHAM'} else 'full',
            'groups':groups,'task':task,'seed':42}


def cold_compile_geometry(packet,case,folder):
    from renderer.measure import measure_jobs
    from renderer.utils import node_link_layout
    cards=packet['evidence']['cards']
    candidate=next(c['id'] for c in cards if c['kind']=='inventory' and c['title']=='Candidate IDs · exhaustive fixed order')
    job={'evidence':str(ROOT/case['base']/'evidence.json'),'profile':'source_scopes_v2','region_widths':[1024],
         'output':str(folder/'dom.json'),'components':packet['components'],
         'full_width_cards':[c['id'] for c in cards if c['kind']=='graph']+[candidate],
         'node_layouts':{'1024':{c['id']:node_link_layout(c,1024,18,tight=True) for c in cards if c['kind']=='graph'}}}
    write(folder/'jobs.json',[job]);measure_jobs(folder/'jobs.json',folder/'measure.log')
    measured=read(folder/'dom.json')['measurements'][0]['cards'];units=source_units(packet,measured)
    for height in (3072,4096):
        placements=pack_units(units,height)
        if placements:return {**case,'height':height,'placements':placements},measured
    raise ValueError('Cold complete source layout does not fit')


def cold_cpu_regression():
    """Real compiler/renderer plus offline provider, covering all request paths."""
    from .utils import CallSession, RQ, mechanism_roster
    from time import monotonic
    import json
    queue=read(RESULTS/'queue.json')['items'];rows=mechanism_roster()
    chosen={ds:next(r['oid'] for r in rows if r['dataset']==ds and read(RESULTS/'qa'/r['oid']/'audit.json')['status']=='ready')
            for ds in ('aiops2022','aiops2025','aegislab')}
    matrix=[('aiops2022','SEM','RCA'),('aiops2025','FULL','RCA'),('aegislab','GEOM','QA'),
            ('aiops2022','NATIVE4','QA'),('aiops2025','SHAM','RCA')]
    folder=RESULTS/'offline_cold';out=[]
    for ds,arm,task in matrix:
        oid=chosen[ds];item=next(q for q in queue if q['oid']==oid and q['arm']==arm and q['task']==task)
        if (folder/(item['key']+'.json')).exists():out.append(read(folder/(item['key']+'.json')));continue
        packet=read(PREPARED/'capacity'/oid/'packet.json')
        candidates=next(c['data']['identities'] for c in packet['evidence']['cards'] if c['title']=='Candidate IDs · exhaustive fixed order')
        qa=read(RESULTS/'qa'/oid/'audit.json')
        class OfflineProvider:
            last_usage={'synthetic':True,'input_tokens':0,'output_tokens':0}
            def __call__(self,request):
                if request['task']=='QA':return json.dumps(qa['gold'])
                return json.dumps({'services':candidates[:5],'reason':'offline transaction test','confidence':'low'})
        context=qa if task=='QA' else {'candidates':candidates,'numeric_to_natural':{s:s for s in candidates},'accepted':[candidates[0]]}
        session=CallSession(folder/'sessions'/item['key'],OfflineProvider(),limit=1)
        start=monotonic()
        try:
            response=session.run(item['key'],lambda:cold_materialize(item,folder/'materialized'),context)
            assert response['request_hash']==item['identity']
            assert session.run(item['key'],lambda:1/0,context)==response
            assert response['outcome']['status'] not in {'model_failure','infrastructure_failure'}
        finally:session.close()
        record={'oid':oid,'arm':arm,'task':task,'status':'passed','seconds':monotonic()-start,
                'new_model_calls':0,'offline_provider_calls':1,'complete_input_identity_equal':True}
        write(folder/(item['key']+'.json'),record);out.append(record)
    report={'status':'passed','cases':out,'model_calls':0,'gpu_started':False,'fixture_scores_are_not_scientific_results':True}
    write(folder/'report.json',report);return report


class DeadlineStop:
    """Passive stop; the parent watchdog also covers loading/prefill/rendering."""
    def __init__(self,deadline):self.deadline=deadline;self.expired=False
    def __call__(self,input_ids,scores,**kwargs):
        from time import monotonic
        self.expired=self.deadline is not None and monotonic()>=self.deadline
        return self.expired


class PartialGeneration:
    """Checkpoint output IDs every two seconds; never stores prompt tokens."""
    def __init__(self,tokenizer,path,input_tokens):
        from time import monotonic
        self.tokenizer=tokenizer;self.path=path;self.input_tokens=input_tokens
        self.ids=[];self.first=True;self.last=monotonic();self.ended=False
    def put(self,value):
        from time import monotonic
        if self.first:self.first=False;return
        self.ids.extend(value.reshape(-1).detach().cpu().tolist())
        if monotonic()-self.last>=2:self.flush()
    def flush(self):
        from time import monotonic
        if self.path is not None:
            write(self.path,{'status':'uncommitted_partial','generation_returned':self.ended,
                  'input_tokens':self.input_tokens,'output_tokens':len(self.ids),'token_ids':self.ids,
                  'response':self.tokenizer.decode(self.ids,skip_special_tokens=True)})
        self.last=monotonic()
    def end(self):self.ended=True;self.flush()


def register_smoke():
    """Fixed hash cases reused from CPU cold-path tests; no outcomes consulted."""
    from .utils import RQ,mechanism_roster,sha,digest
    queue=read(RESULTS/'queue.json')['items'];rows=mechanism_roster()
    datasets=('aiops2022','aiops2025','aegislab')
    chosen={ds:next(r['oid'] for r in rows if r['dataset']==ds and read(RESULTS/'qa'/r['oid']/'audit.json')['status']=='ready') for ds in datasets}
    matrix=[('aiops2022','SEM','RCA'),('aiops2025','GEOM','RCA'),('aegislab','FULL','RCA'),
      ('aiops2022','NATIVE4','QA'),('aiops2025','SEM','QA'),('aegislab','GEOM','QA'),
      ('aiops2022','SHAM','RCA'),('aiops2025','NATIVE4','RCA'),('aegislab','SEM','RCA'),
      ('aiops2022','FULL','QA'),('aiops2025','GEOM','QA'),('aegislab','SEM','QA'),
      ('aiops2022','FULL','RCA'),('aiops2025','FULL','RCA'),('aegislab','NATIVE4','RCA'),
      ('aiops2022','GEOM','RCA'),('aiops2025','SEM','RCA'),('aegislab','SHAM','RCA')]
    items=[];owners={}
    for ds,arm,task in matrix:
        item=dict(next(q for q in queue if q['oid']==chosen[ds] and q['arm']==arm and q['task']==task))
        item['dataset']=ds;item['reference']=owners.get(item['identity']);owners.setdefault(item['identity'],item['key']);items.append(item)
    result={'schema':'RQ42SmokeRegistrationV1','chosen':chosen,'items':items,'calls_maximum':18,'seconds':600,
      'timeouts_pass':False,'formal_enabled':False,'rca_calls':12,'qa_calls':6,
      'cpu_queue_sha256':sha(RESULTS/'queue.json'),'model_identity_sha256':sha(RESULTS/'model_identity.json'),
      'selection':'first ready case per dataset in fixed mechanism hash order; identical to offline cold-path cohort',
      'backend':'local Transformers BF16 SDPA; registered visual encoder hooks; no API/network',
      'recipe':'frozen RQ42 generation identities; max8192,context40960,temperature1,top_p.95,seed42,gpu_fraction.75',
      'gates':'protocol/infrastructure/operator/persistence/coverage; no MRR or QA accuracy gate',
      'feature_check':'real checkpoint, tiny tensor: K1 identity, K4 relabel invariance, finite outputs and hook restoration'}
    path=RQ/'configs/smoke_v1.json'
    if path.exists() and read(path)!=result:raise ValueError('Registered smoke is immutable')
    write(path,result);return result


def real_weight_operator_check(solver):
    """Three distinct operations and K1/relabel controls, no language generation."""
    from vlmrca.vlm.vision_partition import partition_vision
    torch=solver.torch;vision=solver.model.model.visual;c=vision.config
    torch.manual_seed(42)
    x=torch.randn(16,c.in_channels*c.temporal_patch_size*c.patch_size*c.patch_size,device='cuda',dtype=torch.bfloat16)
    grid=torch.tensor([[1,4,4]],device='cuda');groups=[0,1,2,3]
    def feature():return vision(x,grid).pooler_output
    with torch.inference_mode():
        full=feature()
        with partition_vision(vision,[0]*4):one=feature()
        with partition_vision(vision,groups):partitioned=feature()
        with partition_vision(vision,[3,2,1,0]):renamed=feature()
        restored=feature()
    if not all(torch.isfinite(v).all() for v in (full,one,partitioned,renamed,restored)):raise ValueError('Nonfinite real vision feature')
    if not torch.equal(full,one) or not torch.equal(full,restored) or not torch.equal(partitioned,renamed):raise ValueError('Real partition identity/relabel/restoration check failed')
    return {'status':'passed','full_blocks':len(vision.blocks),'dtype':str(full.dtype),'shape':list(full.shape),
            'K1_exact':True,'relabel_exact':True,'restored_exact':True,
            'partition_max_abs_delta':float((full-partitioned).abs().max()),'language_model_calls':0,
            'scope':'tiny real-weight vision feature; full-size execution measured by subsequent real-case requests'}


def smoke_worker():
    from time import monotonic
    import traceback
    from .gates import require_execution_qualification
    from .utils import RQ,CallSession,INDEX,smoke_paths
    require_execution_qualification('smoke')
    root,registration_path=smoke_paths();state=read(root/'clock.json');deadline=state['deadline_monotonic']
    registration=read(registration_path);solver=None;session=None
    if (root/'execution_overlay.json').exists():
        overlay=read(root/'execution_overlay.json')
        registration={**registration,'items':[i for i in registration['items'] if i['key'] not in overlay['omitted_redundant_QA']]}
    if monotonic()>=deadline:raise TimeoutError('Expired logical smoke before model loading')
    try:
        session=CallSession(root/'execution',None,limit=18,offline=False)  # own lock before loading weights
        write(root/'progress.json',{'status':'model_loading','completed':0,'total':len(registration['items'])})
        solver=LocalSingleCallSolver(root/'attention',deadline=deadline)
        session.provider=solver
        write(root/'operator.json',real_weight_operator_check(solver))
        historical=read(INDEX)['cases']
        for i,item in enumerate(registration['items']):
            if monotonic()>=deadline:raise TimeoutError('Logical smoke deadline before next request')
            write(root/'progress.json',{'status':'running','completed':i,'total':len(registration['items']),
                    'current':item['key'],'task':item['task'],'elapsed_seconds':monotonic()-state['started_monotonic']})
            oid=item['oid'];old=historical[oid]
            if item['task']=='QA':context=read(RESULTS/'qa'/oid/'audit.json')
            else:
                private=read(ROOT/old['private'])
                context={'candidates':old['candidates'],'numeric_to_natural':private['numeric_to_natural'],'accepted':private['accepted_labels']}
            retry=session.calls.latest_states().get(item['key']) in {'interrupted','infrastructure_failure'}
            result=session.run(item['key'],lambda:cold_materialize(item,root/'materialized'),context,reference=item['reference'],retry=retry)
            print('COMMITTED',i+1,item['key'],result['outcome']['status'],result.get('usage'),flush=True)
        solver.close();solver=None
        audit=verify_smoke(root,registration)
        if monotonic()>deadline:raise TimeoutError('Logical smoke deadline includes saving and validation')
        write(root/'verification.json',audit)
        if registration.get('inherit_completed_from'):
            write(root/'coverage.json',combined_smoke_coverage(root,registration))
        if monotonic()>deadline:raise TimeoutError('Logical smoke deadline includes combined coverage verification')
        write(root/'worker_complete.json',{'status':'passed','elapsed_seconds':monotonic()-state['started_monotonic']})
    except BaseException as exc:
        write(root/'worker_error.json',{'status':'failed','error':repr(exc),'traceback':traceback.format_exc()})
        raise
    finally:
        if session is not None:session.close()
        if solver is not None:solver.close()


def verify_smoke(root,registration):
    from .utils import sha
    # Artifact hashes and registered identity are checked in addition to the
    # host's central scorer. Model mistakes remain recorded outcomes, not retries.
    from vlmrca.vlm.passive_summary import AttentionStore
    rows=[]
    for item in registration['items']:
        result=read(root/'execution/completed'/(item['key']+'.json'))
        if result['request_hash']!=item['identity']:raise ValueError('Committed request identity drift')
        if not result.get('reference'):
            request=read(root/'execution/requests'/(item['key']+f"__call{result['attempt_id']}.json"))
            manifest=read(root/'materialized'/item['key']/'render/manifest.json')
            from .utils import input_identity
            if input_identity(item['arm'],manifest,request['groups'],[request['system'],request['instruction']],item['task'])!=item['identity']:
                raise ValueError('Actual smoke request differs from frozen input')
            expected=[manifest['png_sha256']] if item['arm']!='NATIVE4' else [r['sha256'] for r in manifest['region_exports']]
            if [sha(p) for p in request['images']]!=expected:raise ValueError('Actual image bytes changed')
            usage=result['usage']
            if usage['input_tokens']+8192>40960 or usage['image_tokens']>16384:raise ValueError('Runtime token limit')
            for p,checksum in result['artifact_hashes'].items():
                if sha(root/'execution'/p)!=checksum:raise ValueError('Trajectory integrity')
        rows.append({'key':item['key'],'task':item['task'],'arm':item['arm'],'dataset':item['dataset'],
              'outcome':result['outcome'],'usage':result['usage'],'cold_seconds':result['continuous_cold_seconds']})
    summaries=list((root/'attention').glob('*.json'))
    if any(p.stat().st_size>65536 for p in summaries) or AttentionStore.storage_ceiling()>10**9:raise ValueError('Attention disk cap')
    return {'status':'passed','positions':len(rows),'rows':rows,'attention_records':len(summaries),
      'attention_bytes':sum(p.stat().st_size for p in summaries),'attention_storage_ceiling_10000':AttentionStore.storage_ceiling(),
      'model_accuracy_used_as_gate':False,'GPU_operator':read(root/'operator.json')}


def supervise_smoke(resume_startup=False):
    """Single-use clock; no restart resets the 18-call/600-second logical smoke."""
    import os,sys,time,signal,subprocess
    from .gates import require_execution_qualification
    from .utils import RQ,sha,smoke_paths
    from vlmrca.run_state import DurableCallRegister
    require_execution_qualification('smoke')
    root,registration_path=smoke_paths()
    if not resume_startup:root.mkdir(exist_ok=False)
    registration=read(registration_path)
    if registration['calls_maximum']!=18 or registration['seconds']!=600:raise ValueError('Logical smoke limits')
    began=time.monotonic();deadline=began+600
    if resume_startup:
        if registration_path.name!='smoke_v1.json':raise RuntimeError('Supplemental round clock cannot restart')
        clock=read(root/'clock.json');began=clock['started_monotonic'];deadline=clock['deadline_monotonic']
        ledger=DurableCallRegister(root/'execution/calls.sqlite',limit=18,scope='rq42')
        counts=ledger.summary()
        if counts.get('complete',0) or counts.get('started',0) or time.monotonic()>=deadline:raise RuntimeError('Startup continuation requires no generated answers and remaining original time')
        interruptions=sum(counts.values())
        if interruptions>1:raise RuntimeError('Further runtime repair needs separately authorized qualification')
        archive=root/('startup_failure_'+str(len(list(root.glob('startup_failure_*')))+1));archive.mkdir(exist_ok=False)
        if interruptions:
            # One pre-generation attempt was spent. Omit the LAST repeated QA
            # interface, preserving all five RCA arms, four QA arms and datasets.
            seen=set();redundant=[]
            for item in registration['items']:
                if item['task']=='QA':
                    if item['arm'] in seen:redundant.append(item['key'])
                    seen.add(item['arm'])
            omitted=redundant[-1:]
            write(root/'execution_overlay.json',{'omitted_redundant_QA':omitted,'spent_pre_generation_attempts':interruptions,
              'reason':'numpy attention hash failure before generate; retain original 18 attempts/600 seconds, all interface coverage',
              'new_model_responses_at_revision':0})
            for folder in (root/'materialized').iterdir():
                if not (root/'execution/completed'/(folder.name+'.json')).exists():os.replace(folder,archive/folder.name)
        for name in ('worker.log','worker_error.json','report.json','owned_process.json','progress.json'):
            if (root/name).exists():os.replace(root/name,archive/name)
        write(root/'startup_repair.json',{'cpu_receipt_sha256':sha(RESULTS/'qualification_complete.json'),'clock_reset':False})
    else:write(root/'clock.json',{'started_monotonic':began,'deadline_monotonic':deadline,'started_epoch':time.time(),
      'cpu_receipt_sha256':sha(RESULTS/'qualification_complete.json'),'registration_sha256':sha(registration_path),
      'supervisor_pid':os.getpid(),'scope':'single logical smoke; no clock reset; full run prohibited'})
    with (root/'worker.log').open('x') as stream:
        child=subprocess.Popen([sys.executable,'-m','RQs.RQ4_2.src.main','smoke-worker'],cwd=ROOT,
                               stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
        write(root/'owned_process.json',{'pid':child.pid,'pgid':child.pid,'supervisor_pid':os.getpid()})
        timed_out=False
        try:
            while child.poll() is None:
                remaining=deadline-time.monotonic()
                if remaining<=0:timed_out=True;break
                time.sleep(min(1,remaining))
        finally:
            if child.poll() is None:
                os.killpg(child.pid,signal.SIGTERM)
                try:child.wait(timeout=3)
                except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
    ledger=DurableCallRegister(root/'execution/calls.sqlite',limit=18,scope='rq42')
    ledger.interrupt_scope('GPU smoke owner stopped without durable completion')
    passed=not timed_out and child.returncode==0 and (root/'worker_complete.json').exists() and (root/'verification.json').exists()
    if passed:
        expected=len(registration['items'])-(len(read(root/'execution_overlay.json')['omitted_redundant_QA']) if (root/'execution_overlay.json').exists() else 0)
        passed=read(root/'verification.json').get('status')=='passed' and read(root/'verification.json').get('positions')==expected
        if registration.get('inherit_completed_from'):
            passed=passed and (root/'coverage.json').exists() and read(root/'coverage.json').get('status')=='passed'
    result={'status':'passed' if passed else 'failed','timeout':timed_out,'worker_exit_code':child.returncode,
      'elapsed_seconds':time.monotonic()-began,'calls':ledger.summary(),
      'committed':len(list((root/'execution/completed').glob('*.json'))),'registered_positions':len(registration.get('items',[])),
      'formal_started':False,'owned_worker_stopped':child.poll() is not None,
      'cpu_receipt_sha256':sha(RESULTS/'qualification_complete.json'),'registration_sha256':sha(registration_path)}
    if registration.get('inherit_completed_from'):
        result.update(qualification_mode='affected_paths_plus_compatible_previous_checks',
          inherited_round_status=read(RESULTS/registration['inherit_completed_from']/'report.json')['status'],
          inherited_positions=registration['inherited_positions'],scope=registration['scope'])
    write(root/'report.json',result);write(RESULTS/'gpu_smoke_complete.json',result)
    # Archive the consumed authorization; no persistent execution permission.
    activation=RQ/'configs/activation.json'
    if activation.exists():os.replace(activation,root/'consumed_activation.json')
    return result


def supplement_compatibility():
    """Reuse qualified inputs/answers only when generation semantics are unchanged."""
    import ast,tarfile
    from .utils import RQ,sha
    prior=RESULTS/'gpu_smoke_v1'
    receipt=read(RESULTS/'pre_supplement_1/qualification_complete.json')
    allowed={'exps.py':{'smoke_worker','supervise_smoke'},'utils.py':set()}
    checked=[]
    with tarfile.open(prior/'executed_source_snapshot.tar.gz','r:gz') as archive:
        for name,exceptions in allowed.items():
            path=RQ/'src'/name;member=str(path.relative_to(ROOT))
            old=archive.extractfile(member).read().decode()
            def definitions(text):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(text).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
            a,b=definitions(old),definitions(path.read_text())
            for key,value in a.items():
                if key not in exceptions:
                    if b.get(key)!=value:raise ValueError('Inherited generation path changed: '+name+':'+key)
                    checked.append(name+':'+key)
    for path,value in receipt['source_hashes'].items():
        if path.startswith('RQs/RQ4_2/src/'):continue
        if sha(ROOT/path)!=value:raise ValueError('Inherited input/model/renderer/scorer dependency changed: '+path)
    return {'status':'passed','unchanged_definitions':checked,'new_changes':'bounded scope routing, verification and CPU tests only',
      'old_receipt_sha256':sha(RESULTS/'pre_supplement_1/qualification_complete.json'),
      'old_snapshot_sha256':sha(prior/'executed_source_snapshot.tar.gz'),
      'old_review_sha256':sha(prior/'completed_artifact_review.json'),'new_model_calls':0}


def combined_smoke_coverage(root,registration):
    """Join trusted completion markers; never regenerate prior identical calls."""
    from .utils import RQ,sha
    compatibility=supplement_compatibility()
    inherited=RESULTS/registration['inherit_completed_from']
    old_review=read(inherited/'completed_artifact_review.json')
    if old_review['status']!='passed' or sha(inherited/'completed_artifact_review.json')!=registration['inherited_review_sha256']:
        raise ValueError('Prior artifact review is not bound to this supplement')
    reviewed={r['key'] for r in old_review['rows']}
    original=RQ/'configs/smoke_v1.json'
    if sha(original)!=registration['base_registration_sha256']:raise ValueError('Original smoke matrix changed')
    rows=[];old_count=0;new_count=0
    for item in read(original)['items']:
        path=root/'execution/completed'/(item['key']+'.json');fresh=path.exists()
        if not fresh:
            path=inherited/'execution/completed'/(item['key']+'.json')
            if item['key'] not in reviewed or sha(path)!=registration['inherited_marker_hashes'].get(item['key']):
                raise ValueError('Missing or unreviewed inherited completion')
            old_count+=1
        else:new_count+=1
        result=read(path)
        if result['request_hash']!=item['identity']:raise ValueError('Coverage request identity mismatch')
        rows.append({'key':item['key'],'identity':item['identity'],'marker':str(path),
                     'sha256':sha(path),'reused':not fresh})
    if old_count!=registration['inherited_positions'] or new_count!=len(registration['items']):
        raise ValueError('Supplemental coverage cardinality changed')
    return {'status':'passed','required_positions':len(rows),'inherited':old_count,'new':new_count,
      'positions':rows,'compatibility':compatibility,'prior_smoke_remains_failed':True,
      'interpretation':'All original qualification checks covered through compatible partial results plus newly authorized affected checks'}


def formal_validate(item,request,usage):
    """Commit-time qualification of a NEW/recovered input, never bulk on resume."""
    from pathlib import Path
    from .utils import input_identity,sha
    manifest_path=Path(request['images'][0]).parent/'manifest.json'
    manifest=read(manifest_path)
    actual=input_identity(item['arm'],manifest,request['groups'],[request['system'],request['instruction']],item['task'])
    expected=[manifest['png_sha256']] if item['arm']!='NATIVE4' else [v['sha256'] for v in manifest['region_exports']]
    if actual!=item['identity'] or request['identity']!=actual or [sha(p) for p in request['images']]!=expected:
        raise ValueError('Formal model-visible identity / PNG integrity failed')
    if usage is not None:
        if (usage['input_tokens']+8192>40960 or usage['image_tokens']>16384 or usage['output_tokens']>8192
            or min(usage['input_tokens'],usage['output_tokens'],usage['image_tokens'])<0):
            raise ValueError('Formal processor/response budget mismatch')
    return {'status':'passed','identity':actual,'images':expected,'usage_checked':usage is not None}


def formal_prior_calls():
    """Read actual charged smoke ledgers, not a resettable progress counter."""
    import sqlite3
    rows=[]
    for root in sorted(RESULTS.glob('gpu_smoke*')):
        path=root/'execution/calls.sqlite'
        if not path.is_file():continue
        with sqlite3.connect(f'file:{path}?mode=ro',uri=True) as db:
            count=db.execute('SELECT count(*) FROM calls').fetchone()[0]
            pending=db.execute("SELECT count(*) FROM calls WHERE state='started'").fetchone()[0]
        if pending:raise ValueError('Unreconciled prior smoke calls')
        rows.append({'scope':root.name,'attempts':count})
    return {'rows':rows,'attempts':sum(r['attempts'] for r in rows)}


def formal_loop(root,registration,provider_factory,materialize,context,validate,
                budget_guard=lambda session:None,install_signals=False):
    """Single GPU owner; identical loop used by offline crash/restart tests.

    No model is loaded for completed phases, references, or durable replies.
    Signals request drain; sudden process/power loss is recovered on next start.
    Known runtime/integrity errors fail closed and require a diagnosed repair.
    """
    import signal,traceback
    from time import time
    from pathlib import Path
    from .utils import FormalSession,process_identity,sha
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    session=FormalSession(root/'execution',None,limit=registration['formal_attempt_cap'])
    solver=None;handlers={};items=registration['items'];keys={r['key'] for r in items}
    def progress(status,current=None):
        completed={p.stem for p in (root/'execution/completed').glob('*.json')}
        if completed-keys:raise ValueError('Unknown formal completion keys')
        value={'status':status,'completed':len(completed),'total':len(items),'current':current,
               'calls':session.calls.summary(),'updated_unix':time(),'pid':os.getpid()}
        write(root/'progress.json',value);return value
    def drain_signal(signum,frame):
        write(root/'execution/PAUSE',{'signal':signum,'requested_unix':time()})
    try:
        frozen=root/'registration.json'
        if frozen.exists() and read(frozen)!=registration:raise ValueError('Formal resume registration differs')
        if not frozen.exists():write(frozen,registration)
        write(root/'owner.json',process_identity(os.getpid()))
        marker=root/'phase_complete.qwen.json'
        if marker.exists():
            phase=read(marker)
            if phase['registration_sha256']!=sha(frozen):raise ValueError('Completed phase registration mismatch')
            return phase
        if (root/'BLOCKED.json').exists():raise RuntimeError('Known infrastructure failure requires diagnosis: '+str(root/'BLOCKED.json'))
        if install_signals:
            for sig in (signal.SIGTERM,signal.SIGINT):
                handlers[sig]=signal.signal(sig,drain_signal)
        recovery=session.recover()
        write(root/'recovery'/f'{time_ns_id()}.json',recovery)
        if (root/'execution/PAUSE').exists():return progress('paused')
        progress('starting')
        for item in items:
            done=session.completed(item['key'])
            if done is not None:
                if done['request_hash']!=item['identity']:raise ValueError('Frozen completed identity mismatch')
                continue
            if (root/'execution/PAUSE').exists():break
            states=session.calls.latest_states()
            if states.get(item['key'])=='infrastructure_failure':raise RuntimeError('Known failed request needs explicit repair')
            if not item.get('reference') and states.get(item['key'])!='complete' and solver is None:
                budget_guard(session)
                progress('model_loading',item['key'])
                # A killed request can leave an attention record even without a
                # committed reply. Preserve it; the retry gets a fresh namespace.
                solver=provider_factory(root/'attention'/time_ns_id());session.provider=solver
            progress('running',item['key'])
            result=session.run_item(item,materialize,lambda:context(item),validate,
                                    before_call=lambda:budget_guard(session))
            if result.get('status')=='paused':break
            print('COMMITTED',item['key'],result.get('outcome',{}).get('status'),flush=True)
            progress('running')
        progress('draining')
        if solver is not None:
            closing=solver;solver=None;closing.close()
        completed={p.stem for p in (root/'execution/completed').glob('*.json')}
        if completed!=keys:return progress('paused')
        # Audit only small completion records. Images/trajectories were checked
        # at each commit; reopening their full graph would defeat fast resume.
        rows=[]
        for item in items:
            record=session.completed(item['key'])
            if record['request_hash']!=item['identity'] or record['input_validation']['status']!='passed':
                raise ValueError('Final completion-header audit failed')
            rows.append({'key':item['key'],'oid':item['oid'],'arm':item['arm'],'task':item['task'],
                         'reference':record.get('reference'),'outcome':record['outcome'],'usage':record['usage'],
                         'continuous_cold_seconds':record.get('continuous_cold_seconds'),
                         'recovered_reply':record.get('recovered_reply',False)})
        write(root/'results.json',{'positions':len(rows),'rows':rows,'calls':session.calls.summary(),
                                  'references':sum(bool(r['reference']) for r in rows)})
        with session.calls.connect() as db:
            db.execute('PRAGMA wal_checkpoint(FULL)')
        phase={'status':'complete','positions':len(rows),'registration_sha256':sha(frozen),
               'results_sha256':sha(root/'results.json'),'calls':session.calls.summary(),'writers_drained':True,
               'completed_unix':time()}
        write(marker,phase);progress('complete');return phase
    except BaseException as exc:
        # SIGKILL/power loss cannot enter here: those started calls remain
        # interrupted/recoverable. An observed Python failure is not silently
        # converted into a power-loss retry.
        with session.calls.connect() as db:
            pending=db.execute("SELECT id FROM calls WHERE state='started'").fetchall()
        for (attempt,) in pending:session.calls.finish(attempt,{'error':repr(exc)},state='infrastructure_failure')
        failure={'error':repr(exc),'traceback':traceback.format_exc(),'time':time()}
        write(root/'errors'/f'{time_ns_id()}.json',failure)
        if not (root/'BLOCKED.json').exists():write(root/'BLOCKED.json',failure)
        progress('blocked');raise
    finally:
        try:
            if solver is not None:solver.close()
        finally:
            for sig,handler in handlers.items():signal.signal(sig,handler)
            session.close()


def time_ns_id():
    from time import time_ns
    return str(time_ns())+'_'+str(os.getpid())


def run_formal():
    from .utils import RQ,INDEX
    from .gates import require_execution_qualification
    require_execution_qualification('formal')
    registration=read(RQ/'configs/formal_v1.json');root=RESULTS/'formal_v1'
    historical=None
    def context(item):
        nonlocal historical
        if item['task']=='QA':return read(RESULTS/'qa'/item['oid']/'audit.json')
        # Private data loads after generation and never goes to the provider.
        if historical is None:historical=read(INDEX)['cases']
        old=historical[item['oid']];private=read(ROOT/old['private'])
        return {'candidates':old['candidates'],'numeric_to_natural':private['numeric_to_natural'],
                'accepted':private['accepted_labels']}
    def budget(session):
        prior=formal_prior_calls()
        if prior!=registration['prior_smoke_calls']:raise ValueError('Prior call ledger changed; requalify accounting')
        spent=sum(session.calls.summary().values())
        if prior['attempts']+spent>=registration['combined_call_ceiling']:raise RuntimeError('Cumulative experiment call cap')
    return formal_loop(root,registration,LocalSingleCallSolver,cold_materialize,context,formal_validate,
                       budget_guard=budget,install_signals=True)


def launch_formal(resume=False):
    """Detach locally; never execute as a side effect of readiness or CPU tests."""
    import fcntl,subprocess,sys,time
    from .utils import RQ,formal_status
    from .gates import require_execution_qualification
    require_execution_qualification('formal')
    root=RESULTS/'formal_v1';root.mkdir(exist_ok=True)
    with (root/'launcher.lock').open('a') as launcher:
        fcntl.flock(launcher,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (root/'phase_complete.qwen.json').exists():return read(root/'phase_complete.qwen.json')
        execution=root/'execution';execution.mkdir(exist_ok=True)
        with (execution/'owner.lock').open('a') as owner:
            fcntl.flock(owner,fcntl.LOCK_EX|fcntl.LOCK_NB)
            if (root/'BLOCKED.json').exists():raise RuntimeError('Diagnose BLOCKED.json before resume')
            if (execution/'PAUSE').exists():
                if not resume:raise RuntimeError('Paused: use --resume explicitly')
                (execution/'PAUSE').unlink()
        log=root/'logs'/f'worker_{time_ns_id()}.log';log.parent.mkdir(exist_ok=True)
        with log.open('ab',buffering=0) as stream:
            child=subprocess.Popen([sys.executable,'-m','RQs.RQ4_2.src.main','formal-worker'],
                cwd=ROOT,env=os.environ.copy(),stdin=subprocess.DEVNULL,stdout=stream,stderr=subprocess.STDOUT,
                start_new_session=True,close_fds=True)
        # Wait for lock ownership / failure rather than declaring launch merely
        # because Popen returned. Model loading can safely continue afterward.
        deadline=time.monotonic()+15
        while time.monotonic()<deadline:
            state=formal_status(root)
            if state['owner'] and state['owner']['pid']==child.pid and state['live']:
                return {'status':'launched','pid':child.pid,'log':str(log),'progress':str(root/'progress.json')}
            if child.poll() is not None:raise RuntimeError('Formal worker exited at startup; inspect '+str(log))
            time.sleep(.1)
        raise RuntimeError('Worker ownership acknowledgement missing; inspect '+str(log))
