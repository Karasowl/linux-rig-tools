"""All animated-lab writes use fakes. Never open real hidraw."""
from __future__ import annotations

import contextlib
import hashlib
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

TOOL_ROOT = Path(__file__).resolve().parents[1]
LIB = TOOL_ROOT / "lib"
CLI = TOOL_ROOT / "bin" / "nzxt-n9-animated-write-lab"
D35_PCAP = Path(
    "/home/karasowl/vms/win11-cap/captures/nzxt-n9/"
    "2026-07-21-d35-spectrum-wave-from-fixed/"
    "spectrum-wave-from-fixed-private-bus.pcapng"
)
sys.path.insert(0, str(LIB))

import nzxt_n9_animated as animated
import nzxt_n9_fixed as fixed


def _descriptor(*, include_2a: bool = True) -> bytes:
    descriptor = bytearray(150)
    descriptor[40:46] = fixed.OUTPUT_26_SEQ
    if include_2a:
        descriptor[60:66] = animated.OUTPUT_2A_SEQ
    return bytes(descriptor)


def _fake_sysfs(root: Path) -> tuple[Path, Path, Path]:
    sysfs = root / "sys" / "class" / "hidraw"
    device = sysfs / "hidraw4" / "device"
    device.mkdir(parents=True)
    (device / "uevent").write_text("HID_ID=%s\n" % fixed.TARGET_HID_ID)
    (device / "report_descriptor").write_bytes(_descriptor())
    (sysfs / "hidraw4" / "dev").write_text("240:4\n")
    dev = root / "dev"
    dev.mkdir()
    node = dev / "hidraw4"
    node.touch()
    return sysfs, dev, node


def _char_stat() -> types.SimpleNamespace:
    return types.SimpleNamespace(
        st_mode=stat.S_IFCHR | 0o600,
        st_rdev=os.makedev(240, 4),
    )


class _NoopLock:
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None


class _FakeFixedWriter:
    def __init__(self) -> None:
        self.vectors: list[fixed.ZoneVector] = []

    def send_vector(self, vector: fixed.ZoneVector) -> fixed.SendResult:
        self.vectors.append(vector)
        return fixed.SendResult(False, "delegated")


class FrameTests(unittest.TestCase):
    def test_exact_512_byte_frame_and_hash(self) -> None:
        frame = animated.SpectrumWaveD35().validated_frame()
        self.assertEqual(len(frame), 512)
        self.assertEqual(frame[:7], bytes.fromhex("2a04202002fa00"))
        self.assertEqual(frame[58:60], bytes.fromhex("3103"))
        self.assertEqual(hashlib.sha256(frame).hexdigest(), animated.D35_SHA256)
        self.assertEqual(
            [(index, value) for index, value in enumerate(frame) if value],
            [
                (0, 0x2A),
                (1, 0x04),
                (2, 0x20),
                (3, 0x20),
                (4, 0x02),
                (5, 0xFA),
                (58, 0x31),
                (59, 0x03),
            ],
        )

    def test_validation_rejects_every_mutated_byte(self) -> None:
        original = animated.SpectrumWaveD35().validated_frame()
        for index in range(len(original)):
            mutated = bytearray(original)
            mutated[index] ^= 0x01
            with self.subTest(index=index), self.assertRaises(ValueError):
                animated._validate_d35_frame(bytes(mutated))

    def test_validation_rejects_wrong_length_and_opcode(self) -> None:
        frame = animated.SpectrumWaveD35().validated_frame()
        with self.assertRaises(ValueError):
            animated._validate_d35_frame(frame[:-1])
        mutated = bytearray(frame)
        mutated[0] = 0x26
        with self.assertRaises(ValueError):
            animated._validate_d35_frame(bytes(mutated))

    def test_private_d35_pcap_matches_frozen_frame_when_available(self) -> None:
        tshark = shutil.which("tshark")
        if not D35_PCAP.is_file() or tshark is None:
            self.skipTest("private D35 PCAP or tshark is unavailable")
        result = subprocess.run(
            [
                tshark,
                "-r",
                str(D35_PCAP),
                "-Y",
                (
                    "usb.bus_id == 3 && usb.device_address == 7 && "
                    "usb.transfer_type == 0x01 && "
                    "usb.endpoint_address.direction == 0 && usb.capdata"
                ),
                "-T",
                "fields",
                "-e",
                "usb.capdata",
            ],
            text=True,
            capture_output=True,
            check=True,
        )
        target_frames = []
        for line in result.stdout.splitlines():
            try:
                frame = bytes.fromhex(line)
            except ValueError:
                continue
            if frame.startswith(bytes.fromhex("2a04")):
                target_frames.append(frame)
        self.assertEqual(len(target_frames), 1)
        frame = target_frames[0]
        self.assertEqual(len(frame), 512)
        self.assertEqual(hashlib.sha256(frame).hexdigest(), animated.D35_SHA256)
        self.assertEqual(frame, animated.SpectrumWaveD35().validated_frame())


class WriterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        root = Path(self.tempdir.name)
        self.sysfs, self.dev, self.node = _fake_sysfs(root)
        self.stack = contextlib.ExitStack()
        self.stack.enter_context(
            mock.patch.object(fixed, "SYSFS_HIDRAW_CLASS", self.sysfs)
        )
        self.stack.enter_context(mock.patch.object(fixed, "DEV_DIR", self.dev))
        self.stack.enter_context(
            mock.patch.object(fixed.os, "lstat", return_value=_char_stat())
        )
        self.stack.enter_context(
            mock.patch.object(fixed.os, "access", return_value=True)
        )
        self.stack.enter_context(
            mock.patch.object(fixed.os, "fstat", return_value=_char_stat())
        )

    def tearDown(self) -> None:
        self.stack.close()
        self.tempdir.cleanup()

    def _writer(self) -> animated.SpectrumWaveD35Writer:
        return animated.SpectrumWaveD35Writer(
            temperature_reader=lambda: 54.0,
            lock_factory=_NoopLock,
        )

    def test_offline_preflight_and_apply_never_touch_hardware(self) -> None:
        writer = animated.OfflineSpectrumWaveD35Writer()
        with mock.patch.object(
            animated.os,
            "open",
            side_effect=AssertionError("opened"),
        ), mock.patch.object(
            animated.os,
            "write",
            side_effect=AssertionError("wrote"),
        ), mock.patch.object(
            fixed,
            "resolve_hidraw",
            side_effect=AssertionError("resolved"),
        ):
            self.assertFalse(writer.preflight().physical)
            self.assertFalse(writer.apply().physical)

    def test_real_preflight_never_opens_hidraw(self) -> None:
        with mock.patch.object(
            animated.os,
            "open",
            side_effect=AssertionError("opened"),
        ), mock.patch.object(
            animated.os,
            "write",
            side_effect=AssertionError("wrote"),
        ):
            readiness = self._writer().preflight()
        self.assertEqual(readiness.node, self.node)

    def test_success_is_one_exact_write(self) -> None:
        writes: list[bytes] = []
        with mock.patch.object(animated.os, "open", return_value=31), mock.patch.object(
            animated.os,
            "write",
            side_effect=lambda _fd, data: writes.append(data) or len(data),
        ), mock.patch.object(animated.os, "close"):
            result = self._writer().apply()
        self.assertTrue(result.physical)
        self.assertEqual(writes, [animated.SpectrumWaveD35().validated_frame()])

    def test_write_error_is_one_attempt_without_retry(self) -> None:
        write = mock.Mock(side_effect=OSError("synthetic"))
        with mock.patch.object(animated.os, "open", return_value=31), mock.patch.object(
            animated.os,
            "write",
            write,
        ), mock.patch.object(animated.os, "close"):
            with self.assertRaises(fixed.N9OperationError):
                self._writer().apply()
        self.assertEqual(write.call_count, 1)

    def test_partial_write_is_one_attempt_without_retry(self) -> None:
        write = mock.Mock(return_value=511)
        with mock.patch.object(animated.os, "open", return_value=31), mock.patch.object(
            animated.os,
            "write",
            write,
        ), mock.patch.object(animated.os, "close"):
            with self.assertRaises(fixed.N9OperationError):
                self._writer().apply()
        self.assertEqual(write.call_count, 1)

    def test_pre_open_failure_produces_zero_writes(self) -> None:
        write = mock.Mock()
        with mock.patch.object(fixed.os, "access", return_value=False), mock.patch.object(
            animated.os,
            "open",
        ) as open_mock, mock.patch.object(animated.os, "write", write):
            with self.assertRaises(fixed.N9FixedError):
                self._writer().apply()
        open_mock.assert_not_called()
        write.assert_not_called()

    def test_missing_output_2a_fails_before_open_with_zero_writes(self) -> None:
        descriptor_path = (
            self.sysfs / "hidraw4" / "device" / "report_descriptor"
        )
        descriptor_path.write_bytes(_descriptor(include_2a=False))
        write = mock.Mock()
        with mock.patch.object(animated.os, "open") as open_mock, mock.patch.object(
            animated.os,
            "write",
            write,
        ):
            with self.assertRaisesRegex(fixed.N9FixedError, "Output 0x2a"):
                self._writer().apply()
        open_mock.assert_not_called()
        write.assert_not_called()

    def test_mutated_frozen_frame_fails_before_lock_or_io(self) -> None:
        mutated = bytearray(animated.SpectrumWaveD35().validated_frame())
        mutated[59] ^= 0x01
        lock_factory = mock.Mock(side_effect=AssertionError("locked"))
        with mock.patch.object(
            animated,
            "_D35_FRAME",
            bytes(mutated),
        ), mock.patch.object(
            animated.os,
            "open",
            side_effect=AssertionError("opened"),
        ), mock.patch.object(
            animated.os,
            "write",
            side_effect=AssertionError("wrote"),
        ):
            with self.assertRaises(ValueError):
                animated.SpectrumWaveD35Writer(
                    temperature_reader=lambda: 54.0,
                    lock_factory=lock_factory,
                ).apply()
        lock_factory.assert_not_called()

    def test_post_open_failure_produces_zero_writes(self) -> None:
        write = mock.Mock()
        wrong = types.SimpleNamespace(
            st_mode=stat.S_IFCHR | 0o600,
            st_rdev=os.makedev(240, 5),
        )
        with mock.patch.object(animated.os, "open", return_value=31), mock.patch.object(
            fixed.os,
            "fstat",
            return_value=wrong,
        ), mock.patch.object(animated.os, "write", write), mock.patch.object(
            animated.os,
            "close",
        ):
            with self.assertRaises(fixed.N9FixedError):
                self._writer().apply()
        write.assert_not_called()

    def test_output_2a_loss_after_open_produces_zero_writes(self) -> None:
        write = mock.Mock()
        full_descriptor = _descriptor()
        fixed_only_descriptor = _descriptor(include_2a=False)
        with mock.patch.object(
            Path,
            "read_bytes",
            side_effect=[
                full_descriptor,
                full_descriptor,
                full_descriptor,
                fixed_only_descriptor,
            ],
        ), mock.patch.object(
            animated.os,
            "open",
            return_value=31,
        ), mock.patch.object(
            animated.os,
            "write",
            write,
        ), mock.patch.object(
            animated.os,
            "close",
        ):
            with self.assertRaisesRegex(fixed.N9FixedError, "Output 0x2a"):
                self._writer().apply()
        write.assert_not_called()

    def test_fixed_lock_blocks_animated_writer(self) -> None:
        runtime = Path(self.tempdir.name) / "runtime"
        runtime.mkdir()
        writer = animated.SpectrumWaveD35Writer(temperature_reader=lambda: 54.0)
        with mock.patch.dict(os.environ, {"XDG_RUNTIME_DIR": str(runtime)}):
            with fixed.DeviceWriteLock():
                with mock.patch.object(
                    animated.os,
                    "write",
                    side_effect=AssertionError("wrote"),
                ):
                    with self.assertRaises(fixed.N9OperationError) as raised:
                        writer.apply()
        self.assertEqual(raised.exception.kind, fixed.FailureKind.LOCK_BUSY)


