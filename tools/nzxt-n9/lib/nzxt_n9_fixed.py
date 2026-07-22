"""Safe, narrowly-scoped transport for the NZXT N9 Fixed lab.

Only the capture-backed 0x26/0x04 colour vector and fixed 0x26/0x06 commit
are implemented.  This module deliberately has no generic HID payload API.
"""
from __future__ import annotations

import hashlib
import math
import os
import stat
import subprocess
import time
from pathlib import Path
from typing import Callable, Final, Iterable

REPORT_LEN: Final = 512
ZONE_COUNT: Final = 49
LOAD_HEADER: Final = bytes.fromhex("26042000")
COMMIT_PREFIX: Final = bytes.fromhex("26062000010000310000800032000001")
COMMIT_FRAME: Final = COMMIT_PREFIX + bytes(REPORT_LEN - len(COMMIT_PREFIX))
TARGET_HID_ID: Final = "0003:00001E71:00002023"
DESCRIPTOR_LEN: Final = 150
OUTPUT_26_SEQ: Final = bytes.fromhex("852609019182")
COMMIT_GAP_S: Final = 0.003
D32_FRAME_SHA256: Final = "24a9fd2fbb05769c56505907506c186ba313baa0a277a2506ceb831e77573c70"
D32_PCAP_PATH: Final = Path(
    "/home/karasowl/vms/win11-cap/captures/nzxt-n9/"
    "2026-07-21-d32-fixed-per-zone-49-last-right-to-red/"
    "fixed-per-zone-49-last-right-to-red-private-bus.pcapng"
)
SYSFS_HIDRAW_CLASS = Path("/sys/class/hidraw")
DEV_DIR = Path("/dev")


class N9FixedError(RuntimeError):
    """A closed failure.  Callers must not retry a failed write automatically."""


def srgb_decode(value: float) -> float:
    return value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4


def srgb_encode(value: float) -> float:
    return 12.92 * value if value <= 0.0031308 else 1.055 * (value ** (1 / 2.4)) - 0.055


def component_byte(component: int, brightness: int) -> int:
    """Per-zone candidate quantizer, scale 255, supported by D26-D32.

    This is a thesis, not a claim about CAM internals.  The global model used
    scale 254, so an uncaptured component can differ by plus or minus one.
    """
    if not isinstance(component, int) or not 0 <= component <= 255:
        raise ValueError("RGB component must be an integer from 0 to 255")
    if not isinstance(brightness, int) or not 0 <= brightness <= 100:
        raise ValueError("brightness must be an integer from 0 to 100")
    linear = srgb_decode(component / 255) * (brightness / 100)
    return math.floor(255 * srgb_encode(linear) + 0.422545474091919)


def parse_hex_color(text: str) -> tuple[int, int, int]:
    text = text.strip().removeprefix("#")
    if len(text) != 6 or any(c not in "0123456789abcdefABCDEF" for c in text):
        raise ValueError("color must be exactly six hexadecimal RGB digits")
    return tuple(int(text[offset : offset + 2], 16) for offset in (0, 2, 4))  # type: ignore[return-value]


def build_color_frame(colors: Iterable[tuple[int, int, int]], brightness: int) -> bytes:
    colors = list(colors)
    if len(colors) != ZONE_COUNT:
        raise ValueError("exactly 49 zones are required")
    frame = bytearray(REPORT_LEN)
    frame[:4] = LOAD_HEADER
    for index, (red, green, blue) in enumerate(colors):
        offset = 4 + index * 3
        frame[offset : offset + 3] = bytes((
            component_byte(green, brightness),
            component_byte(red, brightness),
            component_byte(blue, brightness),
        ))
    validate_color_frame(bytes(frame))
    return bytes(frame)


def validate_color_frame(frame: bytes) -> None:
    if len(frame) != REPORT_LEN:
        raise ValueError("colour frame must be exactly 512 bytes")
    if frame[:4] != LOAD_HEADER:
        raise ValueError("colour frame header must be 26 04 20 00")
    if any(frame[4 + ZONE_COUNT * 3 :]):
        raise ValueError("colour frame padding must be zero")


def validate_commit_frame(frame: bytes) -> None:
    if len(frame) != REPORT_LEN or frame[: len(COMMIT_PREFIX)] != COMMIT_PREFIX:
        raise ValueError("commit frame does not have the fixed 26 06 shape")
    if any(frame[len(COMMIT_PREFIX) :]):
        raise ValueError("commit frame padding must be zero")


def _tshark_lines(pcap_path: Path) -> list[str]:
    if not pcap_path.is_file():
        raise N9FixedError("D32 PCAP is not available at %s" % pcap_path)
    try:
        result = subprocess.run(
            ["tshark", "-r", str(pcap_path), "-Y", "usb.capdata", "-T", "fields",
             "-e", "usb.bus_id", "-e", "usb.device_address", "-e", "usb.capdata"],
            check=True, text=True, capture_output=True,
        )
    except FileNotFoundError as exc:
        raise N9FixedError("tshark is required to read the D32 PCAP") from exc
    except subprocess.CalledProcessError as exc:
        raise N9FixedError("could not read D32 PCAP: %s" % exc.stderr.strip()) from exc
    return result.stdout.splitlines()


