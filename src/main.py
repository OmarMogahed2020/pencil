from PySide6.QtWidgets import QApplication
from mainWindow import MainWindow
from config import *
import sys

if __name__ == "__main__":
    userPreferences = loadPreferences()

    application = QApplication()
    mainWindow = MainWindow(sys.argv[1] if len(sys.argv) > 1 else None)
    mainWindow.show()
    sys.exit(application.exec())
