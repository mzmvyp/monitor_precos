"""Teste rápido do token do GitHub."""
import os
import sys
import requests
import urllib3
from pathlib import Path

# Desabilitar warnings de SSL quando verify=False
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Obter diretório do script e mudar para ele
script_dir = Path(__file__).parent.absolute()
os.chdir(script_dir)

# Ler token
token_file = script_dir / ".github_token"
if token_file.exists():
    token = token_file.read_text(encoding="utf-8").strip()
    print(f"✅ Token encontrado: {token[:20]}...")
else:
    print("❌ Arquivo .github_token não encontrado")
    print(f"   Procurando em: {token_file}")
    sys.exit(1)

# Testar conexão
REPO_OWNER = "mzmvyp"
REPO_NAME = "monitor_precos"
BASE_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}"

session = requests.Session()
session.headers.update({
    "Authorization": f"token {token}",
    "Accept": "application/vnd.github.v3+json",
})

# Desabilitar verificação SSL para proxy corporativo
session.verify = False

print(f"\n🔍 Testando conexão com {REPO_OWNER}/{REPO_NAME}...")

try:
    response = session.get(BASE_URL)
    
    if response.status_code == 200:
        repo_data = response.json()
        print(f"✅ Conexão OK!")
        print(f"   Repositório: {repo_data.get('full_name')}")
        print(f"   Branch padrão: {repo_data.get('default_branch')}")
        print(f"   Visibilidade: {repo_data.get('visibility', 'public')}")
        print(f"\n✅ Token válido! Pode usar sync_github.py")
    elif response.status_code == 401:
        print(f"❌ Token inválido ou expirado (401 Unauthorized)")
        print(f"   Resposta: {response.json().get('message', 'Erro desconhecido')}")
    elif response.status_code == 404:
        print(f"❌ Repositório não encontrado (404)")
        print(f"   Verifique se o repositório existe: {REPO_OWNER}/{REPO_NAME}")
    else:
        print(f"❌ Erro: {response.status_code}")
        print(f"   Resposta: {response.text[:200]}")
        
except Exception as e:
    print(f"❌ Erro ao conectar: {e}")

