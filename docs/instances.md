# Instances

```bash
javli instance create survival release 26.1.2
javli instance launch survival
javli instance list
javli instance info survival
javli instance clone survival survival-copy
javli instance delete survival-copy
```

## Persistent modloaders

Instances can remember Fabric, Quilt, Forge or NeoForge and automatically use that loader on launch.

```bash
javli instance create survival release 1.21.1 --loader fabric
javli instance set survival loader fabric
javli instance set survival loader_version 0.18.4
javli instance launch survival
```

`instance list` shows the configured loader. Modloaders require Mojang-backed versions.
