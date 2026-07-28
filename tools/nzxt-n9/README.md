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

## Spectrum Wave D35 write lab (closed, not installed)

`bin/nzxt-n9-animated-write-lab` is a separate conservative harness for
explicitly authorized physical sessions. It can only validate or send the
exact 512-byte D35 `Spectrum Wave` frame, or delegate restoration to the
existing typed D32 Fixed API. It has no generic write, payload, color,
brightness, speed, direction, mode, channel, LED count, or hidraw-path input.

The frozen frame begins `2a 04 20 20 02 fa 00`, has `31 03` at bytes 58 and
59, and has SHA-256
`8b93db5f5b1552e93203d2e59be6734bae53c9d01b217f78744ab031603899ef`.
Applying it makes exactly one 512-byte write with no sleep, commit, retry, or
second write. A partial write or error fails closed. Restoring uses
`restore_d32_vector()` and `N9FixedWriter`, preserving the Fixed data, 3 ms
gap, and commit transaction.

```
nzxt-n9-animated-write-lab --offline preflight
nzxt-n9-animated-write-lab --offline apply-spectrum-wave I-CONFIRM-1E71:2023-LIGHTING-ONLY-APPLY-SPECTRUM-WAVE-D35
nzxt-n9-animated-write-lab --offline restore-d32 I-CONFIRM-1E71:2023-LIGHTING-ONLY-RESTORE-D32-FIXED
```

Remove `--offline` only in a separately authorized supervised hardware
session. Real preflight resolves the fixed HID identity, descriptor,
major:minor, direct character node, write permission, and CPU Package below
85 C without opening hidraw. Apply uses the same nonblocking device lock as
Fixed, repeats all identity checks after open, and then makes its one write.
The two write operations require distinct exact tokens.

Offline mode never resolves, opens, or writes hidraw for D35. Offline D32 reads
and validates the private capture, then uses the existing Fixed offline writer.
An offline success is only mechanical validation and does not constitute
physical QA or a general specification for `2a 04`, other animated modes,
parameters, or devices.

**Verified by the operator on 2026-07-27:** real preflight resolved
`/dev/hidraw2` with CPU Package at 42.0 C without opening hidraw. The laboratory
then made its single exact D35 write. The operator observed Spectrum Wave
working correctly for 10 seconds with fans and pump remaining normal. The
subsequent typed D32 restoration completed successfully and returned the board
to Fixed. This QA validates only the frozen D35 replay and D32 restore on this
board. It does not authorize other animated frames or inferred parameters.

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

## Animated modes: decoded observations (D35-D51)

The D35-D38 series (2026-07-21/22) isolated `Spectrum Wave` with one human
action per window. The D39-D46 campaign (2026-07-22) then enumerated every
remaining CAM lighting mode and decoded the first fields, using attributable
batch selections plus targeted single-variable captures. D47 through D51
(2026-07-25 and 26) closed the fields that campaign left open. Everything below is
verified from the archived PCAPs unless labeled otherwise, for this board,
CAM 4.76.5, and Channel 6.

**Three observed transport patterns, verified** (not a complete
classification: `Monitor Temperature` transmitted nothing in its window and
its pattern remains unknown):

1. **Firmware effects** (fourteen modes): one 512-byte `2a 04` configuration
   frame per user action, **no `26 06` commit**, no further host traffic (up
   to 174 s of observed silence while the animation kept running). The
   controller acknowledges each frame with the `ff 01` echo of the opcode.
2. **`26`-family effects** (`Marquee`, `Wave`): no `2a` frame. Each action
   sends the `Fixed`-style `26 04` GRB vector plus a **parameterized
   `26 06` commit** 2-3 ms later: byte 4 is `02` (Fixed uses `01`) and
   byte 5 selects the effect, `29` Marquee, `35` Wave (`00` Fixed).
   Marquee's LED size is the number of lit triples at the start of the
   vector (one size step went from 3 to 4). The other commit parameters are
   **unknown**.
3. **Host streaming** (`Audio Bass`, `Audio Level`): no configuration frame
   at all. CAM streams `26 14` frames (header `26 14 20 20`, 49 triples)
   about every 32 ms, following the audio, with no commit, for the whole
   remainder of the capture (leaving the mode was not captured). The
   controller acked every streamed frame whose ack window the capture
   covered, and its `ff 03` heartbeat stopped while the stream was active.

**Mode identifiers** (byte 4 of `2a 04`), all measured in traffic. Modes
marked * were captured in a single window and remain single observations:

