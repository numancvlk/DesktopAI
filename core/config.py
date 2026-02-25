# LIBRARIES
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

        if not memoryDbPath or not memoryDbPath.strip():
            raise RuntimeError("MEMORY_DB_PATH eksik veya boş")
        else:
            memoryDbPath = memoryDbPath.strip()

        if baseUrl is None or not baseUrl.strip():
            raise RuntimeError("BASE_URL eksik veya boş")

        if llmModel is None or not llmModel.strip():
            raise RuntimeError("AI_MODEL eksik veya boş")

        try:
            timeout = float(timeout) if timeout is not None else 0.0
        except ValueError as exc:
            raise RuntimeError("TIMEOUT eksik veya boş") from exc

        try:
            defaultTimeout = (
                float(defaultTimeout) if defaultTimeout is not None else 0.0
            )
        except ValueError as exc:
            raise RuntimeError(
                "DEFAULT_TIMEOUT eksik veya boş"
            ) from exc

        try:
            return cls(
                base_url=baseUrl.strip(),
                ai_model=llmModel.strip(),
                timeout=timeout,
                default_timeout=defaultTimeout,
                memory_db_path=memoryDbPath,
            )
        except ValidationError as exc:
            raise RuntimeError("Geçersiz env değerleri") from exc

cachedSettings: Optional[Settings] = None

def get_settings() -> Settings:
    global cachedSettings
    if cachedSettings is None:
        cachedSettings = Settings.from_env()
    return cachedSettings

