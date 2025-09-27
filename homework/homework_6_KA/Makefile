# Makefile — unified-stocks
SHELL := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c
.ONESHELL:


PY := python
QUARTO := quarto

START ?= 2020-01-01
END   ?= 2025-08-01
ROLL  ?= 30

DATA_RAW := data/raw/prices.csv
FEATS    := data/processed/features.parquet
REPORT   := docs/reports/eda.html

# Default target
.DEFAULT_GOAL := help

.PHONY: help all clean clobber qa report backup

help: ## Show help for each target
	@awk 'BEGIN {FS = ":.*##"; printf "Available targets:\n"} /^[a-zA-Z0-9_\-]+:.*##/ {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# all: $(DATA_RAW) $(FEATS) report backup ## Run the full pipeline and back up artifacts
all: $(DATA_RAW) $(FEATS) report train backup

$(DATA_RAW): scripts/get_prices.py tickers_25.csv
	$(PY) scripts/get_prices.py --tickers tickers_25.csv --start $(START) --end $(END) --out $(DATA_RAW)

$(FEATS): scripts/build_features.py $(DATA_RAW) scripts/qa_csv.sh
	# Basic QA first
	scripts/qa_csv.sh $(DATA_RAW)
	$(PY) scripts/build_features.py --input $(DATA_RAW) --out $(FEATS) --roll $(ROLL)

# --- add after FEATS definition, near other targets ---

TRAIN_METRICS := reports/baseline_metrics.json

.PHONY: train
train: $(TRAIN_METRICS) ## Train toy baseline and write metrics

$(TRAIN_METRICS): scripts/train_baseline.py $(FEATS)
	$(PY) scripts/train_baseline.py --features $(FEATS) --out-metrics $(TRAIN_METRICS)

report: $(REPORT) ## Render Quarto EDA to docs1/
$(REPORT): reports/eda.qmd _quarto.yml docs1/style.css
	$(QUARTO) render reports/eda.qmd -P symbol:AAPL -P start_date=$(START) -P end_date=$(END) -P rolling=$(ROLL) --output-dir docs1/
	@test -f $(REPORT) || (echo "Report not generated." && exit 1)

backup: ## Rsync selected artifacts to backups/<timestamp>/
	./scripts/backup.sh

clean: ## Remove intermediate artifacts (safe)
	rm -rf data/interim
	rm -rf data/processed/*.parquet || true

clobber: clean ## Remove generated reports and backups (dangerous)
	rm -rf docs/reports || true
	rm -rf backups || true

DB := data/prices.db

.PHONY: db sql-report
db: ## Build/refresh SQLite database from CSVs
	python scripts/build_db.py --db $(DB) --tickers tickers_25.csv --prices data/raw/prices.csv

sql-report: db ## Generate a simple SQL-driven CSV summary
	$(PY) - <<-'PY'
	import pandas as pd, sqlite3, os
	con = sqlite3.connect("data/prices.db")
	df = pd.read_sql_query("""
	SELECT m.sector,
	       COUNT(*) AS n_obs,
	       AVG(ABS(p.log_return)) AS mean_abs_return
	FROM prices p
	JOIN meta m ON p.ticker = m.ticker
	GROUP BY m.sector
	ORDER BY n_obs DESC;
	""", con)
	os.makedirs("reports", exist_ok=True)
	df.to_csv("reports/sql_sector_summary.csv", index=False)
	print(df.head())
	con.close()
	PY

.PHONY: prices-parquet returns-parquet
prices-parquet:  ## Clean raw prices and save processed Parquet(s)
	python - <<'PY'
	import pandas as pd, glob, pathlib, numpy as np, re, json
	from pathlib import Path
	# (Paste the functions from the lab: standardize_columns, clean_prices, join_meta)
	# Then read raw -> clean -> write parquet as in the lab
	PY

returns-parquet: ## Build returns.parquet with r_1d + calendar features
	python - <<'PY'
	import pandas as pd, numpy as np
	p="data/processed/prices.parquet"; r=pd.read_parquet(p).sort_values(["ticker","date"])
	r["log_return"]=r.groupby("ticker")["adj_close"].apply(lambda s: np.log(s/s.shift(1))).reset_index(level=0, drop=True)
	r["r_1d"]=r.groupby("ticker")["log_return"].shift(-1)
	r["weekday"]=r["date"].dt.weekday.astype("int8"); r["month"]=r["date"].dt.month.astype("int8")
	r[["date","ticker","log_return","r_1d","weekday","month"]].to_parquet("data/processed/returns.parquet", compression="zstd", index=False)
	print("Wrote data/processed/returns.parquet")
	PY


# --- Training step (Part B) ---

TRAIN_METRICS := reports/baseline_metrics.json

.PHONY: train
train: $(TRAIN_METRICS) ## Train toy baseline and write metrics

$(TRAIN_METRICS): scripts/train_baseline.py $(FEATS)
	$(PY) scripts/train_baseline.py --features $(FEATS) --out-metrics $(TRAIN_METRICS)

