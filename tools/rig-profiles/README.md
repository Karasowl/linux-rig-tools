# rig-profiles

One command to switch your rig between `quiet`, `balanced` and `performance`
— the thing vendor apps do from Windows, using only kernel interfaces:

- **CPU**: cpufreq governor + Energy Performance Preference
  (`intel_pstate` and `amd-pstate` both supported)
- **GPU (NVIDIA)**: power limit via `nvidia-smi -pl`

```sh
rig-profiles status
sudo rig-profiles all balanced
sudo rig-profiles cpu quiet          # only CPU
sudo rig-profiles gpu performance    # only GPU
```

| Profile | CPU governor | CPU EPP | GPU power limit |
|---|---|---|---|
| `quiet` | powersave | power | max(70 % of default, min) |
| `balanced` | powersave | balance_performance | default |
| `performance` | performance | performance | max |

Notes:

- The GPU power limit resets on reboot. To persist, add a small systemd
  service that runs `rig-profiles gpu <profile>` at boot.
- Radiator/pump/chassis **fan curves** are NOT here yet — on boards like the
  NZXT N9 they live behind a USB controller. That's what
  [`tools/nzxt-n9`](../nzxt-n9/) is for; when it lands, profiles will drive
  fans too.
- Dependencies: `bash`; `nvidia-smi` optional (GPU part).
