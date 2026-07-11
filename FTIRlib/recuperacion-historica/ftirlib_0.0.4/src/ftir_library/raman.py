"""
Biomedical Raman Spectroscopy and Machine Learning Module
---------------------------------------------------------
Provides specialized preprocessors and ML classifiers for cell line classification.
"""

import numpy as np
from scipy.ndimage import median_filter

def _remove_cosmic_rays_1d(y, window=11, threshold=6.0):
    """Removes sharp cosmic ray spikes from a single 1D spectrum."""
    y_clean = np.copy(y)
    # Apply median filter to get the local trend
    y_med = median_filter(y_clean, size=window)
    diff = y_clean - y_med
    
    # Calculate Modified Z-Score based on Median Absolute Deviation (MAD)
    median_diff = np.median(diff)
    mad = np.median(np.abs(diff - median_diff))
    if mad < 1e-8:
        mad = 1e-8
    z_scores = 0.6745 * (diff - median_diff) / mad
    
    # Identify indices where the spike exceeds the threshold
    spikes = np.where(z_scores > threshold)[0]
    if len(spikes) == 0:
        return y_clean
        
    # Interpolate values of detected spikes using nearest non-spike neighbors
    n = len(y_clean)
    for idx in spikes:
        # Find nearest non-spike neighbor to the left
        left = idx - 1
        while left in spikes and left >= 0:
            left -= 1
        # Find nearest non-spike neighbor to the right
        right = idx + 1
        while right in spikes and right < n:
            right += 1
            
        if left >= 0 and right < n:
            y_clean[idx] = y_clean[left] + (y_clean[right] - y_clean[left]) * (idx - left) / (right - left)
        elif left >= 0:
            y_clean[idx] = y_clean[left]
        elif right < n:
            y_clean[idx] = y_clean[right]
            
    return y_clean

def remove_cosmic_rays(y, window=11, threshold=6.0):
    """
    Detects and filters cosmic ray spikes from 1D or 2D spectral arrays.
    
    Parameters:
        y (ndarray): 1D spectrum or 2D matrix of spectra.
        window (int): Size of the median filter window.
        threshold (float): Modified Z-Score threshold.
        
    Returns:
        ndarray: Filtered spectral array.
    """
    if len(y.shape) == 1:
        return _remove_cosmic_rays_1d(y, window, threshold)
    elif len(y.shape) == 2:
        y_clean = np.copy(y)
        for i in range(len(y)):
            y_clean[i] = _remove_cosmic_rays_1d(y[i], window, threshold)
        return y_clean
    return y

def _normalize_1d(y, method):
    """Applies normalization to a single 1D spectrum."""
    if method == 'vector':
        norm = np.linalg.norm(y)
        return y / norm if norm > 0 else y
    elif method == 'area':
        area = np.sum(y)
        return y / area if area > 0 else y
    elif method == 'snv':
        std = np.std(y)
        return (y - np.mean(y)) / std if std > 0 else y - np.mean(y)
    else:
        raise ValueError(f"Unknown normalization method: {method}")

def normalize_spectra(y, method='vector'):
    """
    Standardizes spectrum intensities using various normalization techniques.
    
    Parameters:
        y (ndarray): 1D spectrum or 2D matrix of spectra.
        method (str): 'vector' (L2 norm), 'area' (L1 integral), or 'snv' (Standard Normal Variate).
        
    Returns:
        ndarray: Normalized spectral array.
    """
    if len(y.shape) == 1:
        return _normalize_1d(y, method)
    elif len(y.shape) == 2:
        y_norm = np.copy(y)
        for i in range(len(y)):
            y_norm[i] = _normalize_1d(y[i], method)
        return y_norm
    return y

from .stats import NearestCentroidClassifier, KernelRidgeClassifier
