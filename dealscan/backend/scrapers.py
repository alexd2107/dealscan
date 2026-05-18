import requests
import json
import pandas as pd
import io
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

def scrape_zillow(city_slug: str, min_price: int, max_price: int):
    url = f"https://www.zillow.com/homes/for_sale/{city_slug}_rb/"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")
        tag = soup.find("script", {"id": "__NEXT_DATA__"})
        if not tag:
            return []
        data = json.loads(tag.string)
        results = (data.get("props", {})
                       .get("pageProps", {})
                       .get("searchPageState", {})
                       .get("cat1", {})
                       .get("searchResults", {})
                       .get("listResults", []))
        listings = []
        for l in results:
            price = l.get("unformattedPrice") or l.get("price") or 0
            if isinstance(price, str):
                price = int(price.replace("$","").replace(",","").strip()) if price else 0
            if not (min_price <= price <= max_price):
                continue
            listings.append({
                "source": "Zillow",
                "zpid": l.get("zpid",""),
                "address": l.get("address","N/A"),
                "price": price,
                "beds": l.get("beds", 0),
                "baths": l.get("baths", 0),
                "sqft": l.get("area", 0),
                "img": l.get("imgSrc",""),
                "url": "https://www.zillow.com" + l.get("detailUrl",""),
                "agent_name": l.get("brokerName",""),
                "agent_email": "",
                "agent_phone": l.get("brokerPhoneNumber",""),
                "city": city_slug.replace("-"," ").title(),
                "zip": l.get("addressZipcode",""),
            })
        return listings
    except Exception as e:
        print(f"Zillow scrape error: {e}")
        return []


def scrape_redfin(city: str, state: str, min_price: int, max_price: int):
    try:
        # Step 1: get region id for city
        search_url = "https://www.redfin.com/stingray/do/location-autocomplete"
        params = {"location": f"{city}, {state}", "v": 2}
        r = requests.get(search_url, headers=HEADERS, params=params, timeout=10)
        raw = r.text.lstrip("{}&&")
        data = json.loads(raw)
        payload = data.get("payload", {})
        sections = payload.get("sections", [])
        region_id = None
        region_type = None
        for section in sections:
            for row in section.get("rows", []):
                if row.get("type") == "2":
                    region_id = row.get("id","").replace("city_","")
                    region_type = 6
                    break
            if region_id:
                break
        if not region_id:
            return []

        # Step 2: fetch listings CSV
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
        r2 = requests.get(gis_url, headers={**HEADERS, "Referer": "https://www.redfin.com/"}, params=params2, timeout=15)
        df = pd.read_csv(io.StringIO(r2.text.lstrip("{}&&")))
        listings = []
        for _, row in df.iterrows():
            price = row.get("PRICE", 0)
            try:
                price = int(str(price).replace("$","").replace(",","").strip())
            except:
                price = 0
            if not (min_price <= price <= max_price):
                continue
            listings.append({
                "source": "Redfin",
                "zpid": str(row.get("MLS#", row.get("LISTING ID",""))),
                "address": row.get("ADDRESS","N/A"),
                "price": price,
                "beds": row.get("BEDS", 0),
                "baths": row.get("BATHS", 0),
                "sqft": row.get("SQUARE FEET", 0),
                "img": "",
                "url": "https://www.redfin.com" + str(row.get("URL (SEE https://www.redfin.com/buy-a-home/comparative-market-analysis FOR INFO ON PRICING)","")).strip(),
                "agent_name": row.get("LISTING AGENT",""),
                "agent_email": "",
                "agent_phone": "",
                "city": city,
                "zip": str(row.get("ZIP OR POSTAL CODE","")).split(".")[0],
            })
        return listings
    except Exception as e:
        print(f"Redfin scrape error: {e}")
        return []
