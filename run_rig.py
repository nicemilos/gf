"""Deterministic side-view run: one identity per limb, a half-cycle apart."""
import math
from pathlib import Path
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QPixmap, QPainter, QColor, QPen, QPainterPath

FRAME_COUNT = 16
FPS = 24
GROUND = 940.0
STANCE_END = .32
CANVAS_WIDTH = 1280
CANVAS_HEIGHT = 1000
SCENE_X = 150

# One foot: contact, push-off, heel recovery behind the body, forward swing,
# extension, then contact again. Values are in units of one leg segment.
# The stance velocity is also the touchdown / toe-off tangent, so the foot
# does not stop or reverse abruptly when it meets or leaves the floor.
FOOT_KEYS = (
    (0., .95, 0., -6.25, 0.),
    (.32, -1.05, 0., -6.25, 0.),
    (.46, -1.35, -.90, 2., -6.),
    (.62, -.40, -1.10, 8., 1.),
    (.80, 1., -.65, 5., 4.),
    (.90, 1.10, -.25, 0., 4.),
    (1., .95, 0., -6.25, 0.),
)


def foot_path(phase):
    """Periodic Hermite trajectory; the supporting foot moves steadily back."""
    phase %= 1
    for a, b in zip(FOOT_KEYS, FOOT_KEYS[1:]):
        if phase <= b[0]:
            duration = b[0] - a[0]
            t = (phase - a[0]) / duration
            h00, h10 = 2 * t ** 3 - 3 * t ** 2 + 1, t ** 3 - 2 * t ** 2 + t
            h01, h11 = -2 * t ** 3 + 3 * t ** 2, t ** 3 - t ** 2
            return tuple(h00 * a[i] + h10 * duration * a[i + 2]
                         + h01 * b[i] + h11 * duration * b[i + 2] for i in (1, 2))


def endpoint(origin, length, angle):
    """Angle measured from downward vertical, positive toward the front."""
    return (origin[0] + length * math.sin(angle),
            origin[1] + length * math.cos(angle))


def smoothstep(t):
    t = min(1., max(0., t))
    return t * t * (3 - 2 * t)


def shoe_rotation(phase):
    """Heel reach, flat support, toe push, heel recovery, then reach again."""
    keys = ((0., -18), (.08, 0), (.20, 0), (.32, 50), (.46, 85),
            (.62, 20), (.80, -25), (.90, -28), (1., -18))
    for (a, x), (b, y) in zip(keys, keys[1:]):
        if phase <= b:
            return x + (y - x) * smoothstep((phase - a) / (b - a))


def sole_lift(angle, leg):
    # Height of the heel/toe after rotation, relative to a level sole. Raising
    # the ankle by this amount keeps the supporting shoe above the floor.
    radians = math.radians(angle)
    pivot_x = .54 if angle >= 0 else -.25
    return leg * max(0., pivot_x * math.sin(radians) + .24 * math.cos(radians) - .24)


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
    leg = 205 if mode == 'natural' else 160
    # Compress during support and rise in flight. Both legs share this pelvis.
    hip_y = GROUND - leg * 1.45 + leg * .11 * math.cos(4 * math.pi * (phase - .20))
    lean = (18 if mode == 'natural' else 23) + 3 * math.sin(phase * 4 * math.pi)
    torso_length = (285 if mode == 'natural' else 220) * (1 + .025 * math.cos(phase * 4 * math.pi))
    angle = math.radians(lean)
    shoulder = (500 + torso_length * math.sin(angle), hip_y - torso_length * math.cos(angle))
    arm = 135 if mode == 'natural' else 125
    # Attachment point follows the shoulder of the open, flared jacket.
    arm_shoulder = (500 - 65 * math.cos(angle) + (torso_length - 65) * math.sin(angle),
                    hip_y - 65 * math.sin(angle) - (torso_length - 65) * math.cos(angle))
    limbs = []
    for offset in (0, .5):
        p = (phase + offset) % 1
        foot_x, foot_y = foot_path(p)
        shoe_angle = shoe_rotation(p)
        support_blend = (1. if p <= STANCE_END else
                         1 - smoothstep((p - STANCE_END) / (.46 - STANCE_END)) if p < .46 else
                         smoothstep((p - .9) / .1) if p > .9 else 0.)
        hip = (500, hip_y)
        reach = 1.12 if mode == 'natural' else 1.20
        ankle = (500 + leg * foot_x * reach,
                 GROUND + leg * foot_y - support_blend * sole_lift(shoe_angle, leg))
        knee = ik(hip, ankle, leg)
        # The upper arm counter-swings against its OWN thigh, not the foot.
        # A recovering heel can be behind the body while its knee drives ahead.
        # Exaggerate the silhouette: open the elbow on the backswing and tuck
        # it on the forward swing instead of locking it to a right angle.
        thigh_angle = math.atan2(knee[0] - hip[0], knee[1] - hip[1])
        swing = math.tanh(thigh_angle / math.radians(43))
        arm_angle = math.radians(-66.5 * swing - 11.5 * swing * swing)
        forward = smoothstep((math.degrees(arm_angle) + 60) / 110)
        elbow_turn = math.radians(18 + 77 * forward)
        elbow = endpoint(arm_shoulder, arm, arm_angle)
        wrist = endpoint(elbow, arm, arm_angle + elbow_turn)
        limbs.append(dict(hip=hip, knee=knee, ankle=ankle, shoulder=arm_shoulder,
                          elbow=elbow, wrist=wrist, phase=p, stance=p <= STANCE_END,
                          shoe_angle=shoe_angle))
    return dict(limbs=limbs, hip_y=hip_y, shoulder=shoulder, leg=leg, arm=arm,
                torso_length=torso_length, lean=lean)


