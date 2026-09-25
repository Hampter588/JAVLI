# Mods, modloaders and content

javli supports Fabric, Quilt, Forge and NeoForge.

## Persistent instance loaders

```bash
javli instance create survival release 1.21.1 --loader fabric
javli instance launch survival
javli instance set survival loader fabric
javli instance set survival loader_version 0.18.4
```

## Modrinth

Modrinth is the default provider.

```bash
javli mods search sodium --minecraft 1.21.1 --loader fabric
javli mods install sodium --instance survival --loader fabric
javli mods list --instance survival
javli modpack search "fabulously optimized"
javli modpack install fabulously-optimized --instance survival
```

## CurseForge

```bash
javli mods search jei --minecraft 1.21.1 --loader neoforge --provider curseforge
javli mods install <project-id-or-slug> --instance survival --provider curseforge
```

Official javli builds can include JAVBED's CurseForge API credential at build time, so users do not need to configure a key when it is present. Source/custom builds can set `CURSEFORGE_API_KEY`.

Windows CMD:

```bat
setx CURSEFORGE_API_KEY "YOUR_KEY_HERE"
```

Open a new terminal afterward. CurseForge filtering supports Forge, Fabric, Quilt and NeoForge. Required dependencies are installed recursively. If a project does not expose a third-party download URL, javli reports that instead of bypassing the restriction.
