"""RQ4.10 immutable records, tolerant QA and deterministic domain operators."""
from pathlib import Path
import os,json,hashlib,re,ast,math
from contextlib import contextmanager
ROOT=Path(__file__).resolve().parents[3]
RQ=ROOT/'RQs/RQ4_10'
RESULTS=Path(os.environ.get('CANVASRCA_RQ410_ROOT',RQ/'results/domain_context_v1'))
HISTORY=ROOT/'RQs/RQ4_9/results/organization_v1'
MODEL=Path(os.environ.get('CANVASRCA_QWEN_MODEL','/home/lglsj/CanvasRCA/models/Qwen3.8-27B'))
@contextmanager
def cache_lock(path):
    import fcntl
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        try:yield
        finally:fcntl.flock(lock,fcntl.LOCK_UN)


def smoke_deadline(folder,seconds):
    """One registered wall-clock window across restarts, including startup."""
    import time
    path=Path(folder)/'window.json'
    if path.exists():window=read(path)
    else:
        window={'opened_unix':time.time(),'seconds':seconds}
        save(path,window)
    if window['seconds']!=seconds:raise ValueError('Smoke window budget changed')
    remaining=window['opened_unix']+seconds-time.time()
    if remaining<=0:raise TimeoutError('Registered smoke window already exhausted')
    return time.monotonic()+remaining


def relaxed_value(text):
    """Non-executing syntax recovery, never semantic/ID guessing."""
    text=text.strip().replace('“','"').replace('”','"').replace('‘',"'").replace('’',"'")
    cleaned=re.sub(r',\s*([}\]])',r'\1',text)
    for source in (text,cleaned,re.sub(r'([{,]\s*)([A-Za-z_]\w*)\s*:',r'\1"\2":',cleaned)):
        try:
            return json.loads(source)
        except (ValueError,TypeError):
            try:
                return ast.literal_eval(source)
            except (ValueError,SyntaxError,TypeError,MemoryError,RecursionError):
                pass
    raise ValueError('No safe literal interpretation')


def literal_objects(text):
    """Outermost complete objects only; don't parse inner lists twice."""
    stack=[];quote=None;escaped=False;start=None;out=[]
    for i,c in enumerate(text):
        if quote:
            if escaped: escaped=False
            elif c=='\\': escaped=True
            elif c==quote: quote=None
            continue
        if c in '\"\'' and stack: quote=c
        elif c in '[{':
            if not stack:start=i
            stack.append(c)
        elif c in ']}' and stack:
            if (stack[-1],c) not in {('[',']'),('{','}')}:
                stack=[];start=None;continue
            stack.pop()
            if not stack:
                try:out.append(relaxed_value(text[start:i+1]))
                except ValueError:pass
    return out


def final_answer_region(raw):
    matches=list(re.finditer(r'(?im)^\s*(?:final\s+answer|最终答案)\s*[:：]\s*',raw))
    return (raw[matches[-1].end():],'explicit_final') if matches else (raw,'whole_response')


def normalize_question_id(value):
    m=re.fullmatch(r'\s*(?:q(?:uestion)?[ _-]*)?0*(\d+)\s*',str(value),re.I)
    return 'q'+str(int(m.group(1))) if m else None


