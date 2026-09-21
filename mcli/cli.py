import argparse, json, sys
from .catalog import all_versions, resolve
from .install import install

ERA_TYPES = ["release", "snapshot", "beta", "alpha", "infdev", "indev", "classic", "preclassic"]

def normalize_type(v):
    return {"old_beta":"beta", "old_alpha":"alpha"}.get(v, v)


def _print_source_warnings(errors):
    if errors:
        print("\nSource warnings:", file=sys.stderr)
        for e in errors: print("  "+e,file=sys.stderr)

def cmd_versions(args):
    from .discovery import versions
    rows,errors=versions(args.source,args.type,getattr(args,"historical",False),getattr(args,"query",None))
    limit=getattr(args,"limit",None)
    if limit: rows=rows[:limit]
    print(f'{"VERSION":28} {"ERA":12} {"SOURCE":12} RELEASED')
    print("-"*78)
    for v in rows:
        typ={"old_beta":"beta","old_alpha":"alpha"}.get(v.type,v.type)
        print(f"{v.id:28} {typ:12} {v.source:12} {v.release_time or '-'}")
    print(f"\n{len(rows)} version(s)")
    _print_source_warnings(errors)

def cmd_search(args):
    from .discovery import search_versions
    rows,errors=search_versions(args.query,args.source,args.type)
    rows=rows[:args.limit]
    print(f'{"VERSION":28} {"ERA":12} {"SOURCE":12}')
    print("-"*56)
    for v in rows:
        typ={"old_beta":"beta","old_alpha":"alpha"}.get(v.type,v.type)
        print(f"{v.id:28} {typ:12} {v.source:12}")
    _print_source_warnings(errors)


def cmd_info(args):
    from .discovery import info
    data,errors=info(args.version,args.source)
    if not data:
        raise SystemExit(f"Version not found: {args.version}")
    print(json.dumps(data,indent=2))
    _print_source_warnings(errors)

def cmd_stats(args):
    from .discovery import stats
    data,errors=stats(args.source)
    print("Total:",data["total"])
    print("By source:")
    for k,v in sorted(data["by_source"].items()): print(f"  {k:14} {v}")
    print("By era:")
    for k,v in sorted(data["by_type"].items()): print(f"  {k:14} {v}")
    _print_source_warnings(errors)

def cmd_launch(args):
    v, errors = resolve(args.version, args.source)
    if not v:
        raise SystemExit(f"Version not found: {args.version}")
    wanted = args.era
    actual = normalize_type(v.type)
    # Mojang collapses legacy eras into old_alpha/old_beta, so only reject clear modern mismatches.
    if wanted in ("release","snapshot","beta","alpha") and actual not in (wanted, "archived", "unknown"):
        raise SystemExit(f"{args.version} is catalogued as {actual}, not {wanted}")
    path, meta = install(v)
    print(f"Installed {v.id} from {v.source}")
    selected = next((x for x in ("fabric","forge","neoforge","quilt") if getattr(args,x,False)), None)
    if selected:
        if v.source != "mojang":
            raise SystemExit("Modloaders are supported on Mojang-backed versions, not raw Omniarchive jars.")
        if selected in ("fabric","quilt"):
            from .loader_launch import launch_profile
            proc, lv = launch_profile(selected, v, path, meta, loader_version=args.loader_version)
            print(f"Started {selected} {lv} on Minecraft {v.id} (PID {proc.pid})")
            return
        if selected in ("forge","neoforge"):
            from .loader_launch import launch_installer_profile
            proc, lv, profile = launch_installer_profile(selected, v, path, meta, loader_version=args.loader_version)
            print(f"Started {selected} {lv} on Minecraft {v.id} (PID {proc.pid})")
            return
    if v.source == "omniarchive":
        from .legacy import launch_legacy
        proc = launch_legacy(v, path)
    else:
        from .launcher import launch
        proc = launch(v, path, meta)
    print(f"Minecraft started (PID {proc.pid})")


def cmd_login(args):
    from .auth import login
    a = login(getattr(args,"alias",None))
    p = a["profile"]
    print(f'Logged in as {p.get("name")} ({p.get("id")})')

def cmd_account(args):
    from .auth import load_account, refresh, logout, list_accounts, use_account, remove_account
    action=args.account_action
    if action=="list":
        active,accounts=list_accounts()
        if not accounts:
            print("No Microsoft accounts saved.")
        for alias,a in accounts.items():
            p=a.get("profile",{})
            marker="*" if alias==active else " "
            print(f'{marker} {alias:18} {p.get("name","Unknown"):18} {p.get("id","")}')
    elif action=="show":
        a=load_account()
        if not a:
            print("No active Microsoft account.")
            return
        p=a.get("profile",{})
        print(f'{p.get("name","Unknown")}  {p.get("id","")}')
    elif action=="use":
        a=use_account(args.alias)
        print("Active account:",a.get("profile",{}).get("name",args.alias))
    elif action=="refresh":
        a=refresh(getattr(args,"alias",None))
        print("Refreshed:",a.get("profile",{}).get("name","Unknown"))
    elif action=="remove":
        a=remove_account(args.alias)
        print("Removed:",a.get("profile",{}).get("name",args.alias))
    elif action=="logout":
        logout()
        print("Active Microsoft account removed from MCLI.")

