"""One pet per user data directory, with local activation of the existing pet."""
import hashlib
import os
from pathlib import Path
from PySide6.QtCore import QObject, QLockFile, Signal
from PySide6.QtNetwork import QLocalServer, QLocalSocket


class SingleInstance(QObject):
    activated = Signal()

    def __init__(self, directory=None):
        super().__init__()
        directory = Path(directory or os.environ.get('XIAOYA_DATA_DIR') or
                         Path(os.environ['LOCALAPPDATA']) / 'XiaoyaLocal')
        directory.mkdir(parents=True, exist_ok=True)
        identity = str(directory.resolve()).casefold().encode('utf-8')
        self.name = 'xiaoya-' + hashlib.sha256(identity).hexdigest()[:24]
        self.lock = QLockFile(str(directory / 'desktop-pet.lock'))
        # Do not expire a lock just because an alive pet has been idle for days.
        # QLockFile still removes a stale lock when its owning process is dead.
        self.lock.setStaleLockTime(0)
        self.primary = self.lock.tryLock(0)
        self.server = None
        if not self.primary:
            if self.lock.error() != QLockFile.LockFailedError:
                raise RuntimeError('无法创建小雅运行锁，请检查用户目录权限')
            socket = QLocalSocket()
            socket.connectToServer(self.name)
            if socket.waitForConnected(1500):
                socket.write(b'show')
                socket.flush()
                socket.waitForBytesWritten(500)
                socket.disconnectFromServer()
            return
        self.server = QLocalServer(self)
        self.server.setSocketOptions(QLocalServer.UserAccessOption)
        if not self.server.listen(self.name):
            self.lock.unlock()
            raise RuntimeError('无法启动小雅本机通信：' + self.server.errorString())
        self.server.newConnection.connect(self._activate)

    def _activate(self):
        while self.server.hasPendingConnections():
            socket = self.server.nextPendingConnection()
            socket.close()
            socket.deleteLater()
            self.activated.emit()

    def close(self):
        if self.primary:
            self.server.close()
            self.lock.unlock()
