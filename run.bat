@echo off
REM Movidesk Automation - Menu Principal

REM Mudar para o diretorio do script
cd /d "%~dp0"

:MENU
cls
echo ============================================================
echo              MOVIDESK AUTOMATION - MENU
echo ============================================================
echo.
echo   1. Relatorio Diario com IA (recomendado)
echo   2. Testar conexoes (SMTP, API, Groq)
echo   3. Ver configuracoes
echo   4. Sair
echo.
echo ============================================================
echo.
echo O Relatorio Diario inclui:
echo   - Tickets novos (ultimas 24h)
echo   - Tickets vencidos (SLA expirado)
echo   - Tickets vencendo (proximos 2 dias)
echo   - Resumos gerados por IA para cada ticket
echo.
echo ============================================================

set /p OPCAO="Escolha uma opcao (1-4): "

if "%OPCAO%"=="1" goto RELATORIO_DIARIO
if "%OPCAO%"=="2" goto TESTAR_CONEXOES
if "%OPCAO%"=="3" goto VER_CONFIG
if "%OPCAO%"=="4" goto SAIR

echo.
echo Opcao invalida! Pressione qualquer tecla para continuar...
pause >nul
goto MENU

:RELATORIO_DIARIO
cls
echo ============================================================
echo   RELATORIO DIARIO COM RESUMOS DE IA
echo ============================================================
echo.
echo Este modo gera um relatorio completo com:
echo   - Tickets novos (ultimas 24 horas)
echo   - Tickets vencidos (SLA expirado)
echo   - Tickets proximos de vencer (proximos 2 dias)
echo   - Resumos gerados por IA para cada ticket (Groq AI)
echo.
echo O relatorio sera enviado por email.
echo O processamento e feito em lotes para respeitar limites.
echo.

REM Check if virtual environment exists
if not exist venv (
    echo [ERRO] Ambiente virtual nao encontrado!
    echo Execute install.bat primeiro.
    pause
    goto MENU
)

REM Check if .env exists
if not exist .env (
    echo [ERRO] Arquivo .env nao encontrado!
    echo Copie .env.example para .env e preencha suas credenciais.
    pause
    goto MENU
)

REM Activate virtual environment
call venv\Scripts\activate.bat
cd /d "%~dp0"

echo Gerando relatorio diario com IA...
echo.
python main.py --once --mode daily-report

call venv\Scripts\deactivate.bat

echo.
echo ============================================================
echo Pressione qualquer tecla para voltar ao menu...
pause >nul
goto MENU

:TESTAR_CONEXOES
cls
echo ============================================================
echo   TESTAR CONEXOES
echo ============================================================
echo.

REM Check if virtual environment exists
if not exist venv (
    echo [ERRO] Ambiente virtual nao encontrado!
    echo Execute install.bat primeiro.
    pause
    goto MENU
)

REM Activate virtual environment
call venv\Scripts\activate.bat
cd /d "%~dp0"

echo Executando testes de conexao...
echo.
python test_system.py

call venv\Scripts\deactivate.bat

echo.
echo ============================================================
echo Pressione qualquer tecla para voltar ao menu...
pause >nul
goto MENU

:VER_CONFIG
cls
echo ============================================================
echo   CONFIGURACOES ATUAIS
echo ============================================================
echo.

if not exist .env (
    echo [ERRO] Arquivo .env nao encontrado!
    pause
    goto MENU
)

if not exist config.yaml (
    echo [ERRO] Arquivo config.yaml nao encontrado!
    pause
    goto MENU
)

echo --- Arquivo .env ---
echo.
type .env | findstr /V "PASSWORD TOKEN API_KEY"
echo.
echo (Credenciais ocultas por seguranca)
echo.
echo.
echo --- Principais configuracoes (config.yaml) ---
echo.
findstr /C:"ticket_limit" /C:"business_hours" /C:"poll_interval" /C:"model:" config.yaml
echo.
echo ============================================================
echo.
echo Para ver todas as configuracoes, abra os arquivos:
echo   - .env (credenciais)
echo   - config.yaml (parametros)
echo.
echo Pressione qualquer tecla para voltar ao menu...
pause >nul
goto MENU

:SAIR
cls
echo.
echo Encerrando Movidesk Automation...
echo.
exit /b 0
