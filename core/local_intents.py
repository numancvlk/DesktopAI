# LIBRARIES
import re
import unicodedata
from difflib import get_close_matches
from typing import Any, Dict, Optional
from .action import safe_app_name
from . import user_modes

# Ekran görüntüsü almak için keywordler
SCREENSHOT_PATTERNS = (
    "ekran goruntusu",
    "screenshot",
    "screen shot",
    "screen capture",
    "screencapture",
    "print screen",
    "prtsc",
    "ss",
)

# Erkan goruntusu almak ıcın aksıyon keyworrdlerı
SCREENSHOT_ACTION_WORDS = (
    "al",
    "cek",
    "kaydet",
    "capture",
    "shot",
)

SCREENSHOT_META_WORDS = (
    "dedim",
    "demistim",
    "diyorum",
    "demek",
    "neden",
    "niye",
    "nasil",
    "oldu",
    "olmus",
)

# open_app komutu icin aksiyon keywordleri
OPEN_APP_KEYWORDS = (
    "ac",
    "open",
    "baslat",
    "calistir",
    "aciver",
    "acsana",
)

# Kullanici ne yaptigini merak ederse sorabilecegi sorular
CAPABILITIES_KEYWORDS = (
    "neler yapabiliyorsun",
    "neler yapabilirsin",
    "ozelliklerin neler",
    "özelliklerin neler",
    "hangi ozelliklerin var",
    "hangi özelliklerin var",
    "nasil ozelliklerin var",
    "nasil özelliklerin var",
    "ne yapabiliyorsun",
    "ne yapabilirsin",
)

#STT bazen yanlis yazabiliyor buraya duzeltmeler ekledik normalize yani
APP_ALIASES = {
    "whatsapp": "whatsapp",
    "watsap": "whatsapp",
    "watsup": "whatsapp",
    "vatsap": "whatsapp",
    "vatsup": "whatsapp",
    "whatsap": "whatsapp",
    "watsapp": "whatsapp",
    "watshapp": "whatsapp",
    "steam": "steam",
    "stim": "steam",
    "stimi": "steam",
    "siti": "steam",
    "sitiyi": "steam",
    "steami": "steam",
    "googlechrome": "chrome",
    "spotify": "spotify",
    "notepad": "notepad",
    "hesapmakinesi": "hesap makinesi",
    "calculator": "hesap makinesi",
}

# STT hatalari icin duzeltmeler #TODO usttekiyle alttaki niye ayri duzelt APP_ALLIES icine al
SPOKEN_WORD_REPLACEMENTS = {
    "siti": "steam",
    "sitiyi": "steam",
    "stimi": "steam",
    "steami": "steam",
    "watsap": "whatsapp",
    "watsup": "whatsapp",
    "vatsap": "whatsapp",
    "vatsup": "whatsapp",
}

# APP adlarini dogru tespit edebilmek ici nveya niyeti
FILLER_WORDS = {
    "lutfen",
    "please",
    "hadi",
    "bana",
    "uygulamasini",
    "uygulama",
    "programini",
    "program",
    "misin",
    "misin",
    "musun",
    "musun",
    "misiniz",
    "musunuz",
    "kocum",
    "kanka",
    "dostum",
}

#MASAUSTUNU DUZENLEMEK ICIN AKSIYON KW'leri
ORGANIZE_DESKTOP_KEYWORDS = (
    "toparla",
    "duzenle",
    "duzenleme",
    "duzenleyiver",
    "duzernle",
    "duzernleyiver",
    "masaustu",
    "masaüstü",
    "masaustumu",
    "masaüstümü",
    "masaustunu",
    "masaüstünü",
    "masautunu",
    "desktop",
    "klasor",
    "klasör",
    "dosyalari",
    "dosyaları",
    "türlerine",
    "turlerine",
    "gore",
    "göre",
)


# disardan gelen inputu temizliyor bu olmazsa bazen niyeti yanlsi tespit ediyor sart
def normalize_user_text(text: str) -> str:
    lowered = (text or "").strip().lower()

    lowered = (
        lowered.replace("ç", "c")
        .replace("ğ", "g")
        .replace("ı", "i")
        .replace("ö", "o")
        .replace("ş", "s")
        .replace("ü", "u")
    )

    normalized = unicodedata.normalize("NFKD", lowered)
    noAccent = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    noPunct = re.sub(r"[^a-z0-9\s]", " ", noAccent)
    return re.sub(r"\s+", " ", noPunct).strip()


# STT hatalarini burda duzeltiyorum
def normalize_mic(text: str) -> str:
    normalized = normalize_user_text(text)
    corrected = normalized

    for wrong, correct in SPOKEN_WORD_REPLACEMENTS.items():
        corrected = re.sub(rf"\b{re.escape(wrong)}\b", correct, corrected)
        
    return corrected


def compact_key(text: str) -> str:
    return re.sub(r"\s+", "", (text or "").strip().lower())


def strip_turkish_suffixes(token: str) -> str:
    if len(token) < 4:
        return token

    for suffix in ("yi", "yı", "yu", "yü", "i", "ı", "u", "ü"):
        if token.endswith(suffix) and len(token) > len(suffix) + 2:
            return token[: -len(suffix)]

    return token


#uygulama adini app_allies a gore cozer yoksa fuzzy mathing ile en yakini buluyoruz
def resolve_app(appName: str) -> str:
    compact = compact_key(appName)

    if not compact:
        return appName

    compactNoSuffix = strip_turkish_suffixes(compact)
    direct = APP_ALIASES.get(compact) or APP_ALIASES.get(compactNoSuffix)

    if direct:
        return direct

    candidates = list(APP_ALIASES.keys())
    nearest = get_close_matches(compactNoSuffix, candidates, n=1, cutoff=0.78)

    if nearest:
        return APP_ALIASES[nearest[0]]

    return appName

