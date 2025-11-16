# 📉 Monitor de Preços - Professional Edition

## 🚀 Versão 4.0.0 - Reflex

Sistema profissional de monitoramento de preços desenvolvido com **Reflex** (Python puro que compila para React).

---

## ⚡ Quick Start

### 1. Instalação
```bash
pip install -r requirements.txt
reflex init
```

### 2. Execução
```bash
.\iniciar_monitor_reflex.bat
```
OU
```bash
reflex run
```

### 3. Acesso
```
http://localhost:3000
```

---

## 🎯 Funcionalidades

### Monitoramento de Preços
- ✅ **20+ produtos** monitorados automaticamente
- ✅ **4 lojas suportadas:** Kabum, Amazon, Pichau, MercadoLivre
- ✅ **Alertas por email** quando preço atinge meta
- ✅ **Detecção de Open Box** (Kabum)
- ✅ **Histórico completo** de preços

### Dashboard Profissional
- 📊 **Métricas em tempo real**
- 📈 **Gráficos interativos** (Plotly)
- 🎯 **Destaques:** Produtos abaixo da meta, maiores quedas
- 📚 **Catálogo completo** com filtros avançados
- 🏆 **Ranking de lojas** por melhor preço

### Gerenciamento
- ➕ **CRUD completo** de produtos
- 📥 **Import/Export** (CSV/JSON)
- 🔄 **Ativar/desativar** produtos
- 📋 **Duplicar** produtos facilmente
- 🔍 **Busca e filtros** avançados

### Estatísticas
- 📊 **Análises por categoria**
- 🏪 **Distribuição por loja**
- 💰 **Economia total** calculada
- ⏰ **Histórico de alertas**

### Monitor de Voos
- ✈️ **Busca inteligente** com DeepSeek AI
- 🎫 **Comparação de preços**
- 📧 **Alertas automáticos**

---

## 🎨 Design Profissional

### Por que Reflex?
- ✅ **100% Python** (sem JavaScript!)
- ✅ **Visual profissional** (compila para React)
- ✅ **Performance superior** ao Streamlit
- ✅ **Totalmente responsivo** (mobile-first)
- ✅ **Customização completa**

### Design System
- 🎨 Paleta de cores consistente
- 🎨 Gradientes modernos
- 🎨 Tipografia profissional
- 🎨 Componentes reutilizáveis
- 🎨 Animações suaves

---

## 📁 Estrutura do Projeto

```
monitor_precos/
├── monitor_app/              # Aplicação Reflex
│   ├── monitor_app.py        # App principal
│   ├── state.py              # State management
│   ├── styles.py             # Design system
│   └── components/           # Componentes reutilizáveis
│       ├── cards.py          # Cards
│       ├── alerts.py         # Alertas
│       ├── badges.py         # Badges
│       └── buttons.py        # Botões
│
├── src/                      # Lógica de negócio
│   ├── price_monitor.py      # Monitor de preços
│   ├── flight_monitor.py     # Monitor de voos
│   └── scrapers/             # Scrapers
│
├── config/                   # Configurações
│   ├── products.yaml         # Produtos
│   └── flights.yaml          # Voos
│
└── data/                     # Histórico
    ├── price_history.csv
    └── flight_history.csv
```

---

## 🛠️ Tecnologias

| Tecnologia | Uso |
|---|---|
| **Reflex** | Framework UI (Python → React) |
| **Selenium** | Web scraping |
| **BeautifulSoup** | HTML parsing |
| **Pandas** | Manipulação de dados |
| **Plotly** | Gráficos interativos |
| **YAML** | Configuração |
| **DeepSeek API** | IA para voos |

---

## 📖 Documentação

- **Migração:** `REFLEX_MIGRATION.md` - Guia completo de migração
- **Diagnóstico:** `DIAGNOSTICO_COMPLETO.md` - Troubleshooting
- **Instalação Windows:** `INSTALACAO_WINDOWS.md` - Setup ChromeDriver

---

## 🔧 Configuração

### Adicionar Produto

1. Acesse: **Gerenciamento** → **Adicionar**
2. Preencha:
   - Nome do produto
   - ID único
   - Categoria
   - Preço desejado
   - URLs das lojas
3. Salvar

### Configurar Alertas

Edite `config/products.yaml`:
```yaml
- id: produto-exemplo
  name: "Nome do Produto"
  category: cpu
  desired_price: 1500.00  # Alerta quando atingir
  enabled: true
  urls:
    - store: kabum
      url: "https://..."
```

---

## 📊 Screenshots

### Dashboard
- Métricas principais
- Produtos em destaque
- Gráficos de tendência

### Gerenciamento
- Lista de produtos
- Formulário de adição
- Import/Export

### Estatísticas
- Análises por categoria
- Ranking de lojas
- Histórico de alertas

---

## 🐛 Troubleshooting

### Erro: ChromeDriver não instalado
```bash
python instalar_chromedriver_manual.py
```

### Erro: Reflex não encontrado
```bash
pip install reflex>=0.4.0
```

### Porta 3000 em uso
```bash
reflex run --frontend-port 3001
```

---

## 🚀 Deploy (Opcional)

O sistema pode ser deployado em:
- **Vercel** (recomendado)
- **Railway**
- **Render**
- **AWS/GCP/Azure**

---

## 📝 Changelog

### v4.0.0 - Professional Edition (16/11/2025)
- ✨ Migração completa para Reflex
- ✨ Design system profissional
- ✨ Componentes reutilizáveis
- ✨ UI responsiva
- ✨ Performance superior

### v3.0.0 - Premium Edition (13/11/2025)
- ✨ Dashboard Premium Streamlit
- ✨ Detecção Open Box
- ✨ Timezone Brasília
- ✨ Scripts de diagnóstico

---

## 📫 Contato

Para bugs ou dúvidas, consulte a documentação em `REFLEX_MIGRATION.md`.

---

## 📜 Licença

Projeto interno - Todos os direitos reservados.

---

**🎉 Monitor de Preços - Professional Edition v4.0.0**

*Desenvolvido com Python 🐍 + Reflex ⚡*
