# Builds and releases

GitHub Actions builds javli after every pushed commit and can also be run manually.

Targets: Windows x64/x86, Linux x64/x86, macOS Intel/Apple Silicon.

Each successful workflow uploads Actions artifacts and creates a GitHub Release tagged with the workflow build number and short commit SHA containing all six packaged binaries.

## CurseForge-enabled official builds

Official builds can inject the `CURSEFORGE_API_KEY` GitHub Actions secret into a temporary `mcli/_build_secrets.py` before PyInstaller runs. The generated file is ignored by Git. A runtime `CURSEFORGE_API_KEY` overrides the built-in value.

The Linux 32-bit target builds inside an i386 Debian container and performs the same injection there. Release publishing requires `contents: write` workflow permission.
