def score_listings(listings: list, city_rents: dict, growth_scores: dict) -> list:
    prices_per_sqft = [
        l["price"] / l["sqft"]
        for l in listings
        if l.get("sqft") and l["sqft"] > 0 and l.get("price")
    ]
    avg_ppsf = sum(prices_per_sqft) / len(prices_per_sqft) if prices_per_sqft else 200

    scored = []
    for l in listings:
        price = l.get("price", 0) or 0
        sqft = l.get("sqft", 0) or 1
        beds = int(l.get("beds", 0) or 0)
        zip_code = l.get("zip", "")

        ppsf = price / sqft
        value_gap = max(0, (avg_ppsf - ppsf) / avg_ppsf * 100) if avg_ppsf else 0

        # Pick rent by bedroom count
        rents = city_rents
        if beds <= 1:
            monthly_rent = rents.get("rent_1br", 1200)
        elif beds == 2:
            monthly_rent = rents.get("rent_2br", 1500)
        else:
            monthly_rent = rents.get("rent_3br", 1800)

        rent_yield = (monthly_rent * 12 / price * 100) if price else 0
        growth_score = growth_scores.get(zip_code, 50.0)

        value_score = round(
            (value_gap * 0.45) + (rent_yield * 0.35) + (growth_score * 0.20), 1
        )

        scored.append({
            **l,
            "monthly_rent_est": monthly_rent,
            "rent_yield": round(rent_yield, 2),
            "value_gap_pct": round(value_gap, 2),
            "growth_score": growth_score,
            "value_score": min(100, round(value_score, 1)),
        })
    return scored
