@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ========================================
echo   Sincronizar com GitHub
echo ========================================
echo.

python sync_github.py --disable-ssl-verify

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ Sincronização concluída com sucesso!
) else (
    echo.
    echo ❌ Erro na sincronização. Verifique os erros acima.
)

pause