def extract_d32_frame(pcap_path: Path = D32_PCAP_PATH, *, lines: Iterable[str] | None = None) -> bytes:
    """Extract the final bus 3/address 7 D32 load frame without modifying it."""
    candidate: bytes | None = None
    for line in _tshark_lines(pcap_path) if lines is None else lines:
        fields = line.split("\t")
        if len(fields) != 3 or fields[0] != "3" or fields[1] != "7":
            continue
        try:
            frame = bytes.fromhex(fields[2])
        except ValueError:
            continue
        if len(frame) == REPORT_LEN and frame.startswith(LOAD_HEADER):
            candidate = frame
    if candidate is None:
        raise N9FixedError("D32 PCAP has no final target 26 04 frame")
    try:
        validate_color_frame(candidate)
    except ValueError as exc:
        raise N9FixedError("D32 frame failed shape validation: %s" % exc) from exc
    digest = hashlib.sha256(candidate).hexdigest()
    if digest != D32_FRAME_SHA256:
        raise N9FixedError("D32 frame hash mismatch: %s" % digest)
    return candidate


def _hid_id(name: str) -> str | None:
    try:
        for line in (SYSFS_HIDRAW_CLASS / name / "device" / "uevent").read_text().splitlines():
            if line.startswith("HID_ID="):
                return line[7:]
    except OSError:
        return None
    return None


def resolve_hidraw() -> Path:
    matches = [p.name for p in SYSFS_HIDRAW_CLASS.glob("hidraw*") if _hid_id(p.name) == TARGET_HID_ID]
    if len(matches) != 1:
        raise N9FixedError("expected exactly one N9 HID_ID %s, found %d" % (TARGET_HID_ID, len(matches)))
    return DEV_DIR / matches[0]


def _descriptor_ok(name: str) -> None:
    try:
        descriptor = (SYSFS_HIDRAW_CLASS / name / "device" / "report_descriptor").read_bytes()
    except OSError as exc:
        raise N9FixedError("cannot read N9 report descriptor") from exc
    if len(descriptor) != DESCRIPTOR_LEN or OUTPUT_26_SEQ not in descriptor:
        raise N9FixedError("N9 descriptor is not the expected 150-byte Output 0x26 descriptor")


def _sysfs_rdev(name: str) -> tuple[int, int]:
    try:
        major, minor = (SYSFS_HIDRAW_CLASS / name / "dev").read_text().strip().split(":")
        return int(major), int(minor)
    except (OSError, ValueError) as exc:
        raise N9FixedError("cannot validate N9 major:minor") from exc


def _open_flags() -> int:
    flags = os.O_WRONLY | os.O_NONBLOCK
    for name in ("O_CLOEXEC", "O_NOFOLLOW"):
        flags |= getattr(os, name, 0)
    return flags


def _verify_open_fd(fd: int, node: Path) -> None:
    info = os.fstat(fd)
    if not stat.S_ISCHR(info.st_mode):
        raise N9FixedError("resolved N9 node is no longer a character device")
    expected = _sysfs_rdev(node.name)
    actual = (os.major(info.st_rdev), os.minor(info.st_rdev))
    if actual != expected or _hid_id(node.name) != TARGET_HID_ID:
        raise N9FixedError("N9 node identity changed after open")
    _descriptor_ok(node.name)


def cpu_package_temperature_c() -> float:
    """Return one unambiguous package sensor, otherwise fail closed."""
    readings: list[float] = []
    for hwmon in Path("/sys/class/hwmon").glob("hwmon*"):
        for label in hwmon.glob("temp*_label"):
            try:
                if label.read_text().strip() not in {"CPU Package", "Package id 0"}:
                    continue
                value = label.with_name(label.name.removesuffix("_label") + "_input").read_text().strip()
                readings.append(int(value) / 1000)
            except (OSError, ValueError):
                continue
    if len(readings) != 1:
        raise N9FixedError("CPU Package temperature is unavailable or ambiguous")
    return readings[0]


def read_only_readiness() -> str:
    """Describe the real write preconditions without opening /dev/hidraw."""
    node = resolve_hidraw()
    _descriptor_ok(node.name)
    temperature = cpu_package_temperature_c()
    if temperature >= 85:
        raise N9FixedError("CPU Package is %.1f C, must be below 85 C" % temperature)
    return "%s listo, CPU Package %.1f C" % (node, temperature)


class N9FixedWriter:
    """Real writer with a fully closed target and exact two-write transaction."""
    def __init__(self, temperature_reader: Callable[[], float] = cpu_package_temperature_c) -> None:
        self.temperature_reader = temperature_reader

    def send(self, data: bytes, commit: bytes = COMMIT_FRAME) -> str:
        validate_color_frame(data)
        validate_commit_frame(commit)
        temperature = self.temperature_reader()
        if temperature >= 85:
            raise N9FixedError("CPU Package is %.1f C, must be below 85 C" % temperature)
        node = resolve_hidraw()
        _descriptor_ok(node.name)
        try:
            fd = os.open(str(node), _open_flags())
        except OSError as exc:
            raise N9FixedError("cannot open N9 device: %s" % exc) from exc
        try:
            _verify_open_fd(fd, node)
            written = os.write(fd, data)
            if written != REPORT_LEN:
                raise N9FixedError("data write was partial, commit was not sent")
            time.sleep(COMMIT_GAP_S)
            written = os.write(fd, commit)
            if written != REPORT_LEN:
                raise N9FixedError("commit write was partial")
        except OSError as exc:
            raise N9FixedError("N9 write failed without retry: %s" % exc) from exc
        finally:
            os.close(fd)
        return "%s, CPU Package %.1f C" % (node, temperature)


class OfflineWriter:
    """Test and laboratory mode.  It validates only, and never opens hidraw."""
    def __init__(self) -> None:
        self.sent: list[tuple[bytes, bytes]] = []

    def send(self, data: bytes, commit: bytes = COMMIT_FRAME) -> str:
        validate_color_frame(data)
        validate_commit_frame(commit)
        self.sent.append((data, commit))
        return "offline validation, zero hidraw writes"
