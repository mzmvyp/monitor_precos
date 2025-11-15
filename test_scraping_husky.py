#!/usr/bin/env python3
"""Teste específico para validar scraping da Fonte Husky."""

import logging
from src.scrapers.kabum import KabumScraper

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# URL da Fonte Husky Sledger 850W
url = "https://www.kabum.com.br/produto/603225/fonte-husky-sledger-850w-80-plus-gold-cybenetics-gold-pfc-ativo-full-modular-bivolt-hfn850pt"

print("\n" + "="*70)
print("🔍 TESTE DE SCRAPING - Fonte Husky Sledger 850W")
print("="*70)
print(f"\n📍 URL: {url}\n")

scraper = KabumScraper()

try:
    print("⏳ Acessando página da Kabum...")
    snapshot = scraper.fetch(url)

    print("\n✅ RESULTADO DO SCRAPING:")
    print(f"   💰 Preço encontrado: R$ {snapshot.price:.2f}")
    print(f"   📝 Preço raw: {snapshot.raw_price}")
    print(f"   📦 Em estoque: {snapshot.in_stock}")
    print(f"   ⚠️  Erro: {snapshot.error}")

    if snapshot.metadata:
        print(f"\n📊 METADATA:")
        for key, value in snapshot.metadata.items():
            print(f"   {key}: {value}")

    print(f"\n🎯 Preço esperado no site: R$ 530,90")
    print(f"🎯 Preço encontrado pelo scraper: R$ {snapshot.price:.2f}")

    if snapshot.price:
        diff = abs(snapshot.price - 530.90)
        if diff < 0.01:
            print("✅ PREÇO CORRETO!")
        else:
            print(f"❌ PREÇO INCORRETO! Diferença: R$ {diff:.2f}")

except Exception as e:
    print(f"\n❌ ERRO AO FAZER SCRAPING:")
    print(f"   {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*70)
