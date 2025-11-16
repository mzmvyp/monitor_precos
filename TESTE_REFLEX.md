# 🧪 Guia de Testes - Monitor de Preços Reflex

## ✅ Checklist de Validação

### 1. Instalação e Inicialização

- [ ] **Instalar dependências**
  ```bash
  pip install -r requirements.txt
  ```
  **Esperado:** Reflex instalado sem erros

- [ ] **Inicializar Reflex**
  ```bash
  reflex init
  ```
  **Esperado:** Criar pasta `.web/` e arquivos de configuração

- [ ] **Executar aplicação**
  ```bash
  .\iniciar_monitor_reflex.bat
  ```
  OU
  ```bash
  reflex run
  ```
  **Esperado:**
  - Backend inicia na porta 8000
  - Frontend inicia na porta 3000
  - Mensagem: "App running at: http://localhost:3000"

- [ ] **Acessar dashboard**
  ```
  http://localhost:3000
  ```
  **Esperado:** Página carrega com header roxo e navegação

---

### 2. Visual e Design

- [ ] **Header profissional**
  - Gradiente roxo (não sólido)
  - Título "📉 Monitor de Preços"
  - Subtítulo "Professional Edition"

- [ ] **Navegação**
  - 5 botões: Dashboard, Gerenciamento, Estatísticas, Voos, Sobre
  - Botão ativo tem gradiente roxo
  - Botões inativos têm fundo cinza claro

- [ ] **Cores profissionais**
  - Não parece Streamlit (sem layout básico)
  - Cards com bordas arredondadas
  - Sombras suaves
  - Espaçamentos consistentes

---

### 3. Dashboard

#### Métricas Principais

- [ ] **4 cards de métricas exibidos**
  - 📦 Produtos Ativos
  - 🏪 Total de URLs
  - 🔍 Verificações
  - 💰 Economia Total

- [ ] **Valores corretos**
  - Produtos Ativos = número de produtos enabled=true
  - Total URLs = soma de todas as URLs
  - Verificações = linhas no price_history.csv

#### Banner de Atualização

- [ ] **Banner exibido corretamente**
  - Se dados > 24h: Banner vermelho (ATENÇÃO)
  - Se dados 6-24h: Banner amarelo (⏰)
  - Se dados < 6h: Banner verde (✅)

#### Sidebar

- [ ] **Sidebar visível no Dashboard**
  - Título "⚙️ Configurações"
  - Seção de filtros
  - Botão "🔄 Atualizar Preços"

- [ ] **Filtros funcionam**
  - Dropdown de categoria
  - Checkboxes de lojas

#### Botão de Atualização

- [ ] **Clicar em "🔄 Atualizar Preços"**
  - Botão mostra loading spinner
  - Mensagem de progresso aparece
  - Após conclusão: mensagem de sucesso

---

### 4. Navegação Entre Páginas

- [ ] **Gerenciamento**
  - Clicar no botão "⚙️ Gerenciamento"
  - Página muda (sem reload completo)
  - Título "⚙️ Gerenciamento de Produtos" aparece

- [ ] **Estatísticas**
  - Clicar no botão "📈 Estatísticas"
  - 4 cards de métricas aparecem
  - Título "📈 Estatísticas e Análises" aparece

- [ ] **Voos**
  - Clicar no botão "✈️ Voos"
  - Botão "🔍 Buscar Voos" aparece
  - Mensagem sobre IA aparece

- [ ] **Sobre**
  - Clicar no botão "ℹ️ Sobre"
  - Card branco com informações aparece
  - Badges de lojas coloridos aparecem
  - Versão "4.0.0 (Reflex Professional Edition)"

---

### 5. Responsividade

- [ ] **Desktop (1920x1080)**
  - Layout ocupa bem o espaço
  - Sidebar à esquerda
  - Conteúdo principal à direita

- [ ] **Tablet (768px)**
  - Navegação wraps (quebra linha)
  - Cards se reorganizam

- [ ] **Mobile (375px)**
  - Uma coluna
  - Sidebar some ou vai para baixo
  - Botões empilhados

---

### 6. Performance

