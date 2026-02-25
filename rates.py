from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Dict, Any, List, Tuple
import yaml

# -----------------------------
# Data models
# -----------------------------

@dataclass(frozen=True)
class CountrySchedule:
    effective_from: date
    daily_base: float  # base daily allowance in local currency


@dataclass(frozen=True)
class CountryRates:
    currency: str
    schedules: List[CountrySchedule]


@dataclass(frozen=True)
class FxSchedule:
    effective_from: date
    rate: float  # to EUR


@dataclass(frozen=True)
class FxRates:
    schedules: List[FxSchedule]


@dataclass(frozen=True)
class Money:
    amount: float
    currency: str


@dataclass(frozen=True)
class PerDiemResult:
    original: Money
    eur: Money


# -----------------------------
# Helpers
# -----------------------------

def parse_date(d: str) -> date:
    y, m, dd = d.split("-")
    return date(int(y), int(m), int(dd))


def pick_schedule_by_date(schedules, on_date: date):
    valid = [s for s in schedules if s.effective_from <= on_date]
    if not valid:
        raise ValueError(f"No schedule valid for date {on_date}")
    valid.sort(key=lambda x: x.effective_from)
    return valid[-1]


# -----------------------------
# Loaders
# -----------------------------

def load_rates(path: str | Path):
    data: Dict[str, Any] = yaml.safe_load(Path(path).read_text(encoding="utf-8"))

    # foreign time bands (percent of daily base)
    bands = data["foreign_time_bands"]
    foreign_bands = []
    for b in bands:
        foreign_bands.append(
            {
                "name": b["name"],
                "min": float(b["min_hours_inclusive"]),
                "max": float(b["max_hours_exclusive"]),
                "percent": float(b["percent_of_daily"]),
            }
        )

    # countries (ONLY those with daily_base schedules; SK with "bands" is skipped here)
    countries: Dict[str, CountryRates] = {}
    for code, c in data["countries"].items():
        scheds: List[CountrySchedule] = []
        for s in c.get("schedules", []):
            # Skip schedules without daily_base (e.g., SK uses "bands")
            if "daily_base" not in s:
                continue
            scheds.append(
                CountrySchedule(
                    effective_from=parse_date(s["effective_from"]),
                    daily_base=float(s["daily_base"]),
                )
            )
        scheds.sort(key=lambda x: x.effective_from)
        countries[code.upper()] = CountryRates(currency=str(c["currency"]), schedules=scheds)

    # FX rates to EUR
    fx: Dict[str, FxRates] = {}
    fx_block = data.get("fx_rates_to_eur", {})
    for cur, block in fx_block.items():
        scheds: List[FxSchedule] = []
        for s in block.get("schedules", []):
            scheds.append(
                FxSchedule(
                    effective_from=parse_date(s["effective_from"]),
                    rate=float(s["rate"]),
                )
            )
        scheds.sort(key=lambda x: x.effective_from)
        fx[cur.upper()] = FxRates(schedules=scheds)

    return {
        "foreign_bands": foreign_bands,
        "countries": countries,
        "fx": fx,
    }


# -----------------------------
# Pickers
# -----------------------------

def pick_country_schedule(rates, code: str, on_date: date) -> Tuple[CountrySchedule, str]:
    code = code.upper()
    if code not in rates["countries"]:
        raise ValueError(f"Unknown country code: {code}")
    cr: CountryRates = rates["countries"][code]
    sched = pick_schedule_by_date(cr.schedules, on_date)
    return sched, cr.currency


def pick_fx_rate(rates, currency: str, on_date: date) -> float:
    currency = currency.upper()
    if currency == "EUR":
        return 1.0
    if currency not in rates["fx"]:
        raise ValueError(f"No FX for currency {currency}")
    fxr: FxRates = rates["fx"][currency]
    sched = pick_schedule_by_date(fxr.schedules, on_date)
    return sched.rate


# -----------------------------
# Compute foreign per diem
# -----------------------------

def _percent_for_hours(bands, hours: float) -> float:
    for b in bands:
        if b["min"] <= hours < b["max"]:
            return b["percent"]
    # fallback
    return 0.0


def compute_foreign_per_diem_for_day(rates, country: str, day: date, hours: float) -> PerDiemResult:
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
