#LIBRARIES
from typing import Any, Dict
from pydantic import BaseModel, Field, validator


class IntentModel(BaseModel):
    """
    LLM'den beklenen JSON
    """
    intent: str = Field(default="")
    command: str = Field(default="none")
    parameters: Dict[str, Any] = Field(default_factory=dict)
    response: str

    class Config:
        extra = "ignore"

    @validator("intent", "command", "response", pre=True)
    def strip_strings(cls, value: Any) -> Any:
        if isinstance(value, str):
            return value.strip()
        return value

    def is_noop(self) -> bool:
        return self.command == "none"

    def requires_action(self) -> bool:
        return not self.is_noop()

