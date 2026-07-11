"""
FTIR Core Processing Library
----------------------------
This module provides classes and functions for loading, smoothing, baseline-correcting,
detecting peaks, and assigning functional groups for FTIR spectra.
"""

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import spsolve
from scipy.signal import savgol_filter, medfilt, find_peaks
import scipy.ndimage


def load_ftir_data(filepath):
    """
    Loads FTIR data from a file.
    Supports space/tab/comma-separated files, ignoring lines starting with '#' or non-numeric headers.
    Tries UTF-8 first, falling back to Latin-1 if decode fails.
    
    Returns:
        wavenumbers (np.ndarray): Wavenumber values (cm^-1)
        transmittance (np.ndarray): Transmittance values (%T)
    """
    wavenumbers = []
    transmittance = []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except UnicodeDecodeError:
        with open(filepath, 'r', encoding='latin-1') as f:
            lines = f.readlines()
            
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#') or line.startswith('##'):
            continue
        if ',' in line:
            parts = line.split(',')
        else:
            parts = line.split()
        if len(parts) >= 2:
            try:
                w = float(parts[0].strip())
                t = float(parts[1].strip())
                wavenumbers.append(w)
                transmittance.append(t)
            except ValueError:
                # Ignore header or non-numeric lines
                continue
                
    return np.array(wavenumbers), np.array(transmittance)


def load_jcamp_dx(filepath):
    """
    Loads spectral data from a JCAMP-DX (.jdx or .dx) file.
    Supports standard XYDATA in (X++(Y..Y)) and (XY..XY) format.
    
    Returns:
        wavenumbers (np.ndarray): Wavenumber values (cm^-1)
        intensities (np.ndarray): Transmittance (%T) or Absorbance (u.a.) values
    """
    metadata = {}
    x_data = []
    y_data = []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except UnicodeDecodeError:
        with open(filepath, 'r', encoding='latin-1') as f:
            lines = f.readlines()
            
    in_data = False
    x_factor = 1.0
    y_factor = 1.0
    first_x = None
    last_x = None
    n_points = None
    format_type = ""
    
    all_y_values = []
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('$$'):
            continue
            
        if line.startswith('##'):
            parts = line[2:].split('=', 1)
            if len(parts) == 2:
                key = parts[0].strip().upper()
                val = parts[1].strip()
                metadata[key] = val
                
                if key == 'XFACTOR':
                    x_factor = float(val)
                elif key == 'YFACTOR':
                    y_factor = float(val)
                elif key == 'FIRSTX':
                    first_x = float(val)
                elif key == 'LASTX':
                    last_x = float(val)
                elif key == 'NPOINTS':
                    n_points = int(val)
                elif key in ('XYDATA', 'XYPOINTS', 'PEAK TABLE'):
                    in_data = True
                    format_type = val
                elif key == 'END':
                    in_data = False
            continue
            
        if in_data:
            clean_line = line.split('$$')[0].strip()
            if not clean_line:
                continue
            # Replace commas (CSV format) with space
            tokens = clean_line.replace(',', ' ').split()
            if not tokens:
                continue
                
            try:
                nums = [float(t) for t in tokens]
            except ValueError:
                # Ignore lines that cannot be parsed as floats (e.g. compressed formats fallback)
                continue
                
            if '(XY..XY)' in format_type or 'PEAK TABLE' in format_type or 'PEAKLIST' in format_type:
                # Pairs of X and Y
                for i in range(0, len(nums), 2):
                    if i + 1 < len(nums):
                        x_data.append(nums[i] * x_factor)
                        y_data.append(nums[i+1] * y_factor)
            else:
                # Standard (X++(Y..Y)) format
                # First token is the line's starting X coordinate
                # The remaining tokens are Y values
                for y_val in nums[1:]:
                    all_y_values.append(y_val)
                    
    # Reconstruct coordinate arrays
    if all_y_values:
        n = len(all_y_values)
        fx = first_x if first_x is not None else 0.0
        lx = last_x if last_x is not None else (n - 1)
        x_data = np.linspace(fx * x_factor, lx * x_factor, n)
        y_data = np.array(all_y_values) * y_factor
    else:
        x_data = np.array(x_data)
        y_data = np.array(y_data)
        
    # Standardize Y if it's transmittance in fraction [0, 1] instead of percentage [0, 100]
    y_units = metadata.get('YUNITS', '').strip().upper()
    if 'TRANSMITTANCE' in y_units:
        if len(y_data) > 0 and np.max(y_data) <= 2.0:
            y_data = y_data * 100.0
            
    return x_data, y_data