def cmd_java(args):
    from .java_manager import installed, install, detect_system, java_major, java_exe, RUNTIMES
    if args.java_action == "list":
        sysjava=detect_system()
        if sysjava:
            print(f"system  Java {java_major(sysjava) or '?'}  {sysjava}")
        for name,home,exe in installed():
            print(f"managed {name:12} {exe}")
    elif args.java_action == "install":
        home=install(args.major, force=args.force)
        print(f"Installed Java {args.major}: {java_exe(home)}")
    elif args.java_action == "path":
        target=RUNTIMES/f"java-{args.major}"
        exe=java_exe(target)
        if exe.exists(): print(exe)
        else: raise SystemExit(f"Managed Java {args.major} is not installed.")

def cmd_instance(args):
    from pathlib import Path
    from .instances import create, get, list_instances, delete, clone, set_value
    if args.instance_action == "create":
        obj=create(args.name,args.era,args.version,args.source)
        print(f'Created instance {obj["name"]}: {obj["era"]} {obj["version"]}')
        print(obj["path"])
    elif args.instance_action == "list":
        rows=list_instances()
        if not rows:
            print("No instances.")
        for x in rows:
            print(f'{x["name"]:20} {x["era"]:10} {x["version"]:20} {x["source"]}')
    elif args.instance_action == "info":
        print(json.dumps(get(args.name),indent=2))
    elif args.instance_action == "delete":
        delete(args.name,args.keep_files)
        print(f'Deleted instance {args.name}' + (" (files kept)" if args.keep_files else ""))
    elif args.instance_action == "clone":
        obj=clone(args.name,args.destination)
        print(f'Cloned {args.name} -> {obj["name"]}')
    elif args.instance_action == "set":
        obj=set_value(args.name,args.key,args.value)
        print(json.dumps(obj,indent=2))
    elif args.instance_action == "launch":
        obj=get(args.name)
        v, errors=resolve(obj["version"],obj["source"])
        if not v:
            raise SystemExit(f'Version not found: {obj["version"]}')
        path,meta=install(v)
        game_dir=Path(obj["path"])/"minecraft"
        if v.source=="omniarchive":
            from .legacy import launch_legacy
            proc=launch_legacy(v,path,game_dir)
        else:
            from .launcher import launch
            proc=launch(v,path,meta,game_dir)
        print(f'Minecraft started from instance {args.name} (PID {proc.pid})')

def cmd_loader(args):
    from .modloaders import install_loader
    result, version=install_loader(args.loader,args.minecraft,args.loader_version)
    print(f"Installed {args.loader} {version} for Minecraft {args.minecraft}")
    print(result)

def cmd_mods(args):
    from .modrinth import search, install_mod, remove_mod, list_mods
    if args.mods_action=="search":
        hits=search(args.query,"mod",args.limit,args.minecraft,args.loader)
        for h in hits:
            print(f'{h["project_id"]:10} {h["title"]} — {h.get("description","")}')
    elif args.mods_action=="install":
        paths=install_mod(args.project,args.instance,args.minecraft,args.loader,not args.no_deps)
        for p in paths: print("Installed",p.name)
    elif args.mods_action=="remove":
        hits=remove_mod(args.name,args.instance)
        for p in hits: print("Removed",p.name)
        if not hits: print("No matching installed mod.")
    elif args.mods_action=="list":
        for p in list_mods(args.instance): print(p.name)

def cmd_modpack(args):
    from .modrinth import search, install_modpack
    if args.modpack_action=="search":
        hits=search(args.query,"modpack",args.limit,args.minecraft,args.loader)
        for h in hits:
            print(f'{h["project_id"]:10} {h["title"]} — {h.get("description","")}')
    elif args.modpack_action=="install":
        idx=install_modpack(args.project,args.instance)
        print("Installed modpack:",idx.get("name","Modrinth pack"))
        print("Minecraft:",idx.get("dependencies",{}).get("minecraft","?"))

