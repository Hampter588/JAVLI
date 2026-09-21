import json, os, platform, re, shutil, subprocess, zipfile
from pathlib import Path
from .cache import ROOT, VERSIONS, ensure
from .net import download
from .auth import load_account, refresh, AuthError

LIBRARIES = ROOT / "libraries"
ASSETS = ROOT / "assets"
NATIVES = ROOT / "natives"
GAME = ROOT / "game"

def _os_name():
    return {"Windows":"windows","Darwin":"osx","Linux":"linux"}.get(platform.system(), "linux")

def _arch():
    return "64" if platform.machine().lower() in ("amd64","x86_64","arm64","aarch64") else "32"

def _rule_ok(rules):
    if not rules:
        return True
    allowed = False
    for rule in rules:
        applies = True
        osrule = rule.get("os")
        if osrule:
            if osrule.get("name") and osrule["name"] != _os_name():
                applies = False
            if osrule.get("arch"):
                want = osrule["arch"]
                machine = platform.machine().lower()
                if want == "x86" and _arch() != "32": applies = False
                elif want == "x86_64" and machine not in ("amd64","x86_64"): applies = False
                elif want == "arm64" and machine not in ("arm64","aarch64"): applies = False
        # Feature rules are false unless MCLI explicitly enables the feature.
        if rule.get("features"):
            applies = False
        if applies:
            allowed = rule.get("action") == "allow"
    return allowed

def _artifact_path(name):
    group, artifact, version = name.split(":")[:3]
    base = LIBRARIES / Path(*group.split(".")) / artifact / version
    return base / f"{artifact}-{version}.jar"

def _download_libraries(meta, natives_dir):
    cp=[]
    natives_dir.mkdir(parents=True, exist_ok=True)
    for lib in meta.get("libraries", []):
        if not _rule_ok(lib.get("rules")):
            continue
        downloads=lib.get("downloads", {})
        artifact=downloads.get("artifact")
        if artifact and artifact.get("url"):
            dest=LIBRARIES / artifact["path"]
            if not dest.exists():
                download(artifact["url"], dest, artifact.get("sha1"))
            cp.append(str(dest))
        elif lib.get("name"):
            # Legacy / installer-generated launcher profile fallback.
            dest=_artifact_path(lib["name"])
            if not dest.exists() and lib.get("url"):
                parts=lib["name"].split(":")
                if len(parts)>=3:
                    group,artifact_id,ver=parts[:3]
                    rel="/".join(group.split("."))+f"/{artifact_id}/{ver}/{artifact_id}-{ver}.jar"
                    base=lib["url"]
                    if not base.endswith("/"): base+="/"
                    try:
                        download(base+rel,dest)
                    except Exception:
                        pass
            if dest.exists():
                cp.append(str(dest))

        classifiers=downloads.get("classifiers", {})
        nat=lib.get("natives", {}).get(_os_name())
        if nat:
            nat=nat.replace("${arch}", _arch())
            c=classifiers.get(nat)
            if c and c.get("url"):
                dest=LIBRARIES / c["path"]
                if not dest.exists():
                    download(c["url"], dest, c.get("sha1"))
                with zipfile.ZipFile(dest) as z:
                    excludes=(lib.get("extract") or {}).get("exclude", ["META-INF/"])
                    for member in z.infolist():
                        if member.is_dir() or any(member.filename.startswith(x) for x in excludes):
                            continue
                        z.extract(member, natives_dir)
    return cp

def _download_assets(meta):
    idx=meta.get("assetIndex")
    if not idx:
        return meta.get("assets", "legacy")
    indexes=ASSETS/"indexes"
    objects=ASSETS/"objects"
    indexes.mkdir(parents=True, exist_ok=True)
    idx_path=indexes/f'{idx["id"]}.json'
    if not idx_path.exists():
        download(idx["url"], idx_path, idx.get("sha1"))
    data=json.loads(idx_path.read_text(encoding="utf-8"))
    for obj in data.get("objects", {}).values():
        h=obj["hash"]
        dest=objects/h[:2]/h
        if not dest.exists():
            download(f"https://resources.download.minecraft.net/{h[:2]}/{h}", dest, h)
    return idx["id"]

