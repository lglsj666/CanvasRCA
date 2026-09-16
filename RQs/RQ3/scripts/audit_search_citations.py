"""Offline visible-reference validation, not a causal-truth or RCA scorer."""
import re


def citation_references(reason, packet, manifest):
    facts = {f['fact_id']:f for f in packet['facts']}
    cards = {c['card']['card_id']:c['card'] for c in manifest['cards']}
    rows=[]
    for match in re.finditer(r'\[(EC\d+)(?:/([^\[\]]+))?\]',reason):
        card_id, detail=match.groups();card=cards.get(card_id)
        bound = [facts[f] for f in card['fact_ids']] if card else []
        if detail:
            bound=[f for f in bound if
                (f['field']=='metric_series_64' and f['payload'].get('panel_id')==detail) or
                (f['field']=='denum_log_template' and f['payload'].get('template_id')==detail)]
        status='unknown_card' if card is None else 'unknown_row' if not bound else 'valid_address'
        rows.append({'citation':match.group(),'start':match.start(),'end':match.end(),
            'card_id':card_id,'detail':detail,'status':status,
            'bound_fact_ids':[f['fact_id'] for f in bound],
            'bound_owner_ids':sorted({e for f in bound for e in f['entity_ids']}),
            'semantic_claim_status':'requires_manual_review'})
    return rows


def self_test():
    p={'facts':[{'fact_id':'m','field':'metric_series_64','entity_ids':['123'],
                'payload':{'panel_id':'M09'}},
               {'fact_id':'l','field':'denum_log_template','entity_ids':['456'],
                'payload':{'template_id':'LT02'}}]}
    m={'cards':[{'card':{'card_id':'EC01','fact_ids':['m']}},
                {'card':{'card_id':'EC02','fact_ids':['l']}}]}
    refs=citation_references('[EC01/M09] [EC02/LT02] [EC01/LT02] [EC03] [EC01] [EC01/M9]',p,m)
    assert [r['status'] for r in refs]==['valid_address','valid_address','unknown_row','unknown_card','valid_address','unknown_row']
    assert refs[0]['bound_owner_ids']==['123']
    assert citation_references('No source claim',p,m)==[]
    assert all(r['semantic_claim_status']=='requires_manual_review' for r in refs)


if __name__=='__main__':
    self_test();print('citation address CPU tests passed; no semantic correctness inferred')
