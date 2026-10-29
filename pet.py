import math
import random
import sys
import time
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, QRectF, QSettings
from PySide6.QtGui import QPixmap, QPainter
from PySide6.QtWidgets import QApplication, QWidget, QMenu, QSystemTrayIcon
from whole_run import WholeRun, FPS as WHOLE_FPS
from companion_ui import Companion, STYLE, beside


class Pet(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('小雅 · 桌面陪伴')
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        base = Path(getattr(sys, '_MEIPASS', Path(__file__).parent)) / 'assets'
        self.open = QPixmap(str(base / 'open.png'))
        self.closed = QPixmap(str(base / 'blink.png'))
        self.q_open = QPixmap(str(base / 'q-open.png'))
        self.q_running = [pix.scaledToHeight(512, Qt.SmoothTransformation)
                          for pix in WholeRun(base).frames]
        self.natural_open = QPixmap(str(base / 'natural-open.png'))
        self.natural_running = [pix.scaledToHeight(512, Qt.SmoothTransformation)
                                for pix in WholeRun(base, 'natural').frames]
        if any(pix.isNull() for pix in (self.open, self.closed, self.q_open,
                                        self.natural_open, *self.q_running, *self.natural_running)):
            raise RuntimeError('缺少角色图片')
        self.appearance = 'q'
        self.settings = QSettings('XiaoyaLocal', 'DesktopPet')
        self.pet_height = int(self.settings.value('height', 330))
        self.motion = str(self.settings.value('motion', 'true')).lower() in ('true', '1')
        self.drag_offset = None
        self.drag_origin = None
        self.dragging = False
        self.run_window_extra = 0
        self.run_direction = 1
        self.last_drag_move = 0
        self.run_started = 0
        self.suppress_click_menu = False
        self.click_menu_timer = QTimer(self)
        self.click_menu_timer.setSingleShot(True)
        self.companion = Companion(self)
        self.click_menu_timer.timeout.connect(self.companion.speak)
        self.started = time.monotonic()
        self.blink_at = self.started + 3
        self.blink_until = 0
        self.jump_at = -100
        self.resize_pet(self.pet_height)
        screen = QApplication.primaryScreen().availableGeometry()
        self.move(screen.right() - self.width() - 40, screen.bottom() - self.height() - 20)
        self.setToolTip('小雅：点击说话，右键打开菜单，拖动跑步，双击跳一下')
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
        h = self.pet_height * (1 if running else 1 + breath)
        frames = self.q_running if self.appearance == 'q' else self.natural_running
        frame = int((now - self.run_started) * WHOLE_FPS) % len(frames)
        if self.appearance == 'q':
            pix = self.q_running[frame] if running else self.q_open
        else:
            pix = self.natural_running[frame] if running else self.natural_open
        w = h * pix.width() / pix.height()
        y = self.height() - 12 - h - lift
        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        if running:
            painter.translate(self.width() / 2, y + h / 2)
            painter.scale(self.run_direction, 1)
            target = QRectF(-w / 2, -h / 2, w, h)
        else:
            target = QRectF((self.width() - w) / 2, y, w, h)
        painter.drawPixmap(target, pix, QRectF(pix.rect()))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.companion.bubble.hide()
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
                frames = self.q_running if self.appearance == 'q' else self.natural_running
                run_width = max(round(self.pet_height * pix.width() / pix.height()) for pix in frames) + 24
                self.run_window_extra = max(0, run_width - self.width())
                if self.run_window_extra:
                    half_extra = self.run_window_extra // 2
                    self.resize(self.width() + self.run_window_extra, self.height())
                    self.move(self.x() - half_extra, self.y())
                    self.drag_offset.setX(self.drag_offset.x() + half_extra)
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
            if self.run_window_extra:
                half_extra = self.run_window_extra // 2
                self.move(self.x() + half_extra, self.y())
                self.resize(self.width() - self.run_window_extra, self.height())
                self.run_window_extra = 0
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

    def menu(self):
        menu = QMenu()
        menu.setStyleSheet(STYLE)
        menu.addAction('小雅 · 桌面陪伴').setEnabled(False)
        menu.addSeparator()
        menu.addAction('和小雅聊天', self.companion.open_chat)
        menu.addAction('模型配置…', self.companion.configure)
        menu.addAction('性格与记忆…', self.companion.memory)
        menu.addSeparator()
        menu.addMenu(self.appearance_menu())
        sizes = menu.addMenu('调整大小')
        for label, height in [('小 · 240', 240), ('中 · 330', 330), ('大 · 440', 440)]:
            sizes.addAction(label, lambda h=height: self.change_size(h))
        breathing = menu.addMenu('呼吸动画')
        for label, enabled in [('开', True), ('关', False)]:
            action = breathing.addAction(label, lambda checked=False, value=enabled: self.toggle_motion(value))
            action.setCheckable(True)
            action.setChecked(self.motion == enabled)
        menu.addAction('跳一下', lambda: setattr(self, 'jump_at', time.monotonic()))
        menu.addAction('移回屏幕内', self.restore)
        menu.addSeparator()
        menu.addAction('退出桌宠', QApplication.instance().quit)
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
        self.settings.setValue('motion', checked)
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
        menu = self.menu()
        position = beside(self, menu.sizeHint())
        if position.x() < self.x():
            menu.setLayoutDirection(Qt.RightToLeft)
        menu.exec(position)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    pet = Pet()
    pet.show()
    if '--smoke-test' in sys.argv:
        QTimer.singleShot(500, app.quit)
    sys.exit(app.exec())
