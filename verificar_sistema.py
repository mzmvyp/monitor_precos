"""Script para verificar se o sistema está funcionando corretamente."""
import sys
from pathlib import Path

print("=" * 80)
print("VERIFICACAO DO SISTEMA DE MONITORAMENTO DE PRECOS")
print("=" * 80)

# 1. Verificar arquivos essenciais
print("\n[1] Verificando arquivos essenciais...")
arquivos_essenciais = [
    "config/products.yaml",
    "src/price_monitor.py",
    "src/scrapers/kabum.py",
    "src/scrapers/amazon.py",
    "src/scrapers/terabyte.py",
    "src/scrapers/pichau.py",
    "streamlit_app.py",
    "run_monitor.py",
    "fetch_prices.py",
]

todos_ok = True
for arquivo in arquivos_essenciais:
    if Path(arquivo).exists():
        print(f"  [OK] {arquivo}")
    else:
        print(f"  [ERRO] {arquivo} NAO ENCONTRADO")
        todos_ok = False

# 2. Verificar dependências
print("\n[2] Verificando dependencias...")
dependencias = [
    "requests",
    "beautifulsoup4",
    "pandas",
    "streamlit",
    "yaml",
]

for dep in dependencias:
    try:
        if dep == "yaml":
            __import__("yaml")
        elif dep == "beautifulsoup4":
            __import__("bs4")
        else:
            __import__(dep)
        print(f"  [OK] {dep}")
    except ImportError:
        print(f"  [ERRO] {dep} NAO INSTALADO")
        todos_ok = False

# 3. Verificar configuração
print("\n[3] Verificando configuracao...")
try:
    from src.config_loader import load_products_config
    produtos = load_products_config(Path("config/products.yaml"))
    print(f"  [OK] {len(produtos)} produtos configurados")
    
    # Contar URLs por loja
    lojas = {}
    for produto in produtos.values():
        for url in produto.urls:
            lojas[url.store] = lojas.get(url.store, 0) + 1
    
    print(f"  [OK] URLs por loja:")
    for loja, count in lojas.items():
        print(f"       - {loja}: {count} URLs")
        
except Exception as e:
    print(f"  [ERRO] Falha ao carregar configuracao: {e}")
    todos_ok = False

# 4. Verificar scrapers
print("\n[4] Verificando scrapers...")
try:
    from src.scrapers.kabum import KabumScraper
    from src.scrapers.amazon import AmazonScraper
    from src.scrapers.terabyte import TerabyteScraper
    from src.scrapers.pichau import PichauScraper
    
    scrapers = [
        ("KaBuM", KabumScraper),
        ("Amazon", AmazonScraper),
        ("Terabyte", TerabyteScraper),
        ("Pichau", PichauScraper),
    ]
    
    for nome, scraper_class in scrapers:
        scraper = scraper_class()
        print(f"  [OK] {nome} ({scraper.store})")
        
except Exception as e:
    print(f"  [ERRO] Falha ao carregar scrapers: {e}")
    todos_ok = False

# 5. Verificar histórico
print("\n[5] Verificando historico de precos...")
history_path = Path("data/price_history.csv")
if history_path.exists():
    import pandas as pd
    df = pd.read_csv(history_path)
    print(f"  [OK] {len(df)} registros no historico")
    
    # Últimas coletas
    if not df.empty:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        ultima_coleta = df['timestamp'].max()
        print(f"  [OK] Ultima coleta: {ultima_coleta}")
else:
    print(f"  [INFO] Nenhum historico ainda (sera criado na primeira coleta)")

# Resultado final
print("\n" + "=" * 80)
if todos_ok:
    print("SISTEMA OK! Pronto para monitorar precos.")
    print("\nPara iniciar:")
    print("  Windows: iniciar_monitor.bat")
    print("  Linux/Mac: python run_monitor.py --interval 60 --disable-ssl-verify")
else:
    print("SISTEMA COM PROBLEMAS! Corrija os erros acima antes de continuar.")
    sys.exit(1)
print("=" * 80)

