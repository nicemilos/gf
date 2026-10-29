"""Deterministic side-view run: one identity per limb, a half-cycle apart."""
import math
from pathlib import Path
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QPixmap, QPainter, QColor, QPen

FRAME_COUNT = 16
FPS = 24
GROUND = 940.0
STANCE_END = .32
LEAN = 12

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
    leg = 195 if mode == 'natural' else 115
    # Compress during support and rise in flight. Both legs share this pelvis.
    hip_y = GROUND - leg * 1.595 + leg * .10 * math.cos(4 * math.pi * (phase - .20))
    torso_length = 285 if mode == 'natural' else 220
    shoulder = (500 + torso_length * math.sin(math.radians(LEAN)),
                hip_y - torso_length * math.cos(math.radians(LEAN)))
    arm = 120 if mode == 'natural' else 90
    # Match the jacket's side seam, rather than attaching the arm to its chest.
    arm_shoulder = (shoulder[0] - 55, shoulder[1] + 75)
    limbs = []
    for offset in (0, .5):
        p = (phase + offset) % 1
        foot_x, foot_y = foot_path(p)
        hip = (500, hip_y)
        ankle = (500 + leg * foot_x, GROUND + leg * foot_y)
        knee = ik(hip, ankle, leg)
        # The upper arm counter-swings against its OWN thigh, not the foot.
        # A recovering heel can be behind the body while its knee drives ahead.
        # Keep the elbow bent: moving a wrist on a horizontal line produced the
        # previous raised-elbow / paddling pose.
        thigh_angle = math.atan2(knee[0] - hip[0], knee[1] - hip[1])
        arm_angle = -math.radians(55) * math.tanh(thigh_angle / math.radians(45))
        elbow = endpoint(arm_shoulder, arm, arm_angle)
        wrist = endpoint(elbow, arm, arm_angle + math.radians(95))
        # Toe-down recovery follows the calf; reach forward with a level shoe.
        if p <= STANCE_END:
            shoe_angle = 0
        elif p <= .62:
            shoe_angle = 42 * math.sin(math.pi * (p - STANCE_END) / (.62 - STANCE_END)) ** 2
        else:
            shoe_angle = -12 * math.sin(math.pi * (p - .62) / .38) ** 2
        limbs.append(dict(hip=hip, knee=knee, ankle=ankle, shoulder=arm_shoulder,
                          elbow=elbow, wrist=wrist, phase=p, stance=p <= STANCE_END,
                          shoe_angle=shoe_angle))
    return dict(limbs=limbs, hip_y=hip_y, shoulder=shoulder, leg=leg, arm=arm,
                torso_length=torso_length)


class RunRig:
    def __init__(self, assets):
        atlas = QPixmap(str(Path(assets) / 'rig/parts.png'))
        natural = QPixmap(str(Path(assets) / 'rig/natural-head.png'))
        closed_torso = QPixmap(str(Path(assets) / 'rig/parts-closed-torso.png'))
        if atlas.isNull() or natural.isNull() or closed_torso.isNull():
            raise RuntimeError('Missing run rig artwork')
        self.parts = {
            'head': atlas.copy(40, 0, 570, 590),
            'torso': closed_torso.copy(710, 105, 320, 400),
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
        # The calf ends at the ankle; extending it beyond the pivot leaves a
        # pointed trouser flap sticking through the separately rotated shoe.
        extent = 1.12 if name == 'shin' else 1.24
        painter.drawPixmap(QRectF(-width / 2, -length * .12, width, length * extent), pix, QRectF(pix.rect()))
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
        height = 450 if mode == 'natural' else 610
        width = height * head.width() / head.height()
        left = shoulder[0] - width * .68
        top = shoulder[1] - height * (.61 if mode == 'natural' else .68)
        # Head stays rigid; only the lower hair strips receive delayed sway.
        for y in range(0, head.height(), 8):
            fraction = y / head.height()
            hair_weight = max(0, (fraction - .56) / .44) ** 2
            sway = hair_weight * (-32 + 14 * math.sin(phase * 4 * math.pi - fraction * 2))
            band = min(10, head.height() - y)
            p.drawPixmap(QRectF(left + sway, top + y / head.height() * height, width, band / head.height() * height),
                         head, QRectF(0, y, head.width(), band))
        torso = self.parts['torso']
        p.save()
        p.translate(500, data['hip_y'])
        p.rotate(LEAN)
        torso_width = 235 if mode == 'natural' else 215
        p.drawPixmap(QRectF(-torso_width / 2, -data['torso_length'] - 30,
                           torso_width, data['torso_length'] + 65), torso, QRectF(torso.rect()))
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
