# Roadmap

## Phase 0 — foundation ✅
- [x] Monorepo, install paths for Arch-based / Debian-based / others
- [x] `rig-diagnose`: hardware inventory + support report
- [x] `rig-profiles`: CPU EPP/governor + NVIDIA power-limit profiles
- [x] Reference-rig documentation, capture guide, udev rules

## Phase 1 — captures
- [ ] NZXT CAM ↔ `1e71:2023` (fan channels, pump header, every RGB mode)
- [ ] MasterCTRL ↔ `2516:0232` (pump modes, display pages, ARGB)
- [ ] Chassis suite ↔ `ff00:020c` (every animation incl. hourglass, clock sync)
- [ ] Identify what `26ce:0a09` (audio-class composite) actually is
- [ ] Zotac Firestorm/Spectra ↔ RTX 5060 Ti RGB

## Phase 2 — drivers
- [ ] `nzxt-n9`: read fan RPMs → set fixed duty → curves → RGB modes
  - The Hue 2 / Smart Device V2 starting hypothesis is refuted. PID `2023` is
    its own protocol generation: 512-byte reports, `26 04` plus a `26 06`
    commit for Fixed, one `2a 04` config frame per action for the
    firmware-rendered animated modes, and `26 14` host streaming for the
    audio modes. See [ESTADO-Y-RUTA.md](ESTADO-Y-RUTA.md) and
    [NZXT-N9-CAM-LIGHTING.md](NZXT-N9-CAM-LIGHTING.md).
  - Lighting is decoded and partly replayed from Linux under closed write
    labs. Nothing about fan channels, pump or curves has been captured yet,
    so the fan half of this item has not started.
- [ ] `cm-nex-digital`: pump duty, display content (temp source), ARGB
- [ ] `chassis-ledmatrix`: effect select, speed, color, clock/hourglass sync
- [ ] Daemon-friendly CLI output (JSON) so CoolerControl/GUIs can wrap us

## Phase 3 — give it back
- [ ] Upstream NZXT + Cooler Master protocols to **liquidctl**
- [ ] Kernel hwmon drivers via **liquidtux** (fan RPM in `sensors`, fancurves
  in BIOS-independent userspace like `fancontrol`/CoolerControl)
- [ ] Evision `320f:5000` + Zotac RTX 50 RGB to **OpenRGB**
- [ ] AUR packages, Debian PPA or repo, Fedora COPR, openSUSE OBS

## Non-goals
- Reimplementing OpenRGB/liquidctl for devices they already support.
- A GUI (CoolerControl and OpenRGB already exist; we feed them).
