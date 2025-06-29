@echo off
setlocal EnableDelayedExpansion

rem ───────── 1. ПАРАМЕТРЫ ────────────────────────────────────────
set "SCRIPT=overlay.py"
set "ICON=app.ico"
set "NAME=OverlayTool"

rem ---- timestamp YYYYMMDD_HHMMSS  (без WMIC) --------------------
for /f "tokens=1-3 delims=/:. " %%a in ("%date% %time%") do (
    set "YYYY=%%c"
    set "MM=%%b"
    set "DD=%%a"
    set "HH=%%d"
    set "NN=%%e"
    set "SS=%%f"
)
if "!HH:~1!"=="" set "HH=0!HH!"   &:: ведёт 0-7 -> 00-07
set "STAMP=!YYYY!!MM!!DD!_!HH!!NN!!SS!"
set "OUT=%NAME%_!STAMP!.exe"

rem ───────── 2. ПРОВЕРКИ ФАЙЛОВ ───────────────────────────────────
if not exist "%SCRIPT%" ( echo [ERROR] %SCRIPT% не найден & goto :fail )
if not exist "%ICON%"   ( echo [ERROR] %ICON%   не найден & goto :fail )

rem ───────── 3. ICO: опциональная проверка -----------------------
where powershell >nul 2>&1
if %errorlevel%==0 (
  powershell -NoLogo -NoProfile -Command ^
    "try {Add-Type -AssemblyName System.Drawing -ErrorAction Stop;" ^
    "$ico=[System.Drawing.Icon]::ExtractAssociatedIcon('%ICON%');" ^
    "if(!$ico){exit 2}; if($ico.Width -lt 256 -or $ico.Height -lt 256){exit 1}}" ^
    "catch{exit 2}"
  if %errorlevel%==1 (
    echo [WARN ] В %ICON% нет слоя 256×256 — крупные значки панели задач могут быть «пустые».
  )
)

rem ───────── 4. PIP / PYINSTALLER --------------------------------
python -m pip install --quiet --upgrade pip pyinstaller
if errorlevel 1 ( echo [ERROR] pip / PyInstaller не установились & goto :fail )

rem ───────── 5. СБОРКА ------------------------------------------
if exist build rd /s /q build
if exist dist  rd /s /q dist

pyinstaller --noconfirm --clean --onefile --windowed ^
            --name "%NAME%" ^
            --icon "%ICON%" ^
            "%SCRIPT%"
if errorlevel 1 goto :fail

if not exist "dist\%NAME%.exe" (
    echo [ERROR] PyInstaller не создал exe
    goto :fail
)

move /y "dist\%NAME%.exe" "%OUT%" >nul

echo.
echo [OK] Готово! exe: %OUT%
echo.

rem ───────── 6. Обновить кэш значков Explorer (если есть PowerShell) ----
where powershell >nul 2>&1
if %errorlevel%==0 (
  powershell -NoLogo -Command "Start-Process ie4uinit.exe -ArgumentList '-show' -NoNewWindow -Wait"
)

pause
exit /b 0

:fail
echo.
echo Сборка прервана.
pause
exit /b 1
