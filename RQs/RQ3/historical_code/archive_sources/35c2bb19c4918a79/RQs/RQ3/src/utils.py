"""RQ3 data isolation, durable call accounting, rewards and paired statistics."""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import sqlite3
import time
from collections import defaultdict
from contextlib import contextmanager
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

import numpy as np
from unified_scripts import canonical_json, stable_hash
from unified_scripts.dataset_segmentation import DatasetSegmentationConfig, allocate_intact_groups as allocate_groups, connected_row_groups
from vlmrca.run_state import (read_json, sha_file, callable_fingerprint,
    lossless_json_archive, archive_response_attention, archive_derived_attention)
from vlmrca.training import chat_token_ids
from RQs.RQ2.src.utils import AsyncWriter as AsyncWriter, atomic_write as atomic_write, write_json as write_json

ROOT = Path(__file__).resolve().parents[3]
PRIMARY = ("aegislab", "aiops2022", "aiops2025")
TRAIN_DATASETS = ("aiops2022", "aiops2025")








def composer_model_path(config):
    value = Path(os.environ.get(config["composer"]["model_path_env"], config["composer"]["model_path"]))
    return value if value.is_absolute() else ROOT / value


@lru_cache(maxsize=2)
def _local_tokenizer(path):
    from transformers import AutoTokenizer
    return AutoTokenizer.from_pretrained(path, local_files_only=True)


def composer_tokenizer(config):
    return _local_tokenizer(str(composer_model_path(config).resolve()))


def composer_input_budget(config):
    """Reserve output and a guard, even when an operator lowers context length."""
    source, harness = config["composer"], config["harness"]
    if harness["catalog_policy"] != "budgeted_region_entity_catalog_v2":
        raise ValueError("obsolete Composer catalogue policy")
    maximum = int(source["max_model_len"])
    output = int(source["max_tokens"])
    guard = int(harness["catalog_context_guard_tokens"])
    target = int(harness["catalog_input_token_target"])
    if min(maximum, output, target) <= 0 or guard < 0:
        raise ValueError("invalid Composer context/output budget")
    available = min(target, maximum - output - guard)
    if available <= 0:
        raise ValueError("Composer has no input budget after output reservation")
    return available


def catalogue_contract(config):
    """Hash the input compiler, not unrelated lifecycle/training dispatch."""
    import inspect
    from . import exps
    model_path = composer_model_path(config)
    files = ("tokenizer.json", "tokenizer_config.json", "chat_template.jinja", "special_tokens_map.json")
    tokenizer = {name: sha_file(model_path / name) for name in files if (model_path / name).is_file()}
    if not tokenizer:
        raise ValueError("Composer tokenizer files are missing")
    functions=[exps.evidence_cards,exps._catalog_order,exps._catalog_preview,exps.composer_parts,
               exps.composer_messages,exps.build_catalog,exps.observation,exps.program_schema,
               exps.default_design,chat_token_ids,composer_tokenizer,composer_input_budget]
    return stable_hash({"schema": "RQ3BudgetedCatalogCacheV4", "seed": config["seed"],
                        "harness": config["harness"], "composer": config["composer"],
                        "tokenizer": tokenizer,"pool_contract":pool_contract(config),
                        "guide":exps.COMPOSER_SYSTEM,"regions":exps.REGIONS,
                        "encodings":exps.ENCODINGS,"design_fields":exps.DESIGN_FIELDS,
                        "observation_schema":inspect.getsource(exps.ComposerObservationV1),
                        "chat_client":sha_file(ROOT/'src/vlmrca/vlm/client.py'),
                        "serialization":sha_file(ROOT/'src/unified_scripts/__init__.py'),
                        "implementation":{f.__name__:callable_fingerprint(f) for f in functions}})


def pool_contract(config):
    """The one evidence compiler, independent of catalogue/training dispatch.

    A later operational phase handler must not invalidate an unchanged pool.
    Keep exact compiler/analyzer/loader hashes, not merely a schema string.
    """
    import inspect
    from . import exps
    functions=('build_pool','relative_metric_clocks','_safe_tree','log_template','readable_log_graph')
    files=[ROOT/'RQs/RQ2/src/exps.py',ROOT/'RQs/RQ2/src/utils.py',
           ROOT/'src/vlmrca/evidence.py',ROOT/'src/vlmrca/processed.py',ROOT/'src/vlmrca/log_calendar.py',ROOT/'src/vlmrca/entity_identity.py',ROOT/'src/vlmrca/metric_calendar.py',
           *sorted((ROOT/'RQs/RQ3/src/renderer').glob('*.py'))]
    body={'schema':'RQ3EvidencePoolCacheV1','seed':config['seed'],'compiler_version':exps.POOL_VERSION,
          'entity_identity_policy':config['harness'].get('entity_identity_policy','legacy_v1'),
          'public_hosting':config['harness'].get('public_hosting',False),
          'public_membership':config['harness'].get('public_membership',False),
          'regions':exps.REGIONS,'metric_clock_pattern':exps.METRIC_CLOCK.pattern,
          'log_token_pattern':exps.LOG_TOKEN.pattern,
          'functions':{name:stable_hash(inspect.getsource(getattr(exps,name))) for name in functions},
          'dependencies':{str(p.relative_to(ROOT)):sha_file(p) for p in files}}
    return stable_hash(body)


def preparation_identity_matches(observed,current,kind):
    if observed==current:return True
    if kind not in {'pool','catalogue'}:return False
    for repair in ('renderer_sort_repair_v1','numeric_geometry_repair_v1','checkpoint_retention_v1','heatmap_render_repair_v1','matrix_axis_repair_v1','source_bins_repair_v1','validation_startup_repair_v1','readable_layout_repair_v1','readable_layout_repair_v2'):
        path=ROOT/'RQs/RQ3/results'/repair/'compatibility.json'
        if not path.exists():continue
        proof=read_json(path)
        if (proof.get('status')!='passed' or current!=proof['after'].get(kind) or
            observed not in proof.get('accepted_before',{}).get(kind,[proof['before'].get(kind)])):continue
        files=proof.get('after_files') if repair!='renderer_sort_repair_v1' else {'RQs/RQ3/src/renderer/designs.py':proof['after']['renderer']}
        if files and all((ROOT/f).is_file() and sha_file(ROOT/f)==h for f,h in files.items()):return True
    return False


def epoch(value):
    if isinstance(value, (float, int)):
        return float(value)
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    return (parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)).timestamp()


def overlap(a, b):
    return a["source"] == b["source"] and max(a["start"], b["start"]) <= min(a["end"], b["end"])


def related(a, b):
    return (bool(a["event"]) and a["event"] == b["event"]) or overlap(a, b)


def window_record(dataset, row, private):
    meta = private["source_metadata"]
    if dataset == "aiops2022":
        center = epoch(private["event"]["absolute_timestamp"])
        width = float(meta["window_sec"])
        start, end = center - width, center + width
        source = str(meta["cloudbed"])
        event = f"{source}:{center}"
    elif dataset == "aiops2025":
        start, end = epoch(meta["telemetry_start_utc"]), epoch(meta["telemetry_end_utc"])
        source = "aiops2025"  # Conservatively treat all source tables as one system.
        event = str(meta.get("uuid") or "")
    else:
        raise ValueError("training window audit may only open AIOPS metadata")
    if not math.isfinite(start + end) or end < start:
        raise ValueError("invalid source window")
    return {"dataset": dataset, "case_id": row["case_id"],
            "opaque_incident_id": row["opaque_incident_id"],
            "source": source, "event": event, "start": start, "end": end}


def components(rows):
    """Connected components, including transitive overlap chains."""
    return connected_row_groups(rows, related)


