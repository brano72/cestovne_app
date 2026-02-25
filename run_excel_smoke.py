from rates import load_rates
from per_diem import compute_foreign_per_diem_for_day
from datetime import timedelta
from import_excel import load_trips

RATES = "rates.yml"
XLSX = "Sluzobne cesty.xlsx"
SHEET = "September 2025"  # uprav ak treba

def days(start, end):
    d = start.date()
    while d <= end.date():
        yield d
        d = d + timedelta(days=1)

rates = load_rates(RATES)
trips = load_trips(XLSX, SHEET)

t = trips[0]
print("Trip:", t["country"], t["start_dt"], "->", t["end_dt"], "|", t["purpose"])

total_eur = 0.0
for day in days(t["start_dt"], t["end_dt"]):
    if t["country"] == "SK":
        print(day, "SK trip - skipping foreign calc in smoke test")
        continue

    res = compute_foreign_per_diem_for_day(rates, t["country"], day, 24.0)
    print(day, res.original.amount, res.original.currency, "=>", res.eur.amount, "EUR")
    total_eur += res.eur.amount

print("TOTAL EUR:", round(total_eur, 2))
