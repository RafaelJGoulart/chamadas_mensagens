@echo off
setlocal

title Sistema de Chamadas

set "SISTEMA_DIR=%~dp0"
set "PENDRIVE_DIR=%SISTEMA_DIR%.."
set "PYTHON_EXE=%PENDRIVE_DIR%\Python\python.exe"

if not exist "%PYTHON_EXE%" (
    echo.
    echo ERRO: Python portatil nao encontrado.
    echo.
    echo Caminho procurado:
    echo %PYTHON_EXE%
    echo.
    pause
    exit /b 1
)

cd /d "%SISTEMA_DIR%"

if not exist "%SISTEMA_DIR%app\app.py" (
    echo.
    echo ERRO: app\app.py nao encontrado em:
    echo %SISTEMA_DIR%app\app.py
    echo.
    echo Copie a pasta SistemaChamadas inteira para o pendrive.
    echo.
    pause
    exit /b 1
)

if not exist "%SISTEMA_DIR%app\config.py" (
    echo.
    echo ERRO: copia incompleta no pendrive - falta app\config.py
    echo.
    echo Apague D:\SistemaChamadas e copie a pasta inteira de novo.
    echo.
    pause
    exit /b 1
)

rem Garante que "from config import ..." funcione em qualquer Python portatil
set "PYTHONPATH=%SISTEMA_DIR%app"

echo.
echo Iniciando o Sistema de Chamadas...
echo Servidor: http://127.0.0.1:5000
echo Para encerrar: pressione CTRL+C nesta janela.
echo.

start "" powershell -NoProfile -WindowStyle Hidden -Command "Start-Sleep -Seconds 3; Start-Process 'http://127.0.0.1:5000'"

"%PYTHON_EXE%" "app\app.py"

echo.
echo O sistema foi encerrado.
pause
exit /b 0