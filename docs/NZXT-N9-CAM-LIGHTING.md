# NZXT CAM lighting observations for N9 Z890

## Scope and evidence status

This document records a manual exploration of NZXT CAM 4.76.5 on one N9 Z890 board, in **Lighting**, **Channel 6: N9 Z890 (1)**. It is not a compatibility promise for another N9 revision, CAM release, channel, operating system, or controller.

Evidence labels used here:

- **Verified from artifacts** means a saved screenshot or isolated USB analysis supports the statement.
- **Reported manual observation** means the behavior was observed during interactive use and reported by the operator.
- **Inference** means a plausible interpretation that needs more controlled evidence.
- **Unknown** means the current evidence does not establish the behavior or protocol meaning.

The color descriptions below are visual impressions only. They are not colorimetry measurements. This document does not decode USB traffic into a safe control protocol.

## Brightness controls and exact test method

**Reported manual observation:** hovering the individual Channel 6 brightness track shows an exact percentage tooltip before clicking.

- Clicking inside the visible track at its left side can select 0%.
- Clicking inside the visible track at its right side reaches at most 99%.
- Reaching 100% with a mouse required clicking immediately to the right of the track, near or inside the sun icon hitbox. The tooltip then showed 100%.
- The hollow circular icon immediately left of the track, and the very close area between that icon and the track, set the value to 0%.

The visible track and the icon hitboxes are distinct. Their exact geometric boundaries are **unknown** and should not be assumed from this observation.

With the slider focused, Right Arrow increased the value by exactly one percentage point per press. The operator verified tooltips at 49%, 50%, 90%, 99%, and 100%. An additional Right Arrow at 100% remained clamped at 100%.

This provides a repeatable, non-dragging method for exact tests:

1. Use hover plus a track click for an observed intermediate value, or focus the slider.
2. Use arrow keys to reach the requested value one percentage point at a time.
3. Confirm the tooltip before recording a capture or drawing a conclusion.

## Fixed color and per-zone customization

**Reported manual observation:** `Fixed` exposes brightness from 0% to 100% and one global palette or custom color.

- Black was visually indistinguishable from LEDs being off or brightness 0%.
- White `#FFFFFF` appeared light cyan on this board.
- Blue appeared blue.
- Some light reds appeared pink, and pink appeared violet.
- Green, yellow, olive, dark orange, strong red, and purple had a visually reasonable correspondence to their selected colors.

These are appearance reports, not calibrated output values.

Enabling `Customize LED colors` disabled the global color selector and displayed a board map. During this exploration, only one clearly selectable region was found, near the upper edge. Setting it red changed only that region while the rest retained the previous global color. Turning the switch off restored the previous global color. More selectable regions remain **unknown** and need a deliberate map.

## CAM state reapplied after USB reconnection

**Reported controlled visual observation on 2026-07-21:** CAM held `Fixed`,
global `#00FF00`, brightness 100%, and per-zone customization disabled. The N9
USB device was detached from the running Windows VM. Linux then sent the frozen
CAM-white frame at 7%, and the operator confirmed the usual light-cyan physical
appearance with the fans still running normally. The USB device was attached
again to the same running VM while CAM remained open. Without any click or CAM
interaction, the physical lighting returned automatically to green at 100%.

This demonstrates that, in this running CAM session, CAM remembered and
reapplied its current lighting state when the N9 reappeared. It also separates
CAM's remembered state from the complete `Fixed` frames sent by Linux. A prior
VM startup showed CAM displaying the last D21 value, `#7F7F7F`, which is
compatible with persistence across CAM or VM restarts, but that startup was not
performed as a controlled persistence test. No USB capture is claimed for the
reconnection observation.

## Shared controls

When an effect exposed speed, its qualitative track used `Slowest`, `Slow`, `Normal`, `Fast`, and `Fastest`. Direction used the same arrow-style control where present. Some effects exposed LED or pixel size, and some exposed a movement switch.

Brightness was enabled for some effects and disabled for others. It may represent opacity or intensity in some modes, but that is an **inference**, not a verified semantic meaning.

## Reported effect matrix

All rows in this table are **reported manual observations** for the tested board and channel. The controls listed as absent were not observed in this exploration. They are not proof that another CAM version cannot expose them.

| Effect | Brightness | Colors | Speed | Direction | Size | Movement | Reported behavior |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `Fixed` | Active | One global color or per-zone customization | No | No | No | No | Static color |
| `Spectrum Wave` | Disabled | Automatic | Yes | Yes | No | No | Continuous rainbow |
| `Breathing` | Active | Up to 8 observed | Yes | No | No | No | Alternates colors with a dark or off phase |
| `Fading` | Active | Up to 8 observed | Yes | No | No | No | Transitions between colors without turning off between them |
| `Covering Marquee` | Active | Up to 8 observed | Yes | Yes | No | No | New color appears to paint over the previous one. The map was informative, not editable |
| `Monitor Temperature` | Active | Preset or custom gradients | No | No | No | No | Source selector offered Core Ultra 7 and Red Hat Virtual GPU Controller. Visible range was 15 C to 90 C. No lower board map was shown |
| `Marquee` | Active | One color | Yes | Yes | LED size | No | A stripe or ray travels across illuminated zones |
| `Pulse` | Active | Up to 8 observed | Yes | No | No | No | Pulses through selected colors |
| `Super Rainbow` | Disabled | Automatic | Yes | Yes | No | No | Smooth multicolor gradient |
| `Audio Bass` | Active | One color | No | No | No | No | Reacted to music played in a browser |
| `Audio Level` | Active | Preset or custom multi-color gradients | No | No | No | No | Reacted to audio level |
| `Rainbow Flow` | Disabled | Automatic | Yes | Yes | No | No | Rainbow flow |
| `Alternating` | Active | Exactly two colors | Yes | Yes | LED size | Yes | Still alternating bands with movement off, travelling bands with movement on |
| `Tai Chi` | Active | Two colors | Yes | Yes | Size control observed | No | Similar to Alternating with smoother blending and motion |
| `Starry Night` | Active | One selected color | Yes | No | No | No | CAM derived a dimmer tone for the twinkle |
| `Rainbow Pulse` | Disabled | Automatic | Yes | Yes | No | No | Dark intervals between rainbow pulses |
| `Candle` | Active | One color | No | No | No | No | Irregular candle-like flicker |
| `Wave` | Active | One color | Yes | Yes | No | No | Exact UI label pending confirmation. No visible physical change occurred in this test even though the map showed a colored region. Possible incomplete channel or broken effect, not a conclusion |
| `Water Cooler` | Disabled | Automatic red and blue | Yes | No | No | No | A red region travelled toward blue and appeared to cool |
| `Loading` | Active | One color | Yes | No configurable direction | No | No | A light or dark segment always travelled in one direction |

