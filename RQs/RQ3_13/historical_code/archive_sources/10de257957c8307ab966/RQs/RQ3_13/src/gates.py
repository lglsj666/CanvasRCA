"""Source/CPU/visual/scientific/budget/smoke gates and registered offline statistics."""
import ast
from collections import Counter, defaultdict
import json
import math
import subprocess
import time
from .utils import ROOT, VERSION, ARMS, MODEL, METRICS, path, read_json, write_json, immutable_json, source_contract, register, logical_key, stable_hash, phase_arms


def static(c):
    started=time.monotonic(); folder=ROOT/"RQs/RQ3_13"
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
    old=read_json(path(c["base_preparation"].replace("preparation","results"))/"qualification/source_freeze.json")["source_contract"]
    for name in c["global_contracts"]+[c["inference_base"]]:
        from .utils import sha_file
        if sha_file(ROOT/name)!=old["files"][name]: raise ValueError("Global scientific/model projection changed")
    report={"status":"passed","source_contract":source_contract(),"source_lines":count,"seconds":time.monotonic()-started,
        "checks":["AST/compile without module execution","all five-module import linkage","JSON/registered configuration",
                  "bash syntax","no placeholder functions","pure public compiler/renderer boundary","global recipe/scorer/split preservation"],
        "scientific_review":"Observed univariate envelope is not a fault, probability, intervention or causal-order estimator; graph-versus-pixel-text contrast and independent repeats are frozen",
        "runtime_qualification":"pending CPU, actual PNG, scientific/budget and GPU smoke"}
    write_json(path(c["results"])/"qualification/static.json",report)
    return {k:v for k,v in report.items() if k!="source_contract"}


def build_renderer(c):
    from .utils import atomic_write, sha_file, runtime
    import os
    # Only explicit deployment files; no figure or case preparation here.
    font=path("build/rq313_renderer/DejaVuSansMono.ttf")
    if not font.exists():
        source=os.environ.get("CANVASRCA_RQ313_FONT","/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf")
        atomic_write(font,__import__("pathlib").Path(source).read_bytes())
    runtime(c)
    report={"status":"built","font_sha256":sha_file(font),"renderer":source_contract()["renderer"]}
    write_json(path(c["results"])/"qualification/renderer_build.json",report)
    return {**report,"next":"static review after deployment identities materialized"}


def require_renderer_build():
    from .utils import config, sha_file
    c=config(); r=read_json(path(c["results"])/"qualification/renderer_build.json")
    if (r.get("status")!="built" or r["renderer"]!=source_contract()["renderer"]
            or r["font_sha256"]!=sha_file(path("build/rq313_renderer/DejaVuSansMono.ttf"))):
        raise ValueError("Native renderer/font identity changed")

def require_qualification(c,smoke):
    if not smoke and not c.get("full_launch_authorized",False):
        raise RuntimeError("User stop-after-smoke amendment: full experiment is not authorized")
    current=source_contract()
    names=("static","cpu","cpu_smoke","visual_review","scientific_review","budget_review")+(() if smoke else ("smoke_review",))
    for name in names:
        report=read_json(path(c["results"])/"qualification"/(name+".json"))
        if report.get("status")!="passed" or report.get("source_contract")!=current:
            raise RuntimeError("Absent/changed qualification: "+name)
        if name.startswith("cpu") and report.get("case_ids")!=[r["opaque_incident_id"] for r in register(c)["smoke" if name=="cpu_smoke" else "cases"]]:
            raise RuntimeError("CPU qualification does not cover authorized cohort")
        if name=="cpu" and not report.get("readiness_passed"):
            raise RuntimeError("No qualified observed excursions or bounded input cost")
    frozen=read_json(path(c["results"])/"qualification/source_freeze.json")
    if frozen.get("source_contract")!=current or frozen.get("status")!="frozen":
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
    if kind=="scientific" and not review.get("excursion_limitations_reviewed"):
        raise ValueError("Scientific review must address reference/observed-order/noncausal limits")
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
    if report.get("status")!="ready" or report.get("model")!=MODEL or report.get("rq313_source_contract")!=source_contract():
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
        for arm in phase_arms(c,smoke):
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
    if outcome["status"]!="complete":
        raise RuntimeError("Smoke not qualified")
    if len(rows)!=18 or any(r["status"]!="done" for r in rows):
        raise RuntimeError("All18 smoke positions must have committed outcomes")
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
            "note":"Artifact review only; human inspection of actual PNG/input/output must supply smoke_review.json"}
    write_json(root/"artifact_review.json",report)
    return {k:v for k,v in report.items() if k!="source_contract"}


