from pathlib import Path
import json
import os

baseDir = Path(__file__).resolve().parent.parent

UI_MAIN_WINDOW = "ui main window"
UI_PREFERENCES = "ui preferences"

HTML_TEXT_EDITOR = "html text editor"
HTML_RTL_HTML = "html rtl html"
HTML_LTR_HTML = "html ltr html"

STYLE_DARK_THEME = "STYLE DARK THEME"
STYLE_LIGHT_THEME = "STYLE LIGHT THEME"
STYLE_DARK_MONOKAI = "STYLE DARK MONOKAI"
STYLE_DARK_DRACULA = "STYLE DARK DRACULA"
STYLE_DARK_NORD = "STYLE DARK NORD"
STYLE_DARK_SOLARIZED = "STYLE DARK SOLARIZED"
STYLE_DARK_GITHUB = "STYLE DARK GITHUB"
STYLE_LIGHT_MONOKAI = "STYLE LIGHT MONOKAI"
STYLE_LIGHT_DRACULA = "STYLE LIGHT DRACULA"
STYLE_LIGHT_NORD = "STYLE LIGHT NORD"
STYLE_LIGHT_SOLARIZED = "STYLE LIGHT SOLARIZED"
STYLE_LIGHT_GITHUB = "STYLE LIGHT GITHUB"

DATA_PREFERENCES_JSON = "DATA PREFERENCES JSON"

DEFAULT_PREFERENCES = """{
    "auto-save": false,
    "theme": "dark-theme",
    "font-size": "13",
    "font-family": "Arial",
    "text-direction": "ltr"
}"""

ASSETS = {
    UI_MAIN_WINDOW: baseDir / "ui" / "mainWindow.ui",
    UI_PREFERENCES: baseDir / "ui" / "preferencesWindow.ui",
    HTML_TEXT_EDITOR: baseDir / "assets" / "html" / "textEditor.html",
    HTML_RTL_HTML: baseDir / "assets" / "html" / "rtlHtml.html",
    HTML_LTR_HTML: baseDir / "assets" / "html" / "ltrHtml.html",
    STYLE_DARK_THEME: baseDir / "assets" / "styles" / "dark-theme.qss",
    STYLE_LIGHT_THEME: baseDir / "assets" / "styles" / "light-theme.qss",
    STYLE_DARK_MONOKAI: baseDir / "assets" / "styles" / "dark-monokai-theme.qss",
    STYLE_DARK_DRACULA: baseDir / "assets" / "styles" / "dark-dracula-theme.qss",
    STYLE_DARK_NORD: baseDir / "assets" / "styles" / "dark-nord-theme.qss",
    STYLE_DARK_SOLARIZED: baseDir / "assets" / "styles" / "dark-solarized-theme.qss",
    STYLE_DARK_GITHUB: baseDir / "assets" / "styles" / "dark-github-theme.qss",
    STYLE_LIGHT_MONOKAI: baseDir / "assets" / "styles" / "light-monokai-theme.qss",
    STYLE_LIGHT_DRACULA: baseDir / "assets" / "styles" / "light-dracula-theme.qss",
    STYLE_LIGHT_NORD: baseDir / "assets" / "styles" / "light-nord-theme.qss",
    STYLE_LIGHT_SOLARIZED: baseDir / "assets" / "styles" / "light-solarized-theme.qss",
    STYLE_LIGHT_GITHUB: baseDir / "assets" / "styles" / "light-github-theme.qss",
    DATA_PREFERENCES_JSON: baseDir / "data" / "preferences.json",
}

def loadPreferences():
    path = ASSETS[DATA_PREFERENCES_JSON]

    if os.path.exists(path) and os.path.getsize(path) > 0:
        with open(path, mode="r") as file:
            return json.load(file)

    # if the file is empty or not found
    writeMode = "r" if os.path.exists(path) and os.path.getsize(path) else "w" if os.path.exists(path) else "x"

    with open(path, mode=writeMode) as file:
        file.write(DEFAULT_PREFERENCES)
    with open(path, mode="r") as file:
        return json.load(file)


def savePreferences(preferences):
    path = ASSETS[DATA_PREFERENCES_JSON]
    with open(path, mode="w") as file:
        json.dump(preferences, file, indent=4)
