# NIXBI App Launcher

A lightweight, customizable application launcher for Windows with a modern dark UI.

## Features
- Custom frameless window with draggable titlebar
- 5 customizable shortcut buttons with add/remove controls
- App library and packs with launch delays
- 5 built-in color themes (Catppuccin Mocha, Dark Green, Dark Blue, Dark Red, Gray)
- Auto-startup with Windows
- Request administrator privileges on demand
- Portable - single exe file

## Download
-https://github.com/NiXBiofc/NIXBI-App-Launcher
-https://t.me/NiXBi_ofc_releases

## Requirements
- Windows 10/11
- No installation needed

## Build from source
```bash
pip install PyQt6 pyinstaller
pyinstaller --onefile --windowed --icon=icon.ico --name=NIXBI_Launcher --hidden-import=PyQt6 launcher.py
