import re
from collections import Counter
from .catalog import all_versions, resolve
from .sources.mojang import MojangSource
from .sources.omniarchive import OmniarchiveSource

def norm_type(t):
    return {"old_beta":"beta","old_alpha":"alpha","pre-classic":"preclassic"}.get(t,t or "unknown")

def versions(source="auto", era=None, historical=False, query=None):
    vals,errors=all_versions(source)
    out=[]
    for v in vals:
        typ=norm_type(v.type)
        if historical and typ in ("release","snapshot"):
            continue
        if era and typ != era:
            continue
        if query and query.lower() not in v.id.lower():
            continue
        out.append(v)
    out.sort(key=lambda v:(v.release_time or "",v.id),reverse=True)
    return out,errors

def search_versions(query, source="auto", era=None):
    vals,errors=versions(source,era,False,query)
    # Better relevance than pure date: exact, prefix, substring, then recency.
    q=query.lower()
    vals.sort(key=lambda v:(
        v.id.lower()==q,
        v.id.lower().startswith(q),
        q in v.id.lower(),
        v.release_time or ""
    ),reverse=True)
    return vals,errors

def info(version_id, source="auto"):
    v,errors=resolve(version_id,source)
    if not v: return None,errors
    src = MojangSource() if v.source=="mojang" else OmniarchiveSource()
    meta=src.details(v)
    return {
        "id":v.id,
        "type":norm_type(v.type),
        "source":v.source,
        "release_time":v.release_time,
        "metadata_url":v.url,
        "java":(meta.get("javaVersion") or {}).get("majorVersion"),
        "main_class":meta.get("mainClass"),
        "asset_index":(meta.get("assetIndex") or {}).get("id") or meta.get("assets"),
        "library_count":len(meta.get("libraries",[])),
        "downloads":list((meta.get("downloads") or {}).keys()),
    },errors

def stats(source="auto"):
    vals,errors=all_versions(source)
    by_source=Counter(v.source for v in vals)
    by_type=Counter(norm_type(v.type) for v in vals)
    return {"total":len(vals),"by_source":dict(by_source),"by_type":dict(by_type)},errors
