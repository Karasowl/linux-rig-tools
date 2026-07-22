"""Closed protocol, vector model and writer for the NZXT N9 Fixed lab.

Only the capture-backed ``26 04`` 49-zone frame and the fixed ``26 06``
commit exist here.  There is deliberately no public API for raw HID bytes.
"""
from __future__ import annotations

import fcntl
import hashlib
import math
import os
import stat
import subprocess
import tempfile
import threading
import time
from dataclasses import dataclass
from enum import Enum
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
_PROCESS_WRITE_LOCK = threading.Lock()


class N9FixedError(RuntimeError):
    """Closed failure.  The caller must not automatically retry it."""


class FailureKind(Enum):
    D32_LOAD = "d32-load"
    LOCK_BUSY = "lock-busy"
    DEVICE = "device"
    THERMAL = "thermal"
    WRITE = "write"


class N9OperationError(N9FixedError):
    """Closed error with a machine-readable kind for the UI state machine."""
    def __init__(self, kind: FailureKind, message: str) -> None:
        super().__init__(message)
        self.kind = kind


def failure_kind(error: Exception) -> FailureKind:
    if isinstance(error, N9OperationError):
        return error.kind
    message = str(error)
    if "CPU Package" in message:
        return FailureKind.THERMAL
    if "N9" in message or "descriptor" in message or "writable" in message:
        return FailureKind.DEVICE
    return FailureKind.WRITE


Rgb = tuple[int, int, int]


def srgb_decode(value: float) -> float:
    return value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4


def srgb_encode(value: float) -> float:
    return 12.92 * value if value <= 0.0031308 else 1.055 * (value ** (1 / 2.4)) - 0.055


def component_byte(component: int, brightness: int) -> int:
    """Per-zone scale-255 candidate, an explicit thesis rather than CAM fact."""
    if not isinstance(component, int) or not 0 <= component <= 255:
        raise ValueError("RGB component must be an integer from 0 to 255")
    if not isinstance(brightness, int) or not 0 <= brightness <= 100:
        raise ValueError("brightness must be an integer from 0 to 100")
    linear = srgb_decode(component / 255) * (brightness / 100)
    return math.floor(255 * srgb_encode(linear) + 0.422545474091919)


def parse_hex_color(text: str) -> Rgb:
    text = text.strip().removeprefix("#")
    if len(text) != 6 or any(char not in "0123456789abcdefABCDEF" for char in text):
        raise ValueError("color must be exactly six hexadecimal RGB digits")
    return tuple(int(text[offset : offset + 2], 16) for offset in (0, 2, 4))  # type: ignore[return-value]


@dataclass(frozen=True)
class ZoneVector:
    """Authoritative 49-zone raw GRB vector.

    The raw triples are what gets sent.  RGB and brightness are used only when
    replacing selected zones, so every unselected triple remains byte literal.
    """

    triples: tuple[bytes, ...]

    def __post_init__(self) -> None:
        if len(self.triples) != ZONE_COUNT or any(len(triple) != 3 for triple in self.triples):
            raise ValueError("ZoneVector requires exactly 49 three-byte GRB triples")

    @classmethod
    def from_rgb(cls, colors: Iterable[Rgb], brightness: int) -> "ZoneVector":
        triples = []
        for red, green, blue in colors:
            triples.append(bytes((
                component_byte(green, brightness),
                component_byte(red, brightness),
                component_byte(blue, brightness),
            )))
        return cls(tuple(triples))

    @classmethod
    def from_frame(cls, frame: bytes) -> "ZoneVector":
        validate_color_frame(frame)
        return cls(tuple(frame[4 + index * 3 : 7 + index * 3] for index in range(ZONE_COUNT)))

    def with_rgb(self, selected: Iterable[int], color: Rgb, brightness: int) -> "ZoneVector":
        selected = frozenset(selected)
        if any(not isinstance(index, int) or not 0 <= index < ZONE_COUNT for index in selected):
            raise ValueError("selected zone index is outside 0..48")
        red, green, blue = color
        replacement = bytes((
            component_byte(green, brightness),
            component_byte(red, brightness),
            component_byte(blue, brightness),
        ))
        return ZoneVector(tuple(replacement if index in selected else triple for index, triple in enumerate(self.triples)))

    def to_frame(self) -> bytes:
        frame = LOAD_HEADER + b"".join(self.triples) + bytes(REPORT_LEN - 4 - ZONE_COUNT * 3)
        validate_color_frame(frame)
        return frame

    def display_rgb(self, index: int) -> Rgb:
        """Raw GRB display proxy, not a claimed reconstruction of CAM RGB."""
        green, red, blue = self.triples[index]
        return red, green, blue


