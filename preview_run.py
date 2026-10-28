"""Review the same articulated run used by the desktop pet."""
import sys
import time
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, QRectF
from PySide6.QtGui import QPainter, QPixmap, QColor, QFont
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                               QPushButton, QLabel, QSlider, QSpinBox, QCheckBox)
from run_rig import RunRig, FRAME_COUNT


class Stage(QWidget):
    def __init__(self):
        super().__init__()
        rig = RunRig(Path(__file__).parent / 'assets')
        self.frames = {debug: [[rig.render(mode, frame) for frame in range(FRAME_COUNT)]
                               for mode in ('natural', 'q')] for debug in (False,)}
        self.rig = rig
        self.debug = False
        self.frame = 0
        self.mirror = False
        self.setMinimumSize(760, 450)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor('#e9edf1'))
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        size = min(self.width() / 2 - 30, self.height() - 90)
        for i in range(2):
            center = self.width() * (i + .5) / 2
            top = 50
            painter.setPen(QColor('#26364a'))
            painter.drawText(QRectF(center - size / 2, 10, size, 30), Qt.AlignCenter,
                             '接近原版' if i == 0 else 'Q 版')
            painter.setPen(QColor('#a7b1bd'))
            painter.drawLine(int(center - size / 2), int(top + size),
                             int(center + size / 2), int(top + size))
            painter.save()
            painter.translate(center, top)
            if self.mirror:
                painter.scale(-1, 1)
            pix = (self.rig.render(('natural', 'q')[i], self.frame, True) if self.debug
                   else self.frames[False][i][self.frame])
            width = size * pix.width() / pix.height()
            painter.drawPixmap(QRectF(-width / 2, 0, width, size), pix, QRectF(pix.rect()))
            painter.restore()


class Preview(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('小雅 · 重做跑步：16帧关节动画')
        self.resize(900, 580)
        self.stage = Stage()
        self.playing = True
        self.started = time.monotonic()
        self.start_frame = 0
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel('16 帧重做版 · 青色为近侧手脚，橙色为远侧手脚 · 第 1 与第 9 帧交换两侧'))
        layout.addWidget(self.stage)
        row = QHBoxLayout()
        self.play_button = QPushButton('暂停')
        self.play_button.clicked.connect(self.toggle)
        row.addWidget(self.play_button)
        previous = QPushButton('上一帧')
        previous.clicked.connect(lambda: self.step(-1))
        row.addWidget(previous)
        following = QPushButton('下一帧')
        following.clicked.connect(lambda: self.step(1))
        row.addWidget(following)
        self.fps = QSpinBox()
        self.fps.setRange(1, 30)
        self.fps.setValue(24)
        self.fps.setSuffix(' 帧/秒')
        self.fps.valueChanged.connect(self.reset_clock)
        row.addWidget(self.fps)
        mirror = QCheckBox('朝左')
        mirror.toggled.connect(self.set_mirror)
        row.addWidget(mirror)
        joints = QCheckBox('四肢标记')
        joints.toggled.connect(self.set_debug)
        row.addWidget(joints)
        self.counter = QLabel()
        row.addWidget(self.counter)
        layout.addLayout(row)
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 15)
        self.slider.sliderMoved.connect(self.seek)
        layout.addWidget(self.slider)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(16)
        self.show_frame(0)

    def show_frame(self, frame):
        self.stage.frame = frame % 16
        self.slider.setValue(self.stage.frame)
        self.counter.setText(f'{self.stage.frame + 1} / 16')
        self.stage.update()

    def reset_clock(self, *_):
        self.started = time.monotonic()
        self.start_frame = self.stage.frame

    def toggle(self):
        self.playing = not self.playing
        self.play_button.setText('暂停' if self.playing else '播放')
        self.reset_clock()

    def seek(self, frame):
        if self.playing:
            self.toggle()
        self.show_frame(frame)
        self.reset_clock()

    def step(self, amount):
        self.seek((self.stage.frame + amount) % 16)

    def set_mirror(self, checked):
        self.stage.mirror = checked
        self.stage.update()

    def set_debug(self, checked):
        self.stage.debug = checked
        self.stage.update()

    def tick(self):
        if self.playing:
            elapsed = time.monotonic() - self.started
            self.show_frame(self.start_frame + int(elapsed * self.fps.value()))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setFont(QFont('Microsoft YaHei UI', 10))
    window = Preview()
    window.show()
    if '--smoke-test' in sys.argv:
        QTimer.singleShot(600, app.quit)
    sys.exit(app.exec())
