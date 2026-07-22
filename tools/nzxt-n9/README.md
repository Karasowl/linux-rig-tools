# nzxt-n9 🔬

Fan, pump-header and RGB control for the USB controller embedded in
**NZXT N9 motherboards** (first target: N9 Z890).

**Status: reverse engineering.** Read-only helpers and a closed lighting lab
harness exist. Fan duty, pump control, and general RGB APIs are not ready.
This device is why your radiator fans, pump header and board RGB can only be
configured from the BIOS or from NZXT CAM on Windows.

## Fixed per-zone laboratory UI

`bin/nzxt-n9-lab` is a provisional PyQt6 application for exploring only the
capture-backed `Fixed` lighting vector. It is intentionally utilitarian, not
the final application design. Its protocol/model module is separate from the
device writer and UI so a later UI can replace this surface without rewriting
the motor.

From this repository checkout, run the uninstalled laboratory directly:

```
cd tools/nzxt-n9
./bin/nzxt-n9-lab --offline
```

It requires Python 3 and PyQt6. On CachyOS or Arch the relevant signed
repository package is `python-pyqt6`. This laboratory is intentionally not
wired into `install.sh`, packaging, or a system service.

Offline mode is the required development and mechanical-QA mode. It shows the
49-zone route (1-17 down the left, 18-34 across the bottom, 35-49 down the
right), supports single click and Ctrl+Click selection, RGB hex or Qt color
selection, a brightness for the selected zones, and an explicit **Apply**
button. It retains one authoritative raw vector of 49 `GRB` triples. Apply
replaces only selected triples and preserves every other raw triple literally,
then sends the complete vector and fixed `26 06` commit. Offline mode validates
that transaction without opening hidraw. It records an **offline validation**,
never a physical send or a physical lighting result.

Without `--offline`, the sole target is resolved by HID_ID
`0003:00001E71:00002023`. It validates the 150-byte descriptor, character
device major:minor before and after open, rechecks HID_ID and descriptor, and
requires one unambiguous CPU Package sensor below 85 C. Before open it uses
`lstat`, requires a directly-addressed character device, checks major:minor
against sysfs, and checks write access. It opens only that node with
write-only nonblocking/no-follow flags, writes the two 512-byte frames 3 ms
apart, and stops without retry on every error. An in-process lock plus a
nonblocking per-user advisory file lock prevents a second process from joining
the data/commit transaction. The UI runs D32 extraction and all I/O in a Qt
worker, and defers window closing until that transaction completes.

The real mode requires a udev permission rule appropriate for **writing** the
target hidraw node. Do not run the UI with `sudo` just to bypass this check.
For an interactive desktop session, a constrained rule such as
`SUBSYSTEM=="hidraw", ATTRS{idVendor}=="1e71", ATTRS{idProduct}=="2023", MODE="0660", TAG+="uaccess"`
is the intended permission model. Inspect and install any system rule through
the normal administrator workflow. There are no controls for payloads, Report
IDs, device paths, LED counts, Cooling, firmware, fans, or other opcodes.

`Restaurar D32` reads the private D32 PCAP at its fixed local path using
`tshark`, extracts the final target frame read-only, and requires SHA-256
`24a9fd2fbb05769c56505907506c186ba313baa0a277a2506ceb831e77573c70` before it
can send it with the fixed commit. The PCAP is never included in Git. After a
successful D32 operation, its exact raw vector becomes the prepared base. An
offline D32 run is labeled validation only, never a physical send. A later
Apply replaces only its selected triples. The UI keeps prepared state, last
physical send, offline validation, and physically-confirmed state separate, and
labels the last one as unknown because CAM RGB cannot be honestly recovered
from raw triples.

The per-zone candidate is explicitly a thesis:

```
floor(255 * srgb_encode(srgb_decode(v / 255) * pct / 100) + 0.422545474091919)
```

D26-D32 support scale 255 through the 25% `89` value. It can still differ by
one byte from the earlier scale-254 global candidate at uncaptured inputs.
This is not presented as a fact about CAM's internal algorithm.

