# tests/test_leakage_features.py
from __future__ import annotations
import numpy as np, pandas as pd
import pytest

SAFE_ROLL = 20

@pytest.fixture(scope="session")
def df():
    import pandas as pd
    import pathlib
    p = pathlib.Path("data/processed/features_v1_static.parquet")
    if not p.exists():
        p = pathlib.Path("data/processed/features_v1.parquet")
    df = pd.read_parquet(p).sort_values(["ticker","date"]).reset_index(drop=True)
    df["date"] = pd.to_datetime(df["date"])
    return df

def test_label_definition_r1d(df):
    for tkr, g in df.groupby("ticker"):
        assert g["r_1d"].iloc[:-1].equals(g["log_return"].iloc[1:]), f"r_1d mismatch for {tkr}"

def _recompute_safe(g: pd.DataFrame) -> pd.DataFrame:
    # Recompute causal features using only <= t information
    out = pd.DataFrame(index=g.index)
    s = g["log_return"]
    out["lag1"] = s.shift(1)
    out["lag2"] = s.shift(2)
    out["lag3"] = s.shift(3)
    rm = s.rolling(SAFE_ROLL, min_periods=SAFE_ROLL).mean()
    rs = s.rolling(SAFE_ROLL, min_periods=SAFE_ROLL).std()
    out["roll_mean_20"] = rm
    out["roll_std_20"]  = rs
    out["zscore_20"]    = (s - rm) / (rs + 1e-8)
    # EWM & expanding if present
    out["exp_mean"] = s.expanding(min_periods=SAFE_ROLL).mean()
    out["exp_std"]  = s.expanding(min_periods=SAFE_ROLL).std()
    out["ewm_mean_20"] = s.ewm(span=20, adjust=False).mean()
    out["ewm_std_20"]  = s.ewm(span=20, adjust=False).std()
    # RSI(14) if adj_close present
    if "adj_close" in g:
        delta = g["adj_close"].diff()
        up = delta.clip(lower=0).ewm(alpha=1/14, adjust=False).mean()
        dn = (-delta.clip(upper=0)).ewm(alpha=1/14, adjust=False).mean()
        rs = up / (dn + 1e-12)
        out["rsi_14"] = 100 - (100/(1+rs))
    return out

@pytest.mark.parametrize("col", ["lag1","lag2","lag3","roll_mean_20","roll_std_20","zscore_20","exp_mean","exp_std","ewm_mean_20","ewm_std_20","rsi_14"])
def test_features_match_causal_recompute(df, col):
    if col not in df.columns:
        pytest.skip(f"{col} not present")
    # Compare per ticker to avoid cross-group alignment issues
    for tkr, g in df.groupby("ticker", sort=False):
        ref = _recompute_safe(g)
        if col not in ref.columns:
            continue
        a = g[col].to_numpy()
        b = ref[col].to_numpy()
        # Allow NaNs at the start; compare where both finite
        mask = np.isfinite(a) & np.isfinite(b)
        if mask.sum() == 0:
            continue
        diff = np.nanmax(np.abs(a[mask] - b[mask]))
        assert float(diff) <= 1e-6, f"{col} deviates from causal recompute for {tkr}: max |Δ|={diff}"

def test_no_feature_equals_target(df):
    y = df["r_1d"].to_numpy()
    for col in df.select_dtypes(include=["float32","float64"]).columns:
        if col in {"r_1d","log_return"}:
            continue
        x = df[col].to_numpy()
        # Proportion of exact equality (within tiny tol) should not be high
        eq = np.isfinite(x) & np.isfinite(y) & (np.abs(x - y) < 1e-12)
        assert eq.mean() < 0.8, f"Suspicious: feature {col} equals target too often"