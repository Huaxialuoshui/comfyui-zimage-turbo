@echo off
chcp 65001 >nul
title Anima Model Setup

cd /d "%~dp0"

python anima_setup.py
pause
