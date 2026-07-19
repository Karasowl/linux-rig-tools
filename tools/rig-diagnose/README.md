# rig-diagnose

Prints a markdown report of every RGB / fan / cooling controller in your
machine: USB IDs, hidraw nodes and permissions, hwmon sensors, exposed PWM fan
channels, and whether each device is on the linux-rig-tools radar.

**Read-only.** It never sends a byte to any device.

```sh
rig-diagnose > my-rig.md
```

Attach `my-rig.md` to a [GitHub issue](https://github.com/Karasowl/linux-rig-tools/issues)
to get your hardware tracked.

- Dependencies: `bash`, `usbutils`, `pciutils` (all preinstalled on most distros)
- Root: not required (root shows nothing extra)
