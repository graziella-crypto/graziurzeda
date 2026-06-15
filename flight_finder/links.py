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


def _yymm(date_iso: str) -> str:
    """'2026-08-15' -> '2608' (ano-mês usado no calendário do Skyscanner)."""
    y, m, _ = date_iso.split("-")
    return f"{y[2:]}{m}"


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


def decolar(config: SearchConfig) -> str:
    # Ex.: https://www.decolar.com/shop/flights/results/roundtrip/GYN/MCZ/2026-08-15/2026-08-22/1/0/0
    return (
        "https://www.decolar.com/shop/flights/results/roundtrip/"
        f"{config.origin}/{config.destination}/"
        f"{config.departure_date}/{config.return_date}/"
        f"{config.adults}/0/0"
    )


def latam(config: SearchConfig) -> str:
    # Busca direta no site da LATAM, com trecho e datas preenchidos.
    return (
        "https://www.latamairlines.com/br/pt/oferta-voos?"
        f"origin={config.origin}&destination={config.destination}"
        f"&outbound={config.departure_date}T12%3A00%3A00.000Z"
        f"&inbound={config.return_date}T12%3A00%3A00.000Z"
        f"&adt={config.adults}&chd=0&inf=0&trip=RT&cabin=Economy"
        "&redemption=false&sort=RECOMMENDED"
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


def price_calendar(config: SearchConfig) -> str:
    """Calendário de preços: mostra os dias mais baratos do mês no Skyscanner.

    Útil para checar se adiantar/atrasar a viagem em 1-2 dias sai mais barato.
    """
    ym = _yymm(config.departure_date)
    rym = _yymm(config.return_date)
    return (
        "https://www.skyscanner.com.br/transporte/passagens-aereas/"
        f"{config.origin.lower()}/{config.destination.lower()}/"
        f"?oym={ym}&iym={rym}&adults={config.adults}&rtn=1"
        "&cabinclass=economy&preferdirects=false"
    )


def all_links(config: SearchConfig) -> dict[str, str]:
    """Dicionário {parceiro: url} com todos os links de busca preenchidos."""
    return {
        "kayak": kayak(config),
        "skyscanner": skyscanner(config),
        "decolar": decolar(config),
        "latam": latam(config),
        "google": google_flights(config),
    }
