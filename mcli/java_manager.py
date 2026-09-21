import json, os, platform, shutil, subprocess, tarfile, zipfile
from pathlib import Path
import requests
from .cache import ROOT

RUNTIMES = ROOT / "runtimes"
UA = "mcli/0.5"
ADOPTIUM = "https://api.adoptium.net/v3"

class JavaError(RuntimeError): pass

def os_name():
    return {"Windows":"windows","Darwin":"mac","Linux":"linux"}.get(platform.system(),"linux")

def arch_name():
    m=platform.machine().lower()
    if m in ("amd64","x86_64"): return "x64"
    if m in ("arm64","aarch64"): return "aarch64"
    if m in ("x86","i386","i686"): return "x86"
    return m

def java_exe(home: Path):
    return home / "bin" / ("java.exe" if os_name()=="windows" else "java")

def installed():
    out=[]
    if RUNTIMES.exists():
        for p in RUNTIMES.iterdir():
            if p.is_dir():
                j=java_exe(p)
                if j.exists():
                    out.append((p.name,p,j))
    return sorted(out)

def detect_system():
    j=shutil.which("java")
    return Path(j) if j else None

def java_major(exe):
    try:
        p=subprocess.run([str(exe),"-version"],capture_output=True,text=True,timeout=10)
        txt=(p.stderr or "")+(p.stdout or "")
        import re
        m=re.search(r'version "([^"]+)',txt)
        if not m: return None
        v=m.group(1)
        if v.startswith("1."): return int(v.split(".")[1])
        return int(v.split(".")[0])
    except Exception:
        return None

def recommended_major(meta, version_id=None):
    # Mojang metadata is authoritative when present.
    jv=(meta or {}).get("javaVersion") or {}
    if jv.get("majorVersion"):
        return int(jv["majorVersion"])

    # Historical fallback. Java 8 is the broadest useful default for old jars.
    vid=(version_id or "").lower()
    if any(x in vid for x in ("classic","indev","infdev")):
        return 8
    return 8

def _api_asset(major):
    url=f"{ADOPTIUM}/assets/latest/{major}/hotspot"
    params={"architecture":arch_name(),"image_type":"jre","os":os_name(),"vendor":"eclipse"}
    r=requests.get(url,params=params,timeout=30,headers={"User-Agent":UA})
    r.raise_for_status()
    data=r.json()
    if not data:
        # Some platforms/majors may publish JDK but not JRE.
        params["image_type"]="jdk"
        r=requests.get(url,params=params,timeout=30,headers={"User-Agent":UA})
        r.raise_for_status()
        data=r.json()
    if not data:
        raise JavaError(f"No Java {major} runtime found for {os_name()} {arch_name()}.")
    pkg=data[0]["binary"]["package"]
    return pkg["link"],pkg.get("checksum")

def install(major, force=False):
    major=int(major)
    final=RUNTIMES/f"java-{major}"
    if java_exe(final).exists() and not force:
        return final
    RUNTIMES.mkdir(parents=True,exist_ok=True)
    url,checksum=_api_asset(major)
    ext=".zip" if os_name()=="windows" else ".tar.gz"
    archive=RUNTIMES/f"java-{major}{ext}"
    with requests.get(url,stream=True,timeout=120,headers={"User-Agent":UA}) as r:
        r.raise_for_status()
        with archive.open("wb") as f:
            for c in r.iter_content(1024*1024):
                if c: f.write(c)
    tmp=RUNTIMES/f".java-{major}-extract"
    if tmp.exists(): shutil.rmtree(tmp)
    tmp.mkdir()
    if ext==".zip":
        with zipfile.ZipFile(archive) as z: z.extractall(tmp)
    else:
        with tarfile.open(archive,"r:gz") as t: t.extractall(tmp)
    children=[p for p in tmp.iterdir() if p.is_dir()]
    home=children[0] if len(children)==1 else tmp
    if final.exists(): shutil.rmtree(final)
    if home==tmp:
        final.mkdir()
        for x in list(tmp.iterdir()): shutil.move(str(x),final/x.name)
        tmp.rmdir()
    else:
        shutil.move(str(home),str(final))
        shutil.rmtree(tmp,ignore_errors=True)
    archive.unlink(missing_ok=True)
    if not java_exe(final).exists():
        # macOS packages commonly put the runtime beneath Contents/Home.
        mh=final/"Contents"/"Home"
        if java_exe(mh).exists():
            actual=mh
            normalized=RUNTIMES/f".java-{major}-normalized"
            if normalized.exists(): shutil.rmtree(normalized)
            shutil.copytree(actual,normalized)
            shutil.rmtree(final)
            normalized.rename(final)
    if not java_exe(final).exists():
        raise JavaError("Java archive extracted, but java executable was not found.")
    return final

def resolve(meta=None, version_id=None, legacy=False, auto_install=True):
    override=os.getenv("MCLI_LEGACY_JAVA" if legacy else "MCLI_JAVA")
    if override and Path(override).exists():
        return Path(override)
    major=8 if legacy else recommended_major(meta,version_id)
    managed=RUNTIMES/f"java-{major}"
    if java_exe(managed).exists():
        return java_exe(managed)
    system=detect_system()
    if system and java_major(system)==major:
        return system
    if auto_install:
        print(f"Java {major} is required; installing a managed runtime...")
        return java_exe(install(major))
    raise JavaError(f"Java {major} is required but not installed.")
