from PyInstaller.__main__ import run
import os, platform, shutil
from pathlib import Path
root=Path(__file__).resolve().parents[1]
dist=root/"dist"; build=root/"build"; spec=root/"mcli.spec"
for p in (dist,build): shutil.rmtree(p,ignore_errors=True)
if spec.exists(): spec.unlink()
run([str(root/"mcli"/"__main__.py"),"--name=mcli","--onefile","--clean","--noconfirm",f"--distpath={dist}",f"--workpath={build}",f"--specpath={root}","--collect-submodules=mcli"])
exe=dist/("mcli.exe" if os.name=="nt" else "mcli")
if not exe.exists(): raise SystemExit(f"Expected binary not found: {exe}")
print(f"Built {exe}"); print(f"Platform: {platform.system()} {platform.machine()}")
