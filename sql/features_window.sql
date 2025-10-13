-- sql/features_window.sql
WITH base AS (
  SELECT
    ticker, date, log_return AS r_1d
  FROM prices
  WHERE date BETWEEN ? AND ?
)
SELECT
  ticker, date, r_1d,
  LAG(r_1d,1) OVER (PARTITION BY ticker ORDER BY date) AS lag1,
  LAG(r_1d,2) OVER (PARTITION BY ticker ORDER BY date) AS lag2,
  LAG(r_1d,3) OVER (PARTITION BY ticker ORDER BY date) AS lag3,
  AVG(r_1d) OVER w20 AS roll_mean_20,
  AVG(r_1d*r_1d) OVER w20 - (AVG(r_1d) OVER w20)*(AVG(r_1d) OVER w20) AS roll_var_20
FROM base
WINDOW w20 AS (
  PARTITION BY ticker
  ORDER BY date
  ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
)
ORDER BY ticker, date;
