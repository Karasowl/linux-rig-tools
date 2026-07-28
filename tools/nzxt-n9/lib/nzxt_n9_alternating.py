"""Closed Alternating D47 laboratory operations for the NZXT N9.

Only the two exact 512-byte frames measured in D47 exist here. This module is
not an encoder, does not expose arbitrary payloads and does not generalize the
D48 through D51 observations.
"""
from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Final

import nzxt_n9_fixed as fixed
from nzxt_n9_animated import (
    _animated_descriptor_ok,
    _animated_readiness,
    offline_restore_d32,
    real_restore_d32,
)
from nzxt_n9_fixed import (
    DeviceWriteLock,
    FailureKind,
    N9OperationError,
    Readiness,
    SendResult,
    _open_flags,
    _verify_open_fd,
    cpu_package_temperature_c,
)

REPORT_LEN: Final = 512
D47_PCAP_PATH: Final = Path(
    "/home/karasowl/vms/win11-cap/captures/nzxt-n9/"
    "2026-07-22-d47-alternating-movement-toggle/"
    "alternating-movement-toggle-private-bus.pcapng"
)
D47_PCAP_SHA256: Final = (
    "191335602dd41483881020cf148fc966543d5c626fda1aa6671b77360399a12f"
)
TRAVEL_RIGHT_NORMAL_FRAME_NUMBER: Final = 1477
IN_PLACE_RIGHT_NORMAL_FRAME_NUMBER: Final = 3725
TRAVEL_RIGHT_NORMAL_SHA256: Final = (
    "bb88f24351f7817582c5f591203c5cae3b4963ad4b6bb1e2fd244b56c9dee782"
)
IN_PLACE_RIGHT_NORMAL_SHA256: Final = (
    "a11850148cec0e00116a7ef2c851d8bf40514bd3ae532e0065c2cc51504023e6"
)
TRAVEL_RIGHT_NORMAL_CONFIRM_TOKEN: Final = (
    "I-CONFIRM-1E71:2023-LIGHTING-ONLY-APPLY-ALTERNATING-D47-"
    "TRAVEL-RIGHT-NORMAL"
)
IN_PLACE_RIGHT_NORMAL_CONFIRM_TOKEN: Final = (
    "I-CONFIRM-1E71:2023-LIGHTING-ONLY-APPLY-ALTERNATING-D47-"
    "IN-PLACE-RIGHT-NORMAL"
)
RESTORE_CONFIRM_TOKEN: Final = (
    "I-CONFIRM-1E71:2023-LIGHTING-ONLY-RESTORE-D32-FIXED"
)

_TRAVEL_RIGHT_NORMAL_FRAME: Final = bytes.fromhex(
    "2a04202005f4010028408b00610000000000000000000000000000000000000000000000000000000000000000000000"
    "000000000000000102003104000000000000000000000000000000000000000000000000000000000000000000000000"
    "000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
    "000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
    "000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
    "000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
    "000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
    "000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
    "000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
    "000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
    "0000000000000000000000000000000000000000000000000000000000000000"
)
_IN_PLACE_RIGHT_NORMAL_FRAME: Final = bytes.fromhex(
    "2a04202005e8030028408b00610000000000000000000000000000000000000000000000000000000000000000000000"
    "000000000000000002003104000000000000000000000000000000000000000000000000000000000000000000000000"
    "000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
    "000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
    "000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
    "000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
    "000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
    "000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
    "000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
    "000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
    "0000000000000000000000000000000000000000000000000000000000000000"
)


def _validate_exact_frame(
    frame: bytes,
    expected: bytes,
    expected_sha256: str,
    label: str,
) -> None:
    """Fail before I/O unless a frame is the named frozen D47 payload."""
    if len(frame) != REPORT_LEN:
        raise ValueError("%s frame must be exactly 512 bytes" % label)
    if frame[:2] != bytes.fromhex("2a04"):
        raise ValueError("%s frame opcode must be 2a 04" % label)
    if frame != expected:
        raise ValueError("%s frame differs from the frozen D47 payload" % label)
    if hashlib.sha256(frame).hexdigest() != expected_sha256:
        raise ValueError("%s frame hash differs from the frozen D47 value" % label)


