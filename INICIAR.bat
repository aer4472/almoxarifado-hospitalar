@echo off
color 0A
cls
echo.
echo ========================================
echo   ALMOXARIFADO HOSPITALAR V4.0
echo ========================================
echo.
echo   Iniciando servidor...
echo.
cd backend
start http://localhost:5000
python app.py
