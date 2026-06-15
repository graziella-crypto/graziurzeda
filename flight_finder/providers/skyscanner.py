"""Provedor Skyscanner via RapidAPI (API pública "Sky-Scrapper").

Traz preços reais para a tela e suporta o calendário de preços (comparativo
de datas). Requer uma chave gratuita do RapidAPI:

1. Crie conta em https://rapidapi.com
2. Assine a API "Sky-Scrapper" (apiheya) — há plano gratuito (sem cartão).
3. Exporte a chave:  export RAPIDAPI_KEY=...

Sem a chave, o app usa o modo demonstração automaticamente.

Observação: é uma API de terceiros (não oficial da Skyscanner). O código é
defensivo: se algum campo faltar ou a cota acabar, ele degrada com elegância
em vez de quebrar a busca.
"""

from __future__ import annotations

from datetime import datetime

import requests

from .. import config as cfg
from ..config import SearchConfig
from ..links import all_links, skyscanner as skyscanner_link
from ..models import FlightOffer
from .base import FlightProvider


class SkyScrapperProvider(FlightProvider):
    name = "skyscanner"

    def __init__(self) -> None:
        self._place_cache: dict[str, tuple[str, str]] = {}

    # --------------------------------------------------------------- helpers
    @property
    def _headers(self) -> dict:
        return {
            "X-RapidAPI-Key": cfg.RAPIDAPI_KEY,
            "X-RapidAPI-Host": cfg.RAPIDAPI_HOST,
        }

    def _get(self, path: str, params: dict) -> dict:
        resp = requests.get(
            f"https://{cfg.RAPIDAPI_HOST}{path}",
            headers=self._headers,
            params=params,
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()

    def _resolve_place(self, code: str) -> tuple[str, str]:
        """Resolve um IATA (ex.: 'GYN') para (skyId, entityId) do Skyscanner."""
        code = code.upper()
        if code in self._place_cache:
            return self._place_cache[code]

        data = self._get(
            "/api/v1/flights/searchAirport",
            {"query": code, "locale": "pt-BR"},
        ).get("data", [])

        chosen = None
        for item in data:
            nav = item.get("navigation", {})
            params = nav.get("relevantFlightParams", {})
            sky_id = params.get("skyId") or item.get("skyId")
            if sky_id == code:
                chosen = item
                break
        if chosen is None and data:
            chosen = data[0]
        if chosen is None:
            raise ValueError(f"Aeroporto não encontrado: {code}")

        nav = chosen.get("navigation", {})
        params = nav.get("relevantFlightParams", {})
        sky_id = params.get("skyId") or chosen.get("skyId") or code
        entity_id = params.get("entityId") or chosen.get("entityId") or ""
        self._place_cache[code] = (sky_id, entity_id)
        return sky_id, entity_id

    # --------------------------------------------------------------- search
    def search(self, config: SearchConfig) -> list[FlightOffer]:
        o_sky, o_ent = self._resolve_place(config.origin)
        d_sky, d_ent = self._resolve_place(config.destination)

        params = {
            "originSkyId": o_sky,
            "destinationSkyId": d_sky,
            "originEntityId": o_ent,
            "destinationEntityId": d_ent,
            "date": config.departure_date,
            "returnDate": config.return_date,
            "cabinClass": "economy",
            "adults": config.adults,
            "sortBy": "price_high",
            "currency": config.currency,
            "market": "BR",
            "countryCode": "BR",
            "locale": "pt-BR",
        }
        payload = self._get("/api/v2/flights/searchFlights", params)
        itineraries = (payload.get("data", {}) or {}).get("itineraries", []) or []

        links = all_links(config)
        sky = skyscanner_link(config)
        offers = [
            self._parse_itinerary(it, config, links, sky) for it in itineraries
        ]
        return [o for o in offers if o is not None]

    def _parse_itinerary(self, it, config, links, sky) -> FlightOffer | None:
        try:
            price = float(it.get("price", {}).get("raw") or 0)
            legs = it.get("legs", []) or []
            if not price or len(legs) < 1:
                return None
            out = legs[0]
            inb = legs[1] if len(legs) > 1 else {}

            airline = self._carrier(out) or self._carrier(inb) or "—"
            # Agências/sites com o preço de cada um (quando a API traz).
            agents = self._agents(it, sky)

            return FlightOffer(
                airline=airline,
                price=round(price, 2),
                currency=config.currency,
                departure_date=config.departure_date,
                return_date=config.return_date,
                origin=config.origin,
                destination=config.destination,
                outbound_departure_time=self._hm(out.get("departure")),
                outbound_arrival_time=self._hm(out.get("arrival")),
                inbound_departure_time=self._hm(inb.get("departure")),
                inbound_arrival_time=self._hm(inb.get("arrival")),
                stops=int(out.get("stopCount", 0) or 0),
                duration_outbound=self._dur(out.get("durationInMinutes")),
                duration_inbound=self._dur(inb.get("durationInMinutes")),
                links={**links, **({"skyscanner": agents[0]["url"]} if agents else {})},
                agents=agents,
                source="skyscanner",
                estimated=False,
            )
        except Exception:
            return None

    # --------------------------------------------------------- price calendar
    def price_calendar(self, config: SearchConfig) -> list[dict]:
        try:
            o_sky, _ = self._resolve_place(config.origin)
            d_sky, _ = self._resolve_place(config.destination)
            payload = self._get(
                "/api/v1/flights/getPriceCalendar",
                {
                    "originSkyId": o_sky,
                    "destinationSkyId": d_sky,
                    "fromDate": config.departure_date,
                    "currency": config.currency,
                },
            )
            days = (
                payload.get("data", {})
                .get("flights", {})
                .get("days", [])
            ) or []
            out = []
            for d in days:
                price = d.get("price")
                if price is None:
                    continue
                out.append(
                    {
                        "date": d.get("day"),
                        "price": round(float(price), 2),
                        "group": d.get("group", "medium"),
                    }
                )
            return out
        except Exception:
            return []

    # ----------------------------------------------------------------- utils
    @staticmethod
    def _carrier(leg) -> str:
        carriers = (leg or {}).get("carriers", {}).get("marketing", []) or []
        if carriers:
            return carriers[0].get("name", "")
        return ""

    def _agents(self, it, fallback_url) -> list[dict]:
        """Extrai preços por agência das pricingOptions, se presentes."""
        agents = []
        for opt in it.get("pricingOptions", []) or []:
            for ag in opt.get("agents", []) or []:
                agents.append(
                    {
                        "name": ag.get("name", "Site parceiro"),
                        "price": round(float(ag.get("price", 0) or 0), 2),
                        "url": ag.get("url") or fallback_url,
                    }
                )
        agents.sort(key=lambda a: a["price"] or 1e9)
        return agents

    @staticmethod
    def _hm(value: str | None) -> str:
        if not value:
            return ""
        try:
            return datetime.fromisoformat(value).strftime("%H:%M")
        except ValueError:
            return value[11:16] if len(value) >= 16 else ""

    @staticmethod
    def _dur(minutes) -> str:
        if not minutes:
            return ""
        minutes = int(minutes)
        return f"{minutes // 60}h{minutes % 60:02d}"