## Top profile or theme dropdown

**Reported manual observation:** the top dropdown listed `Default`, `White`, `Spectrum Wave`, `NZXT Purple`, `Red Alert`, `Vaporwave`, `Siren`, and `Audio Level`. Profiles could also be created and named.

| Profile or theme | Observed resulting mode or appearance |
| --- | --- |
| `White` | `Fixed` white, visually light cyan on this board |
| `Spectrum Wave` | Selected `Spectrum Wave` |
| `NZXT Purple` | `Fixed` purple |
| `Red Alert` | Appeared to select red and white `Pulse` |
| `Vaporwave` | Appeared to select `Fixed` blue |
| `Siren` | Appeared to select `Fixed` green |
| `Audio Level` | Selected `Audio Level` |

The conceptual relationship between several theme names and the resulting effect was unclear during this exploration. The table is an observed mapping, not a stable contract.

## HID report structure and write wire format

**Verified from the live HID report descriptor** (`/sys/class/hidraw/hidrawN/device/report_descriptor`, 150 bytes, read-only) and cross-checked against the D12 and D21 captures:

- The controller uses **numbered HID reports**. The descriptor declares explicit Report IDs for both directions.
- Output Report IDs include `10 12 20 22 24 26 2a f2 fe e2 f4`. Input Report IDs include `11 13 21 23 25 27 29 2b e3 f5 ff`. The descriptor declares **no Feature reports**.
- Report Size is 8 and Report Count is 511, so each report is **511 payload bytes plus one Report ID byte, 512 bytes on the wire**.
- The lighting write uses Report ID `0x26` (declared as Output). The captured frame that begins `26 04 20 00 ...` is already the full 512-byte on-wire buffer: the leading `0x26` is the Report ID, not a data byte.
- This also explains why the `22` and `24` opcodes were never seen in captured traffic. They are declared Output Report IDs (`0x22`, `0x24`) that CAM did not exercise in these sessions, not missing data.

This resolves the wire format only. It does not authorize any write. The bytes after the Report ID (the `04` or `06` sub-command, the channel selector, and the color or brightness data) are described in the sections below, and reproducing any of them on the device stays out of scope until a first controlled write is verified with an operator watching the physical LEDs.

## USB observations from D5 and D6

**Verified from artifacts:** separate, isolated captures observed 512-byte interrupt OUT traffic followed by the same `26 06` buffer.

- D5 captured several `26 04` data patterns during a human brightness interaction. It did not establish a reliable byte-to-percentage mapping.
- D6 associated the individual minimum icon with a `26 04 20` prefix followed by a zero-filled data body, then the common `26 06` buffer.
- D6 associated the individual maximum icon with `26 04 20 00` followed by 147 bytes of `fe`, then the same `26 06` buffer.
- The maximum-icon payload matched the final maximum-state payload observed in the D5 restoration.

This is a strong correlation for these observed icon actions, board, CAM version, and channel. It is not a universal protocol semantic, a proof of channel encoding, or permission to replay packets. Writing or reproducing these buffers is unsafe until further differential captures establish a broader model.

## USB observations from D7, D8, D9 and D11 exact brightness points

**Verified from PCAP:** twelve distinct brightness percentages for the same N9, Channel 6, and device address each contain one 512-byte interrupt OUT `26 04 20 00`, 147 repetitions of the level byte, zero-filled padding after that region, and one associated following `26 06` buffer. D9 adds an independent repeat of the 2% point. Its full 512-byte `26 04 20 00` payload is byte-for-byte identical to D8 2%, including `26` repeated 147 times and the zero-filled remainder. The D8, D9, and D11 analyses classified traffic as target traffic only after an exact bus 3 and address 6 match, so traffic from other devices on the captured bus was retained as contamination rather than counted as a lighting action.

| Reported percentage | Series | PCAP level byte | Confidence |
| ---: | --- | --- | --- |
| 0% | D7 | `00` | High for the PCAP byte, medium for reported percentage |
| 1% | D7 | `19` | High for the PCAP byte, medium for reported percentage |
| 2% | D8 | `26` | High for the PCAP byte, medium for reported percentage |
| 2% repeat | D9 | `26` | High for the PCAP byte, medium for reported percentage |
| 7% | D11 | `4a` | High for the PCAP byte, medium for reported percentage |
| 10% | D8 | `59` | High for the PCAP byte, medium for reported percentage |
| 25% | D8 | `88` | High for the PCAP byte, medium for reported percentage |
| 49% | D7 | `b9` | High for the PCAP byte, medium for reported percentage |
| 50% | D7 | `bb` | High for the PCAP byte, medium for reported percentage |
| 75% | D8 | `e0` | High for the PCAP byte, medium for reported percentage |
| 90% | D7 | `f2` | High for the PCAP byte, medium for reported percentage |
| 99% | D7 | `fd` | High for the PCAP byte, medium for reported percentage |
| 100% | D7 | `fe` | High for the PCAP byte, medium for reported percentage |

