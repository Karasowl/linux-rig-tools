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

Enabling `Customize LED colors` disables the global color selector and displays a board map with 49 individually selectable rectangles. The map is visually confusing because white rectangles blend into the board drawing and CAM initially outlines only the selected rectangle. Deliberate inspection found 17 rectangles down the left edge, 17 across the lower horizontal edge, and 15 down the right edge. Clicking any rectangle opens the same preset and custom color palette.

Turning customization off restores the global `Fixed` state. Turning it on restores a separate saved per-zone state rather than copying the current global color. D26 through D32 below establish the transmitted vector structure and anchor every boundary of the observed `17 + 17 + 15` traversal. The intermediate rectangles were not clicked one by one, so their exact indices follow from the counted contiguous runs and anchored endpoints rather than 49 separate differential captures.

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

## D26 saved per-zone state restoration

**Reported controlled observation:** CAM began in global `Fixed` with
`#0E50AD`, brightness 25 percent, and per-zone customization disabled. During
one isolated capture, the operator enabled per-zone customization once. CAM
immediately displayed a multicolor pattern that had been created during earlier
manual exploration. The operator could not identify every saved color, so the
observation is limited to the visible pattern rather than an invented list of
49 colors. All fans continued spinning normally.

**Verified from PCAP:** D26 contains exactly one 512-byte `26 04 20 00` write
and one fixed `26 06` commit 2.034 ms later. Both USB completions have status 0.
The data frame contains 49 GRB triples and 361 zero padding bytes. Its payload
SHA-256 is
`7496a9fefdcd3938df19afb1fd4439187c10dda206b4ba9a31ce6098a216a736`.
The PCAP SHA-256 is
`11f5bdf243f958d35b822f7fe256c3b95bc22e24aa07d3a14eedf80bda881c5f`.

Forty-three triples are `89 89 89`. The six distinct positions are:

| One-based index | GRB triple |
| ---: | --- |
| 1 | `00 00 89` |
| 3 | `00 00 89` |
| 4 | `7a 89 00` |
| 5 | `32 89 89` |
| 12 | `53 1d 13` |
| 40 | `00 89 27` |

The five distinct positions within indices 1 through 17 match the five colored
segments visible on the left vertical edge. All indices 18 through 34 are
uniform and match the visually uniform lower horizontal edge. Index 40 is the
sixth position within the proposed 35 through 49 group and matches the single
colored segment visible on the right vertical edge. This strongly supports the
physical traversal `17 left + 17 lower + 15 right`, but D26 alone does not prove
every rectangle-to-index correspondence.

D26 contains no `27 04 5b` triple from the preceding global `#0E50AD` state.
Therefore the customization toggle restored a separate complete 49-zone state.
The capture does not determine whether CAM stored that state in its profile, a
cache, or the device. The common customized value `89` is also one level above
the global white value `88` measured at 25 percent in D8. The cause of this
difference remains unknown.

## D27 first per-zone rectangle changed to red

**Reported controlled observation:** with the D26 state intact and
customization still enabled, the first rectangle at the top of the left edge
was selected and its palette was opened outside capture. During D27 the operator
clicked only the pure red preset in the first column of the second palette row.
The operator confirmed that the fans continued spinning normally.

**Verified from PCAP:** D27 contains exactly one 512-byte `26 04 20 00` write
and one fixed `26 06` commit 2.967 ms later. Both USB completions have status 0.
The data payload SHA-256 is
`6e8c6c383e75b2a72d21edbcee8265f4e050ac82585f9fe5e3e990153fbf1d41`.
The PCAP SHA-256 is
`00e2369f901b9fe3ae34a252e4301b0f39c1478a8f25a3707dc79d4bfc69f139`.

Compared byte for byte with D26, only offsets 5 and 6 differ. The first triple
changes from `00 00 89` to `00 89 00`. The other 48 triples, header, zero
padding, and complete commit remain identical. This proves that the first top
rectangle of the left edge maps to triple 1, confirms per-zone red as
`00 89 00` in this saved 25 percent state, and shows that CAM sends the complete
49-zone vector when one rectangle changes.

The result supports the `17 + 17 + 15` traversal and the shared `26 04` frame
format. D27 by itself does not prove each of the remaining 48 rectangle
mappings or a general color and brightness encoder for customized zones. In
particular, the `89` level must not be replaced with the global model's `88`
without further evidence.

## D28 through D32 per-zone boundary anchors

Five additional controlled captures changed one white customized rectangle to
the same pure red preset while preserving the accumulated state from the prior
capture. Each PCAP contains exactly one 512-byte `26 04 20 00` frame, one fixed
`26 06` commit, and successful USB completions. In every comparison, only the
expected triple changed from `89 89 89` to `00 89 00`. The other 48 triples,
header, 361 zero padding bytes, and commit were byte-for-byte identical.

| Series | Human-selected rectangle | Proven one-based triple | PCAP SHA-256 |
| --- | --- | ---: | --- |
| D27 | Top of left vertical edge | 1 | `00e2369f901b9fe3ae34a252e4301b0f39c1478a8f25a3707dc79d4bfc69f139` |
| D28 | Bottom of left vertical edge | 17 | `512fba013f19b11aaa11e44e34ec2c878b2c2786782798c7719bdc7d868e5355` |
| D29 | Left end of lower horizontal edge | 18 | `31c990af16339f2979f108d87b81438468337ed8219c23b614ec51832a93a122` |
| D30 | Right end of lower horizontal edge | 34 | `2986ce8e82355aafa9fabc64df5ac299ec69dc8635cd717dd6eeed4849ada002` |
| D31 | Top of right vertical edge | 35 | `e72dea4cb584af474887c63b3a8cfcee788a161fe6767b79a7a47a85420cbe0a` |
| D32 | Bottom of right vertical edge | 49 | `fdf9940301e64c78ec70fe009f153af7a9a9c7fd59f6cc85ed2dc8a8a766d4a4` |

