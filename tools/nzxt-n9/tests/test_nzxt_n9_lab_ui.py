"""Offscreen UI tests.  Every writer is fake and no test opens hidraw."""
from __future__ import annotations

import importlib.machinery
import importlib.util
import os
import sys
import threading
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt6.QtCore import QEvent, QThread, Qt
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "lib"))
from nzxt_n9_fixed import FailureKind, N9FixedError, N9OperationError, OfflineWriter, Readiness, ZoneVector

loader = importlib.machinery.SourceFileLoader("nzxt_n9_lab", str(ROOT / "bin" / "nzxt-n9-lab"))
spec = importlib.util.spec_from_loader(loader.name, loader)
assert spec is not None
lab = importlib.util.module_from_spec(spec)
loader.exec_module(lab)


def _wait_until(predicate, timeout_ms: int = 1000) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        QApplication.processEvents()
        if predicate():
            return True
        QTest.qWait(10)
        elapsed += 10
    return predicate()


class LabUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.application = QApplication.instance() or QApplication(["test"])

    def test_offline_ctrl_clear_brightness_apply_and_d32_raw_base(self) -> None:
        writer = OfflineWriter()
        d32 = ZoneVector(tuple(bytes((index, index + 1, index + 2)) for index in range(49)))
        window = lab.FixedLabWindow(True, writer=writer, d32_loader=lambda: d32)
        window.show()
        self.assertTrue(_wait_until(lambda: all(button.isVisible() for button in window.zone_buttons)))
        QTest.mouseClick(window.zone_buttons[0], Qt.MouseButton.LeftButton)
        QTest.mouseClick(window.zone_buttons[1], Qt.MouseButton.LeftButton, Qt.KeyboardModifier.ControlModifier)
        self.assertEqual(window.selected, {0, 1})
        QTest.mouseClick(window.zone_buttons[1], Qt.MouseButton.LeftButton, Qt.KeyboardModifier.ControlModifier)
        self.assertEqual(window.selected, {0})
        window._clear_selection()
        self.assertFalse(window.selected)
        window._select_all()
        self.assertEqual(len(window.selected), 49)
        window._clear_selection()
        window._zone_clicked(1, False)
        window.hex_input.setText("0E50AD")
        window.brightness_slider.setValue(50)
        self.assertEqual(window.brightness_spin.value(), 50)
        window.brightness_spin.setValue(25)
        self.assertEqual(window.brightness_slider.value(), 25)
        self.assertTrue(window.apply_button.isEnabled())
        window._apply()
        self.assertTrue(window.busy)
        self.assertTrue(_wait_until(lambda: not window.busy))
        self.assertEqual(writer.sent[-1].triples[1], bytes.fromhex("27045b"))
        window._restore_d32()
        self.assertTrue(_wait_until(lambda: not window.busy))
        self.assertEqual(window.prepared_vector, d32)
        self.assertIsNone(window.last_success_vector)
        self.assertEqual(window.last_offline_validation, d32)
        window._zone_clicked(3, False)
        window.hex_input.setText("FF0000")
        window._apply()
        self.assertTrue(_wait_until(lambda: not window.busy))
        self.assertEqual(writer.sent[-1].triples[3], bytes.fromhex("008900"))
        self.assertEqual(writer.sent[-1].triples[4], d32.triples[4])
        self.assertIn("Físico: desconocido", window.map_state_label.text())
        self.assertIn("validación offline", window.outcome_label.text())
        window.close()

    def test_repeated_worker_cleanup_d32_error_and_lock_occupation(self) -> None:
        window = lab.FixedLabWindow(True, writer=OfflineWriter())
        window._zone_clicked(0, False)
        for _ in range(4):
            window._apply()
            self.assertTrue(_wait_until(lambda: not window.busy))
            QTest.qWait(10)
            QApplication.processEvents()
            QApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
            QApplication.processEvents()
            self.assertFalse(window.findChildren(QThread))

        failing_d32 = lab.FixedLabWindow(True, writer=OfflineWriter(), d32_loader=lambda: (_ for _ in ()).throw(N9FixedError("PCAP missing")))
        failing_d32._zone_clicked(0, False)
        failing_d32._restore_d32()
        self.assertTrue(_wait_until(lambda: not failing_d32.busy))
        self.assertEqual(failing_d32.device_state, lab.DeviceState.OFFLINE)
        self.assertTrue(failing_d32.apply_button.isEnabled())
        self.assertIn("d32-load", failing_d32.outcome_label.text())
        failing_d32.close()

        class BusyWriter:
            def send_vector(self, _vector):
                raise N9OperationError(FailureKind.LOCK_BUSY, "another process holds the N9 Fixed lock")

        occupied = lab.FixedLabWindow(True, writer=BusyWriter())
        occupied._zone_clicked(0, False)
        occupied._apply()
        self.assertTrue(_wait_until(lambda: not occupied.busy))
        self.assertEqual(occupied.device_state, lab.DeviceState.OFFLINE)
        self.assertTrue(occupied.apply_button.isEnabled())
        self.assertIn("ocupación", occupied.outcome_label.text())
        occupied.close()
        window.close()

    def test_real_state_controls_are_derived_from_readiness_and_errors(self) -> None:
        ready = lambda: Readiness(Path("/dev/fake"), 42.0)
        window = lab.FixedLabWindow(False, writer=OfflineWriter(), readiness_reader=ready)
        self.assertTrue(_wait_until(lambda: window.device_state == lab.DeviceState.READY))
        window._zone_clicked(0, False)
        self.assertTrue(window.apply_button.isEnabled())
        window.close()

        thermal = lambda: (_ for _ in ()).throw(N9FixedError("CPU Package is 85.0 C, must be below 85 C"))
        blocked = lab.FixedLabWindow(False, writer=OfflineWriter(), readiness_reader=thermal)
        self.assertTrue(_wait_until(lambda: blocked.device_state == lab.DeviceState.THERMAL))
        blocked._zone_clicked(0, False)
        self.assertFalse(blocked.apply_button.isEnabled())
        self.assertIn("bloqueo térmico", blocked.device_label.text())
        blocked.close()

        absent = lambda: (_ for _ in ()).throw(N9FixedError("expected exactly one N9 HID_ID, found 0"))
        missing = lab.FixedLabWindow(False, writer=OfflineWriter(), readiness_reader=absent)
        self.assertTrue(_wait_until(lambda: missing.device_state == lab.DeviceState.ABSENT))
        missing._zone_clicked(0, False)
        self.assertFalse(missing.apply_button.isEnabled())
        self.assertIn("ausente", missing.device_label.text())
        missing.close()

    def test_busy_rejects_duplicate_and_defers_close_until_transaction_finishes(self) -> None:
        started = threading.Event()
        release = threading.Event()
        class BlockingWriter:
            def send_vector(self, vector):
                started.set()
                release.wait(1)
                return "fake complete"

        window = lab.FixedLabWindow(True, writer=BlockingWriter())
        window.show()
        QApplication.processEvents()
        self.assertTrue(window.isVisible())
        window._zone_clicked(0, False)
        window._apply()
        self.assertTrue(started.wait(1))
        self.assertTrue(window.busy)
        self.assertFalse(window._start_operation("apply", window.prepared_vector))
        window.close()
        self.assertTrue(window._closing_requested)
        release.set()
        self.assertTrue(_wait_until(lambda: window._thread is None))
        self.assertFalse(window.isVisible())

    def test_hex_invalid_and_writer_error_surface(self) -> None:
        class ErrorWriter:
            def send_vector(self, _vector):
                raise N9FixedError("synthetic write failure")
        window = lab.FixedLabWindow(True, writer=ErrorWriter())
        window._zone_clicked(0, False)
        window.hex_input.setText("BAD")
        self.assertFalse(window.apply_button.isEnabled())
        window.hex_input.setText("FFFFFF")
        window._apply()
        self.assertTrue(_wait_until(lambda: window.device_state == lab.DeviceState.ERROR))
        self.assertFalse(window.apply_button.isEnabled())
        self.assertIn("error", window.outcome_label.text())
        window.close()


if __name__ == "__main__":
    unittest.main()
