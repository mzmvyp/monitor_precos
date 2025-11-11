# Monitor de Preços - Black Friday

Sistema automático para monitorar preços de produtos em **KaBuM**, **Amazon**, **Terabyte** e **Pichau**.

## 🚀 Início Rápido

### 1. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 2. Iniciar o Sistema

**Windows:**
```bash
iniciar_monitor.bat
```

**Linux/Mac:**
```bash
python run_monitor.py --interval 60 --disable-ssl-verify
```

**Ou via PowerShell (Windows):**
```powershell
python run_monitor.py --interval 60 --disable-ssl-verify
```

O sistema irá:
- ✅ Coletar preços automaticamente a cada **1 hora**
- ✅ Abrir dashboard em **http://localhost:8501**
- ✅ Salvar histórico em `data/price_history.csv`

## 📊 Dashboard

Acesse **http://localhost:8501** para ver:

- **Panorama Geral**: Preços atuais, menores preços e alertas
- **Histórico de Preços**: Gráficos de evolução por produto
- **Últimos Eventos**: Log de coletas recentes

### Recursos do Dashboard

- ⏱️ **Auto-refresh**: Atualiza automaticamente (configurável)
- 🔄 **Atualização Manual**: Botão para forçar coleta imediata
- 📈 **Gráficos Interativos**: Visualize tendências de preço
- 🎯 **Alertas**: Destaque quando preço está abaixo da meta

## ⚙️ Configuração

### Produtos Monitorados

Edite `config/products.yaml` para adicionar/remover produtos:

```yaml
- id: meu-produto
  name: Nome do Produto
  category: categoria
  target_price: 1000.00
  stores:
    - store: kabum
      url: https://www.kabum.com.br/produto/...
    - store: amazon
      url: https://www.amazon.com.br/...
```

### Intervalo de Coleta

Altere o intervalo (em minutos) no comando:

```bash
python run_monitor.py --interval 30  # 30 minutos
python run_monitor.py --interval 120 # 2 horas
```

### Proxy Corporativo

O sistema já vem configurado para funcionar com proxies corporativos. Use a flag `--disable-ssl-verify`:

```bash
python run_monitor.py --disable-ssl-verify
```

Se você tiver o certificado do proxy, pode configurá-lo:

```bash
set SCRAPER_CA_BUNDLE=C:\caminho\para\certificado.cer
python run_monitor.py
```

## 📁 Estrutura do Projeto

```
validador_precos/
├── config/
│   └── products.yaml          # Configuração de produtos
├── data/
│   └── price_history.csv      # Histórico de preços
├── src/
│   ├── scrapers/              # Scrapers por loja
│   │   ├── kabum.py
│   │   ├── amazon.py
│   │   └── mercadolivre.py
│   ├── models.py              # Modelos de dados
│   └── price_monitor.py       # Orquestrador
├── fetch_prices.py            # Coleta única
├── run_monitor.py             # Coleta contínua + dashboard
├── streamlit_app.py           # Interface web
└── iniciar_monitor.bat        # Atalho Windows
```

## 🛠️ Comandos Úteis

### Coletar Preços Uma Vez

```bash
python fetch_prices.py --disable-ssl-verify
```

### Coletar Produto Específico

```bash
python fetch_prices.py --product cpu-ryzen-5-9600x --disable-ssl-verify
```

### Apenas Dashboard (sem coleta automática)

```bash
streamlit run streamlit_app.py
```

### Monitor sem Dashboard

```bash
python run_monitor.py --no-dashboard --interval 60 --disable-ssl-verify
```

## 🔍 Produtos Configurados

- **Processadores**: Ryzen 5 9600X, Ryzen 7 7700/7700X, Ryzen 5 7600X
- **Placa-Mãe**: ASUS TUF Gaming B650M-E WiFi
- **SSD**: Kingston KC3000 1TB
- **Memória RAM**: XPG Lancer RGB 32GB, Kingston Fury Beast 32GB
- **Coolers**: Rise Mode Aura Ice 240mm, Kit 3 Fans Rise Mode
- **Gabinete**: Kalkan Midgard Mid Tower
- **Fonte**: Husky Sledger 850W 80 Plus Gold
- **Teclado**: Aula F75 Wireless

## 📝 Notas Importantes

1. **Respeite os Termos de Uso** dos sites monitorados
2. **Não reduza demais o intervalo** para evitar bloqueios
3. **Verifique o histórico** regularmente para identificar tendências
4. **Configure alertas de preço** editando `target_price` no YAML

## 🐛 Solução de Problemas

### Erro de SSL/Certificado

Adicione a flag `--disable-ssl-verify` em todos os comandos:

```bash
python fetch_prices.py --disable-ssl-verify
python run_monitor.py --disable-ssl-verify
```

### Preços não coletados

- Verifique se os links estão corretos no `products.yaml`
- Alguns sites podem bloquear após muitas requisições
- Aumente o intervalo de coleta

### Dashboard não abre

```bash
# Verificar se Streamlit está instalado
pip install streamlit

# Testar manualmente
streamlit run streamlit_app.py
```

## 📊 Exemplo de Saída

```
2025-11-10 12:22:39 [INFO] Processador AMD Ryzen 5 9600X | kabum | R$ 1559,99 -> OK
2025-11-10 12:22:39 [INFO] Processador AMD Ryzen 5 9600X | amazon | R$ 1499,99 -> OK ⚠️ ABAIXO DA META!
2025-11-10 12:22:39 [INFO] SSD Kingston KC3000 1TB | kabum | R$ 777,99 -> OK
```

## 🛒 Lojas Suportadas

- ✅ **KaBuM** - Scraping completo com preços e disponibilidade
- ✅ **Amazon** - Scraping completo com preços e disponibilidade
- ✅ **Terabyte** - Scraping completo com preços e disponibilidade
- ✅ **Pichau** - Scraping completo com preços e disponibilidade
- ❌ **Mercado Livre** - Removido (requer login para scraping)

## 🤝 Contribuindo

Sinta-se à vontade para adicionar:
- Notificações (Telegram, Email)
- Melhorias no dashboard
- Novos produtos no `config/products.yaml`

---

**Desenvolvido para monitoramento de preços na Black Friday 2025**

