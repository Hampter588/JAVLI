from .base import Source
from ..model import Version
from ..net import get_json
from ..cache import load_json, save_json

MANIFEST = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"

class MojangSource(Source):
    name = "mojang"

    def manifest(self):
        cached = load_json("mojang-manifest.json")
        if cached:
            return cached
        data = get_json(MANIFEST)
        save_json("mojang-manifest.json", data)
        return data

    def versions(self):
        out = []
        for x in self.manifest().get("versions", []):
            out.append(Version(
                id=x["id"], type=x.get("type", "unknown"), source=self.name,
                url=x.get("url"), release_time=x.get("releaseTime"),
                sha1=x.get("sha1"), raw=x
            ))
        return out

    def details(self, version):
        if not version.url:
            return version.raw
        key = "mojang-version-" + version.id.replace("/", "_") + ".json"
        cached = load_json(key, max_age=86400 * 30)
        if cached:
            return cached
        data = get_json(version.url)
        save_json(key, data)
        return data
