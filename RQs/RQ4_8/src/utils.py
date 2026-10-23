"""RQ4.8 public receivers, transport and durable records. No import-time execution."""
from pathlib import Path
import os,json,hashlib,re,ast
from contextlib import contextmanager
ROOT=Path(__file__).resolve().parents[3]
RQ=ROOT/'RQs/RQ4_8'
RESULTS=Path(os.environ.get('CANVASRCA_RQ48_ROOT',RQ/'results/card_selection_v1'))
SOURCE_ROOT=ROOT
HISTORY=ROOT/'RQs/RQ4_1/results/comparison_coding_v1'
MODEL=Path(os.environ.get('CANVASRCA_QWEN_MODEL','/home/lglsj/CanvasRCA/models/Qwen3.8-27B'))
SINGLE=('S_HASH_PACK','S_BALANCED_FIXED','S_BALANCED_PACK')
MULTI=('M_ID_FIXED','M_ID_PACK','M_MATCHED_HASH_PACK','M_ID_PACK_FULL')
HYBRID=('H_NATIVE8','H_TIME_RESTORE','H_PAIR_RESTORE','H_BOTH_RESTORE')
ARMS=SINGLE+MULTI+HYBRID
NOMINEES=('S_BALANCED_PACK','M_ID_PACK','H_TIME_RESTORE')
HISTORICAL=('U','T_FULL','H_MARGINAL','H_MARGINAL_PHASE')


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


def normalized_card_id(value):
    if isinstance(value,bool):return None
    if isinstance(value,int):return str(value) if value>=0 else None
    if not isinstance(value,str):return None
    m=re.fullmatch(r'\s*(?:(?:card|卡片)\s*#?\s*|#)?(\d+)\s*',value,re.I)
    return str(int(m.group(1))) if m else None


