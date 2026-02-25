import pandas as pd
from datetime import datetime, time
from typing import Optional

def _to_time(v) -> Optional[time]:
    """
    Accepts:
      - datetime.time -> return as-is
      - datetime/datetime64 -> take .time()
      - string "HH:MM" / "HH:MM:SS" -> parse
      - NaN/None/empty -> None
      - float (Excel time serial) -> treat as invalid and return None (safe default)
        (If later you want to support floats, we can convert 0..1 to time.)
    """
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    if pd.isna(v):
        return None

    if isinstance(v, time):
        return v

    # pandas Timestamp / python datetime
    if isinstance(v, pd.Timestamp):
        return v.to_pydatetime().time()
    if isinstance(v, datetime):
        return v.time()

    # strings
    if isinstance(v, str):
        s = v.strip()
        if not s:
            return None
        # allow HH:MM or HH:MM:SS
        for fmt in ("%H:%M", "%H:%M:%S"):
            try:
                return datetime.strptime(s, fmt).time()
            except ValueError:
                pass
        return None

    # numbers (Excel serials) -> ignore for now (safe)
    if isinstance(v, (int, float)):
        return None

    return None


def load_trips(path: str, sheet: str):
    df = pd.read_excel(path, sheet_name=sheet)

    df.columns = [str(c).strip().lower() for c in df.columns]

    req = ["country", "datum", "odchod", "navrat", "prichod"]
    missing = [c for c in req if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}. Found: {list(df.columns)}")

    trips = []
    for _, r in df.iterrows():
        if pd.isna(r["datum"]) or pd.isna(r["odchod"]) or pd.isna(r["navrat"]) or pd.isna(r["prichod"]):
            continue

        if pd.isna(r["country"]) or str(r["country"]).strip() == "":
            continue

        start_dt = datetime.combine(pd.to_datetime(r["datum"]).date(), r["odchod"])
        end_dt = datetime.combine(pd.to_datetime(r["navrat"]).date(), r["prichod"])

        trips.append({
            "country": str(r["country"]).strip().upper(),
            "start_dt": start_dt,
            "end_dt": end_dt,
            "purpose": "" if pd.isna(r.get("dovod")) else str(r.get("dovod")),
            "border_out": _to_time(r.get("prechod hranice tam")),
            "border_in": _to_time(r.get("prechod hranice spat")),
        })

    return trips
