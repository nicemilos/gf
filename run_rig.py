"""Deterministic side-view run: one identity per limb, a half-cycle apart."""
import math
from pathlib import Path
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QPixmap, QPainter, QColor, QPen

FRAME_COUNT = 16
FPS = 24
GROUND = 940.0


def ik(start, end, length, bend=1):
    dx, dy = end[0] - start[0], end[1] - start[1]
    distance = math.hypot(dx, dy)
    if not 0 < distance < 2 * length:
        raise ValueError('Unreachable joint target')
    height = math.sqrt(length * length - distance * distance / 4)
    return ((start[0] + end[0]) / 2 + bend * dy / distance * height,
            (start[1] + end[1]) / 2 - bend * dx / distance * height)


def pose(mode, phase):
    phase %= 1
    leg = 190 if mode == 'natural' else 110
    hip_y = (600 if mode == 'natural' else 750) + leg * .065 * math.sin(phase * 4 * math.pi)
    shoulder = (530, hip_y - (215 if mode == 'natural' else 210))
    arm = 105 if mode == 'natural' else 80
    arm_shoulder = (shoulder[0] - 10, shoulder[1] + (55 if mode == 'natural' else 40))
    limbs = []
    for offset in (0, .5):
        p = (phase + offset) % 1
        reach = leg * .56
        if p <= .4:
            x = reach * (1 - 2 * p / .4)
            y = GROUND
        else:
            s = (p - .4) / .6
            x = reach * (-1 + 2 * (3 * s * s - 2 * s ** 3))
            y = GROUND - leg * .9 * math.sin(math.pi * s)
        hip = (500, hip_y)
        ankle = (500 + x, y)
        knee = ik(hip, ankle, leg)
        # Wrist goes opposite the SAME-side ankle around its own shoulder.
        wrist = (arm_shoulder[0] - .90 * x, arm_shoulder[1] + arm * 1.25)
        elbow = ik(arm_shoulder, wrist, arm, -1)
        limbs.append(dict(hip=hip, knee=knee, ankle=ankle, shoulder=arm_shoulder,
                          elbow=elbow, wrist=wrist, phase=p, stance=p <= .4))
    return dict(limbs=limbs, hip_y=hip_y, shoulder=shoulder, leg=leg, arm=arm)


class RunRig:
    def __init__(self, assets):
        atlas = QPixmap(str(Path(assets) / 'rig/parts.png'))
        natural = QPixmap(str(Path(assets) / 'rig/natural-head.png'))
        if atlas.isNull() or natural.isNull():
            raise RuntimeError('Missing run rig artwork')
        self.parts = {
            'head': atlas.copy(40, 0, 570, 590),
            'torso': atlas.copy(710, 105, 320, 400),
            'upper': atlas.copy(1210, 210, 200, 280),
            'fore': atlas.copy(215, 680, 185, 280),
            'thigh': atlas.copy(725, 640, 215, 340),
            'shin': atlas.copy(1170, 640, 230, 205),
            'shoe': atlas.copy(1185, 855, 275, 120),
            'natural_head': natural.copy(325, 10, 860, 990),
        }
        self.dark = {}
        for name, pix in self.parts.items():
            tinted = pix.copy()
            painter = QPainter(tinted)
            painter.setCompositionMode(QPainter.CompositionMode_SourceAtop)
            painter.fillRect(tinted.rect(), QColor(35, 27, 24, 65))
            painter.end()
            self.dark[name] = tinted

    def segment(self, painter, name, a, b, width, far=False):
        pix = (self.dark if far else self.parts)[name]
        length = math.dist(a, b)
        painter.save()
        painter.translate(*a)
        painter.rotate(-math.degrees(math.atan2(b[0] - a[0], b[1] - a[1])))
        painter.drawPixmap(QRectF(-width / 2, -length * .12, width, length * 1.24), pix, QRectF(pix.rect()))
        painter.restore()

    def draw_limb(self, painter, limb, leg, arm, far, arms):
        if arms:
            self.segment(painter, 'upper', limb['shoulder'], limb['elbow'], arm * .9, far)
            self.segment(painter, 'fore', limb['elbow'], limb['wrist'], arm * .72, far)
        else:
            self.segment(painter, 'shin', limb['knee'], limb['ankle'], leg * .48, far)
            self.segment(painter, 'thigh', limb['hip'], limb['knee'], leg * .56, far)
            pix = (self.dark if far else self.parts)['shoe']
            painter.save()
            painter.translate(*limb['ankle'])
            if not limb['stance']:
                painter.rotate(-22 * math.sin(math.pi * (limb['phase'] - .4) / .6))
            painter.drawPixmap(QRectF(-leg * .24, -leg * .08, leg * .72, leg * .30), pix, QRectF(pix.rect()))
            painter.restore()

    def render(self, mode, frame, debug=False):
        phase = (frame % FRAME_COUNT) / FRAME_COUNT
        data = pose(mode, phase)
        pixmap = QPixmap(1000, 1000)
        pixmap.fill(Qt.transparent)
        p = QPainter(pixmap)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        near, far = data['limbs']
        for arms in (False, True):
            self.draw_limb(p, far, data['leg'], data['arm'], True, arms)
        self.draw_limb(p, near, data['leg'], data['arm'], False, False)
        shoulder = data['shoulder']
        head = self.parts['natural_head' if mode == 'natural' else 'head']
        height = 500 if mode == 'natural' else 650
        width = height * head.width() / head.height()
        left = shoulder[0] - width * .68
        top = shoulder[1] - height * (.61 if mode == 'natural' else .68)
        # Head stays rigid; only the lower hair strips receive delayed sway.
        for y in range(0, head.height(), 8):
            fraction = y / head.height()
            sway = max(0, (fraction - .69) / .31) ** 2 * 9 * math.sin(phase * 4 * math.pi - fraction * 2)
            band = min(10, head.height() - y)
            p.drawPixmap(QRectF(left + sway, top + y / head.height() * height, width, band / head.height() * height),
                         head, QRectF(0, y, head.width(), band))
        torso = self.parts['torso']
        p.drawPixmap(QRectF(shoulder[0] - 90, shoulder[1] - 35, 160, data['hip_y'] - shoulder[1] + 65),
                     torso, QRectF(torso.rect()))
        self.draw_limb(p, near, data['leg'], data['arm'], False, True)
        if debug:
            for limb, color in ((far, '#e6a235'), (near, '#16b4c7')):
                p.setPen(QPen(QColor(color), 7))
                for chain in (('hip', 'knee', 'ankle'), ('shoulder', 'elbow', 'wrist')):
                    for a, b in zip(chain, chain[1:]):
                        p.drawLine(QPointF(*limb[a]), QPointF(*limb[b]))
        p.end()
        return pixmap
