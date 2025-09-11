#!/usr/bin/env python
import argparse, json
from pathlib import Path
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--features", default="data/processed/features.parquet")
    ap.add_argument("--out-metrics", default="reports/baseline_metrics.json")
    args = ap.parse_args()

    df = pd.read_parquet(args.features)
    # Train/test split by date (last 20% for test)
    df = df.dropna(subset=["lag1","lag2","lag3","r_1d"])
    n = len(df)
    split = int(n*0.8)
    Xtr = df[["lag1","lag2","lag3"]].iloc[:split].values
    ytr = df["r_1d"].iloc[:split].values
    Xte = df[["lag1","lag2","lag3"]].iloc[split:].values
    yte = df["r_1d"].iloc[split:].values

    model = LinearRegression().fit(Xtr, ytr)
    pred = model.predict(Xte)
    mae = float(mean_absolute_error(yte, pred))

    Path("reports").mkdir(exist_ok=True)
    with open(args.out_metrics, "w") as f:
        json.dump({"model":"linear(lag1,lag2,lag3)","test_mae":mae,"n_test":len(yte)}, f, indent=2)
    print("Wrote", args.out_metrics, "MAE:", mae)

if __name__ == "__main__":
    main()
