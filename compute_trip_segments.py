from __future__ import annotations
from datetime import datetime, timedelta, time
from typing import Dict, List, Tuple

def _combine_date_time(base_date, t):
    # base_date is date, t is datetime.time
    return datetime.combine(base_date, t)

def resolve_border_datetimes(start_dt: datetime, end_dt: datetime, border_out_time, border_in_time):
    """
    border_out_time / border_in_time are time objects (from Excel).
    We infer dates:
      - border_out_dt is on start date or next day if earlier than start time.
      - border_in_dt is on start date, next day, ... but must be after border_out_dt.
    """
    if border_out_time is None or border_in_time is None:
        return None, None

    b_out = _combine_date_time(start_dt.date(), border_out_time)
    if b_out < start_dt:
        b_out = b_out + timedelta(days=1)

    b_in = _combine_date_time(start_dt.date(), border_in_time)
    while b_in <= b_out:
        b_in = b_in + timedelta(days=1)

    # final sanity
    if not (start_dt <= b_out <= end_dt and start_dt <= b_in <= end_dt and b_out < b_in):
        raise ValueError("Border times out of trip bounds")
    return b_out, b_in

def split_trip_into_country_segments(trip: Dict):
    """
    Returns list of (country, seg_start, seg_end)
    Assumes single foreign country in trip["country"] when != SK.
    Uses border_out/border_in when present.
    """
    start_dt = trip["start_dt"]
    end_dt = trip["end_dt"]
    country = trip["country"]

    b_out, b_in = resolve_border_datetimes(start_dt, end_dt, trip.get("border_out"), trip.get("border_in"))

    if country != "SK" and b_out and b_in:
        segs = [
            ("SK", start_dt, b_out),
            (country, b_out, b_in),
            ("SK", b_in, end_dt),
        ]
    else:
        segs = [(country, start_dt, end_dt)]

    # drop zero/negative
    segs = [(c, s, e) for (c, s, e) in segs if e > s]
    return segs

def iter_days(seg_start: datetime, seg_end: datetime):
    d = seg_start.date()
    while d <= seg_end.date():
        yield d
        d += timedelta(days=1)

def hours_in_day(seg_start: datetime, seg_end: datetime, day) -> float:
    day_start = datetime.combine(day, time(0,0,0))
    day_end = datetime.combine(day, time(23,59,59)) + timedelta(seconds=1)  # exclusive 24:00
    s = max(seg_start, day_start)
    e = min(seg_end, day_end)
    if e <= s:
        return 0.0
    return (e - s).total_seconds() / 3600.0
