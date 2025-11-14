@echo off
chcp 65001 >nul
REM Monitor de Preços - Professional Edition
REM Executa coleta a cada 1 hora e abre dashboard Premium no navegador

echo ========================================
echo  Monitor de Precos - Premium Edition
echo ========================================
echo.
echo Iniciando sistema...
echo - Coleta automatica a cada 1 hora
echo - Dashboard Premium em http://localhost:8501
echo - Estatisticas avancadas
echo - Import/Export CSV/JSON
echo - Alertas por email
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

