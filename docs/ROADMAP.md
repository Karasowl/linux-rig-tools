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
  - First experiment: liquidctl's Smart Device V2 / Hue 2 protocol family
    against PID `2023` (note: 512-byte reports vs Hue 2's 64 suggests a new
    protocol generation)
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
