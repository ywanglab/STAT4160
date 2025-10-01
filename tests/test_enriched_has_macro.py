import pandas as pd
def test_enriched_has_macro():
    df = pd.read_parquet("data/processed/features_v1_ext.parquet")
    assert "date" in df and "ticker" in df
    assert df.filter(regex="^(VIXCLS|DGS10|FEDFUNDS)$").shape[1] >= 1