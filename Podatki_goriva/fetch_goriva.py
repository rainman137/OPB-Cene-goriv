import requests
import csv
import os
from datetime import date

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "data")
os.makedirs(OUTPUT_DIR, exist_ok=True)

BASE = "https://goriva.si/api/v1"
TODAY = date.today().isoformat()


def fetch_fuel_types():
    r = requests.get(f"{BASE}/fuel/", params={"format": "json"})
    rows = r.json()
    with open(f"{OUTPUT_DIR}/fuel_types.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "code", "name", "long_name"])
        for row in rows:
            w.writerow([row["pk"], row["code"], row["name"], row["long_name"]])
    print(f"  -> {len(rows)} fuel types saved")


def fetch_franchises():
    r = requests.get(f"{BASE}/franchise/", params={"format": "json"})
    rows = r.json()
    with open(f"{OUTPUT_DIR}/franchises.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "name"])
        for row in rows:
            w.writerow([row["pk"], row["name"]])
    print(f"  -> {len(rows)} franchises saved")


def fetch_stations_and_prices():
    all_stations = []
    all_prices = []
    page = 1

    while True:
        print(f"  fetching page {page}...")
        r = requests.get(f"{BASE}/search/", params={
            "format": "json", "page": page,
            "franchise": "", "name": "", "o": "", "position": "", "radius": ""
        })
        data = r.json()

        for s in data["results"]:
            all_stations.append({
                "id": s["pk"],
                "franchise_id": s["franchise"],
                "name": s["name"],
                "address": s["address"],
                "zip_code": s["zip_code"],
                "lat": s["lat"],
                "lng": s["lng"],
                "open_hours": s.get("open_hours", "").replace("\n", " | ").replace("\r", "").strip(),
            })
            for fuel_code, price in s["prices"].items():
                if price and price > 0.01:
                    all_prices.append({
                        "station_id": s["pk"],
                        "fuel_code": fuel_code,
                        "price": price,
                        "date": TODAY,
                    })

        if data["next"] is None:
            break
        page += 1

    with open(f"{OUTPUT_DIR}/stations.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "franchise_id", "name", "address", "zip_code", "lat", "lng", "open_hours"])
        for s in all_stations:
            w.writerow(s.values())
    print(f"  -> {len(all_stations)} stations saved")

    with open(f"{OUTPUT_DIR}/prices_{TODAY}.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["station_id", "fuel_code", "price_eur", "date"])
        for p in all_prices:
            w.writerow(p.values())
    print(f"  -> {len(all_prices)} price records saved")


if __name__ == "__main__":
    print("Fetching fuel types...")
    fetch_fuel_types()
    print("Fetching franchises...")
    fetch_franchises()
    print("Fetching stations + prices...")
    fetch_stations_and_prices()
