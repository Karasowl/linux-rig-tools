# nzxt-n9 🔬

Fan, pump-header and RGB control for the USB controller embedded in
**NZXT N9 motherboards** (first target: N9 Z890).

**Status: reverse engineering.** Read-only helpers and a closed lighting lab
harness exist. Fan duty, pump control, and general RGB APIs are not ready.
This device is why your radiator fans, pump header and board RGB can only be
configured from the BIOS or from NZXT CAM on Windows.

## CAM lighting observations

Manual NZXT CAM observations for one N9 Z890 board, CAM 4.76.5, and Channel 6
are documented in [NZXT CAM lighting observations](../../docs/NZXT-N9-CAM-LIGHTING.md).
They are evidence-scoped observations, not a universal support guarantee or a
safe USB write specification.

The current twelve-point brightness evidence rejects one exact sRGB rounding
hypothesis at both 2% and 7%. The 7% result supports a fitted compatible
quantizer family, but does not identify a unique formula or test an arbitrary
lookup table. This does not establish a Linux implementation, a complete
protocol, or permission to reproduce observed USB payloads.

At fixed 7% brightness, isolated global color captures observed 49 repeated
triples: white as `4a 4a 4a`, red as `00 4a 00`, blue as `00 00 4a`, and
green as `4a 00 00`.
Under the still-unproven assumption that these triples encode color components,
the evidence favors `GRB` byte order. A mixed magenta capture produced
`00 4a 4a`, which is compatible with red and blue components being active
together under that interpretation. A non-binary mixed capture for `#804020`
produced `0c 21 03`. This differs from a naive linear component projection and
was reproduced byte for byte in a second final frame. This supports further
testing of a nonlinear transform, without identifying a unique formula or
lookup table. A permuted `#408020` test then produced the predicted `21 0c 03`,
exchanging the first two component levels and preserving the third. This
strengthens `GRB` ordering and a shared transform for the measured levels. It
was followed by `#C08040`, which produced `21 36 0c` and added the new component
level `36` for input 192. One standard sRGB linear-light candidate reproduces
the observed non-maximum inputs 32, 64, 128, and 192 at 7%, but misses the
measured full component by one. A preselected boundary test at input 127 then
produced `20`, refuting an exact 0.07 multiplier and remaining compatible with
an effective multiplier around 0.069 in that candidate family. This is a fitted
compatibility interval, not a confirmed formula. These captures do not prove
one triple per LED, confirm a channel index, or establish safe write semantics.

## Device

| | |
|---|---|
| USB ID | `1e71:2023` ("NZXT N9 Z890") |
| Interface | HID, single interface, interrupt IN/OUT |
| Packet size | **512 bytes** (wMaxPacketSize 0x0200) |
| Windows app | NZXT CAM |
| Upstream | absent from liquidctl (1.15 or older) and OpenRGB |

## What we know

- NZXT's previous embedded controllers (N7 boards, Smart Device V2, RGB & Fan
  Controller `1e71:2009/200e/2010/2011/2019/…`) speak the well-documented
  Hue 2 protocol family with 64-byte reports. liquidctl implements it in
  `liquidctl/driver/smart_device.py`.
- This controller's 512-byte reports suggest a **new protocol generation**,
  but NZXT tends to keep command structure similar (`0x60 0x02`-style
  fan-duty writes, `0x2a`-style RGB writes, status broadcasts on interrupt IN).
- The board exposes **no Super-I/O hwmon chip** to Linux: every fan header is
  behind this device, so RPM telemetry must also come from here.

## Read-only status (WIP)

There is a first, **read-only** helper at `bin/nzxt-n9`. It is not wired into
the installers yet (`install.sh`, PKGBUILD, debian) because the protocol is
still being decoded.

```
nzxt-n9 status    # read a few 'ff 03' input reports and decode them
nzxt-n9 find      # print the hidraw node for 1e71:2023
```

`status` locates the controller's `/dev/hidrawN` node via sysfs, opens it
**read-only**, and decodes the periodic 512-byte `ff 03` report using the U1
field map:

| offset | meaning |
|---|---|
| 0..1 | `ff 03` prefix (heartbeat family) |
| 2..13 | 12-byte echo of the USB iSerial |
| 14..15 | `uint16` little-endian frame counter (+1 per frame) |
| 16 | flag `0x01` (unknown, low confidence) |
| 17..511 | zero padding |

Important: `ff 03` is a **heartbeat/keepalive**. It carries **no** live
CPU/GPU temp, fan RPM or pump telemetry (verified in U1). The counter is not
a sensor. Live telemetry appears to be host-solicited and would require a
device *write*, which this tool deliberately does not do.

