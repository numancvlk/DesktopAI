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
from ui.voice_workers import VoiceListenWorker


class MainScreen(QMainWindow): #ANA PENCERE
    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = None
        self.voiceWorker = None
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

        self.voiceButton = QPushButton("Ses")
        self.voiceButton.clicked.connect(self.on_voice_clicked)
        row.addWidget(self.voiceButton)
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

    def on_voice_clicked(self): #Sesle mesaj gonderme
        if self.voiceWorker is not None:
            return

        self.voiceButton.setEnabled(False)
        self.statusLabel.setText("Dinliyor...")

        self.voiceWorker = VoiceListenWorker()
        self.voiceWorker.transcriptReady.connect(self.on_voice_transcript_ready)
        self.voiceWorker.errorOccured.connect(self.on_voice_error)
        self.voiceWorker.finished.connect(self.on_voice_finished)
        self.voiceWorker.start()

    def on_voice_transcript_ready(self, text: str):
        if not text:
            self.statusLabel.setText("")
            self.voiceButton.setEnabled(True)
            return

        self.inputLine.setText(text)
        self.on_send_clicked()

    def on_voice_error(self, message: str):
        self.chatArea.append(
            f"<span style='color: red;'><b>Ses Hatası:</b> {message}</span>"
        )

    def on_voice_finished(self):
        self.statusLabel.setText("")
        self.voiceButton.setEnabled(True)
        self.voiceWorker = None
