import requests
import pandas as pd
from datetime import datetime
from pathlib import Path

BLS_API_URL = "https://api.bls.gov/publicAPI/v2/timeseries/data/"

SERIES = {
    "nonfarm_employment": "CES0000000001",
    "unemployment_rate": "LNS14000000",
    "labor_force_participation": "LNS11300000",
    "employment_population_ratio": "LNS12300000",
    "avg_hourly_earnings": "CES0500000003",
    "avg_weekly_hours": "CES0500000002",
}

DATA_PATH = Path("data/bls_data.csv")

def fetch_latest_data():
    current_year = datetime.now().year
    payload = {
        "seriesid": list(SERIES.values()),
        "startyear": current_year - 2,
        "endyear": current_year
    }

    response = requests.post(BLS_API_URL, json=payload)
    response.raise_for_status()
    data = response.json()["Results"]["series"]

    rows = []
    for series in data:
        name = [k for k, v in SERIES.items() if v == series["seriesID"]][0]
        for item in series["data"]:
            if item["period"].startswith("M"):
                rows.append({
                    "date": f"{item['year']}-{item['period'][1:]}-01",
                    name: float(item["value"])
                })

    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"])

    df = df.groupby("date").first().reset_index()
    return df


def update_dataset():
    new_data = fetch_latest_data()

    if DATA_PATH.exists() and DATA_PATH.stat().st_size > 0:
        existing = pd.read_csv(DATA_PATH, parse_dates=["date"])
        combined = (
            pd.concat([existing, new_data])
            .drop_duplicates(subset="date")
            .sort_values("date")
        )
    else:
        combined = new_data.sort_values("date")

    combined.to_csv(DATA_PATH, index=False)



if __name__ == "__main__":
    update_dataset()