The anchors prove these boundaries and directions:

- Triples 1 through 17 traverse the left edge from top to bottom.
- Triples 18 through 34 traverse the lower horizontal edge from left to right.
- Triples 35 through 49 traverse the right edge from top to bottom.

This is sufficient engineering evidence for a 49-zone layout model because
the operator counted the matching number of contiguous rectangles in each run,
D26's saved multicolor pattern aligned with the proposed groups, and every
group boundary was then isolated by a differential capture. It is not 49
independent physical clicks, and it does not prove that each visual rectangle
contains exactly one electrical LED.

All six red selections at 25 percent used `00 89 00`. This confirms a stable
per-zone preset value in the tested state, but it does not resolve why global
white at 25 percent measured `88 88 88` while customized white and full red use
level `89`. A per-zone arbitrary color and brightness model still requires
controlled custom-color and brightness captures.

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

## USB observations from D35 through D38, Spectrum Wave series

**Method.** Four isolated captures on 2026-07-21 and 2026-07-22 examined the
`Spectrum Wave` effect with exactly one human action per capture window and a
passive tail after it: D35 switched `Fixed` to `Spectrum Wave` and stayed
passive for about 174 seconds, D36 stepped speed from `Normal` to `Fast` with
one Right Arrow press, D37 changed direction from right to left with one click,
and D38 repeated D35 after the operator restored `Normal` speed, right
direction, and `Fixed` outside capture. Each window captured the whole usbmon
bus 3 with the N9 `1e71:2023` at device address 7, and target traffic was
isolated by that exact address.

**Verified from PCAP:** every capture contains exactly one 512-byte interrupt
OUT write to endpoint `0x02` and no other host write of any size in its
window. No `26 06` commit was transmitted in any of the four captures. Each
write completed with status 0 and was answered within 2 ms by the known
`ff 01` acknowledgment, which echoed the `2a 04` opcode. The `ff 03` heartbeat
continued at its 3-second cadence with its incrementing frame counter, and
bytes 16 through 511 of every inbound frame in these captures were zero.

The four frames, showing every nonzero byte:

| Series | Action | Bytes 0..5 | Byte 55 | Bytes 58..59 | Post-write silence |
| --- | --- | --- | ---: | --- | ---: |
| D35 | `Fixed` to `Spectrum Wave` | `2a 04 20 20 02 fa` | `00` | `31 03` | 174.0 s |
| D36 | Speed `Normal` to `Fast` | `2a 04 20 20 02 96` | `00` | `31 03` | 64.3 s |
| D37 | Direction right to left | `2a 04 20 20 02 96` | `02` | `31 03` | 19.1 s |
| D38 | Repeat of D35 | `2a 04 20 20 02 fa` | `00` | `31 03` | 75.0 s |

All remaining bytes are zero in all four frames. D36 differs from D35 only at
byte 5, D37 differs from D36 only at byte 55, and D38 is byte-for-byte
identical to D35, verified by comparing the SHA-256 of the extracted 512-byte
payloads.

**Verified by operator observation:** the continuous rainbow started with D35,
visibly accelerated with D36, and reversed its travel with D37, while all fans
kept spinning normally throughout the series.

**Verified conclusion:** for `Spectrum Wave` on this board and CAM release,
CAM transmits a single `2a 04` configuration frame per user action, with no
commit and no further traffic, and the animation keeps running on its own.
The effect is rendered by the controller firmware. CAM does not stream
animation frames in this mode. The absence of a commit is now observed four
times for Spectrum Wave. Extending that absence to other modes that may use
`2a 04` remains an inference until they are captured.

Proposed field map with evidence classification:

- Byte 0 `2a`: declared Output Report ID, now observed in traffic for the
  first time. Its use for this write is **verified**. Reading `2a 04` as the
  general animated-effect configuration family is an **inference**.
- Byte 1 `04`: occupies the sub-command position that `Fixed` uses for `04`.
  Same-role interpretation is an **inference**.
- Byte 2 `20`: matches the value and position of the `Fixed` channel selector
  byte. Channel-selector interpretation is an **inference**.
- Byte 3 `20`: differs from the `00` that `Fixed` carries at this offset. Its
  meaning is **unknown**.
- Byte 4 `02`: constant across the series. Its identity as the `Spectrum
  Wave` mode identifier is an **inference** until a second animated mode is
  captured and shows a different value here.
- Byte 5: speed-related field, **verified** to be the only byte that changed
  on a speed step. Measured `fa` (250) for `Normal` and `96` (150) for
  `Fast`. "Lower is faster" is an **inference** from these two points plus
  the observed acceleration. The field width is **unknown**: byte 6 was `00`
  in both states, which fits either a 1-byte field followed by padding or a
  little-endian 16-bit value. The `Slowest`, `Slow`, and `Fastest` values are
  uncaptured.
- Byte 55: direction-related field, **verified** to be the only byte that
  changed on a direction change. Measured `00` for right and `02` for left.
  The encoding rationale (why `02` and not `01`) and any other valid values
  are **unknown**.
- Bytes 58..59 `31 03`: constant in all four frames. Meaning **unknown**.
  `0x31` is 49 decimal, the `Fixed` zone count, which is a suggestive
  coincidence and nothing more.

These captures decode observations only. They do not establish a general safe
write specification for animated modes. The repository's closed D35 laboratory
may replay only the exact frozen D35 frame in a separately authorized physical
session, with D32 Fixed restoration. No other `2a 04` frame or parameter is
authorized by this evidence.

