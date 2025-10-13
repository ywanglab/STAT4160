#!/usr/bin/env python
import numpy as np, pandas as pd, pathlib
def build_features(ret: pd.DataFrame, windows=(5,10,20), add_rsi=True):
    g = ret.sort_values(["ticker","date"]).groupby("ticker", group_keys=False)
    out = ret.copy()

    # Lags of log_return (past info)
    for k in [1,2,3]:
        out[f"lag{k}"] = g["log_return"].shift(k)

    # Rolling mean/std and z-score of returns using past W days **including today**,
    # which is fine because target is r_{t+1}. No extra shift needed.
    for W in windows:
        rm = g["log_return"].rolling(W, min_periods=W).mean()
        rsd= g["log_return"].rolling(W, min_periods=W).std()
        out[f"roll_mean_{W}"] = rm.reset_index(level=0, drop=True) #level 0 is the grouping ticker
        out[f"roll_std_{W}"]  = rsd.reset_index(level=0, drop=True)
        out[f"zscore_{W}"]    = (out["log_return"] - out[f"roll_mean_{W}"]) / (out[f"roll_std_{W}"] + 1e-8)

    # Expanding stats (from start to t): long-memory
    out["exp_mean"] = g["log_return"].expanding(min_periods=20).mean().reset_index(level=0, drop=True)
    out["exp_std"]  = g["log_return"].expanding(min_periods=20).std().reset_index(level=0, drop=True)

    # Exponential weighted (decayed memory)
    for W in [10,20]:
        out[f"ewm_mean_{W}"] = g["log_return"].apply(lambda s: s.ewm(span=W, adjust=False).mean())
        out[f"ewm_std_{W}"]  = g["log_return"].apply(lambda s: s.ewm(span=W, adjust=False).std())

    # Optional RSI(14) using returns sign proxy (toy version)
    if add_rsi:
        def rsi14(s):
            delta = s.diff()
            up = delta.clip(lower=0).ewm(alpha=1/14, adjust=False).mean()
            dn = (-delta.clip(upper=0)).ewm(alpha=1/14, adjust=False).mean()
            rs = up / (dn + 1e-12)
            return 100 - (100 / (1 + rs))
        out["rsi_14"] = g["adj_close"].apply(rsi14) if "adj_close" in out else g["log_return"].apply(rsi14)

    # Cast dtypes
    for c in out.columns:
        if c not in ["date","ticker","weekday","month"] and pd.api.types.is_float_dtype(out[c]):
            out[c] = out[c].astype("float32")
    out["ticker"] = out["ticker"].astype("category")
    return out
    
import numpy as np, pandas as pd, pathlib

def build():
    p = pathlib.Path("data/processed/returns.parquet")
    if not p.exists(): raise SystemExit("Missing returns.parquet — finish Session 9.")
    prices = pd.read_parquet("data/processed/prices.parquet")
    ret = pd.read_parquet(p)
    ret2 = ret.merge(prices[["ticker","date","adj_close","volume"]], on=["ticker","date"], how="left")
    # (Paste the build_features() from class)
    # ...
    fv1 = build_features(ret2)
    keep = ["date","ticker","log_return","r_1d","weekday","month",
            "lag1","lag2","lag3","roll_mean_20","roll_std_20","zscore_20",
            "ewm_mean_20","ewm_std_20","exp_mean","exp_std","adj_close","volume"]
    keep = [c for c in keep if c in fv1.columns]
    fv1 = fv1[keep].dropna().sort_values(["ticker","date"])
    fv1.to_parquet("data/processed/features_v1.parquet", compression="zstd", index=False)
    print("Wrote data/processed/features_v1.parquet", fv1.shape)
if __name__ == "__main__":
    build()