def require_split_targets(split, config):
    """Do not turn an incomplete inventory into a balanced training split."""
    targets = config["data"]["targets"]
    if set(targets) != set(TRAIN_DATASETS):
        raise ValueError("RQ3 training targets must contain exactly the two AIOPS datasets")
    if targets[TRAIN_DATASETS[0]] != targets[TRAIN_DATASETS[1]]:
        raise ValueError("RQ3 requires equal train and validation counts across datasets")
    shortages = {}
    for dataset in TRAIN_DATASETS:
        for partition in ("train", "validation"):
            actual = sum(r["dataset"] == dataset for r in split[partition])
            expected = targets[dataset][partition]
            if type(expected) is not int or expected <= 0:
                raise ValueError("partition targets must be positive integers")
            if actual != expected:
                shortages[f"{dataset}/{partition}"] = {"actual": actual, "required": expected}
    if shortages:
        raise ValueError(f"balanced split is not materialized; preserve isolation: {shortages}")


def partition_rows(config, split, partition):
    """Eval evidence opens only after the complete validation-selection commit."""
    if partition in {'train','validation'}:return split[partition]
    if partition=='tournament':
        t=config.get('tournament',{})
        if (t.get('schema') not in {'RQ3EliminationTournamentV1','RQ3EliminationTournamentV2'} or t.get('roster')!=config['eval_roster']
                or t.get('optimizer_eval_overlap_allowed') is not False
                or t.get('cases')!=480 or config['solver'].get('attention')!='off'):
            raise ValueError('adaptive tournament partition requires its explicit contract')
        if sha_file(ROOT/t['roster'])!=split.get('eval_roster_sha256'):
            raise ValueError('tournament roster differs from the protected split')
        return canonical_eval_rows(config,split)
    if partition!='eval':raise ValueError('unregistered preparation partition')
    freeze=Path(config.get('evaluation_freeze',''))
    if not str(config.get('evaluation_freeze','')):raise ValueError('eval requires frozen validation policies')
    freeze=(ROOT/freeze).resolve();owner=(ROOT/'RQs/RQ3/results').resolve()
    if not freeze.is_relative_to(owner):raise ValueError('eval freeze outside RQ3')
    saved=read_json(freeze);run=freeze.parent.parent
    plan=formal_phase_plan(split,config)
    if (saved.get('split_hash')!=split['split_hash'] or saved.get('plan_hash')!=plan['plan_hash']
            or saved.get('evaluation_used') is not False):raise ValueError('eval freeze does not match isolated validation')
    expected=set(config['experiments']['exp_frozen_solver_generalization']['learned'])
    if set(saved['policies'])!=expected:raise ValueError('incomplete frozen learned-policy set')
    state=read_json(run/'phases/freeze_validation_selected_policies.json')
    if (state.get('status')!='complete' or state.get('plan_hash')!=plan['plan_hash'] or
        state.get('artifact_hashes',{}).get(str(freeze.relative_to(run)))!=sha_file(freeze)):
        raise ValueError('policy selection phase was not committed')
    for policy,spec in saved['policies'].items():
        if policy=='BASE':
            if spec.get('checkpoint') is not None:raise ValueError('BASE cannot use trained weights')
            continue
        checkpoint=(ROOT/spec['checkpoint']).resolve()
        if not checkpoint.is_relative_to(owner):raise ValueError('selected checkpoint outside RQ3')
        verified_checkpoint(checkpoint,allow_inference_only=True)
        if sha_file(checkpoint/'checkpoint.json')!=spec['checkpoint_sha256']:
            raise ValueError('selected validation checkpoint changed before eval')
    return canonical_eval_rows(config,split)


def canonical_eval_rows(config, split):
    """Source-identity projection only; callers enforce their phase authority."""
    rows=[]
    for dataset,ids in split['eval'].items():
        manifest=ROOT/config['processed_root']/'private'/dataset/'manifest.jsonl'
        by_case={}
        for line in manifest.read_text().splitlines():
            if not line.strip():continue
            row=json.loads(line)
            if row['case_id'] in by_case:raise ValueError('duplicated canonical eval identity')
            by_case[row['case_id']]=row['opaque_incident_id']
        for case_id in ids:
            rows.append({'dataset':dataset,'case_id':case_id,'opaque_incident_id':by_case[case_id]})
    if len(rows)!=480 or len({r['opaque_incident_id'] for r in rows})!=480:
        raise ValueError('frozen eval roster lost one-to-one canonical identity')
    return rows


def tournament_register(config, *, allow_policy_migration=False):
    from vlmrca.run_state import SuccessCoverageRegister
    t=config['tournament']; split=RQ3SegmentationAdapter(config).build()
    rows=partition_rows(config,split,'tournament')
    primary=[r['opaque_incident_id'] for r in rows if r['dataset'] in PRIMARY]
    completion=t.get('completion_policy')
    successor={'schema':'GroupedTop1CompletionV1','numerator':4,'denominator':5,
               'dataset_cases':{'aegislab':100,'aiops2022':100,'aiops2025':100,'re2_ob':90,'re2_tt':90}}
    if (t['models']!=['qwen3.8-27b','gemma-4-26b-a4b'] or t['retirement_scope']!='per_model'
            or len(primary)!=300 or t['success_levels']!=[1,3,5]):
        raise ValueError('tournament population/threshold/model contract changed')
    if completion is None:
        if t['top1_successes_required']!=240 or set(t['threshold_datasets'])!=set(PRIMARY):
            raise ValueError('historical coverage contract changed')
    elif (completion!=successor or t['next_stage']!='complete'
            or t['top1_successes_required'] is not None or t['threshold_denominator_cases']!=480
            or set(t['threshold_datasets'])!=set(successor['dataset_cases'])):
        raise ValueError('per-dataset AC@1-only policy differs from the registered amendment')
    # Keep the original history's identity; its threshold is superseded by the
    # separately hashed stopping policy, never rewritten into old round records.
    # The coverage register tracks which model-case pairs have ever reached
    # AC@1.  Representation, evidence selection and their matched decoding
    # guide are method-level interventions and are already frozen in each
    # round's config hash/source archive.  A successor may therefore name the
    # original transport/template identity explicitly without rewriting the
    # immutable coverage history.
    coverage_prompt=t.get('coverage_prompt',t['prompt'])
    coverage_transport=t.get('coverage_transport',t['transport'])
    contract={'models':t['models'],'cases':sorted(r['opaque_incident_id'] for r in rows),
        'threshold_cases':sorted(primary),'threshold_count':240,'levels':[1,3,5],
        'roster_hash':split['eval_roster_sha256'],'prepared_pool_manifest_hash':sha_file(ROOT/t['prepared_pool_manifest']),
        'template_hashes':{k:sha_file(ROOT/v) for k,v in coverage_prompt.items() if k.endswith('_file')},
        'transport':coverage_transport,'profiles':t['model_request_profiles']}
    cohort_policy=t.get('cohort_policy')
    if cohort_policy not in (None,'all_unretired_v1'):raise ValueError('unknown tournament cohort policy')
    reg=SuccessCoverageRegister(ROOT/'RQs/RQ3/results/tournament_v1/coverage',contract,ROOT,
        require_full_cohort=(cohort_policy=='all_unretired_v1' or
            (ROOT/'RQs/RQ3/results/tournament_v1/reset_20260913/deletion_complete.json').is_file()))
    if completion:
        groups={d:sorted(r['opaque_incident_id'] for r in rows if r['dataset']==d) for d in successor['dataset_cases']}
        if {d:len(ids) for d,ids in groups.items()}!=successor['dataset_cases']:
            raise ValueError('tournament dataset population changed')
        if allow_policy_migration:reg.adopt_top1_completion(groups,4,5)
        policy=reg.completion_policy()
        if (not policy or policy['groups']!=groups or policy['numerator']!=4 or policy['denominator']!=5):
            raise ValueError('AC@1 completion policy must be migrated and verified before execution')
    elif allow_policy_migration:
        raise ValueError('policy migration requires the explicit AC@1 successor config')
    return reg


