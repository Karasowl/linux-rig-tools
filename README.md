# linux-rig-tools

**Linux tools for gaming-PC hardware that still lacks native support.**
🇪🇸 [Léeme en español](README.es.md)

Modern motherboards, AIO coolers, cases and peripherals increasingly hide their
fan curves, pump control, RGB effects and LED-matrix displays behind
Windows-only apps (NZXT CAM, Cooler Master MasterCTRL, no-name chassis suites).
On Linux you are left with whatever the BIOS exposes.

This monorepo collects **small, independent tools** — install only the ones
your rig needs. Nothing here depends on anything else in the repo.

## Tools

| Tool | What it does | Status |
|------|--------------|--------|
| [`rig-diagnose`](tools/rig-diagnose/) | Inventories your RGB/fan/cooling controllers and reports what is (un)supported on Linux. Read-only, zero dependencies. | ✅ works today |
| [`rig-profiles`](tools/rig-profiles/) | `quiet` / `balanced` / `performance` profiles for CPU (governor + EPP) and NVIDIA GPU (power limit) without vendor software. | ✅ works today |
| [`nzxt-n9`](tools/nzxt-n9/) | Fan curves, pump header and RGB control for the controller embedded in NZXT N9 motherboards (`1e71:2023`, N9 Z890). Fixed per-zone laboratory UI available. | 🔬 reverse engineering |
| [`cm-nex-digital`](tools/cm-nex-digital/) | Pump, fans, digital display and ARGB of the Cooler Master MasterLiquid Core Nex Digital AIO (`2516:0232`). | 🔬 reverse engineering |
| [`chassis-ledmatrix`](tools/chassis-ledmatrix/) | Effects (hourglass, clock, animations…) of generic chassis LED-matrix controllers (`ff00:020c` and friends). | 🔬 reverse engineering |

Devices that already have a healthy upstream home (OpenRGB, liquidctl) are
**upstreamed, not duplicated** — see the [roadmap](docs/ROADMAP.md).

## Install

Every method installs only the tools you pick.

**Any distro (Arch/CachyOS, Debian/Ubuntu, Fedora, openSUSE…):**

```sh
git clone https://github.com/Karasowl/linux-rig-tools.git
cd linux-rig-tools
sudo ./install.sh            # interactive menu
sudo ./install.sh --all      # everything installable
sudo ./install.sh --uninstall
```

**Arch / CachyOS / Manjaro** — PKGBUILDs in [`packaging/arch/`](packaging/arch/)
(AUR packages planned once the first drivers land):

```sh
cd packaging/arch/rig-profiles && makepkg -si
```

**Debian / Ubuntu / Mint / Pop!_OS** — build .deb packages:

```sh
./packaging/debian/build-debs.sh   # produces dist/*.deb
sudo apt install ./dist/rig-profiles_*_all.deb
```

**Fedora / openSUSE** — use `install.sh` for now; COPR/OBS planned.

## Reference hardware

The first target rig is fully documented in
[docs/HARDWARE.md](docs/HARDWARE.md): NZXT N9 Z890, Intel Core Ultra 7 270K,
Zotac RTX 5060 Ti, Cooler Master MasterLiquid Core Nex Digital, chassis
LED-matrix display. If you own any of these devices your
[captures and reports](docs/CAPTURE-GUIDE.md) are extremely welcome.

## Contributing

Run `rig-diagnose` and attach its output to your issue — that is the single
most useful thing you can do. To help decode a protocol, read the
[capture guide](docs/CAPTURE-GUIDE.md). More in
[CONTRIBUTING.md](CONTRIBUTING.md).

## License

[GPL-3.0-or-later](LICENSE).
