# mcli

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
