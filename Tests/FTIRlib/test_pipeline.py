import pytest
import numpy as np
import sys
import os

# Add FTIRlib to python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../FTIRlib')))

from ftir_library.pipeline import (
    preprocess_spectrum,
    detect_peaks_absorbance,
    detect_peaks_transmittance,
    assign_functional_groups,
    transmittance_to_absorbance
)

def test_transmittance_absorbance_conversion(synthetic_spectrum):
    wavenumbers, y_trans, y_abs = synthetic_spectrum
    
    # Convert T -> A
    calculated_abs = transmittance_to_absorbance(y_trans)
    
    assert len(calculated_abs) == len(y_trans)
    assert not np.isnan(calculated_abs).any()

def test_spectrum_preprocessing(synthetic_spectrum):
    wavenumbers, y_trans, y_abs = synthetic_spectrum
    
    x_proc, y_proc = preprocess_spectrum(
        wavenumbers, y_abs,
        smooth_label='savitzky_golay',
        base_label='airpls',
        space='absorbance'
    )
    
    assert len(x_proc) == len(wavenumbers)
    assert len(y_proc) == len(y_abs)
    assert not np.isnan(y_proc).any()

def test_peak_and_valley_detection(synthetic_spectrum):
    wavenumbers, y_trans, y_abs = synthetic_spectrum
    
    indices, peak_x, peak_y = detect_peaks_absorbance(wavenumbers, y_abs, prominence=0.01, distance=15)
    
    assert len(peak_x) >= 1

def test_functional_group_assignment(synthetic_spectrum):
    wavenumbers, y_trans, y_abs = synthetic_spectrum
    _, peak_x, _ = detect_peaks_absorbance(wavenumbers, y_abs, prominence=0.01, distance=15)
    
    matched, unmatched = assign_functional_groups(peak_x)
    assert isinstance(matched, dict)
