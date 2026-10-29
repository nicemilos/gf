"""Play eight complete drawings. Never transform individual body parts."""
import json
from pathlib import Path
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPixmap, QPainter, QBitmap, QRegion
from coat_palette import coat_tone, match_coat
from PySide6.QtGui import QImage

FRAME_COUNT = 8
FPS = 12


class WholeRun:
    def __init__(self, assets, appearance='q'):
        if appearance not in ('q', 'natural'):
            raise ValueError('Unknown appearance')
        folder = Path(assets) / 'whole-run' / appearance
        manifest = json.loads((folder / 'frames.json').read_text(encoding='utf-8'))
        self.frames = []
        reference = QImage(str(folder / '01.png')).convertToFormat(QImage.Format_RGBA8888)
        reference_tone = coat_tone(reference)
        for index, eye_x in enumerate(manifest['eye_x']):
            source = QPixmap(str(folder / f'{index + 1:02}.png'))
            if source.isNull():
                raise RuntimeError(f'Missing whole-character run frame {index + 1}')
            bounds = QRegion(QBitmap.fromImage(source.toImage().createAlphaMask())).boundingRect()
            source = QPixmap.fromImage(match_coat(source.toImage(), reference_tone))
            scale = manifest.get('target_height', 900) / bounds.height()
            canvas = QPixmap(1400, 1100)
            canvas.fill(Qt.transparent)
            painter = QPainter(canvas)
            painter.setRenderHint(QPainter.SmoothPixmapTransform)
            painter.drawPixmap(QRectF(manifest.get('target_eye_x', 1000) - eye_x * scale, 1030 - bounds.bottom() * scale,
                                      source.width() * scale, source.height() * scale),
                               source, QRectF(source.rect()))
            painter.end()
            self.frames.append(canvas)
        if len(self.frames) != FRAME_COUNT:
            raise RuntimeError('The run cycle requires exactly eight drawings')

    def render(self, frame):
        return self.frames[frame % FRAME_COUNT]
