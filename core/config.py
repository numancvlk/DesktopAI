# LIBRARIES * CONFIG BURDAN GELIR BIZI MDEGERLER
import os
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, ValidationError

class Settings(BaseModel):
    base_url: str
    ai_model: str
    timeout: float
    default_timeout: float
    memory_db_path: str
    screenshot_save_dir: str
    stt_model: str
    stt_language: str
    stt_beam_size: int
    stt_compute_type: str
    stt_sample_rate: int
    stt_record_seconds: float
    rag_enabled: bool
    rag_pdf_dir: str
    rag_embedding_model: str
    rag_top_k: int

    @property
    def baseUrl(self) -> str:
        return self.base_url

    @property
    def llmModel(self) -> str:
        return self.ai_model

    @classmethod
    def from_env(cls) -> "Settings":
        baseUrl = os.getenv("BASE_URL")
        llmModel = os.getenv("LLM_MODEL")
        timeout = os.getenv("TIMEOUT")
        defaultTimeout = os.getenv("DEFAULT_TIMEOUT")
        memoryDbPath = os.getenv("MEMORY_DB_PATH")
        screenshotSaveDir = os.getenv("SCREENSHOT_SAVE_DIR")
        sttModel = os.getenv("STT_MODEL")
        sttLanguage = os.getenv("STT_LANGUAGE")
        sttBeamSize = os.getenv("STT_BEAM_SIZE")
        sttComputeType = os.getenv("STT_COMPUTE_TYPE")
        sttSampleRate = os.getenv("STT_SAMPLE_RATE")
        sttRecordSeconds = os.getenv("STT_RECORD_SECONDS")
        ragEnabledRaw = os.getenv("RAG_ENABLED")
        ragPdfDir = os.getenv("RAG_PDF_DIR")
        ragEmbeddingModel = os.getenv("RAG_EMBEDDING_MODEL")
        ragTopK = os.getenv("RAG_TOP_K")

        if not memoryDbPath or not memoryDbPath.strip():
            raise RuntimeError("MEMORY_DB_PATH eksik veya boş")
        else:
            memoryDbPath = memoryDbPath.strip()

        if baseUrl is None or not baseUrl.strip():
            raise RuntimeError("BASE_URL eksik veya boş")

        if llmModel is None or not llmModel.strip():
            raise RuntimeError("AI_MODEL eksik veya boş")

        if not screenshotSaveDir or not screenshotSaveDir.strip():
            raise RuntimeError("SCREENSHOT_SAVE_DIR eksik veya boş")
        screenshotSaveDir = screenshotSaveDir.strip()

        try:
            timeout = float(timeout) if timeout is not None else 0.0
        except:
            raise RuntimeError("TIMEOUT eksik veya boş")

        try:
            defaultTimeout = (
                float(defaultTimeout) if defaultTimeout is not None else 0.0
            )
        except:
            raise RuntimeError(
                "DEFAULT_TIMEOUT eksik veya boş"
            )

        try:
            sttBeamSizeInt = int(sttBeamSize)
        except Exception:
            raise RuntimeError("STT_BEAM_SIZE geçerli bir tam sayı olmalıdır")

        try:
            sttSampleRateInt = int(sttSampleRate)
        except Exception:
            raise RuntimeError(
                "STT_SAMPLE_RATE geçerli bir tam sayı olmalıdır"
            )

        try:
            ragTopKInt = int(ragTopK)
        except Exception:
            raise RuntimeError("RAG_TOP_K geçerli bir tam sayı olmalıdır")

        ragEnabled = str(ragEnabledRaw).strip().lower() in (
            "1",
            "true",
            "yes",
            "on",
        )

        try:
            return cls(
                base_url=baseUrl.strip(),
                ai_model=llmModel.strip(),
                timeout=timeout,
                default_timeout=defaultTimeout,
                memory_db_path=memoryDbPath,
                screenshot_save_dir=screenshotSaveDir,
                stt_model=sttModel.strip(),
                stt_language=sttLanguage.strip(),
                stt_beam_size=sttBeamSizeInt,
                stt_compute_type=sttComputeType.strip(),
                stt_sample_rate=sttSampleRateInt,
                stt_record_seconds=float(sttRecordSeconds) if sttRecordSeconds is not None else 0.0,
                rag_enabled=ragEnabled,
                rag_pdf_dir=ragPdfDir.strip(),
                rag_embedding_model=ragEmbeddingModel.strip(),
                rag_top_k=ragTopKInt,
            )
        except Exception:
            raise RuntimeError("Geçersiz env değerleri")

cachedSettings: Optional[Settings] = None

def get_settings() -> Settings:
    global cachedSettings
    if cachedSettings is None:
        cachedSettings = Settings.from_env()
    return cachedSettings