def _java():
    override=os.getenv("MCLI_JAVA")
    if override:
        return override
    found=shutil.which("java")
    if found:
        return found
    raise RuntimeError("Java was not found. Install Java or set MCLI_JAVA to java.exe/java.")

def _subst(value, vars):
    for k,v in vars.items():
        value=value.replace("${"+k+"}", str(v))
    return value

def _modern_args(meta, vars):
    jvm=[]
    game=[]
    args=meta.get("arguments")
    if args:
        for item in args.get("jvm", []):
            if isinstance(item,str):
                jvm.append(_subst(item,vars))
            elif _rule_ok(item.get("rules")):
                vals=item.get("value",[])
                if isinstance(vals,str): vals=[vals]
                jvm += [_subst(x,vars) for x in vals]
        for item in args.get("game", []):
            if isinstance(item,str):
                game.append(_subst(item,vars))
            elif _rule_ok(item.get("rules")):
                vals=item.get("value",[])
                if isinstance(vals,str): vals=[vals]
                game += [_subst(x,vars) for x in vals]
    else:
        # Legacy Mojang metadata.
        raw=meta.get("minecraftArguments","")
        import shlex
        game=[_subst(x,vars) for x in shlex.split(raw, posix=_os_name()!="windows")]
    return jvm,game

def launch(version, client_jar, meta, game_dir_override=None):
    ensure()
    if version.source != "mojang":
        raise RuntimeError(
            "Full JVM launch is implemented for Mojang metadata first. "
            "Omniarchive historical launch compatibility is the next layer."
        )

    account=load_account()
    if not account:
        raise AuthError("No Microsoft account saved. Run: mcli login")
    # Refresh on every launch so Minecraft gets a current access token.
    account=refresh()
    profile=account["profile"]

    natives=NATIVES/version.id
    cp=_download_libraries(meta,natives)
    cp.append(str(client_jar))
    asset_index=_download_assets(meta)
    game_dir=Path(game_dir_override) if game_dir_override else GAME/version.id
    game_dir.mkdir(parents=True,exist_ok=True)

    vars={
        "auth_player_name":profile["name"],
        "version_name":version.id,
        "game_directory":str(game_dir),
        "assets_root":str(ASSETS),
        "assets_index_name":asset_index,
        "auth_uuid":profile["id"],
        "auth_access_token":account["minecraft_access_token"],
        "clientid":"",
        "auth_xuid":"",
        "user_type":"msa",
        "version_type":meta.get("type","release"),
        "natives_directory":str(natives),
        "launcher_name":"mcli",
        "launcher_version":"0.3.0",
        "classpath":os.pathsep.join(cp),
        "classpath_separator":os.pathsep,
        "library_directory":str(LIBRARIES),
        "user_properties":"{}",
        "resolution_width":"854",
        "resolution_height":"480",
    }
    jvm_args,game_args=_modern_args(meta,vars)
    if not any(x.startswith("-Xmx") for x in jvm_args):
        jvm_args.insert(0,"-Xmx2G")
    if not any("java.library.path" in x for x in jvm_args):
        jvm_args.append("-Djava.library.path="+str(natives))
    if "-cp" not in jvm_args and "-classpath" not in jvm_args:
        jvm_args += ["-cp",vars["classpath"]]

    main=meta.get("mainClass")
    if not main:
        raise RuntimeError("Version metadata has no mainClass.")
    from .java_manager import resolve as resolve_java
    java = resolve_java(meta=meta, version_id=version.id)
    cmd=[str(java),*jvm_args,main,*game_args]
    print("Launching", version.id, "as", profile["name"])
    return subprocess.Popen(cmd,cwd=game_dir)
