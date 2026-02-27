#LIBRARIES
import os
import tempfile
import wave
import sounddevice as sd

from pathlib import Path
from typing import Optional
from faster_whisper import WhisperModel
from core.config import get_settings

stt_model: Optional[WhisperModel] = None

def get_stt_model() -> WhisperModel:
    global stt_model

    if stt_model is None:
        settings = get_settings()
        stt_model = WhisperModel(
            settings.stt_model,
            device="cpu",
            compute_type=settings.stt_compute_type,
        )

    return stt_model


def record_audio(duration_seconds: float | None = None) -> str:
    settings = get_settings()
    sampleRate = int(settings.stt_sample_rate)
    effectiveDuration = (
        float(duration_seconds) if duration_seconds is not None else settings.stt_record_seconds
    )

    if effectiveDuration <= 0:
        raise ValueError("Recording süresi hatasi")

    sd.default.samplerate = sampleRate
    sd.default.channels = 1

    frames = int(effectiveDuration * sampleRate)
    audio = sd.rec(frames, dtype="int16", channels=1)
    sd.wait()

    fd, temp_path = tempfile.mkstemp(prefix="stt_", suffix=".wav")
    os.close(fd)

    with wave.open(temp_path, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2) 
        wav_file.setframerate(sampleRate)
        wav_file.writeframes(audio.tobytes())

    return temp_path
 
 
def transcribe_audio(audio_path: str) -> str:
     if not audio_path:
         raise ValueError("audio_path boş olamaz.")
 
     path = Path(audio_path)

     if not path.is_file():
         raise FileNotFoundError(f"Ses dosyası bulunamadı {audio_path} hatasi")
 
     settings = get_settings()
     model = get_stt_model()
 
     segments, _ = model.transcribe(
         str(path),
         language=settings.stt_language,
         beam_size=int(settings.stt_beam_size),
     )
 
     transcriptParts = [segment.text for segment in segments]
     transcript = "".join(transcriptParts).strip()
 
     return transcript
 
