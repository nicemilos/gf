import math
import json
import random
import sys
import time
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, QRectF, QSettings, QPoint, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPixmap, QPainter, QIcon, QBitmap, QRegion
from PySide6.QtWidgets import QApplication, QWidget, QMenu, QSystemTrayIcon
from whole_run import WholeRun, FPS as WHOLE_FPS
from companion_ui import Companion, STYLE, beside
from single_instance import SingleInstance
from edge_peek import peek_edge, nearest_peek_edge


class Pet(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('小雅')
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        base = Path(getattr(sys, '_MEIPASS', Path(__file__).parent)) / 'assets'
        self.setWindowIcon(QIcon(str(base / 'app-icon.ico')))
        self.open = QPixmap(str(base / 'open.png'))
        self.closed = QPixmap(str(base / 'blink.png'))
        self.q_open = QPixmap(str(base / 'q-open.png'))
        self.q_running = [pix.scaledToHeight(512, Qt.SmoothTransformation)
                          for pix in WholeRun(base).frames]
        self.natural_open = QPixmap(str(base / 'natural-open.png'))
        self.peeks = {}
        self.peek_insets = {}
        wall_x = json.loads((base / 'peek.json').read_text(encoding='utf-8'))['wall_x']
        for style in ('q', 'natural'):
            sprite = QPixmap(str(base / f'{style}-peek.png'))
            if sprite.isNull():
                raise RuntimeError(f'缺少探头素材：{style}-peek.png')
            bounds = QRegion(QBitmap.fromImage(sprite.toImage().createAlphaMask())).boundingRect()
            self.peeks[style] = sprite.copy(bounds)
            self.peek_insets[style] = (wall_x[style] - bounds.left()) / bounds.height()
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
        self.drag_last_cursor = None
        self.dragging = False
        self.peek_side = None
        self.peek_screen = None
        self.auto_motion = None
        self.auto_target = None
        self.hide_return_position = None
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
        self.tray = QSystemTrayIcon(self.windowIcon(), self)
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
        if self.peek_side:
            pix = self.peeks[self.appearance]
            h = min(self.pet_height * .86, (self.width() - 8) * pix.height() / pix.width())
            w = h * pix.width() / pix.height()
            painter = QPainter(self)
            painter.setRenderHint(QPainter.SmoothPixmapTransform)
            if self.peek_side == 'right':
                painter.translate(self.width(), 0)
                painter.scale(-1, 1)
            # Align the imaginary wall itself, rather than fingertips that
            # curl a few pixels past it, with the physical monitor edge.
            x = -self.peek_insets[self.appearance] * h
            painter.drawPixmap(QRectF(x, (self.height() - h) / 2, w, h), pix, QRectF(pix.rect()))
            return
        now = time.monotonic()
        age = now - self.started
        breath = math.sin(age * 2.2) * .004 if self.motion else 0
        jump_age = now - self.jump_at
        lift = 27 * math.sin(jump_age / .6 * math.pi) if 0 < jump_age < .6 else 0
        running = self.auto_motion is not None or (self.dragging and now - self.last_drag_move < .18)
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
            self.stop_auto_move()
            self.hide_return_position = None
            self.companion.bubble.hide()
            self.drag_offset = event.globalPosition().toPoint() - self.pos()
            if self.peek_side:
                # The virtual standing center starts at the edge, while the
                # visible peeking sprite stays safely clickable inside it.
                r = self.peek_screen.geometry()
                edge = r.left() if self.peek_side == 'left' else r.right() + 1
                self.drag_offset.setX(event.globalPosition().toPoint().x() - edge + self.width() // 2)
            self.drag_origin = event.globalPosition().toPoint()
            self.drag_last_cursor = self.drag_origin
            self.dragging = False
            self.setCursor(Qt.ClosedHandCursor)

    def mouseMoveEvent(self, event):
        if self.drag_offset is not None:
            cursor = event.globalPosition().toPoint()
            if not self.dragging and (cursor - self.drag_origin).manhattanLength() < 4:
                return
            target_width = self.width()
            if not self.dragging:
                self.dragging = True
                self.run_started = time.monotonic()
                frames = self.q_running if self.appearance == 'q' else self.natural_running
                run_width = max(round(self.pet_height * pix.width() / pix.height()) for pix in frames) + 24
                self.run_window_extra = max(0, run_width - self.width())
                if self.run_window_extra:
                    half_extra = self.run_window_extra // 2
                    target_width += self.run_window_extra
                    self.drag_offset.setX(self.drag_offset.x() + half_extra)
            # The visible window is pinned while peeking. Direction must track
            # the pointer, rather than distance from that constrained window.
            delta_x = cursor.x() - self.drag_last_cursor.x()
            self.drag_last_cursor = cursor
            if delta_x:
                self.run_direction = 1 if delta_x > 0 else -1
            self.last_drag_move = time.monotonic()
            desired = cursor - self.drag_offset
            screen = QApplication.screenAt(cursor) or self.peek_screen or QApplication.primaryScreen()
            center = desired + QPoint(target_width // 2, self.height() // 2)
            normal_width = round(self.pet_height * 2 / 3) + 24
            self.peek_side = peek_edge(center, screen.geometry(),
                                       [s.geometry() for s in QApplication.screens()],
                                       normal_width, self.peek_side)
            self.peek_screen = screen if self.peek_side else None
            if self.peek_side:
                desired = self.peek_position(desired.y(), target_width)
            # Commit one final rectangle. Moving outside first and snapping
            # back makes Windows' translucent window visibly flash.
            self.setGeometry(desired.x(), desired.y(), target_width, self.height())
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.drag_offset is not None:
            was_dragging = self.dragging
            self.drag_offset = None
            self.drag_origin = None
            self.drag_last_cursor = None
            self.dragging = False
            if self.run_window_extra:
                half_extra = self.run_window_extra // 2
                width = self.width() - self.run_window_extra
                position = self.peek_position(width=width) if self.peek_side else self.pos() + QPoint(half_extra, 0)
                self.setGeometry(position.x(), position.y(), width, self.height())
                self.run_window_extra = 0
            self.unsetCursor()
            self.keep_on_screen()
            self.update()
            if not was_dragging and not self.suppress_click_menu:
                self.click_menu_position = event.globalPosition().toPoint()
                self.click_menu_timer.start(260)
            self.suppress_click_menu = False

    def keep_on_screen(self):
        if self.peek_side:
            self.position_peek()
            return
        screen = QApplication.screenAt(self.frameGeometry().center()) or QApplication.primaryScreen()
        r = screen.availableGeometry()
        self.move(max(r.left(), min(self.x(), r.right() - self.width() + 1)),
                  max(r.top(), min(self.y(), r.bottom() - self.height() + 1)))

    def peek_position(self, y=None, width=None):
        screen = self.peek_screen if self.peek_screen in QApplication.screens() else QApplication.primaryScreen()
        self.peek_screen = screen
        r = screen.geometry()
        work = screen.availableGeometry()
        x = r.left() if self.peek_side == 'left' else r.right() + 1 - (self.width() if width is None else width)
        y = self.y() if y is None else y
        return QPoint(x, max(work.top(), min(y, work.bottom() + 1 - self.height())))

    def position_peek(self):
        self.move(self.peek_position())

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.click_menu_timer.stop()
            self.suppress_click_menu = True
            self.jump_at = time.monotonic()

    def menu(self):
        menu = QMenu()
        menu.setStyleSheet(STYLE)
        menu.addAction('小雅').setEnabled(False)
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
        hiding = menu.addAction(self.hiding_label(), self.toggle_hiding)
        hiding.setObjectName('toggle_hiding')
        # The tray retains its menu while drag/animation can change state.
        menu.aboutToShow.connect(lambda: hiding.setText(self.hiding_label()))
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
        self.stop_auto_move()
        self.resize_pet(height)
        self.keep_on_screen()

    def hiding_label(self):
        return '快回来' if self.peek_side or self.auto_target == 'hide' else '躲起来'

    def toggle_hiding(self):
        if self.peek_side or self.auto_target == 'hide':
            self.come_back()
        else:
            self.hide_nearby()

    def stop_auto_move(self):
        if self.auto_motion is None:
            return
        self.auto_motion.stop()
        self.auto_motion.deleteLater()
        self.auto_motion = None
        self.auto_target = None
        if self.run_window_extra:
            width = self.width() - self.run_window_extra
            x = self.x() + self.run_window_extra // 2
            self.run_window_extra = 0
            self.setGeometry(x, self.y(), width, self.height())
        self.update()

    def inside_position(self, screen, preferred):
        r = screen.availableGeometry()
        width = round(self.pet_height * 2 / 3) + 24
        return QPoint(max(r.left(), min(preferred.x(), r.right() + 1 - width)),
                      max(r.top(), min(preferred.y(), r.bottom() + 1 - self.height())))

    def return_position(self):
        screen = self.peek_screen or QApplication.screenAt(self.geometry().center()) or QApplication.primaryScreen()
        if screen not in QApplication.screens():
            screen = QApplication.primaryScreen()
        if self.hide_return_position is not None:
            center = self.hide_return_position + QPoint(round(self.pet_height * 2 / 3 + 24) // 2, self.height() // 2)
            screen = QApplication.screenAt(center) or screen
            return screen, self.inside_position(screen, self.hide_return_position)
        r = screen.availableGeometry()
        width = round(self.pet_height * 2 / 3) + 24
        margin = max(40, width // 2)
        x = r.left() + margin if self.peek_side == 'left' else r.right() + 1 - width - margin
        return screen, self.inside_position(screen, QPoint(x, self.y()))

    def hide_nearby(self):
        self.stop_auto_move()
        self.companion.bubble.hide()
        self.click_menu_timer.stop()
        self.hide_return_position = self.pos()
        screens = QApplication.screens()
        index, side = nearest_peek_edge(self.geometry().center(), [s.geometry() for s in screens])
        screen = screens[index]
        r = screen.geometry()
        center_x = r.left() if side == 'left' else r.right() + 1
        self.start_auto_move(QPoint(center_x, self.y()), 'hide', screen, side)

    def come_back(self):
        self.stop_auto_move()
        screen, position = self.return_position()
        width = round(self.pet_height * 2 / 3) + 24
        self.start_auto_move(position + QPoint(width // 2, 0), 'return', screen)

    def start_auto_move(self, target, purpose, screen, side=None):
        """Animate a virtual center; commit the final peeking rectangle once."""
        self.companion.bubble.hide()
        self.click_menu_timer.stop()
        self.peek_side = None
        self.peek_screen = screen
        normal_width = round(self.pet_height * 2 / 3) + 24
        frames = self.q_running if self.appearance == 'q' else self.natural_running
        width = max(normal_width, max(round(self.pet_height * p.width() / p.height()) for p in frames) + 24)
        center_x = self.x() + self.width() // 2
        target.setY(self.inside_position(screen, target).y())
        start = QPoint(center_x - width // 2, self.y())
        end = QPoint(target.x() - width // 2, target.y())
        self.run_direction = 1 if end.x() >= start.x() else -1
        self.run_started = time.monotonic()
        self.run_window_extra = width - normal_width
        animation = QPropertyAnimation(self, b'pos', self)
        self.auto_motion = animation
        self.auto_target = purpose
        self.setGeometry(start.x(), start.y(), width, self.height())
        animation.setDuration(max(240, min(1500, round((end - start).manhattanLength() / 800 * 1000))))
        animation.setStartValue(start)
        animation.setEndValue(end)
        animation.setEasingCurve(QEasingCurve.InOutSine)

        def finished():
            if self.auto_motion is not animation:
                return
            self.auto_motion = None
            self.auto_target = None
            self.run_window_extra = 0
            self.peek_side = side if purpose == 'hide' else None
            self.peek_screen = screen if self.peek_side else None
            position = self.peek_position(end.y(), normal_width) if self.peek_side else QPoint(target.x() - normal_width // 2, end.y())
            self.setGeometry(position.x(), position.y(), normal_width, self.height())
            if not self.peek_side:
                self.hide_return_position = None
            self.update()
            animation.deleteLater()

        animation.finished.connect(finished)
        animation.start()
        self.update()

    def restore(self):
        self.stop_auto_move()
        position = self.return_position()[1] if self.peek_side else None
        self.peek_side = None
        self.peek_screen = None
        self.hide_return_position = None
        if position is not None:
            self.move(position)
        # Re-map the native window even if Windows hid it outside Qt.
        self.hide()
        self.show()
        self.keep_on_screen()
        self.raise_()
        self.activateWindow()

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
    app.setWindowIcon(QIcon(str(Path(getattr(sys, '_MEIPASS', Path(__file__).parent)) / 'assets/app-icon.ico')))
    app.setQuitOnLastWindowClosed(False)
    instance = SingleInstance()
    if not instance.primary:
        sys.exit(0)
    app.aboutToQuit.connect(instance.close)
    pet = Pet()
    instance.activated.connect(pet.restore)
    pet.show()
    if '--smoke-test' in sys.argv:
        QTimer.singleShot(500, app.quit)
    sys.exit(app.exec())
