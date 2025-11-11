from __future__ import annotations

import argparse
import logging
from pathlib import Path

from src.price_monitor import PriceMonitor

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Coleta preços e salva histórico.")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config/products.yaml"),
        help="Arquivo de configuração dos produtos.",
    )
    parser.add_argument(
        "--history",
        type=Path,
        default=Path("data/price_history.csv"),
        help="Destino do histórico de preços.",
    )
    parser.add_argument(
        "--product",
        action="append",
        dest="products",
        help="IDs de produtos específicos para coletar (pode repetir).",
    )
    parser.add_argument(
        "--disable-ssl-verify",
        action="store_true",
        help="Desabilitar verificação SSL (útil para proxies corporativos).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    
    # Configurar SSL se necessário
    if args.disable_ssl_verify:
        import os
        os.environ["SCRAPER_VERIFY_SSL"] = "false"
        logging.info("Verificação SSL desabilitada")
    
    monitor = PriceMonitor(config_path=args.config, history_path=args.history)
    snapshots = monitor.collect(product_ids=args.products)
    for snap in snapshots:
        logging.info(
            "%s | %s | %s -> %s",
            snap.product_name,
            snap.store,
            snap.raw_price or "-",
            "OK" if snap.error is None else f"Erro: {snap.error}",
        )


if __name__ == "__main__":
    main()

