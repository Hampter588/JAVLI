from PyInstaller.__main__ import run
import os, platform, shutil
from pathlib import Path

root = Path(__file__).resolve().parents[1]
dist = root / "dist"
build = root / "build"
spec = root / "mcli.spec"

for p in (dist, build):
    shutil.rmtree(p, ignore_errors=True)
if spec.exists():
    spec.unlink()

# Freeze the package entry point as a module-aware bootstrap.
# Running mcli/__main__.py directly breaks relative imports because PyInstaller
# executes it as top-level __main__ with no package parent.
bootstrap = root / "mcli_pyinstaller_entry.py"
bootstrap.write_text(
    "from mcli.cli import main\n"
    "if __name__ == '__main__':\n"
    "    main()\n",
    encoding="utf-8",
)

args = [
    str(bootstrap),
    "--name=javli",
    "--onefile",
    "--clean",
    "--noconfirm",
    f"--distpath={dist}",
    f"--workpath={build}",
    f"--specpath={root}",
    "--collect-submodules=mcli",
]
try:
    run(args)
finally:
    bootstrap.unlink(missing_ok=True)

exe = dist / ("javli.exe" if os.name == "nt" else "javli")
if not exe.exists():
    raise SystemExit(f"Expected binary not found: {exe}")

print(f"Built {exe}")
print(f"Platform: {platform.system()} {platform.machine()}")
