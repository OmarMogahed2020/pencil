from pathlib import Path
import json
import os

baseDir = Path(__file__).resolve().parent.parent

ICON_APP_ICON = "APP ICON"

UI_MAIN_WINDOW = "UI MAIN WINDOW"
UI_PREFERENCES = "UI PREFERENCES"

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
    ICON_APP_ICON: baseDir / "assets" / "icons" / "pencilIcon.png",
}


def loadPreferences():
    path = ASSETS[DATA_PREFERENCES_JSON]

    if os.path.exists(path) and os.path.getsize(path) > 0:
        try:
            with open(path, mode="r") as file:
                return json.load(file)
        except json.JSONDecodeError:
            pass

    with open(path, mode="w") as file:
        file.write(DEFAULT_PREFERENCES)
    with open(path, mode="r") as file:
        return json.load(file)


def savePreferences(preferences):
    path = ASSETS[DATA_PREFERENCES_JSON]
    with open(path, mode="w") as file:
        json.dump(preferences, file, indent=4)
