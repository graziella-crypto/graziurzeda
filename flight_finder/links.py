"""Monta links de busca REAIS, já preenchidos com origem, destino e datas.

Diferente de uma busca genérica, estes links abrem direto a página de
resultados do parceiro com o trecho e as datas selecionados — sem o usuário
precisar redigitar nada.
"""

from __future__ import annotations

from .config import SearchConfig


def _yymmdd(date_iso: str) -> str:
    """'2026-08-15' -> '260815' (formato usado pelo Skyscanner)."""
    y, m, d = date_iso.split("-")
    return f"{y[2:]}{m}{d}"


def kayak(config: SearchConfig) -> str:
    # Ex.: https://www.kayak.com.br/flights/GYN-MCZ/2026-08-15/2026-08-22?sort=price_a
    return (
        f"https://www.kayak.com.br/flights/"
        f"{config.origin}-{config.destination}/"
        f"{config.departure_date}/{config.return_date}"
        f"?sort=price_a&fs=stops=~2"
    )


def skyscanner(config: SearchConfig) -> str:
    # Ex.: https://www.skyscanner.com.br/transporte/passagens-aereas/gyn/mcz/260815/260822/
    return (
        "https://www.skyscanner.com.br/transporte/passagens-aereas/"
        f"{config.origin.lower()}/{config.destination.lower()}/"
        f"{_yymmdd(config.departure_date)}/{_yymmdd(config.return_date)}/"
        f"?adults={config.adults}&cabinclass=economy&rtn=1"
    )


def google_flights(config: SearchConfig) -> str:
    # Formato com fragmento que preenche trecho e datas na busca do Google Voos.
    return (
        "https://www.google.com/travel/flights?hl=pt-BR&curr="
        f"{config.currency}#flt="
        f"{config.origin}.{config.destination}.{config.departure_date}*"
        f"{config.destination}.{config.origin}.{config.return_date};"
        f"c:{config.currency};e:1;sd:1;t:f"
    )


def all_links(config: SearchConfig) -> dict[str, str]:
    """Dicionário {parceiro: url} com todos os links de busca preenchidos."""
    return {
        "kayak": kayak(config),
        "skyscanner": skyscanner(config),
        "google": google_flights(config),
    }