**Reported manual observation:** the D7 1%, 49%, 50%, 90%, 99%, and 100% points came from the stated focused-keyboard procedure. The 99% capture followed a separately counted preparation from 90% to 98% while capture was stopped. The evidence does not state whether a focus click occurred for the 99% or 100% capture. D8 has one private human-action JSON for each point, sourced from the operator's manual session report rather than an automatic CAM read. The records state the reported start and target, the preparation outside capture, the focus-recovery click, one Right Arrow, and tooltip confirmation. They do not invent interaction timestamps. D9 has a separate private report that CAM was prepared at 1% outside capture, then a click on the slider thumb recovered focus, one Right Arrow was pressed, and hover confirmed 2%. D11 has a separate private report that CAM was prepared at 6% outside capture, then a click on the slider thumb recovered focus, one Right Arrow was pressed, and hover confirmed 7% without further clicks. These reports are not automatic CAM reads and do not invent interaction timestamps.

**Verified from PCAP:** each D7, D8, D9, and D11 sample has one target write and one associated `26 06` buffer. In the D7 samples documented as one focused Right Arrow action, that action produced one target write in its isolated window. For D7, a recovery click on the current slider value before the arrow action did not add a target write in the 49%, 50%, and 90% captures. This supports a limited observation that same-value recovery clicks did not generate target writes in those tests, not a general UI guarantee. The focused Right Arrow action is the documented one-percentage-point procedure. The D8 human-action records are checked against the PCAP for one target write, its repeated byte, and no additional target write from the focus-recovery click within the isolated window. This is a limited observation for these captures, not a general UI guarantee.

**Verified from PCAP:** keyboard 100% is byte-for-byte identical to the D6 maximum-icon write, including its 147 `fe` level bytes and associated `26 06` buffer.

**Model and uncertainty:** D7's candidate was sRGB IEC 61966-2-1 with `x = percentage / 100`, scale 254, and nearest half-up rounding. It fit the seven D7 values, but D8 2% measures `26` where that candidate predicts `27`. D9 independently repeats the same complete payload and `26` byte at reported 2%. D11 measures `4a` at reported 7%, where that candidate predicts `4b`. This refutes the exact sRGB rule at a second percentage, but does not confirm an alternative quantizer or a protocol model. Standard sRGB variants using scale 254 or 255 with floor, ceil, nearest half-up, or banker's rounding do not fit all twelve measured points. Quantized-input sRGB variants and tested simple power curves also do not fit all twelve points.

A non-standard fitted quantizer such as `floor(254*sRGB(x)+t)` remains compatible with all twelve points for a range of `t`. Its prediction at 7% is `4a`, so D11 supports that family against the exact sRGB candidate. An unconstrained integer lookup table can copy the points by construction. These are compatible explanations, not evidence that CAM uses either one. The data do not identify a unique conversion or exclude a discrete table. The repeated byte remains a measured field correlation, not confirmed protocol semantics or a safe write specification.

## USB observation from D12 global Fixed color change

**Reported manual observation:** outside the capture, Channel 6 was `Fixed`, at 7% brightness, with per-zone customization disabled and global white `#FFFFFF`. White was already the selected default, so there was no additional white selection. During the capture, the global picker was opened and the red preset was selected once. CAM displayed `#FF0000` and the board was seen red. No brightness, effect, or per-zone change was reported. This report contains no interaction timestamps, and the visual observation is not colorimetry.

**Verified from PCAP:** D12 has one target `26 04 20 00` interrupt OUT write, followed by one `26 06` write 3.975 ms later with no target OUT write between them. The target requires the exact bus 3 and address 6 match. The `26 04 20 00` body is not the uniform brightness pattern from D7 through D11. Its 147-byte active region is 49 repetitions of `00 4a 00`, followed by 361 zero bytes. Against D11's 7% white-brightness capture with the same header, 98 active-region bytes differ. D11 has `4a` in all three positions of each group, while D12 keeps `4a` in the second position and zero in the first and third.

This is a limited correlation for the observed board, CAM release, Channel 6, `Fixed`, reported 7% brightness, and reported white-to-red action. If the three bytes were interpreted as `RGB` or `BGR`, the nonzero component would be G, not R. `GRB` and `BRG` are permutations that would place R in the second position. One transition does not confirm any byte order, RGB encoding, LED count, channel index, command semantics, or a safe write format. The ordering and proximity of the two writes do not attribute either one to opening the picker or selecting red. Do not reproduce these buffers.

## USB observation from D13 global Fixed color change

**Reported manual observation:** the starting state was Channel 6, `Fixed`, 7% brightness, per-zone customization disabled, and global red `#FF0000`. During the capture, the global picker was opened and the blue preset was selected once. CAM displayed `#0000FF` and the board was seen blue. No other change was reported. This report contains no interaction timestamps, and the visual observation is not colorimetry.

**Verified from PCAP:** D13 has one target `26 04 20 00` interrupt OUT write, followed by one `26 06` write 2.054 ms later with no target OUT write between them. The target requires the exact bus 3 and address 6 match. The active region is 49 repetitions of `00 00 4a`, followed by 361 zero bytes. D13 differs from both D12 red and D11 white at 7% in 98 active-region bytes. The header, active-region length, 49 triple repetitions, and zero padding are unchanged.

