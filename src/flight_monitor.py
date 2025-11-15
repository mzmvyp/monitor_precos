"""Monitor de voos integrado ao sistema."""
from __future__ import annotations

import logging
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

import pandas as pd
import yaml

from .flight_agent import FlightAgent, FlightOption
from .alert_manager import AlertManager

LOGGER = logging.getLogger(__name__)


class FlightMonitor:
    """Monitor de voos usando FlightAgent."""
    
    def __init__(
        self,
        config_path: Path = Path("config/flights.yaml"),
        history_path: Path = Path("data/flight_history.csv"),
        enable_alerts: bool = True,
    ):
        self.config_path = config_path
        self.history_path = history_path
        self.agent = FlightAgent()
        self.alert_manager = AlertManager() if enable_alerts else None
        self._ensure_history_file()
    
    def _ensure_history_file(self) -> None:
        """Garante que o arquivo de histórico existe."""
        if not self.history_path.parent.exists():
            self.history_path.parent.mkdir(parents=True, exist_ok=True)
        
        if not self.history_path.exists():
            df = pd.DataFrame(columns=[
                "timestamp",
                "flight_id",
                "origin",
                "destination",
                "departure_date",
                "return_date",
                "price",
                "currency",
                "airline",
                "stops",
                "duration",
                "url",
            ])
            df.to_csv(self.history_path, index=False, encoding="utf-8")
    
    def load_config(self) -> dict:
        """Carrega configuração de voos."""
        if not self.config_path.exists():
            LOGGER.warning(f"Arquivo de configuração não encontrado: {self.config_path}")
            return {"flights": []}
        
        with open(self.config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    
    def collect(self, flight_ids: Sequence[str] | None = None) -> list[FlightOption]:
        """
        Coleta preços de voos.
        
        Args:
            flight_ids: IDs específicos para coletar (None = todos)
        """
        config = self.load_config()
        flights_config = config.get("flights", [])
        
        if not flights_config:
            LOGGER.warning("Nenhuma configuração de voo encontrada")
            return []
        
        all_flights = []
        
        for flight_config in flights_config:
            flight_id = flight_config.get("id")
            
            # Filtrar por IDs se especificado
            if flight_ids and flight_id not in flight_ids:
                continue
            
            LOGGER.info(f"Buscando voos: {flight_config.get('name')}")
            
            # Calcular datas de volta automaticamente
            from datetime import datetime, timedelta
            departure_dates = flight_config.get("departure_dates", [])
            return_offset = flight_config.get("return_offset_days", 14)
            top_n = flight_config.get("top_flights_per_route", 3)
            
            # Gerar datas de volta baseadas nas datas de ida + offset
            return_dates = []
            for dep_date_str in departure_dates:
                dep_date = datetime.strptime(dep_date_str, "%Y-%m-%d")
                ret_date = dep_date + timedelta(days=return_offset)
                return_dates.append(ret_date.strftime("%Y-%m-%d"))
            
            try:
                flights = self.agent.search_best_flights(
                    origin=flight_config.get("origin"),
                    destinations=flight_config.get("destinations", []),
                    departure_dates=departure_dates,
                    return_dates=return_dates,
                    max_price=flight_config.get("max_price"),
                    top_n=top_n
                )
                
                # Adicionar ID do config
                for flight in flights:
                    flight.flight_id = flight_id
                
                all_flights.extend(flights)
                
            except Exception as e:
                LOGGER.error(f"Erro ao buscar voos {flight_id}: {e}")
        
        # Salvar no histórico
        self._append_history(all_flights)
        
        # Verificar alertas para voos
        if self.alert_manager:
            self._check_flight_alerts(all_flights)
        
        return all_flights
    
    def _append_history(self, flights: list[FlightOption]) -> None:
        """Adiciona voos ao histórico."""
        if not flights:
            return
        
        records = []
        for flight in flights:
            record = {
                "timestamp": flight.found_at.isoformat(),
                "flight_id": getattr(flight, "flight_id", "unknown"),
                "origin": flight.origin,
                "destination": flight.destination,
                "departure_date": flight.departure_date,
                "return_date": flight.return_date,
                "price": flight.price,
                "currency": flight.currency,
                "airline": flight.airline,
                "stops": flight.stops,
                "duration": flight.duration,
                "url": flight.url,
            }
            records.append(record)
        
        df = pd.DataFrame(records)
        
        # Append ao CSV
        df.to_csv(
            self.history_path,
            mode="a",
            header=not self.history_path.exists(),
            index=False,
            encoding="utf-8"
        )
        
        LOGGER.info(f"Salvos {len(records)} voos no histórico")
    
    def get_latest_flights(self) -> pd.DataFrame:
        """Retorna os voos mais recentes."""
        if not self.history_path.exists():
            return pd.DataFrame()
        
        df = pd.read_csv(self.history_path, encoding="utf-8")
        
        if df.empty:
            return df
        
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        
        # Pegar os mais recentes de cada combinação
        latest = (
            df.sort_values("timestamp")
            .groupby(["origin", "destination", "departure_date", "return_date", "airline"])
            .tail(1)
            .reset_index(drop=True)
        )
        
        return latest.sort_values("price")
    
    def _check_flight_alerts(self, flights: list[FlightOption]) -> None:
        """Verifica e envia alertas para voos com preços atrativos."""
        if not self.alert_manager or not flights:
            return

        # Carregar histórico de voos (pode estar vazio se for primeira vez)
        history = pd.DataFrame()
        if self.history_path.exists():
            history = pd.read_csv(self.history_path, encoding="utf-8")
            if not history.empty:
                history["timestamp"] = pd.to_datetime(history["timestamp"])

        # Carregar configuração para pegar preço de alerta
        config = self.load_config()

        for flight in flights:
            flight_config = next(
                (f for f in config.get("flights", []) if f.get("id") == flight.flight_id),
                None
            )

            if not flight_config:
                continue

            alert_price = flight_config.get("alert_price")  # Ex: 5000.0

            # Buscar histórico deste voo específico (mesma rota/data, qualquer airline)
            flight_history = pd.DataFrame()
            if not history.empty:
                flight_history = history[
                    (history["flight_id"] == flight.flight_id) &
                    (history["origin"] == flight.origin) &
                    (history["destination"] == flight.destination) &
                    (history["departure_date"] == flight.departure_date) &
                    (history["return_date"] == flight.return_date)
                ].sort_values("timestamp")

            product_name = f"Voo {flight.origin} → {flight.destination} ({flight.departure_date})"
            product_id = f"flight-{flight.flight_id}-{flight.origin}-{flight.destination}-{flight.departure_date}"

            # CASO 1: Voo já foi visto antes - comparar com preço anterior
            if len(flight_history) >= 2:
                previous_price = flight_history.iloc[-2]["price"]

                self.alert_manager.check_and_alert(
                    product_id=product_id,
                    product_name=product_name,
                    store=flight.airline,
                    url=flight.url,
                    current_price=flight.price,
                    previous_price=previous_price,
                    desired_price=alert_price,
                )

            # CASO 2: Primeira vez vendo este voo - alertar se preço for atrativo
            elif alert_price and flight.price <= alert_price:
                LOGGER.info(f"🎯 Voo atrativo encontrado: {product_name} - R$ {flight.price:.2f}")

                # Enviar alerta de "voo atrativo encontrado"
                self.alert_manager.check_and_alert(
                    product_id=product_id,
                    product_name=f"{product_name} [NOVA OFERTA]",
                    store=flight.airline,
                    url=flight.url,
                    current_price=flight.price,
                    previous_price=alert_price + 1.0,  # Simular "preço anterior" maior para disparar alerta
                    desired_price=alert_price,
                )
    
    def close(self):
        """Fecha o agent."""
        self.agent.close()

