@echo off
chcp 65001 >nul
title Qwen3-VL-2B-Instruct Download

cd /d "%~dp0"

python qwen3vl_download.py
pause
