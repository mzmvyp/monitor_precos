# 📧 Como Configurar Alertas por Email (GRÁTIS!)

## 🎯 O Que Você Vai Receber:

Quando um produto baixar de preço, você receberá um email assim:

```
De: willian.prado@ymail.com
Para: willian.prado@ymail.com
Assunto: 🔥 ALERTA DE PREÇO: Memória XPG Lancer RGB 32GB

🎯 PROMOÇÃO DETECTADA!

Produto: Memória XPG Lancer RGB 32GB
Loja: TERABYTE

💰 PREÇO ATUAL: R$ 990.00
📉 PREÇO ANTERIOR: R$ 1099.00
🔻 REDUÇÃO: 9.9%

🎯 Preço Desejado: R$ 1000.00

🔗 COMPRAR AGORA:
https://www.terabyteshop.com.br/produto/...

⏰ Alerta enviado em: 12/11/2025 14:35:22
```

---

## 🚀 Configuração Rápida (3 minutos) - YAHOO MAIL

### Passo 1: Gerar Senha de App do Yahoo

⚠️ **IMPORTANTE**: Não é a senha normal do Yahoo!

1. **Acesse a página de segurança do Yahoo**:
   - Vá para: https://login.yahoo.com/account/security
   - Faça login com `willian.prado@ymail.com`

2. **Gere a senha de app**:
   - Role até "Gerar senha de app"
   - Nome do app: "Monitor de Preços"
   - Clique em "Gerar"
   - **COPIE A SENHA** (16 caracteres, ex: `abcdefghijklmnop`)
   
   **OU use este link direto**: https://login.yahoo.com/account/security/app-passwords

---

### Passo 2: Configurar no Sistema

Edite o arquivo `config/alerts.yaml`:

```yaml
email:
  enabled: true
  recipient: "willian.prado@ymail.com"  # ✅ Já configurado!
  
  smtp_server: "smtp.mail.yahoo.com"  # ✅ Já configurado!
  smtp_port: 587  # ✅ Já configurado!
  sender_email: "willian.prado@ymail.com"  # ✅ Já configurado!
  sender_password: ""  # ← COLE A SENHA DE APP AQUI (única coisa que falta!)
```

**Exemplo completo**:
```yaml
email:
  enabled: true
  recipient: "willian.prado@ymail.com"
  
  smtp_server: "smtp.mail.yahoo.com"
  smtp_port: 587
  sender_email: "willian.prado@ymail.com"
  sender_password: "abcdefghijklmnop"  # ← Senha de app do Yahoo
```

---

### Passo 3: Testar!

Execute:
```powershell
python -c "from src.alert_manager import AlertManager; am = AlertManager(); print('✅ Configuração OK!' if am._send_email('Teste', 'Email de teste do monitor de preços') else '❌ Erro na configuração')"
```

**Resultado esperado**:
```
✅ Email enviado para willian.prado@ymail.com
✅ Configuração OK!
```

Verifique sua caixa de entrada em `willian.prado@ymail.com`!

---

## ⚙️ Configurações de Alerta

### Quando Você Será Alertado:

Edite `config/alerts.yaml`:

```yaml
alerts:
  # Redução mínima para disparar alerta
  price_drop_threshold: 5.0  # 5% de redução
  
  # Alertar quando ficar abaixo do preço desejado
  below_desired_price: true
  
  # Não enviar mais de 1 alerta a cada X horas do mesmo produto
  cooldown_hours: 6
  
  # Produtos prioritários (alerta com redução menor)
  priority_products:
    - "mem-ddr5-32gb-xpg"  # Memória XPG (você perdeu a promoção)
    - "cpu-ryzen-7-8700f"  # Ryzen 8700F (acabou de adicionar)
  
  # Redução mínima para produtos prioritários
  priority_threshold: 2.0  # 2% já dispara alerta!
```

---

## 📊 Exemplos de Alertas:

### Exemplo 1: Produto Prioritário (Memória XPG)
```
Preço anterior: R$ 1.099,00
Preço atual: R$ 1.077,00
Redução: 2%

✅ ALERTA ENVIADO! (produto prioritário, threshold 2%)
```

### Exemplo 2: Produto Normal
```
Preço anterior: R$ 1.500,00
Preço atual: R$ 1.425,00
Redução: 5%

✅ ALERTA ENVIADO! (threshold padrão 5%)
```

### Exemplo 3: Abaixo do Preço Desejado
```
Preço desejado: R$ 1.300,00
Preço atual: R$ 1.289,00

✅ ALERTA ENVIADO! (abaixo do preço desejado)
```

### Exemplo 4: Cooldown Ativo
```
Último alerta: 3 horas atrás
Cooldown: 6 horas

⏳ ALERTA NÃO ENVIADO (aguardando cooldown)
```

---

## 🔧 Solução de Problemas:

### Erro: "Username and Password not accepted"
**Causa**: Senha de app incorreta ou verificação em 2 etapas não ativada.
**Solução**: Refaça o Passo 2.

### Erro: "SMTPAuthenticationError"
**Causa**: Email ou senha incorretos.
**Solução**: Verifique `sender_email` e `sender_password` em `config/alerts.yaml`.

### Email não chega
**Causa**: Pode estar na pasta de spam.
**Solução**: 
1. Verifique a pasta de spam/lixo eletrônico
2. Marque como "Não é spam"
3. Adicione o remetente aos contatos

---

## 🎉 Pronto!

Agora você receberá alertas automáticos quando:
- ✅ Preço cair 5% ou mais
- ✅ Preço ficar abaixo do desejado
- ✅ Produtos prioritários caírem 2% ou mais

**Nunca mais perca uma promoção!** 🚀

---

## 📱 Alternativa: Notificações no Celular

### Opção 1: Email no Celular
- Configure o app de email do seu celular
- Ative notificações push para o email `willian.prado@ymail.com`
- Receberá alertas instantâneos!

### Opção 2: IFTTT (Grátis)
1. Instale o app IFTTT: https://ifttt.com/
2. Crie um applet: "Se receber email com assunto 'ALERTA DE PREÇO' → Enviar notificação"
3. Receberá notificações push no celular!

---

**Custo Total**: R$ 0,00 (100% GRÁTIS!) ✅