def reuse_tournament_call(reference, parts, envelope, output):
    """Exact-request alias: retain original record bytes, never sample a no-op again."""
    from vlmrca.run_state import audit_call_artifacts
    source=(ROOT/reference['record']).resolve();output=Path(output).resolve()
    owner=(ROOT/'RQs/RQ3/results/tournament_v1').resolve()
    if (not source.is_relative_to(owner) or not output.is_relative_to(owner)
            or source.parent.name!='trajectories' or source.parent.parent==output
            or sha_file(source)!=reference['sha256']):
        raise ValueError('invalid tournament reuse source')
    prior=source.parent.parent;record=read_json(source);audit_call_artifacts(record,prior)
    paths=[p for p in record['artifact_hashes'] if p.startswith('prompts/')]
    if len(paths)!=1:raise ValueError('ambiguous original request')
    original=read_json(prior/paths[0])
    if stable_hash({k:v for k,v in original.items() if k!='parts'})!=stable_hash(envelope):
        raise ValueError('reuse model/schema/prompt/recipe mismatch')
    def normalized(values, root=None):
        out=[]
        for part in values:
            row=dict(part)
            if 'png' in row:row['image_sha256']=stable_hash(row.pop('png'))
            if 'image_path' in row:
                if root is None:raise ValueError('unresolved current image')
                path=(root/row.pop('image_path')).resolve()
                if not path.is_relative_to(root) or sha_file(path)!=row['image_sha256']:
                    raise ValueError('reuse image mismatch')
            out.append(row)
        return out
    if normalized(parts)!=normalized(original['parts'],prior):
        raise ValueError('reuse model-visible evidence differs')
    # Copy only the small no-attention reply transaction; original paths and bytes
    # make conversation/image links work and retain the original call identity.
    if record.get('attention',{}).get('status')!='disabled_by_protocol':
        raise ValueError('reuse requires attention-off tournament source')
    inventory={**record['artifact_hashes'],str(source.relative_to(prior)):reference['sha256']}
    for relative,digest in inventory.items():
        target=(output/relative).resolve();origin=(prior/relative).resolve()
        if not target.is_relative_to(output) or not origin.is_relative_to(prior):
            raise ValueError('reuse artifact escaped its owner')
        if target.exists() and sha_file(target)!=digest:raise ValueError('reuse destination collision')
        if not target.exists():atomic_write(target,origin.read_bytes())
        if sha_file(target)!=digest:raise ValueError('reuse copy failed')
    audit_call_artifacts(record,output)
    return record


class RQ3SegmentationAdapter:
    """Explicit grouped adapter to the single unified segmentation authority."""
    def __init__(self, config):
        self.config = config
        self.base = DatasetSegmentationConfig.load(config["unified"]["segmentation"])

    def build(self, *, require_targets=True):
        cfg = self.config
        corpus = ROOT / cfg["processed_root"]
        roster_path = ROOT / cfg["eval_roster"]
        roster = read_json(roster_path)
        if roster["total"] != 480 or sum(map(len, roster["datasets"].values())) != 480:
            raise ValueError("the final eval roster must remain exactly 480")
        out = {"schema_version": "RQ3PrivateSplitV1", "eval_roster_sha256": sha_file(roster_path),
               "segmentation_sha256": self.base.effective_hash(), "seed": cfg["seed"],
               "train": [], "validation": [], "unused": [], "excluded": [], "eval": roster["datasets"]}
        for dataset in TRAIN_DATASETS:
            manifest = corpus / "private" / dataset / "manifest.jsonl"
            rows = [json.loads(line) for line in manifest.read_text().splitlines() if line.strip()]
            windows = [window_record(dataset, r, read_json(corpus / "private" / dataset / "cases" / f"{r['opaque_incident_id']}.json")) for r in rows]
            eval_ids = set(roster["datasets"][dataset])
            eval_windows = [w for w in windows if w["case_id"] in eval_ids]
            if len(eval_windows) != len(eval_ids):
                raise ValueError("eval cases absent from canonical corpus")
            # Build groups BEFORE removing eval neighbours: removing a bridge
            # window first would conceal transitive shared-event membership.
            eligible = []
            for group in components(windows):
                if any(w["case_id"] in eval_ids for w in group):
                    out["excluded"].extend({**w, "reason": "eval_connected_event_window"} for w in group)
                else:
                    eligible.append(group)
            target = cfg["data"]["targets"][dataset]
            allocated = allocate_groups(eligible, target["train"], target["validation"], cfg["seed"])
            for partition in allocated:
                out[partition].extend(allocated[partition])
        out["counts"] = {p: {d: sum(r["dataset"] == d for r in out[p]) for d in TRAIN_DATASETS}
                         for p in ("train", "validation", "unused", "excluded")}
        if cfg["data"]["shortage_policy"] != "fail_until_exact_balanced_counts":
            raise ValueError("obsolete RQ3 shortage policy")
        out["target_counts"] = cfg["data"]["targets"]
        out["targets_met"] = all(out["counts"][p][d] == cfg["data"]["targets"][d][p]
                                 for d in TRAIN_DATASETS for p in ("train", "validation"))
        if require_targets:
            require_split_targets(out, cfg)
        for a in out["train"]:
            for b in out["validation"]:
                if a["dataset"] == b["dataset"] and related(a, b):
                    raise ValueError("train/validation leakage")
        out["split_hash"] = stable_hash(out)
        return out


from vlmrca.run_state import DurableCallRegister, PhaseJournal


class CallLedger(DurableCallRegister):
    def recover_persisted(self, root):
        from .gates import audit_call_artifacts
        return super().recover_persisted(root, audit=audit_call_artifacts)


def cost_reward(rr, tokens, reference, rr_only=False):
    names = ("composer_input", "composer_output", "solver_input", "solver_output")
    if not 0 <= rr <= 1 or any(float(reference[k]) <= 0 for k in names):
        raise ValueError("invalid reward or cost reference")
    values = [float(tokens[k]) / float(reference[k]) for k in names]
    if any(not math.isfinite(x) or x < 0 for x in values):
        raise ValueError("invalid token accounting")
    cost = float(np.mean(values))
    return {"schema_version": "RCARewardV1", "rr": rr, "cost_index": cost,
            "reward": rr if rr_only else rr - .02 * min(cost, 2.)}


def rloo_advantages(rewards):
    values = np.asarray(rewards, dtype=float)
    if values.shape != (4,) or not np.isfinite(values).all():
        raise ValueError("RLOO requires four finite outcomes; exclude infrastructure-failed groups")
    return (values - (values.sum() - values) / 3).tolist()


def attribution(u00, u10, u01, u11):
    return {"content_at_fixed": u10-u00, "design_at_fixed": u01-u00,
            "interaction": u11-u10-u01+u00, "total": u11-u00,
            "content_at_learned": u11-u01, "design_at_learned": u11-u10}


from vlmrca.paired_stats import paired_statistics, holm


