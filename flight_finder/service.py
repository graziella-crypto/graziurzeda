"""Camada de orquestração: busca ofertas e identifica achados/promoções."""

from __future__ import annotations

import statistics

from .config import SearchConfig
from .links import all_links
from .links import price_calendar as price_calendar_link
from .models import FlightOffer, SearchResult
from .providers import get_provider
from .providers.base import FlightProvider


class FlightFinder:
    """Coordena o provedor de dados e aplica a análise de preços."""

    def __init__(self, provider: FlightProvider | None = None) -> None:
        self.provider = provider or get_provider()

    def search(self, config: SearchConfig) -> SearchResult:
        notice = ""
        try:
            offers = self.provider.search(config)
            # API respondeu, mas sem voos (comum no ambiente de TESTE da Amadeus).
            if not offers and self.provider.name == "amadeus":
                notice = (
                    "A API Amadeus respondeu, mas não retornou voos para este "
                    "trecho/datas. No ambiente de TESTE a cobertura é limitada "
                    "(rotas domésticas como GYN-MCZ podem não existir). Use os "
                    "links de busca real abaixo ou configure chaves de produção."
                )
            calendar = self._safe_calendar(self.provider, config)
        except Exception as exc:  # rede/credenciais falharam -> cai para demo
            from .providers.demo import DemoProvider

            notice = self._explain_error(exc)
            self.provider = DemoProvider()
            offers = self.provider.search(config)
            calendar = self._safe_calendar(self.provider, config)

        return self._analyse(offers, config, notice, calendar)

    @staticmethod
    def _safe_calendar(provider: FlightProvider, config: SearchConfig) -> list[dict]:
        """Busca o calendário sem deixar uma falha derrubar a busca principal."""
        try:
            return provider.price_calendar(config)
        except Exception:
            return []

    @staticmethod
    def _explain_error(exc: Exception) -> str:
        """Traduz a falha da API em uma mensagem útil para o usuário."""
        status = getattr(getattr(exc, "response", None), "status_code", None)
        if status == 401:
            return (
                "Chaves da Amadeus inválidas ou ausentes (erro 401). Confira "
                "AMADEUS_CLIENT_ID/SECRET e se o AMADEUS_HOST corresponde ao "
                "ambiente das chaves (teste x produção). Exibindo demonstração."
            )
        if status == 429:
            return (
                "Limite de requisições da Amadeus atingido (erro 429). "
                "Tente novamente em instantes. Exibindo demonstração."
            )
        if status:
            return (
                f"A API Amadeus retornou erro {status}. "
                "Exibindo dados de demonstração."
            )
        return (
            "Não foi possível conectar à API Amadeus "
            f"({type(exc).__name__}). Exibindo dados de demonstração."
        )

    # ------------------------------------------------------------- análise
    def _analyse(
        self,
        offers: list[FlightOffer],
        config: SearchConfig,
        notice: str,
        calendar: list[dict] | None = None,
    ) -> SearchResult:
        result = SearchResult(
            provider=self.provider.name,
            notice=notice,
            search_links=all_links(config),
            calendar_link=price_calendar_link(config),
            calendar=self._mark_cheapest_days(calendar or []),
        )
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

    @staticmethod
    def _mark_cheapest_days(calendar: list[dict]) -> list[dict]:
        """Classifica os dias em barato/médio/caro e marca o mais barato."""
        if not calendar:
            return calendar
        prices = [d["price"] for d in calendar if d.get("price")]
        if not prices:
            return calendar
        cheapest = min(prices)
        lo = statistics.quantiles(prices, n=3)[0] if len(prices) >= 3 else cheapest
        hi = statistics.quantiles(prices, n=3)[-1] if len(prices) >= 3 else max(prices)
        for d in calendar:
            p = d.get("price")
            d["is_cheapest"] = p == cheapest
            if p is None:
                d["group"] = "medium"
            elif p <= lo:
                d["group"] = "low"
            elif p >= hi:
                d["group"] = "high"
            else:
                d["group"] = "medium"
        return calendar
