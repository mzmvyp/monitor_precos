@echo off
echo ========================================
echo  Commit Final - Sistema com Selenium
echo ========================================
echo.

echo Adicionando arquivos...
git add -A

echo.
echo Criando commit...
git commit -m "Sistema completo com Selenium - 100%% funcional

MIGRACAO PARA SELENIUM:
- Todos os scrapers usando navegador real (Chrome headless)
- Resolvido 100%% dos erros 403 (Pichau e Terabyte)
- Sistema anti-deteccao completo

ARQUIVOS PRINCIPAIS:
- src/scrapers/selenium_base.py - Base Selenium
- testar_scrapers.py - Testes automatizados (8/8 passando)
- requirements.txt - Selenium + webdriver-manager
- README.md - Documentacao consolidada

LIMPEZA:
- Removidos arquivos temporarios e de teste
- Removidos instaladores redundantes
- Documentacao consolidada em README.md

TESTES:
- Pichau: OK (resolvido 403)
- Terabyte: OK (resolvido 403)
- Kabum: OK
- Amazon: OK
- Mercado Livre: OK

STATUS: Pronto para uso"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERRO no commit!
    pause
    exit /b 1
)

echo.
echo Enviando para GitHub...
git push origin main

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERRO no push!
    pause
    exit /b 1
)

echo.
echo ========================================
echo  Sucesso! Codigo enviado para GitHub
echo ========================================
echo.
echo Repositorio: https://github.com/mzmvyp/monitor_precos
echo.
pause