def cmd_server(args):
    from .servers import create, list_servers, start, stop, status, delete, accept_eula, properties
    a=args.server_action
    if a=="create":
        obj,_=create(args.name,args.version,args.kind,args.memory)
        print(f'Created {obj["kind"]} server {obj["name"]} ({obj["version"]})')
        print(obj["path"])
        print("EULA is NOT accepted automatically. After reading it, run:")
        print(f"  mcli server eula {obj['name']}")
    elif a=="list":
        for x in list_servers():
            try: _,running=status(x["name"])
            except Exception: running=False
            print(f'{"RUNNING" if running else "STOPPED":8} {x["name"]:18} {x["kind"]:8} {x["version"]}')
    elif a=="start":
        p=start(args.name,args.foreground); print(f"Started {args.name} (PID {p.pid})")
    elif a=="stop":
        print("Stopped." if stop(args.name) else "Server was not running.")
    elif a=="status":
        obj,running=status(args.name); print("RUNNING" if running else "STOPPED",obj.get("pid") or "")
    elif a=="eula":
        accept_eula(args.name); print("EULA marked accepted for",args.name)
    elif a=="delete":
        delete(args.name,args.keep_files); print("Deleted",args.name)
    elif a=="get":
        v=properties(args.name,args.key); print("" if v is None else v)
    elif a=="set":
        properties(args.name,args.key,args.value); print(f"{args.key}={args.value}")

def cmd_random(args):
    from .random_launch import launch_random
    v,proc,errors=launch_random(args.source,args.type,args.historical,args.dry_run)
    typ={"old_beta":"beta","old_alpha":"alpha"}.get(v.type,v.type)
    print(f"Random pick: {v.id} [{typ}] via {v.source}")
    if proc:
        print(f"Minecraft started (PID {proc.pid})")
    _print_source_warnings(errors)

