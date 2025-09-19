from __future__ import annotations
import sqlite3
import pandas as pd
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path("data/prices.db")

@contextmanager
def connect(db_path: str | Path = DB_PATH):
    con = sqlite3.connect(str(db_path))
    con.execute("PRAGMA foreign_keys = ON;")
    try:
        yield con
    finally:
        con.close()

def query_df(sql: str, params: tuple | list | None = None, db_path: str | Path = DB_PATH) -> pd.DataFrame:
    with connect(db_path) as con:
        return pd.read_sql_query(sql, con, params=params)

def sector_summary(start: str, end: str, db_path: str | Path = DB_PATH) -> pd.DataFrame:
    sql = '''
    SELECT m.sector, p.log_return
    FROM prices p JOIN meta m ON p.ticker = m.ticker
    WHERE p.date BETWEEN ? AND ?;
    '''
    df = query_df(sql, [start, end], db_path)
    if df.empty:
        return df
    g = df.assign(abs=lambda d: d["log_return"].abs()).groupby("sector")
    return g.agg(mean_abs_return=("abs","mean"),
                 mean_return=("log_return","mean"),
                 std_return=("log_return","std")).reset_index()
