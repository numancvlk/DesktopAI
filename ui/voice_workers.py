#LIBRARIES
from PySide6.QtCore import QThread, Signal


class VoiceListenWorker(QThread): #STT Worker
    transcriptReady = Signal(str)
    errorOccured = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

    def run(self):
        raise NotImplementedError("Ses dinleme etkin degil")


class VoiceSpeakWorker(QThread): # TTS Worker
    speakFinished = Signal()
    errorOccured = Signal(str)

    def __init__(self, text: str = "", parent=None):
        super().__init__(parent)
        self.text = text

    def run(self):
        raise NotImplementedError("Ses çıktısı etkin degil")
