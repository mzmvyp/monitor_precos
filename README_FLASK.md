# 📉 Monitor de Preços - Flask Professional Edition

## 🎯 Versão 5.0.0 - 100% Python (SEM Node.js!)

Sistema profissional de monitoramento de preços desenvolvido com **Flask** - framework web Python puro.

---

## ✅ **POR QUE FLASK?**

### Realmente 100% Python
- ✅ **Zero Node.js** (não precisa!)
- ✅ **Zero npm** (não precisa!)
- ✅ **Zero instalações extras** (só Flask)
- ✅ **Funciona em ambiente corporativo** com restrições

### Visual Profissional
- ✅ Tailwind CSS via CDN (sem npm)
- ✅ Alpine.js via CDN (sem npm)
- ✅ Chart.js via CDN (sem npm)
- ✅ Design moderno e responsivo

### Arquitetura Profissional
- ✅ Rotas organizadas
- ✅ Templates Jinja2
- ✅ API REST completa
- ✅ Integração com sistema existente

---

## 🚀 **Quick Start**

### 1. Instalar Flask
```bash
pip install -r requirements.txt
```

### 2. Executar
```bash
.\iniciar_monitor_flask.bat
```

OU manualmente:
```bash
python app.py
```

### 3. Acessar
```
http://localhost:5000
```

**Pronto! Sem complicação!**

---

## 📁 **Estrutura do Projeto**

```
monitor_precos/
├── app.py                      # Aplicação Flask principal
│
├── flask_app/                  # Frontend Flask
│   ├── templates/              # Templates HTML
│   │   ├── base.html           # Template base
│   │   ├── dashboard.html      # Dashboard
│   │   ├── gerenciamento.html  # Gerenciamento
│   │   ├── estatisticas.html   # Estatísticas
│   │   ├── voos.html           # Voos
│   │   └── sobre.html          # Sobre
│   │
│   └── static/                 # Arquivos estáticos
│       ├── css/
│       │   └── custom.css      # CSS customizado
│       └── js/
│           └── app.js          # JavaScript
│
├── src/                        # Lógica de negócio (mantida)
│   ├── price_monitor.py        # Monitor de preços
│   ├── flight_monitor.py       # Monitor de voos
│   ├── alert_manager.py        # Alertas
│   └── scrapers/               # Scrapers
│
├── config/                     # Configurações
│   ├── products.yaml           # Produtos
│   └── flights.yaml            # Voos
│
├── data/                       # Dados
│   ├── price_history.csv       # Histórico preços
│   └── flight_history.csv      # Histórico voos
│
└── iniciar_monitor_flask.bat  # Script inicialização
```

---

## 🎨 **Design Profissional**

### Tecnologias Frontend (Todas via CDN!)
| Tecnologia | Versão | Uso |
|---|---|---|
| **Tailwind CSS** | 3.x | Estilização profissional |
| **Alpine.js** | 3.x | Interatividade reativa |
| **Chart.js** | 4.x | Gráficos interativos |

**Nenhuma instalação necessária - tudo via CDN!**