def receive_qa(raw,public_items):
    """Extract using question IDs/types/domains; accepted solutions are forbidden."""
    if any(set(q)&{'solutions','accepted','oracle','answer','expected'} for q in public_items):
        raise ValueError('QA extractor must not receive an oracle')
    byid={q['id']:q for q in public_items};text,region=final_answer_region(raw)
    rows=[];discarded=[];paths=[]
    def add(qid,value,path):
        key=normalize_question_id(qid)
        if key not in byid:
            discarded.append({'id':qid,'reason':'invalid_question_id','value':value});return
        if isinstance(value,dict):
            fields=[value[k] for k in ('answer','value','values','response','result') if k in value]
            if len({stable(x) for x in fields})!=1:
                rows.append((key,{'parse_conflict':True}));return
            value=fields[0]
        rows.append((key,value));paths.append(path)
    for obj in literal_objects(text):
        if isinstance(obj,dict):
            if 'answers' in obj:
                entries=obj['answers']
                if isinstance(entries,dict):
                    for k,v in entries.items():add(k,v,'answers_mapping')
                elif isinstance(entries,list):
                    for index,item in enumerate(entries):
                        if isinstance(item,dict):
                            qid=item.get('id',item.get('question_id',item.get('qid')))
                            add(qid,{k:v for k,v in item.items() if k not in {'id','qid','question_id'}},'answers_list')
                        elif len(entries)==len(public_items):
                            add(public_items[index]['id'],item,'complete_ordered_answer_list')
                        else:discarded.append({'value':item,'reason':'missing_question_id'})
            elif any(k in obj for k in ('id','question_id','qid')):
                add(obj.get('id',obj.get('question_id',obj.get('qid'))),{k:v for k,v in obj.items() if k not in {'id','qid','question_id'}},'standalone_item')
            else:
                for k,v in obj.items():
                    if normalize_question_id(k):add(k,v,'question_mapping')
        elif isinstance(obj,list):
            for item in obj:
                if isinstance(item,dict) and any(k in item for k in ('id','question_id','qid')):
                    add(item.get('id',item.get('question_id',item.get('qid'))),
                        {k:v for k,v in item.items() if k not in {'id','qid','question_id'}},'bare_answer_item_list')
    if not rows and re.search(r'\banswers\b\s*["\']?\s*:',text):
        # A damaged outer answers list may contain fully closed item objects.
        # Recover only those objects, never an unfinished final answer value.
        for m in re.finditer(r'\{[^{}]*\}',text):
            try:obj=relaxed_value(m.group())
            except ValueError:continue
            if isinstance(obj,dict) and any(k in obj for k in ('id','question_id','qid')):
                add(obj.get('id',obj.get('question_id',obj.get('qid'))),
                    {k:v for k,v in obj.items() if k not in {'id','qid','question_id'}},'complete_item_in_damaged_envelope')
    # A truncated prose answer may contain complete per-question answers but
    # no final JSON. Question headings are locators, never answer values.
    headings=set()
    if not rows:
        active=None
        for index,line in enumerate(text.splitlines()):
            plain=line.replace('**','').replace('__','')
            heading=re.fullmatch(r'\s*(?:#{1,6}\s*)?(?:(?:\d+[.)]|[-*])\s+)?(?:Question\s+)?(q(?:uestion)?\s*\d+)\s*(?:[:：.)]\s*)?(.*?)\s*',plain,re.I)
            if heading and (not heading[2] or '?' in heading[2] or '？' in heading[2]):
                active=heading[1];headings.add(index);continue
            answer=re.fullmatch(r'\s*(?:[-*]\s*)?(?:final\s+)?answer\s*[:：=]\s*(.+?)\s*',plain,re.I)
            if active and answer:
                value=answer[1]
                try:value=relaxed_value(value)
                except ValueError:pass
                add(active,value,'explicit_answer_in_question_section')
    # Also compare explicit q-ID summary lines with section answers. A plain
    # numbered reasoning step inside a section is not an answer list.
    if not rows or headings:
        for index,line in enumerate(text.splitlines()):
            if index in headings:continue
            m=re.fullmatch(r'\s*(?:[-*]\s*)?(Q(?:uestion)?\s*\d+|\d+)\s*[.:：=)]\s*(.+?)\s*',line,re.I)
            if m:
                if headings and not m[1].lower().startswith('q'):continue
                value=m.group(2)
                try:value=relaxed_value(value)
                except ValueError:pass
                add(m.group(1),value,'line_answer')
    if not rows and len(public_items)==1:
        obj=None
        try:obj=relaxed_value(text)
        except ValueError:pass
        if isinstance(obj,dict) and set(obj)<= {'answer','value','response'} and obj:
            add(public_items[0]['id'],obj,'single_answer_field')
        elif isinstance(obj,(str,int,float,list)) and not isinstance(obj,bool):
            add(public_items[0]['id'],obj,'single_answer_literal')
        else:
            explicit=re.findall(r'(?im)^\s*(?:final\s+)?answer\s*[:=]\s*(.+?)\s*$',text)
            if explicit:
                for value in explicit:add(public_items[0]['id'],value,'single_explicit_answer')
            elif text.strip() and len(text.splitlines())==1 and not re.search(r'\b(?:q|question)\s*\d+\s*[:=]',text,re.I):
                add(public_items[0]['id'],text,'single_natural_answer')
    grouped={}
    for qid,value in rows:
        q=byid[qid]
        value=extract_answer_value(value,q)
        seq=list(value) if isinstance(value,(list,tuple)) else [value]
        clean=[]
        for v in seq:
            if q.get('id_domain') is not None:
                norm=re.sub(r'^(?:service|pod|node)\s*(?:id\s*)?[:#]?\s*','',str(v).strip(),flags=re.I)
                if norm not in q['id_domain']:
                    discarded.append({'id':qid,'value':v,'reason':'invalid_answer_id'});continue
                v=norm
            if isinstance(v,(str,int,float)) and not isinstance(v,bool):
                if str(v).strip():
                    v=str(v).strip()
                    if q['type']=='number':
                        from decimal import Decimal,InvalidOperation
                        try:
                            value=Decimal(v)
                            if value.is_finite():v=str(value.normalize())
                        except InvalidOperation:pass
                    clean.append(v)
            else:
                discarded.append({'id':qid,'value':v,'reason':'invalid_answer_value'})
        normalized=sorted({stable(v):v for v in clean}.values(),key=stable)
        grouped.setdefault(qid,[]).append(normalized)
    extracted={};conflicts=[]
    for qid,lists in grouped.items():
        versions={stable(x) for x in lists}
        if len(versions)>1:conflicts.append(qid)
        else:extracted[qid]=lists[0]
    try:
        obj=json.loads(raw);strict=isinstance(obj,dict) and set(obj)=={'answers'} and isinstance(obj['answers'],list)
        strict=strict and all(isinstance(x,dict) and set(x)=={'id','answer'} and x['id'] in byid for x in obj['answers'])
    except (ValueError,TypeError):strict=False
    return {'schema':'QAReceptionV2','raw':raw,'answers':extracted,'ambiguous_ids':conflicts,
            'discarded':discarded,'paths':paths,'region':region,'strict_format':strict,'oracle_access':False}


def public_qa_items(items):
    return [{k:q[k] for k in ('id','question','type','mode','id_domain','answer_vocabulary','unit_factors') if k in q} for q in items]


def validate_qa_item(q):
    required={'id','question','type','mode','solutions','proof','support_cards'}
    if not required<=set(q) or not q['question'].strip() or not q['solutions'] or not q['proof']:
        raise ValueError('QA requires a question, nonempty oracle and visible proof')
    if q['mode'] not in {'single','alternatives','required_values'}:raise ValueError('Unknown QA cardinality')
    if q['type'] not in {'number','string','id'}:raise ValueError('Unknown QA answer type')
    if any(not isinstance(s,list) or not s or any(v is None or isinstance(v,bool) or str(v).strip()=='' for v in s) for s in q['solutions']):
        raise ValueError('Empty QA answer is not allowed; zero is allowed')
    if q['mode']!='required_values' and any(len(s)!=1 for s in q['solutions']):raise ValueError('Single answer oracle is not a tuple')
    if q['type']=='number':
        from decimal import Decimal,InvalidOperation
        for solution in q['solutions']:
            for value in solution:
                try:valid=Decimal(str(value)).is_finite()
                except InvalidOperation:valid=False
                if not valid:raise ValueError('QA numeric oracle must be finite and parseable')
    if q['type']=='id' and any(str(v) not in q.get('id_domain',[]) for s in q['solutions'] for v in s):
        raise ValueError('QA oracle ID is outside its public domain')
    return True


