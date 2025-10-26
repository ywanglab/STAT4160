# scripts/data_dictionary.py
#!/usr/bin/env python
import pandas as pd
from pathlib import Path

def describe_parquet(path):
    df = pd.read_parquet(path)
    dtypes = df.dtypes.astype(str).to_dict()
    return pd.DataFrame({"column": list(dtypes.keys()), "dtype": list(dtypes.values())})

def main():
    rows=[]
    for path in ["data/processed/prices.parquet",
                 "data/processed/returns.parquet",
                 "data/processed/features_v1.parquet",
                 "data/processed/features_v1_ext.parquet"]:
        p = Path(path)
        if p.exists():
            df = describe_parquet(p)
            df.insert(0, "dataset", p.name) # insert a new col as the first col
            rows.append(df)
    out = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame(columns=["dataset","column","dtype"])
    Path("reports").mkdir(exist_ok=True)
    out.to_csv("reports/data_dictionary.csv", index=False)
    print("Wrote reports/data_dictionary.csv")

if __name__ == "__main__":
    main()