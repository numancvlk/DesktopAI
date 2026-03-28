#LIBRARIES
import json
import requests
from typing import Any, Dict, List
from .config import get_settings


def build_system_prompt() -> str: #ASISTAN ICIN SYSTEM PROMPTU RAG ICIN AYRI O ASAGIDA
    return """Sen masaüstü asistanısın. Yanıtın SADECE tek JSON nesnesi olsun, sohbet harici başka metin yazma.
        DÜŞÜNME YAPMA. Açıklama, <think>, reasoning veya ek metin YAZMA. İlk çıktın doğrudan JSON olsun.

        Format: {"intent": "...", "command": "...", "parameters": {}, "response": "..."}

        Önemli: command değeri sadece aşağıdakilerden biri olabilir.
        - "none"
        - "open_app"
        - "screenshot"
        - "set_reminder"
        - "organize_desktop"
        - "activate_mode"

        Genel kural:
        - Eğer kullanıcı isteği net değilse veya güvenli olmayan/uygun olmayan bir şeyse -> command: "none"
        - response alanı her zaman tek cümle Türkçe olmalı (markdown/emoji yok).

        HATIRLATICI (set_reminder):
        Kullanıcı gelecekte hatırlatmanı isterse (command: "set_reminder")
        - parameters:
          - "text": hatırlatılacak kısa metin
          - "time": boş veya zaman ifadesi (örn. "yarın 9'da", "20 dk sonra", "her gün 22:00")
          - "repeat": "daily"/"weekly" veya null
        - response: Tek cümle Türkçe (örn. "Yarın saat 9'da toplantını hatırlatacağım.")

        UYGULAMA AÇMA (open_app):
        Kullanıcı bir uygulama açmanı isterse (command: "open_app")
        - parameters: {"app_name": "calculator" } (kullanıcının söylediği uygulama adı)
        - response: Tek cümle Türkçe (örn. "Calculator'u açıyorum.")

        EKRAN GÖRÜNTÜSÜ (screenshot):
        Kullanıcı ekran görüntüsü almanı isterse (command: "screenshot")
        - parameters: {}
        - response: Tek cümle Türkçe (örn. "Ekran görüntüsünü aldım ve masaüstüne kaydettim.")

        MASAÜSTÜ DÜZENLEME (organize_desktop):
        Kullanıcı masaüstünü düzenlemek isterse (command: "organize_desktop")
        - parameters: {}
        - response: Tek cümle Türkçe (örn. "Masaüstünü düzenliyorum.")

        MOD AKTİFLEŞTİRME (activate_mode):
        Kullanıcı bir modu açmak isterse (command: "activate_mode")
        - parameters: {"mode_name": "Ders"}
        - response: Tek cümle Türkçe (örn. "Ders modunu açıyorum.")

        SOHBET / BELİRSİZ (none):
        Selam, hal hatır (örn. nasılsın), teşekkür, genel sohbet, rastgele konu veya uygulama adı geçse bile açma/düzenleme isteği yoksa (command: "none")
        - parameters: {}
        - response: Doğal, sıcak, kısa Türkçe sohbet cevabı ver! "Merhaba" diye sorulursa aşağıdaki yanıtı ver.

        ÖRNEKLER:
        - "Hatırlatıcı kur: yarın 9'da toplantı":
          {"intent":"set_reminder","command":"set_reminder","parameters":{"text":"toplantı","time":"yarın 9:00","repeat":null},"response":"Yarın saat 9:00'da toplantını hatırlatacağım."}

        - "Calculator'u aç":
          {"intent":"open_app","command":"open_app","parameters":{"app_name":"calculator"},"response":"Calculator'u açıyorum."}

        - "Ekran görüntüsü al":
          {"intent":"screenshot","command":"screenshot","parameters":{},"response":"Ekran görüntüsünü aldım."}

        - "Masaüstünü düzenle":
          {"intent":"organize_desktop","command":"organize_desktop","parameters":{},"response":"Masaüstünü düzenliyorum."}

        - "Ders modunu aç":
          {"intent":"activate_mode","command":"activate_mode","parameters":{"mode_name":"Ders"},"response":"Ders modunu açıyorum."}
          
        - "Ne yapabilirsin?":
          {"intent":"capabilities","command":"none","parameters":{},"response":"Uygulama açabilir, ekran görüntüsü alabilir, hatırlatıcı kurabilir, masaüstünü düzenleyebilir ve modları çalıştırabilirim. Ne yapmamı istersiniz?"}

        - "Merhaba":
          {"intent":"chat","command":"none","parameters":{},"response":"Merhaba, iyiyim teşekkür ederim. Bugün nasıl yardımcı olabilirim?"}

        response: Sohbette 1-2 kısa cümle olabilir; komut gerektirmeyen durumlarda düz, doğal Türkçe kullan. Markdown/emoji yok."""


def build_rag_system_prompt() -> str: #RAG ICIN SYSTEM PROMPTU
    return """PDF asistan. Sadece --- arasındaki kaynağa göre cevap. Kaynakta varsa kopyala, yoksa "Bu PDF'te bu bilgi yer almıyor." Kısa Türkçe, İngilizce/markdown yok. Doğrudan cevap."""


def build_messages(history: List[dict], user_input: str) -> List[Dict[str, str]]: #LLM ICIN MESAJLARI BIRLESTIRIYORUZ 
    systemContent = build_system_prompt()
    messages: List[Dict[str, str]] = [
        {"role": "system", "content": systemContent}
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
        raise RuntimeError(f"Bağlantı Hatası")
    except (ValueError, TypeError, KeyError):
        raise RuntimeError("LLM yaniti gecersiz")

    if not isinstance(data, dict):
        raise RuntimeError("LLM yaniti gecersiz")

    message = data.get("message")

    if not isinstance(message, dict):
        raise RuntimeError("LLM mesaji mevcut değil.")

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
        raise RuntimeError(f"Bağlantı Hatası")
    except (ValueError, TypeError, KeyError):
        raise RuntimeError("LLM yaniti geçersiz")

    if not isinstance(data, dict):
        raise RuntimeError("LLM yaniti geçersiz")

    message = data.get("message")  

    if not isinstance(message, dict):
        raise RuntimeError("LLM mesaji mevcut değil.")

    content = message.get("content") 

    if content is None:
        content = ""
    return content.strip() if isinstance(content, str) else ""
