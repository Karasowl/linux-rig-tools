#!/usr/bin/env bash
# linux-rig-tools installer — installs only the tools you pick.
# Works on any systemd-based distro (Arch/CachyOS, Debian/Ubuntu, Fedora,
# openSUSE, ...). Prefer your package manager when packages exist — see
# packaging/README.md.
set -euo pipefail

REPO_DIR=$(cd "$(dirname "$0")" && pwd)
BIN_DIR=/usr/local/bin
UDEV_DIR=/etc/udev/rules.d
# Tools that ship a working executable today. 🔬 tools are added here as
# soon as they have one.
INSTALLABLE=(rig-diagnose rig-profiles)

msg() { printf '\033[1;32m==>\033[0m %s\n' "$*"; }
err() { printf '\033[1;31merror:\033[0m %s\n' "$*" >&2; }

detect_distro() {
  local id like
  id=$(. /etc/os-release 2>/dev/null && echo "${ID:-}") || true
  like=$(. /etc/os-release 2>/dev/null && echo "${ID_LIKE:-}") || true
  case "$id $like" in
    *arch*)            echo "arch-based (tip: PKGBUILDs in packaging/arch/)" ;;
    *debian*|*ubuntu*) echo "debian-based (tip: packaging/debian/build-debs.sh)" ;;
    *fedora*|*rhel*)   echo "fedora-based" ;;
    *suse*)            echo "opensuse-based" ;;
    *)                 echo "unknown" ;;
  esac
}

install_tool() {
  local t=$1 src
  src="$REPO_DIR/tools/$t/bin/$t"
  [[ -f "$src" ]] || { err "tool '$t' has no installable binary yet"; return 1; }
  install -Dm755 "$src" "$BIN_DIR/$t"
  msg "installed $t -> $BIN_DIR/$t"
}

install_udev() {
  install -Dm644 "$REPO_DIR/udev/60-linux-rig-tools.rules" \
    "$UDEV_DIR/60-linux-rig-tools.rules"
  udevadm control --reload-rules && udevadm trigger
  msg "installed udev rules (user hidraw access for target devices)"
}

uninstall_all() {
  local t
  for t in "${INSTALLABLE[@]}"; do
    [[ -f "$BIN_DIR/$t" ]] && rm -f "$BIN_DIR/$t" && msg "removed $t"
  done
  if [[ -f "$UDEV_DIR/60-linux-rig-tools.rules" ]]; then
    rm -f "$UDEV_DIR/60-linux-rig-tools.rules"
    udevadm control --reload-rules || true
    msg "removed udev rules"
  fi
}

usage() { echo "usage: sudo ./install.sh [--all | --list | --uninstall]"; }

if [[ "${1:-}" == "--list" ]]; then
  printf '%s\n' "${INSTALLABLE[@]}"
  exit 0
fi

if [[ $EUID -ne 0 ]]; then
  err "run with sudo (installs to $BIN_DIR and $UDEV_DIR)"
  exit 1
fi

case "${1:-}" in
  --uninstall)
    uninstall_all
    ;;
  --all)
    for t in "${INSTALLABLE[@]}"; do install_tool "$t"; done
    install_udev
    ;;
  "")
    msg "distro: $(detect_distro)"
    echo "Tools available to install:"
    i=1
    for t in "${INSTALLABLE[@]}"; do echo "  $i) $t"; i=$((i + 1)); done
    read -rp "Numbers to install (space-separated), or 'a' for all: " sel
    if [[ "$sel" == a* ]]; then
      for t in "${INSTALLABLE[@]}"; do install_tool "$t"; done
    else
      for n in $sel; do
        idx=$((n - 1))
        if [[ $idx -ge 0 && $idx -lt ${#INSTALLABLE[@]} ]]; then
          install_tool "${INSTALLABLE[$idx]}"
        else
          err "no tool number $n"
        fi
      done
    fi
    read -rp "Install udev rules for hidraw access (needed by future device tools)? [y/N] " u
    [[ "$u" == [yY]* ]] && install_udev
    ;;
  *)
    usage
    exit 1
    ;;
esac

msg "done"
