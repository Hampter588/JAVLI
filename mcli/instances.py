import json, re, shutil
from pathlib import Path
from .cache import ROOT

INSTANCES = ROOT / "instances"
INDEX = ROOT / "instances.json"

class InstanceError(RuntimeError): pass

def _load():
    try:
        data=json.loads(INDEX.read_text(encoding="utf-8"))
        return data if isinstance(data,dict) else {}
    except Exception:
        return {}

def _save(data):
    ROOT.mkdir(parents=True,exist_ok=True)
    INDEX.write_text(json.dumps(data,indent=2),encoding="utf-8")

def valid_name(name):
    return bool(re.fullmatch(r"[A-Za-z0-9._-]+",name))

def create(name, era, version, source="auto"):
    if not valid_name(name):
        raise InstanceError("Instance names may contain letters, numbers, dot, underscore and dash.")
    data=_load()
    if name in data:
        raise InstanceError(f"Instance already exists: {name}")
    path=INSTANCES/name
    path.mkdir(parents=True,exist_ok=False)
    for sub in ("minecraft","mods","resourcepacks","shaderpacks","screenshots"):
        (path/sub).mkdir(exist_ok=True)
    obj={"name":name,"era":era,"version":version,"source":source,"path":str(path)}
    (path/"instance.json").write_text(json.dumps(obj,indent=2),encoding="utf-8")
    data[name]=obj
    _save(data)
    return obj

def get(name):
    obj=_load().get(name)
    if not obj:
        raise InstanceError(f"Unknown instance: {name}")
    return obj

def list_instances():
    return list(_load().values())

def delete(name, keep_files=False):
    data=_load()
    obj=data.pop(name,None)
    if not obj:
        raise InstanceError(f"Unknown instance: {name}")
    _save(data)
    if not keep_files:
        shutil.rmtree(Path(obj["path"]),ignore_errors=True)
    return obj

def clone(src, dest):
    old=get(src)
    if not valid_name(dest):
        raise InstanceError("Invalid destination instance name.")
    data=_load()
    if dest in data:
        raise InstanceError(f"Instance already exists: {dest}")
    srcp=Path(old["path"]); dstp=INSTANCES/dest
    shutil.copytree(srcp,dstp)
    obj=dict(old); obj["name"]=dest; obj["path"]=str(dstp)
    (dstp/"instance.json").write_text(json.dumps(obj,indent=2),encoding="utf-8")
    data[dest]=obj; _save(data)
    return obj

def set_value(name,key,value):
    data=_load()
    if name not in data: raise InstanceError(f"Unknown instance: {name}")
    if key not in ("version","era","source"):
        raise InstanceError("Editable fields: version, era, source")
    data[name][key]=value
    p=Path(data[name]["path"])/"instance.json"
    p.write_text(json.dumps(data[name],indent=2),encoding="utf-8")
    _save(data)
    return data[name]
