from __future__ import annotations

import argparse
import logging
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Sequence

from src.price_monitor import PriceMonitor

LOGGER = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Executa a coleta contínua e opcionalmente inicia o dashboard Streamlit."
    )
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
        help="Arquivo de histórico de preços.",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=60.0,
        help="Intervalo entre coletas em minutos (padrão: 60 = 1 hora).",
    )
    parser.add_argument(
        "--product",
        action="append",
        dest="products",
        help="IDs de produtos específicos para coletar (pode repetir).",
    )
    parser.add_argument(
        "--no-dashboard",
        action="store_true",
        help="Não iniciar o dashboard Streamlit automaticamente.",
    )
    parser.add_argument(
        "--streamlit-port",
        type=int,
        default=8501,
        help="Porta para o Streamlit (quando iniciado automaticamente).",
    )
    parser.add_argument(
        "--disable-ssl-verify",
        action="store_true",
        help="Desabilitar verificação SSL (útil para proxies corporativos).",
    )
    return parser.parse_args()


def collector_loop(
    monitor: PriceMonitor,
    stop_event: threading.Event,
    interval_minutes: float,
    product_ids: Sequence[str] | None,
) -> None:
    interval_seconds = max(60, int(interval_minutes * 60))
    LOGGER.info("Coleta contínua iniciada. Intervalo: %s segundos", interval_seconds)

    while not stop_event.is_set():
        start = time.perf_counter()
        try:
            snapshots = monitor.collect(product_ids=product_ids)
            LOGGER.info("Coletados %s registros.", len(snapshots))
        except Exception:  # noqa: BLE001
            LOGGER.exception("Erro inesperado durante coleta")

        elapsed = time.perf_counter() - start
        remaining = interval_seconds - elapsed

        if remaining <= 0:
            LOGGER.warning(
                "Coleta demorou %ss (mais que o intervalo de %ss). Reiniciando imediatamente.",
                elapsed,
                interval_seconds,
            )
            continue

        if stop_event.wait(remaining):
            break


def start_streamlit(port: int) -> subprocess.Popen:
    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        "streamlit_app.py",
        "--server.port",
        str(port),
        "--server.headless",
        "true",
    ]
    LOGGER.info("Iniciando Streamlit: %s", " ".join(cmd))
    return subprocess.Popen(cmd)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    args = parse_args()

    # Configurar SSL se necessário
    if args.disable_ssl_verify:
        import os
        os.environ["SCRAPER_VERIFY_SSL"] = "false"
        LOGGER.info("Verificação SSL desabilitada")

    monitor = PriceMonitor(config_path=args.config, history_path=args.history)
    stop_event = threading.Event()

    collector_thread = threading.Thread(
        target=collector_loop,
        args=(monitor, stop_event, args.interval, args.products),
        daemon=True,
    )

    streamlit_process: subprocess.Popen | None = None

    def shutdown(signum=None, frame=None):  # noqa: D401, ANN001
        LOGGER.info("Encerrando monitor...")
        stop_event.set()
        collector_thread.join(timeout=10)
        if streamlit_process and streamlit_process.poll() is None:
            LOGGER.info("Finalizando processo do Streamlit...")
            streamlit_process.terminate()
            try:
                streamlit_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                LOGGER.warning("Streamlit não encerrou em 10s. Forçando kill.")
                streamlit_process.kill()

    signal.signal(signal.SIGINT, shutdown)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, shutdown)

    collector_thread.start()

    if not args.no_dashboard:
        streamlit_process = start_streamlit(args.streamlit_port)

    try:
        while collector_thread.is_alive():
            collector_thread.join(timeout=1)
    finally:
        shutdown()


if __name__ == "__main__":
    main()

