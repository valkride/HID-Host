@echo off
echo Installing PyInstaller...
pip install pyinstaller

echo Building executable...
pyinstaller --onefile --console --add-data "hid-config.json;." --hidden-import hid --hidden-import psutil --hidden-import GPUtil --hidden-import pycaw.pycaw --hidden-import comtypes --hidden-import win32pdh hid-host.py

echo Build complete!
pause