# ==========================================
# 1. SMOOTHING ALGORITHMS
# ==========================================

def moving_average(y, window=5):
    """
    Applies a moving average filter.
    Handles boundaries by padding with edge values.
    """
    if window < 2:
        return y.copy()
    pad_width = window // 2
    padded_y = np.pad(y, pad_width, mode='edge')
    kernel = np.ones(window) / window
    # Valid convolution returns the same size as y after padding
    smoothed = np.convolve(padded_y, kernel, mode='valid')
    # If window is even, convolve result might be off by 1, handle it
    if len(smoothed) < len(y):
        smoothed = np.pad(smoothed, (0, len(y) - len(smoothed)), mode='edge')
    elif len(smoothed) > len(y):
        smoothed = smoothed[:len(y)]
    return smoothed


def savitzky_golay(y, window=11, poly=2):
    """
    Applies a Savitzky-Golay filter.
    Window must be odd and greater than poly.
    """
    # Ensure window is odd
    if window % 2 == 0:
        window += 1
    # Ensure window is greater than poly
    if window <= poly:
        window = poly + 1
        if window % 2 == 0:
            window += 1
    return savgol_filter(y, window_length=window, polyorder=poly, mode='nearest')


def median_filter(y, window=5):
    """
    Applies a median filter.
    Window must be odd.
    """
    if window % 2 == 0:
        window += 1
    return medfilt(y, kernel_size=window)


def percentile_filter(y, window=5, percentile=50):
    """
    Applies a percentile filter.
    """
    return scipy.ndimage.percentile_filter(y, percentile, size=window, mode='nearest')


# ==========================================
# 2. BASELINE CORRECTION ALGORITHMS
# ==========================================

def baseline_detrend(x, y):
    """
    Removes a linear trend from the data.
    """
    coeffs = np.polyfit(x, y, 1)
    trend = np.polyval(coeffs, x)
    # Corrected signal is the residual plus the mean of y to keep the scale
    return y - trend + np.mean(y)


def baseline_linear(x, y):
    """
    Draws a straight line between the first and last points and subtracts/normalizes it.
    """
    x0, x1 = x[0], x[-1]
    y0, y1 = y[0], y[-1]
    line = y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return y - line + np.mean(y)


def baseline_polynomial(x, y, deg=2, max_iter=20, tol=1e-3, peak_direction='down'):
    """
    Iterative Modified Polynomial Fitting (IModPoly) to fit a baseline without fitting peaks.
    """
    y_base = y.copy()
    last_coefs = np.zeros(deg + 1)
    
    for i in range(max_iter):
        coeffs = np.polyfit(x, y_base, deg)
        z = np.polyval(coeffs, x)
        
        # Check convergence
        if i > 0 and np.linalg.norm(coeffs - last_coefs) < tol:
            break
        last_coefs = coeffs
        
        # Residuals standard deviation
        residuals = y - z
        sigma = np.std(residuals)
        
        # Suppress peaks
        if peak_direction == 'down':
            # Transmittance peaks point down, so raw data is below baseline
            mask = y < z - sigma
            y_base[mask] = z[mask]
            y_base[~mask] = y[~mask]
        else:
            # Absorbance peaks point up, so raw data is above baseline
            mask = y > z + sigma
            y_base[mask] = z[mask]
            y_base[~mask] = y[~mask]
            
    # Re-evaluate final baseline
    coeffs = np.polyfit(x, y_base, deg)
    z = np.polyval(coeffs, x)
    return z