**Verified by the operator on 2026-07-27:** Linux preflight resolved the N9 as
`/dev/hidraw2`, validated the fixed identity and descriptor with CPU Package at
42.0 C, and did not open hidraw. The closed laboratory then sent the single
frozen D35 frame. The operator observed Spectrum Wave working correctly for 10
seconds with fans and pump remaining normal. The typed D32 Fixed restoration
completed successfully immediately afterward. This physical QA validates only
that exact D35 replay and D32 restore on this board. It does not generalize any
other animated frame, speed, direction, color, or unknown field.

## USB observations from D39 through D51, animated-mode campaign

**Method.** Eight isolated captures on 2026-07-22 completed the enumeration of
CAM's lighting modes and the first field decoding for Channel 6. D39 through
D42 were batch captures: the operator selected the announced modes in order
with pauses longer than 12 seconds and touched no other control, so each write
is attributed by announced order and timestamp. D43 through D45 were targeted
single-variable captures (color list, LED size and direction, brightness and
speed extremes). D46 was an exploratory window with a negative result. D47
through D51 are follow-up captures on 2026-07-25 and 26 that closed the
fields this campaign left open: D47 under the announced single-action
protocol, D48 only partly, D49 with a pre-registered numeric prediction, and
D50 and D51 as confirmation windows with every value pre-registered plus
internal controls. D50a is an aborted exploratory capture kept separately,
whose reconstruction D50 then confirmed. Each carries its own attribution
caveat, recorded below. In the eight 2026-07-22 captures the N9 `1e71:2023`
was device 7 on usbmon bus 3; in D47 through D51, after a VM restart and a
live re-attach, it was device 6 on the same bus. In every capture target traffic
was isolated by exact device address, every host write completed with status
0, and the controller answered each write within 3 ms with the known `ff 01`
acknowledgment echoing the opcode at bytes 14 and 15. Verification for the
D39-D46 material was re-run against the archived PCAPs (SHA-256 checked
against the capture sidecars) by the decoding worker.

**Verified: three observed transport patterns.** The captured modes used
three distinct write patterns, all through 512-byte interrupt OUT reports.
This is not a complete classification of the lighting surface: `Monitor
Temperature` transmitted nothing in its window and its transport pattern
remains **unknown**.

| Pattern | Frames | Modes observed |
| --- | --- | --- |
| Single `2a 04` configuration frame, no commit | 1 per user action | Spectrum Wave, Breathing, Fading, Covering Marquee, Pulse, Super Rainbow, Rainbow Flow, Rainbow Pulse, Water Cooler, Loading, Alternating, Tai Chi, Starry Night, Candle |
| `26 04` data vector plus parameterized `26 06` commit | 2 per user action, 2-3 ms apart | `Fixed` (constant commit), Marquee and Wave (parameterized commit) |
| `26 14` streaming, no configuration frame and no commit | continuous, about every 32 ms | Audio Bass, Audio Level |

### Mode identifier table (byte 4 of the `2a 04` frame)

All identifiers below were measured in traffic. Modes captured in one window
remain single observations. The speed column is the little-endian uint16 at
bytes 5 and 6 as transmitted, which is CAM's remembered per-mode speed state,
with UI labels noted only where the operator confirmed them.

| Mode | ID | Windows observed | Speed seen | Colors (byte 56) | Byte 55 | Byte 57 | Bytes 58-59 |
| --- | ---: | --- | --- | ---: | --- | --- | --- |
| `Fading` | `01` | 1 (D39) | 40 | 3 | `00` | `08` | `31 03` |
| `Spectrum Wave` | `02` | 4 (D35-D38) | 250 `Normal`, 150 `Fast` | 0 | `00` right, `02` left | `00` | `31 03` |
| `Covering Marquee` | `04` | 1 (D39) | 150 | 2 | `00` | `00` | `31 03` |
| `Alternating` | `05` | 7 (D41, D44, D47-D51) | all five notches in both sub-modes: travelling 800/700/500/400/300, in place 1600/1300/1000/800/600 | 2 | all four measured: `00`, `01`, `02`, `03` | `00` | `31 04` |
| `Pulse` | `06` | 1 (D39) | 15 | 1 | `00` | `08` | `31 03` |
| `Breathing` | `07` | 3 (D39, D43, D45) | 40 `Slowest`, 20 `Normal`, 4 `Fastest` | 1 to 3 | `00` | `08` | `31 03` |
| `Candle` | `08` | 1 (D41) | 50 | 1 | `00` | `00` | `31 03` |
| `Starry Night` | `09` | 1 (D41) | 15 | 1 | `01` | `00` | `31 03` |
| `Rainbow Flow` | `0b` | 1 (D40) | 250 | 0 | `00` | `00` | `31 03` |
| `Super Rainbow` | `0c` | 1 (D40) | 150 | 0 | `00` | `00` | `31 03` |
| `Rainbow Pulse` | `0d` | 1 (D40) | 250 | 0 | `00` | `00` | `31 03` |
| `Tai Chi` | `0e` | 1 (D41) | 30 | 2 | `00` | `05` | `31 03` |
| `Water Cooler` | `0f` | 1 (D40) | 30 | 2 | `00` | `05` | `31 03` |
| `Loading` | `10` | 1 (D40) | 10 | 1 | `00` | `04` | `31 03` |

`Marquee` and `Wave` do not use the `2a` family, so no `2a` identifier exists
for them in any capture. The values `03` and `0a` never appeared at byte 4.
Whether the firmware reserves them (for example for the two `26`-family
effects) is **unknown**. Byte 4 as the mode identifier, an inference after
D35-D38, is now **verified** for the fourteen modes above: fourteen distinct
constants that follow the announced selection order across four independent
windows.

### Field map of the `2a 04` frame

- Bytes 0-2 `2a 04 20`: as in D35-D38. The `20` at byte 2 matching the
  `Fixed` channel-selector position remains an **inference**.
