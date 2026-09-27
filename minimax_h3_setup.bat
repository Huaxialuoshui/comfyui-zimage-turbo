@echo off
chcp 65001 >nul
title MiniMax H3 模型下载（魔搭源）

echo ============================================================
echo   MiniMax H3 模型下载
echo   数据源: 魔搭 Comfy-Org/MiniMax-H3（国内直连）
echo   FL2VA 全家桶约 42.5 GB；加 --ref2va 再下 20 GB
echo ============================================================
echo.

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] 未找到 Python，请先安装 Python 3.10+
    pause
    exit /b 1
)

echo [*] 开始下载（支持断点续传，中断后重新双击本脚本即可继续）...
echo.

python "%~dp0scripts\install_minimax_h3.py" %*

echo.
echo ============================================================
echo   下载结束。若提示未完成，请重新运行本脚本续传。
echo ============================================================
pause
