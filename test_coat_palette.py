import unittest
from pathlib import Path
from PySide6.QtGui import QImage
from coat_palette import coat_tone, match_coat


class CoatPaletteTests(unittest.TestCase):
    def test_color_consistency_without_geometry_or_head_changes(self):
        folder = Path(__file__).parent / 'assets/whole-run/q'
        reference = QImage(str(folder / '01.png')).convertToFormat(QImage.Format_RGBA8888)
        target = coat_tone(reference)
        for path in sorted(folder.glob('*.png')):
            image = QImage(str(path)).convertToFormat(QImage.Format_RGBA8888)
            corrected = match_coat(image, target)
            before, after = bytes(image.constBits()), bytes(corrected.constBits())
            self.assertEqual(image.size(), corrected.size())
            self.assertEqual(before[3::4], after[3::4], path.name)
            head_end = int(image.height() * .45) * image.bytesPerLine()
            shoes_start = int(image.height() * .80) * image.bytesPerLine()
            self.assertEqual(before[:head_end], after[:head_end], path.name)
            self.assertEqual(before[shoes_start:], after[shoes_start:], path.name)
            self.assertTrue(all(abs(a - b) <= 2 for a, b in zip(coat_tone(corrected), target)), path.name)
            if path.name == '01.png':
                self.assertEqual(before, after)


if __name__ == '__main__':
    unittest.main()
