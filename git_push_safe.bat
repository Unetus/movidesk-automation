@echo off
REM Script de Verificação de Segurança Antes de Push
echo ================================================
echo   Verificacao de Seguranca Pre-Push
echo ================================================
echo.

set ISSUES_FOUND=0

echo Verificando arquivos que serao enviados...
echo.

REM Verificar se .env está sendo commitado
git ls-files | findstr ".env$" >nul 2>&1
if not errorlevel 1 (
    echo [ERRO] Arquivo .env encontrado no commit!
    echo        Adicione ao .gitignore: echo .env ^>^> .gitignore
    set ISSUES_FOUND=1
)

REM Verificar se há arquivos de log commitados
git ls-files | findstr "\.log$" >nul 2>&1
if not errorlevel 1 (
    echo [AVISO] Arquivos .log encontrados no commit
    echo         Considere adicionar *.log ao .gitignore
    set ISSUES_FOUND=1
)

REM Verificar se há dados sensíveis em config.yaml
findstr /C:"token" /C:"password" /C:"key" config.yaml | findstr /V /C:"your_" /C:"exemplo" /C:"example" >nul 2>&1
if not errorlevel 1 (
    echo [AVISO] Possivel credencial real em config.yaml
    echo         Verifique manualmente se nao ha dados sensiveis
    set ISSUES_FOUND=1
)

REM Buscar por possíveis credenciais no código
echo.
echo Buscando padroes de credenciais no codigo...
findstr /S /I /C:"password=" /C:"token=" /C:"api_key=" src\*.py 2>nul | findstr /V /C:"your_" /C:"example" >nul 2>&1
if not errorlevel 1 (
    echo [AVISO] Possivel credencial hardcoded encontrada
    echo         Busque por "password=", "token=", "api_key=" no codigo
    set ISSUES_FOUND=1
)

REM Verificar tamanho de arquivos grandes
echo.
echo Verificando arquivos grandes...
for /f "tokens=*" %%f in ('git ls-files') do (
    if exist "%%f" (
        for %%s in ("%%f") do (
            if %%~zs GTR 10485760 (
                echo [AVISO] Arquivo grande: %%f ^(%%~zs bytes^)
                echo          GitHub recomenda arquivos ^< 10MB
                set ISSUES_FOUND=1
            )
        )
    )
)

echo.
echo ================================================

if %ISSUES_FOUND%==1 (
    echo.
    echo [!] PROBLEMAS ENCONTRADOS
    echo.
    echo Revise os avisos acima antes de fazer push
    echo.
    choice /C SN /M "Deseja continuar mesmo assim?"
    if errorlevel 2 (
        echo Push cancelado
        pause
        exit /b 1
    )
) else (
    echo.
    echo [OK] Nenhum problema de seguranca encontrado!
    echo.
)

echo ================================================
echo   Resumo do que sera enviado:
echo ================================================
echo.
git log --oneline origin/main..HEAD 2>nul
if errorlevel 1 (
    echo [INFO] Primeiro push - sem comparacao com remote
)

echo.
echo ================================================
choice /C SN /M "Confirma o push para o GitHub?"
if errorlevel 2 (
    echo Push cancelado pelo usuario
    pause
    exit /b 0
)

echo.
echo Enviando para o GitHub...
git push

if errorlevel 1 (
    echo.
    echo [ERRO] Falha no push
    echo.
    echo Possivel causa:
    echo - Remote nao configurado: git remote add origin URL
    echo - Branch nao configurado: git push -u origin main
    echo - Credenciais incorretas
    pause
    exit /b 1
)

echo.
echo [OK] Push concluido com sucesso!
echo.

REM Verificar se há tags para enviar
git tag >nul 2>&1
if not errorlevel 1 (
    echo.
    choice /C SN /M "Deseja enviar as tags tambem?"
    if not errorlevel 2 (
        git push --tags
        echo [OK] Tags enviadas
    )
)

echo.
echo ================================================
echo   Push concluido!
echo ================================================
echo.
echo Seu codigo esta no GitHub!
echo Veja em: 
git remote get-url origin 2>nul
echo.
pause
