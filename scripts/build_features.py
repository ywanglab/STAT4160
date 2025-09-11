#!/usr/bin/env python
import argparse
from pathlib import Path
import pandas as pd, numpy as np

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="data/raw/prices.csv")
    ap.add_argument("--out", default="data/processed/features.parquet")
    ap.add_argument("--roll", type=int, default=20)
    args = ap.parse_args()

    df = pd.read_csv(args.input, parse_dates=["date"])
    df = df.sort_values(["ticker","date"])
    # groupwise lags
    df["r_1d"] = df["log_return"]
    for k in (1,2,3):
        df[f"lag{k}"] = df.groupby("ticker")["r_1d"].shift(k)
    df["roll_mean"] = (df.groupby("ticker")["r_1d"]
                         .rolling(args.roll, min_periods=args.roll//2).mean()
                         .reset_index(level=0, drop=True))
    df["roll_std"]  = (df.groupby("ticker")["r_1d"]
                         .rolling(args.roll, min_periods=args.roll//2).std()
                         .reset_index(level=0, drop=True))
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    # Save compactly
    df.to_parquet(out, index=False)
    print("Wrote", out, "rows:", len(df))

if __name__ == "__main__":
    main()
