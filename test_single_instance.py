"""Exercise real process locks and activation, including crash recovery."""
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parent
WORKER = '''
import sys
from pathlib import Path
from PySide6.QtCore import QCoreApplication, QTimer
from single_instance import SingleInstance
app = QCoreApplication(sys.argv)
folder = Path(sys.argv[1])
instance = SingleInstance(folder)
if not instance.primary:
    sys.exit(0)
instance.activated.connect(lambda: (folder / 'activated').write_text('yes'))
(folder / 'ready').write_text('yes')
app.aboutToQuit.connect(instance.close)
QTimer.singleShot(30000, app.quit)
sys.exit(app.exec())
'''


class SingleInstanceTests(unittest.TestCase):
    def wait_file(self, path):
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline:
            if path.exists():
                return
            time.sleep(.05)
        self.fail(f'Timed out waiting for {path.name}')

    def test_duplicate_activation_and_crash_recovery(self):
        with tempfile.TemporaryDirectory(prefix='xiaoya-instance-') as directory:
            folder = Path(directory)
            args = [sys.executable, '-c', WORKER, directory]
            first = subprocess.Popen(args, cwd=ROOT)
            try:
                self.wait_file(folder / 'ready')
                duplicates = [subprocess.Popen(args, cwd=ROOT) for _ in range(4)]
                try:
                    for process in duplicates:
                        self.assertEqual(process.wait(timeout=8), 0)
                finally:
                    for process in duplicates:
                        if process.poll() is None:
                            process.kill()
                            process.wait()
                self.assertIsNone(first.poll())
                self.wait_file(folder / 'activated')
            finally:
                first.kill()
                first.wait()
            (folder / 'ready').unlink()
            replacement = subprocess.Popen(args, cwd=ROOT)
            try:
                self.wait_file(folder / 'ready')
                self.assertIsNone(replacement.poll())
            finally:
                replacement.kill()
                replacement.wait()


if __name__ == '__main__':
    unittest.main()
