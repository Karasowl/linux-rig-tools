# Contributing

## The single most useful thing

Run the inventory tool and attach its output to a GitHub issue:

```sh
tools/rig-diagnose/bin/rig-diagnose > my-rig.md
```

That tells us exactly which controllers you have, their USB IDs, and which
hidraw nodes they expose.

## Helping decode a protocol

Every 🔬 tool needs USB captures taken while the Windows vendor app drives the
device. See [docs/CAPTURE-GUIDE.md](docs/CAPTURE-GUIDE.md) — it takes ~15
minutes with a dual-boot machine.

## Ground rules

- **One directory per tool, fully standalone.** A tool must never import from
  another tool. Shared knowledge goes in `docs/`.
- **Read-only until the protocol is understood.** Never ship code that writes
  reports to a device based on guesses; a wrong write can hang a controller
  until power-cycle (or worse, brick it).
- Working tools are plain `bash` or Python ≥3.10 with `hidapi` only.
- Keep tools installable three ways: `install.sh`, PKGBUILD, `.deb`.
- English for code and docs; the two READMEs (EN/ES) stay in sync.

## Reporting bugs

Include your distro, kernel (`uname -r`), and `rig-diagnose` output.