def baseline_asls(y, lam=1e5, p=0.001, max_iter=15, peak_direction='down'):
    """
    Asymmetric Least Squares (AsLS) baseline estimation.
    Args:
        y: input signal
        lam: smoothness parameter (typically 10^2 to 10^9)
        p: asymmetry parameter (typically 0.001 to 0.1)
        max_iter: maximum number of iterations
        peak_direction: 'down' (transmittance) or 'up' (absorbance)
    """
    L = len(y)
    D2 = sparse.diags([1, -2, 1], [0, 1, 2], shape=(L - 2, L), dtype=float)
    D = D2.T @ D2
    w = np.ones(L)
    z = np.zeros(L)
    
    for i in range(max_iter):
        W = sparse.diags(w, 0, shape=(L, L))
        A = W + lam * D
        z = spsolve(A.tocsr(), w * y)
        
        if peak_direction == 'down':
            # Peaks go down (transmittance)
            w = p * (y < z) + (1 - p) * (y >= z)
        else:
            # Peaks go up (absorbance)
            w = p * (y > z) + (1 - p) * (y <= z)
            
    return z


def baseline_airpls(y, lam=1e5, max_iter=15, tol=1e-3, peak_direction='down'):
    """
    Adaptive Iteratively Reweighted Penalized Least Squares (airPLS).
    Assumes positive peaks. If peak_direction is 'down', inverts the signal first.
    """
    if peak_direction == 'down':
        # Invert transmittance so peaks point up
        # Shift to make it positive
        y_max = np.max(y)
        y_inv = y_max - y
        z_inv = _airpls_core(y_inv, lam, max_iter, tol)
        # Convert baseline back
        return y_max - z_inv
    else:
        return _airpls_core(y, lam, max_iter, tol)


def _airpls_core(y, lam, max_iter, tol):
    L = len(y)
    D2 = sparse.diags([1, -2, 1], [0, 1, 2], shape=(L - 2, L), dtype=float)
    D = D2.T @ D2
    w = np.ones(L)
    z = np.zeros(L)
    
    for t in range(1, max_iter + 1):
        W = sparse.diags(w, 0, shape=(L, L))
        A = W + lam * D
        z = spsolve(A.tocsr(), w * y)
        d = y - z
        d_negative = d[d < 0]
        
        if len(d_negative) == 0:
            break
            
        std_neg = np.std(d_negative)
        if std_neg < tol:
            break
            
        w = np.zeros(L)
        mask = d < 0
        w[mask] = np.exp(t * d[mask] / std_neg)
        w[~mask] = 0
        
    return z


def baseline_arpls(y, lam=1e5, max_iter=15, tol=1e-3, peak_direction='down'):
    """
    Asymmetrically Reweighted Penalized Least Squares (arPLS).
    Assumes positive peaks. If peak_direction is 'down', inverts the signal first.
    """
    if peak_direction == 'down':
        y_max = np.max(y)
        y_inv = y_max - y
        z_inv = _arpls_core(y_inv, lam, max_iter, tol)
        return y_max - z_inv
    else:
        return _arpls_core(y, lam, max_iter, tol)


def _arpls_core(y, lam, max_iter, tol):
    L = len(y)
    D2 = sparse.diags([1, -2, 1], [0, 1, 2], shape=(L - 2, L), dtype=float)
    D = D2.T @ D2
    w = np.ones(L)
    z = np.zeros(L)
    
    for i in range(max_iter):
        W = sparse.diags(w, 0, shape=(L, L))
        A = W + lam * D
        z = spsolve(A.tocsr(), w * y)
        d = y - z
        d_neg = d[d < 0]
        
        if len(d_neg) == 0:
            mean_neg = 0.0
            std_neg = np.std(d)
        else:
            mean_neg = np.mean(d_neg)
            std_neg = np.std(d_neg)
            
        if std_neg < tol:
            break
            
        exponent = (d - (2 * std_neg + mean_neg)) / std_neg
        exponent = np.clip(exponent, -50, 50)
        w = 1.0 / (1.0 + np.exp(exponent))
        
    return z


# ==========================================
# 3. PIPELINE CORRECTION wrapper
# ==========================================

