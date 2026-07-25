import pytest
import numpy as np
import tempfile
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../FTIRlib')))

from ftir_library.pipeline import load_data, FTIR

def test_load_data_txt():
    # Create temporary .txt file
    with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.txt') as tmp:
        tmp.write("4000.0\t95.0\n")
        tmp.write("3500.0\t80.0\n")
        tmp.write("3000.0\t70.0\n")
        tmp_filename = tmp.name

    try:
        x, y = load_data(tmp_filename, FTIR)
        assert len(x) == 3
        assert len(y) == 3
        assert x[0] == 4000.0
        assert y[0] == 95.0
    finally:
        if os.path.exists(tmp_filename):
            os.remove(tmp_filename)
