import pandas as pd
from rates import load_rates
from per_diem import compute_foreign_per_diem_for_day
from sk_per_diem import load_sk_rates, compute_sk_per_diem_for_day
from compute_trip_segments import split_trip_into_country_segments, iter_days, hours_in_day
from import_excel import load_trips

RATES = "rates.yml"
XLSX = "Sluzobne cesty.xlsx"
SHEET = "September 2025"  # zmeň podľa potreby
OUT = "vysledok_stravne_september_2025.xlsx"

rates = load_rates(RATES)
sk_schedules = load_sk_rates(RATES)
trips = load_trips(XLSX, SHEET)

rows = []

for idx, t in enumerate(trips, start=1):
    segments = split_trip_into_country_segments(t)
    trip_total_eur = 0.0

    for country, s, e in segments:
        for day in iter_days(s, e):
            hrs = hours_in_day(s, e, day)
            if hrs <= 0:
                continue

            if country == "SK":
                amt = compute_sk_per_diem_for_day(sk_schedules, day, hrs)
                eur = amt
                orig_amt = amt
                orig_ccy = "EUR"
            else:
                res = compute_foreign_per_diem_for_day(rates, country, day, hrs)
                orig_amt = res.original.amount
                orig_ccy = res.original.currency
                eur = res.eur.amount

            trip_total_eur += eur

            rows.append({
                "trip_id": idx,
                "purpose": t.get("purpose", ""),
                "segment_country": country,
                "day": str(day),
                "hours": round(hrs, 2),
                "orig_amount": orig_amt,
                "orig_currency": orig_ccy,
                "eur_amount": eur,
            })

    rows.append({
        "trip_id": idx,
        "purpose": t.get("purpose", ""),
        "segment_country": "TOTAL",
        "day": "",
        "hours": "",
        "orig_amount": "",
        "orig_currency": "",
        "eur_amount": round(trip_total_eur, 2),
    })

df = pd.DataFrame(rows)
df.to_excel(OUT, index=False)
print("Exported:", OUT)
