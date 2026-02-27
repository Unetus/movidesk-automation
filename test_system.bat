@echo off
REM Movidesk Automation - System Test

REM Mudar para o diretorio do script
cd /d "%~dp0"

echo ================================================
echo Movidesk Automation - Teste de Sistema
echo ================================================
echo.
echo Este script testa:
echo   - Configuracao (credentials)
echo   - Conexao com API Movidesk
echo   - Conexao com Groq AI
echo   - Conexao SMTP (email)
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

REM Run system test
python test_system.py

pause