class RunRig:
    def __init__(self, assets):
        atlas = QPixmap(str(Path(assets) / 'rig/parts.png'))
        natural = QPixmap(str(Path(assets) / 'rig/natural-head.png'))
        expressive = QPixmap(str(Path(assets) / 'rig/expressive-run.png'))
        if atlas.isNull() or natural.isNull() or expressive.isNull():
            raise RuntimeError('Missing run rig artwork')
        self.parts = {
            'head': expressive.copy(0, 90, 990, 780),
            'torso': expressive.copy(1080, 350, 440, 510),
            # Plain sleeve fabric between the old socket and cuff. The rig
            # supplies rounded joint ends, avoiding exposed hollow sockets.
            'upper': atlas.copy(1225, 250, 165, 185),
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
        # The calf ends at the ankle; extending it beyond the pivot leaves a
        # pointed trouser flap sticking through the separately rotated shoe.
        extent = 1.12 if name == 'shin' else 1.24
        target = QRectF(-width / 2, -length * .12, width, length * extent)
        if name == 'upper':
            sleeve = QPainterPath()
            sleeve.addRoundedRect(target, width * .46, width * .46)
            painter.setClipPath(sleeve)
        painter.drawPixmap(target, pix, QRectF(pix.rect()))
        painter.restore()

    def draw_limb(self, painter, limb, leg, arm, far, arms):
        if arms:
            self.segment(painter, 'upper', limb['shoulder'], limb['elbow'], arm * .95, far)
            self.segment(painter, 'fore', limb['elbow'], limb['wrist'], arm * .85, far)
        else:
            self.segment(painter, 'shin', limb['knee'], limb['ankle'], leg * .70, far)
            self.segment(painter, 'thigh', limb['hip'], limb['knee'], leg * .78, far)
            pix = (self.dark if far else self.parts)['shoe']
            painter.save()
            painter.translate(*limb['ankle'])
            painter.rotate(limb['shoe_angle'])
            painter.drawPixmap(QRectF(-leg * .30, -leg * .08, leg * .88, leg * .32), pix, QRectF(pix.rect()))
            painter.restore()

    def render(self, mode, frame, debug=False):
        phase = (frame % FRAME_COUNT) / FRAME_COUNT
        data = pose(mode, phase)
        pixmap = QPixmap(CANVAS_WIDTH, CANVAS_HEIGHT)
        pixmap.fill(Qt.transparent)
        p = QPainter(pixmap)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        p.translate(SCENE_X, 0)
        near, far = data['limbs']
        for arms in (False, True):
            self.draw_limb(p, far, data['leg'], data['arm'], True, arms)
        self.draw_limb(p, near, data['leg'], data['arm'], False, False)
        shoulder = data['shoulder']
        head = self.parts['natural_head' if mode == 'natural' else 'head']
        height = 450 if mode == 'natural' else 650
        width = height * head.width() / head.height()
        left = shoulder[0] - width * (.68 if mode == 'natural' else .76)
        top = shoulder[1] - height * (.61 if mode == 'natural' else .66)
        # Vertical strips bend only the trailing hair; the face and glasses
        # remain rigid. The wave travels toward the tips with a phase delay.
        for x in range(0, head.width(), 4):
            fraction = x / head.width()
            weight = max(0, (.72 - fraction) / .72) ** 1.5
            sway = weight * (24 * math.sin(phase * 4 * math.pi - fraction * 4) - 12)
            band = min(5, head.width() - x)
            p.drawPixmap(QRectF(left + x / head.width() * width, top + sway,
                               band / head.width() * width, height),
                         head, QRectF(x, 0, band, head.height()))
        torso = self.parts['torso']
        p.save()
        p.translate(500, data['hip_y'])
        p.rotate(data['lean'])
        torso_width = 300 if mode == 'natural' else 320
        torso_height = data['torso_length'] + 65
        # The hem opens and recoils after each push-off. Keep the neckline
        # anchored while the lower fabric changes width and trails backward.
        for y in range(0, torso.height(), 4):
            v = y / torso.height()
            flutter = v * v * math.sin(phase * 4 * math.pi - v * 2.5)
            width = torso_width * (1 + .12 * flutter)
            band = min(5, torso.height() - y)
            p.drawPixmap(QRectF(-torso_width * .62 - 18 * flutter,
                               -data['torso_length'] - 30 + v * torso_height,
                               width, band / torso.height() * torso_height),
                         torso, QRectF(0, y, torso.width(), band))
        p.restore()
        self.draw_limb(p, near, data['leg'], data['arm'], False, True)
        if debug:
            for limb, color in ((far, '#e6a235'), (near, '#16b4c7')):
                p.setPen(QPen(QColor(color), 7))
                for chain in (('hip', 'knee', 'ankle'), ('shoulder', 'elbow', 'wrist')):
                    for a, b in zip(chain, chain[1:]):
                        p.drawLine(QPointF(*limb[a]), QPointF(*limb[b]))
        p.end()
        return pixmap
