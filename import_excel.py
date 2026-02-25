import pandas as pd
from datetime import datetime

def load_trips(path: str, sheet: str):
    df = pd.read_excel(path, sheet_name=sheet)

    # normalizuj názvy stĺpcov
    df.columns = [str(c).strip().lower() for c in df.columns]

    req = ["country", "datum", "odchod", "navrat", "prichod"]
    missing = [c for c in req if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}. Found: {list(df.columns)}")

    trips = []
    for _, r in df.iterrows():
        # preskoč nekompletné riadky
        if pd.isna(r["datum"]) or pd.isna(r["odchod"]) or pd.isna(r["navrat"]) or pd.isna(r["prichod"]):
            continue

        # preskoč riadky bez krajiny
        if pd.isna(r["country"]) or str(r["country"]).strip() == "":
            continue

        start_dt = datetime.combine(pd.to_datetime(r["datum"]).date(), r["odchod"])
        end_dt = datetime.combine(pd.to_datetime(r["navrat"]).date(), r["prichod"])

        trips.append({
            "country": str(r["country"]).strip().upper(),
            "start_dt": start_dt,
            "end_dt": end_dt,
            "purpose": "" if pd.isna(r.get("dovod")) else str(r.get("dovod")),
            "border_out": r.get("prechod hranice tam"),
            "border_in": r.get("prechod hranice spat"),
        })

    return trips
