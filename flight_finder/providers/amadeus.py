"""Provedor real usando a API Amadeus Self-Service (gratuita para teste).

Cadastre-se em https://developers.amadeus.com, crie um app e exporte:

    export AMADEUS_CLIENT_ID=...
    export AMADEUS_CLIENT_SECRET=...

O ambiente padrão é o de teste (test.api.amadeus.com), que tem dados
limitados. Para produção, defina AMADEUS_HOST=https://api.amadeus.com.
"""

from __future__ import annotations

import time
from typing import Optional

import requests

from .. import config as cfg
from ..config import SearchConfig
from ..models import FlightOffer
from .base import FlightProvider


class AmadeusProvider(FlightProvider):
    name = "amadeus"

    def __init__(self) -> None:
        self._token: Optional[str] = None
        self._token_expiry: float = 0.0

    # ----------------------------------------------------------------- auth
    def _get_token(self) -> str:
        if self._token and time.time() < self._token_expiry - 30:
            return self._token

        resp = requests.post(
            f"{cfg.AMADEUS_HOST}/v1/security/oauth2/token",
            data={
                "grant_type": "client_credentials",
                "client_id": cfg.AMADEUS_CLIENT_ID,
                "client_secret": cfg.AMADEUS_CLIENT_SECRET,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
        self._token = data["access_token"]
        self._token_expiry = time.time() + data.get("expires_in", 1799)
        return self._token

    # --------------------------------------------------------------- search
    def search(self, config: SearchConfig) -> list[FlightOffer]:
        token = self._get_token()
        params = {
            "originLocationCode": config.origin,
            "destinationLocationCode": config.destination,
            "departureDate": config.departure_date,
            "returnDate": config.return_date,
            "adults": config.adults,
            "currencyCode": config.currency,
            "max": 30,
        }
        resp = requests.get(
            f"{cfg.AMADEUS_HOST}/v2/shopping/flight-offers",
            headers={"Authorization": f"Bearer {token}"},
            params=params,
            timeout=30,
        )
        resp.raise_for_status()
        payload = resp.json()
        carriers = payload.get("dictionaries", {}).get("carriers", {})
        return [
            self._parse_offer(o, config, carriers)
            for o in payload.get("data", [])
        ]

    # ---------------------------------------------------------------- parse
    def _parse_offer(self, offer: dict, config: SearchConfig, carriers: dict) -> FlightOffer:
        price = float(offer["price"]["grandTotal"])
        currency = offer["price"].get("currency", config.currency)

        itineraries = offer.get("itineraries", [])
        out = itineraries[0] if itineraries else {}
        inb = itineraries[1] if len(itineraries) > 1 else {}

        out_segments = out.get("segments", [])
        inb_segments = inb.get("segments", [])

        carrier_code = ""
        if out_segments:
            carrier_code = out_segments[0].get("carrierCode", "")
        airline = carriers.get(carrier_code, carrier_code or "—")

        return FlightOffer(
            airline=airline,
            price=round(price, 2),
            currency=currency,
            departure_date=config.departure_date,
            return_date=config.return_date,
            origin=config.origin,
            destination=config.destination,
            outbound_departure_time=self._time(out_segments, "departure", first=True),
            outbound_arrival_time=self._time(out_segments, "arrival", first=False),
            inbound_departure_time=self._time(inb_segments, "departure", first=True),
            inbound_arrival_time=self._time(inb_segments, "arrival", first=False),
            stops=max(len(out_segments) - 1, 0),
            duration_outbound=self._iso_duration(out.get("duration", "")),
            duration_inbound=self._iso_duration(inb.get("duration", "")),
            source="amadeus",
        )

    @staticmethod
    def _time(segments: list, key: str, first: bool) -> str:
        if not segments:
            return ""
        seg = segments[0] if first else segments[-1]
        at = seg.get(key, {}).get("at", "")
        # "2026-08-15T05:40:00" -> "05:40"
        return at[11:16] if len(at) >= 16 else ""

    @staticmethod
    def _iso_duration(value: str) -> str:
        # "PT5H35M" -> "5h35"
        if not value.startswith("PT"):
            return value
        body = value[2:]
        hours = minutes = ""
        if "H" in body:
            hours, body = body.split("H", 1)
        if "M" in body:
            minutes = body.replace("M", "")
        if hours and minutes:
            return f"{hours}h{int(minutes):02d}"
        if hours:
            return f"{hours}h"
        return f"{minutes}min"
