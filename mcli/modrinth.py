import json, shutil, zipfile
from pathlib import Path
import requests
from .instances import get as get_instance

API="https://api.modrinth.com/v2"
UA="mcli/0.8 (Minecraft CLI launcher)"

class ModrinthError(RuntimeError): pass

def _get(path, params=None):
    r=requests.get(API+path,params=params,timeout=30,headers={"User-Agent":UA})
    r.raise_for_status()
    return r.json()

def search(query, project_type="mod", limit=10, mc=None, loader=None):
    facets=[[f"project_type:{project_type}"]]
    if mc: facets.append([f"versions:{mc}"])
    if loader: facets.append([f"categories:{loader}"])
    return _get("/search",{"query":query,"limit":limit,"facets":json.dumps(facets)}).get("hits",[])

def project_versions(project, mc=None, loader=None):
    params={"include_changelog":"false"}
    if mc: params["game_versions"]=json.dumps([mc])
    if loader: params["loaders"]=json.dumps([loader])
    return _get(f"/project/{project}/version",params)

def choose_version(project, mc=None, loader=None):
    versions=project_versions(project,mc,loader)
    versions=[v for v in versions if v.get("status") in (None,"listed")]
    if not versions: raise ModrinthError(f"No compatible Modrinth version found for {project}")
    # API is normally newest-first. Prefer release, then beta/alpha.
    versions.sort(key=lambda v: (v.get("version_type")=="release",v.get("date_published","")),reverse=True)
    return versions[0]

def _primary(v):
    files=v.get("files",[])
    if not files: raise ModrinthError("Version has no downloadable files.")
    return next((f for f in files if f.get("primary")),files[0])

def _download_file(f,dest_dir):
    dest_dir.mkdir(parents=True,exist_ok=True)
    dest=dest_dir/f["filename"]
    r=requests.get(f["url"],stream=True,timeout=90,headers={"User-Agent":UA})
    r.raise_for_status()
    with dest.open("wb") as out:
        for c in r.iter_content(1024*1024):
            if c: out.write(c)
    return dest

def install_mod(project, instance, mc=None, loader=None, dependencies=True, seen=None):
    obj=get_instance(instance)
    mc=mc or obj["version"]
    seen=seen or set()
    v=choose_version(project,mc,loader)
    if v["id"] in seen: return []
    seen.add(v["id"])
    installed=[]
    f=_primary(v)
    installed.append(_download_file(f,Path(obj["path"])/"minecraft"/"mods"))
    if dependencies:
        for dep in v.get("dependencies",[]):
            if dep.get("dependency_type")!="required": continue
            depid=dep.get("version_id")
            project_id=dep.get("project_id")
            if depid:
                dv=_get(f"/version/{depid}")
                if dv["id"] in seen: continue
                seen.add(dv["id"])
                installed.append(_download_file(_primary(dv),Path(obj["path"])/"minecraft"/"mods"))
            elif project_id:
                installed += install_mod(project_id,instance,mc,loader,True,seen)
    return installed

def remove_mod(name,instance):
    obj=get_instance(instance)
    mods=Path(obj["path"])/"minecraft"/"mods"
    hits=[p for p in mods.glob("*") if name.lower() in p.name.lower()]
    for p in hits: p.unlink()
    return hits

def list_mods(instance):
    obj=get_instance(instance)
    mods=Path(obj["path"])/"minecraft"/"mods"
    return sorted([p for p in mods.glob("*") if p.is_file()])

def install_modpack(project, instance):
    obj=get_instance(instance)
    v=choose_version(project,obj["version"],None)
    f=_primary(v)
    tmp=Path(obj["path"])/".mcli-pack"
    tmp.mkdir(parents=True,exist_ok=True)
    pack=_download_file(f,tmp)
    if pack.suffix.lower()!=".mrpack":
        raise ModrinthError("Selected Modrinth file is not an .mrpack.")
    game=Path(obj["path"])/"minecraft"
    with zipfile.ZipFile(pack) as z:
        index=json.loads(z.read("modrinth.index.json"))
        # Overrides are copied into the game directory.
        for prefix in ("overrides/","client-overrides/"):
            for m in z.infolist():
                if m.filename.startswith(prefix) and not m.is_dir():
                    rel=m.filename[len(prefix):]
                    dest=game/rel; dest.parent.mkdir(parents=True,exist_ok=True)
                    with z.open(m) as src, dest.open("wb") as out: shutil.copyfileobj(src,out)
        for entry in index.get("files",[]):
            env=(entry.get("env") or {}).get("client")
            if env=="unsupported": continue
            downloads=entry.get("downloads") or []
            if not downloads: continue
            dest=game/entry["path"]; dest.parent.mkdir(parents=True,exist_ok=True)
            r=requests.get(downloads[0],stream=True,timeout=90,headers={"User-Agent":UA}); r.raise_for_status()
            with dest.open("wb") as out:
                for c in r.iter_content(1024*1024):
                    if c: out.write(c)
    shutil.rmtree(tmp,ignore_errors=True)
    return index