- Byte 3 `20`: constant in every `2a` frame. `Fixed` carries `00` here and
  the `26 14` stream carries `20`. Meaning **unknown**.
- Byte 4: mode identifier, **verified** (table above).
- Bytes 5-6: speed, **verified** as a little-endian uint16. Alternating's
  `Normal` measured `f4 01` (500), which does not fit one byte. Lower is
  faster, **verified** by the Breathing extremes (`Slowest` 40, `Normal` 20,
  `Fastest` 4) plus the D36 physical acceleration. The scale is per mode
  (Breathing 40 to 4, Spectrum Wave 250 and 150, Alternating 500), so a speed
  value is meaningless without its mode. It is also **per sub-mode**, so the
  same UI notch maps to different raw values depending on byte 55 bit 0,
  which is what produced the unexplained 1000 in D47.

  The track has **exactly five positions** and saturates silently at **both
  ends**: a further arrow press transmitted nothing at the slow extreme
  (D50) or at the fast one (D51), with 48 and 31.8 seconds of tail ruling
  out a late write. Both Alternating curves are now **complete and
  verified**:

  | Notch | No propagation (D51) | With propagation (D50) | Ratio |
  | --- | ---: | ---: | ---: |
  | slow extreme | 1600 | 800 | 2.000 |
  | `Slow` | **1300** | 700 | **1.857** |
  | `Normal` | 1000 | 500 | 2.000 |
  | `Fast` | 800 | 400 | 2.000 |
  | `Fastest` | 600 | 300 | 2.000 |

  **The scale is a lookup table, not an interpolable function** (D50), and
  the sub-mode relationship is **not a constant factor** (D51). The factor
  of 2 holds exactly at four notches and breaks at `Slow`. Neither table
  derives cleanly from the other: half of 1300 is 650, which is what a
  piecewise-linear model predicted for the propagating `Slow`, where CAM
  writes 700. They are **two independent tables** that happen to agree on a
  factor of 2 at four points for **unknown** reasons.

  Both windows pre-registered every value before capturing, D51 with three
  internal controls measured in D48; all three reproduced exactly, so the
  discrepant `Slow` is not a method artifact. Within a sub-mode the steps
  are irregular too (+100, +100, **+200**, +100 with propagation), which
  refuted the piecewise-linear and geometric candidates registered before
  D50. A whole-range linear model and a constant-ratio geometric model were
  already excluded by the measured `Normal`.

  Consequence for a Linux implementation: speed is neither interpolable
  within a sub-mode nor derivable between sub-modes. **Every mode and
  sub-mode pair requires its five raw values transcribed from measurement.**
  A projection would have written 1400 where the real value is 1300.

  Scale **shape** is per mode: Alternating's `Fast` is 0.8x its `Normal`,
  Spectrum Wave's is 0.6x its own (150 against 250, D36), and Breathing's
  extremes are 2.0x and 0.2x. The two Alternating curves differ in shape
  only at `Slow` (1.4x against 1.3x). Ranges for modes other than
  Alternating are incomplete: Breathing has three of five notches and
  Spectrum Wave two of five. Alternating is the only effect in the reported
  matrix exposing a movement switch, so no second mode exists to test the
  sub-mode behaviour against.
- Byte 7: `00` in every frame except Candle, which carried `56` (86).
  Meaning **unknown**. Candle exposes no speed control in the UI yet its
  frame still carried 50 at bytes 5-6, also unexplained.
- Bytes 8 through 8+3N-1: color list, **verified** as contiguous 3-byte
  entries in **R B G order**. D43 anchored the order with controlled
  additions: pure red `#FF0000` entered as `89 00 00` and pure blue
  `#0000FF` as `00 89 00` at 25 percent brightness. This is the reverse
  anchor of `Fixed`'s G R B. Removing an entry compacts the list,
  **verified** in D43 (deleting the middle color shifted blue into its
  slot). Entries beyond the third (the UI suggests up to 8) are uncaptured,
  so their offsets are an extrapolation.
- Brightness: **verified baked into the color entries**, not a separate
  field. One brightness step (25 to 26 percent) rewrote `27 3e 00` to
  `28 40 00` and `00 89 00` to `00 8b 00` and changed nothing else (D45).
  The full-component level `89` at 25 percent equals the per-zone `Fixed`
  level measured in D26-D32. The exact quantizer for the `2a` list is
  **unknown**, compatible with but not proven equal to the Fixed family.
- Byte 55: bit field. Bit 1 is direction, **verified in two modes**
  (Spectrum Wave `00` to `02` in D37, Alternating `01` to `03` in D44, the
  only byte changed in both). Bit 0 is **spatial propagation**, verified in
  D47 by toggling Alternating's movement switch: with `1` the alternation
  travels along the array, with `0` the whole board switches colors in
  place. It does **not** gate the animation itself, since the two colors
  keep alternating either way. The earlier reading of bit 0 as "animation
  running" is corrected. Caution: Starry Night carries `01` although its UI
  exposes no movement switch, which is compatible with a mode that always
  propagates but is not verified. D47 fixes the meaning for Alternating,
  not for the whole family. The two bits are **independent and orthogonal**,
  verified in D48 with all four Alternating combinations measured: `00` and
  `02` without propagation, `01` and `03` with it. CAM keeps writing bit 1
  when bit 0 is clear, so direction never stops being emitted; without
  propagation its visible effect is only a phase inversion of an in-place
  switch, which the operator described as hard to tell apart.
- Byte 56: color count, **verified** (measured 0 through 3, follows the
  list length exactly, including after a deletion).
- Byte 57: per-mode constant (`08` for Breathing, Fading and Pulse, `05`
  for Tai Chi and Water Cooler, `04` for Loading, `00` elsewhere). Meaning
  **unknown**.
