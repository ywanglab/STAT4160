# tests/test_mathy.py
import pytest
# import sys, pathlib
# sys.path.append(str(pathlib.Path.cwd() / "src"))

from src.mathy import moving_avg


def test_moving_avg_basic():
    assert moving_avg([1,2,3,4], 2) == [1, 1.5, 2.5, 3.5]

def test_moving_avg_bad_window():
    with pytest.raises(ValueError):
        moving_avg([1,2,3], 0)
