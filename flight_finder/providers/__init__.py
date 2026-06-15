"""Provedores de dados de passagens."""

from __future__ import annotations

from .. import config as cfg
from .base import FlightProvider
from .demo import DemoProvider
from .amadeus import AmadeusProvider


def get_provider() -> FlightProvider:
    """Escolhe o provedor conforme a configuração e as credenciais disponíveis."""

    choice = cfg.DATA_PROVIDER
    has_amadeus = bool(cfg.AMADEUS_CLIENT_ID and cfg.AMADEUS_CLIENT_SECRET)

    if choice == "amadeus" or (choice == "auto" and has_amadeus):
        return AmadeusProvider()
    return DemoProvider()


__all__ = ["FlightProvider", "DemoProvider", "AmadeusProvider", "get_provider"]
