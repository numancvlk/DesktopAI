# LIBRARIES
import os
import re
import time
import shutil
import itertools
import pyautogui
import pyperclip
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import urlparse
from .config import get_settings
from . import reminders
from . import user_modes

# Başlata gidecek uygulama isimlerinde zararli bir sey olmamiasi icin kontrol ediyoruz
SAFE_APP_PATTERN = re.compile(r"^[a-zA-Z0-9\u00c0-\u024f\s\-_.]{1,80}$")

# Bunlar asistanin acmamasi gereken uygulamaalr 
FORBIDDEN_APP = (
    "cmd", "powershell", "pwsh", "regedit", "format", "del ", "erase ",
    "shutdown", "wscript", "cscript", "schtasks",
)

def safe_app_name(name: str) -> bool:
    if not name or not isinstance(name, str):
        return False

    s = name.strip()

    if not s or len(s) > 80:
        return False

    if not SAFE_APP_PATTERN.match(s):
        return False

    lower = s.lower()

    for bad in FORBIDDEN_APP:
        if bad in lower:
            return False

    if ".." in s or "\\" in s or "/" in s or "&" in s or "|" in s or ";" in s or "%" in s:
        return False

    return True


# baslat menusunu acip uygulama adini yapistirip[ enterla aciyoruz
def open_start_menu(app_name: str) -> None:
    pyperclip.copy(app_name)
    time.sleep(0.05)
    pyautogui.press("win")
    time.sleep(0.6)
    pyautogui.hotkey("ctrl", "v")
    time.sleep(0.5)
    pyautogui.press("enter")


# url formatini kontrol ediyoruz
def normalize_url(raw_url: str) -> Optional[str]:
    if not isinstance(raw_url, str):
        return None

    candidate = raw_url.strip()
    if not candidate:
        return None
    if any(ch in candidate for ch in ("\r", "\n", "\t", " ")):
        return None

    if "://" not in candidate:
        candidate = f"https://{candidate}"

    parsed = urlparse(candidate)
    if parsed.scheme not in {"http", "https"}:
        return None
    if not parsed.netloc:
        return None

    return parsed.geturl()


# Tarayiciyi aciyor en son neler acildi acilmadi onlarin kaydini tutuyor
def open_links(browser_name: str, urls: list[str]) -> tuple[int, int]:
    if not urls:
        return 0, 0

    targetBrowser = (browser_name or "").strip()
    if not targetBrowser:
        return 0, len(urls)
    try:
        open_start_menu(targetBrowser)
    except Exception:
        return 0, len(urls)

    time.sleep(1.8)
    opened = 0
    failed = 0
    for index, url in enumerate(urls):
        try:
            if index > 0:
                pyautogui.hotkey("ctrl", "t")
                time.sleep(0.25)
            pyautogui.hotkey("ctrl", "l")
            time.sleep(0.2)
            pyperclip.copy(url)
            time.sleep(0.05)
            pyautogui.hotkey("ctrl", "v")
            time.sleep(0.15)
            pyautogui.press("enter")
            opened += 1
            time.sleep(0.5)
        except Exception:
            failed += 1
    return opened, failed


def screenshot_save_dir() -> Path:
    settings = get_settings()

    raw = (settings.screenshot_save_dir or "").strip().lower()

    if raw == "desktop":
        userprofile = os.environ.get("USERPROFILE", "")

        if not userprofile:
            return Path(settings.screenshot_save_dir)

        base = Path(userprofile)

        for folder_name in ("Desktop", "Masaüstü"):
            candidate = base / folder_name

            if candidate.is_dir():
                return candidate

        return base / "Desktop"

    return Path(settings.screenshot_save_dir)


# masausutunu duzenlemek icin masaustunun yolunu bulyuoz
def desktop_dir() -> Path:
    userprofile = os.environ.get("USERPROFILE", "") or None

    if userprofile:
        up = Path(userprofile)
        preferreddesktop1 = up / "OneDrive" / "Masaüstü"
        if preferreddesktop1.is_dir():
            return preferreddesktop1

    home = Path.home()

    preferredDesktop = home / "OneDrive" / "Masaüstü"
    if preferredDesktop.is_dir():
        return preferredDesktop

    bases = []

    if userprofile:
        up = Path(userprofile)
        bases.append(up)

        for child in up.iterdir():
            if child.is_dir() and child.name.lower().startswith("onedrive"):
                bases.append(child)

    if home not in bases:
        bases.append(home)

        for child in home.iterdir():
            if child.is_dir() and child.name.lower().startswith("onedrive"):
                bases.append(child)

    checked = set()

    for base in bases:
        if base in checked or not base.is_dir():
            continue

        checked.add(base)

        for folder_name in ("Masaüstü", "Desktop"):

            candidate = base / folder_name
            if candidate.is_dir():
                return candidate

    return home / "Desktop"


