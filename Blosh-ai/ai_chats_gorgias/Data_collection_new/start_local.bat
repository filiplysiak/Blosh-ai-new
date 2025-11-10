@echo off
echo ============================================
echo   Starting Gorgias Widget API (Local)
echo ============================================
echo.
echo IMPORTANT: Make sure you have set environment variables:
echo   - OPENAI_API_KEY
echo   - GORGIAS_AUTH
echo   - GORGIAS_BASE_URL
echo.
echo Server will run on: http://localhost:5000
echo.
echo Keep this window open!
echo Press Ctrl+C to stop the server
echo.
echo ============================================
echo.

cd /d "%~dp0"
python API_widget_server.py
pause