- Bytes 58-59: `31 03` in every mode except Alternating, which carries
  `31 04`. The D35-D38 reading of a constant is corrected: byte 59 varies
  by mode. Meaning of both bytes **unknown**. `0x31` is still 49 decimal,
  still only a suggestive coincidence.

### Marquee and Wave: the `26 04` plus parameterized `26 06` family

**Verified from D39, D41 and D44:** selecting `Marquee` or `Wave` transmits
no `2a` frame. Each sends the familiar `26 04 20 00` data vector followed
2-3 ms later by a `26 06` commit whose bytes 4-5 are parameterized:

- `Fixed` commit (constant, all D1-D32 captures): `26 06 20 00 01 00 00 31 00 00 80 00 32 00 00 01`.
- `Marquee` commit: same frame with byte 4 `02` and byte 5 `29`.
- `Wave` commit: same frame with byte 4 `02` and byte 5 `35`.

Byte 5 therefore selects the effect for the `26`-family (`29` Marquee, `35`
Wave, `00` Fixed), and byte 4 distinguishes the parameterized form (`02`)
from the Fixed form (`01`). Both **verified** in traffic, each effect
selector in two windows for Marquee (D39, D44) and one for Wave (D41). The
remaining commit bytes (`31` at 7, `80` at 10, `32` at 12, `01` at 15) are
identical in all variants and their meaning is **unknown**.

- Marquee's data vector carried its one color as GRB triples, `00 27 3e`
  (the same stored purple that the `2a` list carries as `27 3e 00` in RBG),
  in only the **first N** of the 49 slots, the rest zero. The **LED size
  control is N**: one size step changed the vector from 3 to 4 lit triples
  with no other byte change and a byte-identical commit (D44, **verified**
  for that one step). The mapping of the full size scale to N is
  **unknown**.
- Wave's data vector carried all 49 triples as `89 89 89` (D41), the
  customized-white level at the current 25 percent brightness. Wave's UI
  requests per-zone colors, so the all-white vector is CAM's stored state,
  not a proven default. Physical effect for Wave remains unconfirmed (the
  earlier manual exploration saw no visible change).

### `26 14` real-time streaming (Audio Bass, Audio Level)

**Verified from D42:** selecting `Audio Bass` and then `Audio Level` sent no
configuration frame at all. CAM instead streamed `26 14` frames:

- Header `26 14 20 20`, then 49 triples at bytes 4-150, zero padding after.
- 2176 frames in 70.6 seconds, mean interval 32.5 ms (about 31 fps), with
  no gap at the mode switch and no commit, until capture stop.
- The controller acknowledged every streamed frame whose ack window the
  capture covered, with the `ff 01` echo of `26 14`: 2175 echoes for 2176
  writes, the last write's ack fell outside the window.
- The `ff 03` heartbeat **stopped** when streaming began (last heartbeat at
  t=64.23, stream start t=64.57, none in the remaining 70 seconds). Whether
  it resumes after leaving the audio modes is **unknown**, the capture
  ended inside the stream.
- Frame content: up to t=90.42 every frame's 49 triples were identical to
  each other, pulsing with the music (uniform full-cover color). From
  t=90.45 on, 1225 frames carried spatially non-uniform triples, for
  example 7 uniform triples, an 18-triple gradient, then 24 dark, a
  partially lit meter pattern. Attributing the uniform span to Audio Bass
  and the spatial span to Audio Level follows the announced selection
  order, an **inference**, because the mode switch leaves no USB marker.
- The component order of the `26 14` triples is **unknown**. No controlled
  color anchor exists for this family.

The opcode implies that the animation for these modes is rendered on the
host. A Linux implementation of the audio modes would need a daemon
streaming frames at this cadence, and the same opcode is a candidate for
arbitrary host-rendered real-time effects. That is an engineering
implication, not a safe write specification.

### Temperature Monitor: verified negative result

In D42, the selection of `Monitor Temperature` plus its CPU source produced
**zero writes** during the first 64.6 seconds of the window. In D46, a
dedicated window, the operator's repeated attempts again produced **zero
writes of any kind** (the only N9 traffic was 49 heartbeats), and the board
visibly stayed in the previous Breathing state. D47 adds a third independent
observation on a different day and after a full VM restart: `Monitor
Temperature` was the active effect for the first 34.6 seconds of that window
and transmitted **zero writes**. The failure is in CAM before
the USB layer, not a controller rejection, because nothing was transmitted.
The orchestrator's hypothesis is a CAM issue with virtualized temperature
sources. The mode's transport pattern remains **unknown** and a retry is
pending.

### D47: Alternating's movement switch

A dedicated single-variable window captured on 2026-07-25, after the VM was
restarted and the device re-attached, which re-enumerated the N9 as device 6
on bus 3. PCAP SHA-256
`191335602dd41483881020cf148fc966543d5c626fda1aa6671b77360399a12f`, 129.1
seconds, **three** interrupt OUT writes and no commit, each acknowledged
within 2.7 ms.

The three writes are Alternating's selection frame, the movement switch
turned off, and turned back on. The toggle changed **two** fields at once:
byte 55 bit 0 from `1` to `0`, and the speed uint16 at bytes 5-6 from 500 to
1000. The third frame is **byte-for-byte identical** to the first, so the
off-and-on cycle leaves no residual state in the configuration frame.

The operator's directed physical description resolves the attribution. With
the switch off the two colors **keep alternating**, as a hard cut with no
intermediate tones, and the whole board switches **in place**. With the
switch on the alternation **travels along the board** in one direction. A
period change cannot turn a directional sweep into an in-place blink, so the
observed difference comes from the bit, and bytes 5-6 only carry each
sub-mode's own period. Both values are real periods, because animation runs
in either state.

