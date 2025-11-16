@echo off
chcp 65001 >nul 2>&1
cls

echo ============================================
echo   Monitor de Precos - Professional Edition
echo   Versao 4.0.0 - Reflex
echo ============================================
echo.

echo [1/3] Verificando instalacao do Reflex...
python -c "import reflex" 2>nul
if %errorlevel% neq 0 (
    echo [AVISO] Reflex nao instalado. Instalando...
    pip install -q reflex>=0.4.0
    echo [OK] Reflex instalado com sucesso!
) else (
    echo [OK] Reflex ja instalado
)

echo.
echo [2/3] Verificando dependencias...
pip install -q -r requirements.txt
echo [OK] Dependencias verificadas

echo.
echo [3/3] Iniciando Monitor de Precos Professional Edition...
echo.
echo ============================================
echo   Dashboard disponivel em:
echo   http://localhost:3000
echo ============================================
echo.
echo Pressione Ctrl+C para encerrar
echo.

python -m reflex run

pause
