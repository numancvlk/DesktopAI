#LIBRARIES
import json
import requests
from typing import Any, Dict, List
from .config import get_settings
from . import user_modes


def build_system_prompt() -> str:
    return """Sen masaüstü asistanısın. Yanıtın SADECE tek JSON nesnesi olsun, başka metin yazma.
        DÜŞÜNME YAPMA. Açıklama, <think>, reasoning veya ek metin YAZMA. İlk çıktın doğrudan JSON olsun.

        Format: {"intent": "...", "command": "...", "parameters": {}, "response": "..."}

        ZORUNLU KURAL - MOD vs UYGULAMA AYIRIMI: "X modu" veya "X" (X kullanıcının tanımladığı modlardan biri ise) ASLA open_app değil, activate_mode kullan. Mod isimleri aşağıda belirtilir.
        ZORUNLU KURAL - Aç komutu (sadece uygulama için): Kullanıcı mesajında "ac", "aç", "open" varsa VE bir MOD değilse (notepad, chrome, hesap makinesi gibi uygulama) MUTLAKA command: "open_app" ver.
        TAKİP KURALI: Kullanıcı SADECE "aç"/"ac"/"open" yazdıysa, ÖNCEKİ mesajlardaki uygulama adını kullan.
        - "hesap makinesi ac" -> open_app (uygulama)
        - "oyun modu" veya "oyun modunu aç" -> activate_mode (mod, open_app DEĞİL)

        ZORUNLU KURAL - Ekran görüntüsü (ÖNCELİKLİ): "screenshot", "ekran goruntusu", "ekran al" vb. ASLA uygulama değildir. command: "screenshot".

        Sadece eksik eylem (uygulama için): Kullanıcı SADECE uygulama adı yazdı ("modu" YOK, örn. "hesap makinesi") -> command: "none", response: "[Uygulama] ile ne yapmamı istiyorsun? Açmamı mı?"

        HATIRLATICI KURALLARI (set_reminder):
        - Kullanıcı gelecekte bir zamanda bir olayı hatırlatmanı isterse (örn. "yarın saat 9'da toplantı hatırlat", "20 dakika sonra ders çalışmayı hatırlat"), MUTLAKA command: "set_reminder" kullan.
        - parameters alanında en az şu alanları doldur:
            - "text": Hatırlatılacak kısa açıklama (örn. "toplantı", "ders çalış").
            - "time": İstersen boş bırakabilir veya sadece kullanıcının söylediği zaman ifadesini tekrar edebilirsin; kesin ISO tarih-zaman hesabını sistem kendisi yapacaktır.
            - "repeat": Eğer tekrar eden bir hatırlatıcıysa (ör. "her gün", "her hafta"), sade bir İngilizce/Türkçe kural yazabilirsin (örn. "daily", "weekly"). Değilse null bırak.
        - response alanı TEK cümle, düz Türkçe açıklama olsun (örn. "Yarın saat 9'da toplantını hatırlatacağım.").

        MASAÜSTÜ DÜZENLEME KURALLARI (organize_desktop):
        - Kullanıcı masaüstünü düzenlemek, toplamak, dosyaları türlerine göre klasörlemek isterse (örn. "masaüstümü toparla", "desktop çok dağınık, klasörlere ayır", "masaüstündeki dosyaları türlerine göre düzenle"), MUTLAKA command: "organize_desktop" kullan.
        - Bu komut masaüstündeki dosyaları tamamen yerel olarak türüne göre klasörlere taşır; parameters alanı genellikle boş {} kalabilir.
        - parameters alanı:
            - İlk sürümde boş sözlük {} bırak. Özel bir parametre kullanma.
        - response alanı TEK cümle, düz Türkçe açıklama olsun (örn. "Masaüstündeki dosyalarını türlerine göre klasörlere ayırıp düzenliyorum.").

        ÖRNEKLER:
        - "Her gün saat 22:00'de su içmeyi hatırlat"
          -> {"intent": "set_reminder", "command": "set_reminder", "parameters": {"text": "su iç", "time": "her gün 22:00", "repeat": "daily"}, "response": "Her gün saat 22:00'de su içmeni hatırlatacağım."}
        - "Masaüstümü toparlar mısın, dosyaları türlerine göre klasörlere ayır"
          -> {"intent": "organize_desktop", "command": "organize_desktop", "parameters": {}, "response": "Masaüstündeki dosyalarını türlerine göre klasörlere ayırıp düzenliyorum."}

        response: Her zaman tek cümle Türkçe, düz metin (markdown/emoji yok)."""


def build_user_modes() -> str:
    mods = user_modes.get_modes()

    if not mods:
        return ""

    names = [m.get("name", "").strip() for m in mods if m.get("name")]

    if not names:
        return ""

    names = ", ".join(f'"{n}"' for n in names)

    return f"""
        KULLANICI MODLARI (activate_mode) - ÖNCELİKLİ, open_app ile KARIŞTIRMA:
        Kullanıcının tanımlı modları: {names}. Bunlar UYGULAMA DEĞİL, MOD dur. "X modu" veya "X" (X bu listede varsa) ASLA open_app değil, MUTLAKA activate_mode ver.
        - "oyun modu", "oyun modunu aç", "çalışma modu", "çalışma modunu başlat" -> command: "activate_mode", parameters: {{"mode_name": "mod_adı"}}, response: "[Mod adı] modunu açıyorum."
        - Mod adı yukarıdaki listede TAM EŞLEŞME veya benzer olmalı. Mod İSTEMİYORSA (sadece uygulama: notepad, chrome vb.) open_app kullan.
        AYIRIM: "hesap makinesi aç" = open_app (uygulama). "oyun modu" veya "çalışma modunu aç" = activate_mode (mod).
        """


def build_rag_system_prompt() -> str:
    return """PDF asistan. Sadece --- arasındaki kaynağa göre cevap. Kaynakta varsa kopyala, yoksa "Bu PDF'te bu bilgi yer almıyor." Kısa Türkçe, İngilizce/markdown yok. Doğrudan cevap."""


def build_messages(history: List[dict], user_input: str) -> List[Dict[str, str]]:  # TODO Burda history ekledik ama daha kullanmadik  tam oalrak halledilcek ama sonra
    systemCon = build_system_prompt()
    modesRule = build_user_modes()
    if modesRule:
        systemCon = systemCon.rstrip() + modesRule
    messages: List[Dict[str, str]] = [
        {"role": "system", "content": systemCon}
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
