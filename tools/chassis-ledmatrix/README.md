# chassis-ledmatrix 🔬

Control for the generic **LED-matrix display controllers** shipped with many
modern PC cases — the ones with dozens of built-in animations (hourglass ⏳,
clock, equalizer, scrolling text…) that are configured from a Windows-only
vendor suite and otherwise loop a demo mode.

**Status: reverse engineering — no working code yet.**

## Reference devices (first target case)

| Device | USB ID | Notes |
|---|---|---|
| "309 LED Matrix Controller 200324" | `ff00:020c` | HID class, bogus vendor ID `ff00` — a white-label controller used by several case brands |
| "Generic USB Audio" composite | `26ce:0a09` | 63 audio-class interfaces + 1 HID (`hidraw`). This interface layout is the classic signature of budget USB screens that stream frames over isochronous endpoints. Probably the case's display panel; relationship to `ff00:020c` under investigation |

These white-label controllers appear under many case/fan brands (Coolmoon,
Sama, DarkFlash, Segotep-style ecosystems). Decoding one usually unlocks a
whole family.

## Plan

1. Identify the vendor suite that drives them on Windows and capture:
   effect selection, speed, brightness, color, clock sync (the app must send
   the current time!), text upload if supported.
2. Determine each device's role (`ff00:020c` = effects controller?
   `26ce:0a09` = raw framebuffer?).
3. CLI: `chassis-ledmatrix effect hourglass --speed 3`,
   `chassis-ledmatrix clock --sync`, raw frame upload if the hardware allows.

## How to help

If your case has a LED matrix / dot display: `rig-diagnose` output + the name
of the Windows app that drives it. Captures per the
[capture guide](../../docs/CAPTURE-GUIDE.md).
