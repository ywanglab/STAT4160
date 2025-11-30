# save to tests/test_logging.py
import logging, pandas as pd, numpy as np, pytest
from scripts.logsetup import setup_logging

def check_for_duplicates(df, logger=None):
    logger = logger or setup_logging("dspt")
    dups = df[["ticker","date"]].duplicated().sum()
    if dups > 0:
        logger.warning("Found %d duplicate (ticker,date) rows", dups)
    return dups

def test_duplicate_warning(caplog):
    caplog.set_level(logging.WARNING)
    df = pd.DataFrame({"ticker":["AAPL","AAPL"], "date":pd.to_datetime(["2024-01-02","2024-01-02"])})
    dups = check_for_duplicates(df)
    assert dups == 1
    assert any("duplicate" in rec.message for rec in caplog.records)