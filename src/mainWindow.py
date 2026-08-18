from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QMessageBox, QFileDialog, QApplication, QDialog, QComboBox, QSpinBox
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, QTimer
from PySide6.QtGui import QAction
from config import *
import sys
import json
from pathlib import Path


class MainWindow:
    def __init__(self, preferences=None):
        self.window = self.loadUI()
        self.currentFilePath = None
        self._pendingPreferences = preferences
        self.setHtmlContent()
        self.connectActions()
        self.updateWindowTitle()
        self.autosaveTimer = QTimer()
        self.autosaveTimer.timeout.connect(self.autoSave)
        self.autosaveTimer.stop()
        self.textDirection = "ltr"

    def loadUI(self):
        file = QFile(str(ASSETS[UI_MAIN_WINDOW]))
        loader = QUiLoader()
        mainWindow = loader.load(file)
        file.close()
        mainWindow.showMaximized()
        if not mainWindow:
            QMessageBox.critical(title="Error", message="Couldn't open the main window")
            sys.exit(1)
        return mainWindow

    def updateWindowTitle(self):
        if self.currentFilePath:
            self.window.setWindowTitle(f"Pencil | {self.currentFilePath}")
        else:
            self.window.setWindowTitle("Pencil | untitled")

    def setHtmlContent(self):
        code = None
        with open(ASSETS[HTML_TEXT_EDITOR], mode="r") as file:
            code = file.read()
        widget = self.window.findChild(QWebEngineView, "editorWebEngine")

        if hasattr(self, "_onHtmlLoaded") and self._onHtmlLoaded:
            try:
                widget.loadFinished.disconnect(self._onHtmlLoaded)
            except TypeError:
                pass

        def onLoaded():
            widget.loadFinished.disconnect(onLoaded)
            self.updateDirectionActions()
            if getattr(self, "_pendingPreferences", None):
                self.applyPreferences(self._pendingPreferences)
                self._pendingPreferences = None

        self._onHtmlLoaded = onLoaded
        widget.loadFinished.connect(onLoaded)
        widget.setHtml(code)

    def updateDirectionActions(self):
        widget = self.window.findChild(QWebEngineView, "editorWebEngine")
        widget.page().runJavaScript(
            """
            var ta = document.querySelector('textarea');
            var dir = 'rtl';
            if (ta) {
                dir = ta.getAttribute('dir') || 'rtl';
            }
            dir;
        """,
            self.applyDirectionState,
        )

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
        self.currentFilePath = None
        self.updateWindowTitle()
        self.window.statusBar().showMessage("New file created", 3000)
        self.setHtmlContent()

    def openFile(self):
        filePath, _ = QFileDialog.getOpenFileName(self.window, "Open File", "", "Text Files (*.txt);;All Files (*)")
        if filePath:
            try:
                with open(filePath, mode="r", encoding="utf-8") as file:
                    content = file.read()

                code = None
                with open(ASSETS[HTML_TEXT_EDITOR], mode="r") as file:
                    code = file.read()
                with open(ASSETS[HTML_LTR_HTML if self.textDirection == "ltr" else HTML_RTL_HTML], mode="r") as file:
                    code = f"{file.read()}\n{code}"

                widget = self.window.findChild(QWebEngineView, "editorWebEngine")

                def onLoadFinished(ok):
                    widget.loadFinished.disconnect(onLoadFinished)
                    if ok:
                        jsCode = "var ta = document.getElementById('editor');"
                        jsCode += f"ta.value = {json.dumps(content)};"
                        jsCode += "updateLineNumbers();"
                        jsCode += "highlightCurrentLine();"
                        widget.page().runJavaScript(jsCode)
                    self.updateDirectionActions()
                    self.window.statusBar().showMessage(f"Opened: {filePath}", 3000)

                widget.loadFinished.connect(onLoadFinished)
                widget.setHtml(code)
                self.currentFilePath = filePath
                self.updateWindowTitle()
            except Exception as e:
                QMessageBox.critical(self.window, "Error Opening File", f"Could not open file:\n{filePath}\n\n{e}")

    def saveFile(self):
        if self.currentFilePath:
            self.saveToPath(self.currentFilePath)
        else:
            filePath, _ = QFileDialog.getSaveFileName(self.window, "Save File", "", "HTML Files (*.html *.htm);;All Files (*)")
            if filePath:
                self.saveToPath(filePath)

    def saveToPath(self, filePath):
        widget = self.window.findChild(QWebEngineView, "editorWebEngine")

        def saveText(text):
            try:
                with open(filePath, mode="w", encoding="utf-8") as file:
                    file.write(text)
                self.currentFilePath = filePath
                self.updateWindowTitle()
                self.window.statusBar().showMessage(f"Saved: {filePath}", 3000)
            except Exception as e:
                QMessageBox.critical(self.window, "Error Saving File", f"Could not save file:\n{filePath}\n\n{e}")

        widget.page().runJavaScript("document.querySelector('textarea').value", saveText)

    def exitApp(self):
        self.window.close()

    def undoEdit(self):
        widget = self.window.findChild(QWebEngineView, "editorWebEngine")
        widget.page().runJavaScript("var ta = document.querySelector('textarea'); ta.focus(); document.execCommand('undo');")

    def redoEdit(self):
        widget = self.window.findChild(QWebEngineView, "editorWebEngine")
        widget.page().runJavaScript("var ta = document.querySelector('textarea'); ta.focus(); document.execCommand('redo');")

    def cutEdit(self):
        widget = self.window.findChild(QWebEngineView, "editorWebEngine")
        widget.page().runJavaScript("var ta = document.querySelector('textarea'); ta.focus(); document.execCommand('cut');")

    def copyEdit(self):
        widget = self.window.findChild(QWebEngineView, "editorWebEngine")
        widget.page().runJavaScript("var ta = document.querySelector('textarea'); ta.focus(); document.execCommand('copy');")

    def pasteEdit(self):
        widget = self.window.findChild(QWebEngineView, "editorWebEngine")
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        if text:
            jsCode = f"var ta = document.querySelector('textarea'); ta.value += {json.dumps(text)}; ta.dispatchEvent(new Event('input'));"
            widget.page().runJavaScript(jsCode)

    def setRtl(self):
        self.textDirection = "rtl"
        widget = self.window.findChild(QWebEngineView, "editorWebEngine")
        widget.page().runJavaScript("var container = document.getElementById('editor-container'); container.style.direction = 'rtl';")
        self.window.findChild(QAction, "actionRTL").setEnabled(False)
        self.window.findChild(QAction, "actionLTR").setEnabled(True)
        if not getattr(self, "_pendingPreferences", None):
            savePreferences(self.getCurrentPreferences())

    def setLtr(self):
        self.textDirection = "ltr"
        widget = self.window.findChild(QWebEngineView, "editorWebEngine")
        widget.page().runJavaScript("var container = document.getElementById('editor-container'); container.style.direction = 'ltr';")
        self.window.findChild(QAction, "actionLTR").setEnabled(False)
        self.window.findChild(QAction, "actionRTL").setEnabled(True)
        if not getattr(self, "_pendingPreferences", None):
            savePreferences(self.getCurrentPreferences())

    def toggleAutoSave(self, checked):
        if checked:
            self.autosaveTimer.start(50)
            self.window.statusBar().showMessage("Auto Save enabled", 3000)
        else:
            self.autosaveTimer.stop()
            self.window.statusBar().showMessage("Auto Save disabled", 3000)
        savePreferences(self.getCurrentPreferences())

    def autoSave(self):
        if self.currentFilePath:
            self.saveFile()

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
        file.close()
        if dialog:
            self.initPreferencesDialog(dialog)
            result = dialog.exec()
            if result == QDialog.Accepted:
                preferences = self.readPreferencesFromDialog(dialog)
                self.applyPreferences(preferences)
                savePreferences(preferences)
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
        theme_key = theme_map.get(theme, STYLE_DARK_THEME)
        self.setColorTheme(theme_key)

        direction = preferences.get("text-direction", "ltr")
        autoSave = preferences.get("auto-save", False)

        action = self.window.findChild(QAction, "actionAutoSave")
        if action:
            action.setChecked(autoSave)

        self._pendingPreferences = preferences

        widget = self.window.findChild(QWebEngineView, "editorWebEngine")
        if widget:
            if direction == "rtl":
                self.setRtl()
            else:
                self.setLtr()

            if hasattr(widget, "page"):
                self._applyPendingPreferences()

    def _applyPendingPreferences(self):
        preferences = getattr(self, "_pendingPreferences", None)
        if not preferences:
            return
        
        self._pendingPreferences = None
        fontSize = int(preferences.get("font-size", 13))
        self.applyFontSize(fontSize)
        fontFamily = preferences.get("font-family", "Arial")
        self.applyFontFamily(fontFamily)
        savePreferences(self.getCurrentPreferences())

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
        widget = self.window.findChild(QWebEngineView, "editorWebEngine")
        jsCode = f"var editor = document.getElementById('editor'); if (editor) editor.style.fontSize = '{size}px'; var ln = document.getElementById('lineNumbers'); if (ln) ln.style.fontSize = '{size}px';"
        widget.page().runJavaScript(jsCode)

    def applyFontFamily(self, family):
        self._currentFontFamily = family
        widget = self.window.findChild(QWebEngineView, "editorWebEngine")
        jsCode = f"var editor = document.getElementById('editor'); if (editor) editor.style.fontFamily = '{family}'; var ln = document.getElementById('lineNumbers'); if (ln) ln.style.fontFamily = '{family}';"
        widget.page().runJavaScript(jsCode)

    def getCurrentPreferences(self):
        preferences = {}
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
        preferences["auto-save"] = action.isChecked() if action else False
        return preferences

    def toggleFullScreen(self):
        if self.window.isFullScreen():
            self.window.showMaximized()
        else:
            self.window.showFullScreen()

    def show(self):
        self.window.show()
