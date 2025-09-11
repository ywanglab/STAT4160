# Makefile — unified-stocks
SHELL := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c

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
