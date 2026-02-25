# per_diem.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from rates import RatesConfig, convert_to_eur, pick_country_schedule, pick_foreign_band


@dataclass(frozen=True)
class Money:
    amount: float
    currency: str


@dataclass(frozen=True)
class MoneyWithEur:
    original: Money
    eur: Money


def compute_foreign_per_diem_for_day(
    rates: RatesConfig,
    country: str,
    day: date,
    hours_in_country_that_day: float,
) -> MoneyWithEur:
    sched, currency = pick_country_schedule(rates, country, day)
    band = pick_foreign_band(rates, hours_in_country_that_day)

    original_amount = round(sched.daily_base * (band.percent_of_daily / 100.0), 2)
    original = Money(amount=original_amount, currency=currency)

    eur_amount = convert_to_eur(rates, original_amount, currency, day)
    eur = Money(amount=eur_amount, currency="EUR")

    return MoneyWithEur(original=original, eur=eur)

