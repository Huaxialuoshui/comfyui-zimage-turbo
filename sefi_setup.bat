@echo off
chcp 65001 >nul
title SeFi-Image Model Setup

cd /d "%~dp0"

python sefi_setup.py
pause
