# Reference rig — full hardware inventory

Diagnostic performed on CachyOS, kernel `6.18.38-2-cachyos-lts` (2026-07).
This is the machine the first drivers are being developed against.

## System

| Component | Detail |
|-----------|--------|
| Motherboard | **NZXT N9 Z890** (BIOS 3.14) — sys/board vendor `NZXT` |
| CPU | Intel Core Ultra 7 270K Plus (Arrow Lake-S, 8 P + 16 E cores), `intel_pstate` |
| GPU | **Zotac** GeForce RTX 5060 Ti (GB206, `10de:2d04`, subsystem `19da:1772`), driver 610.43.03 |
| RAM | 2× DDR5 with `spd5118` temp sensors (SMBus 0x51 / 0x53) |
| Storage | WD SN770/SN5000-class NVMe (`15b7:5017`) behind Intel VMD |
| Network | Realtek RTL8126 5GbE + Intel BE200 Wi-Fi 7 / BT |
| AIO | Cooler Master **MasterLiquid Core Nex Digital** (USB `2516:0232`) |

## USB control devices (bus 003, internal headers)

| Device | USB ID | hidraw | Notes |
|--------|--------|--------|-------|
| NZXT N9 Z890 embedded fan/RGB controller | `1e71:2023` | `hidraw1` | HID, 1 interface, **512-byte** IN/OUT packets (Hue 2 family uses 64) |
| Cooler Master `MLQ-Core-Nex-Digital-BK` | `2516:0232` | `hidraw4` | HID, 1 interface. Pump + fans + hex digital display + ARGB |
| "309 LED Matrix Controller 200324" | `ff00:020c` | — (no hidraw bound) | HID class, bogus vendor ID `ff00`. Drives the chassis LED-matrix effects (hourglass, clock, animations) |
| "Generic USB Audio" composite | `26ce:0a09` | `hidraw0` | 63(!) audio-class interfaces + 1 HID — the classic signature of a cheap USB screen streaming frames over isochronous audio endpoints. Likely the chassis display panel; needs investigation |
| Evision RGB Keyboard | `320f:5000` | `hidraw2/3` | Known family in OpenRGB (Redragon/EvoFox OEM); this PID reported as Redragon MITRA K551RGB |

Two Genesys Logic hubs (`05e3:0610`) sit between the root hub and these
devices — the case's internal USB hub chain.

## What Linux sees today (the gaps)

- **No motherboard Super-I/O hwmon chip is exposed.** `sensors` shows
  `coretemp`, `nvme`, `spd5118`, NIC and Wi-Fi — but **zero fan RPM / PWM
  channels**. Every fan header (radiator fans, pump header, chassis fans) is
  owned by the embedded NZXT controller (`1e71:2023`), which only NZXT CAM
  (Windows) speaks. That's why fan curves can only be set in the BIOS.
- `acpi_fan` exposes a stub with `fan1: N/A`.
- `/sys/class/leds` contains only NIC/keyboard-lock LEDs — no RGB zones.
- No `platform_profile` (desktop board).
- liquidctl (as of 1.15.x) supports NZXT `1e71` PIDs up to the 2022 RGB & Fan
  Controller variants; **`2023` is absent**. OpenRGB likewise.
- Cooler Master `2516:0232` is absent from liquidctl and OpenRGB. Windows
  software: **MasterCTRL**.
- `ff00:020c` and `26ce:0a09` appear in no known project.
- Zotac RTX 50-series RGB ("Spectra") is not yet covered by OpenRGB's Zotac
  GPU controllers.

## Support matrix / plan

| Device | Windows app | Linux today | Plan |
|--------|-------------|-------------|------|
| NZXT N9 fan+RGB (`1e71:2023`) | CAM | ❌ BIOS only | [`tools/nzxt-n9`](../tools/nzxt-n9/) → upstream to liquidctl + liquidtux |
| CM Nex Digital AIO (`2516:0232`) | MasterCTRL | ❌ | [`tools/cm-nex-digital`](../tools/cm-nex-digital/) → upstream to liquidctl |
| Chassis LED matrix (`ff00:020c`) | vendor suite | ❌ | [`tools/chassis-ledmatrix`](../tools/chassis-ledmatrix/) |
| Chassis screen? (`26ce:0a09`) | vendor suite | ❌ | investigate under `chassis-ledmatrix` |
| Evision keyboard (`320f:5000`) | Redragon sw | ⚠️ partial | upstream request/patch to OpenRGB |
| Zotac RTX 5060 Ti RGB | Firestorm/Spectra | ❌ | capture + upstream to OpenRGB |
| CPU/GPU power profiles | CAM / BIOS | ✅ sysfs + nvidia-smi | [`tools/rig-profiles`](../tools/rig-profiles/) (works today) |

## Reproducing this inventory

```sh
tools/rig-diagnose/bin/rig-diagnose
```
