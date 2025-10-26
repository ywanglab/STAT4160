# tests/test_dictionary_provenance.py
import os, pandas as pd
def test_provenance_and_dict():
    assert os.path.exists("reports/provenance.md")
    assert os.path.exists("reports/data_dictionary.csv")
    df = pd.read_csv("reports/data_dictionary.csv")
    assert {"dataset","column","dtype"}.issubset(df.columns)