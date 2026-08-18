from PySide6.QtWidgets import QApplication
from mainWindow import MainWindow
from config import *
import sys

if __name__ == "__main__":
    userPreferences = loadPreferences()
    print(userPreferences)

    application = QApplication()
    application.setStyle("Fusion")
    mainWindow = MainWindow(userPreferences)
    mainWindow.show()
    sys.exit(application.exec())
