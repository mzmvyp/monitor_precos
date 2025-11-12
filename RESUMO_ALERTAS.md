# 📧 Sistema de Alertas Implementado!

## ✅ O Que Foi Feito:

### 1. 🔍 Ryzen 7 8700F Adicionado
**Produto**: Processador AMD Ryzen 7 8700F
**Lojas monitoradas**:
- ✅ Terabyte: R$ 1.389,90
- ✅ Kabum: R$ 1.699,99
- ✅ Pichau: R$ 1.389,99

**Preço desejado**: R$ 1.300,00

---

### 2. 📧 Sistema de Alertas por Email (GRÁTIS!)

#### Como Funciona:
```
1. Monitor coleta preços a cada 30 minutos
2. Compara com preço anterior
3. Se houver redução significativa → ENVIA EMAIL!
4. Você recebe alerta no willian.prado@ymail.com
```

#### Quando Você Será Alertado:

| Situação | Threshold | Exemplo |
|----------|-----------|---------|
| **Produto Normal** | 5% redução | R$ 1.500 → R$ 1.425 ✅ |
| **Produto Prioritário** | 2% redução | R$ 1.099 → R$ 1.077 ✅ |
| **Abaixo do Desejado** | Qualquer | R$ 1.300 → R$ 1.289 ✅ |

#### Produtos Prioritários:
- ✅ Memória XPG Lancer RGB 32GB (você perdeu a promoção)
- ✅ Ryzen 7 8700F (acabou de adicionar)

---

## 🚀 Como Ativar os Alertas:

### Passo 1: Configure o Email (5 minutos)

Siga o guia completo em: **`CONFIGURAR_EMAIL.md`**

**Resumo rápido**:
1. Crie/use um Gmail
2. Ative verificação em 2 etapas
3. Gere senha de app: https://myaccount.google.com/apppasswords
4. Edite `config/alerts.yaml`:
   ```yaml
   sender_email: "seuemail@gmail.com"
   sender_password: "sua senha de app aqui"
   ```

---

### Passo 2: Teste o Sistema

#### Teste 1: Ryzen 8700F
```powershell
.\testar_ryzen_8700f.bat
```

**Resultado esperado**:
```
TERABYTE: R$ 1389.90
KABUM: R$ 1699.99
PICHAU: R$ 1389.99
```

#### Teste 2: Email de Alerta
```powershell
python -c "from src.alert_manager import AlertManager; am = AlertManager(); am._send_email('🔥 Teste', 'Email de teste do monitor')"
```

**Resultado esperado**:
```
✅ Email enviado para willian.prado@ymail.com
```

---

### Passo 3: Inicie o Monitor

```powershell
.\iniciar_monitor.bat
```

**O que acontece**:
1. ✅ Coleta preços a cada 30 minutos
2. ✅ Compara com preços anteriores
3. ✅ Envia email se houver redução
4. ✅ Dashboard atualiza em tempo real

---

## 📊 Exemplo de Alerta Real:

### Cenário: Memória XPG em Promoção

**Email que você receberá**:
```
De: monitor.precos.willian@gmail.com
Para: willian.prado@ymail.com
Assunto: 🔥 ALERTA DE PREÇO: Memória XPG Lancer RGB 32GB

🎯 PROMOÇÃO DETECTADA!

Produto: Memória XPG Lancer RGB 32GB (DDR5 6000MHz)
Loja: TERABYTE

💰 PREÇO ATUAL: R$ 990.00
📉 PREÇO ANTERIOR: R$ 1099.00
🔻 REDUÇÃO: 9.9%

🎯 Preço Desejado: R$ 1000.00

🔗 COMPRAR AGORA:
https://www.terabyteshop.com.br/produto/...

⏰ Alerta enviado em: 12/11/2025 14:35:22

---
Monitor de Preços Automático
Não perca mais promoções! 🚀
```

**Você recebe no celular/email em TEMPO REAL!** ⚡

---

## 🎯 Configurações Personalizadas:

### Ajustar Sensibilidade dos Alertas

Edite `config/alerts.yaml`:

```yaml
alerts:
  # Mais sensível (alerta com 3% de redução)
  price_drop_threshold: 3.0
  
  # Menos sensível (alerta apenas com 10% de redução)
  price_drop_threshold: 10.0
  
  # Produtos prioritários (alerta com 1% de redução)
  priority_threshold: 1.0
  
  # Cooldown (não enviar mais de 1 alerta a cada X horas)
  cooldown_hours: 6  # Padrão: 6 horas
```

---

### Adicionar Mais Produtos Prioritários

```yaml
priority_products:
  - "mem-ddr5-32gb-xpg"
  - "cpu-ryzen-7-8700f"
  - "motherboard-asus-tuf-b650m-e"  # ← Adicione aqui
  - "fonte-corsair-rm850x"  # ← E aqui
```

---

## 📱 Receber no Celular:

### Opção 1: App de Email
1. Configure o app de email do celular
2. Adicione `willian.prado@ymail.com`
3. Ative notificações push
4. ✅ Receberá alertas instantâneos!

### Opção 2: IFTTT (Grátis)
1. Instale: https://ifttt.com/
2. Crie applet: "Email → Notificação"
3. ✅ Push no celular!

---

## 🔧 Arquivos Criados/Modificados:

| Arquivo | Descrição |
|---------|-----------|
| `config/products.yaml` | ✅ Ryzen 8700F adicionado |
| `config/alerts.yaml` | ✅ Configuração de alertas |
| `src/alert_manager.py` | ✅ Sistema de alertas |
| `src/price_monitor.py` | ✅ Integração de alertas |
| `CONFIGURAR_EMAIL.md` | ✅ Guia de configuração |
| `testar_ryzen_8700f.bat` | ✅ Script de teste |

---

## 🎉 Resumo:

| Feature | Status | Custo |
|---------|--------|-------|
| **Monitorar Ryzen 8700F** | ✅ Pronto | R$ 0 |
| **Alertas por Email** | ✅ Pronto | R$ 0 |
| **Produtos Prioritários** | ✅ Configurado | R$ 0 |
| **Cooldown Inteligente** | ✅ Ativo | R$ 0 |
| **Notificações Celular** | ✅ Disponível | R$ 0 |

**CUSTO TOTAL**: R$ 0,00 (100% GRÁTIS!) 🎉

---

## 🚀 Próximos Passos:

1. ✅ Leia `CONFIGURAR_EMAIL.md`
2. ✅ Configure o Gmail (5 minutos)
3. ✅ Teste o Ryzen 8700F: `.\testar_ryzen_8700f.bat`
4. ✅ Teste o email de alerta
5. ✅ Inicie o monitor: `.\iniciar_monitor.bat`
6. ✅ Configure notificações no celular (opcional)

---

**Nunca mais perca uma promoção!** 🔥

**Dúvidas?** Consulte `CONFIGURAR_EMAIL.md` para guia completo.

