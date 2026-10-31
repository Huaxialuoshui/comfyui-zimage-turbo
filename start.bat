@echo off
chcp 65001 >nul
title ComfyUI + Z-Image / Anima / SeFi / H3 / Qwen-Image 2.1

echo.
echo ============================================================
echo     ComfyUI + Z-Image / Anima / SeFi / H3 / Qwen-Image 2.1
echo     DanbooruSearch: https://huggingface.co/spaces/SAkizuki/DanbooruSearch
echo ============================================================
echo.

set COMFYUI_DIR=%~dp0ComfyUI
set COMFYUI_PYTHON=%COMFYUI_DIR%\.venv\Scripts\python.exe

if not exist "%COMFYUI_DIR%\main.py" (
    echo [!] ComfyUI not found! Run setup.bat first.
    pause
    exit /b 1
)

if not exist "%COMFYUI_PYTHON%" set COMFYUI_PYTHON=python

:: Open DanbooruSearch prompt helper
echo [*] Opening DanbooruSearch prompt helper...
start "" "https://huggingface.co/spaces/SAkizuki/DanbooruSearch"

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
"%COMFYUI_PYTHON%" main.py --listen 127.0.0.1 --port 8188

if %errorlevel% neq 0 (
    echo.
    echo [!] ComfyUI failed (code: %errorlevel%)
    pause
)


