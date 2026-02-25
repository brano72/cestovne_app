# tests/test_per_diem_fx.py
from datetime import date

import pytest

from rates import load_rates
from per_diem import compute_foreign_per_diem_for_day


def test_czk_fx_and_bands(tmp_path):
    yml = tmp_path / "rates.yml"
    yml.write_text(
        """
version: 1
foreign_time_bands:
  - name: "to_6"
    min_hours_inclusive: 0
    max_hours_exclusive: 6
    percent_of_daily: 25
  - name: "6_to_12"
    min_hours_inclusive: 6
    max_hours_exclusive: 12
    percent_of_daily: 50
  - name: "over_12"
    min_hours_inclusive: 12
    max_hours_exclusive: 1000
    percent_of_daily: 100
countries:
  CZ:
    currency: CZK
    schedules:
      - effective_from: "2026-01-30"
        daily_base: 600
fx_rates_to_eur:
  EUR:
    schedules:
      - effective_from: "1900-01-01"
        rate: 1.0
  CZK:
    schedules:
      - effective_from: "2026-01-01"
        rate: 0.0413616247
""",
        encoding="utf-8",
    )

    rates = load_rates(yml)

    # 25% of 600 = 150 CZK
    r = compute_foreign_per_diem_for_day(rates, "CZ", date(2026, 2, 2), 4.0)
    assert r.original.amount == 150.00
    assert r.original.currency == "CZK"
    assert r.eur.currency == "EUR"
    assert r.eur.amount == round(150.00 * 0.0413616247, 2)

    # 100% of 600 = 600 CZK
    r = compute_foreign_per_diem_for_day(rates, "CZ", date(2026, 2, 2), 13.0)
    assert r.original.amount == 600.00
    assert r.eur.amount == round(600.00 * 0.0413616247, 2)


def test_missing_fx_raises(tmp_path):
    yml = tmp_path / "rates.yml"
    yml.write_text(
        """
version: 1
foreign_time_bands:
  - name: "over_12"
    min_hours_inclusive: 12
    max_hours_exclusive: 1000
    percent_of_daily: 100
countries:
  UK:
    currency: GBP
    schedules:
      - effective_from: "2026-01-30"
        daily_base: 37
fx_rates_to_eur:
  EUR:
    schedules:
      - effective_from: "1900-01-01"
        rate: 1.0
""",
        encoding="utf-8",
    )
    rates = load_rates(yml)
    with pytest.raises(ValueError):
        compute_foreign_per_diem_for_day(rates, "UK", date(2026, 2, 2), 13.0)