def correct_baseline_transmittance(x, y, method='raw', **kwargs):
    """
    Runs the chosen baseline correction method in Transmittance space.
    If method is 'raw', returns baseline as 100% and corrected as y.
    If baseline correction is applied:
        - Multiplicative correction: T_corrected = (T / T_baseline) * 100
          This is standard in spectroscopy and mathematically equivalent
          to subtracting baseline in Absorbance space.
    """
    if str(method).lower() in ('raw', 'none'):
        return np.ones_like(y) * 100, y.copy()
        
    if method == 'detrend':
        # Detrend is additive
        y_corr = baseline_detrend(x, y)
        # Approximate baseline
        z = y - y_corr + 100
        return z, y_corr
        
    if method == 'linear_baseline':
        y_corr = baseline_linear(x, y)
        z = y - y_corr + 100
        return z, y_corr
        
    # Advanced baseline algorithms return the baseline z
    if method == 'polynomial_baseline':
        deg = kwargs.get('deg', 2)
        z = baseline_polynomial(x, y, deg=deg, peak_direction='down')
    elif method == 'asls':
        lam = kwargs.get('lam', 1e5)
        p = kwargs.get('p', 0.001)
        z = baseline_asls(y, lam=lam, p=p, peak_direction='down')
    elif method == 'airpls':
        lam = kwargs.get('lam', 1e5)
        z = baseline_airpls(y, lam=lam, peak_direction='down')
    elif method == 'arpls':
        lam = kwargs.get('lam', 1e5)
        z = baseline_arpls(y, lam=lam, peak_direction='down')
    else:
        raise ValueError(f"Unknown baseline correction method: {method}")
        
    # Multiplicative correction for transmittance: (y / z) * 100
    # Avoid division by zero
    z_safe = np.where(z <= 0, 1e-5, z)
    y_corr = (y / z_safe) * 100
    
    # Clip corrected values between 0 and 150 for sanity
    y_corr = np.clip(y_corr, 0.0, 150.0)
    
    return z, y_corr


# ==========================================
# 4. PEAK DETECTION & GROUP MAPPING
# ==========================================

# Reference functional groups for graphene oxide / reduced graphene oxide
DEFAULT_FUNCTIONAL_GROUPS = {
    "O-H": (3200, 3600),
    "C-H": (2800, 3000),
    "CO2": (2300, 2400),
    "C=O": (1650, 1750),
    "C=C": (1500, 1650),
    "C-O": (1250, 1450),
    "C-O-C": (950, 1250)
}

def detect_peaks_transmittance(x, y_corr, prominence=0.5, distance=10):
    """
    Finds peaks in Transmittance data (local minima).
    To do this, we invert the signal: signal_inv = 100 - y_corr,
    where transmittance drops (peaks) become positive maxima.
    
    Returns:
        peak_indices (np.ndarray): Indices of the peaks in the spectrum
        peak_wavenumbers (np.ndarray): Wavenumbers corresponding to the peaks
        peak_heights (np.ndarray): Original Transmittance %T value at the peaks
    """
    # Invert transmittance so peaks point up
    signal_inv = 100.0 - y_corr
    
    # Use scipy.signal.find_peaks
    indices, properties = find_peaks(signal_inv, prominence=prominence, distance=distance)
    
    # Sort peaks by prominence in descending order
    if len(indices) > 0:
        prominences = properties.get('prominences', np.ones_like(indices))
        sort_idx = np.argsort(prominences)[::-1]
        indices = indices[sort_idx]
        
    return indices, x[indices], y_corr[indices]


def assign_functional_groups(peak_wavenumbers, groups_db=None):
    """
    Maps detected peak wavenumbers to functional groups in the database.
    
    Args:
        peak_wavenumbers: list/array of peak positions (cm^-1)
        groups_db: dict containing {group_name: (min_wavenumber, max_wavenumber)}
        
    Returns:
        matched_groups: dict containing {group_name: list of matching peak wavenumbers}
        noise_peaks: list of peak wavenumbers that do not match any functional group
    """
    if groups_db is None:
        groups_db = DEFAULT_FUNCTIONAL_GROUPS
        
    matched_groups = {g: [] for g in groups_db.keys()}
    noise_peaks = []
    
    for w in peak_wavenumbers:
        matched = False
        for group, (w_min, w_max) in groups_db.items():
            if w_min <= w <= w_max:
                matched_groups[group].append(w)
                matched = True
        if not matched:
            noise_peaks.append(w)
            
    # Filter out empty groups
    matched_groups = {g: peaks for g, peaks in matched_groups.items() if len(peaks) > 0}
    
    return matched_groups, noise_peaks


