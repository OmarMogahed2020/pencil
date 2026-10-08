# Pencil

A lightweight, cross-platform text editor built with Python and PySide6.

## Overview

Pencil is a minimal text editor designed for simplicity and speed. It provides
essential editing features without unnecessary complexity, making it suitable
for quick note-taking, light scripting, and everyday text editing tasks.

## Features

- **File management** — Open, edit, and save plain text files
- **Auto-save** — Optional automatic saving at configurable intervals
- **File watching** — Automatic refresh when the open file changes on disk
- **Multi-theme support** — 12 built-in color themes (dark and light variants)
- **RTL/LTR support** — Full right-to-left and left-to-right text direction, especially for arabic
- **Line numbers** — Synchronized line number display
- **Whitespace visualization** — Spaces and tabs are displayed as dots or an arrow in case of a tab
- **Font customization** — Configurable font family and size
- **Unsaved changes protection** — Prompts to save before closing
- **Persistent preferences** — Settings stored across sessions

## Requirements

- Python 3.10 or later
- PySide6

## Installation

Clone the repository and install dependencies:

```bash
cd pencil
python3 -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate
pip install -r requirements.txt