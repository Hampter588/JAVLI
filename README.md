# mcli
# ALERT MCLI HAS ONLY BEEN  TESTED ON WINDOWS 64 IT MAY NOT WORK AS EXPECTED PLEASE REPORT IISSUES
**The Minecraft Command-Line Launcher**

MCLI brings modern Minecraft, historical builds, Microsoft accounts, Java runtimes, instances, modloaders, mods and servers under one command-line interface.

```console
$ mcli release 1.21.1
$ mcli beta b1.7.3
$ mcli classic c0.30
```

## Install

Requires Python 3.10+.

```bash
python -m pip install -e .
mcli login
mcli release 1.21.1
```

## Sources

- **Mojang** — official version metadata, clients, libraries, assets and server artifacts.
- **Omniarchive** — direct historical Java client discovery for preserved Minecraft builds.

## Versions

```bash
mcli versions
mcli versions --historical
mcli versions --source omniarchive
mcli versions --type beta
mcli search "1.7"
mcli info 1.21.1
mcli stats
```

## Microsoft accounts

```bash
mcli login --alias main
mcli login --alias alt
mcli account list
mcli account use main
mcli account refresh
mcli account remove alt
```

## Java

```bash
mcli java list
mcli java install 8
mcli java install 17
mcli java install 21
```

MCLI can select a managed Java runtime based on Minecraft metadata.

## Instances

```bash
mcli instance create survival release 1.21.1
mcli instance launch survival
mcli instance list
mcli instance clone survival survival-copy
```

Instances isolate saves, settings, configs, mods, resource packs and screenshots.

## Modloaders

```bash
mcli release 1.21.1 --fabric
mcli release 1.21.1 --quilt
mcli release 1.20.1 --forge
mcli release 1.21.1 --neoforge
```

## Modrinth

```bash
mcli mods search sodium --minecraft 1.21.1 --loader fabric
mcli mods install sodium --instance survival --loader fabric
mcli mods list --instance survival

mcli modpack search "fabulously optimized"
mcli modpack install fabulously-optimized --instance survival
```

## Servers

```bash
mcli server create smp 1.21.1
mcli server create paper-smp 1.21.1 --kind paper --memory 4G
mcli server eula smp
mcli server start smp
mcli server status smp
mcli server stop smp
```

MCLI does not accept Mojang's EULA automatically.

## Random Minecraft

```bash
mcli random
mcli random --historical
mcli random --source omniarchive
mcli random --type beta
mcli random --dry-run
```

## Data

Managed data lives under `~/.mcli/`:

```text
accounts.json
assets/
cache/
instances/
libraries/
loaders/
runtimes/
servers/
versions/
```

Treat `accounts.json` as sensitive because it may contain authentication refresh tokens.

## Project status

MCLI 1.0 contains the major launcher architecture and feature set, but should still be treated as an early project until launch paths have been extensively tested across Minecraft versions, operating systems, Java runtimes and modloader combinations. Historical builds can require version-specific compatibility work.

## Roadmap

- CurseForge integration
- mod updates and compatibility management
- import Prism/MultiMC/existing `.minecraft` instances
- download progress, retries and resume
- crash diagnostics and `mcli doctor`
- server console and backups
- stronger historical compatibility profiles
- packaged Windows/macOS/Linux releases

## Disclaimer

MCLI is an independent project and is not affiliated with, endorsed by, or sponsored by Mojang Studios or Microsoft. Minecraft is a trademark of Microsoft Corporation.


## Standalone binaries

MCLI's GitHub Actions workflow builds standalone executables for the six primary desktop OS/architecture targets:

- Windows x64
- Windows ARM64
- Linux x64
- Linux ARM64
- macOS Intel (x86_64)
- macOS Apple Silicon (ARM64)

Run **Build MCLI binaries** manually from GitHub Actions, or push a version tag such as `v1.0.1`.
Tagged builds are also attached to the GitHub Release.

The packaged MCLI executable includes Python and its Python dependencies; users do not need to install Python.
Minecraft's required Java runtimes continue to be managed separately by MCLI.


## Linux distribution packages

Release automation now includes native packaging paths for:

- Debian / Ubuntu: `.deb` for amd64 and arm64
- Fedora / RHEL-family: `.rpm` for x86_64 and aarch64
- Arch Linux: x86_64 and aarch64 package artifacts plus `packaging/arch/PKGBUILD`
- Nix / NixOS: `flake.nix` for x86_64-linux, aarch64-linux, x86_64-darwin and aarch64-darwin
- Generic Linux: standalone x64 and ARM64 tarballs from the binary workflow

Nix users can build the project with:

```bash
nix build
nix run
```

The Arch `PKGBUILD` contains a repository placeholder (`OWNER/REPO`) that should be replaced when the public GitHub repository is chosen.


## Unified manual build workflow

All release builds now live in one workflow:

`.github/workflows/build-all.yml`

It runs **only** from GitHub's **Run workflow** button (`workflow_dispatch`). Enter the version number and GitHub builds the platform matrix.

In addition to Windows, macOS, generic Linux, Debian/Ubuntu, Fedora/RHEL, Arch and Nix/NixOS, the matrix includes distro-native builds for Debian 13, Ubuntu 24.04, Fedora, Rocky Linux 9, openSUSE Tumbleweed and Alpine Linux.

The distro-specific tarballs are useful when libc/runtime compatibility matters; the `.deb`, `.rpm`, Nix and generic standalone artifacts remain the normal distribution choices.


## BSD builds

The manual release workflow also attempts native VM builds for:

- FreeBSD x86_64
- OpenBSD x86_64
- NetBSD x86_64

These run inside BSD virtual machines rather than Linux containers so the resulting executable is built against the target BSD userspace. BSD support should be considered experimental until each artifact is launch-tested on its target OS; Python/PyInstaller support can vary by BSD and release.


## Extended architecture matrix

The manual build workflow also contains experimental jobs for the long-tail architecture matrix:

- Windows x86 (32-bit)
- Linux x86 (32-bit)
- Linux ARMv7
- Linux RISC-V 64 (`riscv64`)
- Linux PowerPC 64 little-endian (`ppc64le`)
- Linux IBM Z (`s390x`)
- FreeBSD ARM64
- OpenBSD ARM64
- NetBSD ARM64

These are intentionally labeled **experimental**. The workflow uses native/VM builds where practical and QEMU containers for exotic Linux architectures. A successful MCLI binary build proves the CLI can be packaged for that target; it does **not** prove every Minecraft generation will launch there. Minecraft/LWJGL native availability, graphics drivers and Java runtime availability remain target-specific constraints.
