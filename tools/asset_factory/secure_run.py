"""Bounded Linux subprocess execution for trusted local Blender/Godot.

No shell, no inherited credential environment, process-group cleanup and bounded log.
Not a network/OS sandbox; only trusted executable inputs.
"""
import os
from pathlib import Path
import resource
import signal
import subprocess
import sys

LOG_LIMIT=8*1024*1024
OUTPUT_LIMIT=64*1024*1024


def _limits():
    resource.setrlimit(resource.RLIMIT_FSIZE,(OUTPUT_LIMIT,OUTPUT_LIMIT))
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    resource.setrlimit(resource.RLIMIT_NOFILE,(1024,1024))
    resource.setrlimit(resource.RLIMIT_CPU,(240,250))


def run(cmd,work,log,timeout):
    if sys.platform!="linux":
        raise ValueError("bounded runner requires Linux")
    work=Path(work).resolve()
    log=Path(log).absolute()
    if log.parent!=work or log.exists() or log.is_symlink():
        raise ValueError("new log inside workspace required")
    env={k:os.environ[k] for k in ("PATH","LANG","LC_ALL","DISPLAY","XAUTHORITY","LD_LIBRARY_PATH","TMPDIR","LIBGL_ALWAYS_SOFTWARE","XDG_RUNTIME_DIR") if k in os.environ}
    home=work/"runtime-home"
    home.mkdir(mode=0o700,exist_ok=True)
    if home.is_symlink() or home.resolve()!=home:
        raise ValueError("unsafe runtime home")
    env.update(HOME=str(home),XDG_CONFIG_HOME=str(home/"config"),XDG_CACHE_HOME=str(home/"cache"),
               PYTHONNOUSERSITE="1",GODOT_SILENCE_ROOT_WARNING="0")
    with log.open("xb") as f:
        proc=subprocess.Popen(cmd,cwd=work,stdout=f,stderr=subprocess.STDOUT,env=env,
                              start_new_session=True,preexec_fn=_limits)
        try:
            code=proc.wait(timeout=timeout)
        except BaseException:
            try:os.killpg(proc.pid,signal.SIGKILL)
            except ProcessLookupError:pass
            proc.wait()
            raise
        finally:
            # Kill lingering group members even if the direct child exited.
            try:os.killpg(proc.pid,signal.SIGKILL)
            except ProcessLookupError:pass
        if code:
            raise subprocess.CalledProcessError(code,cmd)
    with log.open("rb") as f:
        raw=f.read(LOG_LIMIT+1)
    if len(raw)>LOG_LIMIT:
        raise ValueError("tool log exceeds read limit")
    return raw.decode("utf-8",errors="replace")
