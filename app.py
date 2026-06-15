"""Aplicação web: busca passagens baratas e promoções relâmpago.

Trecho padrão: Goiânia (GYN) -> Maceió (MCZ), 15/08/2026 a 22/08/2026.

Executar:
    pip install -r requirements.txt
    python app.py
    # abra http://localhost:5000
"""

from __future__ import annotations

from dataclasses import replace

from flask import Flask, jsonify, render_template, request

from flight_finder.config import SearchConfig, config_from_env
from flight_finder.service import FlightFinder

app = Flask(__name__)


def _config_from_request(args) -> SearchConfig:
    """Aplica eventuais parâmetros da query por cima da configuração padrão."""
    base = config_from_env()
    overrides: dict = {}
    mapping = {
        "origin": ("origin", str),
        "destination": ("destination", str),
        "departure": ("departure_date", str),
        "return": ("return_date", str),
        "adults": ("adults", int),
        "flash": ("flash_deal_threshold", float),
    }
    for param, (field, caster) in mapping.items():
        value = args.get(param)
        if value:
            try:
                overrides[field] = caster(value)
            except (TypeError, ValueError):
                pass
    return replace(base, **overrides) if overrides else base


@app.route("/")
def index():
    return render_template("index.html", config=config_from_env())


@app.route("/api/search")
def api_search():
    config = _config_from_request(request.args)
    result = FlightFinder().search(config)
    payload = result.to_dict()
    payload["config"] = {
        "origin": config.origin,
        "destination": config.destination,
        "departure_date": config.departure_date,
        "return_date": config.return_date,
        "adults": config.adults,
        "currency": config.currency,
        "flash_deal_threshold": config.flash_deal_threshold,
    }
    return jsonify(payload)


@app.route("/healthz")
def healthz():
    return {"status": "ok"}


if __name__ == "__main__":
    import os

    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)
