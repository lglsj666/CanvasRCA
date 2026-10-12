"""Public, IO-free cardinality/representation compiler. No private evaluator input."""
from copy import deepcopy
import json
import re
from .utils import ARMS, MODEL, VERSION, stable_hash
from RQs.RQ3_15.src import exps as parent

VISUAL={'MARGINAL_FLEX','MARGINAL_FIVE','MARKLESS_FIVE','MARGINAL_REPEAT'}
FIVE={'BASE_FIVE','PAIR_FIVE','MARGINAL_FIVE','MARKLESS_FIVE','MARGINAL_REPEAT'}
REPEATS={'MARGINAL_REPEAT'}
FIVE_GUIDE=('Output cardinality for this request: return exactly five distinct IDs from the supplied candidate list, '
            'ranked by plausibility. Additional ranks are alternatives, not claims of five simultaneous causes. '
            'Keep the same services, reason, and confidence JSON fields.')


def request_envelope(arm,system):
    from RQs.RQ3_1.src.main import _request_envelope
    if arm not in ARMS: raise ValueError('Unknown arm')
    envelope=_request_envelope(MODEL,system=system)
    envelope['policy_version']=VERSION
    envelope['schema']=schema_for(arm,envelope['schema'])
    return envelope


def schema_for(arm,base):
    if arm not in ARMS: raise ValueError('Unknown arm')
    schema=deepcopy(base)
    items=schema['json_schema']['schema']['properties']['services']
    if items['minItems']!=1 or items['maxItems']!=5: raise ValueError('Original output schema drift')
    if arm in FIVE: items['minItems']=5
    return schema


def compile_public(inherited,c):
    parent.visible_audit(inherited)
    if len(inherited['candidates'])<5: raise ValueError('Not enough public candidates for registered five ranks')
    texts={}
    for arm in ARMS:
        old='BASE_TEXT' if arm.startswith('BASE_') else 'PAIR_TEXT'
        text=deepcopy(inherited['texts'][old])
        if arm in FIVE: text.insert(-1,{'type':'text','text':FIVE_GUIDE})
        texts[arm]=text
    applicable=bool(inherited['payload']['relations'])
    canonical={a:(a if applicable or a in REPEATS else ('BASE_FIVE' if a in FIVE else 'BASE_FLEX')) for a in ARMS}
    public={'system':inherited['system'],'candidates':deepcopy(inherited['candidates']),
            'texts':texts,'images':{},'payload':deepcopy(inherited['payload']),
            'facts_hash':inherited['facts_hash'],'base_facts_hash':inherited['base_facts_hash'],
            'canonical_arms':canonical,'infeasible':{},'output_adapter':c['output_adapter']['version']}
    visible_audit(public)
    return public


def design_for(payload,c,arm):
    if arm not in VISUAL: raise ValueError('Not a visual arm')
    from renderer.operations import apply_operations
    from renderer.utils import compile_design
    evidence,base,operations,design,audit=parent.design_for(payload,c,'MARGINAL_VISUAL')
    if arm=='MARKLESS_FIVE':
        # Existing design presentation control, not a new operation or local drawing.
        # Every intermediate operation is validated. Start at the registered
        # marginal component before attaching its supported presentation switch.
        def marginal(node):
            if node['type']=='panel': node['component']='trace_joint.marginals'
            else:
                for child in node.get('children',[]): marginal(child)
        marginal(base['tree'])
        base['presentation']={card['id']:{'marks':False,'details':True} for card in evidence['cards']}
        design,audit=apply_operations(evidence,base,operations)
        compile_design(evidence,design)
    return evidence,base,operations,design,audit


def parts_for(public,arm,png=None):
    if arm not in ARMS: raise ValueError('Unknown arm')
    parts=deepcopy(public['texts'][arm])
    if arm in VISUAL and public['payload']['relations']:
        if png is None or not png.startswith(b'\x89PNG\r\n\x1a\n'): raise ValueError('Actual committed PNG required')
        return [{'type':'image','png':png}]+parts
    if png is not None: raise ValueError('Text/fallback must not receive an image')
    return parts


def visible_audit(public):
    visible=json.dumps({k:public[k] for k in ('system','texts','payload')},ensure_ascii=False)
    if re.search(r'(?i)(INC-[A-F0-9]{8}|aiops202[25]|aegislab|ground_truth|injection_time|/home/|/scratch/|trace_id|span_id)',visible):
        raise ValueError('Source/private identity in visible input')
    t=public['texts']
    assert t['PAIR_FLEX']==t['MARGINAL_FLEX']
    assert all(t[a]==t['PAIR_FIVE'] for a in ('MARGINAL_FIVE','MARKLESS_FIVE','MARGINAL_REPEAT'))
    for five,flex in [('BASE_FIVE','BASE_FLEX'),('PAIR_FIVE','PAIR_FLEX'),('MARGINAL_FIVE','MARGINAL_FLEX')]:
        assert t[five][-2]=={'type':'text','text':FIVE_GUIDE}
        assert t[five][:-2]+t[five][-1:]==t[flex]
    assert public['canonical_arms']['MARGINAL_REPEAT']=='MARGINAL_REPEAT'
    if not public['payload']['relations']:
        assert t['BASE_FLEX']==t['PAIR_FLEX'] and t['BASE_FIVE']==t['PAIR_FIVE']
    return {'status':'passed','same_fact_visual_controls':True,'only_registered_cardinality_instruction_added':True}
