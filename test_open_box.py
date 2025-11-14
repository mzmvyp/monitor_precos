#!/usr/bin/env python3
"""Teste para verificar se a detecção de Open Box está funcionando."""

import logging
from src.price_monitor import PriceMonitor

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# Testar com um produto da Kabum
monitor = PriceMonitor()

print("\n🔍 Testando detecção de Open Box...")
print("=" * 60)

# Coletar apenas produtos da Kabum para teste
kabum_products = [
    "cpu-ryzen-5-9600x",
    "cpu-ryzen-7-7700",
    "cpu-ryzen-9-7900x",
]

for product_id in kabum_products:
    print(f"\n📦 Testando: {product_id}")
    snapshots = monitor.collect(product_ids=[product_id])

    for snap in snapshots:
        if snap.store == "kabum" and snap.metadata:
            has_open_box = snap.metadata.get("has_open_box", False)
            open_box_url = snap.metadata.get("open_box_url")
            open_box_price = snap.metadata.get("open_box_price")

            if has_open_box:
                print(f"   ✅ OPEN BOX DETECTADO!")
                print(f"   💰 Preço normal: R$ {snap.price:.2f}")
                if open_box_price:
                    print(f"   📦 Preço Open Box: R$ {open_box_price:.2f}")
                    economia = snap.price - open_box_price
                    print(f"   💵 Economia: R$ {economia:.2f}")
                if open_box_url:
                    print(f"   🔗 URL: {open_box_url}")
            else:
                print(f"   ℹ️  Sem Open Box disponível")
                print(f"   💰 Preço: R$ {snap.price:.2f}")

print("\n" + "=" * 60)
print("✅ Teste concluído!")
print("\nSe nenhum Open Box foi detectado, significa que os produtos")
print("monitorados não têm Open Box disponível no momento.")
