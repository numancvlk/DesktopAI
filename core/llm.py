#LIBRARIES
import json
import requests
from typing import Any, Dict, List
from .config import get_settings

def build_system_prompt() -> str:
    return """Sen masaüstü asistanısın. Yanıtın SADECE tek JSON nesnesi olsun, başka metin yazma.

    Format: {"intent": "...", "command": "...", "parameters": {}, "response": "..."}

    ZORUNLU KURAL - Aç komutu: Kullanıcı mesajında "ac", "aç", "open", "açı" veya açmak anlamı varsa MUTLAKA command: "open_app" ver, app_name olarak uygulama adını yaz. ASLA "ne yapmamı istiyorsun?" diye sorma.
    - hesap makinesi ac -> command: "open_app", parameters: {"app_name": "hesap makinesi"}, response: "Hesap makinesini açıyorum."

    Sadece eksik eylem: Kullanıcı SADECE uygulama adı yazdı, "ac/aç/open" YOK (örn. sadece "hesap makinesi") -> command: "none", parameters: {}, response: "[Uygulama] ile ne yapmamı istiyorsun? Açmamı mı?"

    response: Her zaman tek cümle Türkçe, düz metin (markdown/emoji yok)."""


def build_messages(history: List[dict], user_input: str) -> List[Dict[str, str]]: #Eski mesajlarla yeni mesajlari birleştirir
    messages: List[Dict[str, str]] = [
        {"role": "system", "content": build_system_prompt()}
    ]
    for item in history:
        role = item.get("role", "user")
        content = item.get("content", "")
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": user_input.strip()})
    return messages


def call(history: List[dict], user_input: str) -> str:  # Json yanitini döner
    settings = get_settings()
    baseUrl = settings.baseUrl.rstrip("/")
    model = settings.llmModel
    timeout = settings.timeout

    url = f"{baseUrl}/api/chat"
    payload = {
        "model": model,
        "messages": build_messages(history, user_input),
        "stream": False,
        "format": "json",
    }
    try:
        response = requests.post(url, json=payload, timeout=timeout)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException:
        raise RuntimeError("Baglanti hatasi")
    except (ValueError, TypeError, KeyError):
        raise RuntimeError("LLM yaniti gecersiz")

    if not isinstance(data, dict):
        raise RuntimeError("LLM yaniti gecersiz")

    message = data.get("message")
    if not isinstance(message, dict):
        raise RuntimeError("LLM mesaji yok")
    content = message.get("content")
    if content is None:
        content = ""
    return content.strip() if isinstance(content, str) else ""
