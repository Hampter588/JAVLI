import random
from .catalog import all_versions
from .install import install

class RandomLaunchError(RuntimeError): pass

def candidates(source="auto", era=None, historical=False):
    vals,errors=all_versions(source)
    def typ(v):
        return {"old_beta":"beta","old_alpha":"alpha","pre-classic":"preclassic"}.get(v.type,v.type)
    out=[]
    for v in vals:
        t=typ(v)
        if era and t!=era: continue
        if historical and t in ("release","snapshot"): continue
        out.append(v)
    return out,errors

def choose(source="auto",era=None,historical=False):
    vals,errors=candidates(source,era,historical)
    if not vals:
        raise RandomLaunchError("No versions matched the random selection filters.")
    return random.SystemRandom().choice(vals),errors

def launch_random(source="auto",era=None,historical=False,dry_run=False):
    v,errors=choose(source,era,historical)
    if dry_run:
        return v,None,errors
    path,meta=install(v)
    if v.source=="omniarchive":
        from .legacy import launch_legacy
        proc=launch_legacy(v,path)
    else:
        from .launcher import launch
        proc=launch(v,path,meta)
    return v,proc,errors
