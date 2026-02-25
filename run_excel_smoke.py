for day in days(t["start_dt"], t["end_dt"]):
    if t["country"] == "SK":
        print(day, "SK trip - skipping foreign calc in smoke test")
        continue

    res = compute_foreign_per_diem_for_day(rates, t["country"], day, 24.0)
    print(day, res.original.amount, res.original.currency, "=>", res.eur.amount, "EUR")
    total_eur += res.eur.amount
