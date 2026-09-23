# Launching Minecraft

```bash
javli release 26.1.2
javli beta b1.7.3
javli alpha <version>
javli infdev <version>
javli indev <version>
javli classic <version>
javli preclassic <version>
```

javli resolves the version, downloads required libraries/assets, selects Java, and starts Minecraft.

Asset downloads use 32 concurrent workers and are cached under `~/.javli/assets`.

Default memory: Pre-Classic/Classic/Indev/Infdev 256 MB; Alpha/Beta 512 MB; Release/Snapshot 2 GB.