An earlier reading of this window, which assumed the animation stopped, was
wrong and was corrected before it reached this document. The operator's
general "done, as expected" was taken as confirmation of a stop; the operator
flagged the discrepancy and directed questions established the real
behavior. A general acknowledgment is not a substitute for a directed
physical description.

The repository now has a closed, uninstalled D47 phase 1 laboratory that
freezes only frame 1477 for travelling right at Normal and frame 3725 for
switching in place at Normal. Their SHA-256 values are computed over the
actual 512 binary bytes, not tshark text.

**Verified by the operator on 2026-07-27:** Linux resolved the N9 as
`/dev/hidraw2`, verified the exact D32 frame from its private PCAP, passed the
offline restore check, and passed real preflight at 71.0 C without opening
hidraw. The closed laboratory sent frame 1477 once, observed it for 10
seconds, and restored D32 successfully. It then passed another preflight at
42.0 C, sent frame 3725 once, observed it for 10 seconds, and restored D32
again. Final preflight passed at 63.0 C with no process retaining a hidraw
handle. The operator confirmed that both effects looked correct and that fans
and pump remained normal. This physical QA validates only those two exact D47
replays and their D32 restorations on this board. At that date the laboratory
exposed no other state. It was widened later, first with the D49 and D50
travelling speeds and then with the D51 in-place speeds, each under its own
evidence and its own authorization. It still exposes no D48 direction state.

### D48: direction and speed without propagation

A follow-up window on 2026-07-25 that closed both questions D47 left open,
both inside Alternating with byte 55 bit 0 clear. **Nine** interrupt OUT
writes, no commit, and across all nine frames **only three bytes vary**:
5, 6 (speed) and 55. Colors, count, byte 57 and bytes 58-59 stayed frozen.

| # | Action | t (s) | Byte 55 | Speed |
| ---: | --- | ---: | --- | ---: |
| 1 | movement off | 17.129 | `00` | 1000 |
| 2 | direction left | 89.686 | `02` | 1000 |
| 3 | direction right | 188.242 | `00` | 1000 |
| 4 | direction left | 224.811 | `02` | 1000 |
| 5 | movement on | 295.433 | `03` | 500 |
| 6 | direction right | 322.542 | `01` | 500 |
| 7 | movement off | 339.060 | `00` | 1000 |
| 8 | speed `Slowest` | 485.616 | `00` | 1600 |
| 9 | speed `Fastest` | 6576.395 | `00` | 600 |

**CAM keeps writing bit 1 with bit 0 clear**, so direction never stops being
emitted. The operator confirmed the direction control and the speed slider
stay visible and enabled without propagation, and that a direction change is
still visible but hard to tell apart, which matches inverting the phase of an
in-place switch.

**The unexplained 1000 of D47 is `Normal` on a different scale, not a
sentinel.** The slider operates in both sub-modes. The operator never touched
it between actions 5 and 7, yet the raw value moved 500 to 1000 and back:
that is a remap of the same notch, not a speed change. Action 9 accelerated
the alternation visibly, as expected for 1600 to 600.

Byte 55 for Alternating is now complete with **all four states measured**,
and bits 0 and 1 are independent.

**Attribution caveat.** Only actions 1, 8 and 9 followed the announced
single-action protocol. Actions 2 through 6 were operator-initiated
exploration, narrated in order, so that stretch is attributed by narrated
order and timestamp, a lower rigor than D43-D45. Three independent checks
corroborate the mapping: the write count matches the narrated action count
exactly, frames 1, 3 and 7 are byte-for-byte identical to each other as are
frames 2 and 4, and the resulting values are consistent with a two-bit
field. The 101-minute gap between actions 8 and 9 is an announced operator
break with the capture running and no CAM interaction.

### D49: the sub-mode factor, predicted before capture

The first window in this campaign to register a **numeric prediction before
capturing**. From D48's no-propagation scale and the known `Normal` 500 with
propagation, a constant factor of 2 predicted `Slowest` 800 and `Fastest`
300. Both were measured exactly, along with `Normal` 500 as a control against
three earlier windows.

Four writes for four announced gestures, and **only bytes 5-6 vary** across
the window: byte 55 stays `01` throughout, so neither propagation nor
direction moved. Frames 1 and 4 are **byte-for-byte identical**. They measure
the same state reached two different ways, once by sub-mode remap without
touching the slider and once by moving the slider from `Normal`, so the remap
depends on neither path nor history.

**Protocol deviation, recorded.** Gesture 2 arrived 7.7 seconds after gesture
1, under the announced 12-second minimum. Attribution is unaffected since the
writes are unambiguously separated, but the window did not meet its announced
pause and is not described as if it had. **The physical confirmation for
gesture 1 was not obtained**: the operator gave a general acknowledgment
without describing whether the alternation resumed travelling. It is recorded
as unconfirmed. The conclusions rest entirely on the trace and on the
pre-registered prediction, but D49 cannot serve as additional physical
confirmation of bit 0's meaning.

### D50: the speed track is a table, not a formula

A confirmation window on 2026-07-25. Every value was registered **before**
capturing, including two internal controls whose values were already measured
in independent windows. Five announced arrow presses produced **four** writes,
and only bytes 5-6 varied.

| Press | Notch | Predicted | Measured |
| ---: | --- | ---: | ---: |
| 1 | `Fast` | 400 | **400** |
| 2 | `Normal` (control) | 500 | **500** |
| 3 | `Slow` | 700 | **700** |
| 4 | slow extreme (control) | 800 | **800** |
| 5 | at the stop | no write | **no write** |

Alternating's speed curve with propagation is therefore complete: 300, 400,
500, 700, 800. Its steps are +100, +100, **+200**, +100, which **refutes**
the two formulas registered beforehand (piecewise-linear predicted `Slow`
650, per-half geometric predicted 632). The scale is a **lookup table**.

