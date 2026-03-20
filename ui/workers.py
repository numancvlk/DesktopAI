#LIBRARIES
import re
import datetime
from typing import Any, Dict
from PySide6.QtCore import QThread, Signal
from core import memory, llm
from core.action import SafeExecutor
from core.validate import IntentParser, IntentParserError, SecurityValidator
from core.config import get_settings
from core.rag import retrieve_relevant_chunks, build_augmented_user_input
from core.local_intents import detect_local_intent, resolve_app_name


def normalize_text_for_time(text: str) -> str:
    lowered = (text or "").strip().lower()
    lowered = (
        lowered.replace("ç", "c")
        .replace("ğ", "g")
        .replace("ı", "i")
        .replace("ö", "o")
        .replace("ş", "s")
        .replace("ü", "u")
    )
    return lowered


def relative_reminder_time(user_text: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    normalized = normalize_text_for_time(user_text)

    match = re.search(r"(\d+)\s*(saniye|sn|dakika|dk|saat)\s*sonra", normalized)

    if match:
        amount = int(match.group(1))
        unit = match.group(2)

        now = datetime.datetime.utcnow()

        if unit in ("saniye", "sn"):
            due = now + datetime.timedelta(seconds=amount)
        elif unit in ("dakika", "dk"):
            due = now + datetime.timedelta(minutes=amount)
        else:
            due = now + datetime.timedelta(hours=amount)

        iTime = due.strftime("%Y-%m-%dT%H:%M:%S")
        newParams = dict(parameters) if isinstance(parameters, dict) else {}
        newParams["time"] = iTime
        return newParams

    timeMatch = re.search(r"(\d{1,2})[.:](\d{2})", normalized)

    if timeMatch:
        hour = int(timeMatch.group(1))
        minute = int(timeMatch.group(2))

        now = datetime.datetime.utcnow()
        base_date = now.date()

        if "yarin" in normalized or "yarın" in user_text.lower():
            base_date = base_date + datetime.timedelta(days=1)
        elif "bugun" in normalized or "bu gun" in normalized or "bugün" in user_text.lower():
            base_date = base_date
        else:
            candidate = datetime.datetime.combine(base_date, datetime.time(hour=hour, minute=minute))

            if candidate <= now:
                base_date = base_date + datetime.timedelta(days=1)

        due = datetime.datetime(
            year=base_date.year,
            month=base_date.month,
            day=base_date.day,
            hour=hour,
            minute=minute,
            second=0,
        )

        iTime = due.strftime("%Y-%m-%dT%H:%M:%S")
        newParams = dict(parameters) if isinstance(parameters, dict) else {}
        newParams["time"] = iTime
        return newParams

    return parameters


class LLMWorker(QThread): #LLM Worker
    startedProcessing = Signal()
    newMessage = Signal(str)
    errorOccured = Signal(str)
    finishedProcessing = Signal()

    def __init__(self, user_input: str, mode: str = "assistant", parent=None): #TODO UI A GELEN HATALARI KALDIRABILRIIZ SIMDILIK KALSIN
        super().__init__(parent)
        self.userInput = user_input
        self.mode = mode

    def run(self):
        self.startedProcessing.emit()

        try:
            history = memory.get_last_messages(limit=3)
            settings = get_settings()

            if self.mode == "rag":
                enrichedInput = self.userInput
                if settings.rag_enabled:
                    try:
                        ragChunks = retrieve_relevant_chunks(self.userInput)
                        enrichedInput = build_augmented_user_input(
                            self.userInput,
                            ragChunks,
                        )
                    except RuntimeError:
                        pass

                answer = llm.call_rag(history, enrichedInput)
                memory.append_message("user", self.userInput)
                memory.append_message("assistant", answer)
                self.newMessage.emit(answer)
                return

            forcedIntent = detect_local_intent(self.userInput)
            if forcedIntent is not None:
                command = forcedIntent["command"]
                parameters = forcedIntent["parameters"]
                displayResponse = forcedIntent.get("response") or "Tamam."
            else:
                    enrichedInput = self.userInput
                    rawJson = llm.call(history, enrichedInput)
                    print("LLM RAW RESPONSE:", rawJson) #TODO DEBUG KALDIRILACAK
                    parser = IntentParser()
                    intent = parser.parse(rawJson)
                    validator = SecurityValidator()
                    normalized = validator.validate(intent)
                    command = normalized.command
                    parameters = normalized.parameters

                    if command == "set_reminder":
                        parameters = relative_reminder_time(self.userInput, parameters)

                    displayResponse = normalized.response or "Anladım, devam edelim."


            if command == "open_app" and isinstance(parameters, dict) and parameters.get("app_name"):
                parameters = dict(parameters)
                parameters["app_name"] = resolve_app_name(parameters["app_name"])

            try:
                executor = SafeExecutor()
                result = executor.execute(command, parameters)

                if result and isinstance(result, str):
                    displayResponse = f"{displayResponse} Dosya: {result}"

            except RuntimeError as e:
                displayResponse = str(e)

            memory.append_message("user", self.userInput)
            memory.append_message("assistant", displayResponse)
            self.newMessage.emit(displayResponse)

        except IntentParserError as exc:
            self.errorOccured.emit(str(exc))

        except RuntimeError as exc:
            self.errorOccured.emit(str(exc))

        except Exception as exc:
            self.errorOccured.emit(f"Beklenmeyen hata: {type(exc).__name__}: {exc}")
            
        finally:
            self.finishedProcessing.emit()
            