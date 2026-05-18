import requests
import json
from bs4 import BeautifulSoup

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

def _clean_city(city: str):
    return (city or "").strip().lower().replace(" ", "-")

def _redfin_region(query: str, state: str = ""):
    search_url = "https://www.redfin.com/stingray/do/location-autocomplete"
    q = f"{query}, {state}".strip(", ")
    r = requests.get(search_url, headers=HEADERS, params={"location": q, "v": 2}, timeout=15)
    if r.status_code != 200:
        return None, None, {"status_code": r.status_code, "rows": []}

    raw = r.text.lstrip("{}&&")
    try:
        data = json.loads(raw)
    except:
        return None, None, {"status_code": r.status_code, "rows": []}

    rows_out = []
    for section in data.get("payload", {}).get("sections", []):
        for row in section.get("rows", []):
            rid = str(row.get("id", "")).strip()
            rtype = row.get("type")
            rows_out.append({"id": rid, "type": rtype, "name": row.get("name", "")})

            if not rid:
                continue
            if rid.startswith("city_"):
                return rid, 6, {"status_code": r.status_code, "rows": rows_out}
            if rid.startswith("zip_"):
                return rid, 7, {"status_code": r.status_code, "rows": rows_out}
            if rid.startswith("county_"):
                return rid, 8, {"status_code": r.status_code, "rows": rows_out}
            if rid.startswith("state_"):
                return rid, 3, {"status_code": r.status_code, "rows": rows_out}
            if rid.startswith("neighborhood_"):
                return rid, 2, {"status_code": r.status_code, "rows": rows_out}

    return None, None, {"status_code": r.status_code, "rows": rows_out}

def scrape_redfin(state: str, min_price: int, max_price: int, city: str = "", radius_miles: int | None = None, debug: bool = False):
    listings = []
    try:
        query = city if city else state
        region_id, region_type, dbg = _redfin_region(query, state if city else "")
        if not region_id:
            return {"listings": [], "debug": {"stage": "region_lookup_failed", **dbg}} if debug else []

        redfin_debug = {
            "stage": "searching",
            "region_id": region_id,
            "region_type": region_type,
            "autocomplete": dbg,
            "pages": [],
        }

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
            r2 = requests.get(
                gis_url,
                headers={**HEADERS, "Referer": "https://www.redfin.com/"},
                params=params,
                timeout=20,
            )

            page_debug = {
                "page": page,
                "status_code": r2.status_code,
                "has_text": bool(r2.text),
                "homes_count": 0,
            }

            if r2.status_code != 200:
                redfin_debug["pages"].append(page_debug)
                break

            raw = r2.text.lstrip("{}&&").strip()
            if not raw:
                redfin_debug["pages"].append(page_debug)
                break

            try:
                data = json.loads(raw)
            except:
                redfin_debug["pages"].append(page_debug)
                break

            payload = data.get("payload", {})
            homes = payload.get("homes", []) or payload.get("result", {}).get("homes", []) or []
            page_debug["homes_count"] = len(homes)
            redfin_debug["pages"].append(page_debug)

            if not homes:
                break

            before = len(listings)
            for row in homes:
                price = _to_int(row.get("price", row.get("priceInfo", {}).get("amount", 0)))
                if not price:
                    continue
                if not (min_price <= price <= max_price):
                    continue

                addr = row.get("displayAddress", row.get("address", "N/A"))
                url_path = row.get("url", row.get("urlPath", ""))
                if url_path and not str(url_path).startswith("http"):
                    url_path = "https://www.redfin.com" + str(url_path)

                agent = row.get("listingAgent", {})
                agent_name = agent.get("agentName", "") if isinstance(agent, dict) else ""

                listings.append({
                    "source": "Redfin",
                    "zpid": str(row.get("propertyId", row.get("id", row.get("mlsId", "")))),
                    "address": addr,
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

        return {"listings": listings, "debug": redfin_debug} if debug else listings
    except Exception as e:
        return {"listings": [], "debug": {"error": str(e)}} if debug else []

def _zillow_parse_results(html: str):
    soup = BeautifulSoup(html, "html.parser")

    scripts = soup.find_all("script")
    for tag in scripts:
        txt = tag.string or tag.get_text() or ""
        if "searchPageState" not in txt and "listResults" not in txt and "__NEXT_DATA__" not in txt:
            continue
        try:
            data = json.loads(txt)
        except:
            continue

        try:
            results = (
                data.get("props", {})
                .get("pageProps", {})
                .get("searchPageState", {})
                .get("cat1", {})
                .get("searchResults", {})
                .get("listResults", [])
            )
            if results:
                return results
        except:
            pass

        try:
            results = (
                data.get("props", {})
                .get("pageProps", {})
                .get("searchPageState", {})
                .get("cat1", {})
                .get("searchResults", {})
                .get("listResults", [])
            )
            if results:
                return results
        except:
            pass

    return []

def scrape_zillow(state: str, min_price: int, max_price: int, city: str = "", radius_miles: int | None = None, debug: bool = False):
    state = state.strip().lower()
    city_clean = _clean_city(city)
    urls = []

    if city_clean:
        urls.append(f"https://www.zillow.com/{city_clean}-{state}/")
        urls.append(f"https://www.zillow.com/homes/for_sale/{city_clean}-{state}_rb/")

    urls.extend([
        f"https://www.zillow.com/{state}/homes/",
        f"https://www.zillow.com/{state}/coming-soon/",
    ])

    listings = []
    zillow_debug = {"stage": "searching", "urls": [], "matches": []}

    for url in urls:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=20)
            url_debug = {"url": url, "status_code": resp.status_code, "results_count": 0}
            zillow_debug["urls"].append(url_debug)

            if resp.status_code != 200:
                continue

            results = _zillow_parse_results(resp.text)
            url_debug["results_count"] = len(results)

            for l in results:
                price = _to_int(l.get("unformattedPrice") or l.get("price") or 0)
                if not price:
                    continue
                if not (min_price <= price <= max_price):
                    continue

                detail_url = l.get("detailUrl", "")
                if detail_url and not detail_url.startswith("http"):
                    detail_url = "https://www.zillow.com" + detail_url

                listings.append({
                    "source": "Zillow",
                    "zpid": l.get("zpid", ""),
                    "address": l.get("address", "N/A"),
                    "price": price,
                    "beds": l.get("beds", 0) or 0,
                    "baths": l.get("baths", 0) or 0,
                    "sqft": l.get("area", 0) or 0,
                    "img": l.get("imgSrc", ""),
                    "url": detail_url,
                    "agent_name": l.get("brokerName", ""),
                    "agent_email": "",
                    "agent_phone": l.get("brokerPhoneNumber", ""),
                    "city": city.title() if city else state.upper(),
                    "zip": l.get("addressZipcode", ""),
                })

            if listings:
                if debug:
                    return {"listings": listings, "debug": zillow_debug}
                return listings
        except Exception as e:
            zillow_debug["matches"].append({"url": url, "error": str(e)})
            continue

    return {"listings": listings, "debug": zillow_debug} if debug else listings