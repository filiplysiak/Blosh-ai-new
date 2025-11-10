@echo off
echo ============================================
echo   Starting ngrok tunnel
echo ============================================
echo.
echo IMPORTANT: 
echo 1. Make sure the API server is running first!
echo    (Run start_local.bat in another terminal)
echo.
echo 2. Copy the HTTPS URL that appears below
echo    Example: https://abc123.ngrok.io
echo.
echo 3. Use that URL in your Gorgias widget configuration
echo.
echo ============================================
echo.

REM Check if ngrok exists in current directory
if exist ngrok.exe (
    echo Found ngrok.exe in current directory
    ngrok.exe http 5000
) else if exist ..\..\..\ngrok.exe (
    echo Found ngrok.exe in parent directory
    ..\..\..\ngrok.exe http 5000
) else (
    echo ERROR: ngrok.exe not found!
    echo.
    echo Please download ngrok:
    echo 1. Go to: https://ngrok.com/download
    echo 2. Download ngrok for Windows
    echo 3. Extract ngrok.exe to this folder
    echo.
    pause
    exit /b 1
)

pause

