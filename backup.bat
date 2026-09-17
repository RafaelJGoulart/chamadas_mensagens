@echo off
setlocal

title Sistema de Chamadas - Backup

set "SISTEMA_DIR=%~dp0"

if not exist "%SISTEMA_DIR%data\sistema.db" (
    echo.
    echo ERRO: banco de dados nao encontrado.
    echo Caminho esperado:
    echo %SISTEMA_DIR%data\sistema.db
    echo.
    echo Inicie o sistema pelo menos uma vez para criar o banco.
    echo.
    pause
    exit /b 1
)

if not exist "%SISTEMA_DIR%backups" mkdir "%SISTEMA_DIR%backups"

for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyy-MM-dd_HHmmss"') do set "DATAHORA=%%i"

set "DESTINO=%SISTEMA_DIR%backups\sistema_%DATAHORA%.db"

copy /y "%SISTEMA_DIR%data\sistema.db" "%DESTINO%" >nul

if %errorlevel% neq 0 (
    echo.
    echo ERRO: falha ao copiar o banco de dados.
    echo.
    pause
    exit /b 1
)

echo.
echo Backup criado com sucesso.
echo Arquivo: backups\sistema_%DATAHORA%.db
echo.
pause