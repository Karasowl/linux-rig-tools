"""Closed Spectrum Wave D35 laboratory operations for the NZXT N9.

This module can only validate or send the exact 512-byte D35 frame. It is not
an encoder or a general ``2a 04`` API. Fixed D32 restoration is delegated to
the already tested typed Fixed implementation.
"""
from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Final, Protocol

import nzxt_n9_fixed as fixed
from nzxt_n9_fixed import (
    DeviceWriteLock,
    FailureKind,
    N9FixedError,
    N9FixedWriter,
    N9OperationError,
    OfflineWriter,
    Readiness,
    SendResult,
    ZoneVector,
    _open_flags,
    _verify_open_fd,
    cpu_package_temperature_c,
    read_only_readiness,
    restore_d32_vector,
)

REPORT_LEN: Final = 512
D35_SHA256: Final = (
    "8b93db5f5b1552e93203d2e59be6734bae53c9d01b217f78744ab031603899ef"
)
D35_PREFIX: Final = bytes.fromhex("2a04202002fa")
D35_BYTES_58_59: Final = bytes.fromhex("3103")
OUTPUT_2A_SEQ: Final = bytes.fromhex("852a09019182")
APPLY_CONFIRM_TOKEN: Final = (
    "I-CONFIRM-1E71:2023-LIGHTING-ONLY-APPLY-SPECTRUM-WAVE-D35"
)
RESTORE_CONFIRM_TOKEN: Final = (
    "I-CONFIRM-1E71:2023-LIGHTING-ONLY-RESTORE-D32-FIXED"
)

_D35_FRAME: Final = (
    D35_PREFIX
    + bytes(58 - len(D35_PREFIX))
    + D35_BYTES_58_59
    + bytes(REPORT_LEN - 60)
)


def _validate_d35_frame(frame: bytes) -> None:
    """Fail before I/O unless ``frame`` is the exact frozen D35 payload."""
    if len(frame) != REPORT_LEN:
        raise ValueError("D35 Spectrum Wave frame must be exactly 512 bytes")
    if frame[:2] != bytes.fromhex("2a04"):
        raise ValueError("D35 Spectrum Wave frame opcode must be 2a 04")
    if frame != _D35_FRAME:
        raise ValueError("D35 Spectrum Wave frame differs from the frozen payload")
    digest = hashlib.sha256(frame).hexdigest()
    if digest != D35_SHA256:
        raise ValueError("D35 Spectrum Wave frame hash differs from the frozen value")


def _animated_descriptor_ok(name: str) -> None:
    """Require the real descriptor's Output Report ID 0x2a capability."""
    path = fixed.SYSFS_HIDRAW_CLASS / name / "device" / "report_descriptor"
    try:
        descriptor = path.read_bytes()
    except OSError as exc:
        raise N9FixedError("cannot read N9 animated report descriptor") from exc
    if len(descriptor) != fixed.DESCRIPTOR_LEN or OUTPUT_2A_SEQ not in descriptor:
        raise N9FixedError(
            "N9 descriptor is not the expected 150-byte Output 0x2a descriptor"
        )


def _animated_readiness(
    temperature_reader: Callable[[], float],
) -> Readiness:
    """Layer Output 0x2a validation onto the existing Fixed readiness."""
    readiness = read_only_readiness(temperature_reader)
    _animated_descriptor_ok(readiness.node.name)
    return readiness


@dataclass(frozen=True)
class SpectrumWaveD35:
    """Typed, parameter-free access to the exact captured D35 frame."""

    def validated_frame(self) -> bytes:
        frame = bytes(_D35_FRAME)
        _validate_d35_frame(frame)
        return frame


class FixedVectorWriter(Protocol):
    """Small typed surface shared by real and offline Fixed writers."""

    def send_vector(self, vector: ZoneVector) -> SendResult:
        ...


class SpectrumWaveD35Writer:
    """Real writer for one exact D35 frame. No retries and no second write."""

    def __init__(
        self,
        temperature_reader: Callable[[], float] = cpu_package_temperature_c,
        lock_factory: Callable[[], DeviceWriteLock] = DeviceWriteLock,
    ) -> None:
        self.temperature_reader = temperature_reader
        self.lock_factory = lock_factory

    def preflight(self) -> Readiness:
        """Validate D35 and target readiness without opening hidraw."""
        SpectrumWaveD35().validated_frame()
        return _animated_readiness(self.temperature_reader)

    def apply(self) -> SendResult:
        """Send D35 once under the lock shared with Fixed operations."""
        frame = SpectrumWaveD35().validated_frame()
        with self.lock_factory():
            readiness = _animated_readiness(self.temperature_reader)
            self._send_frame(readiness.node, frame)
        return SendResult(
            True,
            "%s, CPU Package %.1f C, one exact D35 write"
            % (readiness.node, readiness.temperature_c),
        )

    def _send_frame(self, node: Path, frame: bytes) -> None:
        """Open, revalidate and make exactly one 512-byte write attempt."""
        _validate_d35_frame(frame)
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
                    "D35 write failed without retry: %s" % exc,
                ) from exc
            if written != REPORT_LEN:
                raise N9OperationError(
                    FailureKind.WRITE,
                    "D35 write was partial and was not retried",
                )
        finally:
            try:
                os.close(fd)
            except OSError as exc:
                kind = FailureKind.WRITE if write_attempted else FailureKind.DEVICE
                raise N9OperationError(
                    kind,
                    "close after D35 write attempt failed: %s" % exc,
                ) from exc


class OfflineSpectrumWaveD35Writer:
    """Offline D35 validator. It never resolves, opens or writes hidraw."""

    def preflight(self) -> SendResult:
        SpectrumWaveD35().validated_frame()
        return SendResult(False, "offline D35 validation, zero hidraw opens or writes")

    def apply(self) -> SendResult:
        SpectrumWaveD35().validated_frame()
        return SendResult(False, "offline D35 validation, zero hidraw opens or writes")


def restore_d32(
    writer: FixedVectorWriter,
    loader: Callable[[], ZoneVector] = restore_d32_vector,
) -> SendResult:
    """Load the typed D32 vector and delegate its exact Fixed transaction."""
    vector = loader()
    if not isinstance(vector, ZoneVector):
        raise N9FixedError("D32 loader did not return a typed ZoneVector")
    return writer.send_vector(vector)


def real_restore_d32() -> SendResult:
    """Restore through the existing real Fixed writer."""
    return restore_d32(N9FixedWriter())


def offline_restore_d32() -> SendResult:
    """Validate D32 through the existing offline Fixed writer."""
    return restore_d32(OfflineWriter())