#Uygulama adini tam olarak tespit etmek icin 
def extract_open_app(normalized: str) -> str:
    if not normalized:
        return ""

    appName = normalized

    for keyword in OPEN_APP_KEYWORDS:
        appName = re.sub(rf"\b{keyword}\b", " ", appName)

    appName = re.sub(
        r"\b(acsana|acar misin|acar misiniz|acarmisin|acarmisiniz|aciver|aciverir misin|aciverir misiniz|acsana ya|acsana be)\b",
        " ",
        appName,
    )

    tokens = [
        token
        for token in appName.split()
        if token and token not in FILLER_WORDS and len(token) > 1
    ]

    cleanedTokens = [strip_turkish_suffixes(token) for token in tokens]
    return " ".join(cleanedTokens).strip()


# uygulama acma aksiyon kw leri vvar mi
def open_app_intent(normalized: str) -> bool:
    if not normalized:
        return False

    if any(f" {keyword} " in f" {normalized} " for keyword in OPEN_APP_KEYWORDS):
        return True

    return bool(
        re.search(
            r"\b(acsana|ac|acar misin|acarmisin|aciver|aciverir misin|calistir|baslat|open)\b",
            normalized,
        )
    )


#ekran goruntusu niyetini anlamak icin
def screenshot_intent(normalized: str) -> bool:
    if not normalized:
        return False

    if not any(pattern in normalized for pattern in SCREENSHOT_PATTERNS):
        return False

    if any(f" {word} " in f" {normalized} " for word in SCREENSHOT_META_WORDS):
        return False

    return any(f" {word} " in f" {normalized} " for word in SCREENSHOT_ACTION_WORDS)

#kullanicinin hangi modu acmak istedigini tesp't etmek icin bazende open_app ile karisabiliyor
def activate_mode(text: str) -> Optional[Dict[str, Any]]:
    if not text or not text.strip():
        return None

    try:
        mods = user_modes.modes()
    except RuntimeError:
        return None

    if not mods:
        return None

    normalized = normalize_user_text(text)
    openkeyword = ("ac", "aç", "açı", "open", "baslat", "calistir")

    for kw in openkeyword:
        if kw in normalized:
            candidate = re.sub(rf"\b{re.escape(kw)}\b", " ", normalized).strip()
            candidate = re.sub(r"\s+", " ", candidate)

            if candidate:
                mode = user_modes.mode_name(candidate)

                if mode:
                    return mode

    mode = user_modes.mode_name(text.strip())

    if mode:
        return mode

    for m in mods:
        name = (m.get("name") or "").strip().lower()
        nameNorm = normalize_user_text(name)

        if nameNorm and (nameNorm in normalized or normalized in nameNorm):
            return m

    return None


# masaustunu duzenlemek icin gerekn kw ler var mi diye bakar
def organize_desktop_intent(normalized: str) -> bool:
    if not normalized:
        return False

    return any(kw in normalized for kw in ORGANIZE_DESKTOP_KEYWORDS)

# capabilities listesine bakar ustteki
def capabilities(normalized: str) -> bool:
    if not normalized:
        return False

    return any(kw in normalized for kw in CAPABILITIES_KEYWORDS)



def detect_local_intent(text: str) -> Optional[Dict[str, Any]]: #BURDA ISE LLM'e gitmeden local intent tespit ediyoruz daha hizli bu sekilde 
    normalized = normalize_mic(text)  

    if capabilities(normalized): # Kullanmici neler yapabiliyorsuin diye sorarsa hazir cevap
        return {
            "command": "none",
            "parameters": {},
            "response": (
                "Aşağıdaki işlemleri yapabilirim:\n"
                "- Uygulama açma\n"
                "- Masaüstü düzenleme\n"
                "- RAG modu (PDF soru-cevap)\n"
                "- Mod oluşturma ve çalıştırma\n"
                "- Hatırlatıcı kurma\n"
                "- Sohbet etme\n"
                "- Ekran görüntüsü alma"
            ),
            "normalized": normalized,
        }

    if screenshot_intent(normalized):
        return {
            "command": "screenshot",
            "parameters": {},
            "response": "Ekran görüntüsünü alıp masaüstüne kaydettim.",
            "normalized": normalized,
        }

    modeMatch = activate_mode(text)

    if modeMatch is not None:
        mode_name = modeMatch.get("name", "").strip()

        if mode_name:
            return {
                "command": "activate_mode",
                "parameters": {"mode_name": mode_name},
                "response": f"{mode_name} modunu açıyorum.",
                "normalized": normalized,
            }

    if organize_desktop_intent(normalized):
        return {
            "command": "organize_desktop",
            "parameters": {},
            "response": "Masaüstündeki dosyalarını türlerine göre klasörlere ayırıyorum.",
            "normalized": normalized,
        }

    if open_app_intent(normalized):
        appName = extract_open_app(normalized)
        appName = resolve_app(appName)

        if not appName:
            return None

        if appName and safe_app_name(appName):
            return {
                "command": "open_app",
                "parameters": {"app_name": appName},
                "response": f"{appName.title()} açıyorum.",
                "normalized": normalized,
            }

    tokens = [t for t in normalized.split() if t and t not in FILLER_WORDS]
    
    if len(tokens) <= 2:
        resolved = resolve_app(" ".join(tokens))
        knownapps = set(APP_ALIASES.values())

        if resolved and resolved in knownapps and safe_app_name(resolved):
            return {
                "command": "none",
                "parameters": {},
                "response": f"{resolved.title()} ile ne yapmamı istiyorsun? Açmamı mı?",
                "normalized": normalized,
            }

    return None