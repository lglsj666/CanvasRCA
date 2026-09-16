"""Generic local streaming/partial-output and tokenizer contract regression tests."""
import json
from types import SimpleNamespace as NS

import pytest
from vlmrca.vlm import client
from vlmrca.vlm.configs import VLMConfig


def chunk(content=None, reasoning=None, *, alias='reasoning', finish=None, usage=None):
    delta=NS(content=content, **{alias:reasoning})
    return NS(id='test-stream', choices=[NS(delta=delta, finish_reason=finish)], usage=usage)


@pytest.mark.parametrize('alias', ['reasoning','reasoning_content'])
@pytest.mark.parametrize('outcome', ['complete','length','network_failure'])
def test_reasoning_and_answer_survive_partial_stream(tmp_path, monkeypatch, alias, outcome):
    monkeypatch.setattr(client,'attention_probe_enabled',lambda:False)
    usage=NS(model_dump=lambda:{'prompt_tokens':11,'completion_tokens':7})
    def stream(**kwargs):
        assert kwargs['stream_options']['include_usage']
        yield chunk(reasoning='inspect ',alias=alias)
        yield chunk(reasoning='evidence',alias=alias)
        if outcome=='network_failure':raise TimeoutError('simulated transport timeout')
        if outcome=='complete':yield chunk(content='{"services":[]}')
        yield chunk(finish='stop' if outcome=='complete' else 'length',usage=usage)
    api=NS(chat=NS(completions=NS(create=stream)))
    args=(api,{},VLMConfig(tag='fixture',backend='openai',model_id='fixture'),[],'fixture',tmp_path,None)
    if outcome=='network_failure':
        with pytest.raises(TimeoutError):client._call_openai_streaming(*args)
    else:
        result=client._call_openai_streaming(*args)
        assert result.raw['reasoning_text']=='inspect evidence' and result.output_tokens==7
        assert result.text==('{"services":[]}' if outcome=='complete' else '')
        assert result.performance['output_timing_scope']=='reasoning_and_answer'
        assert result.performance['ttft_s']==result.performance['first_reasoning_s']
        if outcome=='complete':assert result.performance['first_answer_s']>=result.performance['ttft_s']
        else:assert result.performance['first_answer_s'] is None
    partial=json.loads((tmp_path/'fixture.json').read_text())
    assert partial['reasoning_text']=='inspect evidence' and partial['reasoning_chars']==16
    assert partial['status']==('client_error' if outcome=='network_failure' else 'completed')
    assert partial['response_text']==('{"services":[]}' if outcome=='complete' else '')


def test_reasoning_aliases_not_duplicated_or_silently_discarded():
    assert client._reasoning_text(NS(reasoning='a',reasoning_content='a'))=='a'
    with pytest.raises(client.VLMError,match='conflicting'):
        client._reasoning_text(NS(reasoning='a',reasoning_content='b'))


@pytest.mark.parametrize('thinking',[False,True])
def test_token_preflight_matches_explicit_request_template(monkeypatch, thinking):
    cfg=VLMConfig(tag='qwen3.8-27b',backend='openai',model_id='fixture',thinking=thinking,
                  thinking_via_template=True,base_url_env='LOCAL_FIXTURE')
    expected={'enable_thinking':thinking,'preserve_thinking':False}
    if thinking:
        expected['reasoning_effort']='low'
        cfg.extra={'extra_body':{'chat_template_kwargs':expected}}
    monkeypatch.setenv('LOCAL_FIXTURE','http://127.0.0.1:8000/v1')
    monkeypatch.setattr(client,'load_env',lambda:None)
    seen=[]
    class Response:
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def read(self):return b'{"count":19}'
    def tokenize(req,**kwargs):
        seen.append(json.loads(req.data));return Response()
    monkeypatch.setattr(client.urllib.request,'urlopen',tokenize)
    assert client.count_vllm_prompt_tokens([{'type':'text','text':'public task'}],cfg)==19
    assert seen[0]['chat_template_kwargs']==client._template_kwargs(cfg)==expected
