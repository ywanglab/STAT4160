import pandas as pd, numpy as np

def test_features_no_lookahead():
    df = pd.read_parquet("data/processed/features_v1.parquet").sort_values(["ticker","date"])
    # For each ticker, recompute roll_mean_20 with an independent method and compare
    for tkr, g in df.groupby("ticker"):
        s = g["log_return"]
        rm = s.rolling(20, min_periods=20).mean()
        # Our feature should equal this rolling mean (within tol)
        if "roll_mean_20" in g:
            assert np.allclose(g["roll_mean_20"].values, rm.values, equal_nan=True, atol=1e-7)
        # r_1d must be the **lead** of log_return
        assert g["r_1d"].shift(1).iloc[21:].equals(g["log_return"].iloc[21:])