- [ ] **Tempo de carregamento inicial**
  - < 3 segundos para primeira carga

- [ ] **Navegação entre páginas**
  - Instantânea (< 200ms)
  - Sem reload da página

- [ ] **Animações suaves**
  - Fade in dos elementos
  - Hover nos botões

---

### 7. Comparação com Streamlit

| Aspecto | Streamlit | Reflex | ✅ |
|---|---|---|---|
| **Visual** | Básico | Profissional | [ ] |
| **Cores** | Padrão | Customizadas | [ ] |
| **Navegação** | Tabs simples | Botões com gradiente | [ ] |
| **Cards** | Quadrados | Arredondados + sombra | [ ] |
| **Header** | Texto simples | Gradiente roxo | [ ] |
| **Loading** | Spinner básico | Elegante + mensagem | [ ] |

---

### 8. Funcionalidades Core (Mantidas)

- [ ] **Dados carregam**
  - Produtos aparecem (se houver histórico)
  - Estatísticas calculadas corretamente

- [ ] **Config YAML lido**
  - `config/products.yaml` carregado
  - Produtos listados

- [ ] **Histórico lido**
  - `data/price_history.csv` carregado
  - Métricas calculadas

---

### 9. Mensagens de Erro/Sucesso

- [ ] **Erro exibido**
  - Se clicar "Atualizar Preços" sem ChromeDriver
  - Banner vermelho aparece
  - Instruções de instalação aparecem

- [ ] **Sucesso exibido**
  - Após coleta bem-sucedida
  - Banner verde com "✅"

---

### 10. Estado (State Management)

- [ ] **Estado persiste durante navegação**
  - Selecionar filtro no Dashboard
  - Navegar para Estatísticas
  - Voltar ao Dashboard
  - Filtro ainda selecionado

---

## 🎯 Teste de Aceitação Final

### Critérios de Aprovação

**APROVADO se:**
- ✅ Visual é **profissional** (não parece protótipo)
- ✅ Navegação é **rápida** (< 200ms entre páginas)
- ✅ Design é **consistente** (cores, espaçamentos, tipografia)
- ✅ **Todas** as funcionalidades do Streamlit funcionam
- ✅ Responsivo em mobile
- ✅ Sem erros no console do navegador

**REPROVADO se:**
- ❌ Parece Streamlit (visual básico)
- ❌ Navegação lenta ou com reload
- ❌ Erros no console
- ❌ Funcionalidades quebradas
- ❌ Não responsivo

---

## 🐛 Troubleshooting Durante Testes

### Erro: "App failed to compile"

**Verificar:**
```bash
# Sintaxe Python correta?
python -m py_compile monitor_app/monitor_app.py

# Imports corretos?
python -c "from monitor_app import app"
```

### Erro: "Module not found"

**Instalar:**
```bash
pip install reflex plotly
```

### Página em branco

**Verificar console do navegador (F12):**
- Erros de JavaScript?
- API retornando 500?

**Verificar terminal do Reflex:**
- Erros de Python?
- Backend rodando?

### Estado não atualiza

**Forçar reload:**
- Ctrl + Shift + R (hard refresh)
- Limpar cache do navegador

---

## 📝 Relatório de Testes

Preencha após completar todos os testes:

```
Data: ___/___/2025
Testador: __________________

Testes Passados: ___/60
Testes Falhados: ___/60

Visual Profissional: SIM / NÃO
Performance OK: SIM / NÃO
Funcionalidades OK: SIM / NÃO

Status Final: APROVADO / REPROVADO

Observações:
_________________________________
_________________________________
_________________________________
```

---

## 🎉 Próximos Passos (Se Aprovado)

1. **Desativar Streamlit**
   - Remover `streamlit_app_premium.py` do cron/scheduler
   - Usar apenas Reflex daqui em diante

2. **Deploy (Opcional)**
   - Vercel: `vercel deploy`
   - Railway: `railway up`

3. **Customizações**
   - Ajustar cores em `monitor_app/styles.py`
   - Adicionar novos componentes em `monitor_app/components/`

---

**✅ Boa sorte nos testes!**
