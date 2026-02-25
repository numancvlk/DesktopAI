#LIBRARIES
import sys
from PySide6.QtWidgets import QApplication
from core import memory
from ui.screen import MainScreen

def main():
    try:
        memory.init_db()
    except RuntimeError:
        pass
    app = QApplication(sys.argv)
    window = MainScreen()
    window.show()
    sys.exit(app.exec())
