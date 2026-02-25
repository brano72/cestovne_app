import pandas as pd
from datetime import datetime

def load_trips(path: str, sheet: str):
    df = pd.read_excel(path, sheet_name=sheet)

    df.columns = [str(c).strip().lower() for c in df.columns]

    req = ["country", "datum", "odchod", "navrat", "prichod", "dovod"]
    missing = [c for c in req if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}. Found: {list(df.columns)}")

    trips = []
    for _, r in df.iterrows():
        if pd.isna(r["datum"]) or pd.isna(r["odchod"]) or pd.isna(r["navrat"]) or pd.isna(r["prichod"]):
            continue

        start_dt = datetime.combine(pd.to_datetime(r["datum"]).date(), r["odchod"])
        end_dt = datetime.combine(pd.to_datetime(r["navrat"]).date(), r["prichod"])

        trips.append({
            "country": str(r["country"]).strip().upper(),
            "start_dt": start_dt,
            "end_dt": end_dt,
            "purpose": "" if pd.isna(r.get("dovod")) else str(r.get("dovod")),
        })
    return trips
