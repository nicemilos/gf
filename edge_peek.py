"""Detect an exposed desktop edge, with hysteresis and multi-monitor seams."""
from PySide6.QtCore import QPoint


def nearest_peek_edge(center, screens):
    """Return (screen index, side) for the nearest exposed vertical edge."""
    candidates = []
    for index, screen in enumerate(screens):
        y = max(screen.top(), min(center.y(), screen.bottom()))
        for side, x, outside_x in [('left', screen.left(), screen.left() - 1),
                                    ('right', screen.right() + 1, screen.right() + 1)]:
            if any(r.contains(QPoint(outside_x, y)) for r in screens):
                continue
            distance = (center.x() - x) ** 2 + (center.y() - y) ** 2
            candidates.append((distance, index, side))
    _, index, side = min(candidates)
    return index, side


def peek_edge(center, screen, screens, body_width, previous=None):
    threshold = body_width * (.32 if previous else .16)
    y = max(screen.top(), min(center.y(), screen.bottom()))
    left_open = not any(r.contains(QPoint(screen.left() - 1, y)) for r in screens)
    right_open = not any(r.contains(QPoint(screen.right() + 1, y)) for r in screens)
    if left_open and center.x() <= screen.left() + threshold:
        return 'left'
    if right_open and center.x() >= screen.right() + 1 - threshold:
        return 'right'
    return None
