from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from typing import List, Dict, Any, Tuple
import yaml
from pathlib import Path

@dataclass(frozen=True)
class SkBand:
    name: str
    min_hours_inclusive: float
    max_hours_exclusive: float
    amount: float

@dataclass(frozen=True)
class SkSchedule:
    effective_from: date
    bands: List[SkBand]

def _parse_date(d: str) -> date:
    y, m, dd = d.split("-")
    return date(int(y), int(m), int(dd))

def load_sk_rates(path: str | Path) -> List[SkSchedule]:
    data: Dict[str, Any] = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    sk = data["countries"]["SK"]["schedules"]
    schedules: List[SkSchedule] = []
    for s in sk:
        bands = [
            SkBand(
                name=b["name"],
                min_hours_inclusive=float(b["min_hours_inclusive"]),
                max_hours_exclusive=float(b["max_hours_exclusive"]),
                amount=float(b["amount"]),
            )
            for b in s["bands"]
        ]
        bands.sort(key=lambda x: x.min_hours_inclusive)
        schedules.append(SkSchedule(effective_from=_parse_date(s["effective_from"]), bands=bands))
    schedules.sort(key=lambda x: x.effective_from)
    return schedules

def pick_sk_schedule(schedules: List[SkSchedule], on_date: date) -> SkSchedule:
    valid = [s for s in schedules if s.effective_from <= on_date]
    if not valid:
        raise ValueError("No SK schedule valid for date")
    return valid[-1]

def compute_sk_per_diem_for_day(sk_schedules: List[SkSchedule], day: date, hours: float) -> float:
    if hours < 5:
        return 0.0
    sched = pick_sk_schedule(sk_schedules, day)
    for b in sched.bands:
        if b.min_hours_inclusive <= hours < b.max_hours_exclusive:
            return round(b.amount, 2)
    raise ValueError("No SK band matched")
