@echo off
chcp 65001 >nul
title Qwen Model Downloader

echo.
echo ============================================================
echo     Qwen LLM / VL Model Downloader
echo     Supports resume - just re-run if disconnected
echo ============================================================
echo.

cd /d "%~dp0"
echo [*] Downloading Qwen models...
echo [*] Models saved to ComfyUI/models/LLM/Qwen-VL/
echo.

python download_qwen_models.py

pause
