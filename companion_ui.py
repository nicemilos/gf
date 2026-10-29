import html
import random
import threading
from PySide6.QtCore import Qt, QObject, Signal, QTimer, QPoint
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit,
                               QPushButton, QComboBox, QFormLayout, QDialogButtonBox, QCheckBox,
                               QMessageBox, QApplication)
from companion import Store, PERSONALITY, PROVIDERS, chat, probe

STYLE = '''
QDialog, QMenu {background:#fffaf5; color:#453b36; font: 10pt "Microsoft YaHei UI";}
QMenu {border:1px solid #e5d8ce; border-radius:10px; padding:8px;}
QMenu::item {padding:9px 24px 9px 16px; border-radius:6px;}
QMenu::item:selected {background:#f5e5d8; color:#634838;}
QMenu::separator {height:1px; background:#e8ddd4; margin:5px 10px;}
QLineEdit, QTextEdit, QComboBox {background:white; border:1px solid #decfc3; border-radius:7px; padding:7px; color:#453b36;}
QPushButton {background:#f0ded0; border:0; border-radius:7px; padding:8px 14px; color:#453b36;}
QPushButton:hover {background:#e8cfbd;} QPushButton:disabled {color:#999;}
QLabel {color:#554a42;}
'''


def beside(pet, size):
    screen = QApplication.screenAt(pet.frameGeometry().center()) or QApplication.primaryScreen()
    area = screen.availableGeometry()
    rect = pet.frameGeometry()
    x = rect.right() + 14
    if x + size.width() > area.right():
        x = rect.left() - size.width() - 14
    if x < area.left():
        if rect.top() - size.height() - 14 >= area.top():
            return QPoint(max(area.left(), min(rect.left(), area.right() - size.width() + 1)), rect.top() - size.height() - 14)
        if rect.bottom() + size.height() + 14 <= area.bottom():
            return QPoint(max(area.left(), min(rect.left(), area.right() - size.width() + 1)), rect.bottom() + 14)
    x = max(area.left(), min(x, area.right() - size.width() + 1))
    y = max(area.top(), min(rect.top(), area.bottom() - size.height() + 1))
    return QPoint(x, y)


class Jobs(QObject):
    finished = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.callbacks = {}
        self.serial = 0
        self.finished.connect(self.deliver)

    def start(self, function, callback):
        self.serial += 1
        token = self.serial
        self.callbacks[token] = callback
        def run():
            try:
                result, error = function(), ''
            except Exception as exc:
                result, error = None, str(exc)
            try:
                self.finished.emit((token, result, error))
            except RuntimeError:
                pass  # Application has closed; daemon worker owns no GUI state.
        threading.Thread(target=run, daemon=True).start()

    def deliver(self, item):
        token, result, error = item
        callback = self.callbacks.pop(token, None)
        if callback:
            callback(result, error)


