"""Source/CPU/visual/scientific/budget/smoke gates and registered offline statistics."""
import ast
from collections import Counter, defaultdict
import json
import math
import subprocess
import time
from .utils import ROOT, VERSION, ARMS, MODEL, METRICS, path, read_json, write_json, immutable_json, source_contract, register, logical_key, stable_hash, phase_arms


def static(c):
    started=time.monotonic(); folder=ROOT/"RQs/RQ3_16"
    files=sorted((folder/"src").glob("*.py"))
    if {f.stem for f in files}!={"__init__","main","utils","exps","tests","gates"}:
        raise ValueError("Five functional modules plus package marker required")
    trees={f.stem:ast.parse(f.read_text(),filename=str(f)) for f in files}
    for f in files: compile(trees[f.stem],str(f),"exec")
    count=sum(sum(bool(l.strip()) and not l.lstrip().startswith("#") for l in f.read_text().splitlines()) for f in files)
    if count>7500: raise ValueError("Functional source line limit")
    for file in (folder/"configs").glob("*.json"): json.loads(file.read_text())
    shells=list((folder/"scripts").glob("*.sh"))
    if len(shells)>10 or sum(len(p.read_text().splitlines()) for p in shells)>800: raise ValueError("Shell limit")
    for file in shells: subprocess.run(["bash","-n",str(file)],check=True)
    exports={name:{n.name for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
             | {a.asname or a.name for n in tree.body if isinstance(n,(ast.Import,ast.ImportFrom)) for a in n.names}
             | {n.id for p in tree.body if isinstance(p,(ast.Assign,ast.AnnAssign)) for n in ast.walk(p) if isinstance(n,ast.Name)}
             for name,tree in trees.items()}
    for stem,tree in trees.items():
        for node in ast.walk(tree):
            if isinstance(node,ast.ImportFrom) and node.level and node.module in exports:
                if any(a.name not in exports[node.module] for a in node.names): raise ValueError("Broken local import:"+stem)
            if isinstance(node,ast.FunctionDef):
                body=[n for n in node.body if not (isinstance(n,ast.Expr) and isinstance(n.value,ast.Constant) and isinstance(n.value.value,str))]
                if not body or all(isinstance(n,ast.Pass) for n in body): raise ValueError("Placeholder function")
    for text in ("read_json(","score_response_callback","accepted_labels","numeric_to_natural"):
        if text in (folder/"src/exps.py").read_text(): raise ValueError("IO/evaluator in pure renderer/compiler")
    for tree in trees.values():
        for node in ast.walk(tree):
            if isinstance(node,ast.ImportFrom) and (node.module or "").startswith(("PIL.ImageDraw","matplotlib")):
                raise ValueError("Experiment bypasses unified renderer")
    old=read_json(path(c["base_preparation"].replace("preparation","results"))/"qualification/source_freeze.json")["source_contract"]
    for name in c["global_contracts"]+[c["inference_base"]]:
        from .utils import sha_file
        if sha_file(ROOT/name)!=old["files"][name]: raise ValueError("Global scientific/model projection changed")
    protection=read_json(path(c["results"])/"qualification/prechange_protection.json")
    from .utils import sha_file
    for name,digest in protection["source_files"].items():
        if name not in protection["allowed_forward_renderer_changes"] and sha_file(ROOT/name)!=digest:
            raise ValueError("Protected historical dependency changed: "+name)
    if len(list((folder/"descriptions").glob("*.md")))!=3: raise ValueError("Exactly three canonical descriptions required")
    if c["full_launch_authorized"]: raise ValueError("Full execution must remain disabled")
    report={"status":"passed","source_contract":source_contract(),"source_lines":count,"seconds":time.monotonic()-started,
        "checks":["AST/compile without module execution","all five-module import linkage","JSON/registered configuration",
                  "bash syntax","no placeholder functions","pure public compiler/renderer boundary","global recipe/scorer/split preservation"],
        "scientific_review":"Marginal mark contribution and output-cardinality factorial; same facts, no causal proof, no posthoc root routing",
        "runtime_qualification":"pending CPU, actual PNG, scientific/budget and GPU smoke"}
    write_json(path(c["results"])/"qualification/static.json",report)
    return {k:v for k,v in report.items() if k!="source_contract"}


def build_renderer(c):
    from renderer.main import node_runtime
    from .utils import runtime
    import os
    env={**os.environ,"PATH":str(node_runtime().parent)+os.pathsep+os.environ["PATH"]}
    for command in (["npm","run","typecheck"],["npm","run","build"]):
        subprocess.run(command,cwd=ROOT/"src/renderer/web",env=env,check=True)
    runtime(c)
    report={"status":"built","renderer":source_contract()["renderer"]}
    write_json(path(c["results"])/"qualification/renderer_build.json",report)
    return report


def require_renderer_build():
    from .utils import config
    c=config(); report=read_json(path(c["results"])/"qualification/renderer_build.json")
    if report.get("status")!="built" or report["renderer"]!=source_contract()["renderer"]:
        raise ValueError("Unified renderer source/build differs")


def qualified_contract(c,current):
    """Preserve measured qualification across explicit execution activation.

    Only these two authorization/compatibility functions may change. Original
    archives and reviews stay immutable; every scientific dependency and all
    other gate AST nodes must equal the measured source.
    """
    root=path(c["results"])/"qualification"
    frozen=read_json(root/"source_freeze.json")
    if frozen.get("status")!="frozen":
        raise ValueError("Measured source freeze missing")
    original=frozen["source_contract"]
    if original==current:
        return original
    migration=read_json(root/"activation_v1/source_compatibility.json")
    if (migration.get("status")!="passed" or migration.get("qualified_source_contract")!=original
            or migration.get("effective_source_contract")!=current):
        raise RuntimeError("No measured-source compatibility for current execution")
    from .utils import sha_file
    import tarfile
    gate="RQs/RQ3_16/src/gates.py"
    if (set(original["files"])!=set(current["files"]) or original["renderer"]!=current["renderer"]
            or {f for f in current["files"] if current["files"][f]!=original["files"][f]}!={gate}
            or sha_file(root/"frozen_source.tar.gz")!=frozen["archive_sha256"]
            or sha_file(root/"activation_v1/frozen_source.tar.gz")!=migration["effective_archive_sha256"]):
        raise RuntimeError("Execution activation changed a scientific dependency/archive")
    with tarfile.open(root/"frozen_source.tar.gz","r:gz") as archive:
        before=ast.parse(archive.extractfile(gate).read().decode())
    after=ast.parse((ROOT/gate).read_text())
    permitted={"qualified_contract","full_authorized"}
    def remainder(tree):
        tree.body=[n for n in tree.body if not isinstance(n,ast.FunctionDef) or n.name not in permitted]
        return ast.dump(tree,include_attributes=False)
    if remainder(before)!=remainder(after):
        raise RuntimeError("Non-operational gate/statistics/reviewer code changed")
    return original


def full_authorized(c,current):
    """Bind explicit user authorization without rewriting the frozen config."""
    file=path(c["results"])/"qualification/activation_v1/full_authorization.json"
    if not file.exists():
        raise RuntimeError("Formal execution requires explicit user authorization")
    authorization=read_json(file)
    if (authorization.get("status")!="authorized" or authorization.get("authority")!="explicit_user_request"
            or authorization.get("version")!=VERSION or authorization.get("model")!=MODEL
            or authorization.get("config_hash")!=stable_hash(c)
            or authorization.get("effective_source_contract_hash")!=stable_hash(current)
            or authorization.get("registration_hash")!=stable_hash(register(c))
            or authorization.get("registered_positions")!=c["formal_positions"]
            or authorization.get("formal_attempt_limit")!=c["formal_attempt_limit"]
            or not authorization.get("user_request")):
        raise RuntimeError("Full execution receipt does not bind this qualified matrix")


def require_qualification(c,smoke):
    current=source_contract()
    if not smoke:
        full_authorized(c,current)
    qualified=qualified_contract(c,current)
    names=("static","cpu","cpu_smoke","visual_review","scientific_review","budget_review")+(() if smoke else ("smoke_review",))
    for name in names:
        report=read_json(path(c["results"])/"qualification"/(name+".json"))
        if report.get("status")!="passed" or report.get("source_contract")!=qualified:
            raise RuntimeError("Absent/changed qualification: "+name)
        if name.startswith("cpu") and report.get("case_ids")!=[r["opaque_incident_id"] for r in register(c)["smoke" if name=="cpu_smoke" else "cases"]]:
            raise RuntimeError("CPU qualification does not cover authorized cohort")
        if name=="cpu" and not report.get("readiness_passed"):
            raise RuntimeError("Whole-roster input cost/capacity not qualified")
    frozen=read_json(path(c["results"])/"qualification/source_freeze.json")
    if frozen.get("source_contract")!=qualified or frozen.get("status")!="frozen":
        raise RuntimeError("Runtime source freeze missing/changed")
    for row in register(c)["smoke" if smoke else "cases"]:
        marker=read_json(path(c["preparation"])/"flags"/(row["opaque_incident_id"]+".json"))
        if marker.get("version")!=VERSION or marker.get("status")!="done":
            raise RuntimeError("Uncommitted preparation")


def accept_review(c,kind,file):
    """Record concrete future primary-agent reviews; never infer them from static."""
    if kind not in {"scientific","visual","smoke","budget"}:
        raise ValueError("Unknown review kind")
    review=read_json(path(file))
    if review.get("status")!="passed" or review.get("source_contract")!=source_contract() or not review.get("reviewer"):
        raise ValueError("Review must identify reviewer and current source")
    if kind=="visual" and (not review.get("inspected_pngs") or not review.get("deterministic_rerender")):
        raise ValueError("Actual PNG and determinism review required")
    if kind=="scientific" and not review.get("representation_limitations_reviewed"):
        raise ValueError("Scientific review must address same-fact/repetition/native-unit/noncausal limits")
    if kind=="smoke" and (not review.get("actual_inputs_outputs_reviewed") or read_json(path(c["results"])/"smoke/artifact_review.json").get("status")!="passed"):
        raise ValueError("Actual smoke artifacts and output review required")
    if kind=="budget":
        spent=review.get("verified_major_spent")
        if (not isinstance(spent,int) or isinstance(spent,bool) or spent<0 or not review.get("ledger_evidence")
                or review.get("major_ceiling")!=c["major_budget"]["ceiling"] or spent+c["total_attempt_limit"]>c["major_budget"]["ceiling"]):
            raise ValueError("Current major budget evidence/allocation does not fit")
        evidence=review["ledger_evidence"]
        if not isinstance(evidence,list): raise ValueError("Concrete ledger evidence list required")
        from .utils import sha_file
        import sqlite3
        counted=0; seen=set()
        for entry in evidence:
            file=path(entry["file"])
            if file in seen or sha_file(file)!=entry["sha256"]:
                raise ValueError("Duplicate/changed major budget evidence")
            seen.add(file)
            if entry["kind"]=="sqlite":
                with sqlite3.connect(file.resolve().as_uri()+"?mode=ro",uri=True) as db:
                    count=db.execute("SELECT COUNT(*) FROM calls").fetchone()[0]
            elif entry["kind"]=="json_counter":
                value=read_json(file)
                for key in entry["keys"]: value=value[key]
                count=value
            else: raise ValueError("Unknown budget ledger format")
            if not isinstance(count,int) or isinstance(count,bool) or count<0 or count!=entry["initiated"]:
                raise ValueError("Major ledger count mismatch")
            counted+=count
        if counted!=spent:
            raise ValueError("Major budget sum does not match cited ledgers")
    immutable_json(path(c["results"])/"qualification"/(kind+"_review.json"),review)
    return {"status":"review_recorded","kind":kind}


def freeze(c):
    """Archive source only after complete CPU/reviewer gates; never start a GPU."""
    import tarfile
    from .utils import sha_file
    current=source_contract(); root=path(c["results"])/"qualification"
    for name in ("static","cpu","cpu_smoke","visual_review","scientific_review","budget_review"):
        report=read_json(root/(name+".json"))
        if report.get("status")!="passed" or report.get("source_contract")!=current:
            raise RuntimeError("Cannot freeze before current qualification: "+name)
    archive=root/"frozen_source.tar.gz"
    if archive.exists():
        value=read_json(root/"source_freeze.json")
        if value["source_contract"]!=current or value["archive_sha256"]!=sha_file(archive):
            raise ValueError("Historical source archive changed")
        return {"status":"already_frozen"}
    temporary=root/"frozen_source.tar.gz.tmp"
    names=set(current["files"])|{"src/renderer/"+n for n in current["renderer"]["files"]}
    with tarfile.open(temporary,"w:gz") as tar:
        for name in sorted(names): tar.add(ROOT/name,arcname=name)
    temporary.replace(archive)
    immutable_json(root/"source_freeze.json",{"status":"frozen","source_contract":current,"archive_sha256":sha_file(archive),
        "runtime_checkpoint_audit":read_json(root/"cpu.json")["checkpoint_audit"]})
    return {"status":"frozen","files":len(names)}


def require_runtime_attestation(c,root):
    report=read_json(root/"attestation.json")
    if report.get("status")!="ready" or report.get("model")!=MODEL or report.get("rq316_source_contract")!=source_contract():
        raise RuntimeError("Current runtime has no matching source/model attestation")
    from .utils import runtime,sha_file
    profile,spec=runtime(c)
    if report.get("recipe")!=spec or report.get("profile_sha256")!=sha_file(profile.source):
        raise RuntimeError("Attested effective recipe/profile differs from registered runtime")


def records(c,smoke=False):
    reg=register(c)
    root=path(c["results"])/("smoke" if smoke else "formal")
    rows=[]
    for r in reg["smoke" if smoke else "cases"]:
        oid=r["opaque_incident_id"]
        for arm in phase_arms(c,smoke,r):
            file=root/"flags"/(logical_key(oid,arm)+".json")
            value=read_json(file) if file.exists() else {"status":"pending"}
            rows.append({**value,"case":oid,"arm":arm,"dataset":r["dataset"],
                         "event_group":reg["groups"].get(oid,r["leakage_group"])})
    return root,rows


def summarize(c,smoke=False):
    _,rows=records(c,smoke)
    states=dict(Counter(r["status"] for r in rows))
    return {"status":"incomplete" if states.get("pending") else "complete", "positions":len(rows),"counts":states,
            "by_arm":{a:dict(Counter(r["status"] for r in rows if r["arm"]==a)) for a in ARMS},
            "reference_positions":sum(bool(r.get("no_op")) for r in rows)}


def review_smoke(c):
    from RQs.RQ3_1.src.main import audit_completion_artifacts
    from vlmrca.run_state import DurableCallRegister
    root,rows=records(c,True)
    outcome=read_json(root/"supervisor.json")
    if outcome["status"] not in {"complete","bounded_timeout"}:
        raise RuntimeError("Smoke not qualified")
    if len(rows)!=18 or any(r["status"] not in {"done","pending","fail"} for r in rows):
        raise RuntimeError("Foreign/missing smoke matrix")
    if any(r["status"]=="fail" and r.get("failure_class")!="request_timeout" for r in rows):
        raise RuntimeError("Non-timeout smoke failure")
    if any(r["status"]=="pending" for r in rows) and outcome["status"]!="bounded_timeout":
        raise RuntimeError("Unexplained missing smoke results")
    seen=set(); audits=[]
    for r in rows:
        if r["status"]!="done" or r["call_key"] in seen:
            continue
        seen.add(r["call_key"])
        audit_completion_artifacts(root,r["call_key"])
        result=read_json(root/"outputs"/(r["call_key"]+".json"))
        score=result.get("score",{}); metrics=score.get("metrics",score)
        if any(not isinstance(metrics.get(k),(int,float)) or not math.isfinite(metrics[k]) for k in METRICS):
            raise ValueError("Nonfinite smoke scoring")
        audits.append({"case":r["case"],"arm":r["arm"],"call_key":r["call_key"],"status":result.get("status")})
    report={"status":"passed","source_contract":source_contract(),"outcome":outcome,"completed_audits":audits,
            "accounting":DurableCallRegister(root/"calls.sqlite",scope=VERSION,limit=c["smoke_attempt_limit"]).summary(),
            "coverage_complete":all(r['status']=='done' for r in rows),
            "unfinished_positions":[{'case':r['case'],'arm':r['arm'],'status':r['status']} for r in rows if r['status']!='done'],
            "timeout_only_policy":"Codex.md: timeout alone passes the logical smoke; incomplete coverage remains explicit",
            "note":"Artifact review only; human inspection of actual PNG/input/output must supply smoke_review.json"}
    write_json(root/"artifact_review.json",report)
    return {k:v for k,v in report.items() if k!="source_contract"}


def paired(values):
    """Registered Pratt-zero test; all-zero and zero-variance are explicit."""
    import numpy as np
    from scipy.stats import wilcoxon
    x=np.round(np.asarray(values,dtype=float),12)
    if not len(x): return {'n':0,'delta':None,'p':None,'dz':None,'positive':0,'negative':0,'equal':0}
    if not np.isfinite(x).all(): raise ValueError('Nonfinite paired differences')
    sd=float(x.std(ddof=1)) if len(x)>1 else 0.
    return {'n':len(x),'delta':float(x.mean()),
            'p':float(wilcoxon(x,zero_method='pratt',alternative='two-sided').pvalue) if np.any(x) else 1.,
            'dz':float(x.mean()/sd) if sd else None,'dz_undefined_zero_variance':sd==0,
            'positive':int((x>0).sum()),'negative':int((x<0).sum()),'equal':int((x==0).sum())}


def holm(rows):
    """Unestimable tests still occupy their registered family position."""
    previous=0.
    for i,row in enumerate(sorted(rows,key=lambda x:1. if x['p'] is None else x['p'])):
        if row['p'] is None: row['holm_p']=None; continue
        previous=max(previous,min(1.,row['p']*(len(rows)-i)));row['holm_p']=previous
    return rows


def contrast(cases,coefficients,metric='mrr'):
    """Complete-case linear contrast plus partial-information score bounds.

    Every unknown arm score independently occupies [0,1]. Thus a missing
    interaction may span [-2,2], while known components tighten its bounds.
    Group tests average the same observed case contrasts within frozen events;
    full-roster bounds separately retain all cases and all registered groups.
    """
    if not coefficients or abs(sum(coefficients.values()))>1e-12: raise ValueError('Not a zero-sum contrast')
    differences=[];groups=defaultdict(list);bounds=[];group_bounds=defaultdict(list);missing=[]
    for row in cases:
        values={a:row['arms'][a]['metrics'].get(metric) if row['arms'][a].get('metrics') is not None else None for a in coefficients}
        low=high=0.;group=(row['dataset'],row['event_group'])
        for arm,k in coefficients.items():
            v=values[arm]
            if v is None: low+=min(0,k);high+=max(0,k)
            else:
                if not math.isfinite(v) or not 0<=v<=1: raise ValueError('Invalid scored metric')
                low+=k*v;high+=k*v
        bounds.append((low,high));group_bounds[group].append((low,high))
        if any(v is None for v in values.values()): missing.append(row['case']);continue
        value=round(sum(coefficients[a]*v for a,v in values.items()),12)
        differences.append(value);groups[group].append(value)
    n=len(cases)
    mean=lambda xs:sum(xs)/len(xs) if xs else None
    interval=[mean([b[i] for b in bounds]) for i in (0,1)]
    grouped_interval=[mean([mean([b[i] for b in bs]) for bs in group_bounds.values()]) for i in (0,1)]
    return {'coefficients':coefficients,'metric':metric,'registered_n':n,'missing_cases':missing,
            'case':paired(differences),'event_group':paired([mean(v) for v in groups.values()]),
            'full_denominator_bounds':interval,'full_group_bounds':grouped_interval,
            'registered_groups':len(group_bounds),'observed_group_case_counts':{'|'.join(k):len(v) for k,v in groups.items()}}


def statistical_families(c,cases):
    families={}
    for name,metric in [('primary_mrr','mrr'),('secondary_mrr','mrr'),('secondary_ac5','ac@5')]:
        rows=[]
        if name=='primary_mrr':
            definitions=[({a:1,b:-1},scope) for a,b,scope in c['primary_contrasts']]
        else:
            definitions=[({a:1,b:-1},'all') for a,b in c['secondary_contrasts']]+[(c['secondary_interaction'],'all')]
        for coefficients,scope in definitions:
            subset=[r for r in cases if scope=='all' or r['dataset']==scope or scope=='aiops' and r['dataset'] in c['primary_datasets']]
            rows.append({'scope':scope,**contrast(subset,coefficients,metric)})
        for level in ('case','event_group'): holm([r[level] for r in rows])
        families[name]=rows
    return families


def analyze(c):
    """Future terminal-matrix analysis; no model calls or result rewriting."""
    root,rows=records(c)
    if any(r['status']=='pending' for r in rows): raise RuntimeError('Complete registered matrix required for formal analysis')
    grouped={};costs={}
    for row in rows:
        oid,arm=row['case'],row['arm']
        grouped.setdefault(oid,{'case':oid,'dataset':row['dataset'],'event_group':row['event_group'],'arms':{}})
        item={'status':row['status'],'metrics':row.get('metrics'),'reference':bool(row.get('no_op')),'usage':None,'list_length':None}
        if row['status']=='done':
            key=row['call_key'];output=read_json(root/'outputs'/(key+'.json'))
            item['model_status']=output['status']
            try:
                answer=json.loads(output['response']);item['list_length']=len(answer['services'])
            except (ValueError,KeyError,TypeError): item['list_length']=None
            cost=read_json(root/'cost'/(key+'.json'));costs[key]=cost
            if all(isinstance(cost.get(k),(int,float)) and math.isfinite(cost[k]) and cost[k]>=0 for k in ('input_tokens','output_tokens','total_tokens')):
                item['usage']={k:cost[k] for k in ('input_tokens','output_tokens','total_tokens','image_tokens')}
        grouped[oid]['arms'][arm]=item
    cases=list(grouped.values());absolute=[]
    for dataset in ['all',*c['case_counts']]:
        subset=[r for r in cases if dataset=='all' or r['dataset']==dataset]
        for arm in ARMS:
            values=[r['arms'][arm] for r in subset];known=[r for r in values if r['metrics'] is not None]
            metric={m:sum(r['metrics'][m] for r in known)/len(known) if known else None for m in METRICS}
            bounds={m:[sum(r['metrics'][m] for r in known)/len(values),(sum(r['metrics'][m] for r in known)+len(values)-len(known))/len(values)] for m in METRICS}
            usage=[r['usage'] for r in values if r['usage'] is not None]
            lengths=[r['list_length'] for r in values if r['list_length'] is not None]
            absolute.append({'dataset':dataset,'arm':arm,'registered':len(values),'known':len(known),'metrics':metric,
                             'full_denominator_bounds':bounds,'usage_known':len(usage),
                             'mean_input_output':sum(r['total_tokens'] for r in usage)/len(usage) if usage else None,
                             'mean_returned_length':sum(lengths)/len(lengths) if lengths else None,
                             'fixed_five_noncompliant':sum(n!=5 for n in lengths) if arm.endswith('FIVE') or arm=='MARGINAL_REPEAT' else None})
    macro={}
    for arm in ARMS:
        macro[arm]={}
        for metric in METRICS:
            values=[next(r['metrics'][metric] for r in absolute if r['dataset']==d and r['arm']==arm) for d in c['case_counts']]
            macro[arm][metric]=sum(values)/len(values) if all(v is not None for v in values) else None
    paired_cost=[]
    for dataset in c['case_counts']:
        subset=[r for r in cases if r['dataset']==dataset]
        for control,limit in [('BASE_FIVE',1.2),('PAIR_FIVE',1.1)]:
            available=[r for r in subset if all(r['arms'][a]['usage'] is not None for a in ('MARGINAL_FIVE',control))]
            den=sum(r['arms'][control]['usage']['total_tokens'] for r in available)
            ratio=sum(r['arms']['MARGINAL_FIVE']['usage']['total_tokens'] for r in available)/den if den else None
            paired_cost.append({'dataset':dataset,'control':control,'known':len(available),'registered':len(subset),'ratio':ratio,'limit':limit})
    report={'status':'complete_statistics_pending_reason_review','source_contract':source_contract(),'cases':cases,
            'absolute':absolute,'macro':macro,'families':statistical_families(c,cases),'paired_total_cost':paired_cost,
            'unique_successful_billed_calls':len(costs),'unknown_usage_not_zero':True,'CI_reported':False,
            'note':'Development evidence only; adoption also requires full artifact/reason review and all preregistered thresholds.'}
    write_json(root/'analysis/statistics.json',report)
    return {'status':report['status'],'cases':len(cases),'path':str(root/'analysis/statistics.json')}
