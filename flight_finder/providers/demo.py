"""Provedor de demonstração.

Gera ofertas realistas para o trecho Goiânia (GYN) -> Maceió (MCZ) sem
depender de credenciais ou rede. Os preços usam uma semente baseada nas
datas da busca, de modo que o resultado é estável entre execuções, mas
ainda assim apresenta variação e algumas promoções relâmpago.

Útil para demonstrar a aplicação imediatamente. Para preços reais,
configure as credenciais do Amadeus (veja o README).
"""

from __future__ import annotations

import hashlib
import random
from datetime import datetime, timedelta

from ..config import SearchConfig
from ..links import all_links, skyscanner as skyscanner_link
from ..models import FlightOffer
from .base import FlightProvider

# Sites/agências fictícios usados para simular o comparativo por buscador.
_AGENT_NAMES = ["MaxMilhas", "Decolar", "123Milhas", "Kayak", "Skyscanner", "GOL", "LATAM"]

# Companhias que operam o mercado doméstico brasileiro e faixas de preço
# típicas (ida e volta, em BRL) para um trecho de média distância como GYN-MCZ.
_AIRLINES = [
    ("GOL", 620, 1180),
    ("LATAM", 690, 1320),
    ("Azul", 650, 1260),
    ("Voepass", 740, 1400),
]

# A maioria dos voos GYN-MCZ tem ao menos uma conexão (BSB, GRU, CGH, REC...).
_CONNECTIONS = ["BSB", "GRU", "VCP", "REC", "CGH"]

_OUTBOUND_TIMES = [
    ("05:40", "11:05", "5h25"),
    ("08:15", "13:50", "5h35"),
    ("10:30", "17:20", "6h50"),
    ("13:05", "18:10", "5h05"),
    ("16:40", "23:15", "6h35"),
    ("19:20", "06:05", "10h45"),
]

_INBOUND_TIMES = [
    ("06:10", "11:40", "5h30"),
    ("09:25", "15:00", "5h35"),
    ("12:00", "18:35", "6h35"),
    ("14:45", "20:10", "5h25"),
    ("18:30", "23:55", "5h25"),
    ("21:15", "07:50", "10h35"),
]


class DemoProvider(FlightProvider):
    name = "demo"

    def search(self, config: SearchConfig) -> list[FlightOffer]:
        seed_src = f"{config.origin}{config.destination}{config.departure_date}{config.return_date}"
        seed = int(hashlib.sha256(seed_src.encode()).hexdigest(), 16) % (10**8)
        rng = random.Random(seed)
        links = all_links(config)

        offers: list[FlightOffer] = []
        # Entre 9 e 14 ofertas, variando companhia, horário e número de paradas.
        n_offers = rng.randint(9, 14)
        for _ in range(n_offers):
            airline, low, high = rng.choice(_AIRLINES)
            stops = rng.choices([0, 1, 2], weights=[15, 60, 25])[0]

            base = rng.uniform(low, high)
            # Voos diretos custam mais; mais paradas tendem a baratear.
            if stops == 0:
                base *= 1.25
            elif stops == 2:
                base *= 0.85

            # Alguns assentos recebem uma "promoção relâmpago" agressiva.
            if rng.random() < 0.18:
                base *= rng.uniform(0.55, 0.72)

            price = round(base, 2)

            out_dep, out_arr, out_dur = rng.choice(_OUTBOUND_TIMES)
            in_dep, in_arr, in_dur = rng.choice(_INBOUND_TIMES)

            offers.append(
                FlightOffer(
                    airline=airline,
                    price=price,
                    currency=config.currency,
                    departure_date=config.departure_date,
                    return_date=config.return_date,
                    origin=config.origin,
                    destination=config.destination,
                    outbound_departure_time=out_dep,
                    outbound_arrival_time=out_arr,
                    inbound_departure_time=in_dep,
                    inbound_arrival_time=in_arr,
                    stops=stops,
                    duration_outbound=out_dur,
                    duration_inbound=in_dur,
                    links=links,
                    agents=self._fake_agents(rng, price, links),
                    source="demo",
                    estimated=True,
                )
            )

        return offers

    @staticmethod
    def _fake_agents(rng, price, links) -> list[dict]:
        """Simula o preço do mesmo voo em alguns sites de busca."""
        names = rng.sample(_AGENT_NAMES, k=rng.randint(3, 4))
        agents = []
        for i, name in enumerate(names):
            # O primeiro é o mais barato; os demais um pouco acima.
            factor = 1.0 if i == 0 else rng.uniform(1.02, 1.18)
            agents.append(
                {
                    "name": name,
                    "price": round(price * factor, 2),
                    "url": links.get("skyscanner", ""),
                }
            )
        agents.sort(key=lambda a: a["price"])
        return agents

    def price_calendar(self, config: SearchConfig) -> list[dict]:
        """Comparativo de datas simulado: 14 dias a partir de 3 dias antes."""
        try:
            start = datetime.fromisoformat(config.departure_date) - timedelta(days=3)
        except ValueError:
            return []
        seed = int(
            hashlib.sha256((config.origin + config.destination + "cal").encode())
            .hexdigest(),
            16,
        ) % (10**8)
        rng = random.Random(seed)
        days = []
        for i in range(14):
            day = start + timedelta(days=i)
            price = round(rng.uniform(420, 1150), 2)
            days.append({"date": day.strftime("%Y-%m-%d"), "price": price, "group": "medium"})
        return days
