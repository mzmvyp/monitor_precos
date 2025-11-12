# 📊 Monitor de Preços - Sistema Completo

## ✅ Status: 100% Funcional

Última atualização: 11/11/2025

---

## 🎯 Funcionalidades

### 🛒 Lojas Suportadas (Hardware)
- ✅ **Kabum** - Funcionando
- ✅ **Amazon** - Funcionando
- ✅ **Mercado Livre** - Funcionando
- ✅ **Terabyte** - Funcionando (com bypass Cloudflare)
- ✅ **Pichau** - Funcionando

### 🚢 Serviços de Viagem
- ✅ **Royal Caribbean** - Cruzeiros (NOVO!)

### 📱 Dashboard
- ✅ Interface Streamlit responsiva
- ✅ **Links clicáveis** - Clique para abrir produtos
- ✅ Gráficos de histórico de preços
- ✅ Filtros por categoria
- ✅ Atualização manual e automática
- ✅ Alertas de preço

### 🌐 Acesso Remoto
- ✅ **Tailscale** - Acesso seguro de qualquer lugar
- ✅ Guia completo em `GUIA_TAILSCALE.md`

---

## 📦 Produtos Monitorados

### 💻 Hardware (PC Gamer)
- Processadores AMD Ryzen (5 9600X, 7 7700, 7 7700X, 5 7600X)
- Placa-Mãe ASUS TUF Gaming B650M-E WiFi
- SSD Kingston KC3000 1TB
- Memórias DDR5 (XPG Lancer, Kingston Fury Beast)
- Water Cooler Rise Mode Aura Ice 240mm
- Fans Rise Mode Aura Pro
- Gabinete Kalkan Midgard
- Fontes 850W Gold (Husky Sledger, Gamemax GX850 Pro)

### 🚢 Viagens
- **Cruzeiro Royal Caribbean - Grécia 7 Noites**
  - Data: 05-12 Setembro 2026
  - Navio: Explorer of the Seas
  - Roteiro: Ravena → Santorini → Mykonos → Atenas → Split → Ravena
  - Preço atual: R$ 11.335,62 (2 adultos, cabine interior)

---

## 🔧 Tecnologias Anti-Bot

### Terabyte (Cloudflare)
- ✅ Delays inteligentes (3-5s inicial + 5-8s carregamento)
- ✅ Detecção automática de challenge
- ✅ Aguardo adicional de 10s se detectar Cloudflare
- ✅ Scroll lento e realista
- ✅ User-Agent atualizado (Chrome 120)

### Royal Caribbean
- ✅ Delays adequados (2-4s + 5-8s)
- ✅ Parse inteligente de preços (múltiplos formatos)
- ✅ Busca em JSON-LD, CSS, regex e data-attributes
- ✅ Detecção de banner de cookies

---

## 🚀 Como Usar

### Iniciar Monitor Completo
```bash
iniciar_monitor.bat
```

### Acessar Dashboard
- **Local**: http://localhost:8501
- **Remoto (Tailscale)**: http://100.64.0.X:8501

### Atualizar Preços Manualmente
No dashboard, clique em **"Atualizar preços agora"** na barra lateral.

### Configurar Produtos
Edite `config/products.yaml` para adicionar/remover produtos.

---

## 📊 Dashboard - Recursos

### Tabela Principal
| Coluna | Descrição |
|--------|-----------|
| **Produto** | Nome do produto/serviço |
| **Loja** | Loja ou serviço |
| **Preço** | Valor numérico formatado |
| **Link** | 🔗 Clique para abrir (NOVO!) |
| **Status** | Acima/Abaixo da meta |
| **Atualizado** | Data/hora da última coleta |

### Gráficos
- Histórico de preços por produto
- Comparação entre lojas
- Evolução temporal

### Filtros
- Por categoria (CPU, Memory, Storage, PSU, Cruise, etc.)
- Por produto específico
- Por período

---

## 🔐 Acesso Remoto com Tailscale

