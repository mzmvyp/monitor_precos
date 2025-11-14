# 🔧 Instalação do Chrome para Scraping

## Problema
O sistema de scraping parou de funcionar com o erro:
```
Message: unknown error: cannot find Chrome binary
```

## Causa
O Google Chrome ou Chromium não está instalado no sistema. Os scrapers (especialmente Terabyte) usam Selenium com Chrome headless para coletar preços.

## Solução

### Para Ubuntu/Debian:

```bash
# Opção 1: Instalar Chromium (recomendado - mais leve)
sudo apt-get update
sudo apt-get install -y chromium-browser chromium-chromedriver

# Opção 2: Instalar Google Chrome
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i google-chrome-stable_current_amd64.deb
sudo apt-get install -f  # Corrigir dependências se necessário
```

### Para Windows:

1. **Baixar Google Chrome:**
   - Acesse: https://www.google.com/chrome/
   - Baixe e instale normalmente

2. **Verificar instalação:**
   ```powershell
   # Verificar se Chrome está no PATH
   where chrome
   # Ou procurar em: C:\Program Files\Google\Chrome\Application\chrome.exe
   ```

### Para macOS:

```bash
# Instalar via Homebrew
brew install --cask google-chrome

# Ou baixar manualmente de: https://www.google.com/chrome/
```

---

## ✅ Verificar se instalou corretamente:

```bash
# Linux/Mac
which google-chrome || which chromium || which chromium-browser

# Windows (PowerShell)
where chrome
```

---

## 🧪 Testar o Scraping:

Após instalar o Chrome, teste se o scraping funciona:

```bash
# Testar scraping de 1 produto
python3 -c "
from src.price_monitor import PriceMonitor
from pathlib import Path

monitor = PriceMonitor(
    config_path=Path('config/products.yaml'),
    history_path=Path('data/price_history.csv')
)

print('Testando scraping...')
snapshots = monitor.collect(product_ids=['cpu-ryzen-5-9600x'])
print(f'✅ Coletados {len(snapshots)} preços!')
for snap in snapshots:
    if snap.price:
        print(f'  {snap.store}: R$ {snap.price:.2f}')
    else:
        print(f'  {snap.store}: ERRO - {snap.error}')
"
```

---

## 🚀 Rodar o Dashboard:

Depois que o Chrome estiver instalado:

```bash
# Atualizar preços pelo dashboard
streamlit run streamlit_app_premium.py

# Ou pelo script principal
python3 -m src.price_monitor
```

---

## 📝 Observações:

1. **ChromeDriver é instalado automaticamente** pelo `webdriver-manager`
2. Você só precisa instalar o **navegador Chrome/Chromium**
3. O Selenium roda em modo **headless** (sem abrir janelas)
4. Produtos que não usam Selenium (Amazon, Kabum, Pichau com BeautifulSoup) continuam funcionando

---

## 🔍 Diagnóstico

Se continuar com problemas após instalar o Chrome:

```bash
# Verificar logs detalhados
python3 -m src.price_monitor --log-level DEBUG

# Verificar variáveis de ambiente
echo $CHROMEDRIVER_PATH

# Tentar instalar ChromeDriver manualmente
pip install --upgrade webdriver-manager
```

---

## ❓ Dúvidas?

- **Erro: "ChromeDriver incompatível"** → Execute: `python instalar_chromedriver_manual.py`
- **Erro: "invalid session id"** → Chrome foi atualizado, reinstale o ChromeDriver
- **Erro de permissão** → Use `sudo` no Linux ou execute como Administrador no Windows
