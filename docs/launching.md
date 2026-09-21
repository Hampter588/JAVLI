# Launching Minecraft

```bash
mcli release 26.1.2
mcli beta b1.7.3
mcli alpha <version>
mcli infdev <version>
mcli indev <version>
mcli classic <version>
mcli preclassic <version>
```

MCLI resolves the version, downloads required libraries/assets, selects Java, and starts Minecraft.

Asset downloads use 32 concurrent workers and are cached under `~/.mcli/assets`.

Default memory: Pre-Classic/Classic/Indev/Infdev 256 MB; Alpha/Beta 512 MB; Release/Snapshot 2 GB.
