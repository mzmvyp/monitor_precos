# 🪟 Instalação no Windows - Guia Rápido

## ❌ Problema:
```
RuntimeError: Falha ao instalar ChromeDriver automaticamente.
```

## ✅ Solução (3 passos simples):

### **Passo 1: Verifique se o Google Chrome está instalado**

1. Abra o Chrome
2. Clique nos 3 pontinhos (canto superior direito)
3. **Ajuda** → **Sobre o Google Chrome**
4. Veja a versão (ex: `131.0.6778.86`)

**Se o Chrome NÃO estiver instalado:**
- Baixe aqui: https://www.google.com/chrome/
- Instale e volte ao Passo 1

---

### **Passo 2: Execute o script de instalação do ChromeDriver**

Abra o **PowerShell** ou **CMD** na pasta do projeto e execute:

```powershell
python instalar_chromedriver_manual.py
```

**O que o script faz:**
- ✅ Detecta automaticamente a versão do Chrome
- ✅ Baixa o ChromeDriver compatível
- ✅ Instala em `C:\Users\SeuUsuario\.chromedriver\`
- ✅ Configura a variável de ambiente no arquivo `.env`

**Saída esperada:**
```
======================================================================
🔧 INSTALADOR MANUAL DO CHROMEDRIVER
======================================================================

🔍 Detectando versão do Chrome...
✅ Chrome detectado: 131.0.6778.86

🔍 Buscando ChromeDriver compatível com Chrome 131.0.6778.86...
✅ ChromeDriver compatível: 131.0.6778.108

📁 Diretório de instalação: C:\Users\SeuUsuario\.chromedriver

📥 Baixando ChromeDriver 131.0.6778.108 para win64...
✅ Download concluído (8.5 MB)
📦 Extraindo para C:\Users\SeuUsuario\.chromedriver...
✅ ChromeDriver instalado: C:\Users\SeuUsuario\.chromedriver\chromedriver.exe

✅ Configurado em .env: CHROMEDRIVER_PATH=C:\Users\SeuUsuario\.chromedriver\chromedriver.exe

======================================================================
✅ INSTALAÇÃO CONCLUÍDA COM SUCESSO!
======================================================================
```

---

### **Passo 3: Execute o Dashboard**

```powershell
streamlit run streamlit_app_premium.py
```

**No dashboard:**
1. Clique em **"🔄 Atualizar Preços"** na barra lateral
2. Aguarde a coleta (pode demorar alguns minutos)
3. Os preços serão atualizados! ✅

---

## 🧪 Testar se está funcionando:

```powershell
python -c "import os; print('ChromeDriver:', os.getenv('CHROMEDRIVER_PATH'))"
```

**Resultado esperado:**
```
ChromeDriver: C:\Users\SeuUsuario\.chromedriver\chromedriver.exe
```

---

## 🆘 Problemas Comuns:

### **Erro: "python não é reconhecido"**

**Solução:**
```powershell
# Use py ao invés de python
py instalar_chromedriver_manual.py
```

Ou adicione Python ao PATH:
1. Painel de Controle → Sistema → Configurações avançadas
2. Variáveis de ambiente
3. Editar variável PATH
4. Adicionar: `C:\Python312\` (ou onde o Python está instalado)

---

### **Erro: "Chrome não encontrado"**

**Solução:**
1. Instale o Chrome: https://www.google.com/chrome/
2. Execute novamente: `python instalar_chromedriver_manual.py`

---

### **Erro: "ModuleNotFoundError: No module named 'selenium'"**

**Solução:**
```powershell
pip install selenium webdriver-manager
```

---

### **Preços continuam desatualizados**

**Solução:**
1. Feche o Streamlit (Ctrl+C)
2. Feche o PowerShell/CMD
3. Abra um NOVO terminal
4. Execute novamente:
   ```powershell
   streamlit run streamlit_app_premium.py
   ```
5. Clique em "Atualizar Preços"

**Por quê?** A variável de ambiente do .env só é carregada quando o programa inicia.

---

### **Erro: "invalid session id" ou "Chrome crashed"**

**Solução:**
1. Atualize o Chrome para a versão mais recente
2. Execute novamente: `python instalar_chromedriver_manual.py`
3. Reinicie o dashboard

---

## 🔍 Verificar Logs:

Se continuar com problemas, rode com logs detalhados:

```powershell
python -c "
from src.price_monitor import PriceMonitor
from pathlib import Path
import logging

logging.basicConfig(level=logging.DEBUG)

monitor = PriceMonitor(
    config_path=Path('config/products.yaml'),
    history_path=Path('data/price_history.csv')
)

print('Testando scraping...')
snapshots = monitor.collect(product_ids=['cpu-ryzen-5-9600x'])
print(f'Coletados: {len(snapshots)} preços')
"
```

---

## 📂 Estrutura de Arquivos:

Após a instalação, você terá:

```
C:\Users\SeuUsuario\
└── .chromedriver\
    └── chromedriver.exe    ← ChromeDriver instalado aqui

C:\Users\SeuUsuario\...\monitor_precos\
├── .env                    ← Variável CHROMEDRIVER_PATH configurada aqui
├── instalar_chromedriver_manual.py
├── streamlit_app_premium.py
└── config/
    └── products.yaml
```

---

## 🎯 Checklist:

- [ ] Google Chrome instalado e atualizado
- [ ] Script `instalar_chromedriver_manual.py` executado com sucesso
- [ ] Arquivo `.env` criado com `CHROMEDRIVER_PATH`
- [ ] ChromeDriver em `C:\Users\SeuUsuario\.chromedriver\chromedriver.exe`
- [ ] Dashboard abre sem erros
- [ ] Botão "Atualizar Preços" funciona
- [ ] Preços atualizados aparecem no dashboard

---

## 💡 Dica Extra:

Para atualizar automaticamente todo dia, crie um **agendador de tarefas** do Windows:

1. Abra "Agendador de Tarefas" (Task Scheduler)
2. Criar Tarefa Básica
3. Nome: "Monitor de Preços"
4. Gatilho: Diário (ex: 8:00 AM)
5. Ação: Executar script Python
   - Programa: `C:\Python312\python.exe`
   - Argumentos: `-m src.price_monitor`
   - Iniciar em: `C:\Users\...\monitor_precos\`

Assim o sistema coleta preços automaticamente e envia emails quando tiver promoção! 🚀

---

## 📧 Suporte:

Se continuar com problemas:
1. Copie a mensagem de erro completa
2. Execute: `python instalar_chromedriver_manual.py`
3. Cole o resultado
4. Informe a versão do Chrome (Menu → Ajuda → Sobre)
