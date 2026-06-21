@echo off
chcp 65001 >nul
title Image Resizer Tool

echo.
echo ============================================================
echo     Image Resizer Tool - Z-Image Turbo
echo ============================================================
echo.

cd /d "%~dp0"

echo [*] Starting Image Resizer...
echo [*] Open: http://127.0.0.1:8199
echo.

python image_resizer.py

pause