# ayni isimde dosyalar varsa onlari 1 2 diye siraliyoruz 
def resolve_name_collision(targetPath: Path) -> Path:
    parent = targetPath.parent
    stem = targetPath.stem
    suffix = targetPath.suffix

    for index in itertools.count(1):
        candidate = parent / f"{stem}_{index}{suffix}"

        if not candidate.exists():
            return candidate


# Masaustundeki dosyalari kategorilere ayiriyorz
def organize_desktop() -> str:
    desktop = desktop_dir()

    if not desktop.is_dir():
        raise RuntimeError("Masaüstü klasörü bulunamadi")

    dosyaYollari: Dict[str, tuple[str, Optional[str]]] = {
        ".pdf": ("Belgeler", "PDF"),
        ".doc": ("Belgeler", "Word"),
        ".docx": ("Belgeler", "Word"),
        ".txt": ("Belgeler", None),
        ".xls": ("Belgeler", "Excel"),
        ".xlsx": ("Belgeler", "Excel"),
        ".ppt": ("Belgeler", "PowerPoint"),
        ".pptx": ("Belgeler", "PowerPoint"),
 
        ".jpg": ("Resimler ve Videolar", "Resimler"),
        ".jpeg": ("Resimler ve Videolar", "Resimler"),
        ".png": ("Resimler ve Videolar", "Resimler"),
        ".gif": ("Resimler ve Videolar", "Resimler"),


        ".mp4": ("Resimler ve Videolar", "Videolar"),
        ".mkv": ("Resimler ve Videolar", "Videolar"),
        ".avi": ("Resimler ve Videolar", "Videolar"),
        ".mov": ("Resimler ve Videolar", "Videolar"),

        ".mp3": ("Muzik", None),
        ".wav": ("Muzik", None),

        ".zip": ("Arsivler", None),
        ".rar": ("Arsivler", None),

        ".lnk": ("Kisayollar", None),
    }

    moved: Dict[str, int] = {}

    for entry in desktop.iterdir():
        if not entry.is_file():
            continue

        if entry.name.startswith("."):
            continue

        ext = entry.suffix.lower()
        if not ext:
            continue

        mapping = dosyaYollari.get(ext)
        if not mapping:
            continue

        categoryName, subfolder = mapping

        targetDir = desktop / categoryName
        if subfolder:
            targetDir = targetDir / subfolder
        targetDir.mkdir(parents=True, exist_ok=True)

        targetPath = targetDir / entry.name
        if targetPath.exists():
            targetPath = resolve_name_collision(targetPath)

        try:
            shutil.move(str(entry), str(targetPath))
            moved[categoryName] = moved.get(categoryName, 0) + 1
        except OSError:
            continue

    totalMoved = sum(moved.values())

    if totalMoved == 0:
        return "Masaüstü zaten düzenli görünüyor!"

    parts = []

    for name, count in moved.items():
        if count:
            parts.append(f"{count} dosya '{name}' klasörüne taşındı")

    summary = ", ".join(parts)
    return f"Masaüstü düzenlendi: {summary}."


# Ekran gorunutusunu kaydedıp ekranda gosterıyoruz
def take_screenshot() -> str:
    saveDir = desktop_dir()
    saveDir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"ekran_goruntusu_{timestamp}.png"
    filepath = saveDir / filename
    try:
        time.sleep(3)
        img = pyautogui.screenshot()
        img.save(str(filepath))

    except OSError:
        raise RuntimeError("Ekran goruntusu kaydedilmedi")

    try:
        os.startfile(str(filepath))

    except OSError:
        pass
        
    return str(filepath)



def parse_reminder_time(raw: Any) -> datetime: #HATIRLATICI ICIN ZAMAN FORMATINI KONTROL EDIYORUZ

    if not isinstance(raw, str) or not raw.strip():
        raise RuntimeError("Hatırlatıcı zamanı yanlis")

    value = raw.strip()

    candidate = value[:-1] if value.endswith("Z") else value

    try:
        return datetime.fromisoformat(candidate)
    except ValueError:
        pass

    match = re.match(r"^\+(\d+)([mh])$", value)

    if match:
        amount = int(match.group(1))
        unit = match.group(2)
        now = datetime.utcnow()

        if unit == "m":
            return now + timedelta(minutes=amount)
        return now + timedelta(hours=amount)

    raise RuntimeError("Hatırlatıcı zamanı yanlis")

