@echo off
REM Script para debug - mostra campos brutos da API do Movidesk

echo ============================================================
echo   DEBUG - Campos da API Movidesk
echo ============================================================
echo.
echo Este script mostra os campos brutos retornados pela API
echo para identificar qual campo contem a "Previsao de solucao"
echo.
echo Escolha uma opcao:
echo   1. Ver campos selecionados (com $select)
echo   2. Ver TODOS os campos (sem filtro)
echo.

set /p option="Digite 1 ou 2: "

REM Check if virtual environment exists
if not exist venv (
    echo [ERRO] Ambiente virtual nao encontrado!
    echo Execute install.bat primeiro.
    pause
    exit /b 1
)

REM Check if .env exists
if not exist .env (
    echo [ERRO] Arquivo .env nao encontrado!
    echo Execute install.bat primeiro.
    pause
    exit /b 1
)

REM Activate virtual environment and run
call venv\Scripts\activate.bat

echo.
echo Executando script de debug...
echo.

if "%option%"=="1" (
    python debug_ticket_fields.py
) else if "%option%"=="2" (
    python debug_all_fields.py
) else (
    echo Opcao invalida!
    pause
    exit /b 1
)

echo.
echo ============================================================
pause
