@echo off
REM Script de Inicialização Git e Verificação de Segurança
echo ================================================
echo   Git Setup e Verificacao de Seguranca
echo ================================================
echo.

REM Verificar se Git está instalado
git --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Git nao encontrado! Instale em: https://git-scm.com/download/win
    pause
    exit /b 1
)

echo [OK] Git encontrado
echo.

REM Verificar se já é um repositório Git
if exist ".git" (
    echo [AVISO] Este diretorio ja e um repositorio Git
    echo.
    choice /C SN /M "Deseja continuar mesmo assim?"
    if errorlevel 2 exit /b 0
)

echo ================================================
echo   Verificando seguranca...
echo ================================================
echo.

REM Verificar se .env existe mas não está no .gitignore
if exist ".env" (
    findstr /C:".env" .gitignore >nul 2>&1
    if errorlevel 1 (
        echo [ERRO] Arquivo .env encontrado mas NAO esta no .gitignore!
        echo Por favor adicione ".env" ao .gitignore antes de continuar
        pause
        exit /b 1
    ) else (
        echo [OK] .env protegido no .gitignore
    )
) else (
    echo [OK] Arquivo .env nao encontrado (seguro)
)

REM Verificar se pastas data/ e logs/ estão protegidas
findstr /C:"data/" .gitignore >nul 2>&1
if errorlevel 1 (
    echo [AVISO] Pasta data/ nao esta no .gitignore
) else (
    echo [OK] data/ protegido no .gitignore
)

findstr /C:"logs/" .gitignore >nul 2>&1
if errorlevel 1 (
    echo [AVISO] Pasta logs/ nao esta no .gitignore
) else (
    echo [OK] logs/ protegido no .gitignore
)

echo.
echo ================================================
echo   Inicializando repositorio Git...
echo ================================================
echo.

REM Inicializar Git se ainda não inicializado
if not exist ".git" (
    git init
    echo [OK] Repositorio Git inicializado
) else (
    echo [INFO] Repositorio ja inicializado
)

REM Configurar user.name e user.email se não configurados
git config user.name >nul 2>&1
if errorlevel 1 (
    echo.
    set /p GIT_NAME="Digite seu nome (para commits): "
    git config user.name "%GIT_NAME%"
)

git config user.email >nul 2>&1
if errorlevel 1 (
    echo.
    set /p GIT_EMAIL="Digite seu email (para commits): "
    git config user.email "%GIT_EMAIL%"
)

echo.
echo [OK] Configuracao do Git concluida
echo     Nome: 
git config user.name
echo     Email: 
git config user.email

echo.
echo ================================================
echo   Preparando primeiro commit...
echo ================================================
echo.

REM Adicionar todos os arquivos (respeitando .gitignore)
git add .
echo [OK] Arquivos adicionados

echo.
echo Arquivos que serao commitados:
echo.
git status --short

echo.
echo ================================================
choice /C SN /M "Deseja criar o commit da versao estavel agora?"
if errorlevel 2 (
    echo.
    echo Commit cancelado. Execute 'git commit -m "mensagem"' quando estiver pronto
    pause
    exit /b 0
)

REM Criar commit inicial
git commit -m "feat: versao estavel do sistema de automacao Movidesk

- Sistema de polling inteligente com rate limiting
- Integracao com Groq para resumos por IA
- Notificacoes por email com templates HTML
- Persistencia de estado em SQLite
- Configuracao via YAML e variáveis de ambiente
- Scripts de instalacao e execucao para Windows"

if errorlevel 1 (
    echo [ERRO] Falha ao criar commit
    pause
    exit /b 1
)

echo [OK] Commit criado com sucesso!

echo.
echo ================================================
choice /C SN /M "Deseja criar tag v1.0.0?"
if errorlevel 2 (
    echo Tag nao criada
    goto :fim
)

REM Criar tag da versão estável
git tag -a v1.0.0 -m "Versao estavel 1.0.0 - Sistema funcionando"
echo [OK] Tag v1.0.0 criada

:fim
echo.
echo ================================================
echo   Setup concluido com sucesso!
echo ================================================
echo.
echo Proximos passos:
echo.
echo 1. Criar repositorio no GitHub (https://github.com/new)
echo 2. Conectar com: git remote add origin URL_DO_GITHUB
echo 3. Enviar codigo: git push -u origin main
echo 4. Enviar tag: git push origin v1.0.0
echo.
echo Para criar branch de desenvolvimento:
echo   git checkout -b development
echo.
echo Consulte GITHUB_SETUP.md para mais detalhes
echo.
pause
