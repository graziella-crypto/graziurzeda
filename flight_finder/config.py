"""Configuração central da busca.

Os valores padrão já vêm preparados para a viagem solicitada:
Goiânia (GYN) -> Maceió (MCZ), ida em 15/08/2026 e volta em 22/08/2026.
Tudo pode ser sobrescrito por variáveis de ambiente ou pela interface web.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class SearchConfig:
    origin: str = "GYN"          # Goiânia - Santa Genoveva
    destination: str = "MCZ"     # Maceió - Zumbi dos Palmares
    departure_date: str = "2026-08-15"
    return_date: str = "2026-08-22"
    adults: int = 1
    currency: str = "BRL"

    # Quando uma tarifa fica abaixo deste valor (em BRL) ela é marcada
    # como "promoção relâmpago". Ajustável pelo usuário.
    flash_deal_threshold: float = 700.0

    # Uma tarifa também é considerada um "achado" quando fica este
    # percentual (ou mais) abaixo da mediana dos preços encontrados.
    deal_discount_pct: float = 0.15


def config_from_env() -> SearchConfig:
    """Monta a configuração a partir das variáveis de ambiente (com defaults)."""

    def _get(name: str, default: str) -> str:
        return os.environ.get(name, default)

    return SearchConfig(
        origin=_get("FF_ORIGIN", SearchConfig.origin),
        destination=_get("FF_DESTINATION", SearchConfig.destination),
        departure_date=_get("FF_DEPARTURE", SearchConfig.departure_date),
        return_date=_get("FF_RETURN", SearchConfig.return_date),
        adults=int(_get("FF_ADULTS", str(SearchConfig.adults))),
        currency=_get("FF_CURRENCY", SearchConfig.currency),
        flash_deal_threshold=float(
            _get("FF_FLASH_THRESHOLD", str(SearchConfig.flash_deal_threshold))
        ),
        deal_discount_pct=float(
            _get("FF_DEAL_DISCOUNT", str(SearchConfig.deal_discount_pct))
        ),
    )


# Provedor de dados: "auto" usa a API real (Amadeus) se houver credenciais,
# caso contrário cai no modo demonstração. Pode forçar "amadeus" ou "demo".
DATA_PROVIDER = os.environ.get("FF_PROVIDER", "auto").lower()

AMADEUS_CLIENT_ID = os.environ.get("AMADEUS_CLIENT_ID", "")
AMADEUS_CLIENT_SECRET = os.environ.get("AMADEUS_CLIENT_SECRET", "")
AMADEUS_HOST = os.environ.get("AMADEUS_HOST", "https://test.api.amadeus.com")
