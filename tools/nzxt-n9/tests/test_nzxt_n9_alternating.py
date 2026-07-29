"""All Alternating D47 to D51 tests use fakes. Never open real hidraw."""
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

# Every closed Apply the CLI exposes, as (command, exact token, frame label).
# The label is the frozen operation the library reports, so this table pins
# the command-to-frame wiring end to end.
APPLY_CLI_OPERATIONS = (
    (
        "apply-travel-right-fastest",
        alternating.TRAVEL_RIGHT_FASTEST_CONFIRM_TOKEN,
        "D49 travel-right-fastest",
    ),
    (
        "apply-travel-right-fast",
        alternating.TRAVEL_RIGHT_FAST_CONFIRM_TOKEN,
        "D50 travel-right-fast",
    ),
    (
        "apply-travel-right-normal",
        alternating.TRAVEL_RIGHT_NORMAL_CONFIRM_TOKEN,
        "D47 travel-right-normal",
    ),
    (
        "apply-travel-right-slow",
        alternating.TRAVEL_RIGHT_SLOW_CONFIRM_TOKEN,
        "D50 travel-right-slow",
    ),
    (
        "apply-travel-right-slowest",
        alternating.TRAVEL_RIGHT_SLOWEST_CONFIRM_TOKEN,
        "D49 travel-right-slowest",
    ),
    (
        "apply-in-place-right-fastest",
        alternating.IN_PLACE_RIGHT_FASTEST_CONFIRM_TOKEN,
        "D51 in-place-right-fastest",
    ),
    (
        "apply-in-place-right-fast",
        alternating.IN_PLACE_RIGHT_FAST_CONFIRM_TOKEN,
        "D51 in-place-right-fast",
    ),
    (
        "apply-in-place-right-normal",
        alternating.IN_PLACE_RIGHT_NORMAL_CONFIRM_TOKEN,
        "D47 in-place-right-normal",
    ),
    (
        "apply-in-place-right-slow",
        alternating.IN_PLACE_RIGHT_SLOW_CONFIRM_TOKEN,
        "D51 in-place-right-slow",
    ),
    (
        "apply-in-place-right-slowest",
        alternating.IN_PLACE_RIGHT_SLOWEST_CONFIRM_TOKEN,
        "D51 in-place-right-slowest",
    ),
    (
        "apply-travel-left-normal",
        alternating.TRAVEL_LEFT_NORMAL_CONFIRM_TOKEN,
        "D48 travel-left-normal",
    ),
    (
        "apply-in-place-left-normal",
        alternating.IN_PLACE_LEFT_NORMAL_CONFIRM_TOKEN,
        "D48 in-place-left-normal",
    ),
)


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
        in_place_by_name = {
            "fastest": states.in_place_right_fastest_frame(),
            "fast": states.in_place_right_fast_frame(),
            "normal": states.in_place_right_normal_frame(),
            "slow": states.in_place_right_slow_frame(),
            "slowest": states.in_place_right_slowest_frame(),
        }
        travel = states.travel_right_normal_frame()
        in_place = states.in_place_right_normal_frame()

        for frame in (*travel_by_name.values(), *in_place_by_name.values()):
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
            with self.subTest(table="travel", name=name):
                self.assertEqual(int.from_bytes(frame[5:7], "little"), speed)
                self.assertEqual(frame[55], 1)
                self.assertEqual(hashlib.sha256(frame).hexdigest(), digest)

        expected_in_place = {
            "fastest": (600, alternating.IN_PLACE_RIGHT_FASTEST_SHA256),
            "fast": (800, alternating.IN_PLACE_RIGHT_FAST_SHA256),
            "normal": (1000, alternating.IN_PLACE_RIGHT_NORMAL_SHA256),
            "slow": (1300, alternating.IN_PLACE_RIGHT_SLOW_SHA256),
            "slowest": (1600, alternating.IN_PLACE_RIGHT_SLOWEST_SHA256),
        }
        for name, frame in in_place_by_name.items():
            speed, digest = expected_in_place[name]
            with self.subTest(table="in-place", name=name):
                self.assertEqual(int.from_bytes(frame[5:7], "little"), speed)
                self.assertEqual(frame[55], 0)
                self.assertEqual(hashlib.sha256(frame).hexdigest(), digest)

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
        for name, frame in in_place_by_name.items():
            self.assertEqual(
                [
                    index
                    for index, pair in enumerate(zip(in_place, frame, strict=True))
                    if pair[0] != pair[1]
                ],
                {
                    "fastest": [5, 6],
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
            (
                state.in_place_right_fastest_frame(),
                alternating._IN_PLACE_RIGHT_FASTEST_FRAME,
                alternating.IN_PLACE_RIGHT_FASTEST_SHA256,
                "D51 in-place-right-fastest",
            ),
            (
                state.in_place_right_fast_frame(),
                alternating._IN_PLACE_RIGHT_FAST_FRAME,
                alternating.IN_PLACE_RIGHT_FAST_SHA256,
                "D51 in-place-right-fast",
            ),
            (
                state.in_place_right_slow_frame(),
                alternating._IN_PLACE_RIGHT_SLOW_FRAME,
                alternating.IN_PLACE_RIGHT_SLOW_SHA256,
                "D51 in-place-right-slow",
            ),
            (
                state.in_place_right_slowest_frame(),
                alternating._IN_PLACE_RIGHT_SLOWEST_FRAME,
                alternating.IN_PLACE_RIGHT_SLOWEST_SHA256,
                "D51 in-place-right-slowest",
            ),
            (
                state.in_place_left_normal_frame(),
                alternating._IN_PLACE_LEFT_NORMAL_FRAME,
                alternating.IN_PLACE_LEFT_NORMAL_SHA256,
                "D48 in-place-left-normal",
            ),
            (
                state.travel_left_normal_frame(),
                alternating._TRAVEL_LEFT_NORMAL_FRAME,
                alternating.TRAVEL_LEFT_NORMAL_SHA256,
                "D48 travel-left-normal",
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

    def test_private_d51_capture_matches_every_relevant_frame(self) -> None:
        tshark = shutil.which("tshark")
        if not alternating.D51_PCAP_PATH.is_file() or tshark is None:
            self.skipTest("private D51 PCAP or tshark is unavailable")

        self.assertEqual(
            hashlib.sha256(alternating.D51_PCAP_PATH.read_bytes()).hexdigest(),
            alternating.D51_PCAP_SHA256,
        )
        state = alternating.AlternatingD47()
        expected_frames = [
            (
                alternating.IN_PLACE_RIGHT_SLOWEST_D51_FRAME_NUMBER,
                state.in_place_right_slowest_frame(),
            ),
            (
                alternating.IN_PLACE_RIGHT_SLOW_D51_FRAME_NUMBER,
                state.in_place_right_slow_frame(),
            ),
            (
                alternating.IN_PLACE_RIGHT_NORMAL_D51_FRAME_NUMBER,
                state.in_place_right_normal_frame(),
            ),
            (
                alternating.IN_PLACE_RIGHT_FAST_D51_FRAME_NUMBER,
                state.in_place_right_fast_frame(),
            ),
            (
                alternating.IN_PLACE_RIGHT_FASTEST_D51_FRAME_NUMBER,
                state.in_place_right_fastest_frame(),
            ),
        ]
        result = subprocess.run(
            [
                tshark,
                "-r",
                str(alternating.D51_PCAP_PATH),
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

    def test_private_d48_capture_matches_every_relevant_frame(self) -> None:
        """D48 is the most cross-validated window in the series.

        Six of its nine writes reproduce states frozen from D47, D49, D50 and
        D51 byte for byte. Asserting the whole write list, not just the two
        new leftward frames, turns those six into standing controls.
        """
        tshark = shutil.which("tshark")
        if not alternating.D48_PCAP_PATH.is_file() or tshark is None:
            self.skipTest("private D48 PCAP or tshark is unavailable")

        self.assertEqual(
            hashlib.sha256(alternating.D48_PCAP_PATH.read_bytes()).hexdigest(),
            alternating.D48_PCAP_SHA256,
        )
        state = alternating.AlternatingD47()
        in_place_right = state.in_place_right_normal_frame()
        in_place_left = state.in_place_left_normal_frame()
        expected_frames = [
            (alternating.IN_PLACE_RIGHT_NORMAL_D48_FRAME_NUMBERS[0], in_place_right),
            (alternating.IN_PLACE_LEFT_NORMAL_D48_FRAME_NUMBERS[0], in_place_left),
            (alternating.IN_PLACE_RIGHT_NORMAL_D48_FRAME_NUMBERS[1], in_place_right),
            (alternating.IN_PLACE_LEFT_NORMAL_D48_FRAME_NUMBERS[1], in_place_left),
            (
                alternating.TRAVEL_LEFT_NORMAL_D48_FRAME_NUMBER,
                state.travel_left_normal_frame(),
            ),
            (
                alternating.TRAVEL_RIGHT_NORMAL_D48_FRAME_NUMBER,
                state.travel_right_normal_frame(),
            ),
            (alternating.IN_PLACE_RIGHT_NORMAL_D48_FRAME_NUMBERS[2], in_place_right),
            (
                alternating.IN_PLACE_RIGHT_SLOWEST_D48_FRAME_NUMBER,
                state.in_place_right_slowest_frame(),
            ),
            (
                alternating.IN_PLACE_RIGHT_FASTEST_D48_FRAME_NUMBER,
                state.in_place_right_fastest_frame(),
            ),
        ]
        result = subprocess.run(
            [
                tshark,
                "-r",
                str(alternating.D48_PCAP_PATH),
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

    def test_direction_bit_is_the_only_difference_from_a_validated_frame(self) -> None:
        """Each leftward frame is one byte away from a frame already sent.

        That is what makes D48 safe to freeze despite its weaker gesture
        attribution. The captured bytes are not in question, only which
        narrated gesture produced them, and the direction bit is the sole
        difference from a rightward state already written to this board.
        """
        state = alternating.AlternatingD47()
        pairs = (
            (
                state.in_place_left_normal_frame(),
                state.in_place_right_normal_frame(),
                0x02,
                0x00,
            ),
            (
                state.travel_left_normal_frame(),
                state.travel_right_normal_frame(),
                0x03,
                0x01,
            ),
        )
        for left, right, left_bits, right_bits in pairs:
            with self.subTest(left_bits=left_bits):
                self.assertEqual(
                    [
                        index
                        for index, pair in enumerate(zip(left, right, strict=True))
                        if pair[0] != pair[1]
                    ],
                    [55],
                )
                self.assertEqual(left[55], left_bits)
                self.assertEqual(right[55], right_bits)
                # Bit 1 is direction, bit 0 is propagation and must not move.
                self.assertEqual(left[55] ^ right[55], 0b10)

    def test_byte_55_has_all_four_measured_values(self) -> None:
        """The two-bit field is complete, which is what names the directions.

        The two rightward values are frozen and physically validated, so the
        remaining two are the leftward ones by elimination inside a closed
        field. The narrated gesture order agrees but is not load bearing.
        """
        state = alternating.AlternatingD47()
        by_bits = {
            state.in_place_right_normal_frame()[55]: "in-place right",
            state.travel_right_normal_frame()[55]: "travelling right",
            state.in_place_left_normal_frame()[55]: "in-place left",
            state.travel_left_normal_frame()[55]: "travelling left",
        }
        self.assertEqual(sorted(by_bits), [0x00, 0x01, 0x02, 0x03])
        self.assertEqual(len(set(by_bits.values())), 4)

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

    def test_in_place_normal_is_the_same_payload_in_d47_and_d51(self) -> None:
        """D47 frame 3725 and D51 frame 6865 are one cross-capture control."""
        state = alternating.AlternatingD47()
        self.assertEqual(
            hashlib.sha256(state.in_place_right_normal_frame()).hexdigest(),
            "a11850148cec0e00116a7ef2c851d8bf40514bd3ae532e0065c2cc51504023e6",
        )

    def test_the_two_speed_tables_are_independent_transcriptions(self) -> None:
        """D51 refuted the sub-mode factor of 2, so neither table derives.

        The factor holds at four notches and breaks at Slow, where the
        measured pair is 700 and 1300 rather than 700 and 1400. Deriving one
        table from the other would silently write a value CAM never sent.
        """
        state = alternating.AlternatingD47()
        travelling = {
            "fastest": state.travel_right_fastest_frame(),
            "fast": state.travel_right_fast_frame(),
            "normal": state.travel_right_normal_frame(),
            "slow": state.travel_right_slow_frame(),
            "slowest": state.travel_right_slowest_frame(),
        }
        in_place = {
            "fastest": state.in_place_right_fastest_frame(),
            "fast": state.in_place_right_fast_frame(),
            "normal": state.in_place_right_normal_frame(),
            "slow": state.in_place_right_slow_frame(),
            "slowest": state.in_place_right_slowest_frame(),
        }
        speed = lambda frame: int.from_bytes(frame[5:7], "little")  # noqa: E731
        measured = {
            name: (speed(travelling[name]), speed(in_place[name]))
            for name in travelling
        }
        self.assertEqual(
            measured,
            {
                "fastest": (300, 600),
                "fast": (400, 800),
                "normal": (500, 1000),
                "slow": (700, 1300),
                "slowest": (800, 1600),
            },
        )
        doubled = {
            name: pair for name, pair in measured.items() if pair[1] == pair[0] * 2
        }
        self.assertEqual(set(doubled), {"fastest", "fast", "normal", "slowest"})
        self.assertNotEqual(measured["slow"][1], measured["slow"][0] * 2)

    def test_speed_800_exists_in_both_tables_as_two_distinct_frames(self) -> None:
        """The raw speed alone never identifies an operation.

        Travelling Slowest and in-place Fast both carry 800 in bytes 5 and 6
        and differ only in byte 55. Selecting by speed would send the wrong
        sub-mode, so the frames stay separate and separately hashed.
        """
        state = alternating.AlternatingD47()
        travelling = state.travel_right_slowest_frame()
        in_place = state.in_place_right_fast_frame()
        self.assertEqual(travelling[5:7], in_place[5:7])
        self.assertEqual(int.from_bytes(travelling[5:7], "little"), 800)
        self.assertEqual(travelling[55], 1)
        self.assertEqual(in_place[55], 0)
        self.assertEqual(
            [
                index
                for index, pair in enumerate(zip(travelling, in_place, strict=True))
                if pair[0] != pair[1]
            ],
            [55],
        )
        self.assertNotEqual(
            hashlib.sha256(travelling).hexdigest(),
            hashlib.sha256(in_place).hexdigest(),
        )


class WriterTests(unittest.TestCase):
    APPLY_OPERATION_NAMES = (
        "apply_travel_right_fastest",
        "apply_travel_right_fast",
        "apply_travel_right_normal",
        "apply_travel_right_slow",
        "apply_travel_right_slowest",
        "apply_in_place_right_fastest",
        "apply_in_place_right_fast",
        "apply_in_place_right_normal",
        "apply_in_place_right_slow",
        "apply_in_place_right_slowest",
        "apply_travel_left_normal",
        "apply_in_place_left_normal",
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
            self.assertFalse(writer.apply_in_place_right_fastest().physical)
            self.assertFalse(writer.apply_in_place_right_fast().physical)
            self.assertFalse(writer.apply_in_place_right_normal().physical)
            self.assertFalse(writer.apply_in_place_right_slow().physical)
            self.assertFalse(writer.apply_in_place_right_slowest().physical)
            self.assertFalse(writer.apply_travel_left_normal().physical)
            self.assertFalse(writer.apply_in_place_left_normal().physical)

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
                self._writer().apply_in_place_right_fastest,
                state.in_place_right_fastest_frame(),
            ),
            (
                self._writer().apply_in_place_right_fast,
                state.in_place_right_fast_frame(),
            ),
            (
                self._writer().apply_in_place_right_normal,
                state.in_place_right_normal_frame(),
            ),
            (
                self._writer().apply_in_place_right_slow,
                state.in_place_right_slow_frame(),
            ),
            (
                self._writer().apply_in_place_right_slowest,
                state.in_place_right_slowest_frame(),
            ),
            (
                self._writer().apply_travel_left_normal,
                state.travel_left_normal_frame(),
            ),
            (
                self._writer().apply_in_place_left_normal,
                state.in_place_left_normal_frame(),
            ),
        )
        self.assertEqual(len(operations), len(self.APPLY_OPERATION_NAMES))
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
        for operation_name in self.APPLY_OPERATION_NAMES:
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
        # argparse rewraps the description, so compare on collapsed whitespace.
        described = " ".join(result.stdout.split())
        self.assertIn("exactly captured D47 to D51", described)
        self.assertIn("not a general 2a 04", described)
        self.assertIn("neither derives from the other", described)

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
                "apply-in-place-right-fastest",
                alternating.IN_PLACE_RIGHT_FASTEST_CONFIRM_TOKEN,
            ),
            (
                "apply-in-place-right-fast",
                alternating.IN_PLACE_RIGHT_FAST_CONFIRM_TOKEN,
            ),
            (
                "apply-in-place-right-normal",
                alternating.IN_PLACE_RIGHT_NORMAL_CONFIRM_TOKEN,
            ),
            (
                "apply-in-place-right-slow",
                alternating.IN_PLACE_RIGHT_SLOW_CONFIRM_TOKEN,
            ),
            (
                "apply-in-place-right-slowest",
                alternating.IN_PLACE_RIGHT_SLOWEST_CONFIRM_TOKEN,
            ),
            (
                "apply-travel-left-normal",
                alternating.TRAVEL_LEFT_NORMAL_CONFIRM_TOKEN,
            ),
            (
                "apply-in-place-left-normal",
                alternating.IN_PLACE_LEFT_NORMAL_CONFIRM_TOKEN,
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
        self.assertEqual(preflight.returncode, 0, preflight.stderr)
        self.assertIn("zero hidraw", preflight.stdout)
        for command, token, _label in APPLY_CLI_OPERATIONS:
            with self.subTest(command=command):
                result = self.run_cli("--offline", command, token)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("zero hidraw", result.stdout)

    def test_every_cli_command_is_bound_to_its_own_frozen_frame(self) -> None:
        """Guard the command-to-frame wiring, where a copy-paste would land.

        The detail line names the exact frozen operation the CLI reached, so
        an exact match rules out a command silently sending a neighbouring
        speed. Matching the whole sentence matters because `in-place-right-fast`
        is a prefix of `in-place-right-fastest`.
        """
        self.assertEqual(
            len(APPLY_CLI_OPERATIONS),
            len(WriterTests.APPLY_OPERATION_NAMES),
        )
        self.assertEqual(
            len({label for _command, _token, label in APPLY_CLI_OPERATIONS}),
            len(APPLY_CLI_OPERATIONS),
        )
        for command, token, label in APPLY_CLI_OPERATIONS:
            with self.subTest(command=command):
                result = self.run_cli("--offline", command, token)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(
                    result.stdout.strip(),
                    "OK: offline %s validation, zero hidraw opens or writes"
                    % label,
                )

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
