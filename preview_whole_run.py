"""Review the eight full-character Q drawings used by the desktop pet."""
import sys
import time
from pathlib import Path
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QSlider, QSpinBox, QComboBox
from whole_run import WholeRun, FRAME_COUNT, FPS


class Preview(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('小雅 · 两版整帧跑步 · 1→8→1')
        self.runs = {mode: WholeRun(Path(__file__).parent / 'assets', mode) for mode in ('q', 'natural')}
        self.run = self.runs['natural']
        self.playing = True
        self.frame = 0
        self.started = time.monotonic()
        self.start_frame = 0
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel('8张完整人物 · 第1、5帧为相反大跨步 · 腿部遮挡仍待细化'))
        self.picture = QLabel(alignment=Qt.AlignCenter)
        self.picture.setStyleSheet('background: #e9edf1')
        layout.addWidget(self.picture)
        row = QHBoxLayout()
        appearance = QComboBox()
        appearance.addItems(['原版', 'Q版'])
        appearance.currentIndexChanged.connect(lambda index: self.change_appearance(('natural', 'q')[index]))
        row.addWidget(appearance)
        self.play = QPushButton('暂停')
        self.play.clicked.connect(self.toggle)
        row.addWidget(self.play)
        for label, delta in (('上一帧', -1), ('下一帧', 1)):
            button = QPushButton(label)
            button.clicked.connect(lambda _, d=delta: self.seek(self.frame + d))
            row.addWidget(button)
        self.fps = QSpinBox()
        self.fps.setRange(1, 24)
        self.fps.setValue(FPS)
        self.fps.setSuffix(' 帧/秒')
        self.fps.valueChanged.connect(self.reset_clock)
        row.addWidget(self.fps)
        self.counter = QLabel()
        row.addWidget(self.counter)
        layout.addLayout(row)
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, FRAME_COUNT - 1)
        self.slider.sliderMoved.connect(self.seek)
        layout.addWidget(self.slider)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(16)
        self.show_frame(0)

    def change_appearance(self, mode):
        self.run = self.runs[mode]
        self.show_frame(self.frame)

    def show_frame(self, frame):
        self.frame = frame % FRAME_COUNT
        self.picture.setPixmap(self.run.render(self.frame).scaledToHeight(470, Qt.SmoothTransformation))
        self.slider.setValue(self.frame)
        self.counter.setText(f'{self.frame + 1} / {FRAME_COUNT}')

    def reset_clock(self, *_):
        self.started = time.monotonic()
        self.start_frame = self.frame

    def toggle(self):
        self.playing = not self.playing
        self.play.setText('暂停' if self.playing else '播放')
        self.reset_clock()

    def seek(self, frame):
        if self.playing:
            self.toggle()
        self.show_frame(frame)
        self.reset_clock()

    def tick(self):
        if self.playing:
            self.show_frame(self.start_frame + int((time.monotonic() - self.started) * self.fps.value()))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Preview()
    window.show()
    if '--smoke-test' in sys.argv:
        QTimer.singleShot(600, app.quit)
    sys.exit(app.exec())
