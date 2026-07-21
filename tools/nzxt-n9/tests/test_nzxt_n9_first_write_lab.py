#!/usr/bin/env python3
"""Offline unit tests for nzxt-n9-first-write-lab.

No real hardware. Sysfs and device nodes are temporary directories.
os.open / os.write / os.close / os.fstat / time.sleep are mocked for write paths.
"""

from __future__ import annotations

import importlib.machinery
import importlib.util
import io
import os
import stat
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

# Load the lab harness as a module from its bin path (not installed as a package).
# The bin script has no .py suffix, so provide an explicit SourceFileLoader.
_LAB_PATH = (
    Path(__file__).resolve().parents[1] / "bin" / "nzxt-n9-first-write-lab"
)
_LOADER = importlib.machinery.SourceFileLoader(
    "nzxt_n9_first_write_lab", str(_LAB_PATH)
)
_SPEC = importlib.util.spec_from_loader(_LOADER.name, _LOADER)
assert _SPEC is not None and _SPEC.loader is not None
lab = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(lab)


# Default fake hidraw major:minor (offline only, not a real kernel mapping).
_DEFAULT_MAJOR = 245
_DEFAULT_MINOR = 1


# Minimal 150-byte HID report descriptor containing Output Report ID 0x26
# sequence 85 26 09 01 91 82 (as observed on the N9 Z890).
def _make_descriptor(valid: bool = True) -> bytes:
    seq = bytes([0x85, 0x26, 0x09, 0x01, 0x91, 0x82])
    if not valid:
        seq = bytes([0x85, 0x10, 0x09, 0x01, 0x91, 0x82])  # different Report ID
    body = bytearray(150)
    # Place the sequence at a mid offset so the "in" check is not trivial.
    body[40:46] = seq
    return bytes(body)


def _expected_open_flags() -> int:
    flags = os.O_WRONLY | os.O_NONBLOCK
    if hasattr(os, "O_CLOEXEC"):
        flags |= os.O_CLOEXEC
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    return flags


def _make_char_stat(
    major: int = _DEFAULT_MAJOR, minor: int = _DEFAULT_MINOR
) -> types.SimpleNamespace:
    """Build a minimal os.stat_result-like object for a character device."""
    return types.SimpleNamespace(
        st_mode=stat.S_IFCHR | 0o600,
        st_rdev=os.makedev(major, minor),
    )


def _make_non_char_stat() -> types.SimpleNamespace:
    """Build a stat-like object that is NOT a character device (regular file)."""
    return types.SimpleNamespace(
        st_mode=stat.S_IFREG | 0o644,
        st_rdev=0,
    )


def _install_fake_sysfs(
    root: Path,
    *,
    names: list[str] | None = None,
    hid_ids: dict[str, str] | None = None,
    descriptor: bytes | None = None,
    desc_by_name: dict[str, bytes] | None = None,
    dev_numbers: dict[str, tuple[int, int]] | None = None,
) -> Path:
    """Create a fake /sys/class/hidraw tree under root. Returns class dir.

    Each hidrawN gets device/uevent, device/report_descriptor, and a `dev`
    file with major:minor (required for post-open fd binding).
    """
    class_dir = root / "class" / "hidraw"
    class_dir.mkdir(parents=True)
    if names is None:
        names = ["hidraw1"]
    if hid_ids is None:
        hid_ids = {n: lab.TARGET_HID_ID for n in names}
    if descriptor is None:
        descriptor = _make_descriptor(valid=True)

    for idx, name in enumerate(names):
        node_dir = class_dir / name
        dev = node_dir / "device"
        dev.mkdir(parents=True)
        hid_id = hid_ids.get(name, "0003:00000000:00000000")
        (dev / "uevent").write_text(
            "DRIVER=hid-generic\nHID_ID=%s\nHID_NAME=NZXT N9 Z890\n" % hid_id,
            encoding="utf-8",
        )
        desc = (
            desc_by_name[name]
            if desc_by_name and name in desc_by_name
            else descriptor
        )
        (dev / "report_descriptor").write_bytes(desc)
        if dev_numbers and name in dev_numbers:
            major, minor = dev_numbers[name]
        else:
            major, minor = _DEFAULT_MAJOR, _DEFAULT_MINOR + idx
        (node_dir / "dev").write_text("%d:%d\n" % (major, minor), encoding="utf-8")
    return class_dir


