"""Render the approved Q avatar as an application badge; package multi-size ICO."""
from pathlib import Path
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QImage, QPainter, QPainterPath, QPen
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


def main():
    image = QImage(512, 512, QImage.Format_ARGB32_Premultiplied)
    image.fill(Qt.transparent)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setRenderHint(QPainter.SmoothPixmapTransform)
    circle = QRectF(12, 12, 488, 488)
    painter.setPen(Qt.NoPen)
    painter.setBrush(QColor('#fff2e1'))
    painter.drawEllipse(circle)
    clip = QPainterPath()
    clip.addEllipse(circle)
    painter.setClipPath(clip)
    avatar = QImage(str(ROOT / 'assets/q-open.png'))
    painter.drawImage(QRectF(24, 24, 464, 464), avatar, QRectF(65, 0, 990, 990))
    painter.setClipping(False)
    painter.setPen(QPen(QColor('#ab826c'), 8))
    painter.setBrush(Qt.NoBrush)
    painter.drawEllipse(circle)
    painter.end()
    png = ROOT / 'assets/app-icon.png'
    image.save(str(png))
    # ICO encoding only; all drawing is done with Qt above.
    with Image.open(png) as source:
        source.save(ROOT / 'assets/app-icon.ico', format='ICO',
                    sizes=[(n, n) for n in (16, 24, 32, 48, 64, 128, 256)])


if __name__ == '__main__':
    main()
