# save to tests/test_labels_multistep.py
import pandas as pd, numpy as np

def test_r5d_definition():
    df = pd.read_parquet("data/processed/returns_multistep.parquet").sort_values(["ticker","date"])
    if "r_5d" not in df.columns:
        return
    for tkr, g in df.groupby("ticker"):
        lr = g["log_return"]
        r5 = sum(lr.shift(-h) for h in range(1,6))
        diff = (g["r_5d"] - r5).abs().max()
        assert float(diff) < 1e-10, f"r_5d misdefined for {tkr} (max |Δ|={diff})"