def registered_schedule(split, config):
    """An explicit budgeted task graph. Labels are absent from schedule keys."""
    require_split_targets(split, config)
    budget = config["budget"]
    if budget["planned"] + budget["reserve"] > budget["hard_limit"]:
        raise ValueError("planned schedule and reserve exceed the unchanged RQ3 hard call limit")
    train=split["train"];validation=split["validation"]
    evaluation=[{"dataset":d,"case_id":c} for d,ids in split["eval"].items() for c in ids]
    tasks=[]

    def add(stage,role,row,policy,extra=None):
        identity={"stage":stage,"role":role,"dataset":row["dataset"],"case_id":row["case_id"],
                  "policy":policy,**(extra or {})}
        tasks.append({**identity,"call_key":stable_hash(identity),"max_new_calls":1})

    for branch,seed in config["rl"]["branches"].items():
        for traversal in range(config["rl"]["traversals"]):
            for row in sorted(train,key=lambda r:stable_hash([seed,traversal,r["opaque_incident_id"]])):
                for sample in range(config["rl"]["group_size"]):
                    for role in ("composer","solver"):
                        add("rl",role,row,branch,{"traversal":traversal,"sample":sample})
        for checkpoint in config["rl"]["validation_fractions"]:
            for row in validation:
                for role in ("composer","solver"):add("validation",role,row,branch,{"fraction":checkpoint})
    for row in validation:
        for design in range(12):add("fixed_validation","solver",row,f"F{design+1:02d}")
        for policy in ("SFT","IMITATION"):
            for role in ("composer","solver"):add("validation",role,row,policy)
    learned=config["experiments"]["exp_frozen_solver_generalization"]["learned"]
    fixed=config["experiments"]["exp_frozen_solver_generalization"]["fixed"]
    for row in evaluation:
        for policy in fixed:add("eval","solver",row,policy)
        for policy in learned:
            for role in ("composer","solver"):add("eval",role,row,policy)
        # U00/U11 reuse D_FIXED/RL_COST_42; no extra Composer generation.
        for condition in ("U10","U01","TextTwin","ScreenshotTwin"):
            add("attribution","solver",row,condition)
    subset=[]
    for d in PRIMARY:
        subset.extend(sorted((r for r in evaluation if r["dataset"]==d),key=lambda r:stable_hash([42,r["dataset"],r["case_id"]]))[:40])
    for row in subset:
        for condition in config["experiments"]["exp_selection_design_attribution"]["local_interventions"]:
            add("local_intervention","solver",row,condition)
        # One extra Composer + Solver under reanonymized observation tests
        # selection equivariance, in addition to fixed-program ID remapping.
        for role in ("composer","solver"):add("local_intervention",role,row,"composer_reanonymize")
        add("local_intervention","solver",row,"identical_repeat_second")
    keys=[t["call_key"] for t in tasks]
    if (len(set(keys))!=len(keys) or len(keys)>budget["planned"]
            or len(keys)+budget["reserve"]>budget["hard_limit"]):
        raise ValueError("schedule duplication or planned call-budget overflow")
    return {"schema_version":"RQ3ScheduleV1","tasks":tasks,"new_calls_max":len(tasks),
            "eval_count":len(evaluation),"local_intervention_cases":subset,
            "hard_limit":config["budget"]["hard_limit"],"split_hash":split["split_hash"]}


def rloo_batches(split, config, branch):
    """Exact on-policy update boundaries including all checkpoint fractions.

    A validation boundary can shorten a batch, but never drops/repeats a case
    group or crosses the boundary before checkpoint selection is evaluated.
    """
    require_split_targets(split, config)
    if branch not in config["rl"]["branches"]:
        raise ValueError("unregistered RL branch")
    seed = config["rl"]["branches"][branch]
    order = []
    for traversal in range(config["rl"]["traversals"]):
        rows = sorted(split["train"],key=lambda r:stable_hash([seed,traversal,r["opaque_incident_id"]]))
        order.extend({**r,"traversal":traversal,"partition":"train"} for r in rows)
    total = len(order)
    boundaries = {}
    for fraction in config["rl"]["validation_fractions"]:
        point = total * fraction
        if not float(point).is_integer() or not 0 < point <= total:
            raise ValueError("checkpoint fraction is not an exact case-group boundary")
        boundaries[int(point)] = fraction
    if len(boundaries) != len(config["rl"]["validation_fractions"]) or total not in boundaries:
        raise ValueError("duplicate checkpoint boundary or final validation missing")
    cursor = 0; batches = []
    while cursor < total:
        boundary = min(i for i in boundaries if i > cursor)
        end = min(cursor+config["rl"]["case_groups_per_update"],boundary)
        if end <= cursor:
            raise ValueError("invalid RL batch capacity")
        rows = order[cursor:end]
        batches.append({"index":len(batches),"start":cursor,"end":end,"cases":rows,
                        "branch":branch,"seed":seed,"validation_fraction":boundaries.get(end),
                        "batch_hash":stable_hash([branch,cursor,end,rows,split["split_hash"]])})
        cursor = end
    return batches


def macro_by_dataset(rows, field):
    groups=defaultdict(list)
    for r in rows:groups[r["dataset"]].append(float(r[field]))
    if not groups:return None
    return float(np.mean([np.mean(v) for v in groups.values()]))


def select_validation_checkpoint(rows, objective):
    """Only frozen validation records, no eval or TrainTicket observations."""
    grouped=defaultdict(list)
    for r in rows:
        if r["partition"]!="validation" or r["dataset"] not in TRAIN_DATASETS:
            raise ValueError("checkpoint selection received forbidden data")
        grouped[r["checkpoint"]].append(r)
    if not grouped:raise ValueError("no validation checkpoints")
    counts={k:sorted((r["dataset"],r["case_id"]) for r in v) for k,v in grouped.items()}
    if len({canonical_json(x) for x in counts.values()})!=1:
        raise ValueError("checkpoint validation pairing is incomplete")
    scores={k:macro_by_dataset(v,objective) for k,v in grouped.items()}
    return sorted(scores,key=lambda k:(-scores[k],k))[0]


def select_fixed_validation(rows, split, design_ids):
    """Choose D_FIXED on the complete paired validation population only.

    Design/context failures retain zero quality and zero unspent tokens.
    Infrastructure holes are not silently removed from either denominator.
    """
    grouped=defaultdict(list)
    for row in rows:
        if row.get('infrastructure_error') or row.get('design') not in design_ids:
            raise ValueError('unregistered/infrastructure-incomplete fixed-design result')
        grouped[row['design']].append(row)
    if set(grouped)!=set(design_ids):raise ValueError('fixed-design validation is incomplete')
    for design,items in grouped.items():validate_validation_population(items,split,checkpoint=design)
    scores={design:{'mrr':macro_by_dataset(items,'reciprocal_rank'),
                    'tokens':macro_by_dataset(items,'total_tokens'),
                    'executable_rate':macro_by_dataset(items,'executable')}
            for design,items in grouped.items()}
    if not any(s['executable_rate']>0 for s in scores.values()):
        raise ValueError('no fixed design reached an executable validation input')
    selected=min((d for d in scores if scores[d]['executable_rate']>0),
                 key=lambda d:(-scores[d]['mrr'],scores[d]['tokens'],d))
    result={'schema_version':'RQ3FixedDesignSelectionV1','split_hash':split['split_hash'],
            'selected':selected,'scores':scores,'population_hash':stable_hash(rows),
            'selection_rule':'macro_mrr_then_total_tokens_then_id'}
    result['selection_hash']=stable_hash(result)
    return result


def imitation_examples(groups):
    """Same-feedback best-of-four imitation; never regenerate or call Solver."""
    examples=[]
    for g in groups:
        if g["partition"]!="train" or g["dataset"] not in TRAIN_DATASETS or g["branch"]!="RL_COST_42":
            raise ValueError("imitation source is not the registered training branch")
        valid=[r for r in g["rollouts"] if r.get("program_valid") and not r.get("infrastructure_error")]
        if valid:
            best=sorted(valid,key=lambda r:(-r["reward"],stable_hash(r["program"])))[0]
            examples.append({"dataset":g["dataset"],"case_id":g["case_id"],"partition":"train",
                             "program":best["program"],"messages":best["messages"],
                             "source_rollout":best["call_key"]})
    return examples


