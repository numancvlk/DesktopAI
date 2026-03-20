#LIBRARIES
from PySide6.QtCore import QThread, Signal
from voice.stt import record_audio, transcribe_audio


class VoiceListenWorker(QThread): #STT Worker UI kitlenmesi STT sirasinda diye
    transcriptReady = Signal(str)
    errorOccured = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

    def run(self):
        try:
            audioPath = record_audio()
            transcript = transcribe_audio(audioPath)
            self.transcriptReady.emit(transcript)
        except Exception as exc:
            self.errorOccured.emit(str(exc))


# class VoiceSpeakWorker(QThread): # TTS Worker sistem dostu olmasi icin eklemicem
#     speakFinished = Signal()
#     errorOccured = Signal(str)

#     def __init__(self, text: str = "", parent=None):
#         super().__init__(parent)
#         self.text = text

#     def run(self):
#         raise NotImplementedError("Ses çıktısı etkin degil")
