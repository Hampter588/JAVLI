import json, re, subprocess
from pathlib import Path
import requests
from .cache import ROOT
from .java_manager import resolve as resolve_java

LOADERS=ROOT/"loaders"
UA="mcli/0.7"
FABRIC="https://meta.fabricmc.net"
QUILT="https://meta.quiltmc.org"

class LoaderError(RuntimeError): pass

def _get(url):
    r=requests.get(url,timeout=30,headers={"User-Agent":UA})
    r.raise_for_status()
    return r.json()

def _write_profile(loader, mc, data):
    d=LOADERS/loader/mc
    d.mkdir(parents=True,exist_ok=True)
    p=d/"version.json"
    p.write_text(json.dumps(data,indent=2),encoding="utf-8")
    return p

def fabric(mc, loader_version=None):
    rows=_get(f"{FABRIC}/v2/versions/loader/{mc}")
    if not rows: raise LoaderError(f"Fabric has no loader metadata for Minecraft {mc}")
    lv=loader_version or rows[0]["loader"]["version"]
    profile=_get(f"{FABRIC}/v2/versions/loader/{mc}/{lv}/profile/json")
    return _write_profile("fabric",mc,profile),lv

def quilt(mc, loader_version=None):
    rows=_get(f"{QUILT}/v3/versions/loader/{mc}")
    if not rows: raise LoaderError(f"Quilt has no loader metadata for Minecraft {mc}")
    # v3 rows expose loader.version
    lv=loader_version or rows[0]["loader"]["version"]
    profile=_get(f"{QUILT}/v3/versions/loader/{mc}/{lv}/profile/json")
    return _write_profile("quilt",mc,profile),lv

def _maven_versions(url):
    r=requests.get(url,timeout=30,headers={"User-Agent":UA}); r.raise_for_status()
    return re.findall(r'href=["\\\']([^/"\\\']+)/["\\\']', r.text)

def neoforge(mc, loader_version=None):
    base="https://maven.neoforged.net/releases/net/neoforged/neoforge/"
    versions=_maven_versions(base)
    # NeoForge 20.2+ versioning follows MC minor lines (e.g. 21.1.x for 1.21.1).
    parts=mc.split(".")
    prefix=None
    if len(parts)>=2 and parts[0]=="1":
        prefix=parts[1] + ("."+parts[2] if len(parts)>=3 else ".0") + "."
    candidates=[v for v in versions if not prefix or v.startswith(prefix)]
    if not candidates: raise LoaderError(f"No NeoForge installer found for Minecraft {mc}")
    lv=loader_version or candidates[-1]
    url=f"{base}{lv}/neoforge-{lv}-installer.jar"
    return _installer("neoforge",mc,lv,url)

def forge(mc, loader_version=None):
    base=f"https://maven.minecraftforge.net/net/minecraftforge/forge/"
    versions=_maven_versions(base)
    prefix=mc+"-"
    candidates=[v for v in versions if v.startswith(prefix)]
    if loader_version:
        full=loader_version if loader_version.startswith(prefix) else prefix+loader_version
    elif candidates:
        full=candidates[-1]
    else:
        raise LoaderError(f"No Forge installer found for Minecraft {mc}")
    forgever=full[len(prefix):]
    url=f"{base}{full}/forge-{full}-installer.jar"
    return _installer("forge",mc,forgever,url)

def _installer(loader,mc,lv,url):
    d=LOADERS/loader/mc/lv
    d.mkdir(parents=True,exist_ok=True)
    jar=d/f"{loader}-{lv}-installer.jar"
    if not jar.exists():
        r=requests.get(url,timeout=90,headers={"User-Agent":UA}); r.raise_for_status()
        jar.write_bytes(r.content)
    java=resolve_java(version_id=mc)
    # Client installers understand --installClient and install into a launcher-style directory.
    target=d/"client"
    target.mkdir(exist_ok=True)
    proc=subprocess.run([str(java),"-jar",str(jar),"--installClient",str(target)],
                        cwd=target,text=True,capture_output=True)
    if proc.returncode:
        raise LoaderError(proc.stdout+"\n"+proc.stderr)
    return target,lv

def install_loader(loader,mc,loader_version=None):
    if loader=="fabric": return fabric(mc,loader_version)
    if loader=="quilt": return quilt(mc,loader_version)
    if loader=="forge": return forge(mc,loader_version)
    if loader=="neoforge": return neoforge(mc,loader_version)
    raise LoaderError("Unknown modloader: "+loader)
