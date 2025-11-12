# ⚙️ Configuração do Monitoramento Automático

## 📊 Como Funciona

O sistema monitora **automaticamente** produtos e voos em intervalos configuráveis.

---

## ⏰ Frequências de Atualização

### 📦 Produtos (Hardware, Cruzeiros)
- **Intervalo padrão**: 60 minutos (1 hora)
- **Configurável**: Pode ajustar no comando

**Lojas monitoradas**:
- Kabum
- Amazon
- Mercado Livre
- Pichau
- Terabyte (com Cloudflare bypass)

### ✈️ Voos
- **Intervalo padrão**: 360 minutos (6 horas)
- **Motivo**: Busca de voos demora ~5 minutos
- **Automático**: Roda junto com produtos

**Por que 6 horas?**
- Preços de voos não mudam tanto quanto produtos
- Busca é mais demorada (Google Flights)
- Evita sobrecarga do sistema

---

## 🚀 Iniciando o Monitor

### Comando Padrão (1h produtos, 6h voos):
```powershell
.\iniciar_monitor.bat
```

### Comando Personalizado:
```powershell
python run_monitor.py --interval 30
```
- Produtos: a cada 30 minutos
- Voos: a cada 6 horas (fixo)

---

## 📈 Exemplo de Execução

```
[10:00] Coletando produtos... (15 produtos)
[10:05] Coletados 15 registros de produtos.
[10:05] Próxima busca de voos em 5 ciclos

[11:00] Coletando produtos... (15 produtos)
[11:05] Coletados 15 registros de produtos.
[11:05] Próxima busca de voos em 4 ciclos

[12:00] Coletando produtos... (15 produtos)
[12:05] Coletados 15 registros de produtos.
[12:05] Próxima busca de voos em 3 ciclos

...

[16:00] Coletando produtos... (15 produtos)
[16:05] Coletados 15 registros de produtos.
[16:05] Iniciando busca de voos (a cada 6h)...
[16:10] Coletados 9 voos.
[16:10] Próxima busca de voos em 6 ciclos

[17:00] Coletando produtos... (15 produtos)
...
```

---

## 🎯 Ajustar Frequência de Voos

### Editar `run_monitor.py`:

```python
# Linha 77
flight_check_interval = 6  # horas
```

**Opções recomendadas**:
- `3` = A cada 3 horas (mais frequente)
- `6` = A cada 6 horas (padrão)
- `12` = A cada 12 horas (menos frequente)
- `24` = 1x por dia

**Não recomendado**:
- ❌ Menos de 3 horas (sobrecarga)
- ❌ Mais de 24 horas (perde oportunidades)

---

## 💾 Histórico de Dados

### Produtos:
**Arquivo**: `data/price_history.csv`

**Colunas**:
```
timestamp, product_id, product_name, category, store, 
url, price, currency, in_stock, raw_price, error
```

**Retenção**: Ilimitada (você decide quando limpar)

### Voos:
**Arquivo**: `data/flight_history.csv`

**Colunas**:
```
timestamp, flight_id, origin, destination, departure_date, 
return_date, price, currency, airline, stops, duration, url
```

**Retenção**: Ilimitada

---

## 📊 Dashboard - Dados em Tempo Real

### Atualização Automática:
- **Padrão**: A cada 5 minutos
- **Configurável**: Na barra lateral do dashboard

### Como Funciona:
1. Monitor coleta dados → Salva em CSV
2. Dashboard lê CSV → Mostra na tela
3. Sistema de cores calcula tendências
4. Você vê tudo atualizado!

---

## 🔧 Comandos Úteis

### Ver Logs em Tempo Real:
```powershell
# O monitor já mostra logs no terminal
.\iniciar_monitor.bat
```

### Forçar Atualização Manual:
No dashboard:
- **Produtos**: Clique em "Atualizar preços agora"
- **Voos**: Clique em "🔍 Buscar Voos Agora"

### Parar o Monitor:
```
Ctrl + C
```

---

## 📅 Exemplo de Agenda Diária

```
00:00 - Produtos (1ª coleta do dia)
01:00 - Produtos
02:00 - Produtos
03:00 - Produtos
04:00 - Produtos
05:00 - Produtos
06:00 - Produtos + Voos (1ª busca)
07:00 - Produtos
08:00 - Produtos
09:00 - Produtos
10:00 - Produtos
11:00 - Produtos
12:00 - Produtos + Voos (2ª busca)
13:00 - Produtos
14:00 - Produtos
15:00 - Produtos
16:00 - Produtos
17:00 - Produtos
18:00 - Produtos + Voos (3ª busca)
19:00 - Produtos
20:00 - Produtos
21:00 - Produtos
22:00 - Produtos
23:00 - Produtos
```

**Total diário**:
- **24 coletas** de produtos
- **4 buscas** de voos

---

## 💡 Dicas de Otimização

### 1. Horários Ideais
- **Madrugada** (2h-6h): Menos carga nos sites
- **Manhã** (8h-10h): Promoções começam
- **Noite** (20h-22h): Black Friday/ofertas

### 2. Intervalo Recomendado
- **Black Friday**: 30 minutos
- **Normal**: 60 minutos
- **Economia de recursos**: 120 minutos

### 3. Voos
- **Viagem próxima** (< 1 mês): 3 horas
- **Viagem futura** (> 3 meses): 12 horas

---

## 🎯 Resumo Rápido

| Item | Frequência | Ajustável |
|------|------------|-----------|
| **Produtos** | 1 hora | ✅ Sim (`--interval`) |
| **Voos** | 6 horas | ✅ Sim (editar código) |
| **Dashboard** | 5 minutos | ✅ Sim (barra lateral) |

---

## 🔔 Alertas Automáticos (Futuro)

Próximas versões terão:
- 📧 Email quando preço atingir meta
- 📱 Notificação push
- 🤖 Telegram bot
- 📊 Relatório diário

---

**Sistema configurado para máxima economia!** 💰

**Deixe rodando 24/7 e aproveite as melhores ofertas!** 🎯

