# LIBRARIES
import os
import re
import time
import pyautogui
import pyperclip
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
from .config import get_settings

SAFE_APP_PATTERN = re.compile(r"^[a-zA-Z0-9\u00c0-\u024f\s\-_.]{1,80}$")
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


def open_via_start_menu(app_name: str) -> None:
    pyperclip.copy(app_name)
    time.sleep(0.05)
    pyautogui.press("win")
    time.sleep(0.6)
    pyautogui.hotkey("ctrl", "v")
    time.sleep(0.5)
    pyautogui.press("enter")


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


def take_screenshot() -> str:
    saveDir = screenshot_save_dir()
    saveDir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"ekran_goruntusu_{timestamp}.png"
    filepath = saveDir / filename
    try:
        img = pyautogui.screenshot()
        img.save(str(filepath))

    except OSError:
        raise RuntimeError("Ekran goruntusu kaydedilmedi")

    try:
        os.startfile(str(filepath))

    except OSError:
        pass
        
    return str(filepath)


class SafeExecutor:
    ALLOWED_COMMANDS = {"none", "open_app", "screenshot"}

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
                open_via_start_menu(appName)
            except Exception:
                raise RuntimeError("Uygulama acilamadi")
            return None

        if cmd == "screenshot":
            return take_screenshot()

        return None
