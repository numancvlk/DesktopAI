 #LIBRARIES
from PySide6.QtCore import QThread, Signal
from core.rag import index_pdf

class RAGIndexWorker(QThread): 
    indexingFinished = Signal(str)
    errorOccured = Signal(str)

    def __init__(self, pdf_path: str, parent=None):
        super().__init__(parent)

        self.pdfPath = pdf_path

    def run(self):
        try:
            docId = index_pdf(self.pdfPath)
            self.indexingFinished.emit(docId)
        except Exception as exc:
            self.errorOccured.emit(str(exc))

