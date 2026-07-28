"""All Alternating D47, D49 and D50 tests use fakes. Never open real hidraw."""
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
CLI = TOOL_ROOT / "bin" / "nzxt-n9-alternating-write-lab"
sys.path.insert(0, str(LIB))

import nzxt_n9_alternating as alternating
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


class FrameTests(unittest.TestCase):
    def test_exact_frames_hashes_and_critical_bytes(self) -> None:
        states = alternating.AlternatingD47()
        travel_by_name = {
            "fastest": states.travel_right_fastest_frame(),
            "fast": states.travel_right_fast_frame(),
            "normal": states.travel_right_normal_frame(),
            "slow": states.travel_right_slow_frame(),
            "slowest": states.travel_right_slowest_frame(),
        }
        travel = states.travel_right_normal_frame()
        in_place = states.in_place_right_normal_frame()

        for frame in (*travel_by_name.values(), in_place):
            self.assertEqual(len(frame), 512)
            self.assertEqual(frame[:5], bytes.fromhex("2a04202005"))
            self.assertEqual(frame[8:14], bytes.fromhex("28408b006100"))
            self.assertEqual(frame[56], 2)
            self.assertEqual(frame[57], 0)
            self.assertEqual(frame[58:60], bytes.fromhex("3104"))
            self.assertFalse(any(frame[60:]))

        expected = {
            "fastest": (300, alternating.TRAVEL_RIGHT_FASTEST_SHA256),
            "fast": (400, alternating.TRAVEL_RIGHT_FAST_SHA256),
            "normal": (500, alternating.TRAVEL_RIGHT_NORMAL_SHA256),
            "slow": (700, alternating.TRAVEL_RIGHT_SLOW_SHA256),
            "slowest": (800, alternating.TRAVEL_RIGHT_SLOWEST_SHA256),
        }
        for name, frame in travel_by_name.items():
            speed, digest = expected[name]
            with self.subTest(name=name):
                self.assertEqual(int.from_bytes(frame[5:7], "little"), speed)
                self.assertEqual(frame[55], 1)
                self.assertEqual(hashlib.sha256(frame).hexdigest(), digest)

        self.assertEqual(in_place[5:7], bytes.fromhex("e803"))
        self.assertEqual(in_place[55], 0)
        self.assertEqual(
            hashlib.sha256(in_place).hexdigest(),
            alternating.IN_PLACE_RIGHT_NORMAL_SHA256,
        )
        for name, frame in travel_by_name.items():
            self.assertEqual(
                [
                    index
                    for index, pair in enumerate(zip(travel, frame, strict=True))
                    if pair[0] != pair[1]
                ],
                {
                    "fastest": [5],
                    "fast": [5],
                    "normal": [],
                    "slow": [5, 6],
                    "slowest": [5, 6],
                }[name],
            )
        self.assertEqual(
            [
                index
                for index, pair in enumerate(zip(travel, in_place, strict=True))
                if pair[0] != pair[1]
            ],
            [5, 6, 55],
        )

    def test_every_mutated_byte_fails_closed(self) -> None:
        state = alternating.AlternatingD47()
        cases = (
            (
                state.travel_right_fastest_frame(),
                alternating._TRAVEL_RIGHT_FASTEST_FRAME,
                alternating.TRAVEL_RIGHT_FASTEST_SHA256,
                "D49 travel-right-fastest",
            ),
            (
                state.travel_right_fast_frame(),
                alternating._TRAVEL_RIGHT_FAST_FRAME,
                alternating.TRAVEL_RIGHT_FAST_SHA256,
                "D50 travel-right-fast",
            ),
            (
                state.travel_right_normal_frame(),
                alternating._TRAVEL_RIGHT_NORMAL_FRAME,
                alternating.TRAVEL_RIGHT_NORMAL_SHA256,
                "D47 travel-right-normal",
            ),
            (
                state.in_place_right_normal_frame(),
                alternating._IN_PLACE_RIGHT_NORMAL_FRAME,
                alternating.IN_PLACE_RIGHT_NORMAL_SHA256,
                "D47 in-place-right-normal",
            ),
            (
                state.travel_right_slow_frame(),
                alternating._TRAVEL_RIGHT_SLOW_FRAME,
                alternating.TRAVEL_RIGHT_SLOW_SHA256,
                "D50 travel-right-slow",
            ),
            (
                state.travel_right_slowest_frame(),
                alternating._TRAVEL_RIGHT_SLOWEST_FRAME,
                alternating.TRAVEL_RIGHT_SLOWEST_SHA256,
                "D49 travel-right-slowest",
            ),
        )
        for original, expected, digest, label in cases:
            for index in range(len(original)):
                mutated = bytearray(original)
                mutated[index] ^= 1
                with self.subTest(label=label, index=index), self.assertRaises(
                    ValueError
                ):
                    alternating._validate_exact_frame(
                        bytes(mutated),
                        expected,
                        digest,
                        label,
                    )

    def test_private_d47_capture_matches_frames_and_binary_hashes(self) -> None:
        tshark = shutil.which("tshark")
        if not alternating.D47_PCAP_PATH.is_file() or tshark is None:
            self.skipTest("private D47 PCAP or tshark is unavailable")

        self.assertEqual(
            hashlib.sha256(alternating.D47_PCAP_PATH.read_bytes()).hexdigest(),
            alternating.D47_PCAP_SHA256,
        )
        result = subprocess.run(
            [
                tshark,
                "-r",
                str(alternating.D47_PCAP_PATH),
                "-Y",
                (
                    "usb.bus_id == 3 && usb.device_address == 6 && "
                    "usb.transfer_type == 0x01 && "
                    "usb.endpoint_address.direction == 0 && usb.capdata"
                ),
                "-T",
                "fields",
                "-e",
                "frame.number",
                "-e",
                "usb.capdata",
            ],
            text=True,
            capture_output=True,
            check=True,
        )
        frames = []
        for line in result.stdout.splitlines():
            number, hex_payload = line.split("\t", 1)
            frame = bytes.fromhex(hex_payload)
            if frame.startswith(bytes.fromhex("2a04")):
                frames.append((int(number), frame))

        state = alternating.AlternatingD47()
        self.assertEqual(
            frames,
            [
                (
                    alternating.TRAVEL_RIGHT_NORMAL_FRAME_NUMBER,
                    state.travel_right_normal_frame(),
                ),
                (
                    alternating.IN_PLACE_RIGHT_NORMAL_FRAME_NUMBER,
                    state.in_place_right_normal_frame(),
                ),
                (4667, state.travel_right_normal_frame()),
            ],
        )

    def test_private_d49_and_d50_captures_match_every_relevant_frame(self) -> None:
        tshark = shutil.which("tshark")
        if (
            not alternating.D49_PCAP_PATH.is_file()
            or not alternating.D50_PCAP_PATH.is_file()
            or tshark is None
        ):
            self.skipTest("private D49 and D50 PCAPs or tshark are unavailable")

        captures = (
            (
                alternating.D49_PCAP_PATH,
                alternating.D49_PCAP_SHA256,
                [
                    (
                        alternating.TRAVEL_RIGHT_FASTEST_D49_FRAME_NUMBERS[0],
                        alternating.AlternatingD47().travel_right_fastest_frame(),
                    ),
                    (
                        alternating.TRAVEL_RIGHT_SLOWEST_D49_FRAME_NUMBER,
                        alternating.AlternatingD47().travel_right_slowest_frame(),
                    ),
                    (
                        alternating.TRAVEL_RIGHT_NORMAL_D49_FRAME_NUMBER,
                        alternating.AlternatingD47().travel_right_normal_frame(),
                    ),
                    (
                        alternating.TRAVEL_RIGHT_FASTEST_D49_FRAME_NUMBERS[1],
                        alternating.AlternatingD47().travel_right_fastest_frame(),
                    ),
                ],
            ),
            (
                alternating.D50_PCAP_PATH,
                alternating.D50_PCAP_SHA256,
                [
                    (
                        alternating.TRAVEL_RIGHT_FAST_D50_FRAME_NUMBER,
                        alternating.AlternatingD47().travel_right_fast_frame(),
                    ),
                    (
                        alternating.TRAVEL_RIGHT_NORMAL_D50_FRAME_NUMBER,
                        alternating.AlternatingD47().travel_right_normal_frame(),
                    ),
                    (
                        alternating.TRAVEL_RIGHT_SLOW_D50_FRAME_NUMBER,
                        alternating.AlternatingD47().travel_right_slow_frame(),
                    ),
                    (
                        alternating.TRAVEL_RIGHT_SLOWEST_D50_FRAME_NUMBER,
                        alternating.AlternatingD47().travel_right_slowest_frame(),
                    ),
                ],
            ),
        )
        for path, expected_pcap_sha256, expected_frames in captures:
            with self.subTest(path=path):
                self.assertEqual(
                    hashlib.sha256(path.read_bytes()).hexdigest(),
                    expected_pcap_sha256,
                )
                result = subprocess.run(
                    [
                        tshark,
                        "-r",
                        str(path),
                        "-Y",
                        (
                            "usb.bus_id == 3 && usb.device_address == 6 && "
                            "usb.transfer_type == 0x01 && "
                            "usb.endpoint_address.direction == 0 && usb.capdata"
                        ),
                        "-T",
                        "fields",
                        "-e",
                        "frame.number",
                        "-e",
                        "usb.capdata",
                    ],
                    text=True,
                    capture_output=True,
                    check=True,
                )
                actual_frames = []
                for line in result.stdout.splitlines():
                    number, hex_payload = line.split("\t", 1)
                    frame = bytes.fromhex(hex_payload)
                    if frame.startswith(bytes.fromhex("2a04")):
                        actual_frames.append((int(number), frame))
                self.assertEqual(actual_frames, expected_frames)

    def test_repeated_controls_are_identical_across_d47_d49_and_d50(self) -> None:
        state = alternating.AlternatingD47()
        normal = state.travel_right_normal_frame()
        slowest = state.travel_right_slowest_frame()
        self.assertEqual(
            hashlib.sha256(normal).hexdigest(),
            "bb88f24351f7817582c5f591203c5cae3b4963ad4b6bb1e2fd244b56c9dee782",
        )
        self.assertEqual(
            hashlib.sha256(slowest).hexdigest(),
            "bca2c0146e7ea24ea02f9f3ef1be93117d9559871ca275637ecf845a69db03fe",
        )


