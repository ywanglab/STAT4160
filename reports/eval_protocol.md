# Evaluation Protocol (Leakage-Aware)

**Date:** 2025-12-01

## Splits

- Train window (split 1): **2020-01-01 → 2020-05-19**
- Embargo: **5** business days
- Validation window: **2020-05-22 → 2020-06-18**
- Step between origins: **63** business days

## Static Universe

- Universe file: **universe_2020-04-21.csv**
- Count: **25** tickers
- Rule: tickers with ≥252 obs by first train end; fixed universe.

## Labels

- `r_1d` = next-day log return (`log_return.shift(-1)` per ticker).
- `r_5d` (if used) = sum of future 5 daily log returns.

## Leakage Controls

- Features computed only with past values (≤ t).
- No cross-split forward fill; uses 5-day embargo.
- Scaler/normalizer fitted on TRAIN only.
- Verified by `test_leakage_features.py` and `test_labels_multistep.py`.

## Caveats

- Educational dataset — not investment advice.
- Possible hidden leakage from macro revisions or vendor quirks.
