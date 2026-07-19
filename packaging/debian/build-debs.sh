#!/usr/bin/env bash
# Build one .deb per installable tool. Output goes to dist/ at the repo root.
# Requires: dpkg-deb (present on any Debian-based system).
set -euo pipefail

VERSION=0.1.0
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
OUT="$ROOT/dist"
mkdir -p "$OUT"

build() {
  local name=$1 deps=$2 desc=$3
  local stage
  stage=$(mktemp -d)
  mkdir -p "$stage/DEBIAN" "$stage/usr/bin" "$stage/usr/share/doc/$name"
  install -m755 "$ROOT/tools/$name/bin/$name" "$stage/usr/bin/$name"
  install -m644 "$ROOT/tools/$name/README.md" "$stage/usr/share/doc/$name/README.md"
  cat > "$stage/DEBIAN/control" <<EOF
Package: $name
Version: $VERSION
Section: utils
Priority: optional
Architecture: all
Depends: $deps
Maintainer: Karasowl <ismaelguimarais@gmail.com>
Homepage: https://github.com/Karasowl/linux-rig-tools
Description: $desc
EOF
  dpkg-deb --build --root-owner-group "$stage" "$OUT/${name}_${VERSION}_all.deb"
  rm -rf "$stage"
}

build rig-diagnose "bash, usbutils, pciutils" \
  "Hardware inventory and Linux-support report for RGB/fan/cooling controllers"
build rig-profiles "bash" \
  "quiet/balanced/performance profiles for CPU (governor+EPP) and NVIDIA GPU"

echo "Built:"
ls -1 "$OUT"/*.deb
