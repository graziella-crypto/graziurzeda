"""Modelos de dados usados em toda a aplicação."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Optional

@dataclass
class FlightOffer:
    """Uma oferta de passagem (ida e volta) encontrada por um provedor."""

    airline: str
    price: float
    currency: str
    departure_date: str
    return_date: str
    origin: str
    destination: str
    outbound_departure_time: str = ""
    outbound_arrival_time: str = ""
    inbound_departure_time: str = ""
    inbound_arrival_time: str = ""
    stops: int = 0
    duration_outbound: str = ""
    duration_inbound: str = ""
    # Links de busca REAL já preenchidos (kayak/skyscanner/google).
    links: dict = field(default_factory=dict)
    # Preços por site/agência de venda: [{"name","price","url"}], do mais barato.
    agents: list = field(default_factory=list)
    source: str = "demo"
    # True quando o preço é estimado (modo demonstração), não uma tarifa real.
    estimated: bool = False

    # Preenchidos pela camada de análise (service.py)
    is_flash_deal: bool = False
    is_deal: bool = False
    discount_pct: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class SearchResult:
    """Resultado consolidado de uma busca, já analisado."""

    offers: list[FlightOffer] = field(default_factory=list)
    cheapest: Optional[FlightOffer] = None
    median_price: float = 0.0
    average_price: float = 0.0
    flash_deals_count: int = 0
    deals_count: int = 0
    provider: str = "demo"
    notice: str = ""
    # Links de busca real (GYN→MCZ + datas) para conferir tarifas verdadeiras.
    search_links: dict = field(default_factory=dict)
    # Calendário de preços do mês (dias mais baratos para a viagem).
    calendar_link: str = ""
    # Comparativo de datas: [{"date","price","group","is_cheapest"}].
    calendar: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "offers": [o.to_dict() for o in self.offers],
            "cheapest": self.cheapest.to_dict() if self.cheapest else None,
            "median_price": self.median_price,
            "average_price": self.average_price,
            "flash_deals_count": self.flash_deals_count,
            "deals_count": self.deals_count,
            "provider": self.provider,
            "notice": self.notice,
            "search_links": self.search_links,
            "calendar_link": self.calendar_link,
            "calendar": self.calendar,
        }
