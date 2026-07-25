import os
import numpy as np
import pytest
from ftir_library.core import (
    load_ftir_data,
    load_jcamp_dx,
    moving_average,
    savitzky_golay,
    median_filter,
    percentile_filter,
    correct_baseline_transmittance,
    correct_baseline_absorbance,
    transmittance_to_absorbance
)

# Test data files path
DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "examples"))
JDX_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "muestras jdx"))

def test_load_ftir_data():
    file_path = os.path.join(DATA_DIR, "GO coque s lav ox.txt")
    if os.path.exists(file_path):
        x, y = load_ftir_data(file_path)
        assert len(x) > 0
        assert len(y) == len(x)
        assert isinstance(x, np.ndarray)
        assert isinstance(y, np.ndarray)

def test_load_jcamp_dx():
    file_path = os.path.join(JDX_DIR, "ethanol-64-17-5-IR.jdx")
    if os.path.exists(file_path):
        x, y = load_jcamp_dx(file_path)
        assert len(x) > 0
        assert len(y) == len(x)
        # Check that it converted fraction transmittance to percent transmittance [0, 100]
        assert np.max(y) > 2.0
        assert np.max(y) <= 100.0

def test_filters():
    y = np.array([1.0, 2.0, 3.0, 2.0, 1.0, 10.0, 1.0])
    
    # Moving average
    ma = moving_average(y, window=3)
    assert len(ma) == len(y)
    
    # Savitzky Golay
    sg = savitzky_golay(y, window=5, poly=2)
    assert len(sg) == len(y)
    
    # Median
    med = median_filter(y, window=3)
    assert len(med) == len(y)
    
    # Percentile
    pct = percentile_filter(y, window=3, percentile=50)
    assert len(pct) == len(y)

def test_transmittance_to_absorbance():
    t = np.array([100.0, 10.0, 1.0])
    a = transmittance_to_absorbance(t)
    # A = 2 - log10(T)
    # A(100) = 0, A(10) = 1, A(1) = 2
    assert np.allclose(a, [0.0, 1.0, 2.0], atol=1e-5)

def test_baseline_transmittance():
    x = np.linspace(400, 4000, 100)
    y = np.ones_like(x) * 90.0
    
    # Detrend
    z, corr = correct_baseline_transmittance(x, y, method='detrend')
    assert len(z) == len(y)
    assert len(corr) == len(y)
    
    # RAW/NONE
    z_raw, corr_raw = correct_baseline_transmittance(x, y, method='RAW')
    assert np.allclose(z_raw, 100.0)
    assert np.allclose(corr_raw, y)

def test_baseline_absorbance():
    x = np.linspace(400, 4000, 100)
    y = np.ones_like(x) * 0.5
    
    # airPLS
    z, corr = correct_baseline_absorbance(x, y, method='airpls', lam=1e3)
    assert len(z) == len(y)
    assert len(corr) == len(y)
    
    # RAW/NONE
    z_raw, corr_raw = correct_baseline_absorbance(x, y, method='NONE')
    assert np.allclose(z_raw, 0.0)
    assert np.allclose(corr_raw, y)
