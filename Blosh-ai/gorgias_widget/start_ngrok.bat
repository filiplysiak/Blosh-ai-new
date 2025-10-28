@echo off
echo ============================================
echo   Starting ngrok tunnel...
echo ============================================
echo.
echo Server is running on: http://localhost:5000
echo.
echo Starting ngrok (this will create a public URL)...
echo.
cd /d "%~dp0"
ngrok.exe http 5000

