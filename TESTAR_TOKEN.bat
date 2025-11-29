@echo off
chcp 65001 >nul
cd /d "%~dp0"
python testar_token.py
pause

