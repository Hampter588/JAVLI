# javli
# ALERT javli HAS ONLY BEEN  TESTED ON WINDOWS 64 IT MAY NOT WORK AS EXPECTED PLEASE REPORT IISSUES
**The Minecraft Command-Line Launcher**

javli brings modern Minecraft, historical builds, Microsoft accounts, Java runtimes, instances, modloaders, mods and servers under one command-line interface.

```console
$ javli release 1.21.1
$ javli beta b1.7.3
$ javli classic c0.30
```

## Install

Requires Python 3.10+.

```bash
python -m pip install -e .
javli login
javli release 1.21.1
```

## Sources

- **Mojang** — official version metadata, clients, libraries, assets and server artifacts.
- **Omniarchive** — direct historical Java client discovery for preserved Minecraft builds.

## Versions

```bash
javli versions
javli versions --historical
javli versions --source omniarchive
javli versions --type beta
javli search "1.7"
javli info 1.21.1
javli stats
```

## Microsoft accounts

```bash
javli login --alias main
javli login --alias alt
javli account list
javli account use main
javli account refresh
javli account remove alt
```

## Java

```bash
javli java list
javli java install 8
javli java install 17
javli java install 21
```

javli can select a managed Java runtime based on Minecraft metadata.

## Instances

```bash
javli instance create survival release 1.21.1
javli instance launch survival
javli instance list
javli instance clone survival survival-copy
```

Instances isolate saves, settings, configs, mods, resource packs and screenshots.

## Modloaders

```bash
javli release 1.21.1 --fabric
javli release 1.21.1 --quilt
javli release 1.20.1 --forge
javli release 1.21.1 --neoforge
```

## Modrinth

```bash
javli mods search sodium --minecraft 1.21.1 --loader fabric
javli mods install sodium --instance survival --loader fabric
javli mods list --instance survival

javli modpack search "fabulously optimized"
javli modpack install fabulously-optimized --instance survival
```

## Servers

```bash
javli server create smp 1.21.1
javli server create paper-smp 1.21.1 --kind paper --memory 4G
javli server eula smp
javli server start smp
javli server status smp
javli server stop smp
```

javli does not accept Mojang's EULA automatically.

## Random Minecraft

```bash
javli random
javli random --historical
javli random --source omniarchive
javli random --type beta
javli random --dry-run
```

## Data

Managed data lives under `~/.javli/`:

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

javli 1.0 contains the major launcher architecture and feature set, but should still be treated as an early project until launch paths have been extensively tested across Minecraft versions, operating systems, Java runtimes and modloader combinations. Historical builds can require version-specific compatibility work.

## Roadmap

- CurseForge integration
- mod updates and compatibility management
- import Prism/MultiMC/existing `.minecraft` instances
- download progress, retries and resume
- crash diagnostics and `javli doctor`
- server console and backups
- stronger historical compatibility profiles
- packaged Windows/macOS/Linux releases

## Disclaimer

javli is an independent project and is not affiliated with, endorsed by, or sponsored by Mojang Studios or Microsoft. Minecraft is a trademark of Microsoft Corporation.


## Standalone binaries

javli's GitHub Actions workflow builds standalone executables for the six primary desktop OS/architecture targets:

- Windows x64
- Windows ARM64
- Linux x64
- Linux ARM64
- macOS Intel (x86_64)
- macOS Apple Silicon (ARM64)

Run **Build javli binaries** manually from GitHub Actions, or push a version tag such as `v1.0.1`.
Tagged builds are also attached to the GitHub Release.

The packaged javli executable includes Python and its Python dependencies; users do not need to install Python.
Minecraft's required Java runtimes continue to be managed separately by javli.


