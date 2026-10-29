"""Play eight complete drawings. Never transform individual body parts."""
import json
from pathlib import Path
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPixmap, QPainter, QBitmap, QRegion

FRAME_COUNT = 8
FPS = 12


class WholeRun:
    def __init__(self, assets):
        folder = Path(assets) / 'whole-run/q'
        manifest = json.loads((folder / 'frames.json').read_text(encoding='utf-8'))
        self.frames = []
        for index, eye_x in enumerate(manifest['eye_x']):
            source = QPixmap(str(folder / f'{index + 1:02}.png'))
            if source.isNull():
                raise RuntimeError(f'Missing whole-character run frame {index + 1}')
            bounds = QRegion(QBitmap.fromImage(source.toImage().createAlphaMask())).boundingRect()
            scale = 900 / bounds.height()
            canvas = QPixmap(1400, 1100)
            canvas.fill(Qt.transparent)
            painter = QPainter(canvas)
            painter.setRenderHint(QPainter.SmoothPixmapTransform)
            painter.drawPixmap(QRectF(1000 - eye_x * scale, 1030 - bounds.bottom() * scale,
                                      source.width() * scale, source.height() * scale),
                               source, QRectF(source.rect()))
            painter.end()
            self.frames.append(canvas)
        if len(self.frames) != FRAME_COUNT:
            raise RuntimeError('The run cycle requires exactly eight drawings')

    def render(self, frame):
        return self.frames[frame % FRAME_COUNT]
