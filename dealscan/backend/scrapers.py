import os
import json
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "application/json,text/plain,*/*",
}

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY", "")
RAPIDAPI_HOST = "zillow-com-live-data-scraper-api.p.rapidapi.com"

def _to_int(v):
    try:
        if v is None:
            return 0
        if isinstance(v, (int, float)):
            return int(v)
        s = str(v).replace("$", "").replace(",", "").strip()
        return int(float(s)) if s else 0
    except:
        return 0

def _pick(item, keys, default=""):
    for k in keys:
        if isinstance(item, dict) and item.get(k) not in [None, ""]:
            return item.get(k)
    return default

def scrape_zillow(state: str, min_price: int, max_price: int, city: str = "", radius_miles: int | None = None):
    if not RAPIDAPI_KEY:
        return []

    mlsid = city.strip().replace(" ", "")
    if not mlsid:
        return []

    url = "https://zillow-com-live-data-scraper-api.p.rapidapi.com/bymlsid"
    params = {"mlsid": mlsid, "page": 1}
    headers = {
        **HEADERS,
        "x-rapidapi-host": RAPIDAPI_HOST,
        "x-rapidapi-key": RAPIDAPI_KEY,
    }

    try:
        r = requests.get(url, headers=headers, params=params, timeout=30)
        if r.status_code != 200:
            return []

        data = r.json()

        rows = []
        if isinstance(data, dict):
            for key in ["results", "data", "listings", "homes", "properties"]:
                val = data.get(key)
                if isinstance(val, list):
                    rows = val
                    break
            if not rows:
                for v in data.values():
                    if isinstance(v, list):
                        rows = v
                        break
        elif isinstance(data, list):
            rows = data

        listings = []
        for item in rows:
            if not isinstance(item, dict):
                continue

            price = _to_int(_pick(item, ["price", "unformattedPrice", "listPrice", "amount"]))
            if not price or not (min_price <= price <= max_price):
                continue

            address = _pick(item, ["address", "streetAddress", "displayAddress", "formattedAddress"], "N/A")
            beds = item.get("beds", item.get("bedrooms", 0)) or 0
            baths = item.get("baths", item.get("bathrooms", 0)) or 0
            sqft = _to_int(_pick(item, ["sqft", "livingArea", "area", "sqftLiving"], 0))
            img = _pick(item, ["imgSrc", "image", "photo", "thumbnail"], "")
            detail = _pick(item, ["url", "detailUrl", "hdpUrl"], "")
            if detail and not str(detail).startswith("http"):
                detail = "https://www.zillow.com" + str(detail)

            listings.append({
                "source": "Zillow",
                "zpid": str(_pick(item, ["zpid", "id", "propertyId"], "")),
                "address": address,
                "price": price,
                "beds": beds,
                "baths": baths,
                "sqft": sqft,
                "img": img,
                "url": detail,
                "agent_name": _pick(item, ["brokerName", "agentName", "agent"], ""),
                "agent_email": "",
                "agent_phone": _pick(item, ["brokerPhoneNumber", "phone", "agentPhone"], ""),
                "city": city.title() if city else state.upper(),
                "zip": str(_pick(item, ["zip", "zipcode", "addressZipcode"], "")),
            })

        return listings
    except Exception:
        return []

def _parse_redfin_payload(text: str):
    raw = text.lstrip("{}&&").strip()
    if not raw:
        return []
    try:
        data = json.loads(raw)
    except:
        return []
    payload = data.get("payload", {}) if isinstance(data, dict) else {}
    return payload.get("homes", []) or payload.get("result", {}).get("homes", []) or []

def _redfin_region(query: str, state: str = ""):
    url = "https://www.redfin.com/stingray/do/location-autocomplete"
    q = f"{query}, {state}".strip(", ")
    r = requests.get(url, headers=HEADERS, params={"location": q, "v": 2}, timeout=15)
    if r.status_code != 200:
        return None, None
    try:
        data = json.loads(r.text.lstrip("{}&&"))
    except:
        return None, None

    for section in data.get("payload", {}).get("sections", []):
        for row in section.get("rows", []):
            rid = str(row.get("id", "")).strip()
            if rid.startswith("city_"):
                return rid, 6
            if rid.startswith("zip_"):
                return rid, 7
            if rid.startswith("county_"):
                return rid, 8
            if rid.startswith("state_"):
                return rid, 3
            if rid.startswith("neighborhood_"):
                return rid, 2
    return None, None

def scrape_redfin(state: str, min_price: int, max_price: int, city: str = "", radius_miles: int | None = None):
    listings = []

    query = city if city else state
    region_id, region_type = _redfin_region(query, state if city else "")
    if not region_id:
        return []

    for page in range(1, 6):
        gis_url = "https://www.redfin.com/stingray/api/gis-search"
        params = {
            "al": 1,
            "region_id": region_id,
            "region_type": region_type,
            "min_price": min_price,
            "max_price": max_price,
            "status": 1,
            "uipt": "1,2",
            "v": 8,
            "page_number": page,
            "num_homes": 100,
            "render": "json",
        }

        try:
            r = requests.get(
                gis_url,
                headers={**HEADERS, "Referer": "https://www.redfin.com/"},
                params=params,
                timeout=20,
            )
            if r.status_code != 200:
                break

            homes = _parse_redfin_payload(r.text)
            if not homes:
                break

            before = len(listings)
            for row in homes:
                if not isinstance(row, dict):
                    continue

                price = _to_int(row.get("price", row.get("priceInfo", {}).get("amount", 0)))
                if not price or not (min_price <= price <= max_price):
                    continue

                url_path = row.get("url", row.get("urlPath", ""))
                if url_path and not str(url_path).startswith("http"):
                    url_path = "https://www.redfin.com" + str(url_path)

                agent = row.get("listingAgent", {})
                agent_name = agent.get("agentName", "") if isinstance(agent, dict) else ""

                listings.append({
                    "source": "Redfin",
                    "zpid": str(row.get("propertyId", row.get("id", row.get("mlsId", "")))),
                    "address": row.get("displayAddress", row.get("address", "N/A")),
                    "price": price,
                    "beds": row.get("bedRooms", row.get("beds", 0)) or 0,
                    "baths": row.get("bathRooms", row.get("baths", 0)) or 0,
                    "sqft": row.get("sqFt", row.get("sqft", 0)) or 0,
                    "img": row.get("thumbnail", row.get("imageUrl", "")) or "",
                    "url": url_path,
                    "agent_name": agent_name,
                    "agent_email": "",
                    "agent_phone": "",
                    "city": city.title() if city else state.upper(),
                    "zip": str(row.get("zip", row.get("postalCode", ""))).split(".")[0],
                })

            if len(listings) == before:
                break
        except:
            break

    return listings