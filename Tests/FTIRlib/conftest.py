import pytest
import numpy as np

@pytest.fixture
def synthetic_spectrum():
    """Generates a synthetic FTIR spectrum with wavenumbers and simulated transmittance/absorbance."""
    wavenumbers = np.linspace(4000, 400, 1000)
    # Background baseline trend + Gaussian peaks
    baseline = 0.1 * np.exp(-((wavenumbers - 2000) / 1000) ** 2)
    
    peak1 = 0.5 * np.exp(-((wavenumbers - 3400) / 50) ** 2)  # O-H band
    peak2 = 0.8 * np.exp(-((wavenumbers - 1700) / 30) ** 2)  # C=O band
    peak3 = 0.4 * np.exp(-((wavenumbers - 1050) / 40) ** 2)  # C-O band
    
    y_abs = baseline + peak1 + peak2 + peak3
    y_trans = 100.0 * np.exp(-y_abs)
    
    return wavenumbers, y_trans, y_abs
