# nzxt-n9 🔬

Fan, pump-header and RGB control for the USB controller embedded in
**NZXT N9 motherboards** (first target: N9 Z890).

**Status: reverse engineering — no working code yet.** This device is why
your radiator fans, pump header and board RGB can only be configured from the
BIOS or from NZXT CAM on Windows.

## Device

| | |
|---|---|
| USB ID | `1e71:2023` ("NZXT N9 Z890") |
| Interface | HID, single interface, interrupt IN/OUT |
| Packet size | **512 bytes** (wMaxPacketSize 0x0200) |
| Windows app | NZXT CAM |
| Upstream | absent from liquidctl (≤1.15) and OpenRGB |

## What we know

- NZXT's previous embedded controllers (N7 boards, Smart Device V2, RGB & Fan
  Controller `1e71:2009/200e/2010/2011/2019/…`) speak the well-documented
  Hue 2 protocol family with 64-byte reports — liquidctl implements it in
  `liquidctl/driver/smart_device.py`.
- This controller's 512-byte reports suggest a **new protocol generation**,
  but NZXT tends to keep command structure similar (`0x60 0x02`-style
  fan-duty writes, `0x2a`-style RGB writes, status broadcasts on interrupt IN).
- The board exposes **no Super-I/O hwmon chip** to Linux: every fan header is
  behind this device, so RPM telemetry must also come from here.

## Plan

1. **Captures** (see [docs/CAPTURE-GUIDE.md](../../docs/CAPTURE-GUIDE.md)):
   CAM startup, each fan channel duty change, pump header, each RGB mode.
2. Read-only prototype: decode the interrupt-IN status stream (RPMs, temps).
3. Fan duty + RGB writes, verified against captures only.
4. CLI here; then upstream the protocol to **liquidctl** and a kernel hwmon
   driver to **liquidtux** so `sensors` and CoolerControl see the fans.

## How to help

Own an N9 board (Z890 or newer)? Run `rig-diagnose`, open an issue, and if
you dual-boot: one capture set = massive progress.
