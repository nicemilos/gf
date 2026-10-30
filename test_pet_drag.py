"""Observe native QWidget moves so an offscreen/snap-back cannot go unnoticed."""
import os
import tempfile
import unittest
from unittest.mock import patch
from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtWidgets import QApplication
from pet import Pet


class PointerEvent:
    def __init__(self, point):
        self.point = point

    def globalPosition(self):
        return QPointF(self.point)

    def button(self):
        return Qt.LeftButton


class TracedPet(Pet):
    def moveEvent(self, event):
        if hasattr(self, 'moves'):
            self.moves.append(QPoint(event.pos()))


class PetDragTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.data = tempfile.TemporaryDirectory(prefix='xiaoya-drag-test-')
        old = os.environ.get('XIAOYA_DATA_DIR')
        os.environ['XIAOYA_DATA_DIR'] = cls.data.name
        try:
            cls.pet = TracedPet()
        finally:
            if old is None:
                os.environ.pop('XIAOYA_DATA_DIR', None)
            else:
                os.environ['XIAOYA_DATA_DIR'] = old
        cls.pet.moves = []
        cls.pet.timer.stop()
        cls.pet.tray.hide()
        cls.pet.show()
        cls.app.processEvents()

    @classmethod
    def tearDownClass(cls):
        cls.pet.stop_auto_move()
        cls.pet.companion.bubble.hide()
        cls.pet.close()
        cls.app.processEvents()
        cls.data.cleanup()

    def test_hiding_menu_moves_to_nearest_edge_and_returns(self):
        pet = self.pet
        screen = self.app.primaryScreen()
        screens = patch.object(QApplication, 'screens', return_value=[screen])
        screens.start()
        self.addCleanup(screens.stop)
        r = screen.availableGeometry()
        # Use the retained tray menu, which must refresh after dragging or
        # finishing an animation, as well as newly created context menus.
        tray_menu = pet.tray.contextMenu()
        def action(menu):
            menu.aboutToShow.emit()
            return next(a for a in menu.actions() if a.objectName() == 'toggle_hiding')
        for style in ('q', 'natural'):
            for side in ('left', 'right'):
                with self.subTest(style=style, side=side):
                    pet.restore()
                    pet.change_appearance(style)
                    tray_menu = pet.tray.contextMenu()
                    x = r.left() + 60 if side == 'left' else r.right() + 1 - pet.width() - 60
                    pet.move(x, r.top() + 50)
                    home = pet.pos()
                    self.assertEqual(action(tray_menu).text(), '躲起来')
                    action(tray_menu).trigger()
                    self.assertEqual(pet.auto_target, 'hide')
                    self.assertEqual(action(tray_menu).text(), '快回来')
                    pet.auto_motion.setCurrentTime(pet.auto_motion.duration())
                    self.assertEqual(pet.peek_side, side)
                    context_menu = pet.menu()
                    self.assertEqual(action(context_menu).text(), '快回来')
                    action(tray_menu).trigger()
                    self.assertEqual(pet.auto_target, 'return')
                    pet.auto_motion.setCurrentTime(pet.auto_motion.duration())
                    self.assertIsNone(pet.peek_side)
                    self.assertEqual(pet.pos(), home)
                    self.assertEqual(action(tray_menu).text(), '躲起来')

    def test_return_interrupts_hiding_and_drag_interrupts_auto_move(self):
        pet = self.pet
        pet.restore()
        r = self.app.primaryScreen().availableGeometry()
        pet.move(r.center().x() - pet.width() // 2, r.top() + 50)
        home = pet.pos()
        pet.hide_nearby()
        pet.auto_motion.setCurrentTime(pet.auto_motion.duration() // 2)
        pet.toggle_hiding()
        self.assertEqual(pet.auto_target, 'return')
        pet.auto_motion.setCurrentTime(pet.auto_motion.duration())
        self.assertEqual(pet.pos(), home)
        pet.hide_nearby()
        pet.mousePressEvent(PointerEvent(pet.geometry().center()))
        self.assertIsNone(pet.auto_motion)
        self.assertEqual(pet.run_window_extra, 0)
        pet.mouseReleaseEvent(PointerEvent(pet.geometry().center()))
        pet.click_menu_timer.stop()
        pet.peek_side = 'left'
        pet.peek_screen = self.app.primaryScreen()
        pet.hide_return_position = None
        pet.position_peek()
        pet.toggle_hiding()
        pet.auto_motion.setCurrentTime(pet.auto_motion.duration())
        self.assertIsNone(pet.peek_side)
        self.assertGreater(pet.x(), r.left())
        self.assertTrue(r.contains(pet.geometry()))

    def test_edge_moves_and_release_never_move_outside_then_snap_back(self):
        pet = self.pet
        screen = self.app.primaryScreen()
        # Geometry rules for monitor seams are tested separately. This native
        # movement regression must not depend on the developer's monitor layout.
        screens = patch.object(QApplication, 'screens', return_value=[screen])
        screens.start()
        self.addCleanup(screens.stop)
        r = screen.geometry()
        for style in ('q', 'natural'):
            for side in ('left', 'right'):
                with self.subTest(style=style, side=side):
                    pet.restore()
                    pet.change_appearance(style)
                    pet.move(r.center().x() - pet.width() // 2,
                             screen.availableGeometry().top() + 50)
                    origin = pet.geometry().center()
                    normal_width = pet.width()
                    pet.mousePressEvent(PointerEvent(origin))
                    cursor = QPoint(r.left() if side == 'left' else r.right(), origin.y())
                    pet.moves.clear()
                    pet.mouseMoveEvent(PointerEvent(cursor))
                    self.app.processEvents()
                    self.assertEqual(pet.peek_side, side)
                    self.assertLessEqual(len(pet.moves), 1, 'entering edge moved through intermediate positions')
                    for dy in (1, 2, 3):
                        pet.moves.clear()
                        pet.mouseMoveEvent(PointerEvent(cursor + QPoint(0, dy)))
                        self.app.processEvents()
                        expected_x = r.left() if side == 'left' else r.right() + 1 - pet.width()
                        self.assertEqual([p.x() for p in pet.moves], [expected_x])
                    pet.moves.clear()
                    pet.mouseReleaseEvent(PointerEvent(cursor + QPoint(0, 3)))
                    self.app.processEvents()
                    expected_x = r.left() if side == 'left' else r.right() + 1 - normal_width
                    self.assertTrue(all(p.x() == expected_x for p in pet.moves), 'release shifted away from edge')
                    self.assertEqual(pet.width(), normal_width)
                    self.assertEqual(pet.peek_side, side)
                    # Pulling back must use pointer direction, even while the
                    # visible window is still pinned to the opposite side.
                    start = QPoint(pet.x() + 30 if side == 'left' else pet.geometry().right() - 30,
                                   pet.geometry().center().y())
                    pet.mousePressEvent(PointerEvent(start))
                    inward = start + QPoint(250 if side == 'left' else -250, 0)
                    pet.mouseMoveEvent(PointerEvent(inward))
                    self.assertIsNone(pet.peek_side)
                    self.assertEqual(pet.run_direction, 1 if side == 'left' else -1)
                    pet.mouseReleaseEvent(PointerEvent(inward))


if __name__ == '__main__':
    unittest.main()
