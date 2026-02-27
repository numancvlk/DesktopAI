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


class MainScreen(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = None
        self.voiceWorker = None
        self.build_ui()

    def build_ui(self): 
        self.setWindowTitle("Desktop Assistant")
        self.setMinimumSize(600, 420)
        self.resize(720, 520)

        self.setStyleSheet(
            """
            QMainWindow {
                background-color: #020617;
            }

            QWidget {
                font-family: "Segoe UI", Arial, sans-serif;
                font-size: 13px;
                color: #e5e7eb;
            }

            QTextEdit {
                background-color: #020617;
                border-radius: 10px;
                padding: 10px;
                color: #e5e7eb;
                border: 1px solid #111827;
            }

            QTextEdit:disabled {
                background-color: #020617;
                color: #6b7280;
            }

            QLineEdit {
                background-color: #020617;
                border-radius: 999px;
                padding: 8px 14px;
                border: 1px solid #1e293b;
                color: #e5e7eb;
            }

            QLineEdit:focus {
                border: 1px solid #2563eb;
            }

            QLabel#TitleLabel {
                color: #f9fafb;
                font-size: 18px;
                font-weight: 600;
            }

            QLabel#SubtitleLabel {
                color: #9ca3af;
                font-size: 11px;
            }

            QLabel#StatusLabel {
                color: #9ca3af;
                font-size: 11px;
            }

            QPushButton {
                border-radius: 999px;
                padding: 7px 16px;
                font-size: 13px;
                font-weight: 500;
                border: 1px solid #1f2937;
                background-color: #020617;
                color: #e5e7eb;
            }

            QPushButton:hover:!disabled {
                background-color: #111827;
            }

            QPushButton:pressed:!disabled {
                background-color: #020617;
                border-color: #111827;
            }

            QPushButton:disabled {
                color: #6b7280;
                border-color: #0b1120;
                background-color: #020617;
            }

            QPushButton#PrimaryButton {
                background-color: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #2563eb,
                    stop: 1 #4f46e5
                );
                border-color: #1d4ed8;
                color: #f9fafb;
            }

            QPushButton#PrimaryButton:hover:!disabled {
                background-color: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #1d4ed8,
                    stop: 1 #4338ca
                );
                border-color: #1d4ed8;
            }

            QPushButton#PrimaryButton:pressed:!disabled {
                background-color: #1d4ed8;
                border-color: #1e40af;
            }

            QPushButton#VoiceButton {
                background-color: #022c22;
                border-color: #064e3b;
                color: #a7f3d0;
            }

            QPushButton#VoiceButton:hover:!disabled {
                background-color: #064e3b;
            }

            QPushButton#VoiceButton:pressed:!disabled {
                background-color: #022c22;
            }

            QFrame#BottomBar {
                background-color: #020617;
                border-radius: 999px;
                border: 1px solid #111827;
            }

            QScrollBar:vertical {
                background: #020617;
                width: 8px;
                margin: 4px 0 4px 0;
            }

            QScrollBar::handle:vertical {
                background: #1f2937;
                border-radius: 4px;
            }

            QScrollBar::handle:vertical:hover {
                background: #374151;
            }

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }
            """
        )

        central = QWidget()
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(10)

        headerRow = QHBoxLayout()

        titleColumn = QVBoxLayout()
        titleLabel = QLabel("Desktop Assistant")
        titleLabel.setObjectName("TitleLabel")
        subtitleLabel = QLabel("Masaüstünüzde çalışan akıllı asistan")
        subtitleLabel.setObjectName("SubtitleLabel")
        titleColumn.addWidget(titleLabel)
        titleColumn.addWidget(subtitleLabel)

        headerRow.addLayout(titleColumn)
        headerRow.addStretch()

        self.statusLabel = QLabel("Hazır")
        self.statusLabel.setObjectName("StatusLabel")
        headerRow.addWidget(self.statusLabel, alignment=Qt.AlignRight | Qt.AlignVCenter)

        root.addLayout(headerRow)

        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setFrameShadow(QFrame.Sunken)
        divider.setStyleSheet("color: #1f2937;")
        root.addWidget(divider)

        self.chatArea = QTextEdit()
        self.chatArea.setReadOnly(True)
        self.chatArea.setPlaceholderText("Sohbet geçmişi burada görünecek...")
        root.addWidget(self.chatArea, stretch=1)


        bottomFrame = QFrame()
        bottomFrame.setObjectName("BottomBar")
        bottomLayout = QHBoxLayout(bottomFrame)
        bottomLayout.setContentsMargins(10, 8, 10, 8)
        bottomLayout.setSpacing(8)

        self.inputLine = QLineEdit()
        self.inputLine.setPlaceholderText("Mesajınızı yazın veya 'Ses' ile söyleyin...")
        self.inputLine.returnPressed.connect(self.on_send_clicked)
        bottomLayout.addWidget(self.inputLine, stretch=1)

        self.voiceButton = QPushButton("Ses")
        self.voiceButton.setObjectName("VoiceButton")
        self.voiceButton.setToolTip("Mikrofon ile konuş")
        self.voiceButton.clicked.connect(self.on_voice_clicked)
        bottomLayout.addWidget(self.voiceButton)

        self.sendButton = QPushButton("Gönder")
        self.sendButton.setObjectName("PrimaryButton")
        self.sendButton.setToolTip("Mesajı gönder (Enter)")
        self.sendButton.clicked.connect(self.on_send_clicked)
        bottomLayout.addWidget(self.sendButton)

        root.addWidget(bottomFrame)

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