**Inference:** if each three-byte group represents color components in its observed byte order, D12 places reported red in the second position and D13 places reported blue in the third. This distinguishes the two candidates left by D12 and favors `GRB` over `BRG`. Under `GRB`, the first position is G, the second is R, and the third is B. This inference depends on the color-component assumption.

**Unknown:** these captures do not independently prove that the triples are RGB components, that each triple represents one physical LED, that there are exactly 49 LEDs, that the channel is encoded in this frame, or that `26 04 20 00` has a safe write semantic. Do not reproduce these buffers.

## D14 autonomous custom-green attempt

**Verified from private screenshots and action records:** D14 passed its preflight and opened CAM's `CUSTOM` color dialog from an initial global `#0000FF` state. The dialog exposed Hex, R, G, and B fields plus `Swatch` and `Cancel`, but no separate apply button. Entering exact `#00FF00` changed the dialog to R0 G255 B0 and updated the Channel 6 color chip immediately.

**Capture status:** blocked by the test's own safety condition. The USB capture had not started because the intended sequence required preparing the exact value without applying it, then applying it once under capture. CAM instead applied the color while the hex field was being edited. No D14 PCAP exists, so this attempt provides UI behavior evidence only and does not test the predicted `4a 00 00` USB structure. The physical tower response was not observed by camera.

The later D15 test used direct Hex entry with the capture active and retained every write in the window. D14 did not restore blue and left CAM displaying `#00FF00`.

## D14b guest-clipboard attempt

**Verified from private screenshots and action records:** D14b tested whether QEMU Guest Agent could place `0000FF` in the interactive Windows clipboard before a single paste into CAM. The clipboard written by QGA's PowerShell process did not reach CAM's graphical session. After selecting the Hex field and sending one paste outside capture, the field was empty while CAM's R0 G255 B0 state and green map remained unchanged.

**Capture status:** blocked before capture. No D14b PCAP exists and no physical response was observed by camera. The failed paste demonstrates a Windows session boundary for this method, not a USB behavior. A later attempt must validate clipboard delivery through the active SPICE desktop session before starting any capture.

## D14c host-to-guest SPICE clipboard attempt

**Verified from private screenshots and runtime records:** D14c preserved the host clipboard without logging its content, confirmed the SPICE channel and Windows guest agents, and attempted to restore `#0000FF` through the host Wayland clipboard. The first attempt contained a trailing newline. A corrected six-byte `0000FF` host value was then verified by size and hash. Neither paste reached CAM. The Hex field became empty while the R0 G255 B0 state and green map remained unchanged.

**Capture status:** blocked before capture. No D14c PCAP exists. The original host clipboard restoration performed by the worker failed because its backup was itself a test value and the private file was removed too early. The orchestrator recovered the most recent Klipper text item preceding the two test entries, without exposing its content, and verified its 165-byte size and SHA-256 after restoration. This selection is based on history ordering and is recorded privately. Clipboard-dependent CAM tests are no longer recommended for this environment.

## USB observation from D15 direct Hex color change

**Verified from private screenshots, action records, and PCAP:** D15 began with Channel 6 in `Fixed` at reported 7% brightness and per-zone customization disabled. Outside the capture, direct Hex entry restored blue `#0000FF`, with CAM showing R0 G0 B255 and a blue board map. The Hex field was then selected in full. With one `usbmon3` capture active, the six keys `0`, `0`, `f`, `f`, `0`, and `0` were entered. CAM ended at green `#00FF00`, with R0 G255 B0 and a green board map. The physical tower response was not observed because no camera was available.

The archived PCAP has SHA-256 `c8beb788477ca83f02dd8d9e4dd967ec1f7759523df93019b45df53476087eb3`, 18540 bytes, and 104 frames. Exact bus 3 and address 6 filtering leaves two outgoing target writes. Frame 97 is the only `26 04 20 00` write. Its active region is 49 repetitions of `4a 00 00`, followed by 361 zero bytes. Frame 101 is a `26 06` write 1.931 ms later, with no target OUT write between them. No intermediate `26 04 20 00` write appeared for the individual Hex characters in this capture.

At the same reported 7% brightness, the four controlled colors now compare as follows:

| Reported color | Series | Repeated triple |
| --- | --- | --- |
| White `#FFFFFF` | D11 | `4a 4a 4a` |
| Red `#FF0000` | D12 | `00 4a 00` |
| Blue `#0000FF` | D13 | `00 00 4a` |
| Green `#00FF00` | D15 | `4a 00 00` |

**Inference:** under the still-unproven color-component interpretation, D15 fills the position that D12 and D13 left unresolved and independently supports `GRB` byte order. The four captures do not prove one triple per physical LED, an exact LED count, a channel field, safe write semantics, or that other effects use the same layout. Do not reproduce these buffers.

## USB observation from D16 mixed Fixed color

**Verified from private screenshots, action records, and PCAP:** D16 began from green `#00FF00` with the complete Hex value selected. One `usbmon3` capture was active while the six keys `f`, `f`, `0`, `0`, `f`, and `f` were entered without clicks or other key events. CAM ended at magenta `#FF00FF`, with R255 G0 B255 and a magenta board map. Channel 6 remained in `Fixed`, at reported 7% brightness, with per-zone customization disabled. The physical tower response was not observed because no camera was available.

The archived PCAP has SHA-256 `b74abea4553b11e3435a9e338ed7d51ba12a07ac548e7b251ccf1bcd3d02c57a`, 21104 bytes, and 112 frames. Exact bus 3 and address 6 filtering leaves 24 target frames and two outgoing target writes. Frame 105 is the only `26 04 20 00` write. Its active region is 49 repetitions of `00 4a 4a`, followed by 361 zero bytes. Frame 109 is a `26 06` write 2.020 ms later, with no target OUT write between them.

