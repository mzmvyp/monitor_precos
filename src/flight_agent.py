"""Agent de busca de voos usando DeepSeek API."""
from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from config.deepseek_config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL

LOGGER = logging.getLogger(__name__)


@dataclass
class FlightOption:
    """Opção de voo encontrada."""
    origin: str
    destination: str
    departure_date: str
    return_date: str
    price: float
    currency: str
    airline: str
    stops: int
    duration: str
    url: str
    found_at: datetime
    flight_id: str = ""  # ID do config


class FlightAgent:
    """Agent que usa DeepSeek para buscar voos."""
    
    def __init__(self, api_key: str = DEEPSEEK_API_KEY):
        self.api_key = api_key
        self.base_url = DEEPSEEK_BASE_URL
        self.model = DEEPSEEK_MODEL
        self.driver = None
        
    def _init_driver(self):
        """Inicializa o Chrome driver."""
        if self.driver:
            return
            
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/136.0.0.0 Safari/537.36"
        )
        
        # Usar ChromeDriver manual se disponível
        import os
        from pathlib import Path
        manual_chromedriver = Path.home() / ".chromedriver" / "chromedriver-win64" / "chromedriver.exe"
        
        if manual_chromedriver.exists():
            service = Service(str(manual_chromedriver))
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
        else:
            from webdriver_manager.chrome import ChromeDriverManager
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
        LOGGER.info("FlightAgent: Chrome driver inicializado")
    
    def _call_deepseek(self, prompt: str, html_content: str = "") -> str:
        """Chama a API DeepSeek."""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            messages = [
                {
                    "role": "system",
                    "content": (
                        "Você é um assistente especializado em extrair informações de voos de páginas web. "
                        "Você recebe HTML de sites de busca de voos e extrai preços, horários, companhias aéreas, etc. "
                        "Sempre responda em formato JSON válido."
                    )
                },
                {
                    "role": "user",
                    "content": f"{prompt}\n\nHTML:\n{html_content[:10000]}"  # Limitar a 10k chars
                }
            ]
            
            data = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.1,  # Baixa temperatura para respostas mais consistentes
                "max_tokens": 2000
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )
            
            response.raise_for_status()
            result = response.json()
            
            return result["choices"][0]["message"]["content"]
            
        except Exception as e:
            LOGGER.error(f"Erro ao chamar DeepSeek API: {e}")
            return ""
    
    def search_google_flights(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: str
    ) -> list[FlightOption]:
        """
        Busca voos no Google Flights usando Selenium + DeepSeek.
        
        Args:
            origin: Código do aeroporto de origem (ex: GRU)
            destination: Código do aeroporto de destino (ex: MXP)
            departure_date: Data de ida (YYYY-MM-DD)
            return_date: Data de volta (YYYY-MM-DD)
        """
        self._init_driver()
        
        # Construir URL do Google Flights
        # Usar formato de busca direto
        from urllib.parse import quote
        
        search_query = f"{origin} to {destination} {departure_date} to {return_date}"
        url = f"https://www.google.com/travel/flights?q={quote(search_query)}&curr=BRL&hl=pt-BR"
        
        LOGGER.info(f"Buscando voos: {origin} → {destination} ({departure_date} a {return_date})")
        
        try:
            # Acessar Google Flights
            self.driver.get(url)
            LOGGER.info(f"URL: {url}")
            LOGGER.info("Aguardando 30 segundos para Google Flights carregar todos os voos...")
            
            # Aguardar carregamento inicial
            time.sleep(10)
            
            # Scroll para forçar carregamento de mais voos
            LOGGER.info("Scrolling para carregar mais opções...")
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/3);")
            time.sleep(5)
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            time.sleep(5)
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(5)
            
            # Aguardar mais voos carregarem (os mais baratos aparecem por último)
            LOGGER.info("Aguardando voos mais baratos carregarem...")
            time.sleep(10)
            
            # Voltar ao topo para pegar todos
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(2)
            
            LOGGER.info("Carregamento completo! Extraindo dados...")
            
            # Pegar HTML da página
            html = self.driver.page_source
            
            # Salvar HTML para debug
            debug_file = f"debug_flight_{destination}_{departure_date}.html"
            with open(debug_file, "w", encoding="utf-8") as f:
                f.write(html)
            LOGGER.info(f"HTML salvo em: {debug_file}")
            
            # Parse direto do HTML usando BeautifulSoup
            from bs4 import BeautifulSoup
            import re
            
            soup = BeautifulSoup(html, "html.parser")
            flights = []
            
            # Companhias aéreas para buscar
            airlines_patterns = [
                "Air France", "LATAM", "Azul", "Gol", "TAP", "Lufthansa", 
                "KLM", "Alitalia", "ITA Airways", "Swiss", "Turkish Airlines",
                "Emirates", "Qatar", "United", "American Airlines", "Delta",
                "Iberia", "British Airways", "Air Europa"
            ]
            
            # Buscar todos os elementos que contenham companhias aéreas
            page_text = soup.get_text()
            
            # Encontrar todos os blocos de voo (geralmente contêm companhia + preço + detalhes)
            for airline_pattern in airlines_patterns:
                # Buscar todas as ocorrências da companhia
                if airline_pattern.lower() not in page_text.lower():
                    continue
                
                # Encontrar elementos que contenham essa companhia
                airline_elements = soup.find_all(string=re.compile(airline_pattern, re.IGNORECASE))
                
                for airline_elem in airline_elements:
                    try:
                        # Pegar o container pai (geralmente tem todas as infos do voo)
                        container = airline_elem.parent
                        for _ in range(5):  # Subir até 5 níveis
                            if container and container.parent:
                                container = container.parent
                            else:
                                break
                        
                        if not container:
                            continue
                        
                        container_text = container.get_text()
                        
                        # Buscar preço neste container
                        price_match = re.search(r'R\$\s*([\d.,]+)', container_text)
                        if not price_match:
                            continue
                        
                        price_str = price_match.group(1)
                        price_float = float(price_str.replace(".", "").replace(",", "."))
                        
                        # Filtrar preços irreais
                        if price_float < 2000 or price_float > 50000:
                            continue
                        
                        # Buscar paradas
                        stops = -1
                        if "direto" in container_text.lower() or "nonstop" in container_text.lower():
                            stops = 0
                        elif "1 parada" in container_text.lower() or "1 stop" in container_text.lower():
                            stops = 1
                        elif "2 paradas" in container_text.lower() or "2 stops" in container_text.lower():
                            stops = 2
                        
                        # Buscar duração
                        duration = "N/A"
                        duration_match = re.search(r'(\d+)h\s*(\d+)?\s*min', container_text)
                        if duration_match:
                            hours = duration_match.group(1)
                            mins = duration_match.group(2) or "00"
                            duration = f"{hours}h {mins}m"
                        
                        # Criar voo (usar preço+companhia como chave única)
                        flight_key = f"{price_float}_{airline_pattern}"
                        
                        # Verificar se já existe
                        if not any(f.price == price_float and f.airline == airline_pattern for f in flights):
                            flight = FlightOption(
                                origin=origin,
                                destination=destination,
                                departure_date=departure_date,
                                return_date=return_date,
                                price=price_float,
                                currency="BRL",
                                airline=airline_pattern,
                                stops=stops,
                                duration=duration,
                                url=url,
                                found_at=datetime.now()
                            )
                            flights.append(flight)
                            LOGGER.debug(f"Voo encontrado: {airline_pattern} - R$ {price_float}")
                    
                    except Exception as e:
                        LOGGER.debug(f"Erro ao processar elemento: {e}")
                        continue
            
            # Ordenar por preço
            flights.sort(key=lambda f: f.price)
            
            # Limitar a 15 melhores
            flights = flights[:15]
            
            LOGGER.info(f"Encontrados {len(flights)} voos com companhias identificadas")
            
            # Se não encontrou nenhum com companhia, usar método antigo como fallback
            if not flights:
                LOGGER.warning("Nenhum voo com companhia identificada, usando fallback...")
                price_elements = soup.find_all(string=re.compile(r'R\$\s*[\d.,]+'))
                prices = []
                for elem in price_elements:
                    match = re.search(r'R\$\s*([\d.,]+)', elem)
                    if match:
                        try:
                            price_float = float(match.group(1).replace(".", "").replace(",", "."))
                            if 2000 < price_float < 50000:
                                prices.append(price_float)
                        except:
                            pass
                
                prices = sorted(list(set(prices)))[:10]
                for price in prices:
                    flights.append(FlightOption(
                        origin=origin,
                        destination=destination,
                        departure_date=departure_date,
                        return_date=return_date,
                        price=price,
                        currency="BRL",
                        airline="Várias",
                        stops=-1,
                        duration="N/A",
                        url=url,
                        found_at=datetime.now()
                    ))
            
            return flights
                
        except Exception as e:
            LOGGER.error(f"Erro ao buscar voos: {e}")
            return []
    
    def search_best_flights(
        self,
        origin: str,
        destinations: list[str],
        departure_dates: list[str],
        return_dates: list[str],
        max_price: Optional[float] = None,
        top_n: int = 3
    ) -> list[FlightOption]:
        """
        Busca melhores voos em múltiplas combinações.
        
        Args:
            origin: Aeroporto de origem (ex: GRU)
            destinations: Lista de aeroportos destino (ex: [MXP, BLQ, FLR, VCE])
            departure_dates: Lista de datas de ida possíveis
            return_dates: Lista de datas de volta correspondentes
            max_price: Preço máximo aceitável (opcional)
            top_n: Quantos voos manter por combinação (os mais baratos)
        """
        all_flights = []
        
        # Parear datas de ida com datas de volta (1:1)
        if len(departure_dates) != len(return_dates):
            LOGGER.warning(f"Datas de ida ({len(departure_dates)}) != datas de volta ({len(return_dates)})")
            # Ajustar para o menor tamanho
            min_len = min(len(departure_dates), len(return_dates))
            departure_dates = departure_dates[:min_len]
            return_dates = return_dates[:min_len]
        
        date_pairs = list(zip(departure_dates, return_dates))
        total_searches = len(destinations) * len(date_pairs)
        LOGGER.info(f"Iniciando busca em {total_searches} combinações (top {top_n} por rota)...")
        
        search_count = 0
        for dest in destinations:
            for dep_date, ret_date in date_pairs:
                search_count += 1
                LOGGER.info(f"Busca {search_count}/{total_searches}: {origin}→{dest} ({dep_date} a {ret_date})")
                
                flights = self.search_google_flights(origin, dest, dep_date, ret_date)
                
                # Filtrar por preço se especificado
                if max_price:
                    flights = [f for f in flights if f.price <= max_price]
                
                # Ordenar por preço e pegar apenas os top_n mais baratos
                flights.sort(key=lambda f: f.price)
                flights = flights[:top_n]
                
                LOGGER.info(f"  → Encontrados {len(flights)} voos (top {top_n})")
                all_flights.extend(flights)
                
                # Delay entre buscas para não sobrecarregar
                if search_count < total_searches:
                    time.sleep(5)
        
        # Ordenar resultado final por preço
        all_flights.sort(key=lambda f: f.price)
        
        LOGGER.info(f"Total de voos encontrados: {len(all_flights)}")
        return all_flights
    
    def close(self):
        """Fecha o driver."""
        if self.driver:
            self.driver.quit()
            self.driver = None


def test_flight_agent():
    """Teste do agent de voos."""
    agent = FlightAgent()
    
    try:
        # Teste simples: GRU → Milão
        flights = agent.search_google_flights(
            origin="GRU",
            destination="MXP",
            departure_date="2026-09-01",
            return_date="2026-09-14"
        )
        
        print(f"\n{'='*60}")
        print(f"Encontrados {len(flights)} voos")
        print(f"{'='*60}")
        
        for i, flight in enumerate(flights[:5], 1):  # Mostrar top 5
            print(f"\n{i}. {flight.airline}")
            print(f"   Preço: R$ {flight.price:.2f}")
            print(f"   Paradas: {flight.stops}")
            print(f"   Duração: {flight.duration}")
        
    finally:
        agent.close()


if __name__ == "__main__":
    test_flight_agent()

