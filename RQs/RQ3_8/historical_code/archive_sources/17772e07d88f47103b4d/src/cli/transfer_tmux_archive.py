"""Transfer an explicit tar archive through the user-authenticated tmux SSH TTY.

Does not alter authentication or create a network listener. Remote extraction is
restricted to a registered staging tree; deployment is a separate explicit step.
"""
import argparse
import base64
import hashlib
from pathlib import Path
import shlex
import subprocess
import time


def tmux(*args,**kwargs):
    return subprocess.run(['tmux',*args],check=True,**kwargs)


def main():
    p=argparse.ArgumentParser();p.add_argument('archive',type=Path);p.add_argument('--tag',required=True)
    p.add_argument('--remote-root',required=True);p.add_argument('--remote-python',required=True)
    p.add_argument('--pane',required=True)
    args=p.parse_args()
    if not args.tag.replace('_','').isalnum():raise ValueError('unsafe tag')
    data=args.archive.read_bytes();expected=hashlib.sha256(data).hexdigest()
    target=args.remote_root.rstrip('/')+'/'+args.tag
    code=("import sys,base64,pathlib,hashlib,tarfile,io; "
          "blob=bytearray(); "
          "exec(\"for line in sys.stdin:\\n if line.strip()=='RQ38_END': break\\n blob.extend(base64.b64decode(line))\"); "
          f"assert hashlib.sha256(blob).hexdigest()=={expected!r}; "
          f"root=pathlib.Path({target!r}); root.mkdir(parents=True,exist_ok=True); "
          "t=tarfile.open(fileobj=io.BytesIO(blob),mode='r:gz'); "
          "assert all(not m.issym() and not m.islnk() and (root/m.name).resolve().is_relative_to(root.resolve()) for m in t.getmembers()); "
          "t.extractall(root,filter='data'); print('TRANSFER_COMPLETE',len(blob),flush=True)")
    command='stty -echo; '+shlex.quote(args.remote_python)+' -u -c '+shlex.quote(code)+'; stty echo'
    tmux('send-keys','-t',args.pane,'-l',command)
    tmux('send-keys','-t',args.pane,'Enter')
    time.sleep(1)
    encoded=base64.b64encode(data)
    # Line length below the Linux canonical terminal input bound (4096).
    lines=[encoded[i:i+3000]+b'\n' for i in range(0,len(encoded),3000)]
    for i in range(0,len(lines),64):
        tmux('load-buffer','-b','rq38transfer','-',input=b''.join(lines[i:i+64]))
        tmux('paste-buffer','-d','-b','rq38transfer','-t',args.pane)
        time.sleep(.08)
    tmux('send-keys','-t',args.pane,'-l','RQ38_END')
    tmux('send-keys','-t',args.pane,'Enter')
    print('Sent',len(data),'bytes; expected sha256',expected,'staging',target)


if __name__=='__main__':main()
