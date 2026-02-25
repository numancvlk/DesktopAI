# LIBRARIES
import sys
from dotenv import load_dotenv
from PySide6.QtWidgets import QApplication
from core import memory
from ui.screen import MainScreen


def main():
    load_dotenv()
    try:
        memory.init_db()
    except RuntimeError:
        pass
    app = QApplication(sys.argv)
    window = MainScreen()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
