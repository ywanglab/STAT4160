# save to scripts/write_eval_protocol.py
from __future__ import annotations
import pandas as pd, numpy as np
from pathlib import Path
from datetime import date

def make_rolling_origin_splits(dates, train_min=252, val_size=63, step=63, embargo=5):
    u = np.array(sorted(pd.to_datetime(pd.Series(dates).unique())))
    i = train_min - 1; out=[]
    while True:
        if i >= len(u): break
        a,b = u[0], u[i]; vs=i+embargo+1; ve=vs+val_size-1
        if ve >= len(u): break
        out.append((a,b,u[vs],u[ve])); i += step
    return out

def main():
    ret = pd.read_parquet("data/processed/returns.parquet").sort_values(["ticker","date"])
    # splits = make_rolling_origin_splits(ret["date"]). # this split is empty
    splits = make_rolling_origin_splits(ret["date"], train_min=80, val_size=21, step=21, embargo=5)
    a,b,c,d = splits[0]
    # Universe info
    univ_files = sorted(Path("data/static").glob("universe_*.csv")) # see below for more explanantions
    univ = univ_files[-1] if univ_files else None # take the last file
    univ_count = pd.read_csv(univ).shape[0] if univ else ret["ticker"].nunique()
    md = []
    md += ["# Evaluation Protocol (Leakage‑Aware)", ""]
    md += ["**Date:** " + date.today().isoformat(), ""]
    md += ["## Splits", f"- Train window (split 1): **{a.date()} → {b.date()}**",
           f"- Embargo: **5** business days", f"- Validation window: **{c.date()} → {d.date()}**",
           f"- Step between origins: **63** business days", ""]
    md += ["## Static Universe", f"- Universe file: **{univ.name if univ else '(none)'}**",
           f"- Count: **{univ_count}** tickers", 
           "- Selection rule: tickers with ≥252 obs by first train end; fixed for all splits.", ""]
    md += ["## Labels", "- `r_1d` = next‑day log return `log_return.shift(-1)` per ticker.",
           "- `r_5d` (if used) = sum of `log_return.shift(-1..-5)`.", ""]
    md += ["## Leakage Controls",
           "- Features computed from ≤ t only (rolling/ewm/expanding without negative shifts).",
           "- No forward‑fill across split boundaries; embargo = 5 days.",
           "- Scalers/normalizers fit on TRAIN only.",
           "- Tests: `tests/test_leakage_features.py`, `tests/test_labels_multistep.py`.", ""]
    md += ["## Caveats",
           "- Educational dataset; not investment advice.",
           "- Survivorship minimized via static universe; still subject to data vendor quirks.", ""]
    Path("reports").mkdir(parents=True, exist_ok=True)
    Path("reports/eval_protocol.md").write_text("\n".join(md))
    print("Wrote reports/eval_protocol.md")

if __name__ == "__main__":
    main()