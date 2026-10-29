import math
import os
import unittest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtWidgets import QApplication
from run_rig import pose, foot_path, RunRig, GROUND, STANCE_END, FOOT_KEYS
from pathlib import Path


class RunCycleTests(unittest.TestCase):
    def test_full_cycle_invariants(self):
        for mode in ('natural', 'q'):
            for frame in range(160):
                phase = frame / 160
                data = pose(mode, phase)
                opposite = pose(mode, phase + .5)
                near, far = data['limbs']
                self.assertLessEqual((near['knee'][0] - far['knee'][0]) *
                                     (near['wrist'][0] - far['wrist'][0]), 1e-8)
                for side, limb in enumerate(data['limbs']):
                    leg_x = limb['knee'][0] - limb['hip'][0]
                    arm_x = limb['elbow'][0] - limb['shoulder'][0]
                    self.assertLessEqual(leg_x * arm_x, 1e-8)
                    self.assertGreater(limb['elbow'][1], limb['shoulder'][1])
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

    def test_stride_has_extension_recovery_and_flight(self):
        for mode in ('natural', 'q'):
            cycle = [pose(mode, i / 160) for i in range(160)]
            leg = cycle[0]['leg']
            # Large opening between the feet, not the old small-step shuffle.
            self.assertGreater(max(abs(p['limbs'][0]['ankle'][0] - p['limbs'][1]['ankle'][0])
                                   for p in cycle), 2.2 * leg)
            recovery = pose(mode, .46)['limbs'][0]
            self.assertLess(recovery['ankle'][0], recovery['knee'][0])
            self.assertLess(recovery['ankle'][1], recovery['knee'][1])
            drive = pose(mode, .75)['limbs'][0]
            self.assertGreater(drive['knee'][0], drive['hip'][0])
            self.assertLess(drive['knee'][1], drive['ankle'][1])
            for data in cycle:
                self.assertLessEqual(sum(limb['stance'] for limb in data['limbs']), 1)

    def test_foot_path_is_continuous_through_contact_and_wrap(self):
        epsilon = 1e-6
        for key in FOOT_KEYS:
            t = key[0]
            before, at, after = foot_path(t - epsilon), foot_path(t), foot_path(t + epsilon)
            for dimension in (0, 1):
                self.assertAlmostEqual(before[dimension], after[dimension], delta=2e-5)
                left = (at[dimension] - before[dimension]) / epsilon
                right = (after[dimension] - at[dimension]) / epsilon
                self.assertAlmostEqual(left, right, delta=.002)
        for i in range(33):
            x, y = foot_path(STANCE_END * i / 32)
            self.assertAlmostEqual(y, 0)
            self.assertAlmostEqual(x, .95 - 6.25 * STANCE_END * i / 32)

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
