#LIBRARIES
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTextEdit,
    QLineEdit,
    QPushButton,
    QLabel,
    QFrame,
)
from ui.workers import LLMWorker


class MainScreen(QMainWindow): #ANA PENCERE
    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = None
        self.build_ui()

    def build_ui(self): #UI BILESENLERI
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        self.chatArea = QTextEdit()
        self.chatArea.setReadOnly(True)
        self.chatArea.setPlaceholderText("Sohbet geçmişi")
        layout.addWidget(self.chatArea)

        self.statusLabel = QLabel("")
        self.statusLabel.setStyleSheet("color: gray;")
        layout.addWidget(self.statusLabel)

        row = QHBoxLayout()
        self.inputLine = QLineEdit()
        self.inputLine.setPlaceholderText("Mesajınızı yazın...")
        self.inputLine.returnPressed.connect(self.on_send_clicked)
        row.addWidget(self.inputLine)

        self.sendButton = QPushButton("Gönder")
        self.sendButton.clicked.connect(self.on_send_clicked)
        row.addWidget(self.sendButton)
        layout.addLayout(row)

        self.setWindowTitle("Desktop Assistant")
        self.setMinimumSize(400, 300)
        self.resize(500, 450)

    def on_send_clicked(self):
        text = self.inputLine.text().strip()

        if not text:
            return

        self.inputLine.clear()
        self.chatArea.append(f"<b>Sen:</b> {text}")
        self.sendButton.setEnabled(False)
        self.statusLabel.setText("Düşünüyor...")
        self.worker = LLMWorker(text)
        self.worker.startedProcessing.connect(self.on_started)
        self.worker.newMessage.connect(self.on_message_ready)
        self.worker.errorOccured.connect(self.on_error)
        self.worker.finishedProcessing.connect(self.on_finished)
        self.worker.start()

    def on_started(self): #Worker basladiginda
        pass

    def on_message_ready(self, text: str): #Worker mesaj hazir oldugunda
        self.chatArea.append(f"<b>Asistan:</b> {text}")

    def on_error(self, message: str): #Worker hatasi oldugunda
        self.chatArea.append(f"<span style='color: red;'><b>Hata:</b> {message}</span>")

    def on_finished(self): #Worker bitirdiginde
        self.statusLabel.setText("")
        self.sendButton.setEnabled(True)
        self.worker = None