def calculate_pipeline_score(total_peaks, matched_groups, noise_peaks, noise_penalty_weight=1.0):
    """
    Computes a evaluation score for the current preprocessing pipeline:
    Score = N_peaks + N_groups_detected - W_n * N_noise_peaks
    
    Since Total Peaks = Valid Peaks + Noise Peaks, this is equivalent to:
    Score = Valid Peaks + N_groups_detected + (1 - W_n) * Noise Peaks
    
    If noise_penalty_weight == 1.0, the noise peaks cancel out exactly:
    Score = Valid Peaks + N_groups_detected
    
    If noise_penalty_weight == 2.0:
    Score = Valid Peaks + N_groups_detected - Noise Peaks
    """
    n_peaks = len(total_peaks)
    n_groups = len(matched_groups)
    n_noise = len(noise_peaks)
    
    score = n_peaks + n_groups - noise_penalty_weight * n_noise
    return int(round(score))


# ==========================================
# 5. ABSORBANCE SPACE SUPPORT
# ==========================================

def transmittance_to_absorbance(t):
    """
    Converts Transmittance %T to Absorbance A.
    Formula: A = 2 - log10(T)
    Clips transmittance to a small positive value to avoid undefined log of zero or negatives.
    """
    t_clipped = np.clip(t, 1e-5, 150.0)
    return 2.0 - np.log10(t_clipped)


def correct_baseline_absorbance(x, y_abs, method='raw', **kwargs):
    """
    Runs baseline correction in Absorbance space (where peaks point UP).
    Returns:
        z (np.ndarray): The estimated baseline
        y_corr (np.ndarray): The corrected absorbance (y_abs - z)
    """
    if str(method).lower() in ('raw', 'none'):
        return np.zeros_like(y_abs), y_abs.copy()
        
    if method == 'detrend':
        # Detrend returns y - trend + mean(y)
        # So we can calculate baseline as trend - mean(y)
        coeffs = np.polyfit(x, y_abs, 1)
        z = np.polyval(coeffs, x) - np.mean(y_abs)
        y_corr = y_abs - z
        return z, y_corr
        
    if method == 'linear_baseline':
        x0, x1 = x[0], x[-1]
        y0, y1 = y_abs[0], y_abs[-1]
        z = y0 + (y1 - y0) * (x - x0) / (x1 - x0) - np.mean(y_abs)
        y_corr = y_abs - z
        return z, y_corr
        
    # Advanced baseline algorithms
    if method == 'polynomial_baseline':
        deg = kwargs.get('deg', 2)
        z = baseline_polynomial(x, y_abs, deg=deg, peak_direction='up')
    elif method == 'asls':
        lam = kwargs.get('lam', 1e5)
        p = kwargs.get('p', 0.001)
        z = baseline_asls(y_abs, lam=lam, p=p, peak_direction='up')
    elif method == 'airpls':
        lam = kwargs.get('lam', 1e5)
        z = baseline_airpls(y_abs, lam=lam, peak_direction='up')
    elif method == 'arpls':
        lam = kwargs.get('lam', 1e5)
        z = baseline_arpls(y_abs, lam=lam, peak_direction='up')
    else:
        raise ValueError(f"Unknown baseline correction method in absorbance: {method}")
        
    y_corr = y_abs - z
    return z, y_corr


def detect_peaks_absorbance(x, y_abs_corr, prominence=0.02, distance=15):
    """
    Finds peaks in Absorbance data (local maxima).
    No inversion is needed since peaks point UP.
    
    Returns:
        peak_indices (np.ndarray): Indices of the peaks in the spectrum
        peak_wavenumbers (np.ndarray): Wavenumbers corresponding to the peaks
        peak_heights (np.ndarray): Absorbance value at the peaks
    """
    # Use scipy.signal.find_peaks on absorbance
    indices, properties = find_peaks(y_abs_corr, prominence=prominence, distance=distance)
    
    # Sort peaks by prominence in descending order
    if len(indices) > 0:
        prominences = properties.get('prominences', np.ones_like(indices))
        sort_idx = np.argsort(prominences)[::-1]
        indices = indices[sort_idx]
        
    return indices, x[indices], y_abs_corr[indices]

