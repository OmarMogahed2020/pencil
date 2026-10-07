from PySide6.QtWidgets import QMessageBox, QFileDialog, QTextEdit, QDialog, QComboBox, QSpinBox, QMessageBox, QStatusBar, QHBoxLayout
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, QTimer, QFileSystemWatcher, Qt, QEvent, QObject
from PySide6.QtGui import QAction, QIcon, QTextOption, QFontMetrics
from config import *
import sys
import os


class CloseHandler(QObject):
    def __init__(self, callback):
        super().__init__()
        self.callback = callback

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.Close:
            if self.callback() is False:
                event.ignore()
                return True
        try:
            return super().eventFilter(obj, event)
        except RuntimeError:
            return False


class MainWindow:
    def __init__(self, openedFilePath=None):
        self.window = self.loadUI()
        self.currentFilePath = None
        self.connectActions()
        self.updateWindowTitle()

        self.autosaveTimer = QTimer()
        self.autosaveTimer.timeout.connect(self.autoSave)
        self.autosaveTimer.stop()

        self.textDirection = "ltr"
        self.window.setWindowIcon(QIcon(f"{ASSETS[ICON_APP_ICON]}"))

        self.fileWatcher = QFileSystemWatcher()
        self.fileWatcher.fileChanged.connect(self.refreshFile)
        self.preferencesWatcher = QFileSystemWatcher()
        self.preferencesWatcher.fileChanged.connect(lambda: self.applyPreferences(self.getCurrentPreferences()))
        self.preferencesWatcher.addPath(f"{ASSETS[DATA_PREFERENCES_JSON]}")

        self.savedByApp = False  # used to one time stop the file refreshing method if a change happened by the app itself
        self.lastSavedText = None  # used to compare the last changes with the editor text
        self.lastAppliedPreferences = None

        self._closeHandler = CloseHandler(self.askToSaveChanges)  # <-
        self.window.installEventFilter(self._closeHandler)  # <-

        self.applyPreferences(self.getCurrentPreferences())

        if openedFilePath:
            self.openFilePath(openedFilePath)

    def refreshFile(self):
        if self.currentFilePath:
            try:
                with open(self.currentFilePath, mode="r", encoding="utf-8") as file:
                    text = file.read()
                    textEdit = self.window.findChild(QTextEdit, "textEdit")
                    if textEdit.toPlainText() != text:
                        textEdit.setText(text)

                    self.lastSavedText = text  # to prevent the loop completely

            except FileNotFoundError:
                QMessageBox.critical(self.window, "Error", "Couldn't update the file")
                sys.exit(1)

    def loadUI(self):
        file = QFile(str(ASSETS[UI_MAIN_WINDOW]))
        loader = QUiLoader()
        mainWindow = loader.load(file)
        file.close()
        mainWindow.showMaximized()

        numberLine = mainWindow.findChild(QTextEdit, "numberLine")
        numberLine.setDisabled(True)
        numberLine.setReadOnly(True)
        numberLine.setCursor(Qt.ArrowCursor)
        numberLine.viewport().setCursor(Qt.ArrowCursor)
        textEdit = mainWindow.findChild(QTextEdit, "textEdit")
        textEdit.textChanged.connect(lambda: self.refreshNumberLineNumbers(textEdit))
        textEdit.verticalScrollBar().valueChanged.connect(lambda: self.refreshNumberLineScroll(textEdit))

        if not mainWindow:
            QMessageBox.critical(self.window, "Error", "Couldn't open the main window")
            sys.exit(1)
        return mainWindow

    def refreshNumberLineNumbers(self, textEdit: QTextEdit):
        number = 1
        text = textEdit.toPlainText()
        for letter in text:
            if letter == "\n":
                number += 1
        format_ = ""
        for number in range(number):
            format_ += f"{number+1}\n"

        widget = self.window.findChild(QTextEdit, "numberLine")
        widget.setText(format_)
        widget.setFont(textEdit.font())
        widget.setFontWeight(textEdit.fontWeight())
        self.refreshNumberLineScroll(textEdit)

        metrics = QFontMetrics(textEdit.font())
        width = metrics.horizontalAdvance(f" {str(number+1).zfill(4)}")  # to fit the largest number
        self.window.findChild(QTextEdit, "numberLine").setFixedWidth(width)

    def refreshNumberLineScroll(self, textEdit: QTextEdit):
        offset = textEdit.verticalScrollBar().value()
        self.window.findChild(QTextEdit, "numberLine").verticalScrollBar().setValue(offset)

    def updateWindowTitle(self):
        if self.currentFilePath:
            self.window.setWindowTitle(f"Pencil | {self.currentFilePath}")
        else:
            self.window.setWindowTitle("Pencil | untitled")

    def applyDirectionState(self, direction):
        if direction == "rtl":
            self.window.findChild(QAction, "actionRTL").setEnabled(False)
            self.window.findChild(QAction, "actionLTR").setEnabled(True)
        else:
            self.window.findChild(QAction, "actionLTR").setEnabled(False)
            self.window.findChild(QAction, "actionRTL").setEnabled(True)

    def connectActions(self):
        self.window.findChild(QAction, "actionPreferences").triggered.connect(self.showPreferences)
        self.window.findChild(QAction, "actionNew").triggered.connect(self.newFile)
        self.window.findChild(QAction, "actionOpen").triggered.connect(self.openFile)
        self.window.findChild(QAction, "actionSave").triggered.connect(self.saveFile)
        self.window.findChild(QAction, "actionAutoSave").toggled.connect(self.toggleAutoSave)
        self.window.findChild(QAction, "actionExit").triggered.connect(self.exitApp)
        self.window.findChild(QAction, "actionUndo").triggered.connect(self.undoEdit)
        self.window.findChild(QAction, "actionRedo").triggered.connect(self.redoEdit)
        self.window.findChild(QAction, "actionCut").triggered.connect(self.cutEdit)
        self.window.findChild(QAction, "actionCopy").triggered.connect(self.copyEdit)
        self.window.findChild(QAction, "actionPaste").triggered.connect(self.pasteEdit)
        self.window.findChild(QAction, "actionRTL").triggered.connect(self.setRtl)
        self.window.findChild(QAction, "actionLTR").triggered.connect(self.setLtr)
        self.window.findChild(QAction, "actionFullScreen").triggered.connect(self.toggleFullScreen)

    def newFile(self):
        self.askToSaveChanges()
        self.currentFilePath = None
        self.window.findChild(QTextEdit, "textEdit").setText("")
        self.window.findChild(QStatusBar, "statusbar").showMessage("Created a new empty file", 3000)
        self.updateWindowTitle()

    def openFile(self):
        filePath, _ = QFileDialog.getOpenFileName(self.window, "Open File", "", "All Files (*)")
        if filePath:
            self.openFilePath(filePath)

    def openFilePath(self, filePath):
        try:
            with open(filePath, mode="r", encoding="utf-8") as file:
                self.window.findChild(QTextEdit, "textEdit").setPlainText(file.read())
            self.currentFilePath = filePath
            self.updateWindowTitle()
            self.window.findChild(QStatusBar, "statusbar").showMessage(
                f"Opened `{self.currentFilePath}`",
                3000,
            )

            self.fileWatcher.addPath(self.currentFilePath)
        except FileNotFoundError:
            QMessageBox.critical(self.window, "Error", "Couldn't open the file")
            sys.exit(1)

    def saveFile(self):
        if self.currentFilePath:
            self.saveToPath(self.currentFilePath)
        else:
            self.currentFilePath, _ = QFileDialog.getOpenFileName(self.window, "Save as", "", "All Files (*)")
            self.saveToPath(self.currentFilePath)

    def saveToPath(self, filePath):
        try:
            mode = "w" if os.path.exists(f"{filePath}") else "x"
            with open(f"{self.currentFilePath}", mode=mode, encoding="utf-8") as file:
                text = self.window.findChild(QTextEdit, "textEdit").toPlainText()
                file.write(text)
                self.lastSavedText = text
                self.updateWindowTitle()
                self.window.findChild(QStatusBar, "statusbar").showMessage(
                    f"Saved changes to `{self.currentFilePath}`",
                    1000,
                )
        except:
            QMessageBox.critical(self.window, "Error", "Couldn't save the file")
            sys.exit(1)

    def undoEdit(self):
        self.window.findChild(QTextEdit, "textEdit").undo()

    def redoEdit(self):
        self.window.findChild(QTextEdit, "textEdit").redo()

    def cutEdit(self):
        self.window.findChild(QTextEdit, "textEdit").cut()

    def copyEdit(self):
        self.window.findChild(QTextEdit, "textEdit").copy()

    def pasteEdit(self):
        self.window.findChild(QTextEdit, "textEdit").paste()

    def setRtl(self):
        self.textDirection = "rtl"
        editor = self.window.findChild(QTextEdit, "textEdit")
        editor.setLayoutDirection(Qt.RightToLeft)
        opt = QTextOption()
        opt.setTextDirection(Qt.RightToLeft)
        opt.setFlags(opt.flags() | QTextOption.ShowTabsAndSpaces)
        editor.document().setDefaultTextOption(opt)

        numberLine = self.window.findChild(QTextEdit, "numberLine")
        numberLine.setLayoutDirection(Qt.LeftToRight)
        opt = QTextOption()
        opt.setTextDirection(Qt.LeftToRight)
        opt.setFlags(opt.flags() | QTextOption.ShowTabsAndSpaces)
        numberLine.document().setDefaultTextOption(opt)

        self.applyDirectionState("rtl")
        self.window.findChild(QHBoxLayout, "textLayout").setDirection(QHBoxLayout.RightToLeft)
        self.saveDirectionToPreferences()

    def setLtr(self):
        self.textDirection = "ltr"
        editor = self.window.findChild(QTextEdit, "textEdit")
        editor.setLayoutDirection(Qt.LeftToRight)
        opt = QTextOption()
        opt.setTextDirection(Qt.LeftToRight)
        opt.setFlags(opt.flags() | QTextOption.ShowTabsAndSpaces)
        editor.document().setDefaultTextOption(opt)

        numberLine = self.window.findChild(QTextEdit, "numberLine")
        numberLine.setLayoutDirection(Qt.RightToLeft)
        opt = QTextOption()
        opt.setTextDirection(Qt.RightToLeft)
        opt.setFlags(opt.flags() | QTextOption.ShowTabsAndSpaces)
        numberLine.document().setDefaultTextOption(opt)

        self.applyDirectionState("ltr")
        self.window.findChild(QHBoxLayout, "textLayout").setDirection(QHBoxLayout.LeftToRight)
        self.saveDirectionToPreferences()

    def saveDirectionToPreferences(self):  # because it is not edited by the dialog directly
        try:
            old = ""
            with open(ASSETS[DATA_PREFERENCES_JSON], mode="r", encoding="utf-8") as file:
                old = json.loads(file.read())
            old["text-direction"] = self.textDirection
            with open(ASSETS[DATA_PREFERENCES_JSON], mode="w", encoding="utf-8") as file:
                file.write(json.dumps(old, indent=4))
        except FileNotFoundError:
            QMessageBox.critical(self.window, "Pencil", "Preferences doesn't exist")
            sys.exit(1)
        except json.decoder.JSONDecodeError:
            self.saveDirectionToPreferences()

    def toggleAutoSave(self, checked):
        if checked:
            self.autosaveTimer.start(200)
            self.window.statusBar().showMessage("Auto Save enabled", 3000)
        else:
            self.autosaveTimer.stop()
            self.window.statusBar().showMessage("Auto Save disabled", 3000)
        preferences = self.getCurrentPreferences()
        preferences["auto-save"] = checked
        savePreferences(preferences)

    def autoSave(self):
        if self.currentFilePath:
            text = self.window.findChild(QTextEdit, "textEdit").toPlainText()
            if text != self.lastSavedText:
                self.saveToPath(self.currentFilePath)

    def setColorTheme(self, themeKey):
        self._currentTheme = themeKey
        try:
            with open(ASSETS[themeKey], mode="r") as file:
                self.window.setStyleSheet(file.read())
        except:
            print(f"didn't find the style `{themeKey}`")
            sys.exit(1)

    def showPreferences(self):
        file = QFile(str(ASSETS[UI_PREFERENCES]))
        loader = QUiLoader()
        dialog = loader.load(file)
        dialog.setStyleSheet(self.window.styleSheet())
        file.close()
        if dialog:
            self.initPreferencesDialog(dialog)
            result = dialog.exec()
            if result == QDialog.Accepted:
                preferences = self.readPreferencesFromDialog(dialog)
                savePreferences(preferences)  # should be first to save preferences before updating the editor
                self.applyPreferences(preferences)
        else:
            QMessageBox.critical(self.window, "Error", "Couldn't open the preferences window")

    def initPreferencesDialog(self, dialog):
        themeCombo = dialog.findChild(QComboBox, "comboBox")
        spinBox = dialog.findChild(QSpinBox, "spinBox")
        fontCombo = dialog.findChild(QComboBox, "fontComboBox")

        theme_map = {
            "dark-theme": 0,
            "light-theme": 1,
            "dark-monokai-theme": 2,
            "light-monokai-theme": 3,
            "dark-dracula-theme": 4,
            "light-dracula-theme": 5,
            "dark-nord-theme": 6,
            "light-nord-theme": 7,
            "dark-solarized-theme": 8,
            "light-solarized-theme": 9,
            "dark-github-theme": 10,
            "light-github-theme": 11,
        }

        if themeCombo:
            currentTheme = getattr(self, "_currentTheme", "dark-theme")
            themeCombo.setCurrentIndex(theme_map.get(currentTheme, 0))

        if spinBox:
            spinBox.setValue(int(getattr(self, "_currentFontSize", 13)))

        theme_key_to_display = {
            STYLE_DARK_THEME: "Dark",
            STYLE_LIGHT_THEME: "Light",
            STYLE_DARK_MONOKAI: "Dark Monokai",
            STYLE_LIGHT_MONOKAI: "Light Monokai",
            STYLE_DARK_DRACULA: "Dark Dracula",
            STYLE_LIGHT_DRACULA: "Light Dracula",
            STYLE_DARK_NORD: "Dark Nord",
            STYLE_LIGHT_NORD: "Light Nord",
            STYLE_DARK_SOLARIZED: "Dark Solarized",
            STYLE_LIGHT_SOLARIZED: "Light Solarized",
            STYLE_DARK_GITHUB: "Dark Github",
            STYLE_LIGHT_GITHUB: "Light Github",
        }

        themeCombo.setCurrentText(theme_key_to_display[self._currentTheme])

        if fontCombo:
            fontFamily = getattr(self, "_currentFontFamily", "Arial")
            index = fontCombo.findText(fontFamily)
            if index >= 0:
                fontCombo.setCurrentIndex(index)

    def applyPreferences(self, preferences):

        if self.lastAppliedPreferences == preferences:
            return
        self.lastAppliedPreferences = preferences

        theme = preferences.get("theme", "dark-theme")
        theme_map = {
            "dark-theme": STYLE_DARK_THEME,
            "light-theme": STYLE_LIGHT_THEME,
            "dark-monokai-theme": STYLE_DARK_MONOKAI,
            "light-monokai-theme": STYLE_LIGHT_MONOKAI,
            "dark-dracula-theme": STYLE_DARK_DRACULA,
            "light-dracula-theme": STYLE_LIGHT_DRACULA,
            "dark-nord-theme": STYLE_DARK_NORD,
            "light-nord-theme": STYLE_LIGHT_NORD,
            "dark-solarized-theme": STYLE_DARK_SOLARIZED,
            "light-solarized-theme": STYLE_LIGHT_SOLARIZED,
            "dark-github-theme": STYLE_DARK_GITHUB,
            "light-github-theme": STYLE_LIGHT_GITHUB,
        }
        self.setColorTheme(theme_map.get(theme, STYLE_DARK_THEME))

        direction = preferences.get("text-direction", "ltr")
        if direction == "rtl":
            self.setRtl()
        else:
            self.setLtr()

        autoSave = preferences.get("auto-save", False)
        action = self.window.findChild(QAction, "actionAutoSave")
        if action:
            action.setChecked(autoSave)

        self.applyFontSize(int(preferences.get("font-size", 13)))
        self.applyFontFamily(preferences.get("font-family", "Arial"))

        textEdit = self.window.findChild(QTextEdit, "textEdit")
        metrics = QFontMetrics(textEdit.font())
        width = metrics.horizontalAdvance(" ")
        textEdit.setTabStopDistance(width * 4)

        self.refreshNumberLineNumbers(textEdit)
        self.refreshNumberLineScroll(textEdit)

        updatedPreferences = f"{json.dumps(preferences, indent=4)}"
        with open(ASSETS[DATA_PREFERENCES_JSON], mode="w", encoding="utf-8") as file:
            file.write(updatedPreferences)

    def readPreferencesFromDialog(self, dialog):
        preferences = {}
        themeCombo = dialog.findChild(QComboBox, "comboBox")
        spinBox = dialog.findChild(QSpinBox, "spinBox")
        fontCombo = dialog.findChild(QComboBox, "fontComboBox")
        autoSaveAction = self.window.findChild(QAction, "actionAutoSave")

        theme_map = {
            0: "dark-theme",
            1: "light-theme",
            2: "dark-monokai-theme",
            3: "light-monokai-theme",
            4: "dark-dracula-theme",
            5: "light-dracula-theme",
            6: "dark-nord-theme",
            7: "light-nord-theme",
            8: "dark-solarized-theme",
            9: "light-solarized-theme",
            10: "dark-github-theme",
            11: "light-github-theme",
        }

        if themeCombo:
            index = themeCombo.currentIndex()
            preferences["theme"] = theme_map.get(index, "dark-theme")

        if spinBox:
            preferences["font-size"] = spinBox.value()

        if fontCombo:
            preferences["font-family"] = fontCombo.currentText()

        if autoSaveAction:
            preferences["auto-save"] = autoSaveAction.isChecked()

        preferences["text-direction"] = self.textDirection

        return preferences

    def applyFontSize(self, size):
        self._currentFontSize = size
        editor = self.window.findChild(QTextEdit, "textEdit")
        font = editor.font()
        font.setPointSize(size)
        editor.setFont(font)

    def applyFontFamily(self, family):
        self._currentFontFamily = family
        editor = self.window.findChild(QTextEdit, "textEdit")
        font = editor.font()
        font.setFamily(family)
        editor.setFont(font)

    def getCurrentPreferences(self):
        preferences = {}
        try:
            with open(ASSETS[DATA_PREFERENCES_JSON], mode="r", encoding="utf-8") as file:
                preferences = json.loads(file.read())
        except FileNotFoundError:
            theme_slug_map = {
                STYLE_DARK_THEME: "dark-theme",
                STYLE_LIGHT_THEME: "light-theme",
                STYLE_DARK_MONOKAI: "dark-monokai-theme",
                STYLE_LIGHT_MONOKAI: "light-monokai-theme",
                STYLE_DARK_DRACULA: "dark-dracula-theme",
                STYLE_LIGHT_DRACULA: "light-dracula-theme",
                STYLE_DARK_NORD: "dark-nord-theme",
                STYLE_LIGHT_NORD: "light-nord-theme",
                STYLE_DARK_SOLARIZED: "dark-solarized-theme",
                STYLE_LIGHT_SOLARIZED: "light-solarized-theme",
                STYLE_DARK_GITHUB: "dark-github-theme",
                STYLE_LIGHT_GITHUB: "light-github-theme",
            }
            preferences["theme"] = theme_slug_map.get(getattr(self, "_currentTheme", STYLE_DARK_THEME), "dark-theme")
            preferences["font-size"] = getattr(self, "_currentFontSize", 13)
            preferences["font-family"] = getattr(self, "_currentFontFamily", "Arial")
            preferences["text-direction"] = self.textDirection
            action = self.window.findChild(QAction, "actionAutoSave")
            preferences["auto-save"] = action.isChecked() if action and preferences["auto-save"] else False
        return preferences

    def toggleFullScreen(self):
        if self.window.isFullScreen():
            self.window.showMaximized()
        else:
            self.window.showFullScreen()

    def theFileDiffer(self, filePath):
        currentText = self.window.findChild(QTextEdit, "textEdit").toPlainText()
        try:
            with open(filePath, mode="r", encoding="utf-8") as file:
                if file.read() == currentText:
                    return False
                else:
                    return True
        except FileNotFoundError:
            return False  # it will "SaveAs" the file

    def askToSaveChanges(self):
        if self.getCurrentPreferences()["auto-save"] == True:
            self.saveFile()  # to make sure that the file is saved
            return
        elif type(self.currentFilePath) is str and not self.theFileDiffer(self.currentFilePath):
            return

        result = QMessageBox.question(
            self.window,
            "Pencil",
            "Do you want to save the file?",
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
            QMessageBox.Yes,
        )

        if result == QMessageBox.Yes:
            self.saveFile()
            return True
        elif result == QMessageBox.No:
            return True
        return False

    def show(self):
        self.window.show()

    def exitApp(self):
        self.window.close()
