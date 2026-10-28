import math
import os
import unittest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtWidgets import QApplication
from run_rig import pose, RunRig, GROUND
from pathlib import Path


class RunCycleTests(unittest.TestCase):
    def test_full_cycle_invariants(self):
        for mode in ('natural', 'q'):
            for frame in range(160):
                phase = frame / 160
                data = pose(mode, phase)
                opposite = pose(mode, phase + .5)
                for side, limb in enumerate(data['limbs']):
                    leg_x = limb['ankle'][0] - limb['hip'][0]
                    arm_x = limb['wrist'][0] - limb['shoulder'][0] - data['arm'] * .45
                    self.assertLessEqual(leg_x * arm_x, 1e-8)
                    for point in ('hip', 'knee', 'ankle', 'shoulder', 'elbow', 'wrist'):
                        for a, b in zip(limb[point], opposite['limbs'][1 - side][point]):
                            self.assertAlmostEqual(a, b, places=7)
                    self.assertLessEqual(limb['ankle'][1], GROUND + 1e-8)
                    if limb['stance']:
                        self.assertAlmostEqual(limb['ankle'][1], GROUND)
                    for a, b, length in (('hip', 'knee', data['leg']), ('knee', 'ankle', data['leg']),
                                          ('shoulder', 'elbow', data['arm']), ('elbow', 'wrist', data['arm'])):
                        self.assertAlmostEqual(math.dist(limb[a], limb[b]), length, places=7)
            self.assertTrue(all(not limb['stance'] for limb in pose(mode, .45)['limbs']))
            self.assertLess(pose(mode, .45)['hip_y'], pose(mode, .2)['hip_y'])
            self.assertEqual(pose(mode, 0), pose(mode, 1))

    def test_all_frames_render_without_edge_clipping(self):
        app = QApplication.instance() or QApplication([])
        rig = RunRig(Path(__file__).parent / 'assets')
        for mode in ('natural', 'q'):
            for frame in range(16):
                img = rig.render(mode, frame).toImage()
                for n in range(1000):
                    for x, y in ((n, 0), (n, 999), (0, n), (999, n)):
                        self.assertEqual(img.pixelColor(x, y).alpha(), 0, (mode, frame, x, y))


if __name__ == '__main__':
    unittest.main()