def build_color_frame(colors: Iterable[Rgb], brightness: int) -> bytes:
    """Compatibility helper.  New callers should retain a ZoneVector instead."""
    return ZoneVector.from_rgb(colors, brightness).to_frame()


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
    """Read-only extraction of the final D32 target frame from its private PCAP."""
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
    validate_color_frame(candidate)
    digest = hashlib.sha256(candidate).hexdigest()
    if digest != D32_FRAME_SHA256:
        raise N9FixedError("D32 frame hash mismatch: %s" % digest)
    return candidate


def restore_d32_vector(pcap_path: Path = D32_PCAP_PATH) -> ZoneVector:
    """Public typed restoration API.  Raw extraction stays inside this module."""
    return ZoneVector.from_frame(extract_d32_frame(pcap_path))


def _hid_id(name: str) -> str | None:
    try:
        for line in (SYSFS_HIDRAW_CLASS / name / "device" / "uevent").read_text().splitlines():
            if line.startswith("HID_ID="):
                return line[7:]
    except OSError:
        return None
    return None


def resolve_hidraw() -> Path:
    matches = [path.name for path in SYSFS_HIDRAW_CLASS.glob("hidraw*") if _hid_id(path.name) == TARGET_HID_ID]
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


def _device_stat(node: Path, *, follow: bool) -> os.stat_result:
    try:
        return os.stat(node) if follow else os.lstat(node)
    except OSError as exc:
        raise N9FixedError("cannot stat N9 node %s" % node) from exc


def _verify_node_before_open(node: Path) -> None:
    info = _device_stat(node, follow=False)
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISCHR(info.st_mode):
        raise N9FixedError("resolved N9 node is not a direct character device")
    actual = (os.major(info.st_rdev), os.minor(info.st_rdev))
    if actual != _sysfs_rdev(node.name):
        raise N9FixedError("resolved N9 node major:minor differs from sysfs")
    if not os.access(node, os.W_OK):
        raise N9FixedError("N9 node is not writable by this user")
    if _hid_id(node.name) != TARGET_HID_ID:
        raise N9FixedError("N9 HID_ID changed before open")
    _descriptor_ok(node.name)


def _open_flags() -> int:
    flags = os.O_WRONLY | os.O_NONBLOCK
    for name in ("O_CLOEXEC", "O_NOFOLLOW"):
        flags |= getattr(os, name, 0)
    return flags


def _verify_open_fd(fd: int, node: Path) -> None:
    info = os.fstat(fd)
    if not stat.S_ISCHR(info.st_mode):
        raise N9FixedError("resolved N9 node is no longer a character device")
    if (os.major(info.st_rdev), os.minor(info.st_rdev)) != _sysfs_rdev(node.name):
        raise N9FixedError("N9 node identity changed after open")
    if _hid_id(node.name) != TARGET_HID_ID:
        raise N9FixedError("N9 HID_ID changed after open")
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


@dataclass(frozen=True)
class Readiness:
    node: Path
    temperature_c: float


@dataclass(frozen=True)
class SendResult:
    """Separates a physical HID transaction from an offline frame validation."""
    physical: bool
    detail: str


