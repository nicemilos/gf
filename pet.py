import math
import random
import sys
import time
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, QRectF, QSettings
from PySide6.QtGui import QPixmap, QPainter, QCursor, QAction
from PySide6.QtWidgets import QApplication, QWidget, QMenu, QSystemTrayIcon


class Pet(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('小雅 · 桌面陪伴')
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        base = Path(getattr(sys, '_MEIPASS', Path(__file__).parent)) / 'assets'
        self.open = QPixmap(str(base / 'open.png'))
        self.closed = QPixmap(str(base / 'blink.png'))
        if self.open.isNull() or self.closed.isNull():
            raise RuntimeError('缺少角色图片')
        self.settings = QSettings('XiaoyaLocal', 'DesktopPet')
        self.pet_height = int(self.settings.value('height', 330))
        self.motion = True
        self.drag_offset = None
        self.started = time.monotonic()
        self.blink_at = self.started + 3
        self.blink_until = 0
        self.jump_at = -100
        self.resize_pet(self.pet_height)
        screen = QApplication.primaryScreen().availableGeometry()
        self.move(screen.right() - self.width() - 40, screen.bottom() - self.height() - 20)
        self.setToolTip('小雅：拖动我换个位置，双击跳一下，右键打开菜单')
        self.tray = QSystemTrayIcon(self.open, self)
        self.tray.setToolTip('小雅 · 双击托盘图标找回桌宠')
        self.tray.setContextMenu(self.menu())
        self.tray.activated.connect(self.tray_activated)
        self.tray.show()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(33)

    def resize_pet(self, height):
        self.pet_height = height
        self.resize(round(height * 2 / 3) + 24, height + 45)
        self.settings.setValue('height', height)
        self.update()

    def tick(self):
        now = time.monotonic()
        if now >= self.blink_at:
            self.blink_until = now + .16
            self.blink_at = now + random.uniform(3, 6)
        self.update()

    def paintEvent(self, event):
        now = time.monotonic()
        age = now - self.started
        breath = math.sin(age * 2.2) * .004 if self.motion else 0
        jump_age = now - self.jump_at
        lift = 27 * math.sin(jump_age / .6 * math.pi) if 0 < jump_age < .6 else 0
        h = self.pet_height * (1 + breath)
        w = h * self.open.width() / self.open.height()
        y = self.height() - 12 - h - lift
        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        pix = self.closed if self.motion and now < self.blink_until else self.open
        painter.drawPixmap(QRectF((self.width() - w) / 2, y, w, h), pix, QRectF(pix.rect()))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_offset = event.globalPosition().toPoint() - self.pos()
            self.setCursor(Qt.ClosedHandCursor)

    def mouseMoveEvent(self, event):
        if self.drag_offset is not None:
            self.move(event.globalPosition().toPoint() - self.drag_offset)

    def mouseReleaseEvent(self, event):
        self.drag_offset = None
        self.unsetCursor()
        self.keep_on_screen()

    def keep_on_screen(self):
        screen = QApplication.screenAt(self.frameGeometry().center()) or QApplication.primaryScreen()
        r = screen.availableGeometry()
        self.move(max(r.left(), min(self.x(), r.right() - self.width() + 1)),
                  max(r.top(), min(self.y(), r.bottom() - self.height() + 1)))

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.jump_at = time.monotonic()

    def menu(self):
        menu = QMenu()
        menu.addAction('小雅 · 桌面陪伴').setEnabled(False)
        menu.addSeparator()
        sizes = menu.addMenu('调整大小')
        for label, height in [('小 · 240', 240), ('中 · 330', 330), ('大 · 440', 440)]:
            sizes.addAction(label, lambda h=height: self.change_size(h))
        action = menu.addAction('呼吸与眨眼')
        action.setCheckable(True)
        action.setChecked(self.motion)
        action.triggered.connect(self.toggle_motion)
        menu.addAction('跳一下', lambda: setattr(self, 'jump_at', time.monotonic()))
        menu.addAction('找回桌宠', self.restore)
        menu.addSeparator()
        menu.addAction('退出小雅', QApplication.instance().quit)
        return menu

    def toggle_motion(self, checked):
        self.motion = checked
        self.tray.setContextMenu(self.menu())

    def change_size(self, height):
        self.resize_pet(height)
        self.keep_on_screen()

    def restore(self):
        self.show()
        self.keep_on_screen()
        self.raise_()

    def tray_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.restore()

    def contextMenuEvent(self, event):
        self.menu().exec(event.globalPos())


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    pet = Pet()
    pet.show()
    if '--smoke-test' in sys.argv:
        QTimer.singleShot(500, app.quit)
    sys.exit(app.exec())
