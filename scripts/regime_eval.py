# save to scripts/regime_eval.py
#!/usr/bin/env python
from __future__ import annotations
import argparse, json, numpy as np, pandas as pd
from pathlib import Path
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression

import warnings
warnings.filterwarnings('ignore')

def make_splits(dates, train_min=252, val_size=63, step=63, embargo=5):
    u = np.array(sorted(pd.to_datetime(pd.Series(dates).unique())))
    splits=[]; i=train_min-1; n=len(u)
    while True:
        if i>=n: break
        a,b = u[0], u[i]; vs=i+embargo+1; ve=vs+val_size-1
        if ve>=n: break
        splits.append((a,b,u[vs],u[ve])); i+=step
    return splits

def regime_thresholds(train_df, vol_col="roll_std_20", q_low=0.33, q_high=0.66):
    v = train_df[vol_col].dropna().to_numpy()
    if len(v) < 100:
        q_low, q_high = 0.4, 0.8
    return float(np.quantile(v, q_low)), float(np.quantile(v, q_high))

def label_regime(df, vol_col, lo, hi):
    out = df.copy()
    vc = out[vol_col]
    reg = pd.Series(pd.Categorical(["unknown"]*len(out), categories=["low","med","high","unknown"]), index=out.index)
    reg[(vc.notna()) & (vc <= lo)] = "low"
    reg[(vc.notna()) & (vc > lo) & (vc < hi)] = "med"
    reg[(vc.notna()) & (vc >= hi)] = "high"
    out["regime"] = reg.astype("category")
    return out

def add_naive(df):
    out = df.copy()
    out["yhat_naive"] = out["log_return"]
    return out

def fit_lin(tr, va, xcols):
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler
    from sklearn.linear_model import LinearRegression
    preds=[]
    for tkr, trk in tr.groupby("ticker"):
        vak = va[va["ticker"]==tkr]
        if len(trk)==0 or len(vak)==0: continue
        Xtr = trk.dropna(subset=xcols); 
        pipe = Pipeline([("scaler", StandardScaler()), ("lr", LinearRegression())])
        pipe.fit(Xtr[xcols].values, Xtr["r_1d"].values)
        yhat = pipe.predict(vak[xcols].fillna(0).values)
        out = vak[["date","ticker","r_1d","log_return","regime"]].copy()
        out["yhat_lin"] = yhat
        preds.append(out)
    return pd.concat(preds, ignore_index=True) if preds else pd.DataFrame()

def mae(y, yhat): y=np.asarray(y); yhat=np.asarray(yhat); return float(np.mean(np.abs(y-yhat)))
def smape(y,yhat,eps=1e-8):
    y=np.asarray(y); yhat=np.asarray(yhat); return float(np.mean(2*np.abs(y-yhat)/(np.abs(y)+np.abs(yhat)+eps)))
def mase(y_true, y_pred, y_train_true, y_train_naive):
    return float(mae(y_true, y_pred)/(mae(y_train_true, y_train_naive)+1e-12))