The fifth press is the measurement of a negative: the control saturates at
the extreme without transmitting, with 48 seconds of tail ruling out a late
write, so the track has **exactly five positions** and none beyond. Before
D50 this rested on the reported effect matrix and CAM's own enum, not on a
measurement.

This window confirms the exploratory reconstruction recorded in D50a, an
aborted capture whose six writes were only examined after the orchestrator
had wrongly stated it contained none. Its values, `Fast` 400 and `Slow` 700,
were reconstructed from the values themselves rather than from an announced
action log; D50 re-derives them under the announced protocol with controls.

The closed, uninstalled Alternating laboratory now exposes the five exact
travelling-right states measured by D47, D49 and D50. It freezes the full
512-byte PCAP payload for each nominal operation rather than encoding a speed:

| Operation | Canonical source frame | Speed | Binary SHA-256 |
| --- | --- | ---: | --- |
| `travel-right-fastest` | D49 1789 and 2579 | 300 | `889337b9110e41ef9a9bae29022e2748d393d8474b9cc7743fc7b4e30ccc4c03` |
| `travel-right-fast` | D50 1443 | 400 | `f0c00d9b1e524fd6143dc72f04a0be41cb4c4b47299e324f78573c6700184f42` |
| `travel-right-normal` | D47 1477 and 4667, D49 2431, D50 1471 | 500 | `bb88f24351f7817582c5f591203c5cae3b4963ad4b6bb1e2fd244b56c9dee782` |
| `travel-right-slow` | D50 1497 | 700 | `ccc5de88b19f5a4ce518ff28beb49783af40073453a6546543d0b84fcb1c6ab2` |
| `travel-right-slowest` | D49 2187 and D50 1519 | 800 | `bca2c0146e7ea24ea02f9f3ef1be93117d9559871ca275637ecf845a69db03fe` |

D47, D49 and D50 reproduce the Normal payload byte for byte. D49 and D50
reproduce the Slowest payload byte for byte. Across the five states only
bytes 5 and 6 differ. D49 PCAP SHA-256 is
`ad4abf5534676c51cd4ee09b03f90c971d8c2193a02ea4de8080725a299b2b14`
and D50 PCAP SHA-256 is
`860c77728a76281056524f0ef469c965e631523fa2faef8bdf50983280a579db`.
The private captures and every relevant frame are re-extracted by the offline
test suite. D50a is not used to construct any payload.

**Verified by the operator on 2026-07-29:** the four remaining D49 and D50
speed states were replayed on this board. Before any write, the three private
PCAPs matched their recorded SHA-256 values, every `2a 04` frame in the
filtered stream of each capture was re-extracted and matched a frozen state
with no leftover frame, the exact D32 restoration frame was verified from its
own private PCAP, the offline restoration check passed, and real preflight
passed at 42.0 C without opening hidraw. Linux resolved the N9 as
`/dev/hidraw3` through its exact HID identity. That is a different node number
than the D47 session used, which confirms that resolution follows the identity
and not a fixed path. The laboratory then sent `travel-right-fastest` once at
48.0 C, `travel-right-fast` once at 42.0 C, `travel-right-slow` once at 43.0 C
and `travel-right-slowest` once at 42.0 C. Each state was observed for 10
seconds and each was followed by a successful D32 restoration. The final
preflight passed at 43.0 C with no process retaining a hidraw handle and with
the heartbeat counter still advancing. The operator confirmed that the four
states appeared as clearly distinct speeds of the same travelling-right
effect, in the expected order, and that fans and pump remained normal.

All five travelling-right speed states now have physical QA on this board.

The closed laboratory was then widened to the second measured table, the
in-place sub-mode of D51. It freezes the full 512-byte payload of each notch,
exactly as the travelling table does:

| Operation | Canonical source frame | Speed | Binary SHA-256 |
| --- | --- | ---: | --- |
| `in-place-right-fastest` | D51 6901 | 600 | `1a96361d6ce5096e3ea84f3cf99054bdc6afd02b859aaaa23455c54dcb8c8e91` |
| `in-place-right-fast` | D51 6885 | 800 | `5b7d7042382bf69c7920465355af73118bca1c394b0d561f4509318d519d1587` |
| `in-place-right-normal` | D47 3725 and D51 6865 | 1000 | `a11850148cec0e00116a7ef2c851d8bf40514bd3ae532e0065c2cc51504023e6` |
| `in-place-right-slow` | D51 6853 | 1300 | `af48e4a14b0357c3fec8d66c8016612d769d4112cb59b11156255f5faa833402` |
| `in-place-right-slowest` | D51 6015 | 1600 | `77a1bb88ad9ae133a0eb6c35ead49d919481fad8c0781e80c7ca95f222a17fcb` |

D51 PCAP SHA-256 is
`511bbc339a392a17c617315d9bb9c0191a061abf6e86e6bce8122249dd087ebe`.
The five frames are the whole `2a 04` content of that window, with no leftover
frame, and across them only bytes 5 and 6 differ. Byte 55 is `00` in all five.
D47 frame 3725 and D51 frame 6865 are the same payload four days apart, which
is the cross-capture control for this table, the counterpart of the Normal and
Slowest controls that anchor the travelling one.

The two tables are stored as independent transcriptions and the code cannot
derive one from the other. That is a direct consequence of D50 and D51: the
scale is a lookup table, and the sub-mode factor of 2 breaks at `Slow`, where
the measured pair is 700 and 1300 rather than 700 and 1400.

