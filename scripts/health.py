# scripts/health.py
from __future__ import annotations
import pandas as pd, numpy as np, json
from pathlib import Path

def df_health(df: pd.DataFrame) -> dict:
    out = {}
    out["rows"] = int(len(df))
    out["cols"] = int(df.shape[1])
    out["date_min"] = str(pd.to_datetime(df["date"]).min().date())
    out["date_max"] = str(pd.to_datetime(df["date"]).max().date())
    out["tickers"]  = int(df["ticker"].nunique())
    # Null counts (top 10)
    na = df.isna().sum().sort_values(ascending=False)
    out["nulls"] = na[na>0].head(10).to_dict()
    # Duplicates
    out["dup_key_rows"] = int(df[["ticker","date"]].duplicated().sum())
    # Example numeric ranges for core cols
    for c in [x for x in ["log_return","r_1d","roll_std_20"] if x in df.columns]:
        s = pd.to_numeric(df[c], errors="coerce")
        out[f"{c}_min"] = float(np.nanmin(s))
        out[f"{c}_max"] = float(np.nanmax(s))
    return out

def write_health_report(in_parquet="data/processed/features_v1.parquet",
                        out_json="reports/health.json", out_md="reports/health.md"):
    p = Path(in_parquet)
    if not p.exists():
        raise SystemExit(f"Missing {in_parquet}.")
    df = pd.read_parquet(p)
    h = df_health(df)
    Path(out_json).write_text(json.dumps(h, indent=2))
    # Render a small Markdown summary
    lines = [
        "# Data Health Summary",
        "",
        f"- Rows: **{h['rows']}**; Cols: **{h['cols']}**; Tickers: **{h['tickers']}**",
        f"- Date range: **{h['date_min']} → {h['date_max']}**",
        f"- Duplicate (ticker,date) rows: **{h['dup_key_rows']}**",
    ]
    if h.get("nulls"):
        lines += ["", "## Top Null Counts", ""]
        lines += [f"- **{k}**: {v}" for k,v in h["nulls"].items()]
    Path(out_md).write_text("\n".join(lines))
    print("Wrote", out_json, "and", out_md)