def validate_validation_population(rows, split, *, checkpoint=None):
    """The exact registered population, not merely equal partial sets."""
    expected={(r['dataset'],r['case_id']) for r in split['validation']}
    actual=[(r.get('dataset'),r.get('case_id')) for r in rows]
    if (not expected or len(actual)!=len(set(actual)) or set(actual)!=expected
            or any(r.get('partition')!='validation' for r in rows)
            or (checkpoint is not None and any(r.get('checkpoint')!=checkpoint for r in rows))):
        raise ValueError('validation population is incomplete, duplicated or not the registered partition')
    return True


def frozen_cost_reference(rows, split):
    """Freeze complete dataset-macro SFT costs; reject infrastructure gaps or unobserved denominators."""
    validate_validation_population(rows,split,checkpoint='SFT')
    if any(r.get('infrastructure_error') or r.get('policy')!='SFT' for r in rows):
        raise ValueError('cost reference requires completed SFT pipeline outcomes')
    fields=('composer_input','composer_output','solver_input','solver_output')
    for row in rows:
        if set(row['tokens'])!=set(fields) or any(not isinstance(v,(int,float)) or
                not math.isfinite(v) or v<0 for v in row['tokens'].values()):
            raise ValueError('invalid actual pipeline token accounting')
    means={key:macro_by_dataset([{'dataset':r['dataset'],'value':r['tokens'][key]} for r in rows],'value')
           for key in fields}
    if any(v is None or not v>0 for v in means.values()):
        raise ValueError('SFT validation did not establish positive cost denominators')
    result={'schema_version':'RQ3FrozenCostReferenceV1','split_hash':split['split_hash'],
            'source_policy':'SFT','case_count':len(rows),'means':means,
            'source_hash':stable_hash(sorted(rows,key=lambda r:(r['dataset'],r['case_id'])))}
    result['reference_hash']=stable_hash(result)
    return result


def read_format_examples(root):
    """Committed teacher-forcing examples only; no filename-derived membership."""
    root=Path(root).resolve();index=read_json(root/'index.json');rows=[]
    paths=[]
    for item in index['files']:
        path=(root/item['path']).resolve()
        if not path.is_relative_to(root) or not path.is_file() or sha_file(path)!=item['sha256'] or path in paths:
            raise ValueError('format-example source hash/path mismatch or duplication')
        paths.append(path);saved=read_json(path)
        if stable_hash(saved['examples'])!=saved['examples_hash']:
            raise ValueError('corrupt teacher-forcing examples')
        rows.extend(saved['examples'])
    if (len(rows)!=index['examples'] or len({(r['dataset'],r['case_id']) for r in rows})!=index['cases']
            or stable_hash(rows)!=index['examples_hash']):
        raise ValueError('teacher-forcing artifact inventory is incomplete')
    return index,rows


def verified_checkpoint(path, *, allow_inference_only=False, **expected):
    """Read a durable local adapter/optimizer checkpoint without loading tensors."""
    path=Path(path).resolve();state=read_json(path/'checkpoint.json')
    if state.get('complete') is not True or any(state.get(k)!=v for k,v in expected.items()):
        raise ValueError('checkpoint stage/contract/data identity mismatch')
    files=state.get('files',{})
    required={'policy/adapter_config.json','policy/adapter_model.safetensors'}
    if not (allow_inference_only and state.get('inference_only')):required.add('training_state.pt')
    if not required<=files.keys():raise ValueError('checkpoint is missing adapter/optimizer inventory')
    for relative,digest in files.items():
        item=(path/relative).resolve()
        if not item.is_relative_to(path) or not item.is_file() or sha_file(item)!=digest:
            raise ValueError('checkpoint artifact missing/corrupt or outside owner')
    return state


def sft_resume_checkpoint(root, examples, config, split_hash):
    """Verify newest committed checkpoint; never skip corruption or load a finished model unnecessarily."""
    import re
    from .exps import training_contract
    root=Path(root);candidates=[]
    for path in root.glob('step-*'):
        if not re.fullmatch(r'step-\d+',path.name):continue
        step=int(path.name.split('-')[1]);candidates.append((step,path))
    if not candidates:return None,False
    step,path=max(candidates)
    state=verified_checkpoint(path,stage=config.get('training_stage','SFT'),data_hash=stable_hash(examples),
                              training_contract=training_contract(config,split_hash),step=step)
    total=len(examples)*config['sft']['epochs'];cursor=state['cursor']
    if type(cursor) is not int or cursor<0 or cursor>total or step!=(cursor+29)//30:
        raise ValueError('SFT checkpoint cursor/update boundary mismatch')
    return path,cursor==total


def retain_rl_checkpoints(config, output):
    """After phase commit, retain periodic/latest states and one lightweight validation best."""
    from vlmrca.training import retain_periodic_checkpoints, snapshot_inference_checkpoint, prune_checkpoints
    output=Path(output)
    for branch in config['rl']['branches']:
        root=output/'models'/branch
        if not root.exists():continue
        checkpoints=sorted(root.glob('batch-[0-9][0-9][0-9]'))
        if not checkpoints:continue
        # Do not prune an optimizer's input until its successor phase is durable.
        for path in checkpoints:
            phase=output/'phases'/f'{branch}_{path.name.replace("-","_")}_update.json'
            if not phase.exists() or read_json(phase)['status']!='complete':break
        else:
            saved={p.stem:read_json(p) for p in (output/'private/validation').glob(f'{branch}_v*.json')}
            if saved:
                best=select_validation_checkpoint([r for s in saved.values() for r in s['rows']],'objective')
                source=ROOT/saved[best]['checkpoint'];target=root/'best-for-eval'/source.name
                if not target.exists():snapshot_inference_checkpoint(source,target)
                state=verified_checkpoint(target,allow_inference_only=True)
                if state.get('parent_checkpoint_sha256')!=saved[best]['checkpoint_sha256']:
                    raise ValueError('validation best weights differ from evaluated policy')
                prune_checkpoints(target.parent,{target},prefix='batch-')
            retain_periodic_checkpoints(root,config.get('checkpoint_interval_updates',20),prefix='batch-',
                                        index_offset=1,preserve_markers=True)


