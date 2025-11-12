# ✈️ Guia do Agent de Voos com DeepSeek

## 🤖 O Que É?

Um **agente inteligente** que usa:
- **Selenium** para acessar Google Flights
- **DeepSeek AI** para extrair informações dos voos
- **Automação** para buscar em múltiplas combinações

---

## 🎯 Seu Caso de Uso

### Viagem para Itália (Setembro 2026)

**Requisitos**:
- 🛫 **Ida**: 30 Ago - 04 Set (precisa chegar antes do cruzeiro dia 05)
- 🛬 **Volta**: 12 Set - 14 Set (após cruzeiro)
- 🌍 **Destinos**: Milão, Bologna, Florença ou Veneza
- 💰 **Orçamento**: Até R$ 8.000
- ⏱️ **Duração**: 15 dias total

**Combinações Possíveis**:
- 6 datas de ida × 3 datas de volta × 4 aeroportos = **72 buscas**!

---

## 🚀 Como Usar

### 1. Teste Rápido (1 busca)

```powershell
.\testar_voos.bat
```

Isso testa: **GRU → Milão** (01-14 Set/2026)

**Resultado esperado**:
```
Encontrados 5 voos

1. LATAM
   Preço: R$ 4.250,00
   Paradas: 1
   Duração: 14h 30m

2. TAP
   Preço: R$ 4.580,00
   Paradas: 1
   Duração: 16h 15m
...
```

---

### 2. Busca Completa (Todas Combinações)

Edite `config/flights.yaml` e execute:

```python
from src.flight_agent import FlightAgent

agent = FlightAgent()

flights = agent.search_best_flights(
    origin="GRU",
    destinations=["MXP", "BLQ", "FLR", "VCE"],
    departure_dates=[
        "2026-08-30", "2026-08-31", "2026-09-01",
        "2026-09-02", "2026-09-03", "2026-09-04"
    ],
    return_dates=["2026-09-12", "2026-09-13", "2026-09-14"],
    max_price=8000.0
)

# Mostrar top 10 mais baratos
for flight in flights[:10]:
    print(f"{flight.airline}: R$ {flight.price:.2f}")

agent.close()
```

---

## ⚙️ Configuração

### Arquivo: `config/flights.yaml`

```yaml
flights:
  - id: "flight-italy-sep2026"
    name: "Voo Brasil → Itália (Set/2026)"
    origin: "GRU"
    destinations: ["MXP", "BLQ", "FLR", "VCE"]
    
    departure_dates:
      - "2026-08-30"
      - "2026-09-04"  # Adicione/remova datas
    
    return_dates:
      - "2026-09-12"
      - "2026-09-14"
    
    max_price: 8000.0
    alert_price: 5000.0  # Alertar se < R$ 5.000
```

---

## 🧠 Como Funciona (Técnico)

### Fluxo:

```
1. Selenium abre Google Flights
   ↓
2. Preenche: origem, destino, datas
   ↓
3. Aguarda carregamento (10s)
   ↓
4. Captura HTML da página
   ↓
5. Envia HTML para DeepSeek API
   ↓
6. DeepSeek extrai:
   - Companhia aérea
   - Preço
   - Paradas
   - Duração
   - Horários
   ↓
7. Retorna JSON estruturado
   ↓
8. Sistema salva e compara
```

### Prompt para DeepSeek:

```
Extraia TODAS as opções de voos desta página do Google Flights.

Para cada voo, extraia:
- airline: Nome da companhia aérea
- price: Preço em reais (apenas número)
- stops: Número de paradas (0 para direto)
- duration: Duração total (ex: "12h 30m")

Retorne JSON:
{
  "flights": [
    {
      "airline": "LATAM",
      "price": 2500.50,
      "stops": 1,
      "duration": "12h 30m"
    }
  ]
}
```

---

## 💡 Vantagens vs Scraping Tradicional

| Aspecto | Scraping Tradicional | Agent DeepSeek |
|---------|---------------------|----------------|
| **Adaptação** | ❌ Quebra se site mudar | ✅ Adapta-se automaticamente |
| **Complexidade** | ❌ Precisa mapear cada elemento | ✅ Entende contexto |
| **Manutenção** | ❌ Alta | ✅ Baixa |
| **Custo** | ✅ Grátis | 💰 ~$0.001 por busca |
| **Velocidade** | ✅ Rápido | ⚠️ Moderado (10s por busca) |

---

## 📊 Custos DeepSeek

### Preços (Novembro 2024):
- **Input**: $0.14 / 1M tokens
- **Output**: $0.28 / 1M tokens

### Estimativa para Sua Busca:
- 72 buscas × ~5k tokens = 360k tokens
- Custo total: **~$0.10** (R$ 0,50)

**Muito barato!** 🎉

---

## 🎯 Integração com Dashboard

### Próxima Versão (Futuro):

```
Dashboard Streamlit
├── 📦 Produtos (já funciona)
├── 🚢 Cruzeiros (já funciona)
└── ✈️ Voos (NOVO!)
    ├── Tabela de voos encontrados
    ├── Filtros (preço, paradas, companhia)
    ├── Gráfico de evolução de preços
    └── Botão "Buscar novamente"
```

---

## 🔧 Troubleshooting

### Erro: "API Key inválida"
**Solução**: Verifique `config/deepseek_config.py`

### Erro: "Nenhum voo encontrado"
**Causas**:
1. Google Flights bloqueou (aguarde 5 min)
2. Datas muito distantes (Google limita a 11 meses)
3. Rota não existe

**Solução**: Tente outra combinação de datas/aeroportos

### Erro: "Timeout"
**Solução**: Aumente o `time.sleep(10)` em `flight_agent.py`

---

## 📝 Próximos Passos

### Agora:
1. ✅ Testar agent: `.\testar_voos.bat`
2. ✅ Ver se DeepSeek extrai corretamente
3. ✅ Ajustar se necessário

### Depois:
1. 🔮 Integrar com dashboard
2. 🔮 Salvar histórico de preços
3. 🔮 Alertas automáticos
4. 🔮 Comparação com outros sites (Decolar, MaxMilhas)

---

## 🎁 Dica Extra

### Melhor Época para Comprar:
- **6-8 semanas antes**: Geralmente preços mais baixos
- **Terça/Quarta**: Dias com preços melhores
- **Madrugada**: Companhias atualizam preços

### Alertas de Preço:
Configure `alert_price: 5000.0` no `flights.yaml` para ser notificado quando encontrar voos < R$ 5.000!

---

**Desenvolvido com 🤖 DeepSeek AI + ✈️ Paixão por viajar!**

**Tempo de desenvolvimento**: ~30 minutos  
**Custo por busca**: ~R$ 0,01  
**Economia potencial**: Milhares de reais! 💰

