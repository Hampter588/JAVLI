import re
from urllib.parse import urljoin, urlparse, unquote
import requests
from .base import Source
from ..model import Version

BASE = "https://vault.omniarchive.uk/archive/java/index.html"
ROOT = "https://vault.omniarchive.uk/archive/java/"
UA = "mcli/1.0 (+Minecraft launcher)"

# Vault uses client-<era>/ directories. Some eras (notably beta/release)
# contain nested version directories, so we recurse only inside the selected
# official client trees.
ERA_PATHS = {
    "preclassic": "client-preclassic/",
    "classic": "client-classic/",
    "indev": "client-indev/",
    "infdev": "client-infdev/",
    "alpha": "client-alpha/",
    "beta": "client-beta/",
    "release": "client-release/",
    "april_fools": "client-april-fools/",
}

class OmniarchiveSource(Source):
    name = "omniarchive"

    def _links(self, url):
        r=requests.get(url,timeout=30,headers={"User-Agent":UA})
        r.raise_for_status()
        return re.findall(r'href=["\\\']([^"\\\']+)["\\\']',r.text,flags=re.I)

    def _crawl_era(self, era, url, depth=0, seen=None):
        seen=seen or set()
        if url in seen or depth>8:
            return []
        seen.add(url)
        out=[]
        root_path=urlparse(ROOT).path
        host=urlparse(ROOT).netloc

        for href in self._links(url):
            if href in ("../","./","/") or href.startswith(("?","#")):
                continue
            full=urljoin(url,href)
            parsed=urlparse(full)
            if parsed.netloc != host or not parsed.path.startswith(root_path):
                continue

            if parsed.path.lower().endswith(".jar"):
                filename=unquote(parsed.path.rsplit("/",1)[-1])
                vid=filename[:-4]
                # Pre-classic vault files are named *-launcher.jar. Keep the
                # archive's actual ID useful at the CLI by removing that suffix.
                if era=="preclassic" and vid.endswith("-launcher"):
                    vid=vid[:-9]
                out.append(Version(
                    id=vid,
                    type=era,
                    source=self.name,
                    url=full,
                    raw={
                        "id":vid,
                        "type":era,
                        "downloads":{"client":{"url":full}},
                        "omniarchive_url":full,
                    },
                ))
            elif href.endswith("/") or parsed.path.endswith("/"):
                out.extend(self._crawl_era(era,full,depth+1,seen))
        return out

    def versions(self):
        vals=[]
        errors=[]
        for era,path in ERA_PATHS.items():
            try:
                vals.extend(self._crawl_era(era,urljoin(ROOT,path)))
            except Exception as e:
                errors.append((era,e))

        unique={}
        for v in vals:
            # Same ID can occasionally exist in multiple archive locations;
            # prefer the first canonical client entry.
            unique.setdefault(v.id,v)

        if not unique and errors:
            detail="; ".join(f"{era}: {err}" for era,err in errors)
            raise RuntimeError("Omniarchive Vault discovery failed: "+detail)
        return list(unique.values())

    def details(self, version):
        return version.raw
