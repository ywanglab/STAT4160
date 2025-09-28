#!/usr/bin/env python
import argparse, sys, time
from pathlib import Path
import pandas as pd, numpy as np

def fetch_yf(ticker, start, end):
    import yfinance as yf
    df = yf.download(ticker, start=start, end=end, auto_adjust=True, progress=False)
    if df is None or df.empty:
        raise RuntimeError("empty")
    df = df.rename(columns=str.lower)[["close","volume"]]
    # --- minimal sanitize to avoid NaNs in adj_close/log_return ---
    df = df.sort_index()
    df = df[~df.index.duplicated(keep="last")]
    df = df.dropna(subset=["close"])
    df["volume"] = df["volume"].fillna(0)
    # --------------------------------------------------------------
    df.index.name = "date"
    df = df.reset_index()
    df["ticker"] = ticker
    return df[["ticker","date","close","volume"]]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tickers", default="tickers_25.csv")
    ap.add_argument("--start", default="2020-01-01")
    ap.add_argument("--end", default="")
    ap.add_argument("--out", default="data/raw/prices.csv")
    args = ap.parse_args()

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    tickers = pd.read_csv(args.tickers)["ticker"].dropna().unique().tolist()

    rows = []
    for t in tickers:
        try:
            df = fetch_yf(t, args.start, args.end or None)
        except Exception:
            # synthetic fallback
            idx = pd.bdate_range(args.start, args.end or pd.Timestamp.today().date())
            rng = np.random.default_rng(42 + hash(t)%1000)
            r = rng.normal(0, 0.01, len(idx))
            price = 100*np.exp(np.cumsum(r))
            vol = rng.integers(1e5, 5e6, len(idx))
            df = pd.DataFrame({"ticker": t, "date": idx, "close": price, "volume": vol})
        df["date"] = pd.to_datetime(df["date"]).dt.date
        df["adj_close"] = df["close"]
        df = df.drop(columns=["close"])
        df["log_return"] = np.log(df["adj_close"]).diff().fillna(0.0)
        rows.append(df)

    allp = pd.concat(rows, ignore_index=True)
    allp = allp[["ticker","date","adj_close","volume","log_return"]]
    allp.to_csv(out, index=False)
    print("Wrote", out, "rows:", len(allp))

if __name__ == "__main__":
    sys.exit(main())