def assemble_rloo_groups(config, split, batch, schedule, composer_rows, solver_rows,
                         observations, reference, policy_version):
    """Bind verified requests to their exact case/policy/sample; keep illegal programs as negatives."""
    from .gates import validate_rollout_probability
    from .exps import composer_messages
    if (reference.get('reference_hash')!=stable_hash({k:v for k,v in reference.items() if k!='reference_hash'})
            or reference.get('split_hash')!=split['split_hash'] or reference.get('source_policy')!='SFT'):
        raise ValueError('RL cost reference is not the frozen SFT validation reference')
    batches=rloo_batches(split,config,batch['branch'])
    if batch not in batches:
        raise ValueError('RL batch differs from the registered traversal/checkpoint boundary')
    if schedule['split_hash']!=split['split_hash']:
        raise ValueError('RL schedule uses a different split')
    tasks={t['call_key']:t for t in schedule['tasks']}
    lookup={(t['role'],t['dataset'],t['case_id'],t.get('traversal'),t.get('sample')):t
            for t in tasks.values() if t['stage']=='rl' and t['policy']==batch['branch']}
    expected={lookup[role,row['dataset'],row['case_id'],row['traversal'],sample]['call_key']
              for row in batch['cases'] for sample in range(4) for role in ('composer','solver')}
    if set(composer_rows)|set(solver_rows)!=expected or set(composer_rows)&set(solver_rows):
        raise ValueError('RL batch has missing, repeated or extra request outcomes')
    groups=[]
    for row in batch['cases']:
        obs=observations[row['opaque_incident_id']]
        group={**row,'branch':batch['branch'],'rollouts':[]}
        for sample in range(4):
            ct=lookup['composer',row['dataset'],row['case_id'],row['traversal'],sample]
            st=lookup['solver',row['dataset'],row['case_id'],row['traversal'],sample]
            c=composer_rows[ct['call_key']];s=solver_rows[st['call_key']]
            for entry,task in ((c,ct),(s,st)):
                if (entry['task']!=task or entry.get('infrastructure_error') or
                        entry['status'] in {'started','interrupted','infrastructure_failure'}):
                    raise ValueError('RL cannot reward incomplete/mismatched infrastructure outcomes')
            record=c['record'];validate_rollout_probability(record,policy_version)
            if (record['call_key']!=ct['call_key'] or c['observation_hash']!=stable_hash(obs)
                    or c['case']!=row['opaque_incident_id']):
                raise ValueError('RL Composer reply is not bound to its original observation')
            if s.get('composer_record_hash')!=record['record_hash']:
                raise ValueError('RL Solver outcome belongs to another Composer sample')
            context_failure=c['status']=='valid' and s['status']=='design_infeasible' and s.get('failure_stage')=='context'
            valid=c['status']=='valid' and not context_failure
            if valid and s['status'] not in {'complete','model_failure'}:
                raise ValueError('a render-qualified program requires its actual Solver outcome')
            if valid and (s['record'].get('call_key')!=st['call_key'] or s['record'].get('role')!='solver'):
                raise ValueError('RL Solver response identity mismatch')
            if not valid and not context_failure and (c['status']!='program_failure' or s['status']!='not_called_invalid_program' or s.get('record') is not None):
                raise ValueError('invalid program must remain an uncalled Solver failure')
            if context_failure and s.get('record') is not None:raise ValueError('context rejection cannot have a Solver response')
            tokens={'composer_input':record['input_tokens'],'composer_output':record['output_tokens'],
                    'solver_input':s['record']['input_tokens'] if valid else 0,
                    'solver_output':s['record']['output_tokens'] if valid else 0}
            rr=float(s['metrics']['mrr']) if valid else 0.
            if not 0<=rr<=1:raise ValueError('invalid reciprocal rank')
            reward=cost_reward(rr,tokens,reference['means'],rr_only=batch['branch']=='RL_RR_42')
            if not valid:reward['reward']=config['rl']['invalid_program_reward']
            group['rollouts'].append({**record,'program_valid':valid,'program':c.get('program'),
                'messages':composer_messages(obs),'reward':reward['reward'],'reward_components':reward,'reciprocal_rank':rr,
                'tokens':tokens,'sample':sample,'infrastructure_error':False,
                'solver_call_key':st['call_key'],'solver_record_hash':s['record']['record_hash'] if valid else None})
        groups.append(group)
    return groups


def formal_phase_plan(split, config):
    """Complete single-GPU lifecycle; every registered generation appears once.

    This is an execution dependency graph, not qualification or permission to
    run it. Model-free phases include durable outputs/checkpoint selection.
    """
    schedule=registered_schedule(split,config); tasks=schedule['tasks']; phases=[]
    buckets=defaultdict(list)
    for task in tasks:buckets[(task['stage'],task['role'],task['policy'])].append(task)

    def choose(stage,role,policy,**filters):
        return [t['call_key'] for t in buckets[stage,role,policy]
                if all(t.get(k)==v for k,v in filters.items())]

    def add(name,kind,keys=(),**details):
        phases.append({'id':name,'kind':kind,'requires':[phases[-1]['id']] if phases else [],
                       'call_keys':list(keys),'details':details})

    def validation(policy,fraction=None):
        extra={} if fraction is None else {'fraction':fraction}
        stem=policy+('_'+str(fraction) if fraction is not None else '')
        for role in ('composer','solver'):
            add('validation_'+stem+'_'+role,role,choose('validation',role,policy,**extra),
                policy=policy,partition='validation',fraction=fraction)

    add('prepare_train_validation','prepare',partitions=['train','validation'])
    add('format_examples','format_examples')
    add('train_SFT','sft_update',policy='SFT')
    validation('SFT')
    add('freeze_cost_reference','freeze_cost_reference')
    keys=[key for design in range(1,13) for key in choose('fixed_validation','solver',f'F{design:02d}')]
    add('fixed_validation','solver',keys,partition='validation',policy='fixed_designs')
    add('freeze_fixed_design','freeze_fixed_design')
    for branch in config['rl']['branches']:
        for batch in rloo_batches(split,config,branch):
            prefix=f'{branch}_batch_{batch["index"]:03d}'
            for role in ('composer','solver'):
                keys=[key for row in batch['cases'] for sample in range(4)
                      for key in choose('rl',role,branch,dataset=row['dataset'],case_id=row['case_id'],
                                        traversal=row['traversal'],sample=sample)]
                add(prefix+'_'+role,role,keys,branch=branch,batch_index=batch['index'],
                    batch_hash=batch['batch_hash'],partition='train')
            add(prefix+'_update','rloo_update',branch=branch,batch_index=batch['index'],batch_hash=batch['batch_hash'])
            if batch['validation_fraction'] is not None:validation(branch,batch['validation_fraction'])
    add('train_IMITATION','imitation_update',source_branch='RL_COST_42')
    validation('IMITATION')
    add('freeze_validation_selected_policies','freeze_policies')
    add('prepare_eval','prepare',partitions=['eval'])
    fixed=config['experiments']['exp_frozen_solver_generalization']['fixed']
    add('eval_fixed','solver',[key for policy in fixed for key in choose('eval','solver',policy)],partition='eval',policy='fixed')
    for policy in config['experiments']['exp_frozen_solver_generalization']['learned']:
        for role in ('composer','solver'):
            add('eval_'+policy+'_'+role,role,choose('eval',role,policy),partition='eval',policy=policy)
    add('attribution_twins','solver',[t['call_key'] for t in tasks if t['stage']=='attribution'],partition='eval')
    add('local_reanonymize_composer','composer',[t['call_key'] for t in tasks
        if t['stage']=='local_intervention' and t['role']=='composer'],partition='eval',policy='RL_COST_42')
    add('local_interventions_solver','solver',[t['call_key'] for t in tasks
        if t['stage']=='local_intervention' and t['role']=='solver'],partition='eval')
    add('verify_analyze_report','analysis')
    actual=[key for p in phases for key in p['call_keys']]
    if len(actual)!=len(set(actual)) or set(actual)!={t['call_key'] for t in tasks}:
        raise ValueError('formal phases omit or duplicate registered calls')
    result={'schema_version':'RQ3FormalPhasePlanV1','split_hash':split['split_hash'],
            'schedule_hash':stable_hash(schedule),'phases':phases,'new_calls_max':len(actual)}
    result['plan_hash']=stable_hash(result)
    return result


