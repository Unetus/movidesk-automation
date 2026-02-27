@echo off
REM Movidesk Automation - Installation Script

REM Mudar para o diretorio do script
cd /d "%~dp0"

echo ================================================
echo Movidesk Automation - Instalador
echo ================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado!
    echo Por favor, instale Python 3.10 ou superior: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [OK] Python encontrado
python --version
echo.

REM Create virtual environment
echo [1/4] Criando ambiente virtual...
if exist venv (
    echo Ambiente virtual ja existe, pulando...
) else (
    python -m venv venv
    if errorlevel 1 (
        echo [ERRO] Falha ao criar ambiente virtual
        pause
        exit /b 1
    )
    echo [OK] Ambiente virtual criado
)
echo.

REM Activate virtual environment and install dependencies
echo [2/4] Instalando dependencias...
call venv\Scripts\activate.bat

REM Garantir que estamos no diretorio correto
cd /d "%~dp0"

python -m pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERRO] Falha ao instalar dependencias
    pause
    exit /b 1
)
echo [OK] Dependencias instaladas
echo.

REM Install PyYAML if not in requirements
pip install pyyaml
echo.

REM Create directories
echo [3/4] Criando diretorios...
if not exist data mkdir data
if not exist logs mkdir logs
echo [OK] Diretorios criados
echo.

REM Check for .env file
echo [4/4] Verificando configuracao...
if not exist .env (
    echo [AVISO] Arquivo .env nao encontrado!
    echo.
    echo IMPORTANTE: Copie .env.example para .env e preencha suas credenciais:
    echo   1. MOVIDESK_TOKEN
    echo   2. GROQ_API_KEY
    echo   3. EMAIL_FROM, EMAIL_PASSWORD, EMAIL_TO
    echo   4. MOVIDESK_AGENT_EMAIL
    echo.
    copy .env.example .env
    echo Arquivo .env criado. Por favor, edite-o com suas credenciais.
) else (
    echo [OK] Arquivo .env encontrado
)
echo.

echo ================================================
echo Instalacao concluida!
echo ================================================
echo.
echo Proximos passos:
echo   1. Edite o arquivo .env com suas credenciais
echo   2. Ajuste config.yaml se necessario (filtros, intervalos, etc)
echo   3. Execute run.bat para iniciar a automacao
echo.
pause
