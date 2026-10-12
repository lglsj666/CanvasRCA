"""Offline DOM measurement of existing components with the actual renderer font.

This admission API emits audit records only. It cannot emit a dashboard or
declare a measured collection to be a qualified model input.
"""
import os
import subprocess
from pathlib import Path

from .main import node_runtime
from .utils import ROOT, RENDERER


def measure_jobs(job_file, log_path):
    bundle = RENDERER / 'web/dist/measure.mjs'
    if not bundle.is_file():
        raise FileNotFoundError('Build the unified renderer measurement bundle')
    env = dict(os.environ, PLAYWRIGHT_BROWSERS_PATH=str(ROOT / 'build/renderer_tooling/browsers'))
    with Path(log_path).open('w') as log:
        subprocess.run([str(node_runtime()), str(bundle), str(job_file)],
                       cwd=RENDERER/'web', env=env, stdout=log, stderr=subprocess.STDOUT,
                       check=True, timeout=3600)
