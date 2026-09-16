"""Shared evaluator accepts correct IDs, never repairs malformed output."""
import pytest
from unified_scripts.rca_scorer import RCAScorer,RCAScorerConfig,score_bound_response


def test_response_binding_and_model_failure():
    scorer=RCAScorer(RCAScorerConfig.load(),hit=lambda a,b:a==b)
    schema={'type':'object','properties':{'services':{'type':'array','items':{'type':'string'}}},'required':['services']}
    def score(text,mapping=None):
        return score_bound_response(text,['100','200'],mapping or {'100':'a','200':'b'},['b'],schema,scorer)
    assert score('{"services":["100","200"]}')['metrics']['mrr']==.5
    for text in ('bad','{}','{"services":[200]}','{"services":["999"]}','{"services":["200","200"]}'):
        result=score(text)
        assert result['status']=='model_failure' and result['metrics']['mrr']==0
    with pytest.raises(ValueError,match='binding incomplete'):score('{"services":["200"]}',{'100':'a'})
