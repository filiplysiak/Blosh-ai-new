@echo off
echo ============================================
echo   Creating Gorgias Widget
echo ============================================
echo.
cd /d "%~dp0"
python create_widget.py
echo.
echo ============================================
echo   Done! Check your Gorgias sidebar
echo ============================================
pause