def verify_work_spec(spec, split, schedule, plan, output):
    """Bind a model phase to its exact registered tasks and immutable inputs."""
    output=Path(output).resolve();owner=(ROOT/'RQs/RQ3/results').resolve()
    if not output.is_relative_to(owner):raise ValueError('formal output outside RQ3')
    if (spec.get('spec_hash')!=stable_hash({k:v for k,v in spec.items() if k!='spec_hash'})
            or spec.get('split_hash')!=split['split_hash'] or spec.get('plan_hash')!=plan['plan_hash']):
        raise ValueError('formal work specification identity changed')
    phase=next((p for p in plan['phases'] if p['id']==spec['phase_id']),None)
    if phase is None or phase['kind'] not in ('composer','solver') or phase['kind']!=spec['role']:
        raise ValueError('not a registered model phase')
    entries=spec['entries'];keys=[r['task']['call_key'] for r in entries]
    if len(keys)!=len(set(keys)) or set(keys)!=set(phase['call_keys']):
        raise ValueError('model phase omits/duplicates registered tasks')
    tasks={t['call_key']:t for t in schedule['tasks']}
    partition=spec['partition']
    if partition!=phase['details']['partition'] or partition not in {'train','validation','eval'}:
        raise ValueError('model phase partition mismatch')
    allowed=({(r['dataset'],r['case_id']):r['opaque_incident_id'] for r in split[partition]}
             if partition!='eval' else {(d,c):None for d,ids in split['eval'].items() for c in ids})
    inventory=spec['artifact_hashes']
    for relative,digest in inventory.items():
        path=(ROOT/relative).resolve()
        if not path.is_relative_to(owner) or not path.is_file() or sha_file(path)!=digest:
            raise ValueError('phase input inventory missing/corrupt/outside RQ3')
    for entry in entries:
        task=entry['task'];identity=(task['dataset'],task['case_id'])
        if task!=tasks[task['call_key']] or identity not in allowed:
            raise ValueError('phase task/case differs from registered partition')
        if allowed[identity] is not None and entry['case']!=allowed[identity]:
            raise ValueError('phase opaque case differs from registered identity')
        for name in ('prepared_public','prepared_private'):
            if entry[name] not in inventory:raise ValueError('uncommitted phase preparation')
        payload=read_json(ROOT/entry['prepared_public']);private=read_json(ROOT/entry['prepared_private'])
        if (payload['split_hash']!=split['split_hash'] or payload['pool']['opaque_incident_id']!=entry['case']
                or (private['dataset'],private['case_id'],private['opaque_incident_id'])!=(*identity,entry['case'])):
            raise ValueError('phase public/private case binding mismatch')
        if type(entry.get('sampling_seed')) is not int:raise ValueError('missing registered sampling seed')
        if spec['role']=='solver' and not entry.get('uncalled_status'):
            if entry['parts_path'] not in inventory:raise ValueError('uncommitted Solver parts')
            bundle=read_json(ROOT/entry['parts_path'])
            if bundle['candidates']!=payload['pool']['candidates']:
                raise ValueError('Solver candidate universe differs from prepared case')
            images=[p for p in bundle['parts'] if 'image_path' in p]
            if len(images)>1:raise ValueError('Solver received multiple dashboards')
            for image in images:
                if inventory.get(image['image_path'])!=image['image_sha256']:
                    raise ValueError('uncommitted Solver image')
        elif spec['role']=='solver' and entry['uncalled_status'] not in {
                'not_called_invalid_program','intervention_infeasible','design_infeasible'}:
            raise ValueError('unknown no-call outcome')
    if not set(spec.get('reconciled_retry_keys',[]))<=set(keys):raise ValueError('retry outside model phase')
    return entries


def owned_gpu_process(function):
    """Children inherit the lease, so a dead supervisor cannot double-launch."""
    import functools
    import fcntl
    @functools.wraps(function)
    def execute(*args,**kwargs):
        path=ROOT/'RQs/RQ3/results/gpu_owner.lock';path.parent.mkdir(parents=True,exist_ok=True)
        with path.open('a+') as lease:
            fcntl.flock(lease,fcntl.LOCK_EX|fcntl.LOCK_NB)
            return function(*args,**kwargs,_gpu_lease_fd=lease.fileno())
    return execute


def reconcile_phase_calls(config, spec, output):
    """Power-loss retries only. Other infrastructure errors require diagnosis."""
    output=Path(output).resolve()
    ledger=CallLedger(ROOT/'RQs/RQ3/results/calls.sqlite',config['budget']['hard_limit'],scope=output.name)
    report=ledger.recover_persisted(output);prefix=output.name+'/'
    keys={r['task']['call_key'] for r in spec['entries']};latest={}
    with ledger.connect() as db:
        for call_id,key,state in db.execute('SELECT id,call_key,state FROM calls WHERE substr(call_key,1,?)=? ORDER BY id',
                                           (len(prefix),prefix)):
            if key[len(prefix):] in keys:latest[key[len(prefix):]]=(call_id,state)
    failures={k:v for k,v in latest.items() if v[1] not in {'complete','interrupted'}}
    if failures:raise RuntimeError('phase has non-interruption infrastructure errors; inspect before retry')
    retry=sorted(k for k,(_,state) in latest.items() if state=='interrupted')
    report['retry_keys']=retry;report['preserved_attempts']={k:latest[k][0] for k in retry}
    if not retry:return spec,report
    result={k:v for k,v in spec.items() if k not in {'spec_hash','reconciled_retry_keys'}}
    result['reconciled_retry_keys']=retry;result['spec_hash']=stable_hash(result)
    return result,report


