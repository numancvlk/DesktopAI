#LIBRARIES
import os
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

def get_os_apps_dir() -> Path:
    localApps = os.environ.get("LOCALAPPDATA", "")

    if not localApps:
        return Path("")

    return Path(localApps) / "Microsoft" / "WindowsApps"

def safe_app_name(name: str) -> bool:
    if not name or not name.strip():
        return False

    forbidden = re.compile(r'[<>:"|?*\\/]')

    if forbidden.search(name):
        return False

    if ".." in name:
        return False 
    return True

def find_app_in_os_apps(app_name: str) -> Optional[Path]:
    osApps = get_os_apps_dir()

    if not osApps.is_dir():
        return None

    normalizedQuery = app_name.strip().lower()

    if not normalizedQuery:
        return None

    bestMatch: Optional[Path] = None

    for exePath in osApps.glob("*.exe"):
        if not exePath.is_file():
            continue

        stem = exePath.stem.lower()

        if stem == normalizedQuery:
            return exePath

        if normalizedQuery in stem and bestMatch is None:
            bestMatch = exePath

    return bestMatch

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

            exePath = find_app_in_os_apps(appName)

            if exePath is None:
                raise RuntimeError("Uygulama bulunamadı")

            try:
                proc = subprocess.Popen(
                    [str(exePath)],
                    shell=False,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            except:
                raise RuntimeError("Uygulama calistirilamadi")
            return
