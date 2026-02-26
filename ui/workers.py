#LIBRARIES
from PySide6.QtCore import QThread, Signal
from core import memory, llm
from core.action import SafeExecutor
from core.validate import IntentParser, IntentParserError, SecurityValidator

class LLMWorker(QThread): #LLM Worker
    startedProcessing = Signal()
    newMessage = Signal(str)
    errorOccured = Signal(str)
    finishedProcessing = Signal()

    def __init__(self, user_input: str, parent=None):
        super().__init__(parent)
        self.userInput = user_input

    def run(self):
        self.startedProcessing.emit()

        try:
            history = memory.get_last_messages(limit=5)
            rawJson = llm.call(history, self.userInput)
            parser = IntentParser()
            intent = parser.parse(rawJson)
            validator = SecurityValidator()
            normalized = validator.validate(intent)

            execOk = True
            displayResponse = normalized.response
            try:
                executor = SafeExecutor()
                result = executor.execute(normalized.command, normalized.parameters)
                if result and isinstance(result, str):
                    displayResponse = f"{normalized.response} Dosya: {result}"
            except RuntimeError as e:
                execOk = False
                self.errorOccured.emit(str(e))

            memory.append_message("user", self.userInput)
            memory.append_message("assistant", displayResponse)
            self.newMessage.emit(displayResponse)

        except IntentParserError as exc:
            self.errorOccured.emit(str(exc))

        except RuntimeError as exc:
            self.errorOccured.emit(str(exc))

        except Exception:
            self.errorOccured.emit("Beklenmeyen bir hata oluştu.")
            
        finally:
            self.finishedProcessing.emit()
