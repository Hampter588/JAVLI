from .sources.mojang import MojangSource
from .sources.omniarchive import OmniarchiveSource

def sources(which="auto"):
    if which == "mojang":
        return [MojangSource()]
    if which == "omniarchive":
        return [OmniarchiveSource()]
    return [MojangSource(), OmniarchiveSource()]

def all_versions(which="auto"):
    merged = {}
    errors = []
    for src in sources(which):
        try:
            for v in src.versions():
                # auto mode intentionally gives Mojang precedence
                merged.setdefault(v.id, v)
        except Exception as e:
            errors.append(f"{src.name}: {e}")
    return list(merged.values()), errors

def resolve(version_id, which="auto"):
    versions, errors = all_versions(which)
    for v in versions:
        if v.id == version_id:
            return v, errors
    return None, errors
