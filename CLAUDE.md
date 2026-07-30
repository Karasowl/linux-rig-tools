# CLAUDE.md

Context for AI coding agents working in this repo.

## What this is

Monorepo of **small, independent Linux tools** for PC hardware that is only
manageable from Windows vendor apps (fan curves, pump control, RGB,
LED-matrix displays). Each tool is standalone and individually installable.
Full project vision: [README.md](README.md). Plan: [docs/ROADMAP.md](docs/ROADMAP.md).
Living state, evidence and route: [docs/ESTADO-Y-RUTA.md](docs/ESTADO-Y-RUTA.md).

## Current state (2026-07-29)

- ✅ Installable and working: `rig-diagnose`, `rig-profiles`, plain bash at
  `tools/<name>/bin/<name>`, tested on the reference rig. They are still the
  only entries in the `INSTALLABLE` array of `install.sh`.
- 🔬 `nzxt-n9` is the active target and it already has real, tested code.
  NZXT N9 Z890 embedded fan/RGB controller `1e71:2023`, 512-byte HID reports,
  owns ALL fan headers because the board exposes zero PWM channels to Linux.
  - `bin/nzxt-n9`: read-only `status` and `find`, plus a purely offline
    `encode`. Never writes to the device.
  - `bin/nzxt-n9-lab`: PyQt6 laboratory for the 49-zone Fixed colour vector.
  - `bin/nzxt-n9-first-write-lab`, `bin/nzxt-n9-animated-write-lab`,
    `bin/nzxt-n9-alternating-write-lab`: closed harnesses that replay exact
    captured 512-byte frames. Not installed, not generic APIs, no encoders.
  - `lib/nzxt_n9_fixed.py`, `lib/nzxt_n9_animated.py`,
    `lib/nzxt_n9_alternating.py`, covered by 112 offline tests in
    `tools/nzxt-n9/tests/`.
  - Decoded and physically validated on the reference board: Fixed lighting
    global and per zone, Spectrum Wave D35, and **all twelve Alternating
    states any capture contains**, which is both full rightward speed tables
    (travelling 300/400/500/700/800, in-place 600/800/1000/1300/1600) plus the
    two leftward Normal states, so byte 55 has had all four of its values
    written to the board. No leftward speed other than Normal is measured
    anywhere and none may be inferred.
  - Decoded but not written: the other thirteen animated modes, the
    parameterized `26 06` of Marquee and Wave, and the `26 14` audio stream.
  - Not captured at all yet: the whole Cooling page, so no RPM, temperature,
    duty or curve support exists.
- 🔬 No code yet, README per tool:
  - `cm-nex-digital`: Cooler Master MasterLiquid Core Nex Digital AIO
    `2516:0232` (pump, digital display, ARGB, Windows app MasterCTRL).
  - `chassis-ledmatrix`: chassis LED-matrix `ff00:020c` plus suspected USB
    screen composite `26ce:0a09` (63 audio ifaces and 1 HID).
- The maintainer's machine IS the reference rig, fully documented in
  [docs/HARDWARE.md](docs/HARDWARE.md). Its Windows dual boot is dead and was
  abandoned as unrecoverable, so the vendor apps now run inside the
  `win11-cap` QEMU/KVM VM. Captures are taken with `usbmon` from Linux while
  the device is attached to that VM ([docs/CAPTURE-GUIDE.md](docs/CAPTURE-GUIDE.md)).

## Hard rules

- **One directory per tool, fully standalone.** No imports between tools.
  Shared knowledge goes in `docs/`.
- **Never write a frame the captures do not contain.** A write lab may only
  send a full 512-byte payload extracted from a private PCAP and pinned by its
  SHA-256. No encoder, no interpolation, no free parameters, no field-level
  synthesis. Speed in particular is a measured table and not a function, so
  intermediate notches must be captured, never computed.
- **Physical writes need explicit per-session authorization from the
  maintainer**, an available exact restore frame, one write attempt with no
  retry, and human visual confirmation afterwards. A bad HID write can hang a
  controller that also drives every fan header.
- Working tools: plain bash, or Python >=3.10 using only the standard library.
  The N9 code opens `/dev/hidrawN` directly and has no `hidapi` dependency.
  The single third-party dependency in the repo is PyQt6, used only by the
  non-installed `nzxt-n9-lab` UI.
- `README.md` and `README.es.md` stay in sync (EN is canonical).
- Every installable tool must be wired in three places: `INSTALLABLE` array
  in `install.sh`, a PKGBUILD in `packaging/arch/<name>/`, and a `build`
  line in `packaging/debian/build-debs.sh`. The N9 write labs are
  deliberately outside all three.
- Releases are git tags `vX.Y.Z` (PKGBUILDs fetch the tag tarball). Bump the
  `VERSION` strings in the tool scripts and packaging together.
- Long-term home for protocols is upstream (liquidctl, liquidtux, OpenRGB).
  This repo is where they get decoded and proven first.

## Next step

Finish N9 lighting before touching cooling. Alternating is now closed for
every state a capture contains, so what remains needs **new captures** rather
than new labs. In order:

1. Measure the five speed notches of the modes other than Alternating.
   Breathing has three of five and Spectrum Wave two of five today. After D51
   these cannot be projected from a known table, they have to be measured one
   by one, and they batch well into a single window.
2. Retry Temperature Monitor, which has a triple negative result in the VM
   (D42, D46, D47) and has never transmitted a frame.
3. If the leftward sub-mode ever needs a speed table, capture a leftward
   sweep. CAM was never swept leftward, so nothing exists to freeze today.

After lighting closes, Macroetapa 3 is the N9 Cooling page, the highest-risk
stage of the project.
