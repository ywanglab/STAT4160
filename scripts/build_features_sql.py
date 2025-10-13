#!/usr/bin/env python
import argparse, sqlite3, pandas as pd, math
from pathlib import Path

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="data/prices.db")
    ap.add_argument("--sqlfile", default="sql/features_window.sql")
    ap.add_argument("--start", default="2019-01-01")
    ap.add_argument("--end",   default="2025-08-01")
    ap.add_argument("--out",   default="data/processed/features_sql.parquet")
    ap.add_argument("--drop-head", type=int, default=3)
    args = ap.parse_args()

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(args.db)
    con.create_function("SQRT", 1,
        lambda x: math.sqrt(x) if x is not None and x >= 0 else None)

    sql = Path(args.sqlfile).read_text()
    df = pd.read_sql_query(sql, con, params=[args.start, args.end])

    df["roll_std_20"] = (df["roll_var_20"].clip(lower=0)).pow(0.5)
    df["zscore_20"] = (df["r_1d"] - df["roll_mean_20"]) / df["roll_std_20"].replace(0, pd.NA)

    df = (df.sort_values(["ticker","date"])
            .groupby("ticker", group_keys=False)
            .apply(lambda g: g.iloc[args.drop_head:]))

    df.to_parquet(args.out, index=False)
    print("✅ Wrote", args.out, "Rows:", len(df))

if __name__ == "__main__":
    main()
