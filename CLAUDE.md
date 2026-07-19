# CLAUDE.md

Context for AI coding agents working in this repo.

## What this is

Monorepo of **small, independent Linux tools** for PC hardware that is only
manageable from Windows vendor apps (fan curves, pump control, RGB,
LED-matrix displays). Each tool is standalone and individually installable.
Full project vision: [README.md](README.md) · plan: [docs/ROADMAP.md](docs/ROADMAP.md).

## Current state (2026-07)

- ✅ Working: `rig-diagnose`, `rig-profiles` — plain bash at
  `tools/<name>/bin/<name>`, tested on the reference rig.
- 🔬 Reverse engineering (no code yet, README per tool):
  - `nzxt-n9` — NZXT N9 Z890 embedded fan/RGB controller `1e71:2023`
    (512-byte HID reports; owns ALL fan headers — board exposes zero PWM
    channels to Linux). First experiment: liquidctl's Hue 2 / Smart Device V2
    protocol family as a starting point.
  - `cm-nex-digital` — Cooler Master MasterLiquid Core Nex Digital AIO
    `2516:0232` (pump, digital display, ARGB; Windows app: MasterCTRL).
  - `chassis-ledmatrix` — chassis LED-matrix `ff00:020c` + suspected USB
    screen composite `26ce:0a09` (63 audio ifaces + 1 HID).
- The maintainer's machine IS the reference rig, fully documented in
  [docs/HARDWARE.md](docs/HARDWARE.md), and dual-boots Windows with the
  vendor apps → USB captures come from there
  ([docs/CAPTURE-GUIDE.md](docs/CAPTURE-GUIDE.md)).

## Hard rules

- **One directory per tool, fully standalone.** No imports between tools;
  shared knowledge goes in `docs/`.
- **Never write to a device based on guesses.** Read-only code until the
  protocol is confirmed by captures. A bad HID write can hang a controller.
- Working tools: plain bash, or Python ≥3.10 with `hidapi` only.
- `README.md` and `README.es.md` stay in sync (EN is canonical).
- Every installable tool must be wired in three places: `INSTALLABLE` array
  in `install.sh`, a PKGBUILD in `packaging/arch/<name>/`, and a `build`
  line in `packaging/debian/build-debs.sh`.
- Releases are git tags `vX.Y.Z` (PKGBUILDs fetch the tag tarball). Bump the
  `VERSION` strings in the tool scripts and packaging together.
- Long-term home for protocols is upstream (liquidctl, liquidtux, OpenRGB);
  this repo is where they get decoded and proven first.

## Next step

Capture NZXT CAM ↔ `1e71:2023` traffic on Windows (USBPcap), then decode:
init handshake → fan RPM telemetry → fan duty writes → RGB modes.