**Safety.** The tool never writes to the device: no HID output reports, no
feature reports, no `ioctl` that sends data. The read path uses Python's
`os.open(..., O_RDONLY | O_NONBLOCK)` plus `os.read`/`os.close` only, no
`os.write`, no `fcntl.ioctl`. A bad HID write can hang the controller, so
writing stays out until the protocol is proven from captures.

Reading `/dev/hidrawN` usually needs permission. Either run with `sudo`, or
add a udev rule:

```
# /etc/udev/rules.d/70-nzxt-n9.rules
SUBSYSTEM=="hidraw", ATTRS{idVendor}=="1e71", ATTRS{idProduct}=="2023", MODE="0440", TAG+="uaccess"
```

then `sudo udevadm control --reload && sudo udevadm trigger`.

Requires `python3` (>=3.10). No `hidapi` dependency.

## Frame encoder (offline, does not send)

`nzxt-n9 encode` builds, in memory, the 512-byte `Fixed` single-color lighting
frame for a color and brightness and prints it as hex. It is a decoding aid, a
way to check our model against captures. **It never opens `/dev/hidraw` and
never sends anything.** The first reversible Linux lighting write used the
closed lab harness below, not this generic encoder.

```
nzxt-n9 encode ff0000 7            # red at 7%, prints the load frame in hex
nzxt-n9 encode 804020 7 --commit   # also print the fixed '26 06' commit frame
nzxt-n9 encode 00ff00 7 --hex-only # raw hex only, one frame per line
```

The frame layout matches the captured `Fixed` writes:

| offset | meaning |
|---|---|
| 0 | `0x26` HID Report ID (first byte of the on-wire buffer) |
| 1..3 | `04 20 00` (sub-command `04`, channel selector `20`, `00`) |
| 4..150 | 49 identical `G R B` triples (147 bytes) |
| 151..511 | zero padding |

Each component byte is `round_half_up(254 * srgb_encode(srgb_decode(v/255) * k))`
with a brightness constant `k`. At 7% `k` sits in the fitted interval
`[0.069272, 0.069968]`; the encoder uses a representative value that reproduces
every measured 7% byte. The output was validated **byte for byte at 7%** against
nine real captures (white, red, blue, green, magenta, `#804020`, `#408020`,
`#C08040`, `#7F7F7F`), and the fixed `26 06` commit frame matches all nine.

**Only 7% is capture-validated.** For any other brightness the encoder scales
`k` linearly from the 7% anchor. That `k(b)` is a model, not anchored point by
point, so a predicted byte can differ from CAM by one level at some
brightnesses. Treat non-7 output as a hypothesis, not a measurement.

## First-write lab harness (closed, not installed)

`bin/nzxt-n9-first-write-lab` is a **laboratory harness**, not a product CLI
and not wired into installers. It was used for the first reversible Linux
lighting write on the reference N9 Z890 (CAM Fixed, Channel 6, 7%). It only
accepts four surfaces:

```
nzxt-n9-first-write-lab preflight
nzxt-n9-first-write-lab apply-red I-CONFIRM-1E71:2023-LIGHTING-ONLY-WRITE
nzxt-n9-first-write-lab restore-white I-CONFIRM-1E71:2023-LIGHTING-ONLY-WRITE
nzxt-n9-first-write-lab --help
```

There is no color, brightness, channel, Report ID, hidraw path, LED count, or
payload argument. Frames are frozen: D12 red `#FF0000` at 7%, D11 CAM
`#FFFFFF` at 7% (visually dim cyan on this board), and the fixed `26 06`
commit. Writes are a pair of exact 512-byte reports with a 3 ms gap. The
device is resolved by HID_ID `0003:00001E71:00002023`, descriptor checks, and
major:minor, with a second bind after open and before any write.

Offline unit tests live in `tests/test_nzxt_n9_first_write_lab.py` and never
open real hardware. Do not treat this harness as a generic lighting API.

## Plan

1. **Captures** (see [docs/CAPTURE-GUIDE.md](../../docs/CAPTURE-GUIDE.md)):
   CAM startup, each fan channel duty change, pump header, each RGB mode.
2. Read-only prototype: decode the interrupt-IN status stream (RPMs, temps).
3. Fan duty + RGB writes, verified against captures only.
4. CLI here, then upstream the protocol to **liquidctl** and a kernel hwmon
   driver to **liquidtux** so `sensors` and CoolerControl see the fans.

## How to help

Own an N9 board (Z890 or newer)? Run `rig-diagnose`, open an issue, and if
you dual-boot: one capture set means massive progress.