class WriterTests(unittest.TestCase):
    APPLY_OPERATION_NAMES = (
        "apply_travel_right_fastest",
        "apply_travel_right_fast",
        "apply_travel_right_normal",
        "apply_travel_right_slow",
        "apply_travel_right_slowest",
        "apply_in_place_right_normal",
    )

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

    def _writer(self) -> alternating.AlternatingD47Writer:
        return alternating.AlternatingD47Writer(
            temperature_reader=lambda: 54.0,
            lock_factory=_NoopLock,
        )

    def test_offline_operations_never_resolve_open_or_write(self) -> None:
        writer = alternating.OfflineAlternatingD47Writer()
        with mock.patch.object(
            alternating.os,
            "open",
            side_effect=AssertionError("opened"),
        ), mock.patch.object(
            alternating.os,
            "write",
            side_effect=AssertionError("wrote"),
        ), mock.patch.object(
            fixed,
            "resolve_hidraw",
            side_effect=AssertionError("resolved"),
        ):
            self.assertFalse(writer.preflight().physical)
            self.assertFalse(writer.apply_travel_right_fastest().physical)
            self.assertFalse(writer.apply_travel_right_fast().physical)
            self.assertFalse(writer.apply_travel_right_normal().physical)
            self.assertFalse(writer.apply_travel_right_slow().physical)
            self.assertFalse(writer.apply_travel_right_slowest().physical)
            self.assertFalse(writer.apply_in_place_right_normal().physical)

    def test_real_preflight_never_opens_hidraw(self) -> None:
        with mock.patch.object(
            alternating.os,
            "open",
            side_effect=AssertionError("opened"),
        ), mock.patch.object(
            alternating.os,
            "write",
            side_effect=AssertionError("wrote"),
        ):
            readiness = self._writer().preflight()
        self.assertEqual(readiness.node, self.node)

    def test_each_success_is_one_exact_write_without_commit(self) -> None:
        state = alternating.AlternatingD47()
        operations = (
            (
                self._writer().apply_travel_right_fastest,
                state.travel_right_fastest_frame(),
            ),
            (
                self._writer().apply_travel_right_fast,
                state.travel_right_fast_frame(),
            ),
            (
                self._writer().apply_travel_right_normal,
                state.travel_right_normal_frame(),
            ),
            (
                self._writer().apply_travel_right_slow,
                state.travel_right_slow_frame(),
            ),
            (
                self._writer().apply_travel_right_slowest,
                state.travel_right_slowest_frame(),
            ),
            (
                self._writer().apply_in_place_right_normal,
                state.in_place_right_normal_frame(),
            ),
        )
        for operation, expected in operations:
            writes: list[bytes] = []
            with mock.patch.object(
                alternating.os,
                "open",
                return_value=31,
            ), mock.patch.object(
                alternating.os,
                "write",
                side_effect=lambda _fd, data: writes.append(data) or len(data),
            ), mock.patch.object(alternating.os, "close"):
                result = operation()
            self.assertTrue(result.physical)
            self.assertEqual(writes, [expected])
            self.assertFalse(any(frame.startswith(b"\x26\x06") for frame in writes))

    def test_write_error_and_partial_write_are_never_retried(self) -> None:
        operation_names = (
            "apply_travel_right_fastest",
            "apply_travel_right_fast",
            "apply_travel_right_normal",
            "apply_travel_right_slow",
            "apply_travel_right_slowest",
        )
        for operation_name in operation_names:
            for side_effect in (OSError("synthetic"), 511):
                write = mock.Mock(
                    side_effect=side_effect
                    if isinstance(side_effect, OSError)
                    else None,
                    return_value=(
                        None if isinstance(side_effect, OSError) else side_effect
                    ),
                )
                with self.subTest(
                    operation=operation_name,
                    side_effect=side_effect,
                ), mock.patch.object(
                    alternating.os,
                    "open",
                    return_value=31,
                ), mock.patch.object(
                    alternating.os,
                    "write",
                    write,
                ), mock.patch.object(alternating.os, "close"):
                    with self.assertRaises(fixed.N9OperationError):
                        getattr(self._writer(), operation_name)()
                self.assertEqual(write.call_count, 1)

    def test_missing_output_2a_fails_before_open_and_write(self) -> None:
        descriptor = self.sysfs / "hidraw4" / "device" / "report_descriptor"
        descriptor.write_bytes(_descriptor(include_2a=False))
        for operation_name in self.APPLY_OPERATION_NAMES:
            with self.subTest(operation=operation_name), mock.patch.object(
                alternating.os,
                "open",
            ) as opened, mock.patch.object(
                alternating.os,
                "write",
            ) as write:
                with self.assertRaisesRegex(fixed.N9FixedError, "Output 0x2a"):
                    getattr(self._writer(), operation_name)()
            opened.assert_not_called()
            write.assert_not_called()

    def test_post_open_identity_failure_produces_zero_writes(self) -> None:
        wrong = types.SimpleNamespace(
            st_mode=stat.S_IFCHR | 0o600,
            st_rdev=os.makedev(240, 5),
        )
        for operation_name in self.APPLY_OPERATION_NAMES:
            with self.subTest(operation=operation_name), mock.patch.object(
                alternating.os,
                "open",
                return_value=31,
            ), mock.patch.object(
                fixed.os,
                "fstat",
                return_value=wrong,
            ), mock.patch.object(
                alternating.os,
                "write",
            ) as write, mock.patch.object(alternating.os, "close"):
                with self.assertRaises(fixed.N9FixedError):
                    getattr(self._writer(), operation_name)()
            write.assert_not_called()

    def test_output_2a_loss_after_open_produces_zero_writes(self) -> None:
        full_descriptor = _descriptor()
        fixed_only_descriptor = _descriptor(include_2a=False)
        for operation_name in self.APPLY_OPERATION_NAMES:
            with self.subTest(operation=operation_name), mock.patch.object(
                Path,
                "read_bytes",
                side_effect=[
                    full_descriptor,
                    full_descriptor,
                    full_descriptor,
                    fixed_only_descriptor,
                ],
            ), mock.patch.object(
                alternating.os,
                "open",
                return_value=31,
            ), mock.patch.object(
                alternating.os,
                "write",
            ) as write, mock.patch.object(alternating.os, "close"):
                with self.assertRaisesRegex(fixed.N9FixedError, "Output 0x2a"):
                    getattr(self._writer(), operation_name)()
            write.assert_not_called()

    def test_mutated_constant_fails_before_lock_or_io(self) -> None:
        mutated = bytearray(
            alternating.AlternatingD47().travel_right_normal_frame()
        )
        mutated[59] ^= 1
        lock = mock.Mock(side_effect=AssertionError("locked"))
        with mock.patch.object(
            alternating,
            "_TRAVEL_RIGHT_NORMAL_FRAME",
            bytes(mutated),
        ), mock.patch.object(
            alternating.os,
            "open",
            side_effect=AssertionError("opened"),
        ), mock.patch.object(
            alternating.os,
            "write",
            side_effect=AssertionError("wrote"),
        ):
            with self.assertRaises(ValueError):
                alternating.AlternatingD47Writer(
                    temperature_reader=lambda: 54.0,
                    lock_factory=lock,
                ).apply_travel_right_normal()
        lock.assert_not_called()

    def test_shared_fixed_lock_blocks_alternating_writer(self) -> None:
        runtime = Path(self.tempdir.name) / "runtime"
        runtime.mkdir()
        writer = alternating.AlternatingD47Writer(
            temperature_reader=lambda: 54.0
        )
        with mock.patch.dict(os.environ, {"XDG_RUNTIME_DIR": str(runtime)}):
            with fixed.DeviceWriteLock():
                with mock.patch.object(
                    alternating.os,
                    "write",
                    side_effect=AssertionError("wrote"),
                ):
                    with self.assertRaises(fixed.N9OperationError) as raised:
                        writer.apply_travel_right_normal()
        self.assertEqual(raised.exception.kind, fixed.FailureKind.LOCK_BUSY)

    def test_raw_or_unknown_operation_is_rejected(self) -> None:
        frame = alternating.AlternatingD47().travel_right_normal_frame()
        with self.assertRaisesRegex(ValueError, "unknown"):
            self._writer()._validate_selected(frame, "arbitrary")


