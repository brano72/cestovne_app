from __future__ import annotations
from datetime import date
from typing import Any

from rates import (
    PerDiemResult,
    Money,
    pick_country_schedule,
    pick_fx_rate,
)

def _percent_for_hours(bands, hours: float) -> float:
    for b in bands:
        if b["min"] <= hours < b["max"]:
            return b["percent"]
    return 0.0

def compute_foreign_per_diem_for_day(rates: Any, country: str, day: date, hours: float) -> PerDiemResult:
    """
    Computes foreign per diem for a single day segment.
    - rates: output of load_rates()
    - country: country code (CZ, PL, DE, AT, UK, ...)
    - day: date
    - hours: number of hours in that country on that day
    """
    # pick country schedule (foreign only; SK is handled elsewhere)
    sched, currency = pick_country_schedule(rates, country, day)

    percent = _percent_for_hours(rates["foreign_bands"], hours)
    original_amount = round(sched.daily_base * (percent / 100.0), 2)

    fx_rate = pick_fx_rate(rates, currency, day)
    eur_amount = round(original_amount * fx_rate, 2)

    return PerDiemResult(
        original=Money(amount=original_amount, currency=currency),
        eur=Money(amount=eur_amount, currency="EUR"),
    )
