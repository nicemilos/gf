import math
import random
import sys
import time
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, QRectF, QSettings
from PySide6.QtGui import QPixmap, QPainter
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
        self.running = QPixmap(str(base / 'run.png'))
        self.q_open = QPixmap(str(base / 'q-open.png'))
        self.q_running = QPixmap(str(base / 'q-run.png'))
        self.natural_open = QPixmap(str(base / 'natural-open.png'))
        if any(pix.isNull() for pix in (self.open, self.closed, self.running,
                                        self.q_open, self.q_running, self.natural_open)):
            raise RuntimeError('缺少角色图片')
        self.appearance = 'q'
        self.settings = QSettings('XiaoyaLocal', 'DesktopPet')
        self.pet_height = int(self.settings.value('height', 330))
        self.motion = True
        self.drag_offset = None
        self.drag_origin = None
        self.dragging = False
        self.run_direction = 1
        self.last_drag_move = 0
        self.run_started = 0
        self.suppress_click_menu = False
        self.click_menu_timer = QTimer(self)
        self.click_menu_timer.setSingleShot(True)
        self.click_menu_timer.timeout.connect(self.show_appearance_menu)
        self.started = time.monotonic()
        self.blink_at = self.started + 3
        self.blink_until = 0
        self.jump_at = -100
        self.resize_pet(self.pet_height)
        screen = QApplication.primaryScreen().availableGeometry()
        self.move(screen.right() - self.width() - 40, screen.bottom() - self.height() - 20)
        self.setToolTip('小雅：点击切换形象，拖动跑步，双击跳一下')
        self.tray = QSystemTrayIcon(self.q_open, self)
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
        running = self.dragging and now - self.last_drag_move < .18
        if running:
            stride = (now - self.run_started) * 13
            lift += 5 + 4 * abs(math.sin(stride))
        h = self.pet_height * (1 + breath)
        if self.appearance == 'q':
            pix = self.q_running if running else self.q_open
        else:
            pix = self.running if running else self.natural_open
        w = h * pix.width() / pix.height()
        y = self.height() - 12 - h - lift
        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        if running:
            painter.translate(self.width() / 2, y + h / 2)
            painter.rotate(3 * math.sin(stride))
            painter.scale(self.run_direction, 1)
            target = QRectF(-w / 2, -h / 2, w, h)
        else:
            target = QRectF((self.width() - w) / 2, y, w, h)
        painter.drawPixmap(target, pix, QRectF(pix.rect()))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_offset = event.globalPosition().toPoint() - self.pos()
            self.drag_origin = event.globalPosition().toPoint()
            self.dragging = False
            self.setCursor(Qt.ClosedHandCursor)

    def mouseMoveEvent(self, event):
        if self.drag_offset is not None:
            cursor = event.globalPosition().toPoint()
            if not self.dragging and (cursor - self.drag_origin).manhattanLength() < 4:
                return
            if not self.dragging:
                self.dragging = True
                self.run_started = time.monotonic()
            delta_x = cursor.x() - self.x() - self.drag_offset.x()
            if delta_x:
                self.run_direction = 1 if delta_x > 0 else -1
            self.last_drag_move = time.monotonic()
            self.move(cursor - self.drag_offset)
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.drag_offset is not None:
            was_dragging = self.dragging
            self.drag_offset = None
            self.drag_origin = None
            self.dragging = False
            self.unsetCursor()
            self.keep_on_screen()
            self.update()
            if not was_dragging and not self.suppress_click_menu:
                self.click_menu_position = event.globalPosition().toPoint()
                self.click_menu_timer.start(260)
            self.suppress_click_menu = False

    def keep_on_screen(self):
        screen = QApplication.screenAt(self.frameGeometry().center()) or QApplication.primaryScreen()
        r = screen.availableGeometry()
        self.move(max(r.left(), min(self.x(), r.right() - self.width() + 1)),
                  max(r.top(), min(self.y(), r.bottom() - self.height() + 1)))

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.click_menu_timer.stop()
            self.suppress_click_menu = True
            self.jump_at = time.monotonic()

    def show_appearance_menu(self):
        self.active_appearance_menu = self.appearance_menu()
        self.active_appearance_menu.popup(self.click_menu_position)

    def menu(self):
        menu = QMenu()
        menu.addAction('小雅 · 桌面陪伴').setEnabled(False)
        menu.addSeparator()
        menu.addMenu(self.appearance_menu())
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

    def appearance_menu(self):
        menu = QMenu('切换形象', self)
        for label, appearance in [('Q版形象', 'q'), ('接近原照', 'natural')]:
            action = menu.addAction(label, lambda chosen=appearance: self.change_appearance(chosen))
            action.setCheckable(True)
            action.setChecked(self.appearance == appearance)
        return menu

    def change_appearance(self, appearance):
        self.appearance = appearance
        self.tray.setIcon(self.q_open if appearance == 'q' else self.natural_open)
        self.tray.setContextMenu(self.menu())
        self.update()

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
