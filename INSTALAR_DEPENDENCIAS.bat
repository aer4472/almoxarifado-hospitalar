@echo off
color 0A
cls
echo.
echo  ================================================
echo      INSTALAR DEPENDENCIAS DO SISTEMA
echo  ================================================
echo.
echo  Este script vai instalar todas as bibliotecas
echo  necessarias para o sistema funcionar!
echo.
echo  ================================================
echo.
pause

echo.
echo Instalando dependencias...
echo.

pip install -r requirements.txt --break-system-packages

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Tentando sem --break-system-packages...
    pip install -r requirements.txt
)

echo.
echo ================================================
echo  INSTALACAO CONCLUIDA!
echo ================================================
echo.
echo Agora voce pode iniciar o servidor:
echo   cd backend
echo   python app.py
echo.
pause
