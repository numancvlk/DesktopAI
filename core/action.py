# LIBRARIES
import re
import time
import pyautogui
import pyperclip
from typing import Any, Dict

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


class SafeExecutor:
    ALLOWED_COMMANDS = {"none", "open_app"}

    def execute(self, command: str, parameters: Dict[str, Any]) -> None:
        cmd = (command or "").strip().lower()

        if cmd not in self.ALLOWED_COMMANDS:
            raise RuntimeError("Bu komut tanımlı değil")

        if cmd == "none":
            return

        if cmd == "open_app":
            appName = parameters.get("app_name") if isinstance(parameters, dict) else None
            
            if not isinstance(appName, str) or not safe_app_name(appName):
                raise RuntimeError("Geçersiz uygulama")
                
            appName = appName.strip()

            try:
                open_via_start_menu(appName)
            except Exception:
                raise RuntimeError("Uygulama acilamadi")