class FrameConstructionTests(unittest.TestCase):
    def test_red_frame_shape(self) -> None:
        frame = lab.build_color_frame(lab.RED_TRIPLE)
        self.assertEqual(len(frame), 512)
        self.assertEqual(frame[0:4], bytes([0x26, 0x04, 0x20, 0x00]))
        for i in range(49):
            start = 4 + i * 3
            self.assertEqual(
                frame[start : start + 3],
                bytes([0x00, 0x4A, 0x00]),
                "triple %d" % i,
            )
        self.assertTrue(all(b == 0 for b in frame[4 + 49 * 3 :]))
        lab.validate_color_frame(frame, lab.RED_TRIPLE)

    def test_white_frame_shape(self) -> None:
        frame = lab.build_color_frame(lab.WHITE_TRIPLE)
        self.assertEqual(len(frame), 512)
        self.assertEqual(frame[0:4], bytes([0x26, 0x04, 0x20, 0x00]))
        for i in range(49):
            start = 4 + i * 3
            self.assertEqual(
                frame[start : start + 3],
                bytes([0x4A, 0x4A, 0x4A]),
                "triple %d" % i,
            )
        self.assertTrue(all(b == 0 for b in frame[4 + 49 * 3 :]))
        lab.validate_color_frame(frame, lab.WHITE_TRIPLE)

    def test_model_yellow40_frame_shape(self) -> None:
        frame = lab.build_color_frame(lab.YELLOW40_TRIPLE)
        self.assertEqual(len(frame), 512)
        self.assertEqual(frame[0:4], bytes([0x26, 0x04, 0x20, 0x00]))
        for i in range(49):
            start = 4 + i * 3
            self.assertEqual(
                frame[start : start + 3],
                bytes([0x89, 0xA9, 0x00]),
                "triple %d" % i,
            )
        self.assertTrue(all(b == 0 for b in frame[4 + 49 * 3 :]))
        lab.validate_color_frame(frame, lab.YELLOW40_TRIPLE)

    def test_commit_frame_shape(self) -> None:
        frame = lab.build_commit_frame()
        self.assertEqual(len(frame), 512)
        expected_prefix = bytes.fromhex(
            "26062000010000310000800032000001"
        )
        self.assertEqual(frame[0:16], expected_prefix)
        self.assertTrue(all(b == 0 for b in frame[16:]))
        lab.validate_commit_frame(frame)

    def test_build_and_validate_frames_returns_four(self) -> None:
        red, white, yellow40, commit = lab.build_and_validate_frames()
        self.assertEqual(len(red), 512)
        self.assertEqual(len(white), 512)
        self.assertEqual(len(yellow40), 512)
        self.assertEqual(len(commit), 512)
        self.assertNotEqual(red, white)
        self.assertNotEqual(yellow40, red)
        self.assertNotEqual(yellow40, white)
        self.assertEqual(red[4:7], bytes([0x00, 0x4A, 0x00]))
        self.assertEqual(white[4:7], bytes([0x4A, 0x4A, 0x4A]))
        self.assertEqual(yellow40[4:7], bytes([0x89, 0xA9, 0x00]))


