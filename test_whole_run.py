import os
import unittest
from pathlib import Path
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtWidgets import QApplication
from whole_run import WholeRun


class WholeRunTests(unittest.TestCase):
    def test_both_eight_frame_cycles_and_foreground_margins(self):
        app = QApplication.instance() or QApplication([])
        for mode in ('q', 'natural'):
            run = WholeRun(Path(__file__).parent / 'assets', mode)
            self.assertEqual(len(run.frames), 8)
            self.assertEqual(run.render(8).cacheKey(), run.render(0).cacheKey())
            self.assertEqual(run.render(-1).cacheKey(), run.render(7).cacheKey())
            fingerprints = set()
            for frame in run.frames:
                image = frame.toImage()
                fingerprints.add(hash(bytes(image.constBits())))
                for x in range(image.width()):
                    for y in (0, image.height() - 1):
                        self.assertLess(image.pixelColor(x, y).alpha(), 128)
                for y in range(image.height()):
                    for x in (0, image.width() - 1):
                        self.assertLess(image.pixelColor(x, y).alpha(), 128)
            self.assertEqual(len(fingerprints), 8)


if __name__ == '__main__':
    unittest.main()
