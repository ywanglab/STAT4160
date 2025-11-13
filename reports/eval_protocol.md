# Evaluation Protocol (Leakage‑Aware)

**Date:** 2025-11-09

## Splits
- Train window (split 1): **2020-01-01 → 2020-04-21**
- Embargo: **5** business days
- Validation window: **2020-04-29 → 2020-05-27**
- Step between origins: **63** business days

## Static Universe
- Universe file: **universe_2020-04-21.csv**
- Count: **25** tickers
- Selection rule: tickers with ≥252 obs by first train end; fixed for all splits.

## Labels
- `r_1d` = next‑day log return `log_return.shift(-1)` per ticker.
- `r_5d` (if used) = sum of `log_return.shift(-1..-5)`.

## Leakage Controls
- Features computed from ≤ t only (rolling/ewm/expanding without negative shifts).
- No forward‑fill across split boundaries; embargo = 5 days.
- Scalers/normalizers fit on TRAIN only.
- Tests: `tests/test_leakage_features.py`, `tests/test_labels_multistep.py`.

## Caveats
- Educational dataset; not investment advice.
- Survivorship minimized via static universe; still subject to data vendor quirks.
