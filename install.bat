@echo off
setlocal
set "SRC=%~dp0"
echo Starting JewAI Installer from %SRC%
echo %SRC% | findstr /I /C:"JewAI_v5" /C:"JewAI_test" >nul
if not errorlevel 1 (
  if exist "C:\jewai\Tools\installer\install.ps1" (
    echo WARNING: running from TEST COPY. Source at C:\jewai. Agents may be STALE.
    choice /C YN /M "Continue? (N=run from C:\jewai)"
    if errorlevel 2 exit /b 1
  )
)
powershell -NoProfile -ExecutionPolicy Bypass -File "%SRC%Tools\installer\install.ps1"
pause
