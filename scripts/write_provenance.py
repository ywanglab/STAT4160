# scripts/write_provenance.py
#!/usr/bin/env python
import json, pandas as pd
from pathlib import Path
Path("reports").mkdir(exist_ok=True)

provenance = []
if Path("data/static/sector_map.provenance.json").exists():
    provenance.append(json.loads(Path("data/static/sector_map.provenance.json").read_text()))
else:
    provenance.append({"source_url":"(none)","fetched_at_utc":"(n/a)"})

md = ["# Data provenance",
      "",
      "## Web sources",
      "",
      "| Source | Fetched at |",
      "|---|---|"]
for p in provenance:
    md.append(f"| {p['source_url']} | {p['fetched_at_utc']} |")

Path("reports/provenance.md").write_text("\n".join(md))
print("Wrote reports/provenance.md")