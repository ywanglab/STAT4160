#!/usr/bin/env python
import os, json, time, hashlib, pandas as pd, sqlite3
from pathlib import Path
import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("FRED_API_KEY","").strip()
BASE = "https://api.stlouisfed.org/fred/series/observations"

def sess():
    s = requests.Session()
    s.headers.update({"User-Agent":"dspt-class/1.0"})
    s.mount("https://", HTTPAdapter(max_retries=Retry(total=3, backoff_factor=0.5,
                                                      status_forcelist=[429,500,502,503,504])))
    return s

def ckey(url, params):
    raw = url + "?" + "&".join(f"{k}={params[k]}" for k in sorted(params))
    return hashlib.sha1(raw.encode()).hexdigest()

def cached_get(url, params, ttl=86400):
    key = ckey(url, params); p = Path(f".cache/api/{key}.json")
    p.parent.mkdir(parents=True, exist_ok=True)
    if p.exists() and (time.time() - p.stat().st_mtime < ttl):
        return json.loads(p.read_text())
    r = sess().get(url, params=params, timeout=20); r.raise_for_status()
    data = r.json(); p.write_text(json.dumps(data)); return data

def fetch_series(series_id, start="2015-01-01"):
    if not API_KEY: raise SystemExit("Set FRED_API_KEY in .env")
    params = {"series_id":series_id, "api_key":API_KEY, "file_type":"json", "observation_start":start}
    data = cached_get(BASE, params)
    df = pd.DataFrame(data["observations"])[["date","value"]]
    df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")  # store as TEXT YYYY-MM-DD
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df["series_id"] = series_id
    # df = df.drop_duplicates(subset=["series_id","date"])
    return df.dropna(subset=["value"])

def ensure_schema(con):
    con.execute("""
        CREATE TABLE IF NOT EXISTS macro_series(
            series_id TEXT,
            date      TEXT,
            value     REAL,
            PRIMARY KEY(series_id, date)
        )
    """)
    # Optional: index on date for faster slicing across all series
    con.execute("CREATE INDEX IF NOT EXISTS idx_macro_series_date ON macro_series(date)")

def upsert_dataframe(con, df):
    sql = """
        INSERT INTO macro_series(series_id, date, value)
        VALUES (?, ?, ?)
        ON CONFLICT(series_id, date) DO UPDATE SET
            value = excluded.value  --replace teh existing row's value with the incoming row's value
    """
    rows = list(df[["series_id","date","value"]].itertuples(index=False, name=None))
    con.executemany(sql, rows)

def main(series_id, start="2015-01-01"):
    df = fetch_series(series_id, start=start)
    con = sqlite3.connect("data/prices.db")
    try:
        ensure_schema(con)
        upsert_dataframe(con, df)
        con.commit()
    finally:
        con.close()
    print(f"Upserted {series_id}: {len(df)} rows from {start}")

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--series-id", default="VIXCLS")
    ap.add_argument("--start", default="2015-01-01")
    args, _ = ap.parse_known_args()
    main(args.series_id, start=args.start)