def analyze_formal(config,output,plan):
    """Verify full population and infrastructure; describe outcomes/attention, not recovered reasoning."""
    import pandas as pd
    from functools import lru_cache
    from .main import verified_phase_outcomes
    from RQs.RQ2_1.src.utils import is_granularity_aware_hit
    from .exps import select_packet,ComposerProgramV1,fixed_selection
    from .main import hydrate
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    split=RQ3SegmentationAdapter(config).build();schedule=registered_schedule(split,config)
    rows_by_key={}
    for phase in plan['phases']:
        if phase['kind'] in {'composer','solver'}:
            for row in verified_phase_outcomes(config,phase,output):rows_by_key[row['task']['call_key']]=row
    if set(rows_by_key)!={t['call_key'] for t in schedule['tasks']}:raise ValueError('final analysis lacks registered outcomes')
    @lru_cache(maxsize=8)
    def evidence(case):
        root=output/'prepared/eval';payload=read_json(root/'public'/f'{case}.json')
        return payload,read_json(root/'private'/f'{case}.json')
    rows=[];attention=[]
    for outcome in rows_by_key.values():
        task=outcome['task']
        if task['role']!='solver':continue
        if outcome['status'] not in {'complete','model_failure','not_called_invalid_program','intervention_infeasible','design_infeasible'}:
            raise ValueError('final analysis has an unresolved infrastructure outcome')
        identity={k:v for k,v in task.items() if k not in {'call_key','max_new_calls'}};identity['role']='composer'
        composer=rows_by_key.get(stable_hash(identity));record=read_json(output/outcome['record_path']) if outcome.get('record_path') else {}
        row={**task,'case':outcome['case'],'status':outcome['status'],**outcome['metrics'],
            'composer_input':composer['input_tokens'] if composer else 0,'composer_output':composer['output_tokens'] if composer else 0,
            'solver_input':outcome['input_tokens'],'solver_output':outcome['output_tokens'],
            'image_tokens':record.get('image_tokens',0),'text_tokens':record.get('text_tokens',0),
            'executable':int(outcome['status'] in {'complete','model_failure'}),
            'parse_success':int(outcome['status']=='complete')}
        row['pipeline_tokens']=sum(row[k] for k in ('composer_input','composer_output','solver_input','solver_output'))
        row['program_valid']=int(composer['status']=='valid') if composer else None
        if task['stage']=='eval':
            payload,private=evidence(row['case']);pool=payload['pool'];selected=None
            root_ids={e for e,n in private['numeric_to_natural'].items() if any(is_granularity_aware_hit(n,a) for a in private['accepted'])}
            if composer and composer['status']=='valid':selected=read_json(output/composer['render']['packet'])
            elif task['policy']=='D_FIXED':
                pool,cards=hydrate(payload)
                program=ComposerProgramV1(fixed_selection(cards),read_json(output/'private/frozen_fixed_design.json')['design'])
                selected=select_packet(pool,cards,program)[0]
            elif task['policy'] in {'T_FIXED','C_FIXED','TPV_FIXED'}:
                selected=read_json(output/'fixed_baselines/public'/f"{row['case']}.json")['packet']
            def entities(facts):return {e for f in facts for e in f.get('entity_ids',[])}
            shown=entities(selected['facts']) if selected else set();available=entities(pool['facts'])
            advertised={e for c in payload['observation']['cards'] for e in c['entities']}
            reason=(outcome.get('parsed') or {}).get('reason','');mentions=set(re.findall(r'(?<!\d)\d{3,5}(?!\d)',reason))
            row.update(fault_type=private['fault_type'],root_granularity=','.join(sorted({private['granularity'][private['numeric_to_natural'][e]] for e in root_ids})),
                candidate_count=len(pool['candidates']),pool_root_available=int(bool(root_ids&available)),
                catalogue_root_available=int(bool(root_ids&advertised)),selected_root_available=int(bool(root_ids&shown)),
                root_entity_cited=int(bool(mentions&root_ids)),entity_mention_precision=len(mentions&shown)/len(mentions) if mentions else None,
                selected_fact_count=len(selected['facts']) if selected else 0,selected_entity_count=len(shown))
        rows.append(row)
        for query,diagnostic in record.get('attention',{}).items():
            if not isinstance(diagnostic,dict):continue
            for image in diagnostic.get('image_regions',[]):
                for region,mass in image.get('global_region_mass',{}).items():
                    attention.append({'case':row['case'],'dataset':task['dataset'],'stage':task['stage'],'policy':task['policy'],
                        'query':query,'transport':'image','region':region,'mass':mass,
                        'density':image['region_attention_per_pixel'].get(region),'lift':image['region_density_lift'].get(region)})
            for region,data in diagnostic.get('text_regions',{}).items():
                attention.append({'case':row['case'],'dataset':task['dataset'],'stage':task['stage'],'policy':task['policy'],
                    'query':query,'transport':'text','region':region,'mass':data['attention_mass'],
                    'density':data['attention_per_token'],'lift':data['normalized_focus']})
    frame=pd.DataFrame(rows);directory=output/'analysis';directory.mkdir(parents=True,exist_ok=True);artifacts=[]
    def csv(name,table):
        path=directory/f'{name}.csv';atomic_write(path,table.to_csv(index=False).encode());artifacts.append(path)
    csv('all_solver_outcomes',frame);attn=pd.DataFrame(attention);csv('attention',attn)
    evaluation=frame[frame.stage=='eval'].copy()
    if len(evaluation)!=480*10 or evaluation.duplicated(['case','policy']).any():raise ValueError('eval arms/population incomplete')
    measures=['mrr','ac@1','ac@3','ac@5','avg@3','avg@5','composer_input','composer_output','solver_input',
              'solver_output','text_tokens','image_tokens','pipeline_tokens','executable','parse_success','program_valid',
              'pool_root_available','catalogue_root_available','selected_root_available','root_entity_cited','entity_mention_precision']
    measures=[m for m in measures if m in evaluation]
    summary=evaluation.groupby(['dataset','policy'])[measures].mean().reset_index();csv('performance_cost_runtime',summary)
    csv('failure_strata',evaluation.groupby(['dataset','policy','fault_type','root_granularity','status'],dropna=False).agg(n=('case','size'),mrr=('mrr','mean')).reset_index())
    csv('learning_validation',frame[frame.stage=='validation'].groupby(['policy','fraction','dataset'],dropna=False)[measures[:1]+['pipeline_tokens','program_valid']].mean().reset_index())
    pivot=evaluation.pivot(index=['dataset','case'],columns='policy',values='mrr')
    pivot['RL_COST']=(pivot.RL_COST_42+pivot.RL_COST_43)/2;comparisons=[]
    families=[('primary',PRIMARY,'RL_COST',['TPV_FIXED','D_FIXED','SFT']),
              ('transfer',('aegislab',),'RL_COST',['TPV_FIXED','D_FIXED']),
              ('secondary',PRIMARY,'RL_COST_42',['RL_RR_42','IMITATION'])]
    for family,datasets,treatment,controls in families:
        subset=pivot[pivot.index.get_level_values('dataset').isin(datasets)];batch=[]
        for control in controls:
            batch.append({'family':family,'treatment':treatment,'control':control,**paired_statistics(subset[control],subset[treatment])})
        for row,p in zip(batch,holm([r['p'] for r in batch]),strict=True):row['adjusted_p']=p;row['material_gain']=row['delta']>=.05 and p<.05
        comparisons.extend(batch)
    csv('paired_hypotheses',pd.DataFrame(comparisons))
    interventions=frame[frame.stage.isin(['attribution','local_intervention'])].pivot(index=['dataset','case'],columns='policy',values='mrr')
    joined=pivot.join(interventions);effects=[]
    for (dataset,case),r in joined.iterrows():
        effects.append({'dataset':dataset,'case':case,**attribution(r.D_FIXED,r.U10,r.U01,r.RL_COST_42)})
    effects=pd.DataFrame(effects);csv('conditional_attribution',effects)
    csv('intervention_scores',joined.reset_index())
    status={'status':'complete_population_analyzed','new_model_calls':0,'solver_outcomes':len(frame),'eval_cases':480,
            'actual_attempts':CallLedger(ROOT/'RQs/RQ3/results/calls.sqlite',config['budget']['hard_limit']).summary(),
            'attention_correlational_only':True,'grounding_scope':'explicit numeric entity mentions; not numeric-claim or causal verification',
            'manual_final_audit_required':True}
    write_json(directory/'summary.json',status);artifacts.append(directory/'summary.json')
    def figure(name,table,ylabel):
        fig,ax=plt.subplots(figsize=(max(9,len(table)*.65),5));table.plot.bar(ax=ax)
        ax.set_ylabel(ylabel);ax.tick_params(axis='x',labelrotation=40);fig.tight_layout()
        path=directory/f'{name}.png';fig.savefig(path,dpi=160);plt.close(fig);artifacts.append(path)
    headline=evaluation[evaluation.dataset.isin(PRIMARY)].groupby('policy')[['mrr','pipeline_tokens']].mean()
    figure('headline_mrr',headline[['mrr']],'Mean reciprocal rank; three primary datasets')
    figure('pipeline_token_cost',headline[['pipeline_tokens']],'Composer + Solver input/output tokens')
    figure('conditional_effects',effects.groupby('dataset')[['content_at_fixed','design_at_fixed','interaction']].mean(),'Conditional MRR change')
    if len(attn):
        density=attn[(attn.stage=='eval')&(attn.transport=='image')&(attn.query=='answer')].groupby(['policy','region']).lift.mean().unstack()
        if len(density):figure('answer_attention_density',density,'Area-normalized attention density lift')
    caveat='Model and program failures remain in end-to-end denominators. Entity mentions are not proof of correct reasoning. Attention is correlational. Two RL seeds are averaged per case for primary tests, not independent cases. No confidence intervals. TrainTicket is training-held-out, not claimed absent from pretraining. A final manual audit is still required.'
    sections={'exp_composer_learning':('Learning and feedback controls','learning_validation.csv','pipeline_token_cost.png'),
              'exp_frozen_solver_generalization':('Fixed-Solver generalization','performance_cost_runtime.csv','headline_mrr.png'),
              'exp_selection_design_attribution':('Conditional selection/design attribution','conditional_attribution.csv','conditional_effects.png')}
    for experiment,(title,table,picture) in sections.items():
        path=directory/f'{experiment}_findings.md'
        atomic_write(path,(f'# RQ3 — {title}\n\nStatus: complete registered population; pending final manual review.\n\n'
            f'{caveat}\n\n![{title}]({picture})\n\n[Detailed case-level data]({table}); [paired tests](paired_hypotheses.csv); '
            '[attention data](attention.csv); [failure strata](failure_strata.csv).\n\n'
            'Fixed controls and learned policies use newly collected compatible inputs. Report AegisLab separately from RE2-TT; do not merge them into two independent unseen applications.\n').encode());artifacts.append(path)
    return artifacts
