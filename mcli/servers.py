import json, os, re, shutil, signal, subprocess, time
from pathlib import Path
import requests
from .cache import ROOT
from .java_manager import resolve as resolve_java
from .net import download

SERVERS=ROOT/"servers"
INDEX=ROOT/"servers.json"
UA="MCLI/1.0 (https://github.com/Hampter588/MCLI)"

class ServerError(RuntimeError): pass

def _load():
    try: return json.loads(INDEX.read_text(encoding="utf-8"))
    except Exception: return {}

def _save(x):
    ROOT.mkdir(parents=True,exist_ok=True)
    INDEX.write_text(json.dumps(x,indent=2),encoding="utf-8")

def _safe(name):
    return bool(re.fullmatch(r"[A-Za-z0-9._-]+",name))

def get(name):
    x=_load().get(name)
    if not x: raise ServerError(f"Unknown server: {name}")
    return x

def list_servers():
    return list(_load().values())

def _mojang_server(version):
    from .sources.mojang import MojangSource
    src=MojangSource()
    v=next((x for x in src.versions() if x.id==version),None)
    if not v: raise ServerError(f"Mojang version not found: {version}")
    meta=src.details(v)
    art=(meta.get("downloads") or {}).get("server")
    if not art: raise ServerError(f"Mojang does not publish a server JAR for {version}")
    return art,meta

def _paper(version):
    # PaperMC retired the old api.papermc.io v2 downloads API.
    # Fill v3 returns build objects directly and includes canonical download URLs.
    api=f"https://fill.papermc.io/v3/projects/paper/versions/{version}/builds"
    r=requests.get(api,timeout=30,headers={"User-Agent":UA})
    if not r.ok:
        try:
            msg=(r.json() or {}).get("message")
        except Exception:
            msg=None
        raise ServerError(msg or f"Paper has no build for {version}")

    data=r.json()
    if isinstance(data,dict) and data.get("ok") is False:
        raise ServerError(data.get("message") or f"Paper has no build for {version}")
    builds=data if isinstance(data,list) else data.get("builds",[])
    if not builds:
        raise ServerError(f"Paper has no build for {version}")

    # Prefer the newest stable build. If a version only has experimental builds,
    # use the newest available build rather than incorrectly claiming it doesn't exist.
    stable=[b for b in builds if str(b.get("channel","")).upper()=="STABLE"]
    candidates=stable or builds

    def build_number(b):
        value=b.get("id",b.get("number",0))
        try: return int(value)
        except Exception: return 0

    build=max(candidates,key=build_number)
    downloads=build.get("downloads") or {}
    app=downloads.get("server:default") or downloads.get("application") or {}
    url=app.get("url")
    if not url:
        raise ServerError(f"Paper build {build_number(build)} for {version} has no server download URL")
    return url,build_number(build)

def create(name,version,kind="vanilla",memory="2G"):
    if not _safe(name): raise ServerError("Server name may contain letters, numbers, dot, underscore and dash.")
    data=_load()
    if name in data: raise ServerError(f"Server already exists: {name}")
    d=SERVERS/name; d.mkdir(parents=True,exist_ok=False)
    jar=d/"server.jar"
    meta=None
    if kind=="vanilla":
        art,meta=_mojang_server(version)
        download(art["url"],jar,art.get("sha1"))
    elif kind=="paper":
        url,build=_paper(version)
        download(url,jar)
    else:
        raise ServerError("v0.11 server creation supports vanilla and Paper directly.")
    obj={"name":name,"version":version,"kind":kind,"memory":memory,"path":str(d),"pid":None}
    (d/"eula.txt").write_text("eula=false\n",encoding="utf-8")
    (d/"server.properties").touch()
    (d/"mcli-server.json").write_text(json.dumps(obj,indent=2),encoding="utf-8")
    data[name]=obj; _save(data)
    return obj,meta

def accept_eula(name):
    data=_load(); obj=get(name)
    Path(obj["path"],"eula.txt").write_text("eula=true\n",encoding="utf-8")
    obj["eula"]=True; data[name]=obj; _save(data)

def _alive(pid):
    if not pid: return False
    try:
        os.kill(int(pid),0); return True
    except OSError: return False

def start(name,foreground=False):
    data=_load(); obj=get(name)
    if _alive(obj.get("pid")): raise ServerError(f"{name} is already running (PID {obj['pid']})")
    d=Path(obj["path"])
    if "eula=true" not in (d/"eula.txt").read_text(encoding="utf-8",errors="ignore").lower():
        raise ServerError(f"EULA is not accepted. Read Mojang's EULA, then run: mcli server eula {name}")
    _,meta=_mojang_server(obj["version"])
    java=resolve_java(meta=meta,version_id=obj["version"])
    cmd=[str(java),f'-Xms{obj["memory"]}',f'-Xmx{obj["memory"]}',"-jar","server.jar","nogui"]
    log=(d/"server.log").open("a",encoding="utf-8")
    if foreground:
        return subprocess.Popen(cmd,cwd=d)
    flags=0
    if os.name=="nt": flags=subprocess.CREATE_NEW_PROCESS_GROUP
    p=subprocess.Popen(cmd,cwd=d,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,
                       creationflags=flags,start_new_session=(os.name!="nt"))
    obj["pid"]=p.pid; data[name]=obj; _save(data)
    return p

def stop(name):
    data=_load(); obj=get(name); pid=obj.get("pid")
    if not _alive(pid):
        obj["pid"]=None; data[name]=obj; _save(data); return False
    if os.name=="nt":
        subprocess.run(["taskkill","/PID",str(pid),"/T","/F"],capture_output=True)
    else:
        os.killpg(os.getpgid(int(pid)),signal.SIGTERM)
    obj["pid"]=None; data[name]=obj; _save(data)
    return True

def status(name):
    obj=get(name)
    return obj,_alive(obj.get("pid"))

def delete(name,keep_files=False):
    data=_load(); obj=get(name)
    if _alive(obj.get("pid")): raise ServerError("Stop the server before deleting it.")
    data.pop(name,None); _save(data)
    if not keep_files: shutil.rmtree(obj["path"],ignore_errors=True)

def properties(name,key=None,value=None):
    p=Path(get(name)["path"])/"server.properties"
    lines=p.read_text(encoding="utf-8",errors="ignore").splitlines() if p.exists() else []
    vals={}
    for line in lines:
        if "=" in line and not line.lstrip().startswith("#"):
            k,v=line.split("=",1); vals[k]=v
    if key is None: return vals
    if value is None: return vals.get(key)
    vals[key]=value
    p.write_text("\n".join(f"{k}={v}" for k,v in vals.items())+"\n",encoding="utf-8")
    return value