def build_parser():







    p = argparse.ArgumentParser(prog="mcli", description="Minecraft Command-Line Launcher")
    sub = p.add_subparsers(dest="command", required=True)

    pr = sub.add_parser("random")
    pr.add_argument("--source", choices=["auto","mojang","omniarchive"], default="auto")
    pr.add_argument("--type", choices=ERA_TYPES)
    pr.add_argument("--historical", action="store_true")
    pr.add_argument("--dry-run", action="store_true")
    pr.set_defaults(func=cmd_random)


    psv=sub.add_parser("server")
    sv=psv.add_subparsers(dest="server_action",required=True)
    svc=sv.add_parser("create"); svc.add_argument("name"); svc.add_argument("version"); svc.add_argument("--kind",choices=["vanilla","paper"],default="vanilla"); svc.add_argument("--memory",default="2G"); svc.set_defaults(func=cmd_server)
    svl=sv.add_parser("list"); svl.set_defaults(func=cmd_server)
    svs=sv.add_parser("start"); svs.add_argument("name"); svs.add_argument("--foreground",action="store_true"); svs.set_defaults(func=cmd_server)
    svx=sv.add_parser("stop"); svx.add_argument("name"); svx.set_defaults(func=cmd_server)
    svt=sv.add_parser("status"); svt.add_argument("name"); svt.set_defaults(func=cmd_server)
    sve=sv.add_parser("eula"); sve.add_argument("name"); sve.set_defaults(func=cmd_server)
    svd=sv.add_parser("delete"); svd.add_argument("name"); svd.add_argument("--keep-files",action="store_true"); svd.set_defaults(func=cmd_server)
    svg=sv.add_parser("get"); svg.add_argument("name"); svg.add_argument("key"); svg.set_defaults(func=cmd_server)
    svp=sv.add_parser("set"); svp.add_argument("name"); svp.add_argument("key"); svp.add_argument("value"); svp.set_defaults(func=cmd_server)


    ps = sub.add_parser("search")
    ps.add_argument("query")
    ps.add_argument("--source", choices=["auto","mojang","omniarchive"], default="auto")
    ps.add_argument("--type", choices=ERA_TYPES)
    ps.add_argument("--limit", type=int, default=25)
    ps.set_defaults(func=cmd_search)

    pst = sub.add_parser("stats")
    pst.add_argument("--source", choices=["auto","mojang","omniarchive"], default="auto")
    pst.set_defaults(func=cmd_stats)


    pm = sub.add_parser("mods")
    ms = pm.add_subparsers(dest="mods_action", required=True)
    mss=ms.add_parser("search"); mss.add_argument("query"); mss.add_argument("--minecraft"); mss.add_argument("--loader"); mss.add_argument("--limit",type=int,default=10); mss.set_defaults(func=cmd_mods)
    msi=ms.add_parser("install"); msi.add_argument("project"); msi.add_argument("--instance",required=True); msi.add_argument("--minecraft"); msi.add_argument("--loader"); msi.add_argument("--no-deps",action="store_true"); msi.set_defaults(func=cmd_mods)
    msr=ms.add_parser("remove"); msr.add_argument("name"); msr.add_argument("--instance",required=True); msr.set_defaults(func=cmd_mods)
    msl=ms.add_parser("list"); msl.add_argument("--instance",required=True); msl.set_defaults(func=cmd_mods)

    pmp = sub.add_parser("modpack")
    mps=pmp.add_subparsers(dest="modpack_action",required=True)
    mpss=mps.add_parser("search"); mpss.add_argument("query"); mpss.add_argument("--minecraft"); mpss.add_argument("--loader"); mpss.add_argument("--limit",type=int,default=10); mpss.set_defaults(func=cmd_modpack)
    mpsi=mps.add_parser("install"); mpsi.add_argument("project"); mpsi.add_argument("--instance",required=True); mpsi.set_defaults(func=cmd_modpack)


    pld = sub.add_parser("loader")
    pld.add_argument("loader", choices=["fabric","forge","neoforge","quilt"])
    pld.add_argument("minecraft")
    pld.add_argument("--loader-version")
    pld.set_defaults(func=cmd_loader)


    pins = sub.add_parser("instance")
    ins = pins.add_subparsers(dest="instance_action", required=True)

    ic = ins.add_parser("create")
    ic.add_argument("name")
    ic.add_argument("era", choices=ERA_TYPES)
    ic.add_argument("version")
    ic.add_argument("--source", choices=["auto","mojang","omniarchive"], default="auto")
    ic.set_defaults(func=cmd_instance)

    il = ins.add_parser("list")
    il.set_defaults(func=cmd_instance)

    ii = ins.add_parser("info")
    ii.add_argument("name")
    ii.set_defaults(func=cmd_instance)

    ila = ins.add_parser("launch")
    ila.add_argument("name")
    ila.set_defaults(func=cmd_instance)

    ide = ins.add_parser("delete")
    ide.add_argument("name")
    ide.add_argument("--keep-files", action="store_true")
    ide.set_defaults(func=cmd_instance)

    icl = ins.add_parser("clone")
    icl.add_argument("name")
    icl.add_argument("destination")
    icl.set_defaults(func=cmd_instance)

    ise = ins.add_parser("set")
    ise.add_argument("name")
    ise.add_argument("key", choices=["version","era","source"])
    ise.add_argument("value")
    ise.set_defaults(func=cmd_instance)


    pj = sub.add_parser("java")
    pjsub = pj.add_subparsers(dest="java_action", required=True)
    pjl = pjsub.add_parser("list")
    pjl.set_defaults(func=cmd_java)
    pji = pjsub.add_parser("install")
    pji.add_argument("major", type=int, choices=[8, 17, 21, 25])
    pji.add_argument("--force", action="store_true")
    pji.set_defaults(func=cmd_java)
    pjp = pjsub.add_parser("path")
    pjp.add_argument("major", type=int, choices=[8, 17, 21, 25])
    pjp.set_defaults(func=cmd_java)


    pl = sub.add_parser("login")
    pl.add_argument("--alias")
    pl.set_defaults(func=cmd_login)

    pa = sub.add_parser("account")
    pas = pa.add_subparsers(dest="account_action")
    pal=pas.add_parser("list"); pal.set_defaults(func=cmd_account)
    pash=pas.add_parser("show"); pash.set_defaults(func=cmd_account)
    pau=pas.add_parser("use"); pau.add_argument("alias"); pau.set_defaults(func=cmd_account)
    par=pas.add_parser("refresh"); par.add_argument("--alias"); par.set_defaults(func=cmd_account)
    parm=pas.add_parser("remove"); parm.add_argument("alias"); parm.set_defaults(func=cmd_account)
    palo=pas.add_parser("logout"); palo.set_defaults(func=cmd_account)
    pa.set_defaults(func=cmd_account, account_action="show")


    pv = sub.add_parser("versions")
    pv.add_argument("--source", choices=["auto","mojang","omniarchive"], default="auto")
    pv.add_argument("--type", choices=ERA_TYPES)
    pv.add_argument("--historical", action="store_true")
    pv.add_argument("--query")
    pv.add_argument("--limit", type=int)
    pv.set_defaults(func=cmd_versions)

    pi = sub.add_parser("info")
    pi.add_argument("version")
    pi.add_argument("--source", choices=["auto","mojang","omniarchive"], default="auto")
    pi.set_defaults(func=cmd_info)

    for era in ERA_TYPES:
        pe = sub.add_parser(era)
        pe.add_argument("version")
        pe.add_argument("--source", choices=["auto","mojang","omniarchive"], default="auto")
        group=pe.add_mutually_exclusive_group()
        group.add_argument("--fabric", action="store_true")
        group.add_argument("--forge", action="store_true")
        group.add_argument("--neoforge", action="store_true")
        group.add_argument("--quilt", action="store_true")
        pe.add_argument("--loader-version")
        pe.set_defaults(func=cmd_launch, era=era)

    return p

def main():
    args = build_parser().parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
