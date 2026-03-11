#LIBRARIES
import json
import requests
from typing import Any, Dict, List
from .config import get_settings


def build_system_prompt() -> str:
    return """Sen masaüstü asistanısın. Yanıtın SADECE tek JSON nesnesi olsun, başka metin yazma.

        Format: {"intent": "...", "command": "...", "parameters": {}, "response": "..."}

        ZORUNLU KURAL - Aç komutu: Kullanıcı mesajında "ac", "aç", "open", "açı" veya açmak anlamı varsa MUTLAKA command: "open_app" ver, app_name olarak uygulama adını yaz. ASLA "ne yapmamı istiyorsun?" diye sorma.
        - "hesap makinesi ac" -> {"intent": "open_app", "command": "open_app", "parameters": {"app_name": "hesap makinesi"}, "response": "Hesap makinesini açıyorum."}

        ZORUNLU KURAL - Ekran görüntüsü (ÖNCELİKLİ): "screenshot", "screencapture", "screen capture", "ekran goruntusu", "ekran görüntüsü", "ekrani kaydet", "ekranı kaydet", "ekran al", "ekran goster" gibi ifadeler ASLA uygulama adı değildir. Bu durumda MUTLAKA command: "screenshot", parameters: {}, response: "Ekran görüntüsünü alıp masaüstüne kaydettim." ver. Bu isteklerde ASLA "ne yapmamı istiyorsun?" veya "Açmamı mı?" deme.

        Sadece eksik eylem: Kullanıcı SADECE bir uygulama adı yazdı (yukarıdaki ekran görüntüsü ifadeleri HARİÇ), "ac/aç/open" YOK (örn. sadece "hesap makinesi") -> command: "none", parameters: {}, response: "[Uygulama] ile ne yapmamı istiyorsun? Açmamı mı?"

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
        - "Yarın saat 9'da toplantı hatırlat"
          -> {"intent": "set_reminder", "command": "set_reminder", "parameters": {"text": "toplantı", "time": "yarın saat 9'da", "repeat": null}, "response": "Yarın saat 9'da toplantını hatırlatacağım."}
        - "20 dakika sonra ders çalışmayı hatırlat"
          -> {"intent": "set_reminder", "command": "set_reminder", "parameters": {"text": "ders çalış", "time": "20 dakika sonra", "repeat": null}, "response": "20 dakika sonra ders çalışmanı hatırlatacağım."}
        - "Her gün saat 22:00'de su içmeyi hatırlat"
          -> {"intent": "set_reminder", "command": "set_reminder", "parameters": {"text": "su iç", "time": "her gün 22:00", "repeat": "daily"}, "response": "Her gün saat 22:00'de su içmeni hatırlatacağım."}
        - "Masaüstümü toparlar mısın, dosyaları türlerine göre klasörlere ayır"
          -> {"intent": "organize_desktop", "command": "organize_desktop", "parameters": {}, "response": "Masaüstündeki dosyalarını türlerine göre klasörlere ayırıp düzenliyorum."}

        response: Her zaman tek cümle Türkçe, düz metin (markdown/emoji yok)."""


def build_rag_system_prompt() -> str:
    return """Sen PDF dokümanları üzerinde çalışan bir soru-cevap asistanısın.

    Sana kullanıcının sorusuna ek olarak PDF'lerden alınmış bağlam parçaları verilecektir.

    Genel kurallar:
    - YANITIN SADECE düz Türkçe metin olsun, JSON veya başka bir format kullanma.
    - Cevabını YALNIZCA verilen bağlamdaki bilgilere dayanarak ver; dış dünyadan ek bilgi kullanma.
    - Eğer bağlam içinde sorunun cevabı AÇIKÇA geçiyorsa, o bilgiyi olduğu gibi kullanarak NET ve KESİN cevap ver.
    - Eğer bağlamda sorunun cevabı YOKSA, "Bu PDF'te bu bilgi yer almıyor." de ve ASLA tahmin yapma.
    - "internete bak", "değişebilir", "tam sayı bilinmiyor" gibi ifadeler KULLANMA.
    - Soruyu sadece tekrar eden, genel ve muğlak cümleler KULLANMA; her zaman mümkün olan en SOMUT ve PDF'ten okunabilir bilgiyi ver.
    - Masaüstü komutları, uygulama açma, ekran görüntüsü vb. ile ilgili hiçbir komut üretme; sadece bilgi amaçlı yanıt ver.

    Özel olarak zaman çizelgesi / tablo soruları (ör. ders programı) için:
    - Kullanıcının sorusunda GEÇEN günü (örn. Pazartesi, Salı, Çarşamba...) DİKKATLE oku.
    - Cevabında HER ZAMAN sorulan günle AYNI günü kullan; farklı bir gün ismi söyleme veya uydurma.
    - Bağlamdaki tabloda o güne karşılık gelen TÜM ders/satır değerlerini tek tek sırala.
    - Örneğin tabloda "Pazartesi" sütununda Matematik, Matematik, Türk Dili ve Edebiyatı, İngilizce, İngilizce yazıyorsa
    ve soru "Pazartesi derslerim neler?" ise cevabın "Pazartesi: Matematik, Matematik, Türk Dili ve Edebiyatı, İngilizce, İngilizce." gibi olsun.
    - Eğer tabloda sorulan gün (örneğin "Salı") hiç geçmiyorsa, açıkça "Bu PDF'te Salı günü ile ilgili bilgi yer almıyor." de.

    Cevapların 1-2 cümle, açık ve sade Türkçe olsun."""


def build_messages(history: List[dict], user_input: str) -> List[Dict[str, str]]:  # TODO Burda history ekledik ama daha kullanmadik  tam oalrak halledilcek ama sonra
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
