from datetime import timedelta
from rates import load_rates
from per_diem import compute_foreign_per_diem_for_day
from sk_per_diem import load_sk_rates, compute_sk_per_diem_for_day
from compute_trip_segments import split_trip_into_country_segments, iter_days, hours_in_day
from import_excel import load_trips

RATES = "rates.yml"
XLSX = "Sluzobne cesty.xlsx"
SHEET = "September 2025"

rates = load_rates(RATES)
sk_schedules = load_sk_rates(RATES)
trips = load_trips(XLSX, SHEET)

# vyber prvý zahraničný trip, aby si hneď videl výpočet
t = next(x for x in trips if x["country"] != "SK")

print("Trip:", t["country"], t["start_dt"], "->", t["end_dt"], "|", t["purpose"])

segments = split_trip_into_country_segments(t)

total_eur = 0.0
for country, s, e in segments:
    for day in iter_days(s, e):
        hrs = hours_in_day(s, e, day)
        if hrs <= 0:
            continue
        if country == "SK":
            amt = compute_sk_per_diem_for_day(sk_schedules, day, hrs)
            print(day, "SK", round(hrs,2), "h =>", amt, "EUR")
            total_eur += amt
        else:
            res = compute_foreign_per_diem_for_day(rates, country, day, hrs)
            print(day, country, round(hrs,2), "h =>", res.original.amount, res.original.currency, "=>", res.eur.amount, "EUR")
            total_eur += res.eur.amount

print("TOTAL EUR:", round(total_eur, 2))
