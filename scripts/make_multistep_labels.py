# save to scripts/make_multistep_labels.py
from __future__ import annotations
import pandas as pd, numpy as np
from pathlib import Path

def make_multistep(in_parquet="data/processed/returns.parquet", horizons=(5,)):
    df = pd.read_parquet(in_parquet).sort_values(["ticker","date"]).reset_index(drop=True)
    for H in horizons:
        # r_Hd = sum of next H log returns: shift(-1) ... shift(-H): accumulative log return over H days
        s = df.groupby("ticker")["log_return"]
        acc = None  # initialize an accumulator 
        for h in range(1, H+1):
            sh = s.shift(-h)
            acc = sh if acc is None else (acc + sh)  # accumulative 
        df[f"r_{H}d"] = acc
    out = df
    Path("data/processed").mkdir(parents=True, exist_ok=True)
    out.to_parquet("data/processed/returns_multistep.parquet", compression="zstd", index=False)
    print("Wrote data/processed/returns_multistep.parquet", out.shape)

if __name__ == "__main__":
    make_multistep()