class RestoreTests(unittest.TestCase):
    def test_restore_delegates_typed_vector_without_reconstruction(self) -> None:
        expected = fixed.ZoneVector(
            tuple(bytes((index, 0, 0)) for index in range(49))
        )
        writer = _FakeFixedWriter()
        loader = mock.Mock(return_value=expected)
        result = animated.restore_d32(writer, loader)
        self.assertEqual(result.detail, "delegated")
        loader.assert_called_once_with()
        self.assertEqual(writer.vectors, [expected])
        self.assertIs(writer.vectors[0], expected)

    def test_restore_rejects_untyped_loader_result(self) -> None:
        writer = _FakeFixedWriter()
        with self.assertRaises(fixed.N9FixedError):
            animated.restore_d32(writer, lambda: bytes(512))  # type: ignore[arg-type]
        self.assertEqual(writer.vectors, [])

    def test_offline_restore_uses_existing_fixed_offline_writer(self) -> None:
        expected = fixed.ZoneVector((bytes(3),) * 49)
        with mock.patch.object(
            animated.os,
            "open",
            side_effect=AssertionError("opened"),
        ), mock.patch.object(
            animated.os,
            "write",
            side_effect=AssertionError("wrote"),
        ):
            result = animated.restore_d32(fixed.OfflineWriter(), lambda: expected)
        self.assertFalse(result.physical)
        self.assertIn("offline validation", result.detail)

    def test_real_restore_d32_constructs_fixed_writer_and_delegates(self) -> None:
        writer = mock.Mock(spec=fixed.N9FixedWriter)
        expected = fixed.SendResult(True, "real delegated")
        with mock.patch.object(
            animated,
            "N9FixedWriter",
            return_value=writer,
        ) as constructor, mock.patch.object(
            animated,
            "restore_d32",
            return_value=expected,
        ) as delegate:
            result = animated.real_restore_d32()
        self.assertIs(result, expected)
        constructor.assert_called_once_with()
        delegate.assert_called_once_with(writer)

    def test_offline_restore_d32_constructs_offline_writer_and_delegates(
        self,
    ) -> None:
        writer = mock.Mock(spec=fixed.OfflineWriter)
        expected = fixed.SendResult(False, "offline delegated")
        with mock.patch.object(
            animated,
            "OfflineWriter",
            return_value=writer,
        ) as constructor, mock.patch.object(
            animated,
            "restore_d32",
            return_value=expected,
        ) as delegate:
            result = animated.offline_restore_d32()
        self.assertIs(result, expected)
        constructor.assert_called_once_with()
        delegate.assert_called_once_with(writer)


