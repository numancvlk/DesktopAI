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

            exec_ok = True
            try:
                executor = SafeExecutor()
                executor.execute(normalized.command, normalized.parameters)
            except RuntimeError as e:
                exec_ok = False
                self.errorOccured.emit(str(e))

            memory.append_message("user", self.userInput)
            memory.append_message("assistant", normalized.response)
            self.newMessage.emit(normalized.response)

        except IntentParserError as exc:
            self.errorOccured.emit(str(exc))

        except RuntimeError as exc:
            self.errorOccured.emit(str(exc))

        except Exception:
            self.errorOccured.emit("Beklenmeyen bir hata oluştu.")
            
        finally:
            self.finishedProcessing.emit()
