# cm-nex-digital 🔬

Pump, fans, hexagonal digital display and ARGB control for the
**Cooler Master MasterLiquid Core Nex Digital** AIO series.

**Status: reverse engineering — no working code yet.**

## Device

| | |
|---|---|
| USB ID | `2516:0232` ("MLQ-Core-Nex-Digital-BK") |
| Interface | HID, single interface |
| Windows app | Cooler Master **MasterCTRL** |
| Upstream | absent from liquidctl and OpenRGB |

## What we know

- The AIO enumerates as a single HID device: pump control, the digital
  display (temperature readout, styles) and lighting all go through it.
- Older Cooler Master coolers (MasterLiquid ML series, `2516:0051` etc.) are
  not in liquidctl either — CM protocols have historically been decoded by
  small standalone projects; this tool aims to be the reference one and then
  upstream.

## Plan

1. Captures of MasterCTRL (see [capture guide](../../docs/CAPTURE-GUIDE.md)):
   startup handshake, pump mode changes, display source/style changes
   (CPU temp vs liquid temp), each ARGB effect, brightness.
2. Read-only prototype: liquid temp + pump RPM telemetry.
3. Writes: pump duty, display config, ARGB.
4. Upstream to **liquidctl**; hwmon via **liquidtux** so the liquid
   temperature shows up in `sensors`.

## How to help

Any Nex Digital owner (240/280/360, black or white): `rig-diagnose` output
first — PIDs may differ per size/color — then captures.
