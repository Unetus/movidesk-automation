@echo off
REM Movidesk Automation - Test Run (Dry Run Mode)

REM Mudar para o diretorio do script
cd /d "%~dp0"

echo ================================================
echo Movidesk Automation - MODO TESTE
echo ================================================
echo.
echo Este modo executa a automacao SEM enviar notificacoes.
echo Use para testar a configuracao e conexao com a API.
echo.

REM Check if virtual environment exists
if not exist venv (
    echo [ERRO] Ambiente virtual nao encontrado!
    echo Execute install.bat primeiro.
    pause
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Garantir que estamos no diretorio correto
cd /d "%~dp0"

REM Run in dry-run mode (single execution)
echo Iniciando em modo teste (execucao unica)...
echo.
python main.py --once --dry-run

pause
