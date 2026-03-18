#LIBRARIES
import json
import requests
from typing import Any, Dict, List
from .config import get_settings


def build_system_prompt() -> str:
    return """Sen masaüstü asistanısın. Yanıtın SADECE tek JSON nesnesi olsun, başka metin yazma.
        DÜŞÜNME YAPMA. Açıklama, <think>, reasoning veya ek metin YAZMA. İlk çıktın doğrudan JSON olsun.

        Format: {"intent": "...", "command": "...", "parameters": {}, "response": "..."}

        Sana SADECE hatırlatıcı kurma, selam/soru veya belirsiz mesajlar gelir. Uygulama açma, ekran görüntüsü, mod aktive etme, masaüstü düzenleme yerel işlenir.

        HATIRLATICI (set_reminder): Kullanıcı gelecekte bir şeyi hatırlatmanı isterse (örn. "yarın 9'da toplantı hatırlat", "20 dk sonra su iç hatırlat") command: "set_reminder" kullan.
        - parameters: "text" (ne hatırlatılacak), "time" (boş veya zaman ifadesi), "repeat" (daily/weekly veya null)
        - response: Tek cümle Türkçe (örn. "Yarın saat 9'da toplantını hatırlatacağım.")

        SOHBET/BELİRSİZ: Selam, teşekkür, "ne yapabilirsin?", genel soru -> command: "none", parameters: {}, response: Doğal, yardımcı Türkçe cevap.

        ÖRNEKLER:
        - "Her gün 22:00'de su iç hatırlat" -> {"intent": "set_reminder", "command": "set_reminder", "parameters": {"text": "su iç", "time": "her gün 22:00", "repeat": "daily"}, "response": "Her gün saat 22:00'de su içmeni hatırlatacağım."}
        - "Merhaba" -> {"intent": "greeting", "command": "none", "parameters": {}, "response": "Merhaba! Size nasıl yardımcı olabilirim?"}
        - "Ne yapabilirsin?" -> {"intent": "capabilities", "command": "none", "parameters": {}, "response": "Uygulama açabilir, ekran görüntüsü alabilir, hatırlatıcı kurabilir, masaüstünü düzenleyebilir ve modları çalıştırabilirim. Ne yapmamı istersiniz?"}

        response: Her zaman tek cümle Türkçe, düz metin (markdown/emoji yok)."""


def build_rag_system_prompt() -> str:
    return """PDF asistan. Sadece --- arasındaki kaynağa göre cevap. Kaynakta varsa kopyala, yoksa "Bu PDF'te bu bilgi yer almıyor." Kısa Türkçe, İngilizce/markdown yok. Doğrudan cevap."""


def build_messages(history: List[dict], user_input: str) -> List[Dict[str, str]]:
    system_content = build_system_prompt()
    messages: List[Dict[str, str]] = [
        {"role": "system", "content": system_content}
    ]
    for item in history:
        role = item.get("role", "user")
        content = item.get("content", "")
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": user_input.strip()})
    return messages


def call(history: List[dict], user_input: str) -> str:  # Bızım JSONU DONUYOR
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
    except requests.RequestException as e:
        raise RuntimeError(f"Ollama baglanti hatasi")
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


def build_rag_messages(history: List[dict], user_input: str) -> List[Dict[str, str]]: #RAG ICIN DONECEGI MESAJLAR
    messages: List[Dict[str, str]] = [
        {"role": "system", "content": build_rag_system_prompt()}
    ]
    messages.append({"role": "user", "content": user_input.strip()})
    return messages


def call_rag(history: List[dict], user_input: str) -> str:
    settings = get_settings()
    baseUrl = settings.baseUrl.rstrip("/")
    model = settings.llmModel
    timeout = settings.timeout

    url = f"{baseUrl}/api/chat"
    payload = {
        "model": model,
        "messages": build_rag_messages(history, user_input),
        "stream": False,
    }
    try:
        response = requests.post(url, json=payload, timeout=timeout)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        raise RuntimeError(f"Ollama baglanti hatasi")
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
