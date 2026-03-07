#LIBRARIES
from PySide6.QtCore import QThread, Signal
from core import memory, llm
from core.action import SafeExecutor
from core.validate import IntentParser, IntentParserError, SecurityValidator
from core.config import get_settings
from core.rag import retrieve_relevant_chunks, build_augmented_user_input


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
            history = memory.get_last_messages(limit=5)
            settings = get_settings()

            if self.mode == "rag":
                enriched_input = self.userInput
                if settings.rag_enabled:
                    try:
                        ragChunks = retrieve_relevant_chunks(self.userInput)
                        enrichedInput = build_augmented_user_input(
                            self.userInput,
                            ragChunks,
                        )
                    except RuntimeError:
                        enrichedInput = self.userInput

                answer = llm.call_rag(history, enrichedInput)
                memory.append_message("user", self.userInput)
                memory.append_message("assistant", answer)
                self.newMessage.emit(answer)
                return

            enrichedInput = self.userInput
            rawJson = llm.call(history, enrichedInput)
            parser = IntentParser()
            intent = parser.parse(rawJson)
            validator = SecurityValidator()
            normalized = validator.validate(intent)

            displayResponse = normalized.response

            try:
                executor = SafeExecutor()
                result = executor.execute(normalized.command, normalized.parameters)
                
                if result and isinstance(result, str):
                    displayResponse = f"{normalized.response} Dosya: {result}"

            except RuntimeError as e:
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
            