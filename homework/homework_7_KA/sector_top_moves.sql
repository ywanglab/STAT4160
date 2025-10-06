-- sql/sector_top_moves.sql
SELECT m.sector, p.ticker, p.date, p.log_return, ABS(p.log_return) AS abs_move
FROM prices p JOIN meta m ON p.ticker = m.ticker
ORDER BY abs_move DESC
LIMIT 10;