Nanosecond timestamps place the color frame 405.645262 ms after the timestamp before the first key and 268.491123 ms after the timestamp recorded after the sixth key. This proves that the observed frame followed the complete six-key sequence in this window. It does not attribute the frame to an individual key.

Compared with the four 7% primary captures, D16 differs by 49 active bytes from white `4a 4a 4a`, 49 from red `00 4a 00`, 49 from blue `00 00 4a`, and 147 from green `4a 00 00`. The header, 512-byte length, 147-byte active region, 49 triples, and 361-byte zero padding remain unchanged.

**Inference:** if the triples encode color components, magenta activates reported red in the second position and reported blue in the third while leaving reported green in the first position at zero. This mixed-color result supports the same `GRB` interpretation as the primary captures and shows a combination compatible with two active components. It still does not prove USB write semantics, one triple per physical LED, a channel field, or safe packet reproduction.

## USB observation from D17 non-binary mixed Fixed color

**Verified from private screenshots, action records, and PCAP:** D17 began from magenta `#FF00FF` with the complete Hex value selected. One `usbmon3` capture was active while the six keys `8`, `0`, `4`, `0`, `2`, and `0` were entered without clicks or other key events. CAM ended at `#804020`, with R128 G64 B32 and a brown board map. Channel 6 remained in `Fixed`, with per-zone customization disabled. The prior reported brightness was 7%, but D17 did not independently display that percentage. The physical tower response was not observed because no camera was available.

The archived PCAP has SHA-256 `01ff85f7b8eb32d063ce11cd8f375f5fe9d080ee041f6344c1be39809cca2a19`, 19388 bytes, and 110 frames. Exact bus 3 and address 6 filtering leaves 18 target frames and two outgoing target writes. Frame 97 is the only `26 04 20 00` write. Its active region is 49 repetitions of `0c 21 03`, followed by 361 zero bytes. Frame 101 is a `26 06` write 2.880 ms later, with no target OUT write between them.

Nanosecond timestamps place the color frame 371.038897 ms after the timestamp before the first key and 266.934109 ms after the timestamp recorded after the sixth key. This establishes that the frame followed the complete six-key sequence in this capture window. It does not attribute the frame to an individual key.

Under the still-unproven `GRB` color-component interpretation, the measured triple associates reported G64 with `0c`, R128 with `21`, and B32 with `03`. All three positions are distinct and nonzero. A naive linear projection from each component through the observed 7% full-component value `4a` predicts `12 25 09`, which does not match `0c 21 03`. The result is compatible with a nonlinear component transform, but one mixed point does not identify a unique formula, quantizer, or lookup table. It also does not establish USB write semantics, physical LED correspondence, channel encoding, or safe packet reproduction.

## USB observation from D18 repeated non-binary color

**Verified from private screenshots, action records, and PCAP:** D18 prepared magenta `#FF00FF` outside capture, selected the complete Hex value, and repeated the direct six-key entry `804020` inside one `usbmon3` capture. CAM again ended at `#804020`, with R128 G64 B32 and a brown board map. Channel 6 remained in `Fixed`, with per-zone customization disabled. A no-click hover over the individual brightness thumb did not expose a legible tooltip, so 7% remains a prior reported value rather than an independent D18 reading. The physical tower response was not observed.

The archived PCAP has SHA-256 `36922225d39a5ad185cb7c7d459ab4539a7e5bde02dce2ee4eb079fa5a4d7267`, 18452 bytes, and 98 frames. Exact bus 3 and address 6 filtering leaves 18 target frames and four outgoing target writes. Two are `26 04 20 00` color candidates, each followed by `26 06`.

- Frame 81 contains 49 repetitions of `00 23 0d`, followed by 361 zero bytes. It occurred after the timestamp before the fourth key and before the timestamp before the fifth key.
- Frame 89 is the final candidate and contains 49 repetitions of `0c 21 03`, followed by 361 zero bytes. It occurred 309.028115 ms after the timestamp recorded after the sixth key.

The complete 512-byte final frame from D18 is byte-for-byte identical to D17. Its payload SHA-256 is `166c8c2ffc6de4e3bc864814aa475c304c79246796e2a3dbee5fb6131163190a`. This establishes reproducibility for the final captured state across these two runs.

**Inference:** the first D18 candidate appeared while the entered text had progressed through the first four characters, `8040`, and before the fifth. Its `00 23 0d` triple is compatible with a temporary shorthand-color interpretation, but no screenshot was taken at the exact USB-frame instant and the capture does not prove the parser rule. The final frame remains the only candidate associated with the visually confirmed six-character `#804020` state.

## USB observation from D19 permuted non-binary color

**Verified from private screenshots, action records, and PCAP:** D19 began from `#804020`, with R128 G64 B32 and the complete Hex value selected. One uninterrupted six-key sequence entered `408020` inside a single `usbmon3` capture. CAM ended at `#408020`, with R64 G128 B32 and a green board map. Channel 6 remained in `Fixed`, with per-zone customization disabled. The physical tower response was not observed.

Before capture, the stated prediction under the combined `GRB` and shared component-transform hypotheses was 49 repetitions of `21 0c 03`. This prediction was recorded as contrastable evidence and was not used as a success condition.

The archived PCAP has SHA-256 `9a6c2153e8c6a2d462ee5198a0f3f0b4474bd258a66d8ff352afbdf846bf469a`, 15780 bytes, and 94 frames. Exact bus 3 and address 6 filtering leaves ten target frames and two outgoing target writes. Frame 76 is the only `26 04 20 00` write. Its active region is 49 repetitions of `21 0c 03`, followed by 361 zero bytes. Frame 80 is a `26 06` write 2.963 ms later.

