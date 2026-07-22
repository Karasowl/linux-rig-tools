"""Offscreen GUI smoke test.  The injected writer never touches hidraw."""
from __future__ import annotations

import importlib.machinery
import importlib.util
import os
import sys
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt6.QtWidgets import QApplication

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "lib"))
from nzxt_n9_fixed import N9FixedError, OfflineWriter, build_color_frame

loader = importlib.machinery.SourceFileLoader("nzxt_n9_lab", str(ROOT / "bin" / "nzxt-n9-lab"))
spec = importlib.util.spec_from_loader(loader.name, loader)
assert spec is not None
lab = importlib.util.module_from_spec(spec)
loader.exec_module(lab)


class LabUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.application = QApplication.instance() or QApplication(["test"])

    def test_offline_apply_and_restore(self) -> None:
        writer = OfflineWriter()
        d32 = build_color_frame([(255, 0, 0)] * 49, 25)
        window = lab.FixedLabWindow(True, writer=writer, d32_loader=lambda: d32)
        window.show()
        self.application.processEvents()
        self.assertEqual(len(window.zone_buttons), 49)
        self.assertTrue(all(button.isVisible() for button in window.zone_buttons))
        self.assertIn("offline", window.device_label.text())
        window._zone_clicked(1, False)
        window.hex_input.setText("0E50AD")
        window._apply()
        self.application.processEvents()
        self.application.processEvents()
        self.assertEqual(len(writer.sent), 1)
        self.assertEqual(writer.sent[0][0][7:10], bytes.fromhex("27045b"))
        window._restore_d32()
        self.application.processEvents()
        self.application.processEvents()
        self.assertEqual(len(writer.sent), 2)
        self.assertTrue(window.raw_d32_restored)
        self.assertIn("D32", window.log.toPlainText())
        window.close()

    def test_visible_selection_validation_and_error_states(self) -> None:
        class ErrorWriter:
            def send(self, _data, _commit):
                raise N9FixedError("CPU Package is 85.0 C, must be below 85 C")

        d32 = build_color_frame([(0, 0, 0)] * 49, 25)
        window = lab.FixedLabWindow(True, writer=ErrorWriter(), d32_loader=lambda: d32)
        self.assertIn("sin selección", window.state_label.text())
        window._zone_clicked(0, False)
        self.assertIn("selección simple", window.state_label.text())
        window._zone_clicked(1, True)
        self.assertIn("selección múltiple", window.state_label.text())
        window._select_all()
        self.assertIn("todas las zonas", window.state_label.text())
        window.hex_input.setText("BAD")
        self.assertIn("hex inválido", window.state_label.text())
        window.hex_input.setText("FFFFFF")
        window._apply()
        self.assertIn("escribiendo", window.state_label.text())
        self.application.processEvents()
        self.application.processEvents()
        self.assertIn("temperatura no disponible", window.state_label.text())
        window.close()


if __name__ == "__main__":
    unittest.main()
