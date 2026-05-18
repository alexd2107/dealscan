from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from scrapers import scrape_zillow, scrape_redfin
from data import get_hud_rent, get_census_growth
from scorer import score_listings
from typing import Optional

app = FastAPI(title="DealScan API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/listings")
async def get_listings(
    city: str = Query(...),
    state: str = Query("NY"),
    min_price: int = Query(0),
    max_price: int = Query(1000000),
    min_rent_yield: float = Query(0.0),
    min_value_score: float = Query(0.0),
    sort_by: str = Query("value_score"),  # value_score | price | rent_yield
):
    city_slug = city.lower().replace(" ", "-")

    zillow_listings = scrape_zillow(city_slug, min_price, max_price)
    redfin_listings = scrape_redfin(city, state, min_price, max_price)
    all_listings = zillow_listings + redfin_listings

    # Deduplicate by address
    seen = set()
    unique = []
    for l in all_listings:
        addr = l.get("address","").lower().strip()
        if addr and addr not in seen:
            seen.add(addr)
            unique.append(l)

    # Fetch rent + growth data
    city_rents = get_hud_rent(state, city)
    zip_codes = list({l.get("zip","") for l in unique if l.get("zip")})
    growth_scores = {z: get_census_growth(z) for z in zip_codes[:20]}

    scored = score_listings(unique, city_rents, growth_scores)

    # Filter
    filtered = [
        l for l in scored
        if l["rent_yield"] >= min_rent_yield
        and l["value_score"] >= min_value_score
    ]

    # Sort
    reverse = True
    if sort_by == "price":
        key_fn = lambda x: x["price"]
        reverse = False
    elif sort_by == "rent_yield":
        key_fn = lambda x: x["rent_yield"]
    else:
        key_fn = lambda x: x["value_score"]

    filtered.sort(key=key_fn, reverse=reverse)
    return {"count": len(filtered), "listings": filtered}


@app.get("/api/health")
def health():
    return {"status": "ok"}
