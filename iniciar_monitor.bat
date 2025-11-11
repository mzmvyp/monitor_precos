@echo off
chcp 65001 >nul
REM Monitor de Preços - Black Friday
REM Executa coleta a cada 1 hora e abre dashboard no navegador

echo ========================================
echo  Monitor de Precos - Black Friday
echo ========================================
echo.
echo Iniciando sistema...
echo - Coleta automatica a cada 1 hora
echo - Dashboard em http://localhost:8501
echo.
echo Pressione Ctrl+C para encerrar
echo ========================================
echo.

REM Executar monitor com dashboard (SSL desabilitado para proxy corporativo)
python run_monitor.py --interval 60 --disable-ssl-verify

if errorlevel 1 (
    echo.
    echo ERRO: Falha ao executar o monitor!
    echo Verifique se Python e dependencias estao instaladas.
    echo.
)

pause