Nanosecond timestamps place the color frame 399.404229 ms after the timestamp before the first key and 256.495532 ms after the timestamp recorded after the sixth key. No intermediate color write appeared in this short uninterrupted sequence.

Compared with D17 and D18, D19 exchanges the first two measured bytes, `0c 21 03` to `21 0c 03`, while preserving the third. This exactly matches the prior permutation prediction. Under the still-unproven color-component interpretation, G128 maps to `21` in the first position, R64 maps to `0c` in the second, and B32 remains `03` in the third. This strengthens both `GRB` ordering and a shared component transform for these measured values. It does not identify a unique transform, prove packet semantics, establish physical LED correspondence, encode a channel, or make replay safe.

## USB observation from D20 second magnitude set

**Verified from private screenshots, action records, and PCAP:** D20 began from `#408020`, with R64 G128 B32 and the complete Hex value selected. One uninterrupted six-key sequence entered `c08040` inside a single `usbmon3` capture. CAM ended at `#C08040`, with R192 G128 B64 and an orange board map. Channel 6 remained in `Fixed`, with per-zone customization disabled. The physical tower response was not observed.

Two predictions were recorded before capture. The empirical partial prediction was `21 ?? 0c`, because G128 and a component magnitude of 64 had already produced `21` and `0c`. A separate refutable candidate, standard sRGB decoding, multiplication by 0.07 in linear light, sRGB encoding, and nearest-integer rounding, predicted the complete triple `21 36 0c`. Neither prediction was a capture success condition.

The archived PCAP has SHA-256 `1aa25806711bfa4bfa3d01f21cfa7ac7282b289979ee3a31259e623f213e4508`, 19896 bytes, and 110 frames. Exact bus 3 and address 6 filtering leaves 18 target frames and two outgoing target writes. Frame 103 is the only `26 04 20 00` write. Its active region is 49 repetitions of `21 36 0c`, followed by 361 zero bytes. Frame 107 is a `26 06` write 1.988 ms later.

The empirical partial prediction and the complete sRGB candidate both coincide with D20. The new R192 magnitude maps to `36`. G128 repeats `21`, and magnitude 64 repeats `0c` across a different component position. Across D17 through D20, the same sRGB candidate at an exact 7% reproduces the observed non-maximum component mappings 32 to `03`, 64 to `0c`, 128 to `21`, and 192 to `36`. It predicts `4b` for a full 255 component, while the independently repeated 7% maximum-component observations are `4a`. The candidate therefore does not explain the full measured set without an additional quantization or normalization detail. No unique transform is established.

## USB observation from D21 quantization boundary

**Verified from private screenshots, action records, and PCAP:** D21 began from `#C08040`, with R192 G128 B64 and the complete Hex value selected. One uninterrupted six-key sequence entered `7f7f7f` inside a single `usbmon3` capture. CAM ended at uniform gray `#7F7F7F`, with R127 G127 B127 and a gray board map. Channel 6 remained in `Fixed`, with per-zone customization disabled. The physical tower response was not observed.

D21 was chosen before measurement to distinguish two specific candidates. Standard sRGB decoding, multiplication by exactly 0.07 in linear light, encoding, and nearest-integer rounding predicts `21 21 21`. The same transform with an effective multiplier in the approximately 0.0687 to 0.0694 range that remained compatible with earlier levels predicts `20 20 20`. Neither prediction was a success condition or an exhaustive model set.

The archived PCAP has SHA-256 `4b66a0865468247cbf394c0038bce98b026f86b0a4cbc4c1528927331a96004c`, 17188 bytes, and 100 frames. Exact bus 3 and address 6 filtering leaves ten target frames and two outgoing target writes. Frame 91 is the only `26 04 20 00` write. Its active region is 49 repetitions of `20 20 20`, followed by 361 zero bytes. Frame 95 is a `26 06` write 3.032 ms later.

The exact 0.07 candidate is refuted at input 127, while the nearby effective-multiplier candidate coincides. Within the stated sRGB decode, multiply, encode, and nearest-rounding family, the combined component observations at inputs 32, 64, 127, 128, 192, and 255 are compatible with an effective multiplier from approximately 0.0687555 through 0.0694154. This is a fitted compatible interval, not evidence that CAM implements that formula. A discrete lookup table or another quantizer remains possible.

D21 also establishes an adjacent threshold in the observed output: input 127 maps to `20`, while input 128 maps to `21` in D17 through D20. This does not establish behavior for unmeasured inputs or other brightness values.

## USB observation from D22 mixed color at 50 percent

**Verified from the controlled operator action and PCAP:** outside capture, CAM
was prepared in global `Fixed` with per-zone customization disabled, color
`#5A23F4`, and the individual Channel 6 brightness at 49 percent. After the
capture was explicitly confirmed active, the operator pressed Right Arrow once
on that slider. CAM displayed 50 percent, and the operator confirmed normal fan
operation. No other CAM action was reported during the capture.

D22 was chosen before measurement to attempt to refute a unified color and
brightness candidate. For each input component `v` and brightness `b`, the
candidate computes
`floor(254 * srgb_encode(srgb_decode(v / 255) * b) + t)`. All earlier measured
points were compatible with `t` from approximately `0.306365377` through
`0.467255293`. At `#5A23F4` and 50 percent, that interval allowed only four GRB
triples: `16 3f b2`, `16 40 b2`, `17 40 b2`, or `17 40 b3`.

The archived PCAP has SHA-256
`ac1c98f39e5faa69f6c684ecd8c7a90181438a18a6566a2b5fdacf627efe5f11`,
5141 packets, and a duration of 48.744236 seconds. Exact bus 3, address 7, and
endpoint `0x02` filtering leaves only two outgoing writes with data. Frame 2747
is the only `26 04 20 00` write. Its active region is 49 repetitions of
`17 40 b2`, followed by exactly 361 zero bytes. Frame 2751 is the `26 06`
commit 3.931 ms later. Both completion records have status zero. No target
packet is truncated or malformed.