| `01` Fading* | `02` Spectrum Wave | `04` Covering Marquee* | `05` Alternating |
|---|---|---|---|
| `06` Pulse* | `07` Breathing | `08` Candle* | `09` Starry Night* |
| `0b` Rainbow Flow* | `0c` Super Rainbow* | `0d` Rainbow Pulse* | `0e` Tai Chi* |
| `0f` Water Cooler* | `10` Loading* | | |

`03` and `0a` never appeared. Marquee and Wave have no `2a` identifier.

Decoded `2a 04` fields, evidence-classified:

- Byte 4 mode identifier: **verified** across fourteen distinct constants
  following the announced selection order in four independent windows.
- Bytes 5-6 speed: **verified** little-endian uint16 (Alternating `Normal`
  is 500), lower is faster (**verified** with Breathing `Slowest` 40,
  `Normal` 20, `Fastest` 4 plus the observed acceleration in D36). The
  scale is **per mode and per sub-mode**, so a value is meaningless without
  both. The track has **exactly five positions** and saturates silently at
  **both ends** (D50 slow, D51 fast): a further arrow press transmits
  nothing. Both Alternating curves are complete and verified, `Fastest` to
  slow extreme: **300/400/500/700/800** with propagation and
  **600/800/1000/1300/1600** without it.
- The speed scale is a **lookup table, not an interpolable function** (D50),
  and the sub-mode relationship is **not a constant factor** (D51). The
  factor of 2 holds exactly at four notches and breaks at `Slow`
  (700 against 1300, ratio 1.857). Neither table derives from the other:
  half of 1300 is 650, which is what a piecewise-linear model predicted for
  the propagating `Slow`, where CAM writes 700. Steps inside a sub-mode are
  irregular too (+100, +100, **+200**, +100 with propagation), refuting the
  piecewise-linear and geometric candidates registered before D50.
- Both windows pre-registered every value before capturing; D51 carried
  three internal controls from D48 and all three reproduced exactly, so the
  discrepant `Slow` is a real measurement. **A Linux implementation must
  transcribe five raw values per mode and per sub-mode**, with no
  interpolation and no derivation between sub-modes. A projection would have
  written 1400 where the real value is 1300.
- Scale shape is per mode: Alternating's `Fast` is 0.8x its `Normal`,
  Spectrum Wave's is 0.6x its own (150 against 250, D36), Breathing's
  extremes are 2.0x and 0.2x. Alternating is the only effect exposing a
  movement switch, so no second mode exists to test sub-mode behaviour
  against. Other modes are incomplete: Breathing three of five notches,
  Spectrum Wave two of five, the rest none.
- Bytes 8+ color list: **verified** contiguous 3-byte entries in **R B G
  order** (pure red entered as `89 00 00`, pure blue as `00 89 00` at 25%),
  the reverse of Fixed's G R B. Byte 56 is the entry count, and deleting an
  entry compacts the list. Brightness is **baked into the entries** (one
  brightness step rewrote only the color bytes), with the full-component
  level matching the per-zone Fixed level at 25%. The exact quantizer is
  **unknown**.
- Byte 55 bit field: bit 1 is direction, **verified in two modes**
  (Spectrum Wave `00` to `02`, Alternating `01` to `03`). Bit 0 is spatial
  propagation, **verified in D47** with Alternating's movement switch: `1`
  makes the alternation travel along the board, `0` makes the whole board
  switch in place. It does not gate the animation, the two colors keep
  alternating either way. Bits 0 and 1 are independent, **verified in D48**
  with all four Alternating states measured, and CAM keeps writing bit 1
  when bit 0 is clear. Starry Night carries `01` without exposing that
  switch, which fits a mode that always propagates but is not verified.
- Bytes 3, 7 (Candle carried `56`), 57, and 58-59 (`31 03`, but `31 04` in
  Alternating): meaning **unknown**.

`Monitor Temperature` has a **verified negative result**: selecting it plus
its CPU source transmitted zero frames in three separate windows, the last of
them on a different day and after a full VM restart (the board visibly kept
its previous effect). The failure is in CAM before the USB
layer, likely related to the virtualized temperature sources (**inference**).
Its transport pattern is **unknown** and a retry is pending.

Implication for Linux, stated as engineering direction rather than a spec:
the audio modes cannot be reproduced with a one-shot write. They would need
a daemon streaming `26 14` frames at ~30 ms cadence. The same opcode is a
candidate path for arbitrary host-rendered real-time effects on the 49
zones. Outside the exact frozen D35 laboratory above, none of this authorizes
writes: no other `2a 04`, parameterized `26 06`, or `26 14` frame is a safe
write specification yet. Details and per-capture evidence live in
[NZXT CAM lighting observations](../../docs/NZXT-N9-CAM-LIGHTING.md).

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
