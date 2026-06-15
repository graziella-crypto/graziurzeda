"""Camada de orquestração: busca ofertas e identifica achados/promoções."""

from __future__ import annotations

import statistics

from .config import SearchConfig
from .models import FlightOffer, SearchResult
from .providers import get_provider
from .providers.base import FlightProvider


class FlightFinder:
    """Coordena o provedor de dados e aplica a análise de preços."""

    def __init__(self, provider: FlightProvider | None = None) -> None:
        self.provider = provider or get_provider()

    def search(self, config: SearchConfig) -> SearchResult:
        try:
            offers = self.provider.search(config)
            notice = ""
        except Exception as exc:  # rede/credenciais falharam -> cai para demo
            from .providers.demo import DemoProvider

            offers = DemoProvider().search(config)
            notice = (
                "Não foi possível consultar a API real "
                f"({type(exc).__name__}). Exibindo dados de demonstração."
            )
            self.provider = DemoProvider()

        return self._analyse(offers, config, notice)

    # ------------------------------------------------------------- análise
    def _analyse(
        self, offers: list[FlightOffer], config: SearchConfig, notice: str
    ) -> SearchResult:
        result = SearchResult(provider=self.provider.name, notice=notice)
        if not offers:
            return result

        prices = [o.price for o in offers]
        median = statistics.median(prices)
        average = statistics.fmean(prices)

        for offer in offers:
            offer.discount_pct = round(
                max(0.0, (median - offer.price) / median) * 100, 1
            )
            # Promoção relâmpago: preço abaixo do limite absoluto definido.
            offer.is_flash_deal = offer.price <= config.flash_deal_threshold
            # Achado: bem abaixo da mediana das tarifas encontradas.
            offer.is_deal = offer.discount_pct >= config.deal_discount_pct * 100

        offers.sort(key=lambda o: o.price)

        result.offers = offers
        result.cheapest = offers[0]
        result.median_price = round(median, 2)
        result.average_price = round(average, 2)
        result.flash_deals_count = sum(1 for o in offers if o.is_flash_deal)
        result.deals_count = sum(1 for o in offers if o.is_deal)
        return result
