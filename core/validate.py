from __future__ import annotations

import json
import re
from typing import Any, Dict, Iterable, Mapping

from pydantic import ValidationError

from .intent import IntentModel


class IntentParserError(Exception):

class IntentParser: #LLM den geleni IntentModel'e dönüştürür.

    def parse(self, raw_payload: Any) -> IntentModel:
        data: Dict[str, Any]

        if isinstance(raw_payload, str):
            try:
                data = json.loads(raw_payload)
            except json.JSONDecodeError as exc:
                raise IntentParserError("LLM yanıtı geçersiz") from exc
        elif isinstance(raw_payload, Mapping):
            data = dict(raw_payload)
        else:
            raise IntentParserError("Intent parsing desteklenmiyor")

        if "intent" not in data:
            data["intent"] = ""
        if "command" not in data:
            data["command"] = "none"
        if "parameters" not in data or data["parameters"] is None:
            data["parameters"] = {}
        if "response" not in data:
            data["response"] = ""

        try:
            return IntentModel(**data)
        except ValidationError as exc:
            raise IntentParserError("LLM IntentParseri dogru doldurmuyooo") from exc


class SecurityValidator:
    ALLOWED_COMMANDS = {"none", "open_app"}
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

