#!/usr/bin/env python
from __future__ import annotations
import argparse, numpy as np, pandas as pd
from pathlib import Path

def mae(y,yhat): return float(np.mean(np.abs(np.asarray(y)-np.asarray(yhat))))
def smape(y,yhat,eps=1e-8):
    y = np.asarray(y); yhat = np.asarray(yhat)
    return float(np.mean(2*np.abs(y-yhat)/(np.abs(y)+np.abs(yhat)+eps)))
def mase(y_true, y_pred, y_train_true, y_train_naive):
    return float(mae(y_true, y_pred) / (mae(y_train_true, y_train_naive)+1e-12))

def make_splits(dates, train_min, val_size, step, embargo):
    u = np.array(sorted(pd.to_datetime(dates.unique()))); n=len(u); out=[]; i=train_min-1
    while True:
        if i>=n: break
        a,b = u[0], u[i]; vs = i + embargo + 1; ve = vs + val_size - 1
        if ve>=n: break
        out.append((a,b,u[vs],u[ve])); i += step
    return out

def add_preds(df, s):
    out = df.copy()
    out["yhat_naive"] = out.groupby("ticker")["log_return"].transform(lambda x: x)
    out["yhat_s"] = out.groupby("ticker")["log_return"].transform(lambda x: x.shift(s-1)) if s>1 else out["yhat_naive"]
    return out

def per_ticker(df_val, df_train, method, s):
    col = "yhat_naive" if method=="naive" else "yhat_s"
    rows=[]
    for tkr, g in df_val.groupby("ticker"):
        gv = g.dropna(subset=["r_1d", col])
        if len(gv)==0: continue
        gt = df_train[df_train["ticker"]==tkr].dropna(subset=["r_1d"])
        gt_pred = gt["log_return"] if method=="naive" else gt["log_return"].shift(s-1)
        gt_pred = gt_pred.loc[gt.index]
        y_tr = gt["r_1d"].to_numpy(); yhat_tr = gt_pred.to_numpy()
        y = gv["r_1d"].to_numpy(); yhat = gv[col].to_numpy()
        rows.append({"ticker":tkr,"n":int(len(y)),
                     "mae": mae(y,yhat),
                     "smape": smape(y,yhat),
                     "mase": mase(y,yhat,y_tr,yhat_tr)})
    return pd.DataFrame(rows)

def agg(pt):
    if pt.empty: return {"macro_mae":np.nan,"macro_smape":np.nan,"macro_mase":np.nan,
                         "micro_mae":np.nan,"micro_smape":np.nan,"micro_mase":np.nan}
    macro = pt[["mae","smape","mase"]].mean().to_dict()
    w = pt["n"].to_numpy()
    micro = {
        "micro_mae": float(np.average(pt["mae"], weights=w)),
        "micro_smape": float(np.average(pt["smape"], weights=w)),
        "micro_mase": float(np.average(pt["mase"], weights=w)),
    }
    return {f"macro_{k}": float(v) for k,v in macro.items()} | micro

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--returns", default="data/processed/returns.parquet")
    ap.add_argument("--seasonality", type=int, default=5)
    ap.add_argument("--train-min", type=int, default=252)
    ap.add_argument("--val-size", type=int, default=63)
    ap.add_argument("--step", type=int, default=63)
    ap.add_argument("--embargo", type=int, default=5)
    ap.add_argument("--out-summary", default="reports/baselines_rollingorigin_summary.csv")
    ap.add_argument("--out-per-ticker", default="reports/baselines_per_ticker_split{sid}_{method}.csv")
    args, _ = ap.parse_known_args()

    df = pd.read_parquet(args.returns).sort_values(["ticker","date"]).reset_index(drop=True)
    splits = make_splits(df["date"], args.train_min, args.val_size, args.step, args.embargo)
    pred = add_preds(df, args.seasonality)

    rows=[]
    for sid, (a,b,c,d) in enumerate(splits, start=1):
        tr = pred[(pred["date"]>=a)&(pred["date"]<=b)]
        va = pred[(pred["date"]>=c)&(pred["date"]<=d)]
        for method in ["naive","s"]:
            pt = per_ticker(va, tr, method, args.seasonality)
            Path("reports").mkdir(exist_ok=True)
            pt.to_csv(args.out_per_ticker.format(sid=sid, method=method), index=False)
            rows.append({"split":sid,"train_range":f"{a.date()}→{b.date()}","val_range":f"{c.date()}→{d.date()}",
                         "method":"naive" if method=="naive" else f"s{args.seasonality}", **agg(pt)})
    pd.DataFrame(rows).to_csv(args.out_summary, index=False)
    print("Wrote", args.out_summary, "and per-ticker CSVs.")

if __name__ == "__main__":
    main()
