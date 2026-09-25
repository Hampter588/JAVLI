import os
from pathlib import Path
import requests
from .instances import get as get_instance

API="https://api.curseforge.com/v1"
UA="javli/1.0"
GAME_ID=432

class CurseForgeError(RuntimeError): pass

def _headers():
    key=os.getenv("CURSEFORGE_API_KEY")
    if not key:
        raise CurseForgeError("CurseForge API key is not configured. Set CURSEFORGE_API_KEY and open a new terminal.")
    return {"x-api-key":key,"Accept":"application/json","User-Agent":UA}

def _get(path,params=None):
    r=requests.get(API+path,params=params,timeout=30,headers=_headers())
    if r.status_code in (401,403):
        raise CurseForgeError("CurseForge rejected the API key. Check CURSEFORGE_API_KEY.")
    r.raise_for_status()
    body=r.json()
    return body.get("data",body)

def search(query, class_id=6, limit=10, mc=None, loader=None):
    params={"gameId":GAME_ID,"searchFilter":query,"classId":class_id,"pageSize":limit,"sortField":2,"sortOrder":"desc"}
    if mc: params["gameVersion"]=mc
    # CurseForge modLoaderType: 1 Forge, 4 Fabric, 5 Quilt, 6 NeoForge.
    loaders={"forge":1,"fabric":4,"quilt":5,"neoforge":6}
    if loader and loader.lower() in loaders: params["modLoaderType"]=loaders[loader.lower()]
    return _get("/mods/search",params)

def _project_id(project, class_id=6):
    s=str(project)
    if s.isdigit(): return int(s)
    hits=search(s,class_id,10)
    exact=next((x for x in hits if str(x.get("slug","")).lower()==s.lower()),None)
    if exact: return int(exact["id"])
    if not hits: raise CurseForgeError(f"No CurseForge project found for {project}")
    return int(hits[0]["id"])

def _files(project_id, mc=None, loader=None):
    params={"pageSize":50}
    if mc: params["gameVersion"]=mc
    loaders={"forge":1,"fabric":4,"quilt":5,"neoforge":6}
    if loader and loader.lower() in loaders: params["modLoaderType"]=loaders[loader.lower()]
    return _get(f"/mods/{project_id}/files",params)

def choose_file(project,mc=None,loader=None,class_id=6):
    pid=_project_id(project,class_id)
    rows=_files(pid,mc,loader)
    if not rows: raise CurseForgeError(f"No compatible CurseForge file found for {project}")
    rows.sort(key=lambda x:x.get("fileDate",""),reverse=True)
    return pid,rows[0]

def _download_url(pid,file):
    url=file.get("downloadUrl")
    if url: return url
    fid=file["id"]
    try: return _get(f"/mods/{pid}/files/{fid}/download-url")
    except Exception: return None

def _download(pid,file,dest_dir):
    url=_download_url(pid,file)
    if not url:
        raise CurseForgeError(f"CurseForge does not expose an automatic download URL for {file.get('displayName') or file.get('fileName')}. Download this file manually from its CurseForge project page.")
    dest_dir.mkdir(parents=True,exist_ok=True)
    dest=dest_dir/file["fileName"]
    with requests.get(url,stream=True,timeout=120,headers={"User-Agent":UA}) as r:
        r.raise_for_status()
        with dest.open("wb") as out:
            for chunk in r.iter_content(1024*1024):
                if chunk: out.write(chunk)
    return dest

def install_mod(project,instance,mc=None,loader=None,dependencies=True,seen=None):
    obj=get_instance(instance)
    mc=mc or obj["version"]
    loader=loader or obj.get("loader")
    seen=seen or set()
    pid,file=choose_file(project,mc,loader,6)
    key=(pid,file["id"])
    if key in seen:return []
    seen.add(key)
    installed=[_download(pid,file,Path(obj["path"])/"minecraft"/"mods")]
    if dependencies:
        for dep in file.get("dependencies",[]):
            if dep.get("relationType")!=3: continue
            depid=dep.get("modId")
            if depid: installed+=install_mod(str(depid),instance,mc,loader,True,seen)
    return installed

def search_modpacks(query,limit=10,mc=None):
    return search(query,4471,limit,mc,None)
