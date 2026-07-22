"""All writer tests use fake sysfs, fds and locks.  Never real hidraw."""
from __future__ import annotations

import hashlib
import os
import stat
import subprocess
import sys
import tempfile
import threading
import types
import unittest
from pathlib import Path
from unittest import mock

LIB = Path(__file__).resolve().parents[1] / "lib"
sys.path.insert(0, str(LIB))
import nzxt_n9_fixed as fixed


def _descriptor() -> bytes:
    descriptor = bytearray(150)
    descriptor[40:46] = fixed.OUTPUT_26_SEQ
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
    return types.SimpleNamespace(st_mode=stat.S_IFCHR | 0o600, st_rdev=os.makedev(240, 4))


class _NoopLock:
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None


def _writer_patches(sysfs: Path, dev: Path, node: Path, *, fstat_value=None):
    if fstat_value is None:
        fstat_value = _char_stat()
    return mock.patch.multiple(
        fixed,
        SYSFS_HIDRAW_CLASS=sysfs,
        DEV_DIR=dev,
    ), mock.patch.object(fixed.os, "lstat", return_value=_char_stat()), mock.patch.object(
        fixed.os, "access", return_value=True
    ), mock.patch.object(fixed.os, "fstat", return_value=fstat_value)


class ZoneVectorTests(unittest.TestCase):
    def test_selected_replacement_preserves_every_other_raw_triple(self) -> None:
        original = fixed.ZoneVector(tuple(bytes((index, 255 - index, index // 2)) for index in range(49)))
        changed = original.with_rgb({1, 48}, fixed.parse_hex_color("0E50AD"), 25)
        self.assertEqual(changed.triples[1], bytes.fromhex("27045b"))
        self.assertEqual(changed.triples[48], bytes.fromhex("27045b"))
        self.assertEqual(changed.triples[0], original.triples[0])
        self.assertEqual(changed.triples[17], original.triples[17])
        self.assertEqual(changed.triples[47], original.triples[47])

    def test_vector_frame_is_exact_49_grb_triples(self) -> None:
        vector = fixed.ZoneVector.from_rgb([(0, 0, 0)] * 49, 25)
        frame = vector.to_frame()
        self.assertEqual(frame[:4], fixed.LOAD_HEADER)
        self.assertEqual(frame[151:], bytes(361))
        self.assertEqual(fixed.ZoneVector.from_frame(frame), vector)

    def test_invalid_vector_fails_before_io(self) -> None:
        with self.assertRaises(ValueError):
            fixed.ZoneVector((b"\0\0\0",) * 48)
        with self.assertRaises(ValueError):
            fixed.ZoneVector.from_rgb([(1, 2, 3)] * 48, 25)

    def test_d32_parser_rejects_bad_hash_without_open(self) -> None:
        synthetic = fixed.ZoneVector.from_rgb([(0, 0, 0)] * 49, 25).to_frame()
        with mock.patch.object(fixed.os, "open", side_effect=AssertionError("opened")):
            with self.assertRaises(fixed.N9FixedError):
                fixed.extract_d32_frame(lines=["3\t7\t" + synthetic.hex()])

    @unittest.skipUnless(fixed.D32_PCAP_PATH.is_file(), "private D32 PCAP unavailable")
    def test_private_d32_capture_has_required_exact_hash_and_typed_api(self) -> None:
        vector = fixed.restore_d32_vector()
        self.assertEqual(hashlib.sha256(vector.to_frame()).hexdigest(), fixed.D32_FRAME_SHA256)
        fixed.validate_commit_frame(fixed.COMMIT_FRAME)


class WriterSafetyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.vector = fixed.ZoneVector.from_rgb([(255, 255, 255)] * 49, 25)

    def test_offline_writer_never_opens_hardware(self) -> None:
        writer = fixed.OfflineWriter()
        with mock.patch.object(fixed.os, "open", side_effect=AssertionError("opened")):
            result = writer.send_vector(self.vector)
        self.assertFalse(result.physical)
        self.assertIn("zero hidraw writes", result.detail)
        self.assertEqual(writer.sent, [self.vector])

    def test_temperature_abort_has_zero_preflight_opens_or_writes(self) -> None:
        writer = fixed.N9FixedWriter(temperature_reader=lambda: 85.0, lock_factory=_NoopLock)
        with mock.patch.object(fixed.os, "open", side_effect=AssertionError("open")), \
             mock.patch.object(fixed.os, "write", side_effect=AssertionError("write")):
            with self.assertRaises(fixed.N9FixedError):
                writer.send_vector(self.vector)

    def test_preopen_regular_node_aborts_before_open(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            sysfs, dev, node = _fake_sysfs(Path(temp))
            regular = types.SimpleNamespace(st_mode=stat.S_IFREG | 0o600, st_rdev=0)
            writer = fixed.N9FixedWriter(temperature_reader=lambda: 42.0, lock_factory=_NoopLock)
            with mock.patch.multiple(fixed, SYSFS_HIDRAW_CLASS=sysfs, DEV_DIR=dev), \
                 mock.patch.object(fixed.os, "lstat", return_value=regular), \
                 mock.patch.object(fixed.os, "open", side_effect=AssertionError("open")), \
                 mock.patch.object(fixed.os, "write", side_effect=AssertionError("write")):
                with self.assertRaises(fixed.N9FixedError):
                    writer.send_vector(self.vector)

    def test_preopen_permission_and_major_minor_are_checked(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            sysfs, dev, node = _fake_sysfs(Path(temp))
            writer = fixed.N9FixedWriter(temperature_reader=lambda: 42.0, lock_factory=_NoopLock)
            for stat_value, writable in ((_char_stat(), False), (types.SimpleNamespace(st_mode=stat.S_IFCHR | 0o600, st_rdev=os.makedev(240, 5)), True)):
                with self.subTest(writable=writable, rdev=stat_value.st_rdev), \
                     mock.patch.multiple(fixed, SYSFS_HIDRAW_CLASS=sysfs, DEV_DIR=dev), \
                     mock.patch.object(fixed.os, "lstat", return_value=stat_value), \
                     mock.patch.object(fixed.os, "access", return_value=writable), \
                     mock.patch.object(fixed.os, "open", side_effect=AssertionError("open")):
                    with self.assertRaises(fixed.N9FixedError):
                        writer.send_vector(self.vector)

    def test_success_uses_expected_flags_two_writes_and_exact_gap(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            sysfs, dev, node = _fake_sysfs(Path(temp))
            writes: list[bytes] = []
            sleeps: list[float] = []
            writer = fixed.N9FixedWriter(temperature_reader=lambda: 42.0, lock_factory=_NoopLock)
            patches = _writer_patches(sysfs, dev, node)
            with patches[0], patches[1], patches[2], patches[3], \
                 mock.patch.object(fixed.os, "open", return_value=9) as open_mock, \
                 mock.patch.object(fixed.os, "write", side_effect=lambda _fd, data: writes.append(data) or 512), \
                 mock.patch.object(fixed.os, "close"), \
                 mock.patch.object(fixed.time, "sleep", side_effect=sleeps.append):
                writer.send_vector(self.vector)
            self.assertEqual(writes, [self.vector.to_frame(), fixed.COMMIT_FRAME])
            self.assertEqual(sleeps, [fixed.COMMIT_GAP_S])
            self.assertEqual(open_mock.call_args.args[1], fixed._open_flags())

    def test_partial_data_never_sends_commit_and_partial_commit_never_retries(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            sysfs, dev, node = _fake_sysfs(Path(temp))
            writer = fixed.N9FixedWriter(temperature_reader=lambda: 42.0, lock_factory=_NoopLock)
            for results, expected_writes in (([8], 1), ([512, 8], 2)):
                writes: list[bytes] = []
                patches = _writer_patches(sysfs, dev, node)
                with self.subTest(results=results), patches[0], patches[1], patches[2], patches[3], \
                     mock.patch.object(fixed.os, "open", return_value=9), \
                     mock.patch.object(fixed.os, "write", side_effect=lambda _fd, data: writes.append(data) or results.pop(0)), \
                     mock.patch.object(fixed.os, "close"), \
                     mock.patch.object(fixed.time, "sleep"):
                    with self.assertRaises(fixed.N9OperationError) as context:
                        writer.send_vector(self.vector)
                self.assertEqual(context.exception.kind, fixed.FailureKind.WRITE)
                self.assertEqual(len(writes), expected_writes)

    def test_post_open_identity_failure_has_zero_writes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            sysfs, dev, node = _fake_sysfs(Path(temp))
            writer = fixed.N9FixedWriter(temperature_reader=lambda: 42.0, lock_factory=_NoopLock)
            patches = _writer_patches(sysfs, dev, node, fstat_value=types.SimpleNamespace(st_mode=stat.S_IFREG | 0o600, st_rdev=0))
            with patches[0], patches[1], patches[2], patches[3], \
                 mock.patch.object(fixed.os, "open", return_value=9), \
                 mock.patch.object(fixed.os, "write", side_effect=AssertionError("write")), \
                 mock.patch.object(fixed.os, "close"):
                with self.assertRaises(fixed.N9FixedError):
                    writer.send_vector(self.vector)

    def test_temperature_reader_rejects_ambiguous_sensor(self) -> None:
        with mock.patch.object(fixed.Path, "glob", return_value=[]):
            with self.assertRaises(fixed.N9FixedError):
                fixed.cpu_package_temperature_c()


class LockTests(unittest.TestCase):
    def test_local_lock_rejects_duplicate(self) -> None:
        with tempfile.TemporaryDirectory() as temp, mock.patch.dict(os.environ, {"XDG_RUNTIME_DIR": temp}):
            first = fixed.DeviceWriteLock()
            second = fixed.DeviceWriteLock()
            with first:
                with self.assertRaises(fixed.N9FixedError):
                    second.__enter__()
            with second:
                pass

    def test_cross_process_advisory_lock_rejects_duplicate(self) -> None:
        with tempfile.TemporaryDirectory() as temp, mock.patch.dict(os.environ, {"XDG_RUNTIME_DIR": temp}):
            path = Path(temp) / "nzxt-n9-1e71-2023.lock"
            script = (
                "import fcntl, pathlib, sys, time\n"
                "handle = pathlib.Path(sys.argv[1]).open('a+')\n"
                "fcntl.flock(handle, fcntl.LOCK_EX)\n"
                "print('locked', flush=True)\n"
                "time.sleep(5)\n"
            )
            process = subprocess.Popen(
                [sys.executable, "-c", script, str(path)],
                stdout=subprocess.PIPE,
                text=True,
            )
            try:
                assert process.stdout is not None
                self.assertEqual(process.stdout.readline().strip(), "locked")
                with self.assertRaises(fixed.N9FixedError):
                    fixed.DeviceWriteLock().__enter__()
            finally:
                process.terminate()
                process.wait(timeout=2)
                if process.stdout is not None:
                    process.stdout.close()


if __name__ == "__main__":
    unittest.main()
