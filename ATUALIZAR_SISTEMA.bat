@echo off
chcp 65001 >nul 2>&1
echo ========================================
echo  ATUALIZAR SISTEMA - Monitor de Precos
echo ========================================
echo.

echo [1/5] Parando processos do monitor...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq Monitor*" 2>nul
timeout /t 2 >nul

echo [2/5] Verificando branch atual...
git branch --show-current

echo [3/5] Baixando atualizacoes do git...
git fetch origin
git pull origin claude/fix-scraping-bugs-01RWBbLyhZA2aFqJaRAHcP8x

echo [4/5] Verificando commits recentes...
echo.
echo Ultimos 5 commits:
git log --oneline -5

echo.
echo [5/5] Validando arquivos criticos...
echo.

findstr /C:"has_open_box" src\scrapers\kabum.py >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Deteccao de Open Box encontrada
) else (
    echo [ERRO] Deteccao de Open Box NAO encontrada
)

findstr /C:"terabyte" config\products.yaml >nul 2>&1
if %errorlevel% equ 0 (
    echo [ERRO] Terabyte ainda presente
) else (
    echo [OK] Terabyte removida
)

findstr /C:"ZoneInfo" src\alert_manager.py >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Timezone de Brasilia configurado
) else (
    echo [ERRO] Timezone de Brasilia NAO configurado
)

echo.
echo ========================================
echo  ATUALIZACAO CONCLUIDA!
echo ========================================
echo.
echo Proximos passos:
echo 1. Rode: iniciar_monitor.bat
echo 2. Aguarde alguns minutos
echo 3. Acesse: http://localhost:8501
echo.
pause
