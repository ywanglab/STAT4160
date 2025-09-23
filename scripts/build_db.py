# scripts/build_db.py
#!/usr/bin/env python
import argparse, sys, textwrap, sqlite3
from pathlib import Path
import pandas as pd, numpy as np

DDL = textwrap.dedent("""
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS meta (
  ticker TEXT PRIMARY KEY,
  name   TEXT,
  sector TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS prices (
  ticker     TEXT NOT NULL,
  date       TEXT NOT NULL,
  adj_close  REAL NOT NULL CHECK (adj_close >= 0),
  volume     INTEGER NOT NULL CHECK (volume >= 0),
  log_return REAL NOT NULL,
  PRIMARY KEY (ticker,date),
  FOREIGN KEY (ticker) REFERENCES meta(ticker)
);
CREATE INDEX IF NOT EXISTS idx_prices_date ON prices(date);
""")

def load_meta(con, tickers_csv: Path):
    if tickers_csv.exists():
        tks = pd.read_csv(tickers_csv)["ticker"].dropna().unique().tolist()
    else:
        raise SystemExit(f"tickers CSV not found: {tickers_csv}")
    sectors = ["Technology","Financials","Healthcare","Energy","Consumer"]
    meta = pd.DataFrame({
        "ticker": tks,
        "name": tks,
        "sector": [sectors[i % len(sectors)] for i in range(len(tks))]
    })
    with con:
        con.executemany("INSERT OR REPLACE INTO meta(ticker,name,sector) VALUES(?,?,?)",
                        meta.itertuples(index=False, name=None))

def load_prices(con, prices_csv: Path):
    df = pd.read_csv(prices_csv, parse_dates=["date"])
    df["date"] = df["date"].dt.strftime("%Y-%m-%d")
    df = df[["ticker","date","adj_close","volume","log_return"]].drop_duplicates(["ticker","date"])
    with con:
        con.executemany(
            "INSERT OR REPLACE INTO prices(ticker,date,adj_close,volume,log_return) VALUES(?,?,?,?,?)",
            df.itertuples(index=False, name=None)
        )

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="data/prices.db")
    ap.add_argument("--tickers", default="tickers_25.csv")
    ap.add_argument("--prices", default="data/raw/prices.csv")
    # args = ap.parse_args()
    args, _ = ap.parse_known_args()

    Path(args.db).parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(args.db)
    con.executescript(DDL)
    load_meta(con, Path(args.tickers))
    load_prices(con, Path(args.prices))
    con.close()
    print("Built DB:", args.db)

if __name__ == "__main__":
    # sys.exit(main())
    main()