@echo off
REM Focus Mode On - start the app and open it in your browser.
REM Double-click this file, or run it from a terminal.
setlocal
cd /d "%~dp0"
title Focus Mode On

set "PORT=8000"
set "URL=http://127.0.0.1:%PORT%"

echo.
echo   Focus Mode On
echo   -------------
echo   Starting the server and opening %URL%
echo   (log in with the password from your .env file)
echo   Keep this window open. Press Ctrl+C to stop the app.
echo.

REM Open the default browser a few seconds after the server starts.
start "" /min cmd /c "timeout /t 4 >nul & start %URL%"

REM Run the app. It loads .env automatically for APP_PASSWORD / OPENAI_API_KEY.
python -m uvicorn app.main:app --host 127.0.0.1 --port %PORT%

echo.
echo Server stopped.
pause
endlocal