class RestoreTests(unittest.TestCase):
    def test_restore_is_the_published_typed_d32_operation(self) -> None:
        self.assertIs(alternating.offline_restore_d32, animated.offline_restore_d32)
        self.assertIs(alternating.real_restore_d32, animated.real_restore_d32)
        writer = mock.Mock(spec=fixed.OfflineWriter)
        expected = fixed.SendResult(False, "typed offline D32")
        with mock.patch.object(
            animated,
            "OfflineWriter",
            return_value=writer,
        ) as constructor, mock.patch.object(
            animated,
            "restore_d32",
            return_value=expected,
        ) as restore:
            self.assertIs(alternating.offline_restore_d32(), expected)
        constructor.assert_called_once_with()
        restore.assert_called_once_with(writer)


class CliTests(unittest.TestCase):
    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(CLI), *args],
            text=True,
            capture_output=True,
            check=False,
        )

    def test_help_states_closed_scope(self) -> None:
        result = self.run_cli("--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("exactly captured D47, D49 and D50", result.stdout)
        self.assertIn("not a general 2a 04", result.stdout)

    def test_offline_commands_require_distinct_exact_tokens(self) -> None:
        cases = (
            (
                "apply-travel-right-fastest",
                alternating.TRAVEL_RIGHT_FASTEST_CONFIRM_TOKEN,
            ),
            (
                "apply-travel-right-fast",
                alternating.TRAVEL_RIGHT_FAST_CONFIRM_TOKEN,
            ),
            (
                "apply-travel-right-normal",
                alternating.TRAVEL_RIGHT_NORMAL_CONFIRM_TOKEN,
            ),
            (
                "apply-travel-right-slow",
                alternating.TRAVEL_RIGHT_SLOW_CONFIRM_TOKEN,
            ),
            (
                "apply-travel-right-slowest",
                alternating.TRAVEL_RIGHT_SLOWEST_CONFIRM_TOKEN,
            ),
            (
                "apply-in-place-right-normal",
                alternating.IN_PLACE_RIGHT_NORMAL_CONFIRM_TOKEN,
            ),
            ("restore-d32", alternating.RESTORE_CONFIRM_TOKEN),
        )
        tokens = tuple(token for _command, token in cases)
        for command, accepted_token in cases:
            for token in ("wrong", *(item for item in tokens if item != accepted_token)):
                with self.subTest(command=command, token=token):
                    result = self.run_cli("--offline", command, token)
                    self.assertEqual(result.returncode, 2)
                    self.assertIn(accepted_token, result.stderr)

    def test_offline_preflight_and_apply_need_no_hardware(self) -> None:
        preflight = self.run_cli("--offline", "preflight")
        fastest = self.run_cli(
            "--offline",
            "apply-travel-right-fastest",
            alternating.TRAVEL_RIGHT_FASTEST_CONFIRM_TOKEN,
        )
        fast = self.run_cli(
            "--offline",
            "apply-travel-right-fast",
            alternating.TRAVEL_RIGHT_FAST_CONFIRM_TOKEN,
        )
        travel = self.run_cli(
            "--offline",
            "apply-travel-right-normal",
            alternating.TRAVEL_RIGHT_NORMAL_CONFIRM_TOKEN,
        )
        in_place = self.run_cli(
            "--offline",
            "apply-in-place-right-normal",
            alternating.IN_PLACE_RIGHT_NORMAL_CONFIRM_TOKEN,
        )
        slow = self.run_cli(
            "--offline",
            "apply-travel-right-slow",
            alternating.TRAVEL_RIGHT_SLOW_CONFIRM_TOKEN,
        )
        slowest = self.run_cli(
            "--offline",
            "apply-travel-right-slowest",
            alternating.TRAVEL_RIGHT_SLOWEST_CONFIRM_TOKEN,
        )
        for result in (preflight, fastest, fast, travel, slow, slowest, in_place):
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("zero hidraw", result.stdout)

    def test_cli_rejects_payloads_unknown_commands_and_missing_tokens(self) -> None:
        extra = self.run_cli(
            "--offline",
            "apply-travel-right-normal",
            alternating.TRAVEL_RIGHT_NORMAL_CONFIRM_TOKEN,
            "payload",
        )
        unknown = self.run_cli("--offline", "write", "2a04")
        missing = self.run_cli("--offline", "apply-in-place-right-normal")
        for result in (extra, unknown, missing):
            self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main()
