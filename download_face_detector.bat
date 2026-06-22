@echo off
chcp 65001 >nul
echo.
echo Downloading MediaPipe Face Landmarker model...
echo.

set DEST=%~dp0ComfyUI\models\detection\face_landmarker_v2_with_blendshapes.task

if not exist "%~dp0ComfyUI\models\detection" mkdir "%~dp0ComfyUI\models\detection"

python -c "import urllib.request,os;url='https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/latest/face_landmarker.task';dest=r'%DEST%';print('Downloading...');urllib.request.urlretrieve(url,dest);print('Done:',os.path.getsize(dest)//1024,'KB')"

if %errorlevel% equ 0 (
    echo.
    echo [OK] Face detector model installed!
) else (
    echo.
    echo [FAIL] Download failed. Try manual: https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/latest/face_landmarker.task
    echo        Save as: %DEST%
)
pause
