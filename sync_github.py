"""
Script para sincronizar o projeto com GitHub usando API (sem Git CLI).
Requer um token de acesso pessoal do GitHub.
"""
import os
import sys
import base64
import json
import argparse
import urllib3
from pathlib import Path
from typing import Optional
import requests

# Desabilitar warnings de SSL quando verify=False
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configurações
REPO_OWNER = "mzmvyp"
REPO_NAME = "monitor_precos"
BRANCH = "main"
BASE_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}"

# Arquivos e pastas a ignorar (baseado no .gitignore)
IGNORE_PATTERNS = {
    "__pycache__",
    ".pyc",
    ".pyo",
    ".pyd",
    ".git",
    ".vscode",
    ".idea",
    "venv",
    "env",
    "ENV",
    ".chromedriver",
    "*.log",
    "*.backup",
    "*.tmp",
    "Thumbs.db",
    ".DS_Store",
    "arquivos_novos",
    "data/*.backup*",
    "data/*.tmp",
}


def get_github_token() -> Optional[str]:
    """Obtém o token do GitHub de variável de ambiente ou arquivo."""
    # Tentar variável de ambiente
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        return token
    
    # Tentar arquivo .github_token (não versionado)
    # Usar caminho absoluto baseado no script
    script_dir = Path(__file__).parent.absolute()
    token_file = script_dir / ".github_token"
    if token_file.exists():
        return token_file.read_text(encoding="utf-8").strip()
    
    return None


def should_ignore(path: Path) -> bool:
    """Verifica se o arquivo/pasta deve ser ignorado."""
    path_str = str(path)
    
    # Ignorar arquivos na raiz que começam com ponto (exceto .gitignore)
    if path.name.startswith(".") and path.name != ".gitignore":
        return True
    
    # Verificar padrões de ignore
    for pattern in IGNORE_PATTERNS:
        if pattern in path_str:
            return True
    
    # Ignorar arquivos de dados sensíveis (exceto CSVs principais)
    if "data" in path_str and path.suffix in [".backup", ".tmp"]:
        return True
    
    return False


def get_all_files(root: Path) -> list[Path]:
    """Lista todos os arquivos do projeto (respeitando .gitignore)."""
    files = []
    
    for item in root.rglob("*"):
        if item.is_file() and not should_ignore(item):
            files.append(item)
    
    return sorted(files)


def get_file_content(file_path: Path) -> str:
    """Lê o conteúdo do arquivo e retorna em base64."""
    try:
        content = file_path.read_bytes()
        return base64.b64encode(content).decode("utf-8")
    except Exception as e:
        print(f"❌ Erro ao ler {file_path}: {e}")
        return None


def get_file_sha(session: requests.Session, file_path: str) -> Optional[str]:
    """Obtém o SHA do arquivo no GitHub (se existir)."""
    url = f"{BASE_URL}/contents/{file_path}"
    response = session.get(url, params={"ref": BRANCH})
    
    if response.status_code == 200:
        return response.json().get("sha")
    return None


def upload_file(
    session: requests.Session,
    file_path: Path,
    relative_path: str,
    content: str,
    message: str = "Atualizar arquivo"
) -> bool:
    """Faz upload de um arquivo para o GitHub."""
    url = f"{BASE_URL}/contents/{relative_path}"
    
    try:
        # Obter SHA se o arquivo já existe
        sha = get_file_sha(session, relative_path)
        
        data = {
            "message": message,
            "content": content,
            "branch": BRANCH,
        }
        
        if sha:
            data["sha"] = sha
        
        response = session.put(url, json=data)
        
        if response.status_code in [200, 201]:
            print(f"✅ {relative_path}")
            return True
        else:
            error_data = response.json() if response.content else {}
            error_msg = error_data.get("message", "Erro desconhecido")
            
            # Verificar se é erro de permissão
            if "not accessible" in error_msg.lower() or "permission" in error_msg.lower():
                print(f"⚠️  {relative_path}: Token sem permissão (pode ser restrição corporativa)")
            else:
                print(f"❌ {relative_path}: {error_msg}")
            return False
    except requests.exceptions.SSLError as e:
        print(f"❌ {relative_path}: Erro SSL - {e}")
        return False
    except Exception as e:
        print(f"❌ {relative_path}: {e}")
        return False