class CliTests(unittest.TestCase):
    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(CLI), *args],
            text=True,
            capture_output=True,
            check=False,
        )

    def test_help_states_scope_and_physical_qa_limit(self) -> None:
        result = self.run_cli("--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("not a general 2a 04", result.stdout)
        self.assertIn("replace physical QA", result.stdout)

    def test_offline_apply_requires_exact_distinct_token(self) -> None:
        wrong = self.run_cli("--offline", "apply-spectrum-wave", "wrong")
        self.assertEqual(wrong.returncode, 2)
        self.assertIn(animated.APPLY_CONFIRM_TOKEN, wrong.stderr)
        restore_token = self.run_cli(
            "--offline",
            "apply-spectrum-wave",
            animated.RESTORE_CONFIRM_TOKEN,
        )
        self.assertEqual(restore_token.returncode, 2)
        accepted = self.run_cli(
            "--offline",
            "apply-spectrum-wave",
            animated.APPLY_CONFIRM_TOKEN,
        )
        self.assertEqual(accepted.returncode, 0)
        self.assertIn("zero hidraw opens or writes", accepted.stdout)

    def test_offline_restore_rejects_apply_token(self) -> None:
        result = self.run_cli(
            "--offline",
            "restore-d32",
            animated.APPLY_CONFIRM_TOKEN,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn(animated.RESTORE_CONFIRM_TOKEN, result.stderr)

    def test_cli_rejects_extra_and_arbitrary_inputs(self) -> None:
        extra = self.run_cli(
            "--offline",
            "apply-spectrum-wave",
            animated.APPLY_CONFIRM_TOKEN,
            "payload",
        )
        self.assertEqual(extra.returncode, 2)
        unknown = self.run_cli("--offline", "write", "2a04")
        self.assertEqual(unknown.returncode, 2)
        missing = self.run_cli("--offline", "restore-d32")
        self.assertEqual(missing.returncode, 2)

    def test_offline_preflight_does_not_need_hardware(self) -> None:
        result = self.run_cli("--offline", "preflight")
        self.assertEqual(result.returncode, 0)
        self.assertIn("zero hidraw opens or writes", result.stdout)


if __name__ == "__main__":
    unittest.main()
