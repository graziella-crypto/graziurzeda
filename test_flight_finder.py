"""Testes da lógica de busca e análise de ofertas.

Roda com pytest (`python -m pytest`) ou diretamente (`python test_flight_finder.py`).
"""

from __future__ import annotations

from flight_finder.config import SearchConfig
from flight_finder.providers.demo import DemoProvider
from flight_finder.service import FlightFinder


def _config(**kw) -> SearchConfig:
    return SearchConfig(**kw)


def test_demo_provider_returns_offers():
    offers = DemoProvider().search(_config())
    assert offers, "deveria retornar pelo menos uma oferta"
    for o in offers:
        assert o.origin == "GYN"
        assert o.destination == "MCZ"
        assert o.price > 0
        assert o.currency == "BRL"


def test_demo_provider_is_deterministic():
    a = DemoProvider().search(_config())
    b = DemoProvider().search(_config())
    assert [o.price for o in a] == [o.price for o in b]


def test_results_sorted_and_cheapest_first():
    result = FlightFinder(DemoProvider()).search(_config())
    prices = [o.price for o in result.offers]
    assert prices == sorted(prices)
    assert result.cheapest is not None
    assert result.cheapest.price == prices[0]


def test_flash_deal_threshold():
    cfg = _config(flash_deal_threshold=750.0)
    result = FlightFinder(DemoProvider()).search(cfg)
    for o in result.offers:
        assert o.is_flash_deal == (o.price <= 750.0)
    assert result.flash_deals_count == sum(1 for o in result.offers if o.is_flash_deal)


def test_deal_detection_relative_to_median():
    cfg = _config(deal_discount_pct=0.15)
    result = FlightFinder(DemoProvider()).search(cfg)
    median = result.median_price
    for o in result.offers:
        expected = (median - o.price) / median * 100 >= 15.0
        assert o.is_deal == expected


def test_summary_stats_present():
    result = FlightFinder(DemoProvider()).search(_config())
    assert result.median_price > 0
    assert result.average_price > 0
    assert result.provider == "demo"


def test_to_dict_serializable():
    import json

    result = FlightFinder(DemoProvider()).search(_config())
    # Não deve levantar exceção ao serializar.
    json.dumps(result.to_dict())


if __name__ == "__main__":
    import traceback

    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"PASS {t.__name__}")
        except Exception:
            failed += 1
            print(f"FAIL {t.__name__}")
            traceback.print_exc()
    print(f"\n{len(tests) - failed}/{len(tests)} testes passaram")
    raise SystemExit(1 if failed else 0)