def read_only_readiness(temperature_reader: Callable[[], float] = cpu_package_temperature_c) -> Readiness:
    """Check a real target without opening hidraw."""
    node = resolve_hidraw()
    _verify_node_before_open(node)
    temperature = temperature_reader()
    if temperature >= 85:
        raise N9FixedError("CPU Package is %.1f C, must be below 85 C" % temperature)
    return Readiness(node, temperature)


class DeviceWriteLock:
    """Nonblocking process and cross-process lock for the one fixed N9 target."""
    def __init__(self) -> None:
        runtime = Path(os.environ.get("XDG_RUNTIME_DIR", "/run/user/%d" % os.getuid()))
        base = runtime if runtime.is_dir() else Path(tempfile.gettempdir())
        self.path = base / "nzxt-n9-1e71-2023.lock"
        self.fd = -1

    def __enter__(self) -> "DeviceWriteLock":
        if not _PROCESS_WRITE_LOCK.acquire(blocking=False):
            raise N9OperationError(FailureKind.LOCK_BUSY, "another N9 Fixed operation is already in progress")
        try:
            flags = os.O_CREAT | os.O_RDWR | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
            self.fd = os.open(str(self.path), flags, 0o600)
            fcntl.flock(self.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except (OSError, BlockingIOError) as exc:
            if self.fd >= 0:
                os.close(self.fd)
                self.fd = -1
            _PROCESS_WRITE_LOCK.release()
            raise N9OperationError(FailureKind.LOCK_BUSY, "another process holds the N9 Fixed lock") from exc
        return self

    def __exit__(self, _type, _value, _traceback) -> None:
        try:
            if self.fd >= 0:
                fcntl.flock(self.fd, fcntl.LOCK_UN)
                os.close(self.fd)
        finally:
            self.fd = -1
            _PROCESS_WRITE_LOCK.release()


class N9FixedWriter:
    """Typed real writer.  Its raw two-frame transaction remains private."""
    def __init__(
        self,
        temperature_reader: Callable[[], float] = cpu_package_temperature_c,
        lock_factory: Callable[[], DeviceWriteLock] = DeviceWriteLock,
    ) -> None:
        self.temperature_reader = temperature_reader
        self.lock_factory = lock_factory

    def send_vector(self, vector: ZoneVector) -> SendResult:
        """Send one typed vector.  Any duplicate or failure is returned closed."""
        data = vector.to_frame()
        validate_commit_frame(COMMIT_FRAME)
        with self.lock_factory():
            readiness = read_only_readiness(self.temperature_reader)
            self._send_frames(readiness.node, data, COMMIT_FRAME)
        return SendResult(True, "%s, CPU Package %.1f C" % (readiness.node, readiness.temperature_c))

    def _send_frames(self, node: Path, data: bytes, commit: bytes) -> None:
        """Exact private data, 3 ms gap, commit transaction.  Never retries."""
        try:
            fd = os.open(str(node), _open_flags())
        except OSError as exc:
            raise N9FixedError("cannot open N9 device: %s" % exc) from exc
        try:
            _verify_open_fd(fd, node)
            if os.write(fd, data) != REPORT_LEN:
                raise N9FixedError("data write was partial, commit was not sent")
            time.sleep(COMMIT_GAP_S)
            if os.write(fd, commit) != REPORT_LEN:
                raise N9FixedError("commit write was partial")
        except OSError as exc:
            raise N9FixedError("N9 write failed without retry: %s" % exc) from exc
        finally:
            os.close(fd)


class OfflineWriter:
    """Typed laboratory writer that validates frames and never opens hidraw."""
    def __init__(self) -> None:
        self.sent: list[ZoneVector] = []

    def send_vector(self, vector: ZoneVector) -> SendResult:
        validate_color_frame(vector.to_frame())
        validate_commit_frame(COMMIT_FRAME)
        self.sent.append(vector)
        return SendResult(False, "offline validation, zero hidraw writes")