The observed triple is exactly the third pre-recorded prediction. Within this
candidate family, D22 narrows the compatible interval to approximately
`0.386776218` through `0.427698800`. This is the first controlled mixed-color
cross-check away from 7 percent, so it strongly supports separability of color
and brightness in the candidate. It does not prove that CAM implements this
formula or exclude a lookup table or another quantizer that agrees at the
measured points.

## USB observation from D24 mixed color at 25 percent

**Verified from the controlled operator action and PCAP:** outside capture, CAM
was prepared in global `Fixed` with per-zone customization disabled, color
`#0E50AD`, and the individual Channel 6 brightness at 24 percent. After the
capture was explicitly confirmed active, the operator pressed Right Arrow once
on that slider. CAM displayed 25 percent, and the operator confirmed normal fan
operation. No other CAM action was reported during the capture.

D24 was chosen before measurement as a second cross-check at a brightness far
from both 7 and 50 percent. Within the interval retained by D22, the unified
candidate allowed only four final GRB triples: `26 03 5a`, `26 04 5a`,
`27 04 5a`, or `27 04 5b`.

The archived PCAP has SHA-256
`9c943091a9461eaa180a6b5702c218f679c98f5b3e0c8f633f10e8d8ac06df06`,
27752 packets, and a duration of 218.792628 seconds. Exact bus 3, address 7,
and endpoint `0x02` filtering leaves only two outgoing writes with data. Frame
25681 is the only `26 04 20 00` write. Its active region is 49 repetitions of
`27 04 5b`, followed by exactly 361 zero bytes. Frame 25685 is the only
`26 06` commit, 2.982 ms later. Both completion records have status zero. No
target packet is truncated or malformed.

The observed triple is exactly the fourth pre-recorded prediction. Within this
candidate family, D24 narrows the compatible interval to
`0.4173921478326008 <= t < 0.4276988003512372`. The candidate has now survived
controlled mixed-color cross-checks at both 25 and 50 percent in addition to
the earlier color and brightness series. This supports a predicted Linux write
as the next falsification step. It still does not prove CAM's internal
implementation or exclude another function that agrees at all measured points.

## D25 predicted Linux write at 40 percent

**Verified from the reviewed code, offline tests, command output, and operator
observation on 2026-07-21:** the unified D1-D24 candidate generated a previously
uncaptured global `Fixed` state, `#FFD000` at 40 percent. The predicted wire
triple was `89 a9 00` in GRB order. The complete 512-byte `26 04` frame had
SHA-256 `c8e1db05b544d92df8815e82e64dba2d23aa92f71d50861b58eba368b6d62138`.
The frame was frozen into the closed laboratory harness before the physical
test.

The implementation checkpoint `65be58601a28d979ad5f4a5987f202452f968846`
passed 35 offline tests and an independent read-only review with no findings.
The tests cover nine captured colors at 7 percent, twelve captured white
brightness points, D22, D24, frame structure, the fixed commit, token gating,
identity failures, and absence of a hidraw open during preflight. The checkpoint
was integrated locally into master as `c449850` without push.

The N9 resolved as `/dev/hidraw2` through the exact HID identity and the
150-byte descriptor. A first unprivileged invocation failed with permission
denied before opening the device and wrote zero bytes. The same reviewed command
was repeated through non-interactive sudo. With CPU Package at 62 C, Linux wrote
the frozen yellow data frame and the known commit. The operator observed an
immediate yellow or golden physical result and confirmed that all fans continued
spinning normally.

Linux then sent the captured white frame at 7 percent with CPU Package at 75 C.
The operator confirmed the customary cyan appearance and normal fan operation.
After the N9 was reattached to the still-running VM, CAM automatically reapplied
its remembered `#0E50AD` state at 25 percent, also confirmed by the operator.

This physically validates construction of a previously uncaptured global
`Fixed` color and brightness from the unified model. Together with D1-D24, it is
sufficient engineering evidence to implement a Linux global `Fixed` controller
with arbitrary RGB input and integer brightness from 0 through 100. It does not
prove CAM's internal algorithm and does not cover per-zone or per-LED `Fixed`
customization.

## Supervised Linux write and restoration

**Harness:** the closed laboratory tool is
`tools/nzxt-n9/bin/nzxt-n9-first-write-lab`. It only exposes `preflight`,
`apply-red`, `apply-model-yellow40`, `restore-white`, and help. Frames are
frozen (D12 red at 7%, D25 model yellow at 40%, D11 CAM white at 7%, and the
observed `26 06` commit). It is not a generic write API and is not installed by
the packaging paths.

**Verified by the operator on 2026-07-21:** the closed Linux harness resolved
the N9 as `/dev/hidraw4` through HID_ID `0003:00001E71:00002023`, checked the
150-byte report descriptor with Output Report ID `0x26`, and sent the frozen
D12 red frame followed by the captured `26 06` commit. The motherboard cover
lighting changed immediately to dim red. Radiator fan rings and RAM lighting
retained their previous states. The operator confirmed that all fans continued
spinning with no perceived change.

The harness then sent the frozen D11 CAM `#FFFFFF` frame and the same commit.
The motherboard zones returned immediately to their customary dim cyan. CAM
labels this state as white, while its physical appearance on this board is
consistently cyan. The operator confirmed that this is the customary default
appearance and is not caused by the viewing angle or the photograph. Red is
rendered reasonably close to the expected color. No full tower restart was
needed.

The CPU package was 66 C before the first write. Samples during the complete
cycle ranged from 47 C to 75 C, below the 85 C abort gate. After restoration,
the N9 remained enumerated with the expected HID identity and descriptor.

