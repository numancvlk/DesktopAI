#LIBRARIES
from typing import Optional
from pydantic import BaseModel

#BU SCRIPT ILERISI ICIN SUANLIK SADECE ISKELET TODO 

class VoiceConfig(BaseModel):

    stt: Optional[str] = None
    tts: Optional[str] = None
    sttLanguage: Optional[str] = None
    ttsLanguage: Optional[str] = None

    class Config:
        extra = "ignore"


class SpeechToTextBackend: #STT Backend
    def start_listening(self, config: Optional[VoiceConfig] = None) -> str:
        raise NotImplementedError("STT henüz uygulanmadı.")

    def stop_listening(self) -> None:
        raise NotImplementedError("STT henüz uygulanmadı.")


class TextToSpeechBackend: #TTS Backend
    def speak(self, text: str, config: Optional[VoiceConfig] = None) -> None:
        raise NotImplementedError("TTS henüz uygulanmadı.")

    def stop(self) -> None:
        raise NotImplementedError("TTS henüz uygulanmadı.")