### Vantagens
- ✅ **Seguro** - Criptografia ponta-a-ponta
- ✅ **Fácil** - Instalação em 10 minutos
- ✅ **Gratuito** - Até 100 dispositivos
- ✅ **Funciona em qualquer rede** - WiFi, 4G, 5G

### Instalação Rápida
1. Criar conta: https://tailscale.com
2. Instalar no PC e celular
3. Fazer login (mesma conta)
4. Acessar: `http://100.64.0.X:8501`

**Guia completo**: `GUIA_TAILSCALE.md`

---

## 📁 Estrutura do Projeto

```
validador_precos/
├── src/
│   ├── scrapers/
│   │   ├── base.py              # Base requests (legado)
│   │   ├── selenium_base.py     # Base Selenium (atual)
│   │   ├── amazon.py            # ✅
│   │   ├── kabum.py             # ✅
│   │   ├── mercadolivre.py      # ✅
│   │   ├── pichau.py            # ✅
│   │   ├── terabyte.py          # ✅ Cloudflare bypass
│   │   └── royalcaribbean.py    # ✅ NOVO!
│   ├── models.py
│   ├── price_monitor.py
│   └── config_loader.py
├── config/
│   └── products.yaml            # Configuração de produtos
├── data/
│   └── price_history.csv        # Histórico de preços
├── streamlit_app.py             # Dashboard (links clicáveis!)
├── iniciar_monitor.bat          # Iniciar tudo
├── GUIA_TAILSCALE.md            # Guia acesso remoto
└── README.md

```

---

## 🧪 Testes Realizados

### Terabyte (Cloudflare Bypass)
- ✅ Memória Kingston Fury Beast: R$ 1.289,79
- ✅ Fonte Gamemax GX850 Pro: R$ 209,90

### Royal Caribbean
- ✅ Cruzeiro Grécia 7 Noites: R$ 11.335,62

### Dashboard
- ✅ Links clicáveis funcionando
- ✅ Formatação de colunas OK
- ✅ Gráficos renderizando
- ✅ Filtros funcionando

### Tailscale
- ✅ Conexão estabelecida
- ✅ Dashboard acessível remotamente

---

## 🎯 Próximas Funcionalidades (Futuro)

### ✈️ Passagens Aéreas
- Google Flights
- Decolar.com
- MaxMilhas
- Companhias aéreas diretas

### 📧 Notificações
- Email quando preço atingir meta
- Telegram bot
- Push notifications

### 📊 Análises Avançadas
- Previsão de tendência de preços
- Melhor dia/hora para comprar
- Comparação com histórico

### 🤖 Automação
- Compra automática (com confirmação)
- Alertas inteligentes
- Recomendações de produtos similares

---

## 💡 Dicas

### Monitoramento Eficiente
- **Intervalo recomendado**: 30-60 minutos
- **Horários ideais**: Madrugada (menos carga nos sites)
- **Evite**: Intervalos < 10 minutos (risco de bloqueio)

### Preços Desejados
- Pesquise histórico antes de definir
- Use sites como Zoom/Buscapé para referência
- Considere 10-15% abaixo do preço atual

### Troubleshooting
- Se scraper falhar: Aguarde 5-10 minutos e tente novamente
- Se Cloudflare bloquear: Aumente delays em `terabyte.py`
- Se dashboard não abrir: Verifique porta 8501 livre

---

## 📞 Suporte

### Logs
Logs detalhados em tempo real no terminal.

### Debug
Para debug detalhado, edite `logging.basicConfig(level=logging.DEBUG)`

### Atualização
```bash
git pull origin main
pip install -r requirements.txt
```

---

## 🏆 Conquistas

- ✅ 100% dos scrapers funcionando
- ✅ Bypass Cloudflare implementado
- ✅ Primeiro scraper de viagens (Royal Caribbean)
- ✅ Dashboard com links clicáveis
- ✅ Acesso remoto configurado
- ✅ Sistema estável e robusto

---

**Desenvolvido com ❤️ para monitorar preços de forma inteligente!**

**Última atualização**: 11/11/2025  
**Versão**: 2.0 - Sistema Completo

