@echo off
chcp 65001 >nul
title ComfyUI + Z-Image Turbo

echo.
echo ============================================================
echo     ComfyUI + Z-Image Turbo
echo ============================================================
echo.

set COMFYUI_DIR=%~dp0ComfyUI

if not exist "%COMFYUI_DIR%\main.py" (
    echo [!] ComfyUI not found! Run setup.bat first.
    pause
    exit /b 1
)

:: Fix OMP conflict
set KMP_DUPLICATE_LIB_OK=TRUE

:: Launch Image Resizer in a separate window
echo [*] Starting Image Resizer...
start "Image Resizer" /min cmd /c "cd /d %~dp0 && python image_resizer.py"

:: Wait a moment for resizer to start
timeout /t 2 /nobreak >nul

echo [*] Starting ComfyUI...
echo [*] ComfyUI: http://127.0.0.1:8188
echo [*] Image Resizer: http://127.0.0.1:8199
echo.

cd /d "%COMFYUI_DIR%"
python main.py --listen 127.0.0.1 --port 8188

if %errorlevel% neq 0 (
    echo.
    echo [!] ComfyUI failed (code: %errorlevel%)
    pause
)