# LLM yada yerel niyet tespitinden sonra sadece bu komutlar calisir olmasi gerekiyor.
class SafeExecutor:
    ALLOWED_COMMANDS = {"none", "open_app", "screenshot", "set_reminder", "organize_desktop", "activate_mode"}

    def execute(self, command: str, parameters: Dict[str, Any]) -> Optional[str]:
        cmd = (command or "").strip().lower()

        if cmd not in self.ALLOWED_COMMANDS:
            raise RuntimeError("Bu komut tanımlı değil")

        if cmd == "none":
            return None 

        if cmd == "open_app":
            appName = parameters.get("app_name") if isinstance(parameters, dict) else None

            if not isinstance(appName, str) or not safe_app_name(appName):
                raise RuntimeError("Geçersiz uygulama")

            appName = appName.strip()

            try:
                open_start_menu(appName)
            except Exception:
                raise RuntimeError("Uygulama acilamadi")
            return None

        if cmd == "screenshot":
            return take_screenshot()

        if cmd == "organize_desktop":
            return organize_desktop()

        # Modlari calistiriyoruz
        if cmd == "activate_mode": #TODO elin degerse bunlari fonksiyona tasi
            modeName = parameters.get("mode_name") if isinstance(parameters, dict) else None
            if not isinstance(modeName, str) or not modeName.strip():
                raise RuntimeError("Mod adi belirtilmedi")

            mode = user_modes.mode_name(modeName.strip())
            if mode is None:
                raise RuntimeError(f"'{modeName.strip()}' modu bulunamadi")

            appNames = mode.get("app_names") or []
            linkUrls = mode.get("link_urls") or []
            browserName = mode.get("browser_name") or ""
            if not appNames and not linkUrls:
                raise RuntimeError(f"'{mode.get('name', modeName)}' modunda acilacak uygulama veya site yok")

            from .local_intents import resolve_app

            skippedInvalidLinks = 0
            skippedDuplicateLinks = 0
            seenLinks = set()
            normalizedLinks: list[str] = []
            for rawUrl in linkUrls:
                normalized = normalize_url(rawUrl)
                if not normalized:
                    skippedInvalidLinks += 1
                    continue
                dedupeKey = normalized.lower()
                if dedupeKey in seenLinks:
                    skippedDuplicateLinks += 1
                    continue
                seenLinks.add(dedupeKey)
                normalizedLinks.append(normalized)

            resolvedBrowser = str(browserName).strip() if isinstance(browserName, str) else ""
            if normalizedLinks and not safe_app_name(resolvedBrowser):
                raise RuntimeError("Link acmak icin mod ayarinda gecerli bir tarayici belirtin")
            openedLinks, failedLinks = open_links(resolvedBrowser, normalizedLinks)

            openedApps = 0
            for app in appNames:
                if not isinstance(app, str) or not safe_app_name(app):
                    continue
                resolved = resolve_app(app.strip())
                try:
                    open_start_menu(resolved)
                    openedApps += 1
                except Exception:
                    pass
                time.sleep(0.7)

            modeDisplayName = mode.get("name", modeName)
            return (
                f"'{modeDisplayName}' modu calisti: {openedApps} uygulama ve {openedLinks} site acildi "
                f"Atlanan site: {skippedInvalidLinks + skippedDuplicateLinks}, acilamayan site: {failedLinks}."
            )

        # hatirlatici ayalari vs TODO bunu da tasi 
        if cmd == "set_reminder":
            if not isinstance(parameters, dict):
                raise RuntimeError("Hatırlatıcı parametreleri geçersiz")

            text = parameters.get("text")
            rawTime = parameters.get("time")
            repeat = parameters.get("repeat")

            if not isinstance(text, str) or not text.strip():
                raise RuntimeError("Hatırlatıcı metni geçersiz")

            due_at = parse_reminder_time(rawTime)

            repeat_rule: Optional[str] = None
            if isinstance(repeat, str) and repeat.strip():
                repeat_rule = repeat.strip()

            reminders.create_reminder(
                text=text.strip(),
                due_at=due_at,
                repeat_rule=repeat_rule,
            )
            return None

        return None
