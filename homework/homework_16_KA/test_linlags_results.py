# tests/test_linlags_results.py
import pandas as pd, os

def test_linlags_summary_exists_and_columns():
    assert os.path.exists("reports/linlags_summary.csv")
    df = pd.read_csv("reports/linlags_summary.csv")
    need = {"split","model","macro_mae","micro_mae"}
    assert need.issubset(df.columns)