class PreflightTests(unittest.TestCase):
    def test_preflight_finds_one_valid_device_without_opening_hidraw(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            class_dir = _install_fake_sysfs(root)
            dev_dir = root / "dev"
            dev_dir.mkdir()
            # Deliberately do NOT create a real hidraw node under /dev.
            opened: list[str] = []

            def fake_open(path, flags, *a, **k):
                opened.append(str(path))
                raise AssertionError(
                    "preflight must never open hidraw, got %r flags=%r"
                    % (path, flags)
                )

            with mock.patch.object(lab, "SYSFS_HIDRAW_CLASS", str(class_dir)):
                with mock.patch.object(lab, "DEV_DIR", str(dev_dir)):
                    with mock.patch.object(lab.os, "open", side_effect=fake_open):
                        buf = io.StringIO()
                        with mock.patch.object(sys, "stdout", buf):
                            rc = lab.cmd_preflight()
            self.assertEqual(rc, 0)
            self.assertEqual(opened, [])
            out = buf.getvalue()
            self.assertIn(str(dev_dir / "hidraw1"), out)
            self.assertIn("sha256", out.lower())
            self.assertIn("ff 03", out)
            self.assertIn("no", out.lower())  # cannot check RPM
            # Digests of all frozen frames must appear.
            red, white, yellow40, commit = lab.build_and_validate_frames()
            self.assertIn(lab.sha256_hex(red), out)
            self.assertIn(lab.sha256_hex(white), out)
            self.assertIn(lab.sha256_hex(yellow40), out)
            self.assertIn(lab.sha256_hex(commit), out)
            self.assertIn("not captured from CAM", out)

    def test_preflight_rejects_zero_devices(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            class_dir = root / "class" / "hidraw"
            class_dir.mkdir(parents=True)
            # Empty class dir, or a non-matching device.
            other = class_dir / "hidraw0" / "device"
            other.mkdir(parents=True)
            (other / "uevent").write_text(
                "HID_ID=0003:00001234:00005678\n", encoding="utf-8"
            )
            with mock.patch.object(lab, "SYSFS_HIDRAW_CLASS", str(class_dir)):
                with self.assertRaises(SystemExit) as ctx:
                    lab.cmd_preflight()
            self.assertEqual(ctx.exception.code, 1)

    def test_preflight_rejects_multiple_devices(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            class_dir = _install_fake_sysfs(
                root, names=["hidraw1", "hidraw3"]
            )
            with mock.patch.object(lab, "SYSFS_HIDRAW_CLASS", str(class_dir)):
                with self.assertRaises(SystemExit) as ctx:
                    lab.cmd_preflight()
            self.assertEqual(ctx.exception.code, 1)

    def test_preflight_rejects_wrong_descriptor_length(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            class_dir = _install_fake_sysfs(
                root, descriptor=b"\x00" * 64  # wrong length
            )
            with mock.patch.object(lab, "SYSFS_HIDRAW_CLASS", str(class_dir)):
                with self.assertRaises(SystemExit) as ctx:
                    lab.cmd_preflight()
            self.assertEqual(ctx.exception.code, 1)

    def test_preflight_rejects_descriptor_missing_output_26(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            class_dir = _install_fake_sysfs(
                root, descriptor=_make_descriptor(valid=False)
            )
            with mock.patch.object(lab, "SYSFS_HIDRAW_CLASS", str(class_dir)):
                with self.assertRaises(SystemExit) as ctx:
                    lab.cmd_preflight()
            self.assertEqual(ctx.exception.code, 1)


class WritePathTests(unittest.TestCase):
    def _patch_env(self, class_dir: Path, dev_dir: Path):
        return mock.patch.multiple(
            lab,
            SYSFS_HIDRAW_CLASS=str(class_dir),
            DEV_DIR=str(dev_dir),
        )

    def _matching_fstat(self, expected_fd: int):
        def fake_fstat(fd):
            self.assertEqual(fd, expected_fd)
            return _make_char_stat()

        return fake_fstat

    def test_wrong_token_fails_before_open(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            class_dir = _install_fake_sysfs(root)
            dev_dir = root / "dev"
            dev_dir.mkdir()
            opened: list[object] = []

            def fake_open(*a, **k):
                opened.append(a)
                raise AssertionError("must not open with wrong token")

            with self._patch_env(class_dir, dev_dir):
                with mock.patch.object(lab.os, "open", side_effect=fake_open):
                    with self.assertRaises(SystemExit) as ctx:
                        lab.cmd_apply_red(["WRONG-TOKEN"])
            self.assertEqual(ctx.exception.code, 1)
            self.assertEqual(opened, [])

            with self._patch_env(class_dir, dev_dir):
                with mock.patch.object(lab.os, "open", side_effect=fake_open):
                    with self.assertRaises(SystemExit) as ctx:
                        lab.cmd_restore_white([])
            self.assertEqual(ctx.exception.code, 1)
            self.assertEqual(opened, [])

            with self._patch_env(class_dir, dev_dir):
                with mock.patch.object(lab.os, "open", side_effect=fake_open):
                    with self.assertRaises(SystemExit) as ctx:
                        lab.cmd_apply_model_yellow40(["WRONG-TOKEN"])
            self.assertEqual(ctx.exception.code, 1)
            self.assertEqual(opened, [])

    def test_apply_red_two_writes_in_order_with_gap(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            class_dir = _install_fake_sysfs(root)
            dev_dir = root / "dev"
            dev_dir.mkdir()
            expected_node = str(dev_dir / "hidraw1")
            red, _white, _yellow40, commit = lab.build_and_validate_frames()

            writes: list[tuple[int, bytes]] = []
            sleeps: list[float] = []
            state = {"fd": 17, "open_flags": None, "closed": False}

            def fake_open(path, flags, *a, **k):
                self.assertEqual(str(path), expected_node)
                self.assertEqual(flags, _expected_open_flags())
                state["open_flags"] = flags
                return state["fd"]

            def fake_write(fd, data):
                self.assertEqual(fd, state["fd"])
                writes.append((fd, bytes(data)))
                return len(data)

            def fake_close(fd):
                self.assertEqual(fd, state["fd"])
                state["closed"] = True

            def fake_sleep(s):
                sleeps.append(s)

            with self._patch_env(class_dir, dev_dir):
                with mock.patch.object(lab.os, "open", side_effect=fake_open):
                    with mock.patch.object(
                        lab.os, "fstat", side_effect=self._matching_fstat(17)
                    ):
                        with mock.patch.object(
                            lab.os, "write", side_effect=fake_write
                        ):
                            with mock.patch.object(
                                lab.os, "close", side_effect=fake_close
                            ):
                                with mock.patch.object(
                                    lab.time, "sleep", side_effect=fake_sleep
                                ):
                                    buf = io.StringIO()
                                    with mock.patch.object(sys, "stdout", buf):
                                        rc = lab.cmd_apply_red(
                                            [lab.CONFIRM_TOKEN]
                                        )
            self.assertEqual(rc, 0)
            self.assertTrue(state["closed"])
            self.assertEqual(len(writes), 2)
            self.assertEqual(writes[0][1], red)
            self.assertEqual(writes[1][1], commit)
            self.assertEqual(len(writes[0][1]), 512)
            self.assertEqual(len(writes[1][1]), 512)
            self.assertEqual(sleeps, [0.003])
            out = buf.getvalue()
            self.assertIn("cannot evaluate cooling", out.lower())

    def test_restore_white_two_writes_in_order_with_gap(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            class_dir = _install_fake_sysfs(root)
            dev_dir = root / "dev"
            dev_dir.mkdir()
            expected_node = str(dev_dir / "hidraw1")
            _red, white, _yellow40, commit = lab.build_and_validate_frames()

            writes: list[bytes] = []
            sleeps: list[float] = []
            state = {"fd": 9, "closed": False}

            def fake_open(path, flags, *a, **k):
                self.assertEqual(str(path), expected_node)
                self.assertEqual(flags, _expected_open_flags())
                return state["fd"]

            def fake_write(fd, data):
                writes.append(bytes(data))
                return len(data)

            def fake_close(fd):
                state["closed"] = True

            def fake_sleep(s):
                sleeps.append(s)

            with self._patch_env(class_dir, dev_dir):
                with mock.patch.object(lab.os, "open", side_effect=fake_open):
                    with mock.patch.object(
                        lab.os, "fstat", side_effect=self._matching_fstat(9)
                    ):
                        with mock.patch.object(
                            lab.os, "write", side_effect=fake_write
                        ):
                            with mock.patch.object(
                                lab.os, "close", side_effect=fake_close
                            ):
                                with mock.patch.object(
                                    lab.time, "sleep", side_effect=fake_sleep
                                ):
                                    buf = io.StringIO()
                                    with mock.patch.object(sys, "stdout", buf):
                                        rc = lab.cmd_restore_white(
                                            [lab.CONFIRM_TOKEN]
                                        )
            self.assertEqual(rc, 0)
            self.assertTrue(state["closed"])
            self.assertEqual(len(writes), 2)
            self.assertEqual(writes[0], white)
            self.assertEqual(writes[1], commit)
            self.assertEqual(sleeps, [0.003])
            out = buf.getvalue()
            self.assertIn("cyan", out.lower())

    def test_apply_model_yellow40_two_writes_in_order_with_gap(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            class_dir = _install_fake_sysfs(root)
            dev_dir = root / "dev"
            dev_dir.mkdir()
            expected_node = str(dev_dir / "hidraw1")
            _red, _white, yellow40, commit = lab.build_and_validate_frames()

            writes: list[bytes] = []
            sleeps: list[float] = []
            state = {"fd": 29, "closed": False}

            def fake_open(path, flags, *a, **k):
                self.assertEqual(str(path), expected_node)
                self.assertEqual(flags, _expected_open_flags())
                return state["fd"]

            def fake_write(fd, data):
                self.assertEqual(fd, state["fd"])
                writes.append(bytes(data))
                return len(data)

            def fake_close(fd):
                self.assertEqual(fd, state["fd"])
                state["closed"] = True

            with self._patch_env(class_dir, dev_dir):
                with mock.patch.object(lab.os, "open", side_effect=fake_open):
                    with mock.patch.object(
                        lab.os, "fstat", side_effect=self._matching_fstat(29)
                    ):
                        with mock.patch.object(
                            lab.os, "write", side_effect=fake_write
                        ):
                            with mock.patch.object(
                                lab.os, "close", side_effect=fake_close
                            ):
                                with mock.patch.object(
                                    lab.time, "sleep", side_effect=sleeps.append
                                ):
                                    buf = io.StringIO()
                                    with mock.patch.object(sys, "stdout", buf):
                                        rc = lab.cmd_apply_model_yellow40(
                                            [lab.CONFIRM_TOKEN]
                                        )
            self.assertEqual(rc, 0)
            self.assertTrue(state["closed"])
            self.assertEqual(writes, [yellow40, commit])
            self.assertEqual(sleeps, [0.003])
            out = buf.getvalue()
            self.assertIn("89 a9 00", out.lower())
            self.assertIn("not a CAM-captured", out)

    def test_partial_first_write_aborts_without_commit_or_retry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            class_dir = _install_fake_sysfs(root)
            dev_dir = root / "dev"
            dev_dir.mkdir()

            writes: list[bytes] = []
            sleeps: list[float] = []
            state = {"fd": 3, "closed": False}

            def fake_open(path, flags, *a, **k):
                return state["fd"]

            def fake_write(fd, data):
                writes.append(bytes(data))
                # Partial: report fewer bytes than requested.
                return 100

            def fake_close(fd):
                state["closed"] = True

            def fake_sleep(s):
                sleeps.append(s)

            with self._patch_env(class_dir, dev_dir):
                with mock.patch.object(lab.os, "open", side_effect=fake_open):
                    with mock.patch.object(
                        lab.os, "fstat", side_effect=self._matching_fstat(3)
                    ):
                        with mock.patch.object(
                            lab.os, "write", side_effect=fake_write
                        ):
                            with mock.patch.object(
                                lab.os, "close", side_effect=fake_close
                            ):
                                with mock.patch.object(
                                    lab.time, "sleep", side_effect=fake_sleep
                                ):
                                    with self.assertRaises(SystemExit) as ctx:
                                        lab.cmd_apply_red([lab.CONFIRM_TOKEN])
            self.assertEqual(ctx.exception.code, 1)
            self.assertEqual(len(writes), 1)  # only first write attempted
            self.assertEqual(sleeps, [])  # no gap, no commit
            self.assertTrue(state["closed"])

    def test_partial_second_write_aborts_without_retry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            class_dir = _install_fake_sysfs(root)
            dev_dir = root / "dev"
            dev_dir.mkdir()

            write_sizes: list[int] = []
            state = {"fd": 4, "closed": False, "n": 0}

            def fake_open(path, flags, *a, **k):
                return state["fd"]

            def fake_write(fd, data):
                state["n"] += 1
                write_sizes.append(len(data))
                if state["n"] == 1:
                    return 512
                return 200  # partial commit

            def fake_close(fd):
                state["closed"] = True

            with self._patch_env(class_dir, dev_dir):
                with mock.patch.object(lab.os, "open", side_effect=fake_open):
                    with mock.patch.object(
                        lab.os, "fstat", side_effect=self._matching_fstat(4)
                    ):
                        with mock.patch.object(
                            lab.os, "write", side_effect=fake_write
                        ):
                            with mock.patch.object(
                                lab.os, "close", side_effect=fake_close
                            ):
                                with mock.patch.object(lab.time, "sleep"):
                                    with self.assertRaises(SystemExit) as ctx:
                                        lab.cmd_restore_white(
                                            [lab.CONFIRM_TOKEN]
                                        )
            self.assertEqual(ctx.exception.code, 1)
            self.assertEqual(write_sizes, [512, 512])  # two attempts only
            self.assertEqual(state["n"], 2)  # no third write / retry
            self.assertTrue(state["closed"])


class FdBindingTests(unittest.TestCase):
    """Post-open fd ↔ sysfs binding before the first os.write."""

    def _patch_env(self, class_dir: Path, dev_dir: Path):
        return mock.patch.multiple(
            lab,
            SYSFS_HIDRAW_CLASS=str(class_dir),
            DEV_DIR=str(dev_dir),
        )

    def test_char_fd_matching_major_minor_allows_both_writes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            class_dir = _install_fake_sysfs(
                root,
                dev_numbers={"hidraw1": (_DEFAULT_MAJOR, _DEFAULT_MINOR)},
            )
            dev_dir = root / "dev"
            dev_dir.mkdir()
            red, _white, _yellow40, commit = lab.build_and_validate_frames()

            writes: list[bytes] = []
            state = {"fd": 21, "closed": False}

            def fake_open(path, flags, *a, **k):
                return state["fd"]

            def fake_fstat(fd):
                self.assertEqual(fd, state["fd"])
                return _make_char_stat(_DEFAULT_MAJOR, _DEFAULT_MINOR)

            def fake_write(fd, data):
                writes.append(bytes(data))
                return len(data)

            def fake_close(fd):
                state["closed"] = True

            with self._patch_env(class_dir, dev_dir):
                with mock.patch.object(lab.os, "open", side_effect=fake_open):
                    with mock.patch.object(
                        lab.os, "fstat", side_effect=fake_fstat
                    ):
                        with mock.patch.object(
                            lab.os, "write", side_effect=fake_write
                        ):
                            with mock.patch.object(
                                lab.os, "close", side_effect=fake_close
                            ):
                                with mock.patch.object(lab.time, "sleep"):
                                    rc = lab.cmd_apply_red([lab.CONFIRM_TOKEN])
            self.assertEqual(rc, 0)
            self.assertEqual(len(writes), 2)
            self.assertEqual(writes[0], red)
            self.assertEqual(writes[1], commit)
            self.assertTrue(state["closed"])

    def test_non_char_fd_aborts_with_zero_writes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            class_dir = _install_fake_sysfs(root)
            dev_dir = root / "dev"
            dev_dir.mkdir()

            writes: list[bytes] = []
            state = {"fd": 22, "closed": False}

            def fake_open(path, flags, *a, **k):
                return state["fd"]

            def fake_fstat(fd):
                return _make_non_char_stat()

            def fake_write(fd, data):
                writes.append(bytes(data))
                return len(data)

            def fake_close(fd):
                state["closed"] = True

            with self._patch_env(class_dir, dev_dir):
                with mock.patch.object(lab.os, "open", side_effect=fake_open):
                    with mock.patch.object(
                        lab.os, "fstat", side_effect=fake_fstat
                    ):
                        with mock.patch.object(
                            lab.os, "write", side_effect=fake_write
                        ):
                            with mock.patch.object(
                                lab.os, "close", side_effect=fake_close
                            ):
                                with mock.patch.object(lab.time, "sleep"):
                                    with self.assertRaises(SystemExit) as ctx:
                                        lab.cmd_apply_red([lab.CONFIRM_TOKEN])
            self.assertEqual(ctx.exception.code, 1)
            self.assertEqual(writes, [])
            self.assertTrue(state["closed"])

    def test_mismatched_major_minor_aborts_with_zero_writes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            # Sysfs says 245:1, fstat will claim 245:99.
            class_dir = _install_fake_sysfs(
                root,
                dev_numbers={"hidraw1": (_DEFAULT_MAJOR, _DEFAULT_MINOR)},
            )
            dev_dir = root / "dev"
            dev_dir.mkdir()

            writes: list[bytes] = []
            state = {"fd": 23, "closed": False}

            def fake_open(path, flags, *a, **k):
                return state["fd"]

            def fake_fstat(fd):
                return _make_char_stat(_DEFAULT_MAJOR, 99)

            def fake_write(fd, data):
                writes.append(bytes(data))
                return len(data)

            def fake_close(fd):
                state["closed"] = True

            with self._patch_env(class_dir, dev_dir):
                with mock.patch.object(lab.os, "open", side_effect=fake_open):
                    with mock.patch.object(
                        lab.os, "fstat", side_effect=fake_fstat
                    ):
                        with mock.patch.object(
                            lab.os, "write", side_effect=fake_write
                        ):
                            with mock.patch.object(
                                lab.os, "close", side_effect=fake_close
                            ):
                                with mock.patch.object(lab.time, "sleep"):
                                    with self.assertRaises(SystemExit) as ctx:
                                        lab.cmd_restore_white(
                                            [lab.CONFIRM_TOKEN]
                                        )
            self.assertEqual(ctx.exception.code, 1)
            self.assertEqual(writes, [])
            self.assertTrue(state["closed"])

    def test_hid_id_changed_after_open_aborts_with_zero_writes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            class_dir = _install_fake_sysfs(root)
            dev_dir = root / "dev"
            dev_dir.mkdir()
            uevent = class_dir / "hidraw1" / "device" / "uevent"

            writes: list[bytes] = []
            state = {"fd": 24, "closed": False}

            def fake_open(path, flags, *a, **k):
                # Race: HID_ID changes after open, before write.
                uevent.write_text(
                    "DRIVER=hid-generic\n"
                    "HID_ID=0003:00009999:00008888\n"
                    "HID_NAME=OTHER\n",
                    encoding="utf-8",
                )
                return state["fd"]

            def fake_fstat(fd):
                return _make_char_stat()

            def fake_write(fd, data):
                writes.append(bytes(data))
                return len(data)

            def fake_close(fd):
                state["closed"] = True

            with self._patch_env(class_dir, dev_dir):
                with mock.patch.object(lab.os, "open", side_effect=fake_open):
                    with mock.patch.object(
                        lab.os, "fstat", side_effect=fake_fstat
                    ):
                        with mock.patch.object(
                            lab.os, "write", side_effect=fake_write
                        ):
                            with mock.patch.object(
                                lab.os, "close", side_effect=fake_close
                            ):
                                with mock.patch.object(lab.time, "sleep"):
                                    with self.assertRaises(SystemExit) as ctx:
                                        lab.cmd_apply_red([lab.CONFIRM_TOKEN])
            self.assertEqual(ctx.exception.code, 1)
            self.assertEqual(writes, [])
            self.assertTrue(state["closed"])

    def test_descriptor_changed_after_open_aborts_with_zero_writes(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            class_dir = _install_fake_sysfs(root)
            dev_dir = root / "dev"
            dev_dir.mkdir()
            desc_path = class_dir / "hidraw1" / "device" / "report_descriptor"

            writes: list[bytes] = []
            state = {"fd": 25, "closed": False}

            def fake_open(path, flags, *a, **k):
                # Race: descriptor mutates after open, before write.
                desc_path.write_bytes(_make_descriptor(valid=False))
                return state["fd"]

            def fake_fstat(fd):
                return _make_char_stat()

            def fake_write(fd, data):
                writes.append(bytes(data))
                return len(data)

            def fake_close(fd):
                state["closed"] = True

            with self._patch_env(class_dir, dev_dir):
                with mock.patch.object(lab.os, "open", side_effect=fake_open):
                    with mock.patch.object(
                        lab.os, "fstat", side_effect=fake_fstat
                    ):
                        with mock.patch.object(
                            lab.os, "write", side_effect=fake_write
                        ):
                            with mock.patch.object(
                                lab.os, "close", side_effect=fake_close
                            ):
                                with mock.patch.object(lab.time, "sleep"):
                                    with self.assertRaises(SystemExit) as ctx:
                                        lab.cmd_apply_red([lab.CONFIRM_TOKEN])
            self.assertEqual(ctx.exception.code, 1)
            self.assertEqual(writes, [])
            self.assertTrue(state["closed"])

    def test_open_flags_include_nofollow_and_cloexec_when_available(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            class_dir = _install_fake_sysfs(root)
            dev_dir = root / "dev"
            dev_dir.mkdir()
            seen_flags: list[int] = []
            state = {"fd": 26}

            def fake_open(path, flags, *a, **k):
                seen_flags.append(flags)
                return state["fd"]

            def fake_fstat(fd):
                return _make_char_stat()

            def fake_write(fd, data):
                return len(data)

            with self._patch_env(class_dir, dev_dir):
                with mock.patch.object(lab.os, "open", side_effect=fake_open):
                    with mock.patch.object(
                        lab.os, "fstat", side_effect=fake_fstat
                    ):
                        with mock.patch.object(
                            lab.os, "write", side_effect=fake_write
                        ):
                            with mock.patch.object(lab.os, "close"):
                                with mock.patch.object(lab.time, "sleep"):
                                    rc = lab.cmd_apply_red([lab.CONFIRM_TOKEN])
            self.assertEqual(rc, 0)
            self.assertEqual(len(seen_flags), 1)
            flags = seen_flags[0]
            self.assertEqual(flags & os.O_WRONLY, os.O_WRONLY)
            self.assertEqual(flags & os.O_NONBLOCK, os.O_NONBLOCK)
            if hasattr(os, "O_CLOEXEC"):
                self.assertEqual(flags & os.O_CLOEXEC, os.O_CLOEXEC)
            if hasattr(os, "O_NOFOLLOW"):
                self.assertEqual(flags & os.O_NOFOLLOW, os.O_NOFOLLOW)
            self.assertEqual(flags, _expected_open_flags())


class NoArbitraryInputTests(unittest.TestCase):
    def test_main_rejects_unknown_command(self) -> None:
        rc = lab.main(["encode", "ff0000", "7"])
        self.assertNotEqual(rc, 0)

    def test_main_rejects_preflight_extra_args(self) -> None:
        rc = lab.main(["preflight", "/dev/hidraw1"])
        self.assertNotEqual(rc, 0)

    def test_main_rejects_color_style_invocation(self) -> None:
        # No path that accepts color/brightness/payload/device/report-id.
        for argv in (
            ["apply-red", "ff0000", "7"],
            ["apply-model-yellow40", "ffd000", "40"],
            ["set-color", "ff0000"],
            ["write", "payload"],
            ["--device", "/dev/hidraw1"],
            ["--report-id", "26"],
            ["--brightness", "7"],
        ):
            try:
                rc = lab.main(list(argv))
            except SystemExit as exc:
                rc = int(exc.code) if exc.code is not None else 1
            self.assertNotEqual(rc, 0, "argv=%r" % (argv,))

    def test_confirm_token_mentions_required_markers(self) -> None:
        self.assertIn("1E71:2023", lab.CONFIRM_TOKEN)
        self.assertIn("LIGHTING-ONLY", lab.CONFIRM_TOKEN)

    def test_help_documents_token_and_frozen_frames(self) -> None:
        buf = io.StringIO()
        with mock.patch.object(sys, "stdout", buf):
            rc = lab.main(["--help"])
        self.assertEqual(rc, 0)
        out = buf.getvalue()
        self.assertIn(lab.CONFIRM_TOKEN, out)
        self.assertIn("00 4a 00", out.lower())
        self.assertIn("89 a9 00", out.lower())
        self.assertIn("4a 4a 4a", out.lower())
        self.assertIn("not captured from CAM", out)
        self.assertIn(lab.YELLOW40_SHA256, out)
        self.assertIn("preflight", out)
        # Must not advertise a generic write / color / brightness API.
        self.assertNotIn("RRGGBB", out)
        self.assertNotIn("--device", out)
        self.assertNotIn("--brightness", out)

    def test_module_has_no_generic_write_entrypoint(self) -> None:
        # Guard against accidental addition of a parameterized write path.
        for name in (
            "write_payload",
            "write_bytes",
            "set_color",
            "set_brightness",
            "open_device",
            "send_report",
        ):
            self.assertFalse(
                hasattr(lab, name),
                "unexpected generic entry point %r" % name,
            )


if __name__ == "__main__":
    unittest.main()
