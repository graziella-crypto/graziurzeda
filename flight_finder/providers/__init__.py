"""Provedores de dados de passagens."""

from __future__ import annotations

from .. import config as cfg
from .base import FlightProvider
from .demo import DemoProvider
from .amadeus import AmadeusProvider
from .skyscanner import SkyScrapperProvider


def get_provider() -> FlightProvider:
    """Escolhe o provedor conforme a configuração e as credenciais disponíveis.

    Ordem do modo "auto": Skyscanner (RapidAPI) > Amadeus > demonstração.
    """
    choice = cfg.DATA_PROVIDER
    has_skyscanner = bool(cfg.RAPIDAPI_KEY)
    has_amadeus = bool(cfg.AMADEUS_CLIENT_ID and cfg.AMADEUS_CLIENT_SECRET)

    if choice == "skyscanner" or (choice == "auto" and has_skyscanner):
        return SkyScrapperProvider()
    if choice == "amadeus" or (choice == "auto" and has_amadeus):
        return AmadeusProvider()
    return DemoProvider()


__all__ = [
    "FlightProvider",
    "DemoProvider",
    "AmadeusProvider",
    "SkyScrapperProvider",
    "get_provider",
]
