"""
Script para limpar completamente o repositório GitHub (deletar todos os arquivos).
Use com cuidado!
"""
import os
import sys
import requests
import urllib3
from pathlib import Path

# Desabilitar warnings de SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configurações
REPO_OWNER = "mzmvyp"
REPO_NAME = "monitor_precos"
BRANCH = "main"
BASE_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}"

def get_github_token():
    """Obtém o token do GitHub."""
    script_dir = Path(__file__).parent.absolute()
    token_file = script_dir / ".github_token"
    if token_file.exists():
        return token_file.read_text(encoding="utf-8").strip()
    return os.environ.get("GITHUB_TOKEN")

def get_all_files_in_repo(session):
    """Lista todos os arquivos no repositório."""
    url = f"{BASE_URL}/git/trees/{BRANCH}?recursive=1"
    response = session.get(url)
    
    if response.status_code != 200:
        print(f"❌ Erro ao listar arquivos: {response.json().get('message', 'Erro desconhecido')}")
        return []
    
    tree = response.json().get("tree", [])
    # Filtrar apenas arquivos (não pastas)
    files = [item for item in tree if item.get("type") == "blob"]
    return files

def delete_file_from_repo(session, file_path, sha):
    """Deleta um arquivo do repositório."""
    url = f"{BASE_URL}/contents/{file_path}"
    
    data = {
        "message": f"Limpar: remover {file_path}",
        "sha": sha,
        "branch": BRANCH,
    }
    
    response = session.delete(url, json=data)
    return response.status_code in [200, 204]

def limpar_repositorio():
    """Limpa completamente o repositório GitHub."""
    token = get_github_token()
    
    if not token:
        print("❌ Token do GitHub não encontrado!")
        return False
    
    session = requests.Session()
    session.headers.update({
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    })
    session.verify = False  # Desabilitar SSL para proxy corporativo
    
    print("🔍 Listando arquivos no repositório...")
    files = get_all_files_in_repo(session)
    
    if not files:
        print("✅ Repositório já está vazio ou erro ao listar arquivos")
        return True
    
    print(f"📋 Encontrados {len(files)} arquivos para deletar\n")
    
    print("⚠️  ATENÇÃO: Isso vai DELETAR TODOS os arquivos do repositório!")
    resposta = input("Digite 'SIM' para confirmar: ")
    
    if resposta != "SIM":
        print("❌ Operação cancelada")
        return False
    
    print(f"\n🗑️  Deletando {len(files)} arquivos...\n")
    
    success_count = 0
    error_count = 0
    
    # Deletar em lotes (API do GitHub tem limites)
    for i, file_item in enumerate(files, 1):
        file_path = file_item.get("path")
        sha = file_item.get("sha")
        
        if delete_file_from_repo(session, file_path, sha):
            print(f"✅ [{i}/{len(files)}] {file_path}")
            success_count += 1
        else:
            print(f"❌ [{i}/{len(files)}] {file_path}")
            error_count += 1
    
    print(f"\n✅ {success_count} arquivos deletados")
    if error_count > 0:
        print(f"❌ {error_count} arquivos com erro")
    
    return error_count == 0

if __name__ == "__main__":
    print("=" * 50)
    print("  LIMPAR REPOSITÓRIO GITHUB")
    print("=" * 50)
    print()
    
    success = limpar_repositorio()
    
    if success:
        print("\n✅ Repositório limpo com sucesso!")
        print("   Agora você pode sincronizar novamente com: python sync_github.py --disable-ssl-verify")
    else:
        print("\n❌ Erro ao limpar repositório")
        sys.exit(1)

