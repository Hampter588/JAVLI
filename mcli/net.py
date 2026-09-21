import hashlib, requests
from pathlib import Path

UA = "mcli/1.0 (+Minecraft launcher)"

def get_json(url, timeout=20):
    r = requests.get(url, timeout=timeout, headers={"User-Agent": UA})
    r.raise_for_status()
    return r.json()

def download(url, dest: Path, sha1=None):
    dest.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, stream=True, timeout=60, headers={"User-Agent": UA}) as r:
        r.raise_for_status()
        h = hashlib.sha1()
        with dest.open("wb") as f:
            for chunk in r.iter_content(1024 * 1024):
                if chunk:
                    f.write(chunk)
                    h.update(chunk)
    if sha1 and h.hexdigest().lower() != sha1.lower():
        dest.unlink(missing_ok=True)
        raise RuntimeError("SHA-1 verification failed")
    return dest