def score_qa(raw,items):
    from decimal import Decimal,InvalidOperation
    for q in items:validate_qa_item(q)
    reception=receive_qa(raw,public_qa_items(items));scores=[]
    def normal(value,q):
        value=str(value).strip().casefold()
        value=re.sub(r'\s+',' ',value)
        if q.get('semantic',{}).get('field')=='exclusive_latency_phase_comparison':
            # The question names both public fields. Accept an unambiguous field
            # name as its phase, without consulting the oracle or guessing prose.
            match=re.fullmatch(r'(reference|current|exl_p95_base_us|exl_p95_fault_us)(?:\s+(?:phase|value))?(?:\s+is\s+(?:larger|higher|greater))?[.!]?',value)
            if match:value={'exl_p95_base_us':'reference','exl_p95_fault_us':'current'}.get(match[1],match[1])
        return q.get('aliases',{}).get(value,value)
    def equals(a,b,q):
        if q['type']=='number':
            # Only explicit registered unit conversions; no percent tolerance.
            def number(v):
                token=str(v).strip();factor=Decimal(1)
                for suffix,scale in sorted(q.get('unit_factors',{}).items(),key=lambda x:-len(x[0])):
                    if token.lower().endswith(suffix.lower()):token=token[:-len(suffix)].strip();factor=Decimal(str(scale));break
                out=Decimal(token)*factor
                if not out.is_finite():raise ValueError('Nonfinite answer')
                return out
            try:return abs(number(a)-number(b))<=Decimal(str(q.get('display_tolerance','0')))
            except (InvalidOperation,ValueError):return False
        return normal(a,q)==normal(b,q)
    for q in items:
        available=q.get('available',True)
        answers=reception['answers'].get(q['id'],[]);full=False;partial=False
        for solution in q['solutions']:
            hits={i for i,v in enumerate(solution) if any(equals(a,v,q) for a in answers)}
            extras=any(not any(equals(a,v,q) for v in solution) for a in answers)
            exact=len(hits)==len(solution) and not extras
            if q['mode']=='required_values':
                full=full or exact
                partial=partial or (bool(hits) and not extras and len(hits)<len(solution))
            else:full=full or (len(answers)==1 and exact)
        credit=1. if full else .5 if q['mode']=='required_values' and partial else 0.
        if q['id'] in reception['ambiguous_ids']:credit=0.;full=False
        scores.append({'id':q['id'],'available':available,'submitted':answers,
                       'content_full':bool(full) if available else None,
                       'tolerant_credit':credit if available else None,
                       'strict_credit':float(full and reception['strict_format']) if available else None,
                       'coverage_credit':credit if available else 0.,
                       'reason':'target_removed' if not available else 'conflicting_answers' if q['id'] in reception['ambiguous_ids'] else 'scored'})
    eligible=[r for r in scores if r['available']]
    return {'schema':'QAScoreV2','policy':'rq410_oracle_blind_sections_subset_half_v2','reception':reception,'items':scores,
            'target_retention':len(eligible)/len(scores) if scores else None,
            'conditional_credit':sum(r['tolerant_credit'] for r in eligible)/len(eligible) if eligible else None,
            'end_to_end_credit':sum(r['coverage_credit'] for r in scores)/len(scores) if scores else None}


def object_json(value):
    """Immutable readable JSON, deduplicated by the bytes actually retained."""
    content=json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n'
    sha=hashlib.sha256(content.encode()).hexdigest();path=RESULTS/'objects'/(sha+'.json')
    if not path.exists():
        path.parent.mkdir(parents=True,exist_ok=True)
        import threading
        tmp=path.with_name(path.name+f'.{os.getpid()}.{threading.get_ident()}.tmp')
        with tmp.open('w') as f:f.write(content);f.flush();os.fsync(f.fileno())
        os.replace(tmp,path)
    if digest(path)!=sha:raise ValueError('Content-addressed record collision')
    return str(path.relative_to(ROOT)),sha


def score_context(oid):
    info=read(RESULTS/'evaluation/index.json')['contexts'][oid];path=RESULTS/info['path']
    if not path.resolve().is_relative_to((RESULTS/'evaluation/contexts').resolve()) or digest(path)!=info['sha256']:
        raise ValueError('Private score context mismatch')
    return read(path)


class CallLedger:
    """Durable attempt accounting. Exact references never allocate calls."""
    def __init__(self):
        import sqlite3
        RESULTS.mkdir(parents=True,exist_ok=True)
        self.path=RESULTS/'calls.sqlite'
        with sqlite3.connect(self.path) as db:
            db.execute('CREATE TABLE IF NOT EXISTS attempts (id INTEGER PRIMARY KEY, scope TEXT, call_key TEXT, state TEXT, began REAL, ended REAL, error TEXT)')
    def start(self,scope,key):
        import sqlite3,time
        cfg=read(RQ/'configs/protocol_v1.json')
        if scope not in {'formal',*cfg['smoke_scopes']}:raise ValueError('Unregistered call scope')
        with sqlite3.connect(self.path,timeout=30) as db:
            db.execute('BEGIN IMMEDIATE')
            count=db.execute('SELECT count(*) FROM attempts').fetchone()[0]
            local=db.execute('SELECT count(*) FROM attempts WHERE scope=?',(scope,)).fetchone()[0]
            limit=cfg['smoke_scopes'].get(scope,cfg['formal_calls']+cfg['infrastructure_recovery_calls'])
            if count>=cfg['total_call_limit'] or local>=limit:raise RuntimeError('Registered attempt budget exhausted')
            cur=db.execute('INSERT INTO attempts(scope,call_key,state,began) VALUES(?,?,?,?)',(scope,key,'started',time.time()))
            return cur.lastrowid
    def finish(self,attempt,error=None):
        import sqlite3,time
        with sqlite3.connect(self.path,timeout=30) as db:
            db.execute('UPDATE attempts SET state=?,ended=?,error=? WHERE id=?',('infrastructure_failed' if error else 'responded',time.time(),error,attempt))


def remember_reference(known,key,record):
    """Independent repeats neither consume nor supply ordinary result reuse."""
    if record.get('item',{}).get('force_call'):return False
    if record.get('generation_identity') and record.get('raw') is not None:
        known.setdefault(record['generation_identity'],key);return True
    return False


def view_conversation(key,scope='formal'):
    """Read the canonical conversation without writing another input/output copy."""
    from urllib.parse import urlencode
    rec=read(RESULTS/scope/'completed'/f'{key}.json');request=read(ROOT/rec['request_path'])
    page=RESULTS/'conversations/index.html'
    return {'schema':'RQ410ConversationViewV2','scope':scope,'key':key,'request':request,
            'raw_response':rec['raw'],'scores':rec['scores'],'usage':rec['usage'],
            'record_path':str(RESULTS/scope/'completed'/f'{key}.json'),
            'browser_url':'http://127.0.0.1:8769/'+str(page.relative_to(ROOT))+'#'+urlencode({'scope':scope,'key':key}),
            'server_command':'python3 -m http.server 8769 --bind 127.0.0.1 --directory '+str(ROOT)}


