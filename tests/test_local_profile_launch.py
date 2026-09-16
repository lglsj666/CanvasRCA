"""Shared local deployment selection and live-command integrity checks; no models."""
import json
import os
from pathlib import Path
import subprocess

import pytest
from vlmrca.run_state import verify_process_command


@pytest.mark.parametrize('explicit',[False,True])
def test_sourced_local_environment_preserves_explicit_profile(tmp_path,explicit):
    root=Path(__file__).resolve().parents[1]
    expected=str(root/'configs/vllm_inference_local.yaml')
    env={**os.environ,'CANVASRCA_STANDALONE':'1','CANVASRCA_CACHE_ROOT':str(tmp_path/'cache')}
    env.pop('CANVASRCA_VLLM_CONFIG',None)
    if explicit:
        expected=str(tmp_path/'explicit profile.yaml')
        env['CANVASRCA_VLLM_CONFIG']=expected
    result=subprocess.run(['bash','-c','source scripts/env_local.sh\nprintf "%s" "$CANVASRCA_VLLM_CONFIG"'],
                          cwd=root,env=env,check=True,capture_output=True,text=True)
    assert result.stdout==expected


def test_live_process_command_rejects_silent_default_profile(monkeypatch):
    expected=['checkpoint','--reasoning-parser','qwen3']
    monkeypatch.setattr(Path,'read_bytes',lambda p:b'/python\0/vllm\0serve\0checkpoint\0--reasoning-parser\0qwen3\0')
    assert verify_process_command(123,expected)[2]=='serve'
    with pytest.raises(ValueError,match='configuration'):
        verify_process_command(123,['checkpoint'])
    monkeypatch.setattr(Path,'read_bytes',lambda p:b'/python\0/vllm\0serve\0checkpoint\0')
    with pytest.raises(ValueError,match='configuration'):
        verify_process_command(123,expected)


def test_local_environment_uses_dedicated_inference_venv(tmp_path):
    root=Path(__file__).resolve().parents[1]
    resources=tmp_path/'local resources'
    env={**os.environ,'CANVASRCA_STANDALONE':'1',
         'CANVASRCA_LOCAL_RESOURCE_ROOT':str(resources),
         'CANVASRCA_CACHE_ROOT':str(tmp_path/'cache')}
    result=subprocess.run(['bash','-c',
        'source scripts/env_local.sh\nprintf "%s\\n" "$CANVASRCA_ENV" "$CANVASRCA_PYTHON" "$CANVASRCA_VLLM_BIN"'],
        cwd=root,env=env,check=True,capture_output=True,text=True)
    infer=resources/'venvs/infer'
    assert result.stdout.splitlines()==[str(infer),str(infer/'bin/python'),str(infer/'bin/vllm')]
