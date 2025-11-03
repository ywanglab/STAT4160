# save to tests/test_health_outputs.py
import os, json

def test_health_files_exist():
    assert os.path.exists("reports/health.json")
    assert os.path.exists("reports/health.md")
    # json is valid
    import json
    json.load(open("reports/health.json"))