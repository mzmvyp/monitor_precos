# 🎨 Sistema de Cores - Tendência de Preços

## 📊 Como Funciona

O sistema compara o **preço atual** com o **preço anterior** e mostra a variação com cores:

---

## 🔴 Vermelho - Preço SUBIU

**Quando aparece**:
- Preço aumentou **mais de 1%** (produtos)
- Preço aumentou **mais de 2%** (voos)

**Exemplo**:
```
🔴 +R$ 150,00 (+5.2%)
```

**Significado**:
- ⚠️ **Não compre agora** - Preço está subindo
- 📈 Tendência de alta
- ⏰ Aguarde para ver se volta a cair

---

## 🟡 Amarelo - Preço ESTÁVEL

**Quando aparece**:
- Variação entre **-1% e +1%** (produtos)
- Variação entre **-2% e +2%** (voos)
- Primeiro registro (sem histórico)

**Exemplo**:
```
🟡 Estável (-0.5%)
🟡 Novo
```

**Significado**:
- ✅ **Pode comprar** - Preço não mudou significativamente
- 📊 Mercado estável
- 🎯 Bom momento se estiver no seu orçamento

---

## 🟢 Verde - Preço CAIU

**Quando aparece**:
- Preço diminuiu **mais de 1%** (produtos)
- Preço diminuiu **mais de 2%** (voos)

**Exemplo**:
```
🟢 R$ -250,00 (-8.3%)
```

**Significado**:
- 🎉 **COMPRE AGORA!** - Preço está caindo
- 📉 Tendência de baixa
- 💰 Oportunidade de economia

---

## ⚪ Branco - Sem Dados

**Quando aparece**:
- Erro ao calcular
- Dados insuficientes

**Exemplo**:
```
⚪ N/A
```

---

## 📈 Exemplos Práticos

### Produto: SSD Kingston KC3000 1TB

| Data | Preço | Tendência | Ação |
|------|-------|-----------|------|
| 10/11 | R$ 750,00 | 🟡 Novo | Aguardar |
| 11/11 | R$ 720,00 | 🟢 R$ -30,00 (-4.0%) | **COMPRAR!** ✅ |
| 12/11 | R$ 715,00 | 🟡 Estável (-0.7%) | Comprar se precisar |
| 13/11 | R$ 780,00 | 🔴 +R$ 65,00 (+9.1%) | **NÃO COMPRAR** ❌ |

### Voo: GRU → Milão

| Data | Preço | Tendência | Ação |
|------|-------|-----------|------|
| 10/11 | R$ 4.500 | 🟡 Novo | Aguardar |
| 11/11 | R$ 4.200 | 🟢 R$ -300 | **COMPRAR!** ✅ |
| 12/11 | R$ 4.180 | 🟡 Estável | Comprar se precisar |
| 13/11 | R$ 4.800 | 🔴 +R$ 620 | **NÃO COMPRAR** ❌ |

---

## 🎯 Estratégias de Compra

### 1. Compra Urgente
- ✅ **Verde ou Amarelo**: Compre
- ⚠️ **Vermelho**: Só se for urgente

### 2. Compra Planejada
- ✅ **Verde**: Compre imediatamente
- 🟡 **Amarelo**: Aguarde 1-2 dias
- ❌ **Vermelho**: Aguarde cair

### 3. Monitoramento
- Configure **preço desejado** em `products.yaml`
- Sistema alerta quando atingir meta
- Combine com tendência verde = **melhor momento!**

---

## 🔔 Alertas Inteligentes

### Combinações Ideais:

#### 🎯 Alerta de Ouro
```
Preço: R$ 700,00
Meta: R$ 750,00
Tendência: 🟢 R$ -50,00 (-6.7%)
Status: Abaixo da meta
```
**= COMPRE AGORA!** 🎉

#### ⚠️ Alerta de Cuidado
```
Preço: R$ 800,00
Meta: R$ 750,00
Tendência: 🔴 +R$ 80,00 (+11.1%)
Status: Acima da meta
```
**= AGUARDE!** ⏰

---

## 📊 Dashboard - Como Ver

### Tabela de Produtos:
```
┌──────────────┬───────┬────────┬──────────────────────┐
│ Produto      │ Loja  │ Preço  │ Tendência            │
├──────────────┼───────┼────────┼──────────────────────┤
│ SSD KC3000   │ Kabum │ 720,00 │ 🟢 R$ -30,00 (-4.0%) │
│ Ryzen 5 9600X│ Amazon│ 1.500  │ 🟡 Estável (+0.2%)   │
│ RTX 4070     │ Pichau│ 3.200  │ 🔴 +R$ 200 (+6.7%)   │
└──────────────┴───────┴────────┴──────────────────────┘
```

### Tabela de Voos:
```
┌──────────┬────────┬──────────┬────────────┐
│ Companhia│ Preço  │ Tendência│ Link       │
├──────────┼────────┼──────────┼────────────┤
│ LATAM    │ 4.200  │ 🟢 R$ -300│ 🔗 Ver    │
│ TAP      │ 4.500  │ 🟡 Novo   │ 🔗 Ver    │
│ Lufthansa│ 5.200  │ 🔴 +R$ 400│ 🔗 Ver    │
└──────────┴────────┴──────────┴────────────┘
```

---

## ⚙️ Configuração

### Ajustar Sensibilidade:

**Produtos** (em `streamlit_app.py`):
```python
if diff_percent > 1:  # Subiu > 1%
    return "🔴"
elif diff_percent < -1:  # Caiu > 1%
    return "🟢"
```

**Voos** (em `streamlit_app.py`):
```python
if diff_percent > 2:  # Subiu > 2%
    return "🔴"
elif diff_percent < -2:  # Caiu > 2%
    return "🟢"
```

**Dica**: Voos têm limiar maior (2%) porque preços variam mais!

---

## 💡 Dicas Avançadas

### 1. Histórico de Tendências
- Veja gráfico de histórico
- Se teve 3+ quedas seguidas = **ótimo momento**
- Se teve 3+ altas seguidas = **aguarde**

### 2. Compare Lojas
```
Produto X:
- Kabum: R$ 700 🟢 (-5%)
- Amazon: R$ 720 🔴 (+3%)
```
**= Compre na Kabum!**

### 3. Combine com Status
```
🟢 Tendência + Abaixo da meta = 🎯 PERFEITO!
🔴 Tendência + Acima da meta = ❌ EVITE!
```

---

## 🎨 Legenda Rápida

| Emoji | Significado | Ação |
|-------|-------------|------|
| 🔴 | Subiu | Aguarde |
| 🟡 | Estável/Novo | OK |
| 🟢 | Caiu | Compre! |
| ⚪ | Sem dados | N/A |

---

**Sistema desenvolvido para maximizar suas economias!** 💰

**Economize mais comprando no momento certo!** 🎯

