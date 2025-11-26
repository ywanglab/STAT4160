# save to tests/test_regime_thresholds.py
import json, pandas as pd

def test_thresholds_exist_and_train_range():
    data = json.load(open("reports/regime_thresholds.json"))
    assert len(data) >= 1
    # basic sanity: low < high
    for sid, rec in data.items():
        assert float(rec["lo"]) < float(rec["hi"])
        assert "→" in rec["train_range"]