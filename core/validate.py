# LIBRARIES
import json
import re
from typing import Any, Dict, Iterable, Mapping
from pydantic import ValidationError
from .intent import IntentModel

class IntentParserError(Exception):
    pass

def fix_json_string(s: str) -> str:
    s = re.sub(r",\s*}", "}", s)
    s = re.sub(r",\s*]", "]", s)
    return s


def extract_json_from_string(text: str) -> Dict[str, Any]:
    text = (text or "").strip()

    if not text:
        raise IntentParserError("LLM yanıtı boş")

    for candidate in (text, fix_json_string(text)):

        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    cleaned = re.sub(r"^```(?:json)?\s*", "", text)
    cleaned = re.sub(r"\s*```\s*$", "", cleaned).strip()

    for candidate in (cleaned, fix_json_string(cleaned)):
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    start = text.find("{")

    if start < 0:
        raise IntentParserError("LLM yanıtı geçersiz")

    depth = 0

    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                chunk = text[start : i + 1]
                for candidate in (chunk, fix_json_string(chunk)):
                    try:
                        return json.loads(candidate)
                    except json.JSONDecodeError:
                        pass
                break

    end = text.rfind("}")

    if end > start:
        chunk = text[start : end + 1]

        for candidate in (chunk, fix_json_string(chunk)):
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                pass
    raise IntentParserError("LLM yanıtı geçersiz")


class IntentParser:
    def parse(self, raw_payload: Any) -> IntentModel:

        if isinstance(raw_payload, str):
            data = extract_json_from_string(raw_payload)

        elif isinstance(raw_payload, Mapping):
            data = dict(raw_payload)

        else:
            raise IntentParserError("Intent parsing yanlis")

        if not isinstance(data, dict):
            raise IntentParserError("LLM yanıtı geçersiz")

        data["intent"] = str(data.get("intent") or "").strip()
        cmd = str(data.get("command") or "none").strip().lower()
        data["command"] = cmd if cmd in ("none", "open_app", "screenshot") else "none"
        params = data.get("parameters")
        data["parameters"] = dict(params) if isinstance(params, dict) else {}
        rawResponse = data.get("response")
        data["response"] = str(rawResponse).strip() if rawResponse is not None else ""

        try:
            return IntentModel(**data)
        except ValidationError:
            raise IntentParserError("LLM yanıtı geçersiz")


class SecurityValidator:
    ALLOWED_COMMANDS = {"none", "open_app", "screenshot"}
    FORBIDDEN_KEYWORDS = (
        "powershell",
        "get-startapps",
        ".ps1",
        "regedit",
        "registry",
        "shutdown",
        "format ",
        "del ",
        "erase ",
        "rm ",
        "rmdir ",
        "cmd.exe",
        "wscript",
        "cscript",
        "schtasks",
    )

    MARKUP_PATTERN = re.compile(r"[*_`#\[\]]")

    def validate(self, intent: IntentModel) -> IntentModel: #Guvenlik kontrolu yapiyoruz
        normalized = intent.copy()

        normalized.command = normalized.command.strip().lower()
        if not normalized.command:
            normalized.command = "none"

        if normalized.command not in self.ALLOWED_COMMANDS:
            normalized.command = "none"
            normalized.parameters = {}
            normalized.response = (
                "Bu istekte tanımlı olmayan bir komut algıladım, "
                "bu yüzden herhangi bir sistem komutu çalıştırmadım."
            )
            normalized.response = self.sanitize_response(normalized.response)
            return normalized

        if self.forbidden_content(
            normalized.intent, normalized.parameters
        ):
            normalized.command = "none"
            normalized.parameters = {}
            normalized.response = (
                "Bu istekte güvenlik riski tespit ettim, "
                "bu yüzden herhangi bir sistem komutu çalıştırmadım."
            )
            normalized.response = self.sanitize_response(normalized.response)
            return normalized

        normalized.response = self.sanitize_response(normalized.response)

        if normalized.command == "none":
            normalized.parameters = {}

        return normalized

    def forbidden_content(
        self,
        intent_text: str,
        parameters: Mapping[str, Any],
    ) -> bool:
        haystack = [intent_text]
        haystack.extend(self.flatten_values(parameters.values()))

        for value in haystack:
            if not isinstance(value, str):
                continue
            lowerValue = value.lower()
            for keyword in self.FORBIDDEN_KEYWORDS:
                if keyword in lowerValue:
                    return True
        return False

    def flatten_values(self, values: Iterable[Any]) -> Iterable[Any]:
        for value in values:
            if isinstance(value, Mapping):
                for inner in self.flatten_values(value.values()):
                    yield inner
            elif isinstance(value, (list, tuple, set)):
                for inner in self.flatten_values(value):
                    yield inner
            else:
                yield value

    def sanitize_response(self, text: str) -> str: #Markdownu kaldniyuoruz
        cleaned = self.MARKUP_PATTERN.sub("", text)
        cleaned = cleaned.strip()
        return cleaned

