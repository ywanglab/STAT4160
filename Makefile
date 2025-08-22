

guard:
	python tools/guard_large_files.py
report:
	quarto render reports/eda.qmd --output-dir docs/

reports-trio:
	quarto render reports/eda-AAPL.qmd -P symbol:AAPL -P start_date:2018-01-01 -P end_date:2025-08-01 --output-dir docs/
	quarto render reports/eda-MSFT.qmd -P symbol:MSFT -P start_date:2018-01-01 -P end_date:2025-08-01 --output-dir docs/
	quarto render reports/eda-NVDA.qmd -P symbol:NVDA -P start_date:2018-01-01 -P end_date:2025-08-01 --output-dir docs/"
