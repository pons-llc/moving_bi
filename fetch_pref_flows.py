"""
Fetch prefecture-to-prefecture migration flows from e-Stat API.
Uses cdArea and cdCat01 filtering to get only the 47x47 prefecture matrix.
"""
import os
import json
import time
import httpx
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent / ".env")
API_KEY = os.getenv("ESTAT_API_KEY")
if not API_KEY:
    raise RuntimeError("ESTAT_API_KEY not set")

BASE_URL = "https://api.e-stat.go.jp/rest/3.0/app/json/getStatsData"

# Prefecture codes: 01000 - 47000
PREF_CODES = [f"{i:02d}000" for i in range(1, 48)]
PREF_CODES_STR = ",".join(PREF_CODES)

# Dataset IDs per year for 転入 (移動前の住所地別転入者数)
DATASETS = {
    2020: "0003420513",
    2021: "0003448460",
    2022: "0004003462",
    2023: "0004014382",
}

results = {}  # year -> list of {from, to, count}

for year, stats_id in DATASETS.items():
    print(f"Fetching {year} (dataset {stats_id})...", flush=True)
    params = {
        "appId": API_KEY,
        "statsDataId": stats_id,
        "cdCat01": PREF_CODES_STR,   # destination (転入先) = prefecture codes
        "cdArea": PREF_CODES_STR,     # source (前住地) = prefecture codes
        "cdCat02": "60000",           # 総数 (all nationalities)
        "limit": 10000,
    }
    flows = []
    start = 1
    while True:
        params["startPosition"] = start
        with httpx.Client(timeout=60.0) as client:
            r = client.get(BASE_URL, params=params)
            r.raise_for_status()
        data = r.json()
        sd = data.get("GET_STATS_DATA", {})
        result_inf = sd.get("RESULT", {})
        if result_inf.get("STATUS", 0) != 0:
            print(f"  API error: {result_inf.get('ERROR_MSG')}")
            break
        statistical = sd.get("STATISTICAL_DATA", {})
        result_meta = statistical.get("RESULT_INF", {})
        total = result_meta.get("TOTAL_NUMBER", 0)
        from_n = result_meta.get("FROM_NUMBER", start)
        to_n = result_meta.get("TO_NUMBER", start)
        values = statistical.get("DATA_INF", {}).get("VALUE", [])
        if isinstance(values, dict):
            values = [values]
        print(f"  pos {from_n}-{to_n} / {total}, got {len(values)} records", flush=True)
        for v in values:
            flows.append({
                "from": v.get("@area"),   # source prefecture
                "to": v.get("@cat01"),    # destination prefecture
                "count": int(v.get("$", 0) or 0),
            })
        if to_n >= total:
            break
        start = to_n + 1
        time.sleep(0.5)  # be polite to the API
    results[year] = flows
    print(f"  Total flows for {year}: {len(flows)}", flush=True)
    time.sleep(1.0)

# Save to JSON
output_path = "/Users/tatsurohatori/Documents/遊び/pref_flows_data.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print(f"\nSaved to {output_path}")
print(f"Total records: {sum(len(v) for v in results.values())}")
