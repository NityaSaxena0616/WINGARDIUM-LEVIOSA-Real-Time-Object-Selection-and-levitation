@echo off
title Wingardium Leviosa - Real-Time Magic Vision System
echo ===============================================================================
echo ✦ WINGARDIUM LEVIOSA ✦ Real-Time Computer Vision Magic System
echo ===============================================================================
echo Starting application, please wait...
echo.

cd /d "%~dp0"
py -3.11 main.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Application closed with error code %ERRORLEVEL%.
    pause
)
