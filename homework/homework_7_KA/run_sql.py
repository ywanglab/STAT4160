# scripts/run_sql.py
#!/usr/bin/env python
import argparse, sqlite3, pandas as pd
from pathlib import Path

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="data/prices.db")
    # ap.add_argument("--sqlfile", required=True)
    ap.add_argument("--sqlfile", default="sql/sector_top_moves.sql")
    ap.add_argument("--params", nargs="*", default=[])
    ap.add_argument("--out", default="")
    # args = ap.parse_args()
    args, _ = ap.parse_known_args()

    sql = Path(args.sqlfile).read_text()
    con = sqlite3.connect(args.db)
    df = pd.read_sql_query(sql, con, params=args.params or None)
    con.close()
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(args.out, index=False)
    print(df.head())

if __name__ == "__main__":
    main()