def receive_selection(raw,visible,diagnostic):
    """Public ID domains only. No candidate/root/answer labels are accepted."""
    visible={str(int(i)) for i in visible};diagnostic={str(int(i)) for i in diagnostic}
    text,region=final_answer_region(raw)
    aliases={'keep_card_indices','keep_cards','keep_indices','selected_cards','card_indices','keep'}
    candidates=[];paths=[];semantic_conflict=False
    for obj in literal_objects(text):
        if isinstance(obj,dict):
            if any(k in obj for k in ('delete','drop','remove','delete_card_indices','drop_card_indices','remove_cards')):
                semantic_conflict=True
            for k in aliases:
                if k in obj:
                    candidates.append(obj[k]);paths.append('field:'+k)
        elif isinstance(obj,list):
            bare=re.sub(r'```(?:json)?|```','',text,flags=re.I)
            residue=re.sub(r'\[[^\[\]]*\]','',bare).strip()
            explicitly_named=bool(re.search(r'(?i)\b(?:keep(?: cards?)?|keep_card_indices|selected cards?|card indices)\s*[:=]\s*\[',bare))
            if not residue or explicitly_named or region=='explicit_final':
                candidates.append(obj);paths.append('explicit_list')
    if re.search(r'(?i)\b(?:delete|drop|remove)\s*(?:cards?|indices|ids)?\s*[:=]',text):
        semantic_conflict=True
    if not candidates and not semantic_conflict:
        # A truncated explicit keep-list: only delimiter-terminated entries count.
        match=re.search(r'(?i)\b(?:keep_card_indices|keep_cards|keep_indices|selected_cards|card_indices)\b["\']?\s*[:=]\s*\[([^\]]*)$',text.strip())
        if match:
            entries=[]
            for piece in match.group(1).split(',')[:-1]:
                try:entries.append(relaxed_value(piece))
                except ValueError:entries.append(piece.strip())
            candidates=[entries];paths=['truncated_explicit_list_complete_entries']
        else:
            clean=re.sub(r'```(?:json)?|```','',text,flags=re.I).strip()
            match=re.fullmatch(r'(?is)(?:(?:keep|keep cards|card indices)\s*[:=]\s*)?((?:["\']?(?:card\s*#?\s*|#)?\d+["\']?\s*[,;、]\s*)+["\']?(?:card\s*#?\s*|#)?\d+["\']?)',clean)
            if match:
                candidates=[[x.strip().strip('"\'') for x in re.split('[,;、]',match.group(1))]];paths=['bare_delimited_list']
            elif clean and all(re.fullmatch(r'\s*[-*•]\s*(?:(?:card|卡片)\s*#?\s*|#)?\d+\s*',x,re.I) for x in clean.splitlines()):
                candidates=[[re.sub(r'^\s*[-*•]\s*','',x) for x in clean.splitlines()]];paths=['bullet_list']
    normalized=[];discarded=[]
    for n,seq in enumerate(candidates):
        if not isinstance(seq,(list,tuple)):
            discarded.append({'list':n,'value':seq,'reason':'not_a_list'});continue
        kept=set()
        for item in seq:
            cid=normalized_card_id(item)
            if cid is None or cid not in visible:
                discarded.append({'list':n,'value':item,'reason':'invalid_card_id'})
            elif cid in kept:
                discarded.append({'list':n,'value':item,'reason':'duplicate'})
            else:kept.add(cid)
        normalized.append(sorted(kept,key=int))
    unique={tuple(seq) for seq in normalized}
    status='semantic_conflict' if semantic_conflict else 'ambiguous' if len(unique)>1 else 'unparseable' if not unique else 'accepted'
    selected=list(next(iter(unique))) if len(unique)==1 and status=='accepted' else []
    if status=='accepted' and not set(selected)&diagnostic:status='no_valid_diagnostic_card'
    try:
        strict=json.loads(raw)
        strict_ok=(isinstance(strict,dict) and set(strict)=={'keep_card_indices'} and
                   isinstance(strict['keep_card_indices'],list) and all(type(x)is int for x in strict['keep_card_indices']))
    except (ValueError,TypeError):strict_ok=False
    return {'schema':'CardSelectionV1','raw':raw,'status':status,'strict_format':strict_ok,
            'region':region,'paths':paths,'discarded':discarded,'selected':selected,
            'executable':status=='accepted','oracle_access':False}


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
    # Recover linewise answers independently, including damaged outer JSON.
    if not rows:
        for line in text.splitlines():
            m=re.fullmatch(r'\s*(?:[-*]\s*)?(Q(?:uestion)?\s*\d+|\d+)\s*[.:：=)]\s*(.+?)\s*',line,re.I)
            if m:
                value=m.group(2)
                try:value=relaxed_value(value)
                except ValueError:pass
                add(m.group(1),value,'line_answer')
    grouped={}
    for qid,value in rows:
        q=byid[qid]
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
    return [{k:q[k] for k in ('id','question','type','mode','id_domain') if k in q} for q in items]


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
                for suffix,scale in q.get('unit_factors',{}).items():
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
                partial=partial or bool(hits)
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
    return {'schema':'QAScoreV2','policy':'tolerant_required_partial_half_v2_phase_alias','reception':reception,'items':scores,
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


def commit_call(scope,item,request,raw,usage,attempt,parent=None,reference=None):
    """Per-call completion is the sole resume commit, after all objects persist."""
    if request:
        request_path,request_sha=object_json(request)
    else:request_path=request_sha=None
    if item['task']=='ACTION':
        inventory=read(RESULTS/'inputs'/item['id']/'inventory.json')
        scores=receive_selection(raw,[c['index'] for c in inventory['cards']],
                                 [c['index'] for c in inventory['cards'] if not c['protected']])
    elif item['task']=='QA':scores=score_qa(raw,request['qa_items'])
    else:scores=score_response(raw,score_context(item['id']))
    record={'schema':'RQ48CommittedCallV1','item':item,'request_path':request_path,'request_sha256':request_sha,
        'raw':raw,'usage':usage,'scores':scores,'attempt':attempt,'reference':reference,'parent':parent,
        'generation_identity':request['identity'] if request else None,'status':'referenced' if reference else 'complete'}
    save(RESULTS/scope/'completed'/f'{item["key"]}.json',record)
    return record


def commit_unavailable(scope,item,parent,reason,items=None):
    if item['task']=='QA':
        qitems=[dict(q,available=False) for q in items or []]
        score=score_qa('',qitems) if qitems else {'items':[],'end_to_end_credit':None,'reason':reason}
    else:score=score_response('{}',score_context(item['id']))
    record={'schema':'RQ48CommittedCallV1','item':item,'status':'model_selection_failed' if reason=='no_valid_selection' else 'not_applicable',
        'parent':parent,'request_path':None,'attempt':None,'reference':None,'raw':None,'scores':score,'usage':{},'reason':reason}
    save(RESULTS/scope/'completed'/f'{item["key"]}.json',record);return record


def remember_reference(known,key,record):
    """Independent repeats neither consume nor supply ordinary result reuse."""
    if record.get('item',{}).get('force_call'):return False
    if record.get('generation_identity') and record.get('raw') is not None:
        known.setdefault(record['generation_identity'],key);return True
    return False


def view_conversation(key,scope='formal'):
    import html
    rec=read(RESULTS/scope/'completed'/f'{key}.json');out=RESULTS/'conversations'/f'{scope}__{key}.html'
    records=[]
    if rec.get('parent'):
        parent_scope=rec['item'].get('parent_scope',scope)
        records.append(('Selection (audit history only; not forwarded)',read(RESULTS/parent_scope/'completed'/f'{rec["parent"]}.json')))
    records.append(('Current request',rec));parts=['<!doctype html><meta charset="utf-8"><style>pre{white-space:pre-wrap}img{max-width:100%}body{max-width:1400px;margin:auto}</style>']
    for title,r in records:
        parts.append('<h2>'+html.escape(title)+'</h2>')
        if r.get('request_path'):
            req=read(ROOT/r['request_path']);parts.append('<pre>'+html.escape(req['prompt'])+'</pre>')
            for image in req['images']:parts.append('<img src="'+html.escape(os.path.relpath(ROOT/image,out.parent))+'">')
        parts.append('<pre>'+html.escape(r.get('raw') or str(r.get('reason','')) )+'</pre>')
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text('\n'.join(parts));return str(out)

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

def historical(row):
    base = Path(row['base'])
    if not base.is_absolute():
        base = SOURCE_ROOT/base
    record = read(HISTORY / f'formal_v28/completed/{row["id"]}__development__A_UNIFORM_E50__BASE.json')
    return base, {'actual_retention':{'indices':record['actual_retention']['indices']}}

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
        for token in range(count):
            x,y=((token%gw+.5)*32/sx,(token//gw+.5)*32/sy)
            if y<geometry.get('header_height',0):
                labels[token]=f'image:{image_index}:header'
            for panel in geometry['panels']:
                px,py,w,h=panel['box']
                if px<=x<px+w and py<=y<py+h:
                    labels[token]=f'image:{image_index}:panel:{panel["card"]}'
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
        if not (request.get('registered_text_baseline') or request.get('hybrid')):
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
    region=attention_regions(request,counts,image_positions,keep,len(batch['input_ids'][0])) if request.get('attention') else None
    # The frozen transport metadata remains compatible; operation U invokes no
    # contiguous-image attention intervention. Region IDs use actual two spans.
    meta={'schema':'RQ43VLLMPromptV13','length':n,'positions':coords.tolist(),'rope_delta':delta,
          'operation':'U','groups':[],'image_start':image_positions[0] if image_positions else 0,
          'image_count':sum(map(len,per_image)),'attention':region,'task':'QA' if request['task']=='ACTION' else request['task']}
    from RQs.RQ4_3.src.utils import validate_vllm_metadata
    validate_vllm_metadata(meta)
    return {'batch':{k:v for k,v in batch.items() if k in {'input_ids','pixel_values','image_grid_thw'}},
        'keep':keep,'source_by_slot':list(range(n)),'image_positions':image_positions,'metadata':meta,
        'image_tokens_original':sum(counts),'token_ids':batch['input_ids'][0,keep].tolist()}

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

def roster():
    from collections import defaultdict,deque,Counter
    index=read(HISTORY/'deployment_v26/request_index.json')['cases']
    events={r['opaque_incident_id']:r for r in read(HISTORY/'cpu_admission_v4/event_group_audit.json')['cases']}
    pools=defaultdict(deque)
    for oid,case in sorted(index.items(),key=lambda x:stable(['rq48-roster-v1',x[0]])):
        event=events[oid]
        pools[(case['dataset'],event['source'])].append({'id':oid,'dataset':case['dataset'],'base':case['base'],
            'source':event['source'],'event_group':event['leakage_group']})
    rows=[]
    while any(pools.values()):
        for pool in pools.values():
            if pool:rows.append(pool.popleft())
    if dict(Counter(r['dataset'] for r in rows))!=read(RQ/'configs/protocol_v1.json')['dataset_counts']:
        raise ValueError('Frozen exposed cohort differs')
    return rows

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
    Processor.__qualname__='RQ48RankingProcessor'
    return Processor

def __getattr__(name):
    if name=='RQ48RankingProcessor':
        result=make_ranking_processor()
    elif name in {'validate_vllm_metadata','vllm_tensor_wire','vllm_tensor_unwire',
                  'VLLMCacheAdmission','vllm_cache_profile'}:
        from importlib import import_module
        result=getattr(import_module('RQs.RQ4_3.src.utils'),name)
    else:
        raise AttributeError(name)
    globals()[name]=result
    return result
