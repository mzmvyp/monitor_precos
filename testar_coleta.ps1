# Script para testar coleta de preços
# Execute: .\testar_coleta.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Teste de Coleta de Precos" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Testar coleta de um produto específico
Write-Host "Testando coleta do Ryzen 5 9600X..." -ForegroundColor Yellow
python fetch_prices.py --product cpu-ryzen-5-9600x --disable-ssl-verify

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Teste concluido!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Para ver o historico completo:"
Write-Host "  type data\price_history.csv"
Write-Host ""
Write-Host "Para iniciar o monitor completo:"
Write-Host "  .\iniciar_monitor.bat"
Write-Host ""


