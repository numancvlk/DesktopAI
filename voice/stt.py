#LIBRARIES
import os
import tempfile
import wave
import numpy as np
import sounddevice as sd
import threading

from pathlib import Path
from typing import Optional
from faster_whisper import WhisperModel
from core.config import get_settings
from core.local_intents import normalize_mic

stt_model: Optional[WhisperModel] = None
stt_load = threading.Lock()

def get_stt_model() -> WhisperModel:
    global stt_model

    if stt_model is None:
        with stt_load:
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

    blockDurationSec = 0.2
    blockFrames = max(1, int(blockDurationSec * sampleRate))
    maxFrames = int(effectiveDuration * sampleRate)
    minListenSec = min(1.0, effectiveDuration)
    silenceStopSec = 0.7
    speechThreshold = 350.0

    capturedFrames = 0
    silentAfterSpeechFrames = 0
    speechStarted = False
    chunks: list[np.ndarray] = []

    with sd.InputStream(samplerate=sampleRate, channels=1, dtype="int16") as stream:
        while capturedFrames < maxFrames:
            chunk, overflowed = stream.read(blockFrames)
            if overflowed:
                continue

            chunks.append(chunk.copy())
            currentFrames = int(chunk.shape[0])
            capturedFrames += currentFrames

            level = float(np.abs(chunk).mean())
            if level >= speechThreshold:
                speechStarted = True
                silentAfterSpeechFrames = 0
            elif speechStarted:
                silentAfterSpeechFrames += currentFrames

            elapsedSec = capturedFrames / sampleRate
            if (
                speechStarted
                and elapsedSec >= minListenSec
                and (silentAfterSpeechFrames / sampleRate) >= silenceStopSec
            ):
                break

    if chunks:
        audio = np.concatenate(chunks, axis=0).astype("int16")
    else:
        audio = np.zeros((1, 1), dtype="int16")

    fd, tempPath = tempfile.mkstemp(prefix="stt_", suffix=".wav")
    os.close(fd)

    with wave.open(tempPath, "wb") as wavFile:
        wavFile.setnchannels(1)
        wavFile.setsampwidth(2) 
        wavFile.setframerate(sampleRate)
        wavFile.writeframes(audio.tobytes())

    return tempPath
 
 
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
        vad_filter=False,
        initial_prompt=(
            "Komutları Türkçe algıla. "
            "kelimelerini doğru yaz."
        ),
    )

    transcriptParts = [segment.text for segment in segments]
    transcript = " ".join(transcriptParts).strip()
    correctedTranscript = normalize_mic(transcript)
    return correctedTranscript
 
