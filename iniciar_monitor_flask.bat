@echo off
chcp 65001 >nul 2>&1
cls

echo ============================================
echo   Monitor de Precos - Flask Edition
echo   Versao 5.0.0 - 100%% Python
echo ============================================
echo.

echo [1/3] Verificando instalacao do Flask...
python -c "import flask" 2>nul
if %errorlevel% neq 0 (
    echo [AVISO] Flask nao instalado. Instalando...
    pip install -q flask>=3.0.0
    echo [OK] Flask instalado com sucesso!
) else (
    echo [OK] Flask ja instalado
)

echo.
echo [2/3] Verificando dependencias...
pip install -q -r requirements.txt
echo [OK] Dependencias verificadas

echo.
echo [3/3] Iniciando Monitor de Precos Flask Edition...
echo.
echo ============================================
echo   Dashboard disponivel em:
echo   http://localhost:5000
echo ============================================
echo.
echo Pressione Ctrl+C para encerrar
echo.

python app.py

pause