def analyze(c):
    """Future complete formal-batch analysis only; never a GPU or tuning path."""
    from RQs.RQ3_1.src.main import audit_completion_artifacts
    root,rows=records(c)
    if any(r["status"]=="pending" for r in rows): raise RuntimeError("Complete formal batch required")
    if not (root/("phase_complete."+MODEL+".json")).exists(): raise RuntimeError("Atomic model phase required")
    seen=set()
    for r in rows:
        if r["status"]=="done" and r["call_key"] not in seen:
            audit_completion_artifacts(root,r["call_key"]); seen.add(r["call_key"])
    primary=[r for r in rows if r["dataset"] in c["primary_datasets"]]
    index={(r["case"],r["arm"]):r for r in primary}
    families={}
    for name in ("primary","secondary"):
        contrasts=[]
        for a,b in c[name+"_contrasts"]:
            pairs=[]
            for oid in sorted({r["case"] for r in primary}):
                x,y=index[(oid,a)],index[(oid,b)]
                if x["status"]==y["status"]=="done": pairs.append((x,y))
            groups=defaultdict(list)
            for x,y in pairs: groups[x["event_group"]].append(x["metrics"]["mrr"]-y["metrics"]["mrr"])
            contrasts.append({"a":a,"b":b,"case":paired_stats([x["metrics"]["mrr"]-y["metrics"]["mrr"] for x,y in pairs]),
                "event_group":paired_stats([sum(v)/len(v) for v in groups.values()]),
                "dataset_deltas":{d:paired_stats([x["metrics"]["mrr"]-y["metrics"]["mrr"] for x,y in pairs if x["dataset"]==d]) for d in c["primary_datasets"]},
                "paired_case_ids":[x["case"] for x,y in pairs],"exclusions":120-len(pairs)})
        holm(contrasts,"case"); holm(contrasts,"event_group"); families[name]=contrasts
    report={"status":"complete_offline_statistics","registered_families":families,"counts":summarize(c),
        "metrics":{d:{a:{"n":len(v:=[r for r in rows if r["dataset"]==d and r["arm"]==a and r["status"]=="done"]),
            **{m:sum(r["metrics"][m] for r in v)/len(v) if v else None for m in METRICS}} for a in ARMS} for d in c["case_counts"]},
        "adoption":"requires full cost/usage and explanation review; statistics alone are insufficient",
        "ci":"not requested or computed","unique_completion_graphs":len(seen)}
    write_json(root/"analysis.json",report)
    return report


def paired_stats(deltas):
    import numpy as np
    from scipy.stats import wilcoxon
    d=np.round(np.asarray(deltas,dtype=float),12)
    if not len(d):
        return {"n":0,"delta":None,"p":1.,"dz":None,"better":0,"worse":0,"tied":0}
    sd=float(d.std(ddof=1)) if len(d)>1 else 0.
    return {"n":len(d),"delta":float(d.mean()),"p":float(wilcoxon(d,zero_method="pratt").pvalue) if np.any(d) else 1.,
            "dz":float(d.mean()/sd) if sd else None,"better":int((d>0).sum()),"worse":int((d<0).sum()),"tied":int((d==0).sum())}


def holm(rows,field=None):
    adjusted=0.
    ordered=sorted(rows,key=lambda r:(r[field] if field else r)["p"])
    for i,row in enumerate(ordered):
        value=row[field] if field else row
        adjusted=max(adjusted,min(1.,value["p"]*(len(ordered)-i)))
        value["p_holm"]=adjusted
