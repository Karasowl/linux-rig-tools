"""Offline tests for the per-zone Fixed model and closed writer."""
from __future__ import annotations

import hashlib
import os
import stat
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

LIB = Path(__file__).resolve().parents[1] / "lib"
sys.path.insert(0, str(LIB))
import nzxt_n9_fixed as fixed


def _descriptor() -> bytes:
    value = bytearray(150)
    value[40:46] = fixed.OUTPUT_26_SEQ
    return bytes(value)


def _fake_sysfs(root: Path) -> tuple[Path, Path]:
    sysfs = root / "sys" / "class" / "hidraw"
    device = sysfs / "hidraw4" / "device"
    device.mkdir(parents=True)
    (device / "uevent").write_text("HID_ID=%s\n" % fixed.TARGET_HID_ID)
    (device / "report_descriptor").write_bytes(_descriptor())
    (sysfs / "hidraw4" / "dev").write_text("240:4\n")
    dev = root / "dev"
    dev.mkdir()
    return sysfs, dev


class PerZoneModelTests(unittest.TestCase):
    def test_zone_vector_has_grb_and_49_triples(self) -> None:
        colors = [(0, 0, 0)] * 49
        colors[1] = fixed.parse_hex_color("0E50AD")
        frame = fixed.build_color_frame(colors, 25)
        self.assertEqual(frame[:4], fixed.LOAD_HEADER)
        self.assertEqual(frame[7:10], bytes.fromhex("27045b"))
        self.assertEqual(frame[4:7], bytes(3))
        self.assertEqual(frame[151:], bytes(361))

    def test_invalid_vector_and_commit_fail_before_io(self) -> None:
        with self.assertRaises(ValueError):
            fixed.build_color_frame([(1, 2, 3)] * 48, 25)
        with self.assertRaises(ValueError):
            fixed.validate_commit_frame(b"bad")

    def test_offline_writer_never_opens_hardware(self) -> None:
        frame = fixed.build_color_frame([(255, 255, 255)] * 49, 25)
        writer = fixed.OfflineWriter()
        with mock.patch.object(fixed.os, "open", side_effect=AssertionError("opened")):
            self.assertIn("zero hidraw writes", writer.send(frame))
        self.assertEqual(len(writer.sent), 1)

    def test_d32_parser_rejects_bad_hash_without_any_write(self) -> None:
        synthetic = fixed.build_color_frame([(0, 0, 0)] * 49, 25)
        with mock.patch.object(fixed.os, "open", side_effect=AssertionError("opened")):
            with self.assertRaises(fixed.N9FixedError):
                fixed.extract_d32_frame(lines=["3\t7\t" + synthetic.hex()])

    @unittest.skipUnless(fixed.D32_PCAP_PATH.is_file(), "private D32 PCAP unavailable")
    def test_private_d32_capture_has_required_exact_hash(self) -> None:
        frame = fixed.extract_d32_frame()
        self.assertEqual(hashlib.sha256(frame).hexdigest(), fixed.D32_FRAME_SHA256)
        fixed.validate_commit_frame(fixed.COMMIT_FRAME)
        self.assertEqual(fixed.COMMIT_FRAME[:16], bytes.fromhex("26062000010000310000800032000001"))


class WriterSafetyTests(unittest.TestCase):
    def test_temperature_abort_has_zero_writes_and_zero_opens(self) -> None:
        frame = fixed.build_color_frame([(255, 255, 255)] * 49, 25)
        writer = fixed.N9FixedWriter(temperature_reader=lambda: 85.0)
        with mock.patch.object(fixed.os, "open", side_effect=AssertionError("open")), \
             mock.patch.object(fixed.os, "write", side_effect=AssertionError("write")):
            with self.assertRaises(fixed.N9FixedError):
                writer.send(frame)

    def test_post_open_identity_failure_has_zero_writes(self) -> None:
        frame = fixed.build_color_frame([(255, 255, 255)] * 49, 25)
        with tempfile.TemporaryDirectory() as temp:
            sysfs, dev = _fake_sysfs(Path(temp))
            fake_stat = types.SimpleNamespace(st_mode=stat.S_IFREG | 0o600, st_rdev=0)
            writer = fixed.N9FixedWriter(temperature_reader=lambda: 42.0)
            with mock.patch.object(fixed, "SYSFS_HIDRAW_CLASS", sysfs), \
                 mock.patch.object(fixed, "DEV_DIR", dev), \
                 mock.patch.object(fixed.os, "open", return_value=9), \
                 mock.patch.object(fixed.os, "fstat", return_value=fake_stat), \
                 mock.patch.object(fixed.os, "write", side_effect=AssertionError("write")), \
                 mock.patch.object(fixed.os, "close"):
                with self.assertRaises(fixed.N9FixedError):
                    writer.send(frame)

    def test_partial_data_does_not_send_commit(self) -> None:
        frame = fixed.build_color_frame([(255, 255, 255)] * 49, 25)
        with tempfile.TemporaryDirectory() as temp:
            sysfs, dev = _fake_sysfs(Path(temp))
            char_stat = types.SimpleNamespace(st_mode=stat.S_IFCHR | 0o600, st_rdev=os.makedev(240, 4))
            writes: list[bytes] = []
            writer = fixed.N9FixedWriter(temperature_reader=lambda: 42.0)
            def write(_fd: int, data: bytes) -> int:
                writes.append(data)
                return 8
            with mock.patch.object(fixed, "SYSFS_HIDRAW_CLASS", sysfs), \
                 mock.patch.object(fixed, "DEV_DIR", dev), \
                 mock.patch.object(fixed.os, "open", return_value=9), \
                 mock.patch.object(fixed.os, "fstat", return_value=char_stat), \
                 mock.patch.object(fixed.os, "write", side_effect=write), \
                 mock.patch.object(fixed.os, "close"):
                with self.assertRaises(fixed.N9FixedError):
                    writer.send(frame)
            self.assertEqual(writes, [frame])


if __name__ == "__main__":
    unittest.main()
