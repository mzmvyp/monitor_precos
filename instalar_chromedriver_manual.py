#!/usr/bin/env python3
"""
Script para instalar ChromeDriver manualmente no Windows.

Resolve o problema: "Falha ao instalar ChromeDriver automaticamente"
"""
import io
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from urllib.request import urlopen


def get_chrome_version_windows():
    """Detecta a versão do Chrome no Windows."""
    try:
        # Método 1: Registry
        import winreg
        key_path = r"SOFTWARE\Google\Chrome\BLBeacon"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as key:
            version = winreg.QueryValueEx(key, "version")[0]
            return version
    except:
        pass

    try:
        # Método 2: Registry HKLM
        import winreg
        key_path = r"SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\Google Chrome"
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
            version = winreg.QueryValueEx(key, "version")[0]
            return version
    except:
        pass

    try:
        # Método 3: Executar chrome.exe --version
        chrome_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
        ]

        for chrome_path in chrome_paths:
            if os.path.exists(chrome_path):
                result = subprocess.run(
                    [chrome_path, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    match = re.search(r"(\d+\.\d+\.\d+\.\d+)", result.stdout)
                    if match:
                        return match.group(1)
    except:
        pass

    return None


def get_chrome_version_linux():
    """Detecta a versão do Chrome no Linux."""
    try:
        commands = [
            ["google-chrome", "--version"],
            ["chromium", "--version"],
            ["chromium-browser", "--version"],
        ]

        for cmd in commands:
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    match = re.search(r"(\d+\.\d+\.\d+\.\d+)", result.stdout)
                    if match:
                        return match.group(1)
            except:
                continue
    except:
        pass

    return None


def get_chrome_version_mac():
    """Detecta a versão do Chrome no macOS."""
    try:
        chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        if os.path.exists(chrome_path):
            result = subprocess.run(
                [chrome_path, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                match = re.search(r"(\d+\.\d+\.\d+\.\d+)", result.stdout)
                if match:
                    return match.group(1)
    except:
        pass

    return None


def get_chrome_version():
    """Detecta a versão do Chrome instalado."""
    system = platform.system()

    if system == "Windows":
        return get_chrome_version_windows()
    elif system == "Linux":
        return get_chrome_version_linux()
    elif system == "Darwin":
        return get_chrome_version_mac()

    return None


def get_chromedriver_version_for_chrome(chrome_version):
    """Busca a versão do ChromeDriver compatível com a versão do Chrome."""
    # Extrair major version (ex: "131.0.6778.86" -> "131")
    major_version = chrome_version.split(".")[0]

    try:
        # API do Chrome for Testing
        url = "https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json"

        print(f"🔍 Buscando ChromeDriver compatível com Chrome {chrome_version}...")

        with urlopen(url, timeout=10) as response:
            data = json.loads(response.read())

        # Procurar versão exata ou mais próxima
        versions = data.get("versions", [])

        # Filtrar versões do mesmo major
        matching_versions = [
            v for v in versions
            if v["version"].startswith(f"{major_version}.")
        ]

        if not matching_versions:
            print(f"⚠️ Nenhuma versão encontrada para Chrome {major_version}")
            return None

        # Pegar a versão mais recente do mesmo major
        latest = matching_versions[-1]

        return latest

    except Exception as e:
        print(f"❌ Erro ao buscar versão do ChromeDriver: {e}")
        return None


def download_chromedriver(version_info, install_dir):
    """Baixa e instala o ChromeDriver."""
    system = platform.system()

    # Determinar plataforma
    if system == "Windows":
        platform_name = "win64" if sys.maxsize > 2**32 else "win32"
    elif system == "Linux":
        platform_name = "linux64"
    elif system == "Darwin":
        platform_name = "mac-x64" if platform.machine() == "x86_64" else "mac-arm64"
    else:
        print(f"❌ Sistema operacional não suportado: {system}")
        return False

    # Procurar download para a plataforma
    downloads = version_info.get("downloads", {}).get("chromedriver", [])

    download_info = None
    for d in downloads:
        if d["platform"] == platform_name:
            download_info = d
            break

    if not download_info:
        print(f"❌ ChromeDriver não disponível para {platform_name}")
        return False

    url = download_info["url"]

    print(f"📥 Baixando ChromeDriver {version_info['version']} para {platform_name}...")
    print(f"   URL: {url}")

    try:
        # Baixar arquivo ZIP
        with urlopen(url, timeout=60) as response:
            zip_data = response.read()

        print(f"✅ Download concluído ({len(zip_data) / 1024 / 1024:.1f} MB)")

        # Extrair ZIP
        print(f"📦 Extraindo para {install_dir}...")

        with zipfile.ZipFile(io.BytesIO(zip_data)) as zip_file:
            zip_file.extractall(install_dir)

        # Encontrar o executável
        exe_name = "chromedriver.exe" if system == "Windows" else "chromedriver"

        # O ZIP geralmente vem em uma pasta chromedriver-platform/chromedriver
        chromedriver_path = None
        for root, dirs, files in os.walk(install_dir):
            if exe_name in files:
                chromedriver_path = Path(root) / exe_name
                break

        if not chromedriver_path:
            print(f"❌ Executável {exe_name} não encontrado após extração")
            return False

        # Mover para o diretório raiz de instalação
        final_path = install_dir / exe_name

        if chromedriver_path != final_path:
            if final_path.exists():
                final_path.unlink()
            shutil.move(str(chromedriver_path), str(final_path))

            # Limpar pasta temporária
            temp_dir = chromedriver_path.parent
            if temp_dir != install_dir:
                shutil.rmtree(temp_dir, ignore_errors=True)

        # Dar permissão de execução (Linux/Mac)
        if system in ["Linux", "Darwin"]:
            os.chmod(final_path, 0o755)

        print(f"✅ ChromeDriver instalado: {final_path}")

        return final_path

    except Exception as e:
        print(f"❌ Erro ao baixar/instalar: {e}")
        import traceback
        traceback.print_exc()
        return False


def configure_environment(chromedriver_path):
    """Configura variável de ambiente para o ChromeDriver."""
    system = platform.system()

    # Criar arquivo .env se não existir
    env_file = Path(".env")

    env_content = ""
    if env_file.exists():
        env_content = env_file.read_text(encoding="utf-8")

    # Remover linha antiga se existir
    lines = [line for line in env_content.split("\n") if not line.startswith("CHROMEDRIVER_PATH=")]

    # Adicionar nova linha
    lines.append(f"CHROMEDRIVER_PATH={chromedriver_path}")

    # Salvar
    env_file.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")

    print(f"✅ Configurado em .env: CHROMEDRIVER_PATH={chromedriver_path}")

    # Configurar no ambiente atual
    os.environ["CHROMEDRIVER_PATH"] = str(chromedriver_path)

    if system == "Windows":
        print("\n⚠️ IMPORTANTE (Windows):")
        print("   Para usar em novas sessões, adicione às variáveis de ambiente do Windows:")
        print(f"   Nome: CHROMEDRIVER_PATH")
        print(f"   Valor: {chromedriver_path}")
        print("\n   Ou rode sempre no mesmo terminal que executou este script.")


def main():
    """Função principal."""
    print("=" * 70)
    print("🔧 INSTALADOR MANUAL DO CHROMEDRIVER")
    print("=" * 70)
    print()

    # Detectar versão do Chrome
    print("🔍 Detectando versão do Chrome...")
    chrome_version = get_chrome_version()

    if not chrome_version:
        print("❌ Google Chrome não encontrado!")
        print()
        print("SOLUÇÃO:")
        print("1. Instale o Google Chrome: https://www.google.com/chrome/")
        print("2. Execute este script novamente")
        return 1

    print(f"✅ Chrome detectado: {chrome_version}")
    print()

    # Buscar versão do ChromeDriver
    version_info = get_chromedriver_version_for_chrome(chrome_version)

    if not version_info:
        print("❌ Não foi possível encontrar ChromeDriver compatível")
        return 1

    print(f"✅ ChromeDriver compatível: {version_info['version']}")
    print()

    # Diretório de instalação
    install_dir = Path.home() / ".chromedriver"
    install_dir.mkdir(parents=True, exist_ok=True)

    print(f"📁 Diretório de instalação: {install_dir}")
    print()

    # Baixar e instalar
    chromedriver_path = download_chromedriver(version_info, install_dir)

    if not chromedriver_path:
        return 1

    print()

    # Configurar ambiente
    configure_environment(chromedriver_path)

    print()
    print("=" * 70)
    print("✅ INSTALAÇÃO CONCLUÍDA COM SUCESSO!")
    print("=" * 70)
    print()
    print("Próximos passos:")
    print("1. Feche e abra novamente o terminal (ou IDE)")
    print("2. Execute o dashboard: streamlit run streamlit_app_premium.py")
    print("3. Clique em 'Atualizar Preços'")
    print()
    print("Se continuar com erro, tente:")
    print("  python -c \"import os; print(os.getenv('CHROMEDRIVER_PATH'))\"")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
