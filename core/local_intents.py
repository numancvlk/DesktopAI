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
    "whatsap": "whatsapp",
    "watsapp": "whatsapp",
    "watshapp": "whatsapp",
    "steam": "steam",
    "stim": "steam",
    "googlechrome": "chrome",
    "spotify": "spotify",
    "notepad": "notepad",
    "hesapmakinesi": "hesap makinesi",
    "calculator": "hesap makinesi",
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
}


def normalize_user_text(text: str) -> str:
    lowered = (text or "").strip().lower()
    normalized = unicodedata.normalize("NFKD", lowered)
    noAccent = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    noPunct = re.sub(r"[^a-z0-9\s]", " ", noAccent)
    return re.sub(r"\s+", " ", noPunct).strip()


def compact_key(text: str) -> str:
    return re.sub(r"\s+", "", (text or "").strip().lower())


def resolve_app_name(appName: str) -> str:
    compact = compact_key(appName)

    if not compact:
        return appName

    direct = APP_ALIASES.get(compact)
    if direct:
        return direct

    candidates = list(APP_ALIASES.keys())
    nearest = get_close_matches(compact, candidates, n=1, cutoff=0.82)

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

    tokens = [token for token in appName.split() if token and token not in FILLER_WORDS]
    return " ".join(tokens).strip()


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


def detect_local_intent(text: str) -> Optional[Dict[str, Any]]:
    normalized = normalize_user_text(text)

    if any(pattern in normalized for pattern in SCREENSHOT_PATTERNS):
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
                "parameters": {"appName": appName},
                "response": f"{appName.title()} açıyorum.",
                "normalized": normalized,
            }

    return None