def per_regime_metrics(val_df, train_df, pred_col):
    rows = []

    # Pre-group training by ticker once (faster)
    train_by_ticker = {
        tkr: g.dropna(subset=["r_1d"])
        for tkr, g in train_df.groupby("ticker")
    }

    for reg, g in val_df.groupby("regime"):
        if reg == "unknown" or len(g) == 0:
            continue

        per_t = []
        for tkr, gv in g.groupby("ticker"):
            gt = train_by_ticker.get(tkr)
            if gt is None or gt.empty:
                continue

            # Align & drop NaNs in y / yhat
            y = gv["r_1d"]
            yhat = gv[pred_col]
            mask = y.notna() & yhat.notna()
            if not mask.any():
                continue

            y = y[mask]
            yhat = yhat[mask]

            # If mase needs clean scaling inputs, align/drop there too
            m = {
                "ticker": tkr,
                "n": int(mask.sum()),
                "mae": float(mae(y, yhat)),
                "smape": float(smape(y, yhat)),
                "mase": float(mase(y, yhat, gt["r_1d"], gt["log_return"])),
                "regime": reg,
            }
            per_t.append(m) # per_t is a list of dict of the same structure

        per_t = pd.DataFrame(per_t) # convert a list of dict into a dataframe
        if per_t.empty:
            continue

        macro = per_t[["mae", "smape", "mase"]].mean().to_dict()

        w = per_t["n"].to_numpy()
        wsum = w.sum()
        if wsum == 0:
            # fall back to macro if no weights
            micro = {
                "micro_mae": float(per_t["mae"].mean()),
                "micro_smape": float(per_t["smape"].mean()),
                "micro_mase": float(per_t["mase"].mean()),
            }
        else:
            micro = {
                "micro_mae": float(np.average(per_t["mae"], weights=w)),
                "micro_smape": float(np.average(per_t["smape"], weights=w)),
                "micro_mase": float(np.average(per_t["mase"], weights=w)),
            }

        rows.append({ # build a new dict by adding new fields.
            "regime": reg,
            **{f"macro_{k}": float(v) for k, v in macro.items()},
            **micro # unpacking an existing dict into key-value pairs inline
        })

    return pd.DataFrame(rows)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--features", default="data/processed/features_v1.parquet")
    ap.add_argument("--train-min", type=int, default=80)
    ap.add_argument("--val-size", type=int, default=21)
    ap.add_argument("--step", type=int, default=21)
    ap.add_argument("--embargo", type=int, default=5)
    ap.add_argument("--vol-col", default="roll_std_20")
    ap.add_argument("--xcols", nargs="+", default=["lag1","lag2","lag3"])
    ap.add_argument("--out-summary", default="reports/regime_summary.csv")
    # args = ap.parse_args(). # not working in Colab
    args, unknown = ap.parse_known_args() # fix
    print("Parsed args:", args)

    df = pd.read_parquet(args.features).sort_values(["ticker","date"]).reset_index(drop=True)
    # Ensure vol col exists
    if args.vol_col not in df.columns:
        df[args.vol_col] = df.groupby("ticker")["log_return"].rolling(20, min_periods=20).std().reset_index(level=0, drop=True)

    # Build lags if missing
    for k in [1,2,3]:
        col = f"lag{k}"
        if col not in df.columns:
            df[col] = df.groupby("ticker")["log_return"].shift(k)

    splits = make_splits(df["date"], args.train_min, args.val_size, args.step, args.embargo)
    Path("reports").mkdir(parents=True, exist_ok=True)
    thresh_rec = {}

    rows=[]
    for sid,(a,b,c,d) in enumerate(splits, start=1):
        tr = df[(df["date"]>=a)&(df["date"]<=b)]
        va = df[(df["date"]>=c)&(df["date"]<=d)]
        lo, hi = regime_thresholds(tr, args.vol_col)
        thresh_rec[sid] = {"lo":lo, "hi":hi, "train_range":f"{a.date()}→{b.date()}"}
        trL = label_regime(tr, args.vol_col, lo, hi)
        vaL = label_regime(va, args.vol_col, lo, hi)

        # predictions
        trN, vaN = add_naive(trL), add_naive(vaL)
        val_lin = fit_lin(trN, vaN, args.xcols)
        vaN = vaN.merge(val_lin[["date","ticker","yhat_lin"]], on=["date","ticker"], how="left")

        # metrics
        m_naive = per_regime_metrics(vaN, trN, "yhat_naive").assign(split=sid, model="naive") # .assign(): add two columns: split, model. See below for more
        m_lin   = per_regime_metrics(vaN.dropna(subset=["yhat_lin"]), trN, "yhat_lin").assign(split=sid, model="lin_lags")

        out = pd.concat([m_naive, m_lin], ignore_index=True)
        out.to_csv(f"reports/regime_metrics_split{sid}.csv", index=False)
        rows.append(out)

    pd.concat(rows, ignore_index=True).to_csv(args.out_summary, index=False)
    Path("reports/regime_thresholds.json").write_text(json.dumps(thresh_rec, indent=2))
    print("Wrote", args.out_summary, "and per-split CSVs; thresholds saved to reports/regime_thresholds.json")

if __name__ == "__main__":
    main()