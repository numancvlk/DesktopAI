#LIBRARIES
import json
import requests
from typing import Any, Dict, List
from .config import get_settings

def build_system_prompt() -> str: #LLM PROMPT
    return """Sen masaüstü asistanısın. Yanıtını MUTLAKA yalnızca aşağıdaki JSON formatında ver. Başka metin, açıklama veya markdown yazma.

            Format (İngilizce anahtarlar):
            {"intent": "...", "command": "...", "parameters": {}, "response": "..."}

            Kurallar:
            - intent: Kullanıcı niyetini kısa özetle (Türkçe veya İngilizce).
            - command: Sadece "none" veya "open_app" kullan.
            - parameters: open_app ise {"app_name": "uygulama adı"} şeklinde; değilse {}.
            - response: Kullanıcıya gösterilecek tek cümlelik Türkçe yanıt. Sadece düz metin: markdown, **kalın**, # başlık, emoji veya []() kullanma. Ses çıktısına uygun olsun.

            ÖNEMLİ - Eksik eylem kuralı: Kullanıcı sadece bir isim yazdıysa (örn. "hesap makinesi") ve ne yapılacağını söylemediyse:
            - command: "none"
            - parameters: {}
            - response: İsmi kullanarak sor: "hesap makinesi ile ne yapmamı istiyorsun? Açmamı mı?" gibi. Kendin eylem başlatma."""


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


def call(history: List[dict], user_input: str) -> str: ? #Json yanitini döner
    settings = get_settings()
    baseUrl = settings.baseUrl.rstrip("/")
    model = settings.llmModel
    timeout = settings.timeout

    url = f"{baseUrl}/api/chat"
    payload = {
        "model": model,
        "messages": build_messages(history, user_input),
        "stream": False,
    }
    try:
        response = requests.post(url, json=payload, timeout=timeout)
        response.raise_for_status()
        data: Dict[str, Any] = response.json()
    except:
        raise RuntimeError("Baglanti hatasi")
    except:
        raise RuntimeError("LLM yaniti gecersiz")

    message = data.get("message")
    if not isinstance(message, dict):
        raise RuntimeError("LLM mesaji yok")
    content = message.get("content")
    if content is None:
        content = ""
    return content.strip() if isinstance(content, str) else ""