def read(path):
    return json.loads(Path(path).read_text())


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def stable(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def save(path, value):
    import threading
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f'.{os.getpid()}.{threading.get_ident()}.tmp')
    with tmp.open('w') as f:
        json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write('\n')
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)
    fd = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def offline():
    import socket
    if os.environ.get('CUDA_VISIBLE_DEVICES') != '':
        raise RuntimeError('CPU requires CUDA_VISIBLE_DEVICES explicitly empty')
    os.environ.update(HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', TOKENIZERS_PARALLELISM='false',
                      OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1')
    original = socket.socket.connect
    def connect(sock, address):
        if sock.family in (socket.AF_INET, socket.AF_INET6):
            raise RuntimeError('Network forbidden during CPU qualification')
        return original(sock, address)
    socket.socket.connect = connect


def physical_cores():
    cores, seen = [], set()
    for cpu in sorted(os.sched_getaffinity(0)):
        folder = Path(f'/sys/devices/system/cpu/cpu{cpu}/topology')
        key = ((folder/'physical_package_id').read_text(), (folder/'core_id').read_text())
        if key not in seen:
            seen.add(key)
            cores.append(cpu)
    return cores[:8]


def rca_schema(generation=False):
    schema={'type':'object','properties':{'services':{'type':'array','minItems':5,'maxItems':5,
        'uniqueItems':True,'items':{'type':'string'}},'reason':{'type':'string'},
        'confidence':{'enum':['high','medium','low']}},'required':['services','reason','confidence'],
        'additionalProperties':False}
    if generation:
        schema['properties']['services']['items']['pattern']='^[1-9][0-9]{2,4}$'
    return schema


def multimodal_gather(ids, positions, image_id, image_counts, per_image):
    """Keep all text and independently registered image subsets in original order."""
    import torch
    image_positions=(ids==image_id).nonzero().flatten().tolist()
    if len(image_positions)!=sum(image_counts) or len(image_counts)!=len(per_image):
        raise ValueError('Per-image gather count mismatch')
    retained_positions=set();offset=0
    for count,keep in zip(image_counts,per_image):
        if keep!=sorted(set(keep)) or any(type(i)is not int or not 0<=i<count for i in keep):
            raise ValueError('Invalid per-image gather subset')
        retained_positions.update(image_positions[offset+i] for i in keep);offset+=count
    keep=[i for i,value in enumerate(ids.tolist()) if value!=image_id or i in retained_positions]
    coords=positions[:,keep]
    return keep,coords,int(coords.max())+1-len(keep),image_positions


def attention_regions(request,counts,image_positions,keep,length):
    """Passive region attribution, using the actual per-image source geometry."""
    names=['other:generated','text:instructions'];raw=[1]*length;offset=0
    if request.get('diagnostic_token_region'):
        start,end=request['diagnostic_token_region'];names.extend(['text:diagnostic_evidence','text:boundary_uncertain'])
        for i in range(max(0,start-2),min(length,end+2)):raw[i]=3
        for i in range(start,end):raw[i]=2
    for image_index,(count,grid,geometry) in enumerate(zip(counts,request['grid_thw'],request['geometry'])):
        gh,gw=grid[1]//2,grid[2]//2
        labels=[f'image:{image_index}:background']*count
        sx=gw*32/geometry['width'];sy=gh*32/geometry['height']
        op=request['operators'][image_index];anchors=set(op['anchors']);evidence=set(op['evidence'])
        for token in range(count):
            x,y=((token%gw+.5)*32/sx,(token//gw+.5)*32/sy)
            if y<geometry.get('header_height',0):
                labels[token]=f'image:{image_index}:header'
            for panel in geometry['panels']:
                px,py,w,h=panel['box']
                if px<=x<px+w and py<=y<py+h:
                    labels[token]=f'image:{image_index}:panel_background'
                    if token in anchors:labels[token]=f'image:{image_index}:identity_stat_labels'
                    elif token in evidence:labels[token]=f'image:{image_index}:data_glyphs'
                    break
        for label in sorted(set(labels)):
            names.append(label)
        lookup={label:i for i,label in enumerate(names)}
        for j,label in enumerate(labels):
            raw[image_positions[offset+j]]=lookup[label]
        offset+=count
    return {'ids':[raw[i] for i in keep],'names':names}


def vllm_prompt_packet(request,processor):
    import math,torch
    from PIL import Image
    from types import SimpleNamespace,MethodType
    from transformers import AutoConfig
    from transformers.models.qwen3_5.modeling_qwen3_5 import Qwen3_5Model
    images=[]
    for path,sha in zip(request['images'],request['image_sha256'],strict=True):
        if digest(ROOT/path)!=sha:raise ValueError('Actual submitted PNG differs from frozen request')
        with Image.open(ROOT/path) as im:
            images.append(im.convert('RGB'))
    batch=processor(text=[request['prompt']],images=images or None,return_tensors='pt')
    cfg=AutoConfig.from_pretrained(MODEL,local_files_only=True)
    shell=SimpleNamespace(config=cfg)
    shell.get_vision_position_ids=MethodType(Qwen3_5Model.get_vision_position_ids,shell)
    if images:
        positions,_=Qwen3_5Model.get_rope_index(shell,batch['input_ids'],batch['mm_token_type_ids'],
            image_grid_thw=batch['image_grid_thw'],attention_mask=batch['attention_mask'])
        counts=[math.prod(g)//4 for g in batch['image_grid_thw'].tolist()]
    else:
        if not (request.get('registered_text_baseline') or request.get('hybrid') or request.get('qa_no_evidence') and request['task']=='QA'):
            raise ValueError('Unregistered image-free diagnostic request')
        positions=torch.arange(batch['input_ids'].shape[-1]).repeat(3,1)[:,None,:];counts=[]
    per_image=request['retained_by_image']
    keep,coords,delta,image_positions=multimodal_gather(batch['input_ids'][0],positions[:,0],cfg.image_token_id,counts,per_image)
    n=len(keep)
    if n!=request['input_tokens'] or n+request['max_output_tokens']>40960:
        raise ValueError('Actual runtime context differs from qualified request')
    if request.get('attention') and request.get('diagnostic_text'):
        evidence_ids=processor.tokenizer.encode(request['diagnostic_text'],add_special_tokens=False)
        interior=evidence_ids[2:-2]
        if not interior:raise ValueError('Diagnostic text region is too short to bind')
        actual=batch['input_ids'][0].tolist()
        starts=[i for i,t in enumerate(actual) if t==interior[0] and actual[i:i+len(interior)]==interior]
        if len(starts)!=1:raise ValueError('Cannot uniquely bind actual diagnostic text attention region')
        request=dict(request,diagnostic_token_region=[starts[0],starts[0]+len(interior)])
    all_positions=list(range(len(batch['input_ids'][0])))
    original_regions=attention_regions(request,counts,image_positions,all_positions,len(all_positions)) if request.get('attention') else None
    region={'ids':[original_regions['ids'][i] for i in keep],'names':original_regions['names']} if original_regions else None
    suffix=processor.tokenizer.encode(PUBLIC_SUFFIX,add_special_tokens=False)[2:-2]
    actual=batch['input_ids'][0].tolist()
    starts=[i for i in range(len(actual)-len(suffix)+1) if actual[i:i+len(suffix)]==suffix]
    if len(starts)!=1 or len(suffix)<8:raise ValueError('Eight public instruction queries are not uniquely located')
    detect_queries=list(range(starts[0]+len(suffix)-8,starts[0]+len(suffix)))
    # The frozen transport metadata remains compatible; operation U invokes no
    # contiguous-image attention intervention. Region IDs use actual two spans.
    meta={'schema':'RQ43VLLMPromptV13','length':n,'positions':coords.tolist(),'rope_delta':delta,
          'operation':'U','groups':[],'image_start':image_positions[0] if image_positions else 0,
          'image_count':sum(map(len,per_image)),'attention':region,'task':'QA' if request['task']=='ACTION' else request['task']}
    from RQs.RQ4_3.src.utils import validate_vllm_metadata
    validate_vllm_metadata(meta)
    return {'batch':{k:v for k,v in batch.items() if k in {'input_ids','pixel_values','image_grid_thw'}},
        'keep':keep,'source_by_slot':list(range(n)),'image_positions':image_positions,'metadata':meta,
        'image_tokens_original':sum(counts),'token_ids':batch['input_ids'][0,keep].tolist(),
        'operators':request['operators'],'original_positions':positions[:,0].tolist(),'image_token_id':cfg.image_token_id,
        'detect_queries':detect_queries,'original_regions':original_regions}


def score_response(response, context):
    from scorer import RCAScorer,RCAScorerConfig,score_bound_response
    scorer=RCAScorer(RCAScorerConfig.load())
    projected, adapter = response, {'status':'original_ranking_schema'}
    standard=score_bound_response(projected,context['candidates'],context['numeric_to_natural'],
                                  context['accepted'],rca_schema(),scorer)
    import re
    try:
        value=json.loads(response);rank=value.get('services',[]) if isinstance(value,dict) else []
        rank=rank if isinstance(rank,list) else []
    except ValueError:
        rank=[]
    predictions=[];seen=set()
    for index,raw in enumerate(rank[:5]):
        token=re.sub(r'^(?:service|node|pod)\s+', '',str(raw).strip(),flags=re.I)
        if token in context['candidates'] and token not in seen:
            predictions.append(context['numeric_to_natural'][token]);seen.add(token)
        else:
            predictions.append(f'__invalid_rank_{index}__')
    tolerant=scorer.score(predictions,context['accepted']).as_dict()
    for k in (1,3):
        tolerant['precision@'+str(k)]=sum(any(scorer.hit(p,label) for label in context['accepted']) for p in predictions[:k])/k
        standard['metrics']['precision@'+str(k)]=tolerant['precision@'+str(k)] if standard['status']=='complete' else 0.
    return {'standard':standard,'tolerant':tolerant,
        'adapter_audit':adapter,
        'tolerant_policy':'JSON services only; trim and remove explicit type prefix; unknown/duplicate remain misses at original rank; no ID repair'}


def object_file(path):
    """Content-addressed ordinary files; immutable verified hardlinks, not archives."""
    import shutil,threading
    path=Path(path);checksum=digest(path);target=RESULTS/'objects'/(checksum+path.suffix)
    target.parent.mkdir(parents=True,exist_ok=True)
    if not target.exists():
        temp=target.with_name(target.name+f'.{os.getpid()}.{threading.get_ident()}.tmp')
        try:
            if path.resolve().is_relative_to((RESULTS/'cache').resolve()):
                # A renderer may overwrite its cache file on recovery. Never
                # let that mutable inode alias a retained model input.
                shutil.copyfile(path,temp)
            else:
                try:os.link(path,temp)
                except OSError:shutil.copyfile(path,temp)
            if digest(temp)!=checksum:raise ValueError('Object changed during retention')
            os.replace(temp,target)
        finally:
            if temp.exists():temp.unlink()
    if digest(target)!=checksum:raise ValueError('Object hash mismatch')
    return str(target.relative_to(ROOT)) if target.is_relative_to(ROOT) else str(target),checksum


def subset(rows, per_dataset, salt):
    """Fixed hash, event diversity first; never uses outputs or ground truth."""
    selected = []
    for dataset in sorted({r['dataset'] for r in rows}):
        pool = sorted((r for r in rows if r['dataset']==dataset),
                      key=lambda r:stable([salt,r['id']]))
        groups, head, rest = set(), [], []
        for row in pool:
            if row['event_group'] in groups:
                rest.append(row)
            else:
                head.append(row)
                groups.add(row['event_group'])
        selected.extend((head+rest)[:per_dataset])
    return selected


def ranking_segment(prefix):
    """Locate only a top-level services array, respecting escaped JSON strings."""
    import re
    depth, quoted, escaped, start = 0, False, False, None
    for i, c in enumerate(prefix):
        if escaped:
            escaped=False
            continue
        if quoted:
            if c=='\\':
                escaped=True
            elif c=='"':
                quoted=False
            continue
        if c=='"':
            if depth==1 and re.match(r'"services"\s*:\s*\[',prefix[i:]):
                start=i+re.match(r'"services"\s*:\s*\[',prefix[i:]).end()
                break
            quoted=True
        elif c in '[{':
            depth+=1
        elif c in ']}':
            depth-=1
    if start is None:
        return 'before'
    quoted=escaped=False
    for c in prefix[start:]:
        if escaped:
            escaped=False
        elif quoted and c=='\\':
            escaped=True
        elif c=='"':
            quoted=not quoted
        elif c==']' and not quoted:
            return 'after'
    return 'inside'


def make_ranking_processor():
    from vllm.v1.sample.logits_processor.interface import LogitsProcessor
    from vllm.v1.sample.logits_processor.builtin import process_dict_updates
    class Processor(LogitsProcessor):
        def __init__(self,vllm_config,device,is_pin_memory):
            from transformers import AutoTokenizer
            self.tokenizer=AutoTokenizer.from_pretrained(vllm_config.model_config.tokenizer,local_files_only=True)
            self.states={}
        def is_argmax_invariant(self):
            return False
        def update_state(self,batch_update):
            def new(params,prompt,output):
                extra=params.extra_args or {}
                if extra['canvasrca']['task']!='RCA':
                    return None
                return {'tokens':output,'preface':extra.get('rq47_preface',False),'done':False}
            process_dict_updates(self.states,batch_update,new)
        def apply(self,logits):
            import torch
            rows=[]
            for row,s in self.states.items():
                if s['done']:
                    continue
                state=ranking_segment(self.tokenizer.decode(s['tokens'],skip_special_tokens=True))
                if state=='after':
                    s['done']=True
                elif state=='inside' or (state=='before' and not s['preface']):
                    rows.append(row)
            if rows:
                indexes=logits[rows].argmax(-1,keepdim=True)
                logits[rows]=torch.full_like(logits[rows],-torch.inf).scatter(1,indexes,logits[rows].gather(1,indexes))
            return logits
    Processor.__module__=__name__
    Processor.__qualname__='RQ410RankingProcessor'
    return Processor


def __getattr__(name):
    if name=='RQ410RankingProcessor':
        result=make_ranking_processor()
    elif name in {'validate_vllm_metadata','vllm_tensor_wire','vllm_tensor_unwire',
                  'VLLMCacheAdmission','vllm_cache_profile'}:
        from importlib import import_module
        result=getattr(import_module('RQs.RQ4_3.src.utils'),name)
    else:
        raise AttributeError(name)
    globals()[name]=result
    return result


def protocol():
    return read(RQ/'configs/protocol_v1.json')


def farthest(pool, selected, width, count):
    """Historical spatial farthest point, exact squared grid distance and ties."""
    import numpy as np
    pool=sorted(set(pool)-set(selected));chosen=[]
    if not 0<=count<=len(pool):raise ValueError('Spatial budget exceeds available E')
    points=np.array([(i%width,i//width) for i in pool],dtype=float).reshape(-1,2)
    distance=np.full(len(pool),np.inf)
    for i in sorted(set(selected)):
        distance=np.minimum(distance,((points-[i%width,i//width])**2).sum(axis=1))
    for _ in range(count):
        j=int(np.argmax(distance));token=pool[j];chosen.append(token)
        distance=np.minimum(distance,((points-points[j])**2).sum(axis=1));distance[j]=-1
    return chosen


def uniform_plan(support):
    a=set(support['anchors']);e={i for r in support['roles'].values() for i in r['tokens']}-a
    n=support['image_tokens'];q=math.ceil(len(e)/2)
    if not a or any(i<0 or i>=n for i in a|e):raise ValueError('Invalid protected/evidence support')
    return {'schema':'VisualOperatorPlanV1','anchors':sorted(a),'evidence':sorted(e),'q':q,
        'grid':support['grid'],'image_tokens':n,'groups':[],
        'retained':sorted(a|set(farthest(e,a,support['grid'][1],q))),'operator':'gather'}


def allocate_slots(sizes,total):
    """Hamilton allocation with one seed per nonempty compatible source group."""
    if any(type(v)is not int or v<=0 for v in sizes) or not len(sizes)<=total<=sum(sizes):
        raise ValueError('Fusion compatibility groups cannot fit the registered q')
    remaining=total-len(sizes);capacity=[s-1 for s in sizes];den=sum(capacity)
    exact=[remaining*c/den if den else 0 for c in capacity];out=[1+math.floor(x) for x in exact]
    rest=total-sum(out)
    order=sorted(range(len(sizes)),key=lambda i:(-(exact[i]-math.floor(exact[i])),i))
    for i in order[:rest]:out[i]+=1
    if sum(out)!=total or any(x>s for x,s in zip(out,sizes)):raise ValueError('Hamilton overflow')
    return out


def sink_candidates(probabilities,image_indices,domain,policy):
    """[heads,queries,keys], at last eight public text queries; no oracle."""
    import numpy as np
    p=np.asarray(probabilities,dtype=float)
    if p.ndim!=3 or p.shape[1]!=policy['queries']:raise ValueError('Sink detection requires eight queries')
    image=list(image_indices);mean=p[:,:,image].mean(axis=0);mass=mean.sum(-1,keepdims=True)
    density=np.divide(mean*len(image),mass,out=np.zeros_like(mean),where=mass>0)
    return [image[i] for i in range(len(image)) if image[i] not in set(domain)
            and int((density[:,i]>=policy['density']).sum())>=policy['min_queries']]


def commit_call(scope,item,request,raw,usage,attempt,reference=None):
    marker=RESULTS/scope/'completed'/f'{item["key"]}.json'
    if marker.exists():
        existing=read(marker)
        if existing['generation_identity']!=request['identity'] or existing['raw']!=raw:raise ValueError('Atomic committed result is immutable')
        return existing
    if usage.get('actual_selection'):
        from copy import deepcopy
        request=deepcopy(request);request['prepared_retained_by_image']=request['retained_by_image']
        request['retained_by_image']=usage['actual_selection']['retained_by_image']
        request['actual_operator_receipt']=usage['actual_selection']
    request_path,sha=object_json(request)
    scores=score_qa(raw,request['qa_items']) if item['task']=='QA' else score_response(raw,score_context(item['id']))
    record={'schema':'RQ410CommittedCallV1','item':item,'request_path':request_path,'request_sha256':sha,
        'raw':raw,'usage':usage,'scores':scores,'attempt':attempt,'reference':reference,
        'generation_identity':request['identity'],'status':'referenced' if reference else 'complete'}
    save(RESULTS/scope/'completed'/f'{item["key"]}.json',record);return record


def extract_answer_value(value,q):
    """Use public type/vocabulary only, never select a candidate using the oracle."""
    if not isinstance(value,str):return value
    text=value.strip().strip('`').strip()
    text=re.sub(r'^(?:the\s+)?(?:answer|value|statistic|unit|entity|phase)\s*(?:is|=|:)\s*','',text,flags=re.I)
    if q['type']=='number':
        text=text.rstrip('.!?。！？，,;；').strip()
        # Remove an explicit field label, not arbitrary numbers in an explanation.
        text=re.sub(r'^(?:p50|p95|reference|current)\s*(?:is|=|:)\s*','',text,flags=re.I)
        suffixes=sorted(set(q.get('unit_factors',{}))|{'µs','μs','us','ms','s'},key=lambda x:(-len(x),x))
        unit_pattern='|'.join(re.escape(x) for x in suffixes)
        found=re.findall(r'(?<![\w.])[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?(?:\s*(?:'+unit_pattern+r'))?(?![\w.])',text)
        return found[0].strip() if len(found)==1 else value
    if q['type']=='id':
        # A sentence-final period is punctuation, not part of an entity ID.
        # Internal decimal points remain excluded by the lexical boundaries.
        text=text.rstrip('.!?。！？，,;；').strip()
        matches=re.findall(r'(?<![\w.])(?:service|pod|node)?\s*(?:ID\s*)?[:#]?\s*(\d+)(?![\w.])',text,re.I)
        return matches if matches else value
    vocabulary=q.get('answer_vocabulary',{})
    # A complete comparative statement is one answer, even though it names
    # both phases. Parse its explicit relation; never choose using the oracle.
    phase_pairs=[('reference','current'),('baseline','peak'),('regular','current')]
    for left,right in phase_pairs:
        if not {left,right}<=set(vocabulary.values()):continue
        names='('+left+'|'+right+')'
        item=r'(?:the\s+)?'+names+r'(?:\s+(?:phase|value))?'
        sentence=text.casefold().rstrip('.!').strip()
        match=re.fullmatch(item+r'\s+(?:is\s+|has\s+(?:a\s+)?)?(higher|larger|greater|lower|smaller|less)(?:\s+value)?\s+than\s+'+item,sentence)
        if match and match[1]!=match[3]:
            return match[1] if match[2] in {'higher','larger','greater'} else match[3]
        match=re.fullmatch(item+r'\s*([<>])\s*'+item,sentence)
        if match and match[1]!=match[3]:return match[1] if match[2]=='>' else match[3]
        match=re.fullmatch(item+r'\s+and\s+'+item+r'\s+(?:are\s+)?(?:equal|the same)',sentence)
        if match and match[1]!=match[2]:return 'equal'
    hits=set()
    for alias,canonical in vocabulary.items():
        if re.search(r'(?<!\w)'+re.escape(alias)+r'(?!\w)',text,re.I):hits.add(canonical)
    return sorted(hits) if hits else text.rstrip('.!')


ARMS=tuple(protocol()['arms'])
PUBLIC_SUFFIX="Read the supplied evidence carefully and return only the answer requested by the current task."


def roster():
    from collections import Counter
    path=RESULTS/'evaluation/roster.json'
    rows=read(path if path.exists() else HISTORY/'evaluation/roster.json')['cases']
    if len({r['id'] for r in rows})!=220 or dict(Counter(r['dataset'] for r in rows))!=protocol()['dataset_counts']:
        raise ValueError('Registered 220-case cohort differs')
    return rows


def domain_packet(plan,geometry,ink=None):
    """Disjoint D/O in real merged-token coordinates; all touching cards retained."""
    a=set(plan['anchors']);e=set(plan['evidence']);n=plan['image_tokens'];h,w=plan['grid']
    if a&e or not a or h*w!=n or any(type(i)is not int or not 0<=i<n for i in a|e):
        raise ValueError('Invalid/disjoint evidence domain')
    d=a|e;o=set(range(n))-d;regions={};card_tokens=set();memberships={}
    for panel in geometry['panels']:
        x,y,bw,bh=panel['box'];inside=[]
        # Positive-area intersection, not center-only ownership at card edges.
        for yy in range(max(0,math.floor(y*h/4096)),min(h,math.ceil((y+bh)*h/4096))):
            for xx in range(max(0,math.floor(x*w/4096)),min(w,math.ceil((x+bw)*w/4096))):inside.append(yy*w+xx)
        card_tokens.update(inside)
        for i in inside:memberships.setdefault(i,[]).append(panel['card'])
    for i in sorted(o):
        signature='|'.join(sorted(memberships.get(i,[]))) or '__outside_cards__'
        regions.setdefault(signature,[]).append(i)
    return {'schema':'EvidenceDomainPacketV2','anchors':sorted(a),'evidence':sorted(e),'domain':sorted(d),
        'outside':sorted(o),'image_tokens':n,'grid':[h,w],'regions':dict(sorted(regions.items())),
        'card_tokens':sorted(card_tokens),'ink_tokens':sorted(ink) if ink is not None else None,
        'definition':'real foreground support; D/O refer to input locations, not feature informativeness'}


def outside_groups(domain):
    o=domain['outside'];d=domain['domain'];w=domain['grid'][1]
    b=min(len(o),256,max(1,len(d)//20))
    if not b:return []
    regions=list(domain['regions'].values());slots=allocate_slots([len(x) for x in regions],b);groups=[]
    for pool,count in zip(regions,slots,strict=True):
        cx=sum(i%w for i in pool)/len(pool);cy=sum(i//w for i in pool)/len(pool)
        first=min(pool,key=lambda i:((i%w-cx)**2+(i//w-cy)**2,i))
        reps=[first]+farthest(pool,[first],w,count-1);buckets={i:[i] for i in sorted(reps)}
        for i in pool:
            if i in buckets:continue
            rep=min(reps,key=lambda j:((i%w-j%w)**2+(i//w-j//w)**2,j));buckets[rep].append(i)
        groups.extend({'representative':rep,'members':sorted(v)} for rep,v in buckets.items())
    return sorted(groups,key=lambda g:g['representative'])


def context_plan(base,domain,arm,case_id):
    from copy import deepcopy
    p=deepcopy(base);p.update(schema='ContextOperatorPlanV1',operator='gather',groups=[],retained=domain['domain'][:])
    d=set(domain['domain']);o=domain['outside'];a=set(p['anchors']);e=set(p['evidence'])
    if arm in protocol()['fusion']:
        groups=outside_groups(domain);p['retained']=sorted(d|{g['representative'] for g in groups})
        if arm!='F_O_REP' and any(len(g['members'])>1 for g in groups):
            p.update(operator='outside_mean',groups=groups,outside=o,assignment='spatial' if arm=='F_O_SPATIAL' else 'feature',
                sham=arm=='F_O_SHAM',sham_seed=stable(['rq410-outside-sham-v1',case_id]))
    elif arm=='P_INK':
        if domain['ink_tokens'] is None:raise ValueError('P_INK requires actual processed pixel evidence')
        p['retained']=sorted(d|set(domain['ink_tokens']))
    elif arm=='P_CARD':p['retained']=sorted(d|set(domain['card_tokens']))
    elif arm=='P_LENGTH_CONTROL':
        p['retained']=sorted(a|set(farthest(e|set(o),a,p['grid'][1],len(e))))
        p['lost_evidence']=sorted(e-set(p['retained']))
    elif arm in protocol()['sink']:
        p.update(operator='sink',retained=list(range(p['image_tokens'])),sink_arm=arm,policy=protocol()['sink_policy'])
    elif arm not in {'P_DOMAIN','V_EXACT_DOMAIN','D14_DOMAIN_FIXED','D14_DOMAIN_PACK'}:
        raise ValueError('Unregistered domain operator '+arm)
    if arm!='P_LENGTH_CONTROL' and not d<=set(p['retained']):raise ValueError('Operator loses protected D')
    p['domain_packet_sha256']=stable(domain)
    return p


def assign_feature_groups(features,plan):
    """GPU cosine assignment; seed ownership is unconditional and ties use index."""
    import torch
    if plan.get('assignment')=='spatial':return plan['groups']
    seeds=sorted(g['representative'] for g in plan['groups']);outside=plan['outside']
    f=features.float();norm=torch.linalg.vector_norm(f,dim=-1,keepdim=True);f=f/norm.clamp_min(1e-30)
    seed_index=torch.tensor(seeds,device=f.device,dtype=torch.long)
    assignments=[]
    for offset in range(0,len(outside),1024):
        ix=torch.tensor(outside[offset:offset+1024],device=f.device,dtype=torch.long)
        similarities=f[ix]@f[seed_index].T
        assignments.extend(similarities.argmax(-1).tolist())
    groups={r:[r] for r in seeds}
    for i,j in zip(outside,assignments,strict=True):
        if i not in groups:groups[seeds[j]].append(i)
    out=[{'representative':r,'members':sorted(m)} for r,m in groups.items()]
    if plan.get('sham'):
        values=sorted((i for g in out for i in g['members'] if i!=g['representative']),key=lambda i:(stable([plan['sham_seed'],i]),i))
        cursor=0
        for g in out:
            size=len(g['members'])-1;g['members']=sorted([g['representative']]+values[cursor:cursor+size]);cursor+=size
    members=[i for g in out for i in g['members']]
    if sorted(members)!=outside or len(members)!=len(set(members)):raise ValueError('O partition duplicates or loses members')
    return out


def redistribute_reference(prob,image,domain,donors,arm):
    """Independent NumPy probability oracle for future numerical qualification."""
    import numpy as np
    p=np.asarray(prob,dtype=np.float64);flat=p.reshape(-1,p.shape[-1]);out=flat.copy();d=sorted(domain)
    o=sorted(set(image)-set(d));c=sorted(set(donors)&set(o));b=sorted(set(o)-set(c));audits=[]
    for r,row in enumerate(flat):
        dm=row[d].sum();om=row[o].sum();cm=row[c].sum();bm=row[b].sum();m=0.
        if arm=='S_O_MASK':
            if om>0 and 1-om>0:out[r,o]=0;out[r]/=1-om;m=om
        elif dm>0:
            source=o if arm=='S_O_REDIST' else c if arm=='S_SINK_REDIST' else b
            m=om if arm=='S_O_REDIST' else min(cm,bm)
            if m>0:out[r,source]-=m*row[source]/row[source].sum();out[r,d]+=m*row[d]/dm
        audits.append({'released':float(m),'operated':bool(m>0)})
    if not np.allclose(out.sum(-1),flat.sum(-1),atol=1e-10) or np.min(out)<-1e-12:raise ValueError('Probability conservation')
    return out.reshape(p.shape),audits


def computation_identity(plan):
    if not plan:return None
    base={'retained':plan['retained'],'kind':'gather'}
    if plan['operator']=='outside_mean':
        return dict(base,kind='outside_mean',groups=plan['groups'],outside=plan['outside'],
            assignment=plan['assignment'],sham=plan['sham'],sham_seed=plan['sham_seed'] if plan['sham'] else None)
    if plan['operator']=='sink':return dict(base,kind='sink',domain=sorted(set(plan['anchors'])|set(plan['evidence'])),arm=plan['sink_arm'],policy=plan['policy'])
    return base


class GPUSampler:
    """Passive utilization samples; compute inference-only summaries after drain."""
    def __init__(self,folder):
        import threading
        self.folder=Path(folder);self.stop_event=threading.Event();self.thread=None;self.samples=[];self.errors=[]
    def start(self):
        import threading
        self.thread=threading.Thread(target=self._sample,daemon=True,name='rq410-gpu-util');self.thread.start()
    def _sample(self):
        import subprocess,time
        while not self.stop_event.is_set():
            try:
                p=subprocess.run(['nvidia-smi','--query-gpu=utilization.gpu,memory.used','--format=csv,noheader,nounits','-i','0'],capture_output=True,text=True,timeout=4)
                if p.returncode:raise RuntimeError(p.stderr.strip())
                gpu,mem=p.stdout.strip().split(',');self.samples.append({'monotonic':time.monotonic(),'gpu_percent':float(gpu),'memory_mib':float(mem)})
            except Exception as exc:self.errors.append(str(exc))
            self.stop_event.wait(1.)
    def close(self):
        self.stop_event.set()
        if self.thread:self.thread.join(timeout=5)
        windows=[]
        for p in (self.folder/'completed').glob('*.json'):
            r=read(p)
            if not r.get('reference'):
                u=r['usage']
                if 'invoke_started_monotonic' in u:windows.append((u['invoke_started_monotonic'],u['invoke_finished_monotonic']))
        selected=[s for s in self.samples if any(a<=s['monotonic']<=b for a,b in windows)]
        save(self.folder/'gpu_utilization.json',{'samples':self.samples,'errors':self.errors,'coverage':'union of actual inference intervals; excludes engine startup',
            'inference_sample_count':len(selected),'inference_mean_percent':sum(x['gpu_percent'] for x in selected)/len(selected) if selected else None})
