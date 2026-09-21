from pathlib import Path
from .catalog import sources
from .cache import VERSIONS, ensure
from .net import download

def install(version):
    ensure()
    src = next(s for s in sources(version.source) if s.name == version.source)
    meta = src.details(version)
    client = (meta.get("downloads") or {}).get("client") or {}
    url = client.get("url") or meta.get("client_url") or version.url
    sha1 = client.get("sha1") or meta.get("client_sha1")
    if not url:
        raise RuntimeError(
            f"{version.source} metadata for {version.id} does not provide a client download URL."
        )
    dest = VERSIONS / version.id / f"{version.id}.jar"
    download(url, dest, sha1)
    return dest, meta