### Gradientes Profissionais
- Primary: Roxo (#667eea → #764ba2)
- Success: Verde (#10b981 → #059669)
- Warning: Laranja (#f59e0b → #d97706)
- Danger: Vermelho (#ef4444 → #dc2626)

### Animações Suaves
- Fade-in nos elementos
- Hover effects nos cards
- Transições suaves
- Loading spinners elegantes

---

## 📊 **Páginas Disponíveis**

### 1. **Dashboard** (`/`)
- Métricas principais (4 cards)
- Banner de atualização (verde/amarelo/vermelho)
- Sidebar com ações e filtros
- Lista de produtos monitorados
- Botão de atualização de preços

### 2. **Gerenciamento** (`/gerenciamento`)
- Lista completa de produtos
- Tabela com ações (editar, remover, duplicar)
- Filtros por categoria/status
- Import/Export CSV

### 3. **Estatísticas** (`/estatisticas`)
- Métricas gerais
- Estatísticas por categoria
- Produtos abaixo da meta
- Economia total

### 4. **Voos** (`/voos`)
- Busca de voos com IA
- Lista de voos encontrados
- Estatísticas (menor/médio/total)

### 5. **Sobre** (`/sobre`)
- Informações do sistema
- Funcionalidades
- Tecnologias utilizadas
- Lojas suportadas

---

## 🔌 **API REST**

Todas as rotas retornam JSON e podem ser usadas para integração.

### Produtos
```bash
GET    /api/products              # Listar todos
GET    /api/products/{id}         # Detalhes de um
POST   /api/products              # Adicionar novo
PUT    /api/products/{id}         # Atualizar
DELETE /api/products/{id}         # Remover
```

### Coleta
```bash
POST   /api/collect               # Coletar preços
POST   /api/flights/collect       # Buscar voos
```

### Estatísticas
```bash
GET    /api/stats                 # Estatísticas gerais
GET    /api/history/{product_id}  # Histórico de produto
```

### Export
```bash
GET    /api/export/csv            # Download CSV
```

### Exemplo de Uso
```javascript
// Coletar preços
const response = await fetch('/api/collect', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'}
});
const data = await response.json();
console.log(data.message);
```

---

## ⚙️ **Configuração**

### Porta do Servidor
Edite `app.py` (última linha):
```python
app.run(debug=True, host='0.0.0.0', port=5000)  # Altere a porta aqui
```

### Adicionar Produto
1. Acesse `/gerenciamento`
2. Clique em "Adicionar Produto"
3. Preencha formulário
4. Salvar

OU edite `config/products.yaml`:
```yaml
items:
  - id: produto-exemplo
    name: "Nome do Produto"
    category: cpu
    desired_price: 1500.00
    enabled: true
    urls:
      - store: kabum
        url: "https://..."
```

---

## 🔧 **Funcionalidades**

### Monitoramento de Preços
- ✅ 20+ produtos configuráveis
- ✅ 4 lojas suportadas
- ✅ Coleta automática
- ✅ Alertas por email
- ✅ Histórico completo
- ✅ Detecção Open Box

### Dashboard Profissional
- ✅ Métricas em tempo real
- ✅ Gráficos interativos
- ✅ Filtros avançados
- ✅ Banner de staleness
- ✅ Responsivo (mobile)

### Gerenciamento
- ✅ CRUD completo
- ✅ Import/Export CSV
- ✅ Ativar/desativar produtos
- ✅ Duplicar produtos

### Estatísticas
- ✅ Por categoria
- ✅ Por loja
- ✅ Economia total
- ✅ Produtos abaixo meta

### Monitor de Voos
- ✅ Busca com DeepSeek AI
- ✅ Comparação de preços
- ✅ Alertas automáticos

---

## 🐛 **Troubleshooting**

### Erro: "ModuleNotFoundError: No module named 'flask'"
```bash
pip install flask>=3.0.0
```

### Erro: Porta 5000 em uso
Altere a porta em `app.py` ou:
```bash
# Windows - matar processo na porta 5000
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

### Erro: ChromeDriver não encontrado
```bash
python instalar_chromedriver_manual.py
```

### Erro: Arquivo não encontrado
Verifique se está no diretório correto:
```bash
cd C:\Users\...\monitor_precos
dir  # Deve ver app.py, flask_app/, src/
```

---

## 📊 **Comparação: Streamlit vs Flask**

| Aspecto | Streamlit | Flask |
|---|---|---|
| **Setup** | ⭐⭐⭐⭐⭐ Simples | ⭐⭐⭐⭐ Médio |
| **Visual** | ⭐⭐ Básico | ⭐⭐⭐⭐⭐ Profissional |
| **Customização** | ⭐⭐ Limitada | ⭐⭐⭐⭐⭐ Total |
| **Performance** | ⭐⭐⭐ Boa | ⭐⭐⭐⭐ Melhor |
| **Mobile** | ⭐⭐ Funciona | ⭐⭐⭐⭐⭐ Responsivo |
| **API** | ⭐⭐ Limitada | ⭐⭐⭐⭐⭐ REST completa |
| **Deploy** | ⭐⭐⭐ Fácil | ⭐⭐⭐⭐⭐ Muito fácil |

---

## 🚀 **Deploy (Opcional)**

Flask pode ser deployado em:

### Opção 1: PythonAnywhere (Free)
```bash
# Upload app.py e flask_app/
# Configure WSGI
# Pronto!
```

### Opção 2: Heroku
```bash
# Criar Procfile:
web: gunicorn app:app

# Deploy:
git push heroku main
```

### Opção 3: AWS/GCP/Azure
- EC2/Compute Engine/VM
- Instalar Python + Flask
- Rodar app.py
- Configurar reverse proxy (nginx)

---

## 📝 **Changelog**

### v5.0.0 - Flask Professional Edition (16/11/2025)
- ✨ Migração completa para Flask
- ✨ 100% Python (sem Node.js!)
- ✨ Design profissional (Tailwind CSS)
- ✨ API REST completa
- ✨ Templates Jinja2
- ✨ Alpine.js para interatividade
- ✨ Responsivo mobile-first

### v4.0.0 - Reflex Edition (DESCONTINUADA)
- ❌ Requeria Node.js (removida)

### v3.0.0 - Streamlit Premium
- ✅ Ainda disponível via `streamlit run streamlit_app_premium.py`

---

## 💡 **Dicas**

### Desenvolvimento
```bash
# Modo debug (auto-reload)
export FLASK_ENV=development  # Linux/Mac
set FLASK_ENV=development     # Windows
python app.py
```

### Produção
```bash
# Instalar gunicorn
pip install gunicorn

# Rodar
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Customização
- **Cores**: Edite `flask_app/static/css/custom.css`
- **Layout**: Edite `flask_app/templates/base.html`
- **Rotas**: Edite `app.py`

---

## ✅ **Requisitos Mínimos**

- Python 3.11+
- Flask 3.0+
- Navegador moderno (Chrome, Firefox, Edge)
- Conexão com internet (para CDNs)

**Nenhuma instalação além do Python e Flask!**

---

## 🎉 **Vantagens Sobre Reflex**

| Característica | Reflex | Flask |
|---|---|---|
| **Requer Node.js?** | ❌ SIM | ✅ NÃO |
| **Requer npm?** | ❌ SIM | ✅ NÃO |
| **Instalações extras?** | ❌ Muitas | ✅ Só Flask |
| **Ambiente corporativo?** | ❌ Difícil | ✅ Fácil |
| **Visual profissional?** | ✅ SIM | ✅ SIM |
| **100% Python?** | ⚠️ Backend sim | ✅ SIM (real!) |

---

**Monitor de Preços - Flask Professional Edition v5.0.0**

*Desenvolvido com Python 🐍 + Flask 🌶️*

**100% Python • Sem Node.js • Funciona em Qualquer Lugar!**
