@echo off
chcp 65001 >nul
title ComfyUI + Z-Image Turbo + QwenVL ??? - ????

echo.
echo ============================================================
echo    ComfyUI + Z-Image Turbo + QwenVL ???
echo    ??????
echo ============================================================
echo.

:: ?? Python
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [??] ??? Python, ???? Python 3.10+
    echo ????: https://www.python.org/downloads/
    pause
    exit /b 1
)

:: ?? Git
where git >nul 2>&1
if %errorlevel% neq 0 (
    echo [??] ??? Git, ???? Git
    echo ????: https://git-scm.com/download/win
    pause
    exit /b 1
)

echo [OK] Python: 
python --version
echo [OK] Git: 
git --version
echo.

:: ?????????
echo [*] ??????...
python -c "import huggingface_hub, requests; print('huggingface_hub OK, requests OK')" 2>nul
if %errorlevel% equ 0 (
    echo [OK] ??????????
) else (
    echo [*] ??????...
    pip install huggingface_hub requests
    if %errorlevel% neq 0 (
        echo [!] ???????????...
    )
)

echo.
echo [*] ???? ComfyUI ???...
echo.

:: ?????? (??????)
python "%~dp0scripts\install.py"

echo.
echo ============================================================
echo   ????! ??????...
echo ============================================================
pause
