#!/usr/bin/env python3
"""Offline golden tests for the generic nzxt-n9 Fixed frame encoder."""

from __future__ import annotations

import subprocess
import unittest
from pathlib import Path


ENCODER = Path(__file__).resolve().parents[1] / "bin" / "nzxt-n9"
LOAD_HEADER = bytes.fromhex("26042000")
COMMIT_PREFIX = bytes.fromhex("26062000010000310000800032000001")
REPORT_LEN = 512
N_LED = 49


def _run_encode(color: str, pct: int, *, commit: bool = False) -> list[bytes]:
    args = [str(ENCODER), "encode", color, str(pct), "--hex-only"]
    if commit:
        args.append("--commit")
    result = subprocess.run(
        args,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.stderr:
        raise AssertionError("hex-only emitted stderr: %r" % result.stderr)
    return [bytes.fromhex(line) for line in result.stdout.splitlines()]


def _assert_frame(test: unittest.TestCase, frame: bytes, triple: bytes) -> None:
    test.assertEqual(len(frame), REPORT_LEN)
    test.assertEqual(frame[:4], LOAD_HEADER)
    for i in range(N_LED):
        start = 4 + i * 3
        test.assertEqual(frame[start : start + 3], triple, "triple %d" % i)
    test.assertEqual(frame[4 + N_LED * 3 :], bytes(361))


class FixedEncoderGoldenTests(unittest.TestCase):
    def test_nine_captured_colors_at_seven_percent(self) -> None:
        captured = {
            "ffffff": "4a4a4a",
            "ff0000": "004a00",
            "0000ff": "00004a",
            "00ff00": "4a0000",
            "ff00ff": "004a4a",
            "804020": "0c2103",
            "408020": "210c03",
            "c08040": "21360c",
            "7f7f7f": "202020",
        }
        for color, triple_hex in captured.items():
            with self.subTest(color=color):
                frames = _run_encode(color, 7)
                self.assertEqual(len(frames), 1)
                _assert_frame(self, frames[0], bytes.fromhex(triple_hex))

    def test_captured_white_brightness_series(self) -> None:
        captured = {
            0: 0x00,
            1: 0x19,
            2: 0x26,
            7: 0x4A,
            10: 0x59,
            25: 0x88,
            49: 0xB9,
            50: 0xBB,
            75: 0xE0,
            90: 0xF2,
            99: 0xFD,
            100: 0xFE,
        }
        for pct, level in captured.items():
            with self.subTest(pct=pct):
                frames = _run_encode("ffffff", pct)
                self.assertEqual(len(frames), 1)
                _assert_frame(self, frames[0], bytes([level, level, level]))

    def test_d22_mixed_color_at_fifty_percent(self) -> None:
        frame = _run_encode("5a23f4", 50)[0]
        _assert_frame(self, frame, bytes.fromhex("1740b2"))

    def test_d24_mixed_color_at_twenty_five_percent(self) -> None:
        frame = _run_encode("0e50ad", 25)[0]
        _assert_frame(self, frame, bytes.fromhex("27045b"))

    def test_uncaptured_yellow40_prediction(self) -> None:
        frame = _run_encode("ffd000", 40)[0]
        _assert_frame(self, frame, bytes.fromhex("89a900"))

    def test_commit_is_fixed_and_zero_padded(self) -> None:
        load, commit = _run_encode("ffd000", 40, commit=True)
        _assert_frame(self, load, bytes.fromhex("89a900"))
        self.assertEqual(len(commit), REPORT_LEN)
        self.assertEqual(commit[:16], COMMIT_PREFIX)
        self.assertEqual(commit[16:], bytes(REPORT_LEN - 16))

    def test_invalid_input_fails_without_frame_output(self) -> None:
        for args in (
            ["encode", "xyz", "40", "--hex-only"],
            ["encode", "ffd000", "101", "--hex-only"],
            ["encode", "ffd000", "40", "--payload", "00"],
        ):
            with self.subTest(args=args):
                result = subprocess.run(
                    [str(ENCODER), *args],
                    check=False,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
