# rates.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Tuple

import yaml


@dataclass(frozen=True)
class TimeBand:
    name: str
    min_hours_inclusive: float
    max_hours_exclusive: float
    percent_of_daily: float  # 25 / 50 / 100


@dataclass(frozen=True)
class CountrySchedule:
    effective_from: date
    daily_base: float


@dataclass(frozen=True)
class CountryRates:
    currency: str
    schedules: List[CountrySchedule]


@dataclass(frozen=True)
class FxSchedule:
    effective_from: date
    rate_to_eur: float  # 1 unit of currency -> EUR


@dataclass(frozen=True)
class RatesConfig:
    foreign_time_bands: List[TimeBand]
    countries: Dict[str, CountryRates]
    fx_rates_to_eur: Dict[str, List[FxSchedule]]


def parse_date(d: str) -> date:
    y, m, dd = d.split("-")
    return date(int(y), int(m), int(dd))


def _load_fx_schedules(raw: dict) -> Dict[str, List[FxSchedule]]:
    out: Dict[str, List[FxSchedule]] = {}
    for ccy, payload in raw.items():
        scheds: List[FxSchedule] = []
        for s in payload["schedules"]:
            scheds.append(
                FxSchedule(
                    effective_from=parse_date(s["effective_from"]),
                    rate_to_eur=float(s["rate"]),
                )
            )
        scheds.sort(key=lambda x: x.effective_from)
        out[ccy.upper()] = scheds
    return out


def load_rates(path: str | Path) -> RatesConfig:
    data: Dict[str, Any] = yaml.safe_load(Path(path).read_text(encoding="utf-8"))

    bands: List[TimeBand] = [
        TimeBand(
            name=b["name"],
            min_hours_inclusive=float(b["min_hours_inclusive"]),
            max_hours_exclusive=float(b["max_hours_exclusive"]),
            percent_of_daily=float(b["percent_of_daily"]),
        )
        for b in data["foreign_time_bands"]
    ]
    bands.sort(key=lambda x: x.min_hours_inclusive)

    countries: Dict[str, CountryRates] = {}
    for code, c in data["countries"].items():
        scheds: List[CountrySchedule] = [
            CountrySchedule(
                effective_from=parse_date(s["effective_from"]),
                daily_base=float(s["daily_base"]),
            )
            for s in c["schedules"]
        ]
        scheds.sort(key=lambda x: x.effective_from)
        countries[code.upper()] = CountryRates(currency=str(c["currency"]), schedules=scheds)

    fx_raw = data.get("fx_rates_to_eur")
    if not fx_raw:
        fx_raw = {"EUR": {"schedules": [{"effective_from": "1900-01-01", "rate": 1.0}]}}
    fx = _load_fx_schedules(fx_raw)

    return RatesConfig(foreign_time_bands=bands, countries=countries, fx_rates_to_eur=fx)


def pick_country_schedule(rates: RatesConfig, country: str, on_date: date) -> Tuple[CountrySchedule, str]:
    code = country.upper()
    if code not in rates.countries:
        raise ValueError(f"Unknown country code: {code}")
    cr = rates.countries[code]
    valid = [s for s in cr.schedules if s.effective_from <= on_date]
    if not valid:
        earliest = min(cr.schedules, key=lambda x: x.effective_from).effective_from
        raise ValueError(
            f"No valid per diem for {code} on {on_date.isoformat()} (earliest effective_from is {earliest})"
        )
    return valid[-1], cr.currency


def pick_foreign_band(rates: RatesConfig, hours: float) -> TimeBand:
    for b in rates.foreign_time_bands:
        if b.min_hours_inclusive <= hours < b.max_hours_exclusive:
            return b
    raise ValueError(f"No foreign band matches hours={hours}")


def pick_fx_rate_to_eur(rates: RatesConfig, currency: str, on_date: date) -> float:
    ccy = currency.upper()
    if ccy not in rates.fx_rates_to_eur:
        raise ValueError(f"Missing FX schedule for currency: {ccy}")
    scheds = rates.fx_rates_to_eur[ccy]
    valid = [s for s in scheds if s.effective_from <= on_date]
    if not valid:
        earliest = min(scheds, key=lambda x: x.effective_from).effective_from
        raise ValueError(
            f"No valid FX rate for {ccy} on {on_date.isoformat()} (earliest effective_from is {earliest})"
        )
    return valid[-1].rate_to_eur


def convert_to_eur(rates: RatesConfig, amount: float, currency: str, on_date: date) -> float:
    rate = pick_fx_rate_to_eur(rates, currency, on_date)
    return round(amount * rate, 2)

