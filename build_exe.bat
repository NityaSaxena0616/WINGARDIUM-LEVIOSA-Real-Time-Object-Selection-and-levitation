@echo off
title Wingardium Leviosa - Build Executable
echo ===============================================================================
echo ✦ Building Wingardium Leviosa Executable ✦
echo ===============================================================================
echo.

cd /d "%~dp0"
python -m PyInstaller --noconfirm --onedir --windowed --add-data "assets;assets" main.py --name "WingardiumLeviosa"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo SUCCESS! Executable created in folder: dist\WingardiumLeviosa\WingardiumLeviosa.exe
    pause
) else (
    echo.
    echo [ERROR] PyInstaller build failed.
    pause
)
