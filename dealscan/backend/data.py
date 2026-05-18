import requests
import os
from dotenv import load_dotenv

load_dotenv()
HUD_TOKEN = os.getenv("HUD_TOKEN","")

STATE_CODES = {
    "AL":"01","AK":"02","AZ":"04","AR":"05","CA":"06","CO":"08","CT":"09","DE":"10",
    "FL":"12","GA":"13","HI":"15","ID":"16","IL":"17","IN":"18","IA":"19","KS":"20",
    "KY":"21","LA":"22","ME":"23","MD":"24","MA":"25","MI":"26","MN":"27","MS":"28",
    "MO":"29","MT":"30","NE":"31","NV":"32","NH":"33","NJ":"34","NM":"35","NY":"36",
    "NC":"37","ND":"38","OH":"39","OK":"40","OR":"41","PA":"42","RI":"44","SC":"45",
    "SD":"46","TN":"47","TX":"48","UT":"49","VT":"50","VA":"51","WA":"53","WV":"54",
    "WI":"55","WY":"56","DC":"11"
}

_hud_cache = {}

def get_hud_rent(state_abbr: str, county_hint: str = "") -> dict:
    key = state_abbr.upper()
    if key in _hud_cache:
        data = _hud_cache[key]
    else:
        url = f"https://www.huduser.gov/hudapi/public/fmr/statedata/{key}"
        headers = {"Authorization": f"Bearer {HUD_TOKEN}"}
        try:
            r = requests.get(url, headers=headers, timeout=10)
            data = r.json().get("data", {}).get("basicdata", [])
            _hud_cache[key] = data
        except:
            return {"rent_1br": 1200, "rent_2br": 1500, "rent_3br": 1800}

    for item in data:
        cname = item.get("county_name","").lower()
        if county_hint.lower() in cname or not county_hint:
            return {
                "rent_1br": item.get("Efficiency", 1200),
                "rent_2br": item.get("One-Bedroom", 1500),
                "rent_3br": item.get("Two-Bedroom", 1800),
            }
    if data:
        first = data[0]
        return {
            "rent_1br": first.get("Efficiency", 1200),
            "rent_2br": first.get("One-Bedroom", 1500),
            "rent_3br": first.get("Two-Bedroom", 1800),
        }
    return {"rent_1br": 1200, "rent_2br": 1500, "rent_3br": 1800}


def get_census_growth(zip_code: str) -> float:
    try:
        url = "https://api.census.gov/data/2022/acs/acs5/profile"
        params = {
            "get": "DP04_0089E,DP05_0001E",
            "for": f"zip code tabulation area:{zip_code}",
        }
        r = requests.get(url, params=params, timeout=10)
        rows = r.json()
        if len(rows) > 1:
            median_val = int(rows[1][0] or 0)
            population = int(rows[1][1] or 0)
            return round(min(100, (median_val / 8000) + (population / 15000)), 1)
    except:
        pass
    return 50.0