class ConfigDialog(QDialog):
    def __init__(self, controller):
        super().__init__(controller.pet)
        self.controller = controller
        self.setWindowTitle('小雅 · 模型配置')
        self.setStyleSheet(STYLE)
        self.resize(510, 380)
        self.testing = False
        self.pending = False
        self.closed = False
        self.finished.connect(lambda _: setattr(self, 'closed', True))
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel('选择厂商，填写密钥；失去输入焦点后自动检测。'))
        form = QFormLayout()
        self.provider = QComboBox()
        self.provider.addItems(PROVIDERS)
        self.base = QLineEdit()
        self.key = QLineEdit()
        self.key.setEchoMode(QLineEdit.Password)
        self.model = QComboBox()
        self.model.setEditable(True)
        self.model.lineEdit().setPlaceholderText('可自动发现，也可填写模型 ID')
        form.addRow('模型厂商', self.provider)
        form.addRow('接口地址', self.base)
        form.addRow('API Key', self.key)
        form.addRow('模型', self.model)
        layout.addLayout(form)
        self.status = QLabel('兼容 Chat Completions 接口；密钥使用 Windows 加密保存在本机。')
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        layout.addWidget(QLabel('连通检测会发送一条简短测试消息；本地模型可以不填密钥。'))
        self.detect = QPushButton('检测连通')
        self.detect.clicked.connect(self.test)
        layout.addWidget(self.detect)
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Save).setText('保存')
        buttons.button(QDialogButtonBox.Cancel).setText('取消')
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        try:
            config = controller.store.credentials()
        except RuntimeError as error:
            config = controller.store.config()
            self.status.setText(str(error))
        self.provider.setCurrentText(config.get('provider', 'DeepSeek'))
        preset = PROVIDERS[self.provider.currentText()]
        self.base.setText(config.get('base_url', preset[0]))
        self.key.setText(config.get('api_key', ''))
        self.model.setEditText(config.get('model', preset[1]))
        self.provider.currentTextChanged.connect(self.preset)
        self.debounce = QTimer(self)
        self.debounce.setSingleShot(True)
        self.debounce.timeout.connect(self.test)
        for edit in (self.base, self.key, self.model.lineEdit()):
            edit.textEdited.connect(lambda _: self.mark_changed())
            edit.editingFinished.connect(lambda: self.debounce.start(700))
        self.fingerprint = None

    def values(self):
        return dict(provider=self.provider.currentText(), base_url=self.base.text().strip(),
                    api_key=self.key.text().strip(), model=self.model.currentText().strip())

    def mark_changed(self):
        self.fingerprint = None
        self.status.setText('配置已更改，等待检测。')

    def preset(self, name):
        url, model = PROVIDERS[name]
        self.base.setText(url)
        self.model.setEditText(model)
        self.mark_changed()
        # Do not send an existing vendor's key to a newly selected vendor.
        self.key.clear()

    def test(self):
        if self.closed:
            return
        config = self.values()
        if not config['base_url']:
            self.status.setText('请填写接口地址。')
            return
        if not config['api_key'] and self.provider.currentText() != '本地 Ollama':
            self.status.setText('请填写 API Key；本地 Ollama 可留空。')
            return
        if self.testing:
            self.pending = True
            return
        if config == self.fingerprint:
            return
        self.testing = True
        self.detect.setEnabled(False)
        self.status.setText('正在获取模型列表并测试聊天连通…')
        def done(result, error):
            self.testing = False
            if self.closed:
                return
            self.detect.setEnabled(True)
            if config != self.values():
                self.status.setText('配置已变更，旧检测结果已忽略。')
            elif error:
                self.status.setText('检测失败：' + error)
            else:
                self.model.blockSignals(True)
                self.model.clear()
                self.model.addItems(result['models'])
                self.model.setEditText(result['model'])
                self.model.blockSignals(False)
                if result.get('error'):
                    self.status.setText('已获取模型列表，但聊天检测失败：' + result['error'] + '；可选择其他模型重试。')
                else:
                    self.fingerprint = self.values()
                    self.status.setText('连接成功，模型可以正常回复。')
            if self.pending:
                self.pending = False
                self.debounce.start(700)
        self.controller.jobs.start(lambda: probe(config), done)

    def save(self):
        config = self.values()
        try:
            from companion import endpoint
            endpoint(config)
            if not config['model']:
                raise ValueError('请先检测并选择模型，或填写模型 ID')
            self.controller.store.save_config(config)
        except (ValueError, RuntimeError) as error:
            self.status.setText(str(error))
            return
        self.accept()


class MemoryDialog(QDialog):
    def __init__(self, controller):
        super().__init__(controller.pet)
        self.setWindowTitle('小雅 · 性格与记忆')
        self.setStyleSheet(STYLE)
        self.resize(540, 610)
        self.store = controller.store
        layout = QVBoxLayout(self)
        self.fields = {}
        for key, title, default in (('personality', '小雅的性格', PERSONALITY), ('user_notes', '关于你的资料与偏好', ''), ('memory', '长期记忆（可编辑、纠正或清空）', '')):
            layout.addWidget(QLabel(title))
            field = QTextEdit()
            field.setPlainText(self.store.get(key, default))
            self.fields[key] = field
            layout.addWidget(field)
        self.auto = QCheckBox('每8轮对话自动整理一次长期记忆（额外调用模型）')
        self.auto.setChecked(self.store.get('auto_memory', '1') == '1')
        layout.addWidget(self.auto)
        layout.addWidget(QLabel('聊天历史和记忆保存在本机；聊天时会发送相关内容给你配置的模型。'))
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Save).setText('保存')
        buttons.button(QDialogButtonBox.Cancel).setText('取消')
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def save(self):
        for key, field in self.fields.items():
            self.store.set(key, field.toPlainText()[:6000])
        self.store.set('auto_memory', '1' if self.auto.isChecked() else '0')
        self.accept()