**Verified by the operator on 2026-07-29:** the four new in-place notches were
replayed on this board. The D51 capture matched its recorded checksums, its
five frames were re-extracted and matched the frozen states with no leftover
frame, the D32 safety net was verified from its own private PCAP, and real
preflight passed at 46.0 C without opening hidraw. The laboratory sent
`in-place-right-fastest` at 49.0 C, `in-place-right-fast` at 46.0 C,
`in-place-right-slow` at 46.0 C and `in-place-right-slowest` at 61.0 C, each
once, each observed for 10 seconds and each followed by a successful D32
restoration. Final preflight passed at 59.0 C with no process retaining a
hidraw handle. The operator confirmed that the whole board toggled in place
with no lateral travel, at four clearly distinct rates from fastest to
slowest, and that fans and pump remained normal. The cycle was run twice
because the operator did not watch the first run, and only the observed second
run counts as evidence.

With this, both Alternating speed tables have physical QA on this board. That
closes the speed scale of the only mode in the matrix that exposes a movement
switch, in both of its sub-modes.

**Scrutiny caveat.** Unlike D35, D47, D49 and D50, this unit was accepted
without an independent review by a second author. The operator waived that
gate explicitly. The capture evidence, the offline suite and the physical QA
stand on their own, but the implementation was not read by anyone other than
its author. The laboratory still exposes no D48 direction state.

### D51: the sub-mode factor is not a rule

A confirmation window on 2026-07-26 measuring the two notches D48 had left
open in the non-propagating sub-mode. Six values pre-registered, **three of
them internal controls** already measured in D48. Seven announced actions
produced **five** writes, and only bytes 5-6 varied.

| Action | Notch | Predicted | Measured |
| --- | --- | ---: | ---: |
| movement off | slow extreme | 1600 | **1600** (control) |
| Right arrow | `Slow` | 1400 | **1300** |
| Right arrow | `Normal` | 1000 | **1000** (control) |
| Right arrow | `Fast` | 800 | **800** (control) |
| Right arrow | `Fastest` | 600 | **600** (control) |
| Right arrow at the stop | none | no write | **no write** |
| refocus click | none | no write | **no write** |

All three controls reproduced exactly, so the single discrepant value is a
real measurement, not a method artifact. The prediction came from projecting
the sub-mode factor of 2 across the whole scale; it holds at four notches
and **fails at `Slow`**, refuting the factor as a general rule.

Two negatives were also measured here: the refocus click after using the
mouse on the movement switch transmitted nothing, confirming for the speed
control what D45 observed only for brightness; and the press against the
**fast** stop transmitted nothing, completing D50's result at the slow stop.

Methodological note worth keeping. The two intermediate notches were omitted
from the model during D48 and D49, and the orchestrator went as far as
calling the scale complete with three of five points. The operator pointed
out they were missing. `Slow` is precisely where the model breaks: a
projection would have written 1400 into this document with no other evidence
contradicting it.

### Cross-window reproducibility

Four frames were byte-for-byte identical across independent captures,
verified by SHA-256 of the extracted payloads: Breathing's selection frame
(D39 and D43), Breathing's two-color state (D43 final and D45 first, so the
list state persisted across sessions), Alternating's selection frame (D41
and D44), and Marquee's 3-triple data frame (D39 and D44).

D47 adds a fifth, weaker but wider check. Its Alternating frame matches D44's
in mode, speed, flags, color count and bytes 57-59, and differs only in the
four color bytes, `27 3e 89 5f` in D44 against `28 40 8b 61` in D47. Three of
those four changes, `27` to `28`, `3e` to `40` and `89` to `8b`, are exactly
the ones D45 measured for the 25-to-26 percent brightness step. The fourth,
`5f` to `61`, was **not measured in D45**: Breathing's list there did not
contain that component, so it is a change compatible with the same step
rather than a repeat of a prior measurement. The state survived a VM shutdown
and a device re-attach, which corroborates the brightness-baked-into-the-
triples model with that limitation stated.

These captures decode observations only. They do not establish a general safe
write specification for any animated or streamed mode. The only narrow
exception is the exact frozen D35 replay in the closed laboratory described
above. No other `2a 04`, parameterized `26 06`, or `26 14` frame is authorized
by this evidence.

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
| `26 04` | OUT, host to controller | Lighting data write (`Fixed` vector, also the Marquee and Wave data vector) | Verified |
| `26 06` | OUT, host to controller | Lighting commit that follows a `26 04` write. Constant for `Fixed`, parameterized at bytes 4-5 for Marquee (`02 29`) and Wave (`02 35`) | Verified |
| `2a 04` | OUT, host to controller | Animated-effect configuration write, one frame per user action with no commit, observed for fourteen firmware-rendered modes (D35-D45) | Verified |
| `26 14` | OUT, host to controller | Host-rendered streaming frame of 49 triples, about every 32 ms with no commit, observed for the audio modes (D42) | Verified |
| `ff 01` | IN, controller to host | Generic acknowledgment that echoes the recognized opcode, observed after `20 03`, `26 04`, `26 06`, `2a 04`, and every streamed `26 14` | Verified |
| `ff 03` | IN, controller to host | Periodic heartbeat about every 3 seconds carrying a frame counter, with no telemetry payload. It stopped during `26 14` streaming in D42 | Verified |

**Verified from the descriptor, not observed in traffic:** the report descriptor also declares Output Report IDs `12 22 24 f2 fe e2 f4` and Input Report IDs `13 23 25 27 29 2b e3 f5` that CAM did not exercise in any captured session. Output Report ID `2a` left this list when the D35-D38 series observed it in traffic. Their existence is a descriptor fact. Their meaning is **unknown** because no capture drove them.

**Unknown, and important for the cooling goal:** none of the current captures contains real temperature telemetry or fan RPM telemetry. The `ff 03` heartbeat carries only a frame counter, not sensor values, and the `Monitor Temperature` lighting effect reads its source from the host, not from a controller telemetry frame. Decoding actual temperature and RPM would require a new capture taken on CAM's Cooling page (fan curves, pump control, sensor readouts), which no session in this document exercised. Do not infer a telemetry opcode from the lighting captures, and do not send any of these opcodes to the device.
