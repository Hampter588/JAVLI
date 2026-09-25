import json, os, platform, shutil, stat, sys, tarfile, tempfile, zipfile
from pathlib import Path
import requests

REPO="JAVBED/javli"
API=f"https://api.github.com/repos/{REPO}/releases/latest"
UA="JAVLI/1.0 (https://github.com/JAVBED/javli)"

class UpdateError(RuntimeError):
    pass

def _target():
    system=platform.system()
    machine=platform.machine().lower()
    bits=64 if sys.maxsize > 2**32 else 32

    if system=="Windows":
        return "javli-windows-x64.zip" if bits==64 else "javli-windows-x86.zip", "javli.exe"
    if system=="Linux":
        return "javli-linux-x64.tar.gz" if bits==64 else "javli-linux-x86.tar.gz", "javli"
    if system=="Darwin":
        if machine in ("arm64","aarch64"):
            return "javli-macos-arm64.tar.gz", "javli"
        return "javli-macos-intel.tar.gz", "javli"
    raise UpdateError(f"Automatic update is not supported on {system} {machine}.")

def _latest_release():
    r=requests.get(API,headers={"User-Agent":UA,"Accept":"application/vnd.github+json"},timeout=30)
    r.raise_for_status()
    return r.json()

def _extract(archive, dest):
    name=archive.name.lower()
    if name.endswith(".zip"):
        with zipfile.ZipFile(archive) as z: z.extractall(dest)
    elif name.endswith(".tar.gz"):
        with tarfile.open(archive,"r:gz") as t: t.extractall(dest)
    else:
        raise UpdateError("Unknown JAVLI release archive format.")

def _current_release_tag():
    # Official manual releases are named manual-<run>. Use the embedded build
    # marker when available; otherwise fall back to executable mtime.
    try:
        from ._build_info import RELEASE_TAG
        return RELEASE_TAG
    except Exception:
        return os.getenv("JAVLI_RELEASE_TAG","")

def prompt_if_update_available():
    if not getattr(sys,"frozen",False) or not sys.stdin.isatty():
        return False
    try:
        release=release or _latest_release()
        latest=release.get("tag_name","")
        current=_current_release_tag()
        if not latest or latest==current:
            return False
        # If no build tag is embedded (older binary), offer the latest release once.
        print("\n+------------------------------------------+")
        print("|           javli update available         |")
        print("+------------------------------------------+")
        if current:
            print(f"  Current: {current}")
        print(f"  Latest:  {latest}")
        print("\n  [1] Yes, update now")
        print("  [2] No, continue")
        while True:
            choice=input("\nChoose 1 or 2: ").strip().lower()
            if choice in ("1","y","yes"):
                update(release=release)
                return True
            if choice in ("2","n","no",""):
                return False
            print("Please choose 1 or 2.")
    except (requests.RequestException, OSError, UpdateError):
        return False

def update(silent=False, release=None):
    if getattr(sys,"frozen",False):
        current=Path(sys.executable).resolve()
    else:
        raise UpdateError("mcli update is for standalone release binaries. Source installs should update with git/pip.")

    asset_name,binary_name=_target()
    release=_latest_release()
    assets={a["name"]:a for a in release.get("assets",[])}
    asset=assets.get(asset_name)
    if not asset:
        available=", ".join(sorted(assets)) or "none"
        raise UpdateError(f"Release {release.get('tag_name','?')} has no {asset_name}. Available: {available}")

    if not silent:
        print(f"Latest release: {release.get('name') or release.get('tag_name')}")
        print(f"Downloading {asset_name}...")

    with tempfile.TemporaryDirectory(prefix="javli-update-") as td:
        td=Path(td)
        archive=td/asset_name
        with requests.get(asset["browser_download_url"],headers={"User-Agent":UA},stream=True,timeout=120) as r:
            r.raise_for_status()
            with archive.open("wb") as f:
                for chunk in r.iter_content(1024*1024):
                    if chunk: f.write(chunk)
        unpack=td/"unpack"; unpack.mkdir()
        _extract(archive,unpack)
        candidates=list(unpack.rglob(binary_name))
        if not candidates:
            raise UpdateError(f"{binary_name} was not found inside {asset_name}.")
        new=candidates[0]

        if os.name=="nt":
            # Windows cannot overwrite the running executable. A detached batch
            # waits for this process to exit, swaps the file, then removes itself.
            replacement=current.with_name(current.name+".new")
            shutil.copy2(new,replacement)
            bat=td/"javli-update.cmd"
            bat.write_text(
                "@echo off\r\n"
                "timeout /t 2 /nobreak >nul\r\n"
                f'move /Y "{replacement}" "{current}" >nul\r\n'
                f'echo JAVLI updated to {release.get("tag_name","latest")}\r\n'
                'del "%~f0"\r\n',
                encoding="utf-8",
            )
            import subprocess
            subprocess.Popen(["cmd","/c",str(bat)],creationflags=subprocess.CREATE_NEW_PROCESS_GROUP|subprocess.DETACHED_PROCESS)
            print("Update downloaded. JAVLI will replace itself after this command exits.")
        else:
            mode=current.stat().st_mode
            staged=current.with_name(current.name+".new")
            shutil.copy2(new,staged)
            staged.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
            os.replace(staged,current)
            print(f"JAVLI updated to {release.get('tag_name','latest')}.")