In real mode, before a physical authoritative base exists, the first **Apply**
is enabled only when all 49 zones are selected. A successful real Apply or D32
restore establishes that vector as the physical base. Later partial Applies
replace only selected triples and preserve the rest literally. Offline mode
keeps partial simulation available but still reports validation, not a physical
send. A data or commit write failure invalidates the physical base because the
hardware may have changed partially. The next real Apply again requires all 49
zones or a successful D32 restore. Failures before the first write do not erase
an already known base.

## CAM lighting observations

Manual NZXT CAM observations for one N9 Z890 board, CAM 4.76.5, and Channel 6
are documented in [NZXT CAM lighting observations](../../docs/NZXT-N9-CAM-LIGHTING.md).
They are evidence-scoped observations, not a universal support guarantee or a
safe USB write specification.

The evidence now covers a twelve-point white-brightness series, nine colors at
7%, and two preselected mixed-color cross-checks. D22 measured `#5A23F4` at 50%
as GRB `17 40 b2`. D24 measured `#0E50AD` at 25% as `27 04 5b`. Both matched
predictions recorded before capture. The combined set is compatible with one
unified quantizer model, but does not prove CAM's internal algorithm or exclude
a lookup table or another function that agrees at the measured points.

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
`os.write`, no `fcntl.ioctl`. A bad HID write can hang the controller, so this
generic helper has no write path. Supervised writes use the separate closed
harness and frozen frames.

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

For an input component `v` and brightness percentage `p`, the unified candidate
computes:

```
floor(254 * srgb_encode(srgb_decode(v / 255) * (p / 100)) + t)
```

The combined D1-D24 evidence retains
`0.4173921478326008 <= t < 0.4276988003512372`. The encoder uses the midpoint
`t = 0.422545474091919`. It reproduces byte for byte all nine captured colors
at 7%, the twelve captured white-brightness points, D22 at 50%, and D24 at 25%.
The fixed `26 06` commit frame also matches the captures. This is a compatible
model, not proof of CAM's implementation. Any uncaptured color and brightness
combination remains a prediction.

The previously uncaptured `#FFD000` at 40% prediction, GRB `89 a9 00`, was
then applied from Linux on the reference N9. The operator observed an immediate
yellow or golden result with normal fan operation. The captured white frame
restored the customary cyan appearance, and CAM reapplied its remembered state
after USB reattachment. This physically validates one generated point outside
the capture set. It supports a generic global `Fixed` controller, but it does
not cover per-zone customization or prove CAM's internal algorithm.

## First-write lab harness (closed, not installed)

`bin/nzxt-n9-first-write-lab` is a **laboratory harness**, not a product CLI
and not wired into installers. It was used for the first reversible Linux
lighting write on the reference N9 Z890 (CAM Fixed, Channel 6, 7%). It now
accepts five surfaces:

```
nzxt-n9-first-write-lab preflight
nzxt-n9-first-write-lab apply-red I-CONFIRM-1E71:2023-LIGHTING-ONLY-WRITE
nzxt-n9-first-write-lab apply-model-yellow40 I-CONFIRM-1E71:2023-LIGHTING-ONLY-WRITE
nzxt-n9-first-write-lab restore-white I-CONFIRM-1E71:2023-LIGHTING-ONLY-WRITE
nzxt-n9-first-write-lab --help
```

There is no color, brightness, channel, Report ID, hidraw path, LED count, or
payload argument. Frames are frozen: D12 red `#FF0000` at 7%, D11 CAM
`#FFFFFF` at 7% (visually dim cyan on this board), predicted `#FFD000` at 40%
with GRB `89 a9 00`, and the captured fixed `26 06` commit. The yellow frame was
an uncaptured D1-D24 model prediction and its Linux physical test produced the
expected yellow or golden result. It remains a model-generated frame, not a CAM
measurement. Writes are a pair of exact
512-byte reports with a 3 ms gap. The device is resolved by HID_ID
`0003:00001E71:00002023`, descriptor checks, and major:minor, with a second
bind after open and before any write.

Offline unit tests live in `tests/test_nzxt_n9_first_write_lab.py` and
`tests/test_nzxt_n9_encoder.py`. They never open real hardware. Do not treat
this harness as a generic lighting API.

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