@dataclass(frozen=True)
class AlternatingD47:
    """Parameter-free access to the two exact D47 frames."""

    def travel_right_normal_frame(self) -> bytes:
        frame = bytes(_TRAVEL_RIGHT_NORMAL_FRAME)
        _validate_exact_frame(
            frame,
            _TRAVEL_RIGHT_NORMAL_FRAME,
            TRAVEL_RIGHT_NORMAL_SHA256,
            "D47 travel-right-normal",
        )
        return frame

    def in_place_right_normal_frame(self) -> bytes:
        frame = bytes(_IN_PLACE_RIGHT_NORMAL_FRAME)
        _validate_exact_frame(
            frame,
            _IN_PLACE_RIGHT_NORMAL_FRAME,
            IN_PLACE_RIGHT_NORMAL_SHA256,
            "D47 in-place-right-normal",
        )
        return frame

    def validate_all(self) -> None:
        self.travel_right_normal_frame()
        self.in_place_right_normal_frame()


class AlternatingD47Writer:
    """Real writer with two closed D47 operations and no raw-frame method."""

    def __init__(
        self,
        temperature_reader: Callable[[], float] = cpu_package_temperature_c,
        lock_factory: Callable[[], DeviceWriteLock] = DeviceWriteLock,
    ) -> None:
        self.temperature_reader = temperature_reader
        self.lock_factory = lock_factory

    def preflight(self) -> Readiness:
        """Validate both D47 frames and readiness without opening hidraw."""
        AlternatingD47().validate_all()
        return _animated_readiness(self.temperature_reader)

    def apply_travel_right_normal(self) -> SendResult:
        return self._apply(
            AlternatingD47().travel_right_normal_frame(),
            "D47 travel-right-normal",
        )

    def apply_in_place_right_normal(self) -> SendResult:
        return self._apply(
            AlternatingD47().in_place_right_normal_frame(),
            "D47 in-place-right-normal",
        )

    def _apply(self, frame: bytes, label: str) -> SendResult:
        """Send one already-frozen frame under the lock shared with Fixed."""
        self._validate_selected(frame, label)
        with self.lock_factory():
            readiness = _animated_readiness(self.temperature_reader)
            self._send_selected(readiness.node, frame, label)
        return SendResult(
            True,
            "%s, CPU Package %.1f C, one exact %s write"
            % (readiness.node, readiness.temperature_c, label),
        )

    @staticmethod
    def _validate_selected(frame: bytes, label: str) -> None:
        if label == "D47 travel-right-normal":
            _validate_exact_frame(
                frame,
                _TRAVEL_RIGHT_NORMAL_FRAME,
                TRAVEL_RIGHT_NORMAL_SHA256,
                label,
            )
            return
        if label == "D47 in-place-right-normal":
            _validate_exact_frame(
                frame,
                _IN_PLACE_RIGHT_NORMAL_FRAME,
                IN_PLACE_RIGHT_NORMAL_SHA256,
                label,
            )
            return
        raise ValueError("unknown Alternating D47 operation")

    def _send_selected(self, node: Path, frame: bytes, label: str) -> None:
        """Open, revalidate and make exactly one 512-byte write attempt."""
        self._validate_selected(frame, label)
        try:
            fd = os.open(str(node), _open_flags())
        except OSError as exc:
            raise N9OperationError(
                FailureKind.DEVICE,
                "cannot open N9 device: %s" % exc,
            ) from exc
        write_attempted = False
        try:
            _verify_open_fd(fd, node)
            _animated_descriptor_ok(node.name)
            try:
                write_attempted = True
                written = os.write(fd, frame)
            except OSError as exc:
                raise N9OperationError(
                    FailureKind.WRITE,
                    "%s write failed without retry: %s" % (label, exc),
                ) from exc
            if written != REPORT_LEN:
                raise N9OperationError(
                    FailureKind.WRITE,
                    "%s write was partial and was not retried" % label,
                )
        finally:
            try:
                os.close(fd)
            except OSError as exc:
                kind = FailureKind.WRITE if write_attempted else FailureKind.DEVICE
                raise N9OperationError(
                    kind,
                    "close after %s write attempt failed: %s" % (label, exc),
                ) from exc


class OfflineAlternatingD47Writer:
    """Offline validator that never resolves, opens or writes hidraw."""

    def preflight(self) -> SendResult:
        AlternatingD47().validate_all()
        return SendResult(
            False,
            "offline D47 validation, zero hidraw resolves, opens or writes",
        )

    def apply_travel_right_normal(self) -> SendResult:
        AlternatingD47().travel_right_normal_frame()
        return SendResult(
            False,
            "offline D47 travel-right-normal validation, zero hidraw opens or writes",
        )

    def apply_in_place_right_normal(self) -> SendResult:
        AlternatingD47().in_place_right_normal_frame()
        return SendResult(
            False,
            "offline D47 in-place-right-normal validation, zero hidraw opens or writes",
        )
