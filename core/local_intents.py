#LIBRARIES  
import re
import unicodedata
from difflib import get_close_matches
from typing import Any, Dict, Optional
from .action import safe_app_name

#FUZZY MATCHINNG KULLANDIM BURDA SUANLIK IYI CALISIYOR BUNDAN BAHSETmeyi unutma

SCREENSHOT_PATTERNS = (
    "screenshot",
    "screen shot",
    "screen capture",
    "screencapture",
    "print screen",
    "prtsc",
    "ekran goruntusu",
    "ekran goruntusunu",
    "ekran goruntusu al",
    "ekran al",
    "ekrani kaydet",
    "ekrani kaydet",
    "ss al",
)

SCREENSHOT_SUBJECT_PATTERNS = (
    "ekran goruntusu",
    "screenshot",
    "screen shot",
    "screen capture",
    "screencapture",
    "print screen",
    "prtsc",
    "ss",
)

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

OPEN_APP_KEYWORDS = (
    "ac",
    "open",
    "baslat",
    "calistir",
    "aciver",
    "acsana",
)

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

FILLER_WORDS = {
    "lutfen",
    "please",
    "hadi",
    "bana",
    "sana",
    "uygulamasini",
    "uygulama",
    "programini",
    "program",
    "sana",
    "misin",
    "misin",
    "musun",
    "musun",
    "misiniz",
    "musunuz",
    "a",
    "kocum",
    "kanka",
    "dostum",
    "evet",
    "yi",
    "yı",
    "yu",
    "yü",
    "i",
    "ı",
    "u",
    "ü",
    "m",
    "s",
    "n",
    "ar",
}


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


def normalize_spoken_command(text: str) -> str:
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


def resolve_app_name(appName: str) -> str:
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


def extract_open_app_name(normalized: str) -> str:
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


def has_open_app_intent(normalized: str) -> bool:
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


def has_screenshot_intent(normalized: str) -> bool:
    if not normalized:
        return False

    if not any(pattern in normalized for pattern in SCREENSHOT_SUBJECT_PATTERNS):
        return False

    if any(f" {word} " in f" {normalized} " for word in SCREENSHOT_META_WORDS):
        return False

    return any(f" {word} " in f" {normalized} " for word in SCREENSHOT_ACTION_WORDS)


def detect_local_intent(text: str) -> Optional[Dict[str, Any]]:
    normalized = normalize_spoken_command(text)

    if has_screenshot_intent(normalized):
        return {
            "command": "screenshot",
            "parameters": {},
            "response": "Ekran görüntüsünü alıp masaüstüne kaydettim.",
            "normalized": normalized,
        }

    if has_open_app_intent(normalized):
        appName = extract_open_app_name(normalized)
        appName = resolve_app_name(appName)
        if not appName:
            return {
                "command": "none",
                "parameters": {},
                "response": "Hangi uygulamayı açayım?",
                "normalized": normalized,
            }
        if appName and safe_app_name(appName):
            return {
                "command": "open_app",
                "parameters": {"app_name": appName},
                "response": f"{appName.title()} açıyorum.",
                "normalized": normalized,
            }

    return None
