guard:
	python tools/guard_large_files.py
report:
	quarto render reports/eda.qmd --output-dir docs/

reports-trio:
	quarto render reports/eda-AAPL.qmd -P symbol:AAPL -P start_date:2018-01-01 -P end_date:2025-08-01 --output-dir docs/
	quarto render reports/eda-MSFT.qmd -P symbol:MSFT -P start_date:2018-01-01 -P end_date:2025-08-01 --output-dir docs/
	quarto render reports/eda-NVDA.qmd -P symbol:NVDA -P start_date:2018-01-01 -P end_date:2025-08-01 --output-dir docs/"
qa:
	# TAB above!
	scripts/qa_csv.sh data/raw/prices.csv

split-by-ticker:
	@bash -c 'HEADER=$$(head -n 1 data/raw/prices.csv); \
	  cut -d, -f1 data/raw/prices.csv | tail -n +2 | sort -u | \
	  while read -r T; do \
	    mkdir -p data/interim/ticker=$$T; \
	    { echo "$$HEADER"; \
	      awk -F, -v TK="$$T" '"'"'NR>1 && $$1==TK'"'"' data/raw/prices.csv; \
	    } > data/interim/ticker=$$T/prices_$$T.csv; \
	  done'

