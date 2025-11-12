# 🌐 Acesso Remoto ao Monitor de Preços

## 📱 Acessar pelo Celular (Mesma Rede WiFi)

### Passo 1: Descobrir seu IP Local

Já está nos logs quando você inicia:
```
Network URL: http://192.168.0.37:8501
```

Ou execute:
```powershell
ipconfig
```

Procure por: `Endereço IPv4: 192.168.0.XX`

### Passo 2: Acessar no Celular

No navegador do celular (conectado no mesmo WiFi):
```
http://192.168.0.37:8501
```

✅ **Funciona imediatamente!** Sem configuração adicional.

---

## 🌍 Acessar de Fora de Casa (Internet)

### Opção A: Ngrok (Mais Fácil)

1. **Instalar Ngrok**:
   - Baixe: https://ngrok.com/download
   - Extraia para: `C:\ngrok\`

2. **Criar conta grátis**:
   - https://dashboard.ngrok.com/signup
   - Copie seu token

3. **Configurar**:
```bash
cd C:\ngrok
ngrok config add-authtoken SEU_TOKEN_AQUI
```

4. **Iniciar túnel**:
```bash
ngrok http 8501
```

5. **Copiar URL**:
```
Forwarding: https://xxxx-xxxx-xxxx.ngrok-free.app -> http://localhost:8501
```

Acesse essa URL de qualquer lugar! 🌍

### Opção B: Port Forwarding no Roteador

1. **Acessar roteador**: http://192.168.0.1
2. **Login**: (geralmente admin/admin)
3. **Procurar**: "Port Forwarding" ou "Encaminhamento de Porta"
4. **Configurar**:
   - Porta Externa: 8501
   - Porta Interna: 8501
   - IP: 192.168.0.37 (seu PC)
   - Protocolo: TCP

5. **Descobrir IP Externo**:
```
http://meuip.com.br
```

6. **Acessar**:
```
http://SEU_IP_EXTERNO:8501
```

⚠️ **Segurança**: Seu IP externo fica exposto na internet!

---

## 🔒 Opção Segura: Tailscale (VPN Gratuita)

### Vantagens:
- ✅ Acesso seguro de qualquer lugar
- ✅ Sem expor portas
- ✅ Gratuito até 100 dispositivos
- ✅ Funciona em celular e PC

### Instalação:

1. **Criar conta**: https://tailscale.com/

2. **Instalar no PC**:
   - Baixe: https://tailscale.com/download/windows
   - Instale e faça login

3. **Instalar no Celular**:
   - Android: https://play.google.com/store/apps/details?id=com.tailscale.ipn
   - iOS: https://apps.apple.com/app/tailscale/id1470499037

4. **Conectar ambos** na mesma conta Tailscale

5. **Descobrir IP Tailscale do PC**:
```powershell
tailscale ip
```
Exemplo: `100.64.0.5`

6. **Acessar no celular**:
```
http://100.64.0.5:8501
```

✅ **Funciona de qualquer lugar com internet!**

---

## 🚀 Deploy em Servidor (Avançado)

### AWS EC2 (Free Tier)

1. **Criar instância Ubuntu**
2. **Instalar dependências**:
```bash
sudo apt update
sudo apt install python3-pip google-chrome-stable
pip3 install -r requirements.txt
```

3. **Copiar projeto**:
```bash
git clone https://github.com/mzmvyp/monitor_precos.git
cd monitor_precos
```

4. **Instalar ChromeDriver**:
```bash
python3 instalar_chromedriver_manual.py
```

5. **Rodar em background**:
```bash
nohup python3 run_monitor.py --interval 60 &
```

6. **Acessar**:
```
http://IP_DO_SERVIDOR:8501
```

### Custo:
- AWS EC2 t2.micro: **Grátis** (12 meses)
- Depois: ~$10/mês

---

## 📊 Comparação de Opções

| Opção | Facilidade | Custo | Acesso | Segurança |
|-------|-----------|-------|--------|-----------|
| **WiFi Local** | ⭐⭐⭐⭐⭐ | Grátis | Só em casa | ✅ Alta |
| **Ngrok** | ⭐⭐⭐⭐ | Grátis | Qualquer lugar | ⚠️ Média |
| **Port Forward** | ⭐⭐⭐ | Grátis | Qualquer lugar | ❌ Baixa |
| **Tailscale** | ⭐⭐⭐⭐ | Grátis | Qualquer lugar | ✅ Alta |
| **AWS/VPS** | ⭐⭐ | $10/mês | Qualquer lugar | ✅ Alta |

---

## 🎯 Recomendação

### Para uso pessoal:
1. **Em casa**: Use WiFi local (já funciona)
2. **Fora de casa**: Use **Tailscale** (mais fácil e seguro)

### Para compartilhar com outros:
Use **AWS EC2** ou **DigitalOcean**

---

## 🔧 Script de Inicialização Automática

Para o monitor iniciar automaticamente quando o PC ligar:

1. **Pressione** `Win + R`
2. **Digite**: `shell:startup`
3. **Copie** `iniciar_monitor.bat` para essa pasta

Pronto! Monitor inicia com o Windows.

---

**Qual opção você prefere? Posso te ajudar a configurar!**

