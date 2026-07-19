# Packaging

Every tool is packaged **individually** — users install only what their
hardware needs.

| Target | Where | Status |
|---|---|---|
| Arch / CachyOS / Manjaro | [`arch/`](arch/) — one PKGBUILD per tool | ✅ local build; AUR upload planned |
| Debian / Ubuntu / Mint / Pop!_OS | [`debian/build-debs.sh`](debian/) — one .deb per tool | ✅ local build; PPA/repo planned |
| Fedora | RPM specs + COPR | planned |
| openSUSE | OBS | planned |

## Arch

```sh
cd packaging/arch/rig-profiles
makepkg -si
```

## Debian/Ubuntu

```sh
./packaging/debian/build-debs.sh     # writes dist/*.deb at the repo root
sudo apt install ./dist/rig-profiles_*_all.deb
```

## Notes

- udev rules (`udev/60-linux-rig-tools.rules`) are only needed by the
  device tools (nzxt-n9, cm-nex-digital, chassis-ledmatrix); their future
  packages will carry the rules. `install.sh` can install them today for
  development.
- Packages for the 🔬 tools appear the moment they have a working binary.
