#!/usr/bin/env bash
# Sync selected artifacts to backups/<timestamp> using rsync.
# Usage: scripts/backup.sh [DEST_ROOT]
set -euo pipefail
ROOT="${1:-backups}"
STAMP="$(date +%Y%m%d-%H%M%S)"
DEST="${ROOT}/run-${STAMP}"
mkdir -p "$DEST"

# What to back up (adjust as needed)
INCLUDE=("data/processed" "reports" "docs")

for src in "${INCLUDE[@]}"; do
  if [[ -d "$src" ]]; then
    echo "Syncing $src -> $DEST/$src"
    rsync -avh --delete --exclude 'raw/' --exclude 'interim/' "$src"/ "$DEST/$src"/
  fi
done

echo "Backup complete at $DEST"
