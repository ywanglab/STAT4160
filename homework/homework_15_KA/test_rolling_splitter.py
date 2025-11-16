# save to tests/test_rolling_splitter.py
import pandas as pd, numpy as np
from datetime import timedelta

def make_splits(dates, train_min, val_size, step, embargo):
    u = np.array(sorted(pd.to_datetime(dates.unique()))); n=len(u); out=[]; i=train_min-1
    while True:
        if i>=n: break
        a,b = u[0], u[i]; vs=i+embargo+1; ve=vs+val_size-1
        if ve>=n: break
        out.append((a,b,u[vs],u[ve])); i+=step
    return out

def test_embargo_and_order():
    dates = pd.bdate_range("2024-01-01", periods=400)
    s = make_splits(pd.Series(dates), 252, 63, 63, 5)
    assert all(b < c for (a,b,c,d) in s), "Embargo/order violated"
    # Splits should move forward
    assert len(s) >= 2 and s[1][1] > s[0][1]