class ChatDialog(QDialog):
    def __init__(self, controller):
        super().__init__(controller.pet)
        self.controller = controller
        self.setWindowTitle('和小雅聊天')
        self.setStyleSheet(STYLE)
        self.resize(440, 520)
        layout = QVBoxLayout(self)
        self.history = QTextEdit()
        self.history.setReadOnly(True)
        layout.addWidget(self.history)
        self.input = QLineEdit()
        self.input.setPlaceholderText('想和小雅说些什么？')
        self.input.setMaxLength(6000)
        self.input.returnPressed.connect(self.send)
        layout.addWidget(self.input)
        row = QHBoxLayout()
        self.send_button = QPushButton('发送')
        self.send_button.clicked.connect(self.send)
        row.addWidget(self.send_button)
        settings = QPushButton('模型配置')
        settings.clicked.connect(controller.configure)
        row.addWidget(settings)
        clear = QPushButton('清空聊天')
        clear.clicked.connect(self.clear)
        row.addWidget(clear)
        layout.addLayout(row)
        self.status = QLabel('记忆可在右键菜单“性格与记忆”中查看。')
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        self.reload()

    def reload(self):
        self.history.clear()
        for row in self.controller.store.history(100):
            self.append(row['role'], row['content'])

    def append(self, role, content):
        self.history.append('<p><b>' + ('你' if role == 'user' else '小雅') + '</b><br>' + html.escape(content).replace('\n', '<br>') + '</p>')
        self.history.verticalScrollBar().setValue(self.history.verticalScrollBar().maximum())

    def send(self):
        question = self.input.text().strip()
        if not question or self.controller.busy:
            return
        if self.controller.send(question):
            self.append('user', question)
            self.input.clear()
            self.send_button.setEnabled(False)
            self.status.setText('小雅正在想…')

    def clear(self):
        if self.controller.busy:
            return
        if QMessageBox.question(self, '清空聊天', '删除本机聊天历史？长期记忆会保留，可在“性格与记忆”中编辑。') == QMessageBox.Yes:
            self.controller.store.clear_history()
            self.reload()


class Companion(QObject):
    def __init__(self, pet):
        super().__init__(pet)
        self.pet = pet
        self.store = Store()
        self.jobs = Jobs(self)
        self.busy = False
        self.window = None
        self.bubble = QLabel(None, Qt.ToolTip | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.bubble.setWordWrap(True)
        self.bubble.setTextFormat(Qt.PlainText)
        self.bubble.setStyleSheet('QLabel {background:#fff8ed;color:#594236;border:1px solid #dcc5b0;border-radius:12px;padding:13px;font:11pt "Microsoft YaHei UI";}')
        self.bubble.setFixedWidth(265)
        self.bubble_timer = QTimer(self)
        self.bubble_timer.setSingleShot(True)
        self.bubble_timer.timeout.connect(self.bubble.hide)
        QApplication.instance().aboutToQuit.connect(self.bubble.close)

    def speak(self, text=None):
        text = text or random.choice(('怎么了？我在这儿呢。', '你在干嘛呀？', '忙完了吗？陪我聊一会儿吧。', '被你发现我在偷偷看你啦。'))
        self.bubble.setText(text[:320])
        self.bubble.adjustSize()
        self.bubble.move(beside(self.pet, self.bubble.size()))
        self.bubble.show()
        self.bubble_timer.start(6500)

    def configure(self):
        dialog = ConfigDialog(self)
        dialog.move(beside(self.pet, dialog.size()))
        dialog.exec()

    def memory(self):
        if self.busy:
            self.speak('等我回复完这一句，再一起整理记忆好吗？')
            return
        dialog = MemoryDialog(self)
        dialog.move(beside(self.pet, dialog.size()))
        dialog.exec()

    def open_chat(self):
        self.bubble.hide()
        if self.window is None:
            self.window = ChatDialog(self)
        self.window.move(beside(self.pet, self.window.size()))
        self.window.show()
        self.window.raise_()
        self.window.activateWindow()
        self.window.input.setFocus()

    def send(self, question):
        try:
            config = self.store.credentials()
            if not config.get('base_url') or not config.get('model'):
                self.configure()
                config = self.store.credentials()
            if not config.get('base_url') or not config.get('model'):
                return False
        except RuntimeError as error:
            self.speak(str(error))
            return False
        self.busy = True
        def done(result, error):
            self.busy = False
            self.window.send_button.setEnabled(True)
            if error:
                self.window.status.setText('发送失败：' + error + '；输入框已保留原消息，可重试。')
                self.window.input.setText(question)
                self.window.reload()
            else:
                self.window.append('assistant', result['answer'])
                self.window.status.setText(result['note'] or '已保存聊天记录。')
                self.speak(result['answer'])
        self.jobs.start(lambda: chat(self.store, config, question), done)
        return True
