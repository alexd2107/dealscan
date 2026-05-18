from pathlib import Path

content = '''from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import math
import statistics

from scrapers import scrape_zillow, scrape_redfin
from data import get_hud_rent, get_census_growth
from scorer import score_listings

app = FastAPI(title="DealScan API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SearchFilters(BaseModel):
    state: str
    city: Optional[str] = ""
    radius_miles: Optional[int] = 0
    min_price: Optional[int] = 0
    max_price: Optional[int] = 1000000
    min_rent_yield: Optional[float] = 0.0
    min_value_score: Optional[float] = 0.0
    sort_by: Optional[str] = "value_score"

class Listing(BaseModel):
    source: str
    zpid: str = ""
    address: str
    price: int
    beds: float = 0
    baths: float = 0
    sqft: float = 0
    img: str = ""
    url: str = ""
    agent_name: str = ""
    agent_email: str = ""
    agent_phone: str = ""
    city: str = ""
    zip: str = ""
    monthly_rent_est: float = 0
    rent_yield: float = 0
    value_gap_pct: float = 0
    growth_score: float = 0
    value_score: float = 0

class SearchResponse(BaseModel):
    count: int
    listings: List[Dict[str, Any]]
    source_counts: Dict[str, int] = {}
    filters: Dict[str, Any] = {}
    timing_ms: Dict[str, float] = {}


def _dedupe_listings(listings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    unique = []
    for l in listings:
        addr = str(l.get("address", "")).lower().strip()
        if not addr:
            continue
        key = f"{addr}|{l.get('price', 0)}|{l.get('beds', 0)}|{l.get('baths', 0)}"
        if key in seen:
            continue
        seen.add(key)
        unique.append(l)
    return unique


def _sort_listings(listings: List[Dict[str, Any]], sort_by: str) -> List[Dict[str, Any]]:
    sort_by = (sort_by or "value_score").lower()
    if sort_by == "price":
        return sorted(listings, key=lambda x: x.get("price", 0))
    if sort_by == "rent_yield":
        return sorted(listings, key=lambda x: x.get("rent_yield", 0), reverse=True)
    if sort_by == "growth_score":
        return sorted(listings, key=lambda x: x.get("growth_score", 0), reverse=True)
    return sorted(listings, key=lambda x: x.get("value_score", 0), reverse=True)


def _apply_filters(listings: List[Dict[str, Any]], min_rent_yield: float, min_value_score: float) -> List[Dict[str, Any]]:
    out = []
    for l in listings:
        if l.get("rent_yield", 0) < min_rent_yield:
            continue
        if l.get("value_score", 0) < min_value_score:
            continue
        out.append(l)
    return out


def _attach_growth_scores(listings: List[Dict[str, Any]], state: str, city: str) -> List[Dict[str, Any]]:
    zips = []
    for l in listings:
        z = str(l.get("zip", "")).strip()
        if z and z not in zips:
            zips.append(z)
    growth_scores = {}
    for z in zips[:40]:
        try:
            growth_scores[z] = get_census_growth(z)
        except Exception:
            growth_scores[z] = 50.0

    city_rents = {}
    try:
        city_rents = get_hud_rent(state, city or "")
    except Exception:
        city_rents = {"rent_1br": 1200, "rent_2br": 1500, "rent_3br": 1800}

    scored = score_listings(listings, city_rents, growth_scores)
    return scored


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


@app.get("/api/version")
def version():
    return {
        "name": "DealScan API",
        "version": "1.0.0",
        "description": "Real estate investment dashboard backend"
    }


@app.get("/api/filters")
def available_filters():
    states = [
        "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA","HI","ID","IL","IN","IA","KS","KY","LA","ME",
        "MD","MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ","NM","NY","NC","ND","OH","OK","OR","PA",
        "RI","SC","SD","TN","TX","UT","VT","VA","WA","WV","WI","WY","DC"
    ]
    sort_options = ["value_score", "price", "rent_yield", "growth_score"]
    return {"states": states, "sort_options": sort_options}


@app.get("/api/listings")
def get_listings(
    state: str = Query(..., min_length=2, max_length=2),
    city: str = Query(""),
    radius_miles: int = Query(0, ge=0, le=250),
    min_price: int = Query(0, ge=0),
    max_price: int = Query(1000000, ge=0),
    min_rent_yield: float = Query(0.0, ge=0),
    min_value_score: float = Query(0.0, ge=0),
    sort_by: str = Query("value_score"),
):
    import time
    t0 = time.time()
    state = state.upper().strip()
    city = city.strip()

    if min_price > max_price:
        raise HTTPException(status_code=400, detail="min_price cannot be greater than max_price")

    zillow_start = time.time()
    zillow_listings = scrape_zillow(state, min_price, max_price, city=city, radius_miles=radius_miles or None)
    zillow_ms = round((time.time() - zillow_start) * 1000, 2)

    redfin_start = time.time()
    redfin_listings = scrape_redfin(state, min_price, max_price, city=city, radius_miles=radius_miles or None)
    redfin_ms = round((time.time() - redfin_start) * 1000, 2)

    all_listings = (zillow_listings or []) + (redfin_listings or [])
    all_listings = _dedupe_listings(all_listings)

    scored = _attach_growth_scores(all_listings, state, city)
    scored = _apply_filters(scored, min_rent_yield=min_rent_yield, min_value_score=min_value_score)
    scored = _sort_listings(scored, sort_by)

    source_counts = {"Zillow": 0, "Redfin": 0}
    for l in scored:
        src = l.get("source", "Unknown")
        source_counts[src] = source_counts.get(src, 0) + 1

    return {
        "count": len(scored),
        "listings": scored,
        "source_counts": source_counts,
        "filters": {
            "state": state,
            "city": city,
            "radius_miles": radius_miles,
            "min_price": min_price,
            "max_price": max_price,
            "min_rent_yield": min_rent_yield,
            "min_value_score": min_value_score,
            "sort_by": sort_by,
        },
        "timing_ms": {
            "zillow": zillow_ms,
            "redfin": redfin_ms,
            "total": round((time.time() - t0) * 1000, 2),
        },
    }


@app.get("/api/debug/scrape")
def debug_scrape(
    state: str = Query(..., min_length=2, max_length=2),
    city: str = Query(""),
    radius_miles: int = Query(0, ge=0, le=250),
    min_price: int = Query(0, ge=0),
    max_price: int = Query(1000000, ge=0),
):
    zillow_listings = scrape_zillow(state.upper(), min_price, max_price, city=city.strip(), radius_miles=radius_miles or None)
    redfin_listings = scrape_redfin(state.upper(), min_price, max_price, city=city.strip(), radius_miles=radius_miles or None)
    return {
        "zillow_count": len(zillow_listings or []),
        "redfin_count": len(redfin_listings or []),
        "zillow_sample": (zillow_listings or [])[:3],
        "redfin_sample": (redfin_listings or [])[:3],
    }


@app.post("/api/listings/score")
def score_only(payload: SearchFilters):
    data = payload.model_dump()
    state = data.get("state", "").upper()
    city = data.get("city", "")
    radius_miles = data.get("radius_miles", 0)
    min_price = data.get("min_price", 0)
    max_price = data.get("max_price", 1000000)
    min_rent_yield = data.get("min_rent_yield", 0.0)
    min_value_score = data.get("min_value_score", 0.0)
    sort_by = data.get("sort_by", "value_score")

    zillow = scrape_zillow(state, min_price, max_price, city=city, radius_miles=radius_miles or None)
    redfin = scrape_redfin(state, min_price, max_price, city=city, radius_miles=radius_miles or None)
    all_listings = _dedupe_listings((zillow or []) + (redfin or []))
    scored = _attach_growth_scores(all_listings, state, city)
    scored = _apply_filters(scored, min_rent_yield=min_rent_yield, min_value_score=min_value_score)
    scored = _sort_listings(scored, sort_by)
    return {"count": len(scored), "listings": scored}


@app.get("/api/insights/state/{state}")
def state_insights(state: str, city: str = ""):
    try:
        rent = get_hud_rent(state.upper(), city)
    except Exception as e:
        rent = {"rent_1br": None, "rent_2br": None, "rent_3br": None}
    return {"state": state.upper(), "city": city, "rent": rent}


@app.get("/api/insights/zip/{zip_code}")
def zip_insights(zip_code: str):
    try:
        growth = get_census_growth(zip_code)
    except Exception:
        growth = 50.0
    return {"zip": zip_code, "growth_score": growth}


@app.get("/api/ping")
def ping():
    return {"pong": True}


@app.get("/api/meta")
def meta():
    return {
        "app": "DealScan",
        "api_version": "1.0.0",
        "now": datetime.utcnow().isoformat() + "Z",
        "endpoints": [
            "/api/health",
            "/api/version",
            "/api/filters",
            "/api/listings",
            "/api/debug/scrape",
            "/api/listings/score",
            "/api/insights/state/{state}",
            "/api/insights/zip/{zip_code}",
            "/api/ping",
            "/api/meta",
        ]
    }
'''
Path('dealscan/backend/main.py').write_text(content)
print('Regenerated main.py')