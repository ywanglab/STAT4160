import pandas as pd

def test_enriched_has_macro():
    df = pd.read_parquet("data/processed/features_v1_ext.parquet")
    assert "date" in df.columns and "ticker" in df.columns
    # At least one of the expected macro series is present
    assert df.filter(regex="^(VIXCLS|DGS10|FEDFUNDS)$").shape[1] >= 1
