# save to scripts/eval_linlags.py
#!/usr/bin/env python
from __future__ import annotations
import argparse, numpy as np, pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from pathlib import Path

def mae(y,yhat): return float(np.mean(np.abs(np.asarray(y)-np.asarray(yhat))))
def smape(y,yhat,eps=1e-8):
    y = np.asarray(y); yhat = np.asarray(yhat)
    return float(np.mean(2*np.abs(y-yhat)/(np.abs(y)+np.abs(yhat)+eps)))
def mase(y_true, y_pred, y_train_true, y_train_naive):
    return float(mae(y_true, y_pred) / (mae(y_train_true, y_train_naive)+1e-12))

def make_splits(dates, train_min, val_size, step, embargo):
    u = np.array(sorted(pd.to_datetime(pd.Series(dates).unique())))
    splits=[]; i=train_min-1; n=len(u)
    while True:
        if i>=n: break
        a,b = u[0], u[i]; vs=i+embargo+1; ve=vs+val_size-1
        if ve>=n: break
        splits.append((a,b,u[vs],u[ve])); i+=step
    return splits

def add_baselines(df, seasonality):
    out = df.copy()
    out["yhat_naive"] = out.groupby("ticker", observed = True)["log_return"].transform(lambda s: s)
    out["yhat_s"] = out.groupby("ticker", observed = True)["log_return"].transform(lambda s: s.shift(seasonality-1)) if seasonality>1 else out["yhat_naive"]
    return out

def fit_predict_lin(train_df, val_df, xcols):
    from sklearn.linear_model import LinearRegression
    from sklearn.preprocessing import StandardScaler
    from sklearn.pipeline import Pipeline
    preds=[]
    for tkr, tr in train_df.groupby("ticker"):
        va = val_df[val_df["ticker"]==tkr]
        if len(tr)==0 or len(va)==0: continue
        pipe = Pipeline([("scaler", StandardScaler()), ("lr", LinearRegression())])
        pipe.fit(tr[xcols].values, tr["r_1d"].values)
        yhat = pipe.predict(va[xcols].values)
        out = va[["date","ticker","r_1d","log_return"]].copy()
        out["yhat_linlags"] = yhat
        preds.append(out)
    return pd.concat(preds, ignore_index=True) if preds else pd.DataFrame()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--features", default="data/processed/features_v1.parquet")
    ap.add_argument("--seasonality", type=int, default=5)
    ap.add_argument("--train-min", type=int, default=252)
    ap.add_argument("--val-size", type=int, default=63)
    ap.add_argument("--step", type=int, default=63)
    ap.add_argument("--embargo", type=int, default=5)
    ap.add_argument("--xcols", nargs="+", default=["lag1","lag2","lag3"])
    ap.add_argument("--out-summary", default="reports/linlags_summary.csv")
    ap.add_argument("--out-per-ticker", default="reports/linlags_per_ticker_split{sid}.csv")
    # args = ap.parse_args() # notworking in Colab
    args, unknown = ap.parse_known_args() # fix
    print("Parsed args:", args)


    df = pd.read_parquet(args.features).sort_values(["ticker","date"]).reset_index(drop=True)
    df["ticker"] = df["ticker"].astype("category")
    splits = make_splits(df["date"], args.train_min, args.val_size, args.step, args.embargo)
    df = add_baselines(df, args.seasonality)

    rows=[]
    for sid, (a,b,c,d) in enumerate(splits, start=1):
        tr = df[(df["date"]>=a)&(df["date"]<=b)]
        va = df[(df["date"]>=c)&(df["date"]<=d)]
        val_pred = fit_predict_lin(tr, va, args.xcols)
        va = va.merge(val_pred[["date","ticker","yhat_linlags"]], on=["date","ticker"], how="left")
        # per-ticker
        pts=[]
        for tkr, gv in va.groupby("ticker"):
            gv = gv.dropna(subset=["r_1d","yhat_linlags"])
            if len(gv)==0: continue
            gt = tr[tr["ticker"]==tkr].dropna(subset=["r_1d"])
            gt_naive = gt["log_return"]  # scale comparator for MASE
            pts.append({"ticker":tkr,"n":int(len(gv)),
                        "mae": mae(gv["r_1d"], gv["yhat_linlags"]),
                        "smape": smape(gv["r_1d"], gv["yhat_linlags"]),
                        "mase": mase(gv["r_1d"], gv["yhat_linlags"], gt["r_1d"], gt_naive)})
        pt = pd.DataFrame(pts)
        Path("reports").mkdir(exist_ok=True)
        pt.assign(split=sid, model="lin_lags").to_csv(args.out_per_ticker.format(sid=sid), index=False)

        # aggregate
        if not pt.empty:
            macro = pt[["mae","smape","mase"]].mean().to_dict()
            w = pt["n"].to_numpy()
            micro = {"micro_mae": float(np.average(pt["mae"], weights=w)),
                     "micro_smape": float(np.average(pt["smape"], weights=w)),
                     "micro_mase": float(np.average(pt["mase"], weights=w))}
        else:
            macro = {"mae":np.nan,"smape":np.nan,"mase":np.nan}
            micro = {"micro_mae":np.nan,"micro_smape":np.nan,"micro_mase":np.nan}
        rows.append({"split":sid,"train_range":f"{a.date()}→{b.date()}","val_range":f"{c.date()}→{d.date()}",
                     "model":"lin_lags", "macro_mae":float(macro["mae"]), "macro_smape":float(macro["smape"]), "macro_mase":float(macro["mase"]),
                     **micro})

    pd.DataFrame(rows).to_csv(args.out_summary, index=False)
    print("Wrote", args.out_summary)

if __name__ == "__main__":
    main()