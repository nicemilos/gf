import unittest
from PySide6.QtCore import QPoint, QRect
from edge_peek import peek_edge, nearest_peek_edge


class EdgePeekTests(unittest.TestCase):
    def test_nearest_hiding_edge_ignores_shared_monitor_seam(self):
        left, right = QRect(-1920, 0, 1920, 1080), QRect(0, 0, 1920, 1080)
        self.assertEqual(nearest_peek_edge(QPoint(10, 500), [left, right]), (1, 'right'))
        self.assertEqual(nearest_peek_edge(QPoint(-10, 500), [left, right]), (0, 'left'))
        self.assertEqual(nearest_peek_edge(QPoint(200, 500), [right]), (0, 'left'))
        self.assertEqual(nearest_peek_edge(QPoint(1700, 500), [right]), (0, 'right'))

    def test_enter_hold_and_exit_on_both_edges(self):
        screen = QRect(0, 0, 1920, 1080)
        for x, previous, expected in [(20, None, 'left'), (50, 'left', 'left'),
                                      (100, 'left', None), (1890, None, 'right'),
                                      (1860, 'right', 'right'), (1800, 'right', None),
                                      (960, None, None)]:
            with self.subTest(x=x):
                self.assertEqual(peek_edge(QPoint(x, 500), screen, [screen], 244, previous), expected)

    def test_connected_monitors_do_not_make_an_invisible_wall(self):
        left, right = QRect(-1920, 0, 1920, 1080), QRect(0, 0, 1920, 1080)
        self.assertIsNone(peek_edge(QPoint(-2, 500), left, [left, right], 244))
        self.assertIsNone(peek_edge(QPoint(2, 500), right, [left, right], 244))
        self.assertEqual(peek_edge(QPoint(-1910, 500), left, [left, right], 244), 'left')

    def test_partial_monitor_seam_and_vertical_offset(self):
        primary, other = QRect(0, 0, 1920, 1080), QRect(1920, 300, 1280, 720)
        self.assertEqual(peek_edge(QPoint(1910, 100), primary, [primary, other], 244), 'right')
        self.assertIsNone(peek_edge(QPoint(1910, 600), primary, [primary, other], 244))


if __name__ == '__main__':
    unittest.main()
