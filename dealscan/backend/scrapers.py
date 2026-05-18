from pathlib import Path

content = '''import requests
import json
import pandas as pd
import io
from bs4 import BeautifulSoup
from urllib.parse import urlencode

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


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


def scrape_zillow(city_slug: str, min_price: int, max_price: int):
    urls = [
        f"https://www.zillow.com/homes/for_sale/{city_slug}_rb/",
        f"https://www.zillow.com/homes/{city_slug}_rb/",
    ]
    listings = []

    for url in urls:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=20)
            if resp.status_code != 200:
                continue
            soup = BeautifulSoup(resp.text, "html.parser")

            # Try JSON script first
            scripts = soup.find_all("script")
            for tag in scripts:
                txt = tag.string or tag.get_text() or ""
                if "searchResults" in txt and "price" in txt:
                    try:
                        data = json.loads(txt)
                        results = (
                            data.get("props", {})
                            .get("pageProps", {})
                            .get("searchPageState", {})
                            .get("cat1", {})
                            .get("searchResults", {})
                            .get("listResults", [])
                        )
                        for l in results:
                            price = _to_int(l.get("unformattedPrice") or l.get("price") or 0)
                            if not (min_price <= price <= max_price):
                                continue
                            listings.append({
                                "source": "Zillow",
                                "zpid": l.get("zpid", ""),
                                "address": l.get("address", "N/A"),
                                "price": price,
                                "beds": l.get("beds", 0) or 0,
                                "baths": l.get("baths", 0) or 0,
                                "sqft": l.get("area", 0) or 0,
                                "img": l.get("imgSrc", ""),
                                "url": "https://www.zillow.com" + l.get("detailUrl", ""),
                                "agent_name": l.get("brokerName", ""),
                                "agent_email": "",
                                "agent_phone": l.get("brokerPhoneNumber", ""),
                                "city": city_slug.replace("-", " ").title(),
                                "zip": l.get("addressZipcode", ""),
                            })
                        if listings:
                            return listings
                    except:
                        pass

            # Fallback: look for embedded JSON blobs with listing info
            text = resp.text
            for marker in ["zpid", "detailUrl", "address", "unformattedPrice"]:
                if marker not in text:
                    continue
            # If Zillow changes the page, don't invent data; just return what we found so far
        except Exception:
            continue

    return listings


def scrape_redfin(city: str, state: str, min_price: int, max_price: int):
    listings = []
    try:
        search_url = "https://www.redfin.com/stingray/do/location-autocomplete"
        params = {"location": f"{city}, {state}", "v": 2}
        r = requests.get(search_url, headers=HEADERS, params=params, timeout=15)
        if r.status_code != 200:
            return []

        raw = r.text.lstrip("{}&&")
        data = json.loads(raw)
        payload = data.get("payload", {})
        sections = payload.get("sections", [])
        region_id = None
        region_type = None
        for section in sections:
            for row in section.get("rows", []):
                rid = str(row.get("id", ""))
                if row.get("type") == "2" and rid.startswith("city_"):
                    region_id = rid.replace("city_", "")
                    region_type = 6
                    break
            if region_id:
                break
        if not region_id:
            return []

        gis_url = "https://www.redfin.com/stingray/api/gis-csv"
        params2 = {
            "al": 1,
            "region_id": region_id,
            "region_type": region_type,
            "min_price": min_price,
            "max_price": max_price,
            "status": 1,
            "uipt": "1,2",
            "v": 8,
            "num_homes": 100,
        }
        r2 = requests.get(gis_url, headers={**HEADERS, "Referer": "https://www.redfin.com/"}, params=params2, timeout=20)
        if r2.status_code != 200:
            return []

        txt = r2.text.lstrip("{}&&")
        if not txt.strip():
            return []

        df = pd.read_csv(io.StringIO(txt))
        for _, row in df.iterrows():
            price = _to_int(row.get("PRICE", 0))
            if price and not (min_price <= price <= max_price):
                continue
            if not price:
                continue
            addr = row.get("ADDRESS", "N/A")
            url_part = str(
                row.get(
                    "URL (SEE https://www.redfin.com/buy-a-home/comparative-market-analysis FOR INFO ON PRICING)",
                    row.get("URL", "")
                )
            ).strip()
            listings.append({
                "source": "Redfin",
                "zpid": str(row.get("MLS#", row.get("LISTING ID", ""))),
                "address": addr,
                "price": price,
                "beds": row.get("BEDS", 0) or 0,
                "baths": row.get("BATHS", 0) or 0,
                "sqft": row.get("SQUARE FEET", 0) or 0,
                "img": "",
                "url": "https://www.redfin.com" + url_part if url_part.startswith("/") else url_part,
                "agent_name": row.get("LISTING AGENT", ""),
                "agent_email": "",
                "agent_phone": "",
                "city": city,
                "zip": str(row.get("ZIP OR POSTAL CODE", "")).split(".")[0],
            })
        return listings
    except Exception:
        return []
'''
Path('dealscan/backend/scrapers.py').write_text(content)
print('scrapers.py rewritten')