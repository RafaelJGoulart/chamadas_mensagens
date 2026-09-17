@echo off
setlocal

title Sistema de Chamadas - Desenvolvimento

cd /d "%~dp0"

where python >nul 2>&1

if %errorlevel% neq 0 (
    echo.
    echo ERRO: Python nao foi encontrado no PATH do computador.
    echo.
    pause
    exit /b 1
)

python "app\app.py"

pause