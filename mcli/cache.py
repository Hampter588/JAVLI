from pathlib import Path
import json, time

ROOT = Path.home() / ".mcli"
CACHE = ROOT / "cache"
VERSIONS = ROOT / "versions"

def ensure():
    CACHE.mkdir(parents=True, exist_ok=True)
    VERSIONS.mkdir(parents=True, exist_ok=True)

def load_json(name, max_age=3600):
    ensure()
    p = CACHE / name
    if not p.exists() or time.time() - p.stat().st_mtime > max_age:
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None

def save_json(name, obj):
    ensure()
    (CACHE / name).write_text(json.dumps(obj, indent=2), encoding="utf-8")
