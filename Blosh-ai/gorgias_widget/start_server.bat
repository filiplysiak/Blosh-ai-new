@echo off
echo ============================================
echo   Starting Gorgias Widget Server
echo ============================================
echo.
echo Server will run on: http://localhost:5000
echo Keep this window open!
echo.
cd /d "%~dp0"
python widget_server.py
pause

