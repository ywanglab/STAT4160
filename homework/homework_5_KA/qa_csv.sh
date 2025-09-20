#!/usr/bin/env bash
# Simple CSV health check
# Usage: scripts/qa_csv.sh path/to/file.csv required_columns_csv
set -euo pipefail
IFS=$'\n\t'

FILE="${1:-}"
REQUIRED="${2:-ticker,date,adj_close,volume,log_return}"

err() { echo "ERROR: $*" >&2; exit 1; }
[[ -z "$FILE" ]] && err "No CSV file provided."
[[ ! -f "$FILE" ]] && err "File not found: $FILE"

# 1) Non-empty and header present
LINES=$(wc -l < "$FILE" || true)
[[ "${LINES:-0}" -lt 2 ]] && err "File has <2 lines (missing data?): $FILE"

HEADER=$(head -n 1 "$FILE")
# 2) All required columns present
IFS=',' read -r -a req <<< "$REQUIRED"
for col in "${req[@]}"; do
  echo "$HEADER" | grep -q -E "(^|,)${col}(,|$)" || err "Missing required column: $col"
done

# 3) No obvious NA/blank values in required numeric cols (basic check)
NUMERIC="adj_close,volume,log_return"
IFS=',' read -r -a nums <<< "$NUMERIC"
for col in "${nums[@]}"; do
  # find column index
  idx=$(awk -F, -v COL="$col" 'NR==1{for(i=1;i<=NF;i++) if($i==COL) print i}' "$FILE")
  [[ -z "${idx:-}" ]] && err "Column not found: $col"
  # check any blank values from row 2 onward
  bad=$(awk -F, -v I="$idx" 'NR>1 && ($I=="" || $I=="NA") {c++} END{print c+0}' "$FILE")
  [[ "$bad" -gt 0 ]] && err "Found $bad blank/NA in column: $col"
done

echo "OK: $FILE passed basic CSV QA ($LINES lines)."