def sync_to_github(dry_run: bool = False, disable_ssl_verify: bool = False):
    """Sincroniza todos os arquivos com o GitHub."""
    # Obter diretório do script e mudar para ele
    script_dir = Path(__file__).parent.absolute()
    os.chdir(script_dir)
    
    token = get_github_token()
    
    if not token:
        print("❌ Token do GitHub não encontrado!")
        print("\n📝 Para obter um token:")
        print("1. Acesse: https://github.com/settings/tokens")
        print("2. Clique em 'Generate new token (classic)'")
        print("3. Dê um nome (ex: 'Monitor Preços Sync')")
        print("4. Marque a opção 'repo' (acesso completo aos repositórios)")
        print("5. Clique em 'Generate token'")
        print("6. Copie o token e salve em um arquivo .github_token na raiz do projeto")
        print("   OU defina a variável de ambiente: set GITHUB_TOKEN=seu_token")
        return False
    
    # Criar sessão com autenticação
    session = requests.Session()
    session.headers.update({
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    })
    
    # Configurar verificação SSL
    if disable_ssl_verify:
        session.verify = False
        print("⚠️  Verificação SSL desabilitada (proxy corporativo)\n")
    
    # Verificar se o repositório existe e temos acesso
    try:
        response = session.get(BASE_URL)
        if response.status_code != 200:
            error_msg = response.json().get('message', 'Erro desconhecido') if response.content else 'Erro desconhecido'
            print(f"❌ Erro ao acessar repositório: {error_msg}")
            
            # Verificar se é problema de permissão
            if "not accessible" in error_msg.lower() or "permission" in error_msg.lower():
                print("\n⚠️  PROBLEMA DE PERMISSÃO DETECTADO:")
                print("   O token pode não ter permissões suficientes ou há restrição corporativa.")
                print("   Possíveis causas:")
                print("   1. Token sem permissão 'repo' (acesso completo)")
                print("   2. Repositório privado e token sem acesso")
                print("   3. Restrição de firewall/proxy corporativo bloqueando escrita")
                print("   4. Política corporativa impedindo acesso via API")
                print("\n💡 Se for restrição corporativa, a sincronização automática não funcionará.")
                print("   Você pode fazer upload manual via interface web do GitHub.")
            return False
    except requests.exceptions.SSLError as e:
        print(f"❌ Erro SSL: {e}")
        print("💡 Tente usar a flag --disable-ssl-verify para proxies corporativos")
        return False
    
    print(f"📦 Sincronizando com {REPO_OWNER}/{REPO_NAME}...")
    print(f"🌿 Branch: {BRANCH}\n")
    
    # Obter diretório raiz do projeto
    root = script_dir
    
    # Listar todos os arquivos
    files = get_all_files(root)
    
    if dry_run:
        print(f"🔍 Modo dry-run: {len(files)} arquivos seriam sincronizados\n")
        for f in files[:10]:  # Mostrar apenas os primeiros 10
            print(f"  - {f}")
        if len(files) > 10:
            print(f"  ... e mais {len(files) - 10} arquivos")
        return True
    
    print(f"📤 Enviando {len(files)} arquivos...\n")
    
    success_count = 0
    error_count = 0
    
    for file_path in files:
        # Calcular caminho relativo
        try:
            relative_path = file_path.relative_to(root).as_posix()
        except ValueError:
            continue
        
        # Ler conteúdo
        content = get_file_content(file_path)
        if content is None:
            error_count += 1
            continue
        
        # Fazer upload
        if upload_file(session, file_path, relative_path, content, f"Sync: {relative_path}"):
            success_count += 1
        else:
            error_count += 1
    
    print(f"\n✅ {success_count} arquivos sincronizados")
    if error_count > 0:
        print(f"❌ {error_count} arquivos com erro")
    
    return error_count == 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Sincroniza o projeto com GitHub usando API (sem Git CLI)"
    )
    parser.add_argument(
        "--dry-run",
        "-d",
        action="store_true",
        help="Modo dry-run (não envia arquivos, apenas lista)"
    )
    parser.add_argument(
        "--disable-ssl-verify",
        action="store_true",
        help="Desabilitar verificação SSL (útil para proxies corporativos)"
    )
    
    args = parser.parse_args()
    
    if args.dry_run:
        print("🔍 MODO DRY-RUN (nenhum arquivo será enviado)\n")
    
    success = sync_to_github(dry_run=args.dry_run, disable_ssl_verify=args.disable_ssl_verify)
    
    if success:
        print("\n✅ Sincronização concluída!")
    else:
        print("\n❌ Sincronização falhou. Verifique os erros acima.")
        sys.exit(1)