A separate read-only attempt received no `ff 03` heartbeat within a five-second
window and ended by timeout. This does not prove that heartbeat emission
stopped, but it cannot be counted as a successful post-write heartbeat check.
Physical restoration, USB enumeration, descriptor identity, and temperature
were independently confirmed.

This proves a physical and reversible Linux lighting write for the observed
motherboard zones. The complete red and restore cycle was then repeated from
the restored cyan state. The second red appeared immediately with all other
observed behavior normal, and the second restoration returned immediately to
the customary cyan. The second cycle began at a CPU package temperature of 49
C, measured 50 C after red, and measured 69 C after restoration. This proves
physical repeatability across two cycles. It does not map the 49 GRB triples to
49 physical LEDs or individual zones.

The frozen white frame uses equal component values, `4a 4a 4a`. The observed
cyan bias therefore does not come from unequal bytes in the transmitted frame.
LED spectral response, electrical channel calibration, the optical diffuser,
or low-brightness channel behavior are compatible explanations, but none has
been measured yet.

## Anomalies and open questions

**Reported manual observation:** while changing effects or profiles, radiator fan lighting and possibly pump lighting stopped being visible. Only RAM and motherboard lighting remained visible.

- The exact triggering action was not identified.
- Switching later profiles did not restore those lights.
- The operator later visually confirmed that the radiator fans were still spinning while their lighting remained off.
- Pump operation was not established by this visual check.
- A later CPU reading of 73 C and GPU reading of 42 C did not prove fan RPM or pump operation.

The observed anomaly is therefore limited to lighting for the radiator fans. The pump lighting status and pump operation remain uncertain. Before drawing a broader hardware conclusion, identify whether the AIO or radiator fans belong to Channel 6, another ARGB header, or another controller, and reproduce only with a prepared capture and safety monitoring.

## Recommended next capture matrix

Do not run these captures concurrently. Change one visible variable per window, record the starting state, confirm the ending tooltip or UI state, and restore the baseline in a separate window.

| Priority | One variable | Controlled states or action | Required confirmation |
| --- | --- | --- | --- |
| 1 | Independently visible brightness | Establish a fresh exact percentage using the verified focused-arrow method before another color capture | Tooltip before and after, one isolated target write, and no reliance on a prior reported percentage. Automated QMP hover did not expose the tooltip in D18 |
| 2 | Same color at another exact brightness | Repeat one non-binary color only after the percentage is visibly confirmed | Test whether the fitted component transform changes with brightness as predicted, without assuming the 7% fit generalizes |
| 3 | Per-zone color | One known map region, one color change | Region selection and unchanged global remainder |
| 4 | Effect selection | `Fixed` to one effect, then restore `Fixed` | Exact effect label and physical result |
| 5 | Speed | One step only on a single effect | Visible speed label before and after |
| 6 | Direction | One arrow selection only on a single effect | Visible direction before and after |

Physical appearance claims require explicit operator observation. Automated screenshots can verify CAM state only. No packet replay should be attempted from this matrix.

## Protocol opcode map

**Verified from PCAP and the live HID report descriptor:** across the captured CAM sessions the observed exchange between CAM and the N9 used a small set of opcodes. Each 512-byte report begins with its HID Report ID, and that Report ID together with the next byte forms the two-byte opcode shown below (for example Report ID `0x26` with `0x04` is the `26 04` lighting write). Every inbound report carried a 12-byte session or serial token right after the opcode, so the opcode plus that token form the recognizable header of each reply. The table below lists only opcodes that were actually seen in traffic (verified) plus the periodic heartbeat and the generic acknowledgment as they were observed (also verified from the captures). Report IDs that the descriptor declares but that CAM never exercised are listed separately as declared only, so they are not confused with observed behavior.

Status meaning in this table:

- **Verified** means the opcode and its direction were seen in at least one saved capture.
- **Observed** means the opcode was seen but its full field semantics past the opcode itself stay uncertain.

| Opcode | Direction | Meaning | Status |
| --- | --- | --- | --- |
| `10 02` | OUT, host to controller | Firmware information request | Verified |
| `11 02` | IN, controller to host | Firmware information reply to `10 02` | Verified |
| `20 03` | OUT, host to controller | Channel and accessory information request | Verified |
| `21 03` | IN, controller to host | Channel and accessory information reply to `20 03` | Verified |
| `26 04` | OUT, host to controller | Lighting data write | Verified |
| `26 06` | OUT, host to controller | Lighting commit that follows a `26 04` write | Verified |
| `ff 01` | IN, controller to host | Generic acknowledgment that echoes the recognized opcode, observed after `20 03`, after `26 04`, and after `26 06` | Verified |
| `ff 03` | IN, controller to host | Periodic heartbeat about every 3 seconds carrying a frame counter, with no telemetry payload | Verified |

**Verified from the descriptor, not observed in traffic:** the report descriptor also declares Output Report IDs `12 22 24 2a f2 fe e2 f4` and Input Report IDs `13 23 25 27 29 2b e3 f5` that CAM did not exercise in any captured session. Their existence is a descriptor fact. Their meaning is **unknown** because no capture drove them.

**Unknown, and important for the cooling goal:** none of the current captures contains real temperature telemetry or fan RPM telemetry. The `ff 03` heartbeat carries only a frame counter, not sensor values, and the `Monitor Temperature` lighting effect reads its source from the host, not from a controller telemetry frame. Decoding actual temperature and RPM would require a new capture taken on CAM's Cooling page (fan curves, pump control, sensor readouts), which no session in this document exercised. Do not infer a telemetry opcode from the lighting captures, and do not send any of these opcodes to the device.
