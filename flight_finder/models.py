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
    deep_link: str = ""
    source: str = "demo"

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
        }
