@echo off
chcp 65001 >nul
title ComfyUI + Z-Image Turbo + QwenVL 一键安装

echo.
echo ============================================================
echo    ComfyUI + Z-Image Turbo + QwenVL 一键安装
echo    自动下载引擎与模型，支持断点续传
echo ============================================================
echo.

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [缺失] 未检测到 Python，请先安装 Python 3.10 或更高版本
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

where git >nul 2>&1
if %errorlevel% neq 0 (
    echo [缺失] 未检测到 Git，请先安装 Git
    echo 下载地址: https://git-scm.com/download/win
    pause
    exit /b 1
)

echo [OK] Python:
python --version
echo [OK] Git:
git --version
echo.

echo [*] 检查依赖库 huggingface_hub / requests ...
python -c "import huggingface_hub, requests; print('OK')" 2>nul
if %errorlevel% equ 0 (
    echo [OK] 依赖库已就绪
) else (
    echo [*] 正在安装依赖库...
    pip install huggingface_hub requests
    if %errorlevel% neq 0 (
        echo [!] 依赖库安装失败，请手动执行: pip install huggingface_hub requests
    )
)

echo.
echo [*] 开始安装 ComfyUI 与 Z-Image Turbo 模型...
echo.

python "%~dp0scripts\install.py"

echo.
echo ============================================================
echo   安装结束! 之后双击 start.bat 即可开始出图
echo ============================================================
pause
