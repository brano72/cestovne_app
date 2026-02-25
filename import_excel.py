    for _, r in df.iterrows():
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
