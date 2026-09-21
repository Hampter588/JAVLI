import re
from urllib.parse import urljoin, urlparse, unquote
import requests
from .base import Source
from ..model import Version

BASE = "https://omniarchive.net/archive/java/client/"
UA = "mcli/0.4 (+Minecraft launcher)"
ERA_WORDS = ("pre-classic","preclassic","classic","indev","infdev","alpha","beta","release","snapshot","april-fools")

class OmniarchiveSource(Source):
    name = "omniarchive"

    def _links(self, url):
        r = requests.get(url, timeout=30, headers={"User-Agent": UA})
        r.raise_for_status()
        return re.findall(r'href=["\']([^"\']+)["\']', r.text, flags=re.I)

    def _era(self, url):
        low = unquote(url).lower()
        for era in ERA_WORDS:
            if f"/{era}/" in low:
                return "preclassic" if era == "pre-classic" else era.replace("-", "_")
        return "archived"

    def _crawl(self, url, depth=0, max_depth=6, seen=None):
        seen = seen or set()
        if url in seen or depth > max_depth:
            return []
        seen.add(url)
        out=[]
        base_host=urlparse(BASE).netloc
        for href in self._links(url):
            if href in ("../","./","/") or href.startswith(("?","#")):
                continue
            full=urljoin(url,href)
            parsed=urlparse(full)
            if parsed.netloc != base_host or not parsed.path.startswith(urlparse(BASE).path):
                continue
            if href.endswith("/"):
                out.extend(self._crawl(full, depth+1, max_depth, seen))
            elif parsed.path.lower().endswith(".jar"):
                filename=unquote(parsed.path.rsplit("/",1)[-1])
                vid=filename[:-4]
                era=self._era(full)
                out.append(Version(
                    id=vid, type=era, source=self.name, url=full,
                    raw={"id":vid,"type":era,"downloads":{"client":{"url":full}}}
                ))
        return out

    def versions(self):
        vals=self._crawl(BASE)
        unique={}
        for v in vals:
            unique.setdefault(v.id,v)
        return list(unique.values())

    def details(self, version):
        return version.raw
