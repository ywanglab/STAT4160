# tests/conftest.py
import sys, pathlib


# Add the project root (the parent of "tests/") to sys.path
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

# sys.path.append(str("/content/drive/MyDrive/dspt25/STAT4160"))
