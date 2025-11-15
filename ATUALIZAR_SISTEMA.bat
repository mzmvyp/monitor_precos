@echo off
chcp 65001 >nul
echo ========================================
echo  ATUALIZAR SISTEMA - Monitor de Preços
echo ========================================
echo.

echo [1/5] Parando processos do monitor...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq Monitor*" 2>nul
timeout /t 2 >nul

echo [2/5] Verificando branch atual...
git branch --show-current

echo [3/5] Baixando atualizações do git...
git fetch origin
git pull origin claude/fix-scraping-bugs-01RWBbLyhZA2aFqJaRAHcP8x

echo [4/5] Verificando commits recentes...
echo.
echo Últimos 5 commits:
git log --oneline -5

echo.
echo [5/5] Validando arquivos críticos...
echo.

if exist "src\scrapers\kabum.py" (
    findstr /C:"has_open_box" src\scrapers\kabum.py >nul
    if errorlevel 1 (
        echo ❌ Detecção de Open Box NÃO encontrada
    ) else (
        echo ✅ Detecção de Open Box OK
    )
) else (
    echo ❌ Arquivo kabum.py não encontrado!
)

if exist "config\products.yaml" (
    findstr /C:"terabyte" config\products.yaml >nul
    if errorlevel 1 (
        echo ✅ Terabyte removida OK
    ) else (
        echo ❌ Terabyte ainda presente!
    )
) else (
    echo ❌ Arquivo products.yaml não encontrado!
)

if exist "src\alert_manager.py" (
    findstr /C:"ZoneInfo" src\alert_manager.py >nul
    if errorlevel 1 (
        echo ❌ Timezone de Brasília NÃO configurado
    ) else (
        echo ✅ Timezone de Brasília OK
    )
) else (
    echo ❌ Arquivo alert_manager.py não encontrado!
)

echo.
echo ========================================
echo ✅ ATUALIZAÇÃO CONCLUÍDA!
echo ========================================
echo.
echo Próximos passos:
echo 1. Rode: iniciar_monitor.bat
echo 2. Aguarde alguns minutos
echo 3. Acesse: http://localhost:8501
echo.
pause
