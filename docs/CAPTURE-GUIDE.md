# USB capture guide (Windows dual-boot)

The 🔬 tools need to see what the vendor apps say to each device. If you
dual-boot Windows with NZXT CAM / MasterCTRL / the chassis suite installed,
you can produce gold-quality captures in minutes.

## One-time setup (Windows)

1. Install [Wireshark](https://www.wireshark.org/download.html) and tick
   **USBPcap** during installation.
2. Reboot Windows.

## Capturing

1. Open Wireshark → double-click the **USBPcap** interface.
2. Set the display filter to the device you're capturing (examples):
   - NZXT N9 controller: `usb.idVendor == 0x1e71 && usb.idProduct == 0x2023`
   - CM Nex Digital: `usb.idVendor == 0x2516 && usb.idProduct == 0x0232`
   - LED matrix: `usb.idVendor == 0xff00`
3. Start the vendor app and perform **one action at a time**, writing down
   the exact time and what you did, e.g.:
   ```
   14:02:10  CAM: set CPU fan curve to Silent
   14:02:45  CAM: set CPU fan curve to Performance
   14:03:20  CAM: LED mode -> hourglass, speed 3, color #FF0000
   ```
4. Stop the capture, save as `.pcapng`.

**The notes file is as important as the capture.** Protocol work is
diffing packets between two known actions.

Ideal capture set per device:

- App startup with device idle (initialization/handshake).
- Each fan/pump mode, one by one.
- The *same* LED effect with two different colors (isolates the color bytes).
- The *same* color with two different effects (isolates the mode byte).
- Brightness / speed changes only.

## Sharing

Open an issue titled `[capture] <device> <USB ID>` and attach the `.pcapng`
plus your notes. Captures can contain your device serial number — that's
normally fine, but strip anything you're not comfortable sharing.

## Alternative without dual-boot

Windows VM (QEMU/KVM + virt-manager) with USB passthrough of the controller,
capturing on the Linux host with `modprobe usbmon` + Wireshark. More setup,
same result — and you can stay in Linux.
