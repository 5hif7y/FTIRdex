"""
FTIR High-Level Pipeline and Utilities
--------------------------------------
This module provides high-level modular functions to run combinatorial grid searches,
generate annotated plots, generate 3x1 subplots galleries, superimpose spectra,
and export numerical reports of peaks and valleys.
"""

import os
import csv
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks

from .core import (
    load_ftir_data,
    load_jcamp_dx,
    moving_average,
    savitzky_golay,
    median_filter,
    percentile_filter,
    correct_baseline_transmittance,
    correct_baseline_absorbance,
    transmittance_to_absorbance,
    detect_peaks_transmittance,
    detect_peaks_absorbance,
    assign_functional_groups,
    calculate_pipeline_score,
    DEFAULT_FUNCTIONAL_GROUPS
)

def _map_spanish_params(param_val):
    if not isinstance(param_val, str):
        return param_val
    
    val = param_val.strip().lower()
    is_spanish = False
    mapped_val = param_val
    
    if val == "transmitancia":
        mapped_val = "transmittance"
        is_spanish = True
    elif val == "absorbancia":
        mapped_val = "absorbance"
        is_spanish = True
    elif val == "lineas":
        mapped_val = "lines"
        is_spanish = True
    elif val == "cajas":
        mapped_val = "box"
        is_spanish = True
        
    if is_spanish:
        import warnings
        warnings.warn(
            "Advertencia: Esta biblioteca admite comandos y parámetros en español para facilitar su adopción y accesibilidad. "
            "No obstante, recomendamos familiarizarse gradualmente con la terminología en inglés, ya que constituye el estándar "
            "predominante en documentación científica, programación e instrumentación analítica.",
            UserWarning,
            stacklevel=3
        )
    return mapped_val

RAW = "RAW"
NONE = "NONE"

# Default combinatorial configurations
DEFAULT_SMOOTHING_CONFIGS = [
    {"name": "RAW", "func": lambda y: y.copy(), "label": "RAW"},
    {"name": "Moving_Average", "func": lambda y: moving_average(y, 3), "label": "Moving_Average(3)"},
    {"name": "Moving_Average", "func": lambda y: moving_average(y, 5), "label": "Moving_Average(5)"},
    {"name": "Moving_Average", "func": lambda y: moving_average(y, 7), "label": "Moving_Average(7)"},
    {"name": "Savitzky_Golay", "func": lambda y: savitzky_golay(y, 7, 2), "label": "Savitzky_Golay(7, 2)"},
    {"name": "Savitzky_Golay", "func": lambda y: savitzky_golay(y, 11, 2), "label": "Savitzky_Golay(11, 2)"},
    {"name": "Savitzky_Golay", "func": lambda y: savitzky_golay(y, 15, 3), "label": "Savitzky_Golay(15, 3)"},
    {"name": "Median_Filter", "func": lambda y: median_filter(y, 3), "label": "Median_Filter(3)"},
    {"name": "Median_Filter", "func": lambda y: median_filter(y, 5), "label": "Median_Filter(5)"},
    {"name": "Median_Filter", "func": lambda y: median_filter(y, 7), "label": "Median_Filter(7)"},
    {"name": "Percentile_Filter", "func": lambda y: percentile_filter(y, 5, 25), "label": "Percentile_Filter(5, 25)"},
    {"name": "Percentile_Filter", "func": lambda y: percentile_filter(y, 5, 75), "label": "Percentile_Filter(5, 75)"},
]

DEFAULT_BASELINE_CONFIGS = [
    {"name": "RAW", "method": "raw", "kwargs": {}, "label": "RAW"},
    {"name": "detrend", "method": "detrend", "kwargs": {}, "label": "detrend"},
    {"name": "linear_baseline", "method": "linear_baseline", "kwargs": {}, "label": "linear_baseline"},
    {"name": "polynomial_baseline", "method": "polynomial_baseline", "kwargs": {"deg": 2}, "label": "polynomial_baseline(deg=2)"},
    {"name": "polynomial_baseline", "method": "polynomial_baseline", "kwargs": {"deg": 3}, "label": "polynomial_baseline(deg=3)"},
    {"name": "polynomial_baseline", "method": "polynomial_baseline", "kwargs": {"deg": 4}, "label": "polynomial_baseline(deg=4)"},
    {"name": "asls", "method": "asls", "kwargs": {"lam": 1e4, "p": 0.001}, "label": "asls(lam=1e4, p=0.001)"},
    {"name": "asls", "method": "asls", "kwargs": {"lam": 1e5, "p": 0.001}, "label": "asls(lam=1e5, p=0.001)"},
    {"name": "asls", "method": "asls", "kwargs": {"lam": 1e6, "p": 0.001}, "label": "asls(lam=1e6, p=0.001)"},
    {"name": "airpls", "method": "airpls", "kwargs": {"lam": 1e4}, "label": "airpls(lam=1e4)"},
    {"name": "airpls", "method": "airpls", "kwargs": {"lam": 1e5}, "label": "airpls(lam=1e5)"},
    {"name": "airpls", "method": "airpls", "kwargs": {"lam": 1e6}, "label": "airpls(lam=1e6)"},
    {"name": "arpls", "method": "arpls", "kwargs": {"lam": 1e4}, "label": "arpls(lam=1e4)"},
    {"name": "arpls", "method": "arpls", "kwargs": {"lam": 1e5}, "label": "arpls(lam=1e5)"},
    {"name": "arpls", "method": "arpls", "kwargs": {"lam": 1e6}, "label": "arpls(lam=1e6)"},
]


def parse_num(s):
    """Parses a string into an int, float, or returns the string if non-numeric."""
    try:
        val = float(s)
        if val.is_integer():
            return int(val)
        return val
    except ValueError:
        return s


def parse_config_params(label):
    """Parses configuration name and parameters from labels, e.g. 'Savitzky_Golay(11, 2)'."""
    label = label.strip()
    if label == "RAW":
        return "raw", {}
        
    if "(" in label and ")" in label:
        name = label.split("(")[0].strip()
        param_str = label.split("(")[1].split(")")[0].strip()
        
        params = {}
        if "," in param_str:
            parts = param_str.split(",")
            for part in parts:
                if "=" in part:
                    k, v = part.split("=")
                    params[k.strip()] = parse_num(v.strip())
                else:
                    val = parse_num(part.strip())
                    if "poly" not in params and len(params) == 1:
                        params["poly"] = val
                    elif "window" not in params:
                        params["window"] = val
        else:
            if "=" in param_str:
                k, v = param_str.split("=")
                params[k.strip()] = parse_num(v.strip())
            else:
                val = parse_num(param_str.strip())
                params["window"] = val
                    
        return name, params
    return label, {}


def apply_smoothing(y, smooth_label):
    """Applies the smoothing filter specified by the config label."""
    if isinstance(smooth_label, str) and smooth_label.upper() in ("RAW", "NONE"):
        return y.copy()
    smooth_name, smooth_params = parse_config_params(smooth_label)
    if smooth_name.lower() in ("raw", "none"):
        return y.copy()
    elif "Moving_Average" in smooth_label:
        return moving_average(y, window=smooth_params.get("window", 5))
    elif "Savitzky_Golay" in smooth_label:
        return savitzky_golay(y, window=smooth_params.get("window", 11), poly=smooth_params.get("poly", 2))
    elif "Median_Filter" in smooth_label:
        return median_filter(y, window=smooth_params.get("window", 5))
    elif "Percentile_Filter" in smooth_label:
        pct = smooth_params.get("percentile", 50)
        if "percentile" not in smooth_params and "poly" in smooth_params:
            pct = smooth_params["poly"]
        return percentile_filter(y, window=smooth_params.get("window", 5), percentile=pct)
    else:
        return y.copy()


def apply_baseline(x, y, base_label, space='absorbance'):
    """Applies the baseline correction specified by the config label."""
    space = _map_spanish_params(space)
    if isinstance(base_label, str) and base_label.upper() in ("RAW", "NONE"):
        base_name = "raw"
        base_params = {}
    else:
        base_name, base_params = parse_config_params(base_label)
        if base_name.lower() in ("raw", "none"):
            base_name = "raw"
            base_params = {}
            
    if space == 'absorbance':
        return correct_baseline_absorbance(x, y, method=base_name, **base_params)
    else:
        return correct_baseline_transmittance(x, y, method=base_name, **base_params)


def preprocess_spectrum(x, y, smooth_label, base_label, space='absorbance'):
    """
    Convenience function to apply smoothing and baseline correction in one step.
    
    Returns:
        baseline (np.ndarray): The estimated baseline
        y_corrected (np.ndarray): The corrected spectrum (absorbance or transmittance)
    """
    y_smoothed = apply_smoothing(y, smooth_label)
    space = _map_spanish_params(space)
    return apply_baseline(x, y_smoothed, base_label, space=space)


def run_grid_search(x, y, output_csv=None, best_config_txt=None, space='absorbance', 
                    prominence=0.02, distance=15, noise_penalty_weight=2.0,
                    smoothing_configs=None, baseline_configs=None, groups_db=None):
    """
    Runs a grid search over combinations of smoothing and baseline correction algorithms.
    
    Args:
        x (np.ndarray): Wavenumbers
        y (np.ndarray): Spectrum values (Absorbance if space='absorbance', Transmittance if space='transmittance')
        output_csv (str): Optional path to save CSV results
        best_config_txt (str): Optional path to save the best configuration as text
        space (str): 'absorbance' or 'transmittance'
        prominence (float): Peak detection prominence
        distance (int): Peak detection minimum distance
        noise_penalty_weight (float): Penalty multiplier for noise peaks in score
        smoothing_configs (list): Custom list of smoothing configs
        baseline_configs (list): Custom list of baseline configs
        groups_db (dict): Optional custom functional group database
        
    Returns:
        best_config (dict): The highest scoring configuration details
        results (list): List of dicts for all configurations executed
    """
    space = _map_spanish_params(space)
    smooth_configs = smoothing_configs if smoothing_configs is not None else DEFAULT_SMOOTHING_CONFIGS
    base_configs = baseline_configs if baseline_configs is not None else DEFAULT_BASELINE_CONFIGS
    
    results = []
    
    for smooth_cfg in smooth_configs:
        # Wrap lambda or use func key
        if "func" in smooth_cfg:
            y_smoothed = smooth_cfg["func"](y)
        else:
            y_smoothed = apply_smoothing(y, smooth_cfg["label"])
            
        for base_cfg in base_configs:
            try:
                if space == 'absorbance':
                    z, y_corrected = correct_baseline_absorbance(
                        x, y_smoothed, method=base_cfg["method"], **base_cfg["kwargs"]
                    )
                    indices, peak_x, peak_y = detect_peaks_absorbance(
                        x, y_corrected, prominence=prominence, distance=distance
                    )
                else:
                    z, y_corrected = correct_baseline_transmittance(
                        x, y_smoothed, method=base_cfg["method"], **base_cfg["kwargs"]
                    )
                    indices, peak_x, peak_y = detect_peaks_transmittance(
                        x, y_corrected, prominence=prominence, distance=distance
                    )
                    
                matched_groups, noise_peaks = assign_functional_groups(peak_x, groups_db=groups_db)
                
                score_std = calculate_pipeline_score(peak_x, matched_groups, noise_peaks, noise_penalty_weight=1.0)
                score_pen = calculate_pipeline_score(peak_x, matched_groups, noise_peaks, noise_penalty_weight=noise_penalty_weight)
                
                group_names = sorted(list(matched_groups.keys()))
                group_names_str = ", ".join(group_names) if group_names else "None"
                
                results.append({
                    "Smoothing": smooth_cfg["label"],
                    "Baseline": base_cfg["label"],
                    "N_Groups_Detected": len(matched_groups),
                    "Detected_Groups": group_names_str,
                    "N_Peaks_Detected": len(peak_x),
                    "N_Noise_Peaks": len(noise_peaks),
                    "Score_Std": score_std,
                    "Score_Penalized": score_pen
                })
            except Exception as e:
                print(f"Error executing combination {smooth_cfg['label']} + {base_cfg['label']}: {e}")
                
    # Save to CSV if requested
    if output_csv:
        with open(output_csv, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                "Smoothing", "Baseline", "N_Groups_Detected", 
                "Detected_Groups", "N_Peaks_Detected", 
                "N_Noise_Peaks", "Score_Std", "Score_Penalized"
            ])
            writer.writeheader()
            writer.writerows(results)
            
    # Find best configuration, excluding RAW baseline to ensure some correction is done
    filtered_results = [r for r in results if r["Baseline"] != "RAW"]
    if not filtered_results:
        filtered_results = results
        
    best_config = max(filtered_results, key=lambda r: (r["Score_Penalized"], r["N_Groups_Detected"], -r["N_Noise_Peaks"]))
    
    # Save best config text if requested
    if best_config_txt:
        with open(best_config_txt, "w", encoding='utf-8') as f:
            f.write(f"Smoothing: {best_config['Smoothing']}\n")
            f.write(f"Baseline: {best_config['Baseline']}\n")
            
    return best_config, results


def plot_config(x, y, smooth_algorithm, baseline_algorithm, *args, **kwargs):
    """
    Plots a specific configuration of smoothing and baseline correction.
    If both smooth_algorithm and baseline_algorithm are RAW or NONE, peak detection and
    functional group mapping are disabled, unless groups_db or group_order are explicitly provided.
    """
    # Extract keyword arguments or set defaults
    output_image = kwargs.pop('output_image', None)
    space = kwargs.pop('space', 'absorbance')
    prominence = kwargs.pop('prominence', 0.02)
    distance = kwargs.pop('distance', 15)
    mode = kwargs.pop('mode', 'lines')
    groups_db = kwargs.pop('groups_db', None)
    group_order = kwargs.pop('group_order', None)
    invert_x = kwargs.pop('invert_x', True)
    
    if kwargs:
        raise TypeError(f"plot_config() got unexpected keyword arguments: {list(kwargs.keys())}")
        
    remaining_args = list(args)
    
    # Try to identify output_image if not already provided as a keyword argument
    if output_image is None and len(remaining_args) > 0:
        # Check if any string argument is not a known parameter keyword
        for idx, arg in enumerate(remaining_args):
            if isinstance(arg, str) and arg.lower() not in ('absorbance', 'transmittance', 'lines', 'box', 'boxes', 'raw', 'none'):
                output_image = arg
                remaining_args.pop(idx)
                break
        else:
            # If no clear filename string was found but the first arg is a string, assume it's output_image
            if isinstance(remaining_args[0], str):
                output_image = remaining_args.pop(0)
                
    # Distribute the rest of the positional arguments
    if len(remaining_args) > 0:
        space = remaining_args.pop(0)
    if len(remaining_args) > 0:
        prominence = remaining_args.pop(0)
    if len(remaining_args) > 0:
        distance = remaining_args.pop(0)
    if len(remaining_args) > 0:
        mode = remaining_args.pop(0)
    if len(remaining_args) > 0:
        groups_db = remaining_args.pop(0)
    if len(remaining_args) > 0:
        group_order = remaining_args.pop(0)
    if len(remaining_args) > 0:
        invert_x = remaining_args.pop(0)

    if output_image is None:
        raise ValueError("Se debe especificar 'output_image' como argumento posicional o de palabra clave.")
        
    space = _map_spanish_params(space)
    mode = _map_spanish_params(mode)
    if mode == "boxes":
        mode = "box"
        
    # Check if both are RAW or NONE
    is_raw_smooth = False
    if isinstance(smooth_algorithm, str):
        is_raw_smooth = smooth_algorithm.upper() in ("RAW", "NONE")
        
    is_raw_base = False
    if isinstance(baseline_algorithm, str):
        is_raw_base = baseline_algorithm.upper() in ("RAW", "NONE")
        
    # Peak detection is disabled if BOTH smooth and baseline are RAW/NONE,
    # unless groups_db or group_order are explicitly specified.
    disable_groups = is_raw_smooth and is_raw_base and (groups_db is None) and (group_order is None)
    
    # Preprocess
    z, y_corrected = preprocess_spectrum(x, y, smooth_algorithm, baseline_algorithm, space=space)
    
    # Set up plot styling
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "Arial", "Inter", "Liberation Sans"]
    
    fig, ax = plt.subplots(figsize=(10, 7), dpi=300)
    ax.plot(x, y_corrected, color='black', linewidth=1.0)
    
    ax.set_xlabel("Número de onda (cm$^{-1}$)", fontsize=13)
    if space == 'absorbance':
        ax.set_ylabel("Absorbancia (u.a.)", fontsize=13)
    else:
        ax.set_ylabel("Transmitancia (u.a.)", fontsize=13)
        
    if invert_x:
        ax.set_xlim(max(x), min(x))
    else:
        ax.set_xlim(min(x), max(x))
        
    y_min, y_max = np.min(y_corrected), np.max(y_corrected)
    y_range = y_max - y_min if y_max > y_min else 1.0
    
    if space == 'absorbance':
        ax.set_ylim(y_min - 0.05 * y_range, y_max + 0.40 * y_range)
    else:
        ax.set_ylim(y_min - 0.35 * y_range, y_max + 0.05 * y_range)
        
    ax.yaxis.set_major_formatter(plt.NullFormatter())
    ax.tick_params(axis='both', which='major', labelsize=11, direction='in', length=6, width=1.0)
    ax.tick_params(axis='both', which='minor', direction='in', length=3, width=1.0)
    ax.minorticks_on()
    ax.yaxis.set_minor_locator(plt.NullLocator())
    
    if not disable_groups:
        # Detect peaks and assign groups
        if space == 'absorbance':
            indices, peak_x, peak_y = detect_peaks_absorbance(x, y_corrected, prominence=prominence, distance=distance)
        else:
            indices, peak_x, peak_y = detect_peaks_transmittance(x, y_corrected, prominence=prominence, distance=distance)
            
        if groups_db is None:
            groups_db = DEFAULT_FUNCTIONAL_GROUPS
        if group_order is None:
            if groups_db is not DEFAULT_FUNCTIONAL_GROUPS:
                group_order = list(groups_db.keys())
            else:
                group_order = ["O-H", "C-H", "CO2", "C=O", "C=C", "C-O", "C-O-C"]
            
        matched_groups, noise_peaks = assign_functional_groups(peak_x, groups_db=groups_db)
        
        sorted_peaks = []
        for group_name in group_order:
            if group_name not in matched_groups:
                # Fallback scan
                w_min, w_max = groups_db[group_name]
                mask = (x >= w_min) & (x <= w_max)
                if np.any(mask):
                    if space == 'absorbance':
                        ext_idx = np.argmax(y_corrected[mask])
                        peak_w = x[mask][ext_idx]
                        peak_val = y_corrected[mask][ext_idx]
                        if peak_val > 0.01:
                            matched_groups[group_name] = [peak_w]
                    else:
                        ext_idx = np.argmin(y_corrected[mask])
                        peak_w = x[mask][ext_idx]
                        peak_val = y_corrected[mask][ext_idx]
                        if peak_val < 99.5:
                            matched_groups[group_name] = [peak_w]
                            
            if group_name in matched_groups:
                peak_w = matched_groups[group_name][0]
                idx = np.abs(x - peak_w).argmin()
                sorted_peaks.append((x[idx], y_corrected[idx], group_name))
                
        sorted_peaks.sort(key=lambda item: item[0], reverse=invert_x)
        
        if mode == 'box':
            for group_name in group_order:
                if group_name in matched_groups:
                    w_min, w_max = groups_db[group_name]
                    ax.axvspan(w_min, w_max, facecolor='red', alpha=0.06, 
                               edgecolor='red', linestyle='--', linewidth=0.8)
                    x_text = (w_min + w_max) / 2
                    if space == 'absorbance':
                        mask_band = (x >= w_min) & (x <= w_max)
                        y_local_max = np.max(y_corrected[mask_band]) if np.any(mask_band) else y_max
                        label_h = len(group_name) * 0.02 * y_range
                        y_plot_top = y_max + 0.40 * y_range
                        if (y_plot_top - y_local_max) > (label_h + 0.05 * y_range):
                            y_text = y_plot_top - 0.02 * y_range
                            va_align = 'top'
                        else:
                            y_text = y_local_max + 0.02 * y_range
                            va_align = 'bottom'
                        ax.text(
                            x_text, y_text, group_name,
                            rotation=270, color='blue', ha='center', va=va_align, 
                            fontsize=12, fontweight='bold'
                        )
                    else:
                        y_text = y_min - 0.12 * y_range
                        ax.text(
                            x_text, y_text, group_name,
                            rotation=270, color='blue', ha='center', va='top', 
                            fontsize=12, fontweight='bold'
                        )
        else:
            alternate = False
            text_offset = 0.10 * y_range if space == 'absorbance' else 0.12 * y_range
            
            for i, (peak_w_exact, peak_val, group_name) in enumerate(sorted_peaks):
                current_offset = text_offset
                if i > 0 and abs(peak_w_exact - sorted_peaks[i-1][0]) < 160:
                    if not alternate:
                        current_offset = text_offset + 0.15 * y_range
                        alternate = True
                    else:
                        current_offset = text_offset
                        alternate = False
                else:
                    alternate = False
                    
                if space == 'absorbance':
                    y_text = peak_val + current_offset
                    ax.plot([peak_w_exact, peak_w_exact], [peak_val, y_text], color='red', linestyle='--', linewidth=1.0)
                    ax.text(
                        peak_w_exact, y_text + 0.02 * y_range, group_name,
                        rotation=270, color='blue', ha='center', va='bottom', fontsize=12, fontweight='bold'
                    )
                else:
                    y_text = peak_val - current_offset
                    ax.plot([peak_w_exact, peak_w_exact], [peak_val, y_text], color='red', linestyle='--', linewidth=1.0)
                    ax.text(
                        peak_w_exact, y_text - 0.02 * y_range, group_name,
                        rotation=270, color='blue', ha='center', va='top', fontsize=12, fontweight='bold'
                    )
                    
    plt.tight_layout()
    plt.savefig(output_image, bbox_inches='tight', dpi=300)
    plt.close()
    print(f"Plot saved to '{output_image}'.")


def plot_best_configuration(x, y, best_cfg, output_image, space='absorbance', prominence=0.02, distance=15, mode='lines', groups_db=None, group_order=None, invert_x=True):
    """
    Plots the best baseline-corrected spectrum with functional groups annotated.
    Includes collision avoidance for labels.
    """
    space = _map_spanish_params(space)
    mode = _map_spanish_params(mode)
    smooth_label = best_cfg["Smoothing"]
    base_label = best_cfg["Baseline"]
    
    # Preprocess
    z, y_corrected = preprocess_spectrum(x, y, smooth_label, base_label, space=space)
    
    # Detect peaks
    if space == 'absorbance':
        indices, peak_x, peak_y = detect_peaks_absorbance(x, y_corrected, prominence=prominence, distance=distance)
    else:
        indices, peak_x, peak_y = detect_peaks_transmittance(x, y_corrected, prominence=prominence, distance=distance)
        
    if groups_db is None:
        groups_db = DEFAULT_FUNCTIONAL_GROUPS
    if group_order is None:
        group_order = ["O-H", "C-H", "CO2", "C=O", "C=C", "C-O", "C-O-C"]
        
    matched_groups, noise_peaks = assign_functional_groups(peak_x, groups_db=groups_db)
    
    # Set up plot styling
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "Arial", "Inter", "Liberation Sans"]
    
    fig, ax = plt.subplots(figsize=(10, 7), dpi=300)
    ax.plot(x, y_corrected, color='black', linewidth=1.0)
    
    ax.set_xlabel("Número de onda (cm$^{-1}$)", fontsize=13)
    if space == 'absorbance':
        ax.set_ylabel("Absorbancia (u.a.)", fontsize=13)
    else:
        ax.set_ylabel("Transmitancia (u.a.)", fontsize=13)
        
    if invert_x:
        ax.set_xlim(max(x), min(x))
    else:
        ax.set_xlim(min(x), max(x))
    
    y_min, y_max = np.min(y_corrected), np.max(y_corrected)
    y_range = y_max - y_min if y_max > y_min else 1.0
    
    if space == 'absorbance':
        ax.set_ylim(y_min - 0.05 * y_range, y_max + 0.40 * y_range) # overhead space for labels
    else:
        ax.set_ylim(y_min - 0.35 * y_range, y_max + 0.05 * y_range) # underhead space for labels
        
    ax.yaxis.set_major_formatter(plt.NullFormatter())
    ax.tick_params(axis='both', which='major', labelsize=11, direction='in', length=6, width=1.0)
    ax.tick_params(axis='both', which='minor', direction='in', length=3, width=1.0)
    ax.minorticks_on()
    ax.yaxis.set_minor_locator(plt.NullLocator())
    
    sorted_peaks = []
    for group_name in group_order:
        if group_name not in matched_groups:
            # Fallback scan for peak in range
            w_min, w_max = groups_db[group_name]
            mask = (x >= w_min) & (x <= w_max)
            if np.any(mask):
                if space == 'absorbance':
                    ext_idx = np.argmax(y_corrected[mask])
                    peak_w = x[mask][ext_idx]
                    peak_val = y_corrected[mask][ext_idx]
                    if peak_val > 0.01:
                        matched_groups[group_name] = [peak_w]
                else:
                    ext_idx = np.argmin(y_corrected[mask])
                    peak_w = x[mask][ext_idx]
                    peak_val = y_corrected[mask][ext_idx]
                    if peak_val < 99.5:
                        matched_groups[group_name] = [peak_w]
                        
        if group_name in matched_groups:
            peak_w = matched_groups[group_name][0]
            idx = np.abs(x - peak_w).argmin()
            sorted_peaks.append((x[idx], y_corrected[idx], group_name))
            
    # Sort left to right
    sorted_peaks.sort(key=lambda item: item[0], reverse=invert_x)
    
    if mode == 'box':
        for group_name in group_order:
            if group_name in matched_groups:
                w_min, w_max = groups_db[group_name]
                ax.axvspan(w_min, w_max, facecolor='red', alpha=0.06, 
                           edgecolor='red', linestyle='--', linewidth=0.8)
                x_text = (w_min + w_max) / 2
                if space == 'absorbance':
                    # Calculate local max in the band to place label dynamically
                    mask_band = (x >= w_min) & (x <= w_max)
                    y_local_max = np.max(y_corrected[mask_band]) if np.any(mask_band) else y_max
                    label_h = len(group_name) * 0.02 * y_range
                    y_plot_top = y_max + 0.40 * y_range
                    if (y_plot_top - y_local_max) > (label_h + 0.05 * y_range):
                        y_text = y_plot_top - 0.02 * y_range
                        va_align = 'top'
                    else:
                        y_text = y_local_max + 0.02 * y_range
                        va_align = 'bottom'
                    ax.text(
                        x_text, y_text, group_name,
                        rotation=270, color='blue', ha='center', va=va_align, 
                        fontsize=12, fontweight='bold'
                    )
                else:
                    y_text = y_min - 0.12 * y_range
                    ax.text(
                        x_text, y_text, group_name,
                        rotation=270, color='blue', ha='center', va='top', 
                        fontsize=12, fontweight='bold'
                    )
    else:
        alternate = False
        text_offset = 0.10 * y_range if space == 'absorbance' else 0.12 * y_range
        
        for i, (peak_w_exact, peak_val, group_name) in enumerate(sorted_peaks):
            current_offset = text_offset
            if i > 0 and abs(peak_w_exact - sorted_peaks[i-1][0]) < 160:
                if not alternate:
                    current_offset = text_offset + 0.15 * y_range
                    alternate = True
                else:
                    current_offset = text_offset
                    alternate = False
            else:
                alternate = False
                
            if space == 'absorbance':
                y_text = peak_val + current_offset
                ax.plot([peak_w_exact, peak_w_exact], [peak_val, y_text], color='red', linestyle='--', linewidth=1.0)
                ax.text(
                    peak_w_exact, y_text + 0.02 * y_range, group_name,
                    rotation=270, color='blue', ha='center', va='bottom', fontsize=12, fontweight='bold'
                )
            else:
                y_text = peak_val - current_offset
                ax.plot([peak_w_exact, peak_w_exact], [peak_val, y_text], color='red', linestyle='--', linewidth=1.0)
                ax.text(
                    peak_w_exact, y_text - 0.02 * y_range, group_name,
                    rotation=270, color='blue', ha='center', va='top', fontsize=12, fontweight='bold'
                )
            
    plt.tight_layout()
    plt.savefig(output_image, bbox_inches='tight', dpi=300)
    plt.close()
    print(f"Plot saved to '{output_image}'.")


def plot_gallery_3x1(x, y, results, output_prefix, space='absorbance', prominence=0.02, distance=15, max_total_plots=15, mode='lines', groups_db=None, group_order=None, invert_x=True):
    """
    Plots the best performing configurations as multiple 3x1 images (3 horizontal subplots in one row per file).
    This keeps the resolution high and prevents document truncation or page-overflow.
    """
    space = _map_spanish_params(space)
    mode = _map_spanish_params(mode)
    max_groups = max(int(r["N_Groups_Detected"]) for r in results)
    gallery_configs = [c for c in results if int(c["N_Groups_Detected"]) == max_groups]
    gallery_configs = [c for c in gallery_configs if c["Baseline"] != "RAW"]
    
    if len(gallery_configs) == 0:
        print("No configurations found for gallery.")
        return
        
    gallery_configs.sort(key=lambda c: (float(c["Score_Penalized"]), -float(c["N_Noise_Peaks"])), reverse=True)
    
    if len(gallery_configs) > max_total_plots:
        gallery_configs = gallery_configs[:max_total_plots]
        
    # Chunk into groups of 3
    chunk_size = 3
    n_chunks = int(np.ceil(len(gallery_configs) / chunk_size))
    
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "Arial", "Inter", "Liberation Sans"]
    
    if groups_db is None:
        groups_db = DEFAULT_FUNCTIONAL_GROUPS
    if group_order is None:
        group_order = ["O-H", "C-H", "CO2", "C=O", "C=C", "C-O", "C-O-C"]
        
    for chunk_idx in range(n_chunks):
        start = chunk_idx * chunk_size
        end = min(start + chunk_size, len(gallery_configs))
        chunk_cfgs = gallery_configs[start:end]
        
        # We always create a 1 row, 3 columns figure. If End-Start < 3, some columns will be empty.
        fig, axes = plt.subplots(1, 3, figsize=(12.5, 3.6), dpi=300)
        axes_flat = axes.flatten()
        
        for i in range(3):
            ax = axes_flat[i]
            if i >= len(chunk_cfgs):
                ax.axis('off')
                continue
                
            cfg = chunk_cfgs[i]
            smooth_label = cfg["Smoothing"]
            base_label = cfg["Baseline"]
            
            # Preprocess
            z, y_corrected = preprocess_spectrum(x, y, smooth_label, base_label, space=space)
            
            # Detect peaks
            if space == 'absorbance':
                indices, peak_x, peak_y = detect_peaks_absorbance(x, y_corrected, prominence=prominence, distance=distance)
            else:
                indices, peak_x, peak_y = detect_peaks_transmittance(x, y_corrected, prominence=prominence, distance=distance)
                
            matched_groups, noise_peaks = assign_functional_groups(peak_x, groups_db=groups_db)
            
            # Plot
            ax.plot(x, y_corrected, color='black', linewidth=0.8)
            if invert_x:
                ax.set_xlim(max(x), min(x))
            else:
                ax.set_xlim(min(x), max(x))
            
            y_min, y_max = np.min(y_corrected), np.max(y_corrected)
            y_range = y_max - y_min if y_max > y_min else 1.0
            
            if space == 'absorbance':
                ax.set_ylim(y_min - 0.05 * y_range, y_max + 0.45 * y_range)
            else:
                ax.set_ylim(y_min - 0.45 * y_range, y_max + 0.05 * y_range)
                
            ax.set_title(f"{smooth_label}\n+ {base_label}", fontsize=8, fontweight='bold', pad=4)
            ax.yaxis.set_major_formatter(plt.NullFormatter())
            ax.tick_params(axis='both', which='major', labelsize=8, direction='in', length=4, width=0.8)
            ax.tick_params(axis='both', which='minor', direction='in', length=2, width=0.8)
            ax.minorticks_on()
            ax.yaxis.set_minor_locator(plt.NullLocator())
            
            ax.set_xlabel("Número de onda (cm$^{-1}$)", fontsize=8)
            
            # Label groups
            text_offset = 0.12 * y_range if space == 'absorbance' else 0.15 * y_range
            
            sorted_peaks = []
            for group_name in group_order:
                if group_name not in matched_groups:
                    w_min, w_max = groups_db[group_name]
                    mask = (x >= w_min) & (x <= w_max)
                    if np.any(mask):
                        if space == 'absorbance':
                            ext_idx = np.argmax(y_corrected[mask])
                            peak_w = x[mask][ext_idx]
                            peak_val = y_corrected[mask][ext_idx]
                            if peak_val > 0.01:
                                matched_groups[group_name] = [peak_w]
                        else:
                            ext_idx = np.argmin(y_corrected[mask])
                            peak_w = x[mask][ext_idx]
                            peak_val = y_corrected[mask][ext_idx]
                            if peak_val < 99.5:
                                matched_groups[group_name] = [peak_w]
                                
                if group_name in matched_groups:
                    peak_w = matched_groups[group_name][0]
                    idx = np.abs(x - peak_w).argmin()
                    sorted_peaks.append((x[idx], y_corrected[idx], group_name))
                    
            sorted_peaks.sort(key=lambda item: item[0], reverse=invert_x)
            
            if mode == 'box':
                for group_name in group_order:
                    if group_name in matched_groups:
                        w_min, w_max = groups_db[group_name]
                        ax.axvspan(w_min, w_max, facecolor='red', alpha=0.06, 
                                   edgecolor='red', linestyle='--', linewidth=0.5)
                        x_text = (w_min + w_max) / 2
                        if space == 'absorbance':
                            # Calculate local max in the band to place label dynamically
                            mask_band = (x >= w_min) & (x <= w_max)
                            y_local_max = np.max(y_corrected[mask_band]) if np.any(mask_band) else y_max
                            label_h = len(group_name) * 0.012 * y_range
                            y_plot_top = y_max + 0.45 * y_range
                            if (y_plot_top - y_local_max) > (label_h + 0.05 * y_range):
                                y_text = y_plot_top - 0.02 * y_range
                                va_align = 'top'
                            else:
                                y_text = y_local_max + 0.02 * y_range
                                va_align = 'bottom'
                            ax.text(
                                x_text, y_text, group_name,
                                rotation=270, color='blue', ha='center', va=va_align, 
                                fontsize=7, fontweight='normal'
                            )
                        else:
                            y_text = y_min - 0.15 * y_range
                            ax.text(
                                x_text, y_text, group_name,
                                rotation=270, color='blue', ha='center', va='top', 
                                fontsize=7, fontweight='normal'
                            )
            else:
                alternate = False
                for j, (peak_w_exact, peak_val, group_name) in enumerate(sorted_peaks):
                    current_offset = text_offset
                    if j > 0 and abs(peak_w_exact - sorted_peaks[j-1][0]) < 160:
                        if not alternate:
                            current_offset = text_offset + 0.15 * y_range
                            alternate = True
                        else:
                            current_offset = text_offset
                            alternate = False
                    else:
                        alternate = False
                        
                    if space == 'absorbance':
                        y_text = peak_val + current_offset
                        ax.plot([peak_w_exact, peak_w_exact], [peak_val, y_text], color='red', linestyle='--', linewidth=0.6)
                        ax.text(
                            peak_w_exact, y_text + 0.02 * y_range, group_name,
                            rotation=270, color='blue', ha='center', va='bottom', fontsize=7, fontweight='normal'
                        )
                    else:
                        y_text = peak_val - current_offset
                        ax.plot([peak_w_exact, peak_w_exact], [peak_val, y_text], color='red', linestyle='--', linewidth=0.6)
                        ax.text(
                            peak_w_exact, y_text - 0.02 * y_range, group_name,
                            rotation=270, color='blue', ha='center', va='top', fontsize=7, fontweight='normal'
                        )
                    
        plt.tight_layout()
        img_name = f"{output_prefix}_part{chunk_idx + 1}.png"
        plt.savefig(img_name, bbox_inches='tight', dpi=300)
        plt.close()
        print(f"Gallery slice saved to '{img_name}'.")


def plot_superposition(x1, y1_corr, label1, x2, y2_corr, label2, output_image, space='absorbance'):
    """
    Plots a superimposed comparison of two processed spectra.
    """
    space = _map_spanish_params(space)
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "Arial", "Inter", "Liberation Sans"]
    
    fig, ax = plt.subplots(figsize=(10, 6), dpi=300)
    
    ax.plot(x1, y1_corr, color='blue', linewidth=1.2, label=label1)
    ax.plot(x2, y2_corr, color='black', linewidth=1.2, label=label2)
    
    ax.set_xlabel("Número de onda (cm$^{-1}$)", fontsize=13)
    if space == 'absorbance':
        ax.set_ylabel("Absorbancia (u.a.)", fontsize=13)
    else:
        ax.set_ylabel("Transmitancia (u.a.)", fontsize=13)
        
    ax.set_xlim(4000, 400)
    ax.yaxis.set_major_formatter(plt.NullFormatter())
    
    ax.tick_params(axis='both', which='major', labelsize=11, direction='in', length=6, width=1.0)
    ax.tick_params(axis='both', which='minor', direction='in', length=3, width=1.0)
    ax.minorticks_on()
    ax.yaxis.set_minor_locator(plt.NullLocator())
    
    for spine in ax.spines.values():
        spine.set_linewidth(1.0)
        
    ax.legend(loc='upper right' if space == 'absorbance' else 'lower left', 
              frameon=True, edgecolor='black', fontsize=11, framealpha=0.9)
              
    plt.tight_layout()
    plt.savefig(output_image, bbox_inches='tight', dpi=300)
    plt.close()
    print(f"Superposition plot saved to '{output_image}'.")


def generate_numerical_report(x, y_corr, sample_name, output_csv, 
                              prominence_peaks=0.02, prominence_valleys=0.02, distance=15, groups_db=None):
    """
    Detects both peaks and valleys in a baseline-corrected absorbance spectrum,
    maps peaks to functional groups, and exports a unified table to CSV.
    """
    # Peaks (local maxima)
    peak_idx, _ = find_peaks(y_corr, prominence=prominence_peaks, distance=distance)
    
    # Valleys (local minima)
    valley_idx, _ = find_peaks(-y_corr, prominence=prominence_valleys, distance=distance)
    
    report_rows = []
    
    # Map peaks to functional groups
    matched_groups, _ = assign_functional_groups(x[peak_idx], groups_db=groups_db)
    
    # Add peaks
    for idx in peak_idx:
        wavenumber = x[idx]
        val = y_corr[idx]
        
        mapped_group = "None"
        for group, pks in matched_groups.items():
            if wavenumber in pks:
                mapped_group = group
                break
                
        report_rows.append({
            "Type": "Peak",
            "Wavenumber": f"{wavenumber:.2f}",
            "Absorbance": f"{val:.6f}",
            "Mapped_Group": mapped_group
        })
        
    # Add valleys
    for idx in valley_idx:
        wavenumber = x[idx]
        val = y_corr[idx]
        report_rows.append({
            "Type": "Valley",
            "Wavenumber": f"{wavenumber:.2f}",
            "Absorbance": f"{val:.6f}",
            "Mapped_Group": "N/A"
        })
        
    # Sort descending by wavenumber
    report_rows.sort(key=lambda r: float(r["Wavenumber"]), reverse=True)
    
    # Write to CSV
    with open(output_csv, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["Type", "Wavenumber", "Absorbance", "Mapped_Group"])
        writer.writeheader()
        writer.writerows(report_rows)
        
    print(f"Saved numerical report for {sample_name} to '{output_csv}' ({len(report_rows)} entries).")
    return report_rows


def run_raman_grid_search(X, y, folds=5):
    """
    Runs a grid search over Raman preprocessing (smoothing window, baseline correction)
    and Kernel Ridge Classifier parameters (kernel, gamma, alpha).
    """
    from .raman import normalize_spectra, KernelRidgeClassifier
    
    smooth_windows = [3, 5, 7]
    baseline_methods = ['detrend', 'polynomial_baseline']
    kernels = ['linear', 'rbf']
    gammas = [1e-3, 1e-2, 0.1, 1.0]
    alphas = [1e-2, 0.1, 1.0, 10.0]
    
    best_acc = -1
    best_cfg = None
    
    x = np.linspace(100, 4278, 2090)
    
    # Precompute grid
    for window in smooth_windows:
        for base_method in baseline_methods:
            # 1. Preprocess batch
            X_prep = []
            for raw_spec in X:
                s = moving_average(raw_spec, window=window)
                _, c = correct_baseline_absorbance(x, s, method=base_method, deg=2)
                n = normalize_spectra(c, method='vector')
                X_prep.append(n)
            X_prep = np.array(X_prep)
            
            # 2. Test classifiers
            for kernel in kernels:
                kernel_gammas = gammas if kernel == 'rbf' else [1.0]
                for gamma in kernel_gammas:
                    for alpha in alphas:
                        np.random.seed(42)
                        indices = np.arange(X_prep.shape[0])
                        np.random.shuffle(indices)
                        
                        fold_sizes = np.full(folds, X_prep.shape[0] // folds)
                        fold_sizes[:X_prep.shape[0] % folds] += 1
                        
                        current = 0
                        correct = 0
                        
                        for fold in range(folds):
                            start, end = current, current + fold_sizes[fold]
                            test_idx = indices[start:end]
                            train_idx = np.setdiff1d(indices, test_idx)
                            current = end
                            
                            X_train, y_train = X_prep[train_idx], y[train_idx]
                            X_test, y_test = X_prep[test_idx], y[test_idx]
                            
                            clf = KernelRidgeClassifier(kernel=kernel, gamma=gamma, alpha=alpha)
                            clf.fit(X_train, y_train)
                            preds = clf.predict(X_test)
                            correct += np.sum(preds == y_test)
                            
                        acc = correct / X_prep.shape[0]
                        if acc > best_acc:
                            best_acc = acc
                            best_cfg = {
                                "smoothing_window": window,
                                "baseline_method": base_method,
                                "kernel": kernel,
                                "gamma": gamma,
                                "alpha": alpha,
                                "accuracy": acc
                            }
                            
    return best_cfg, best_acc


def plot_raman_pca(X, y, class_map, output_image):
    """
    Applies PCA on preprocessed Raman spectra and plots the 2D score space.
    """
    # Center the data
    mean = np.mean(X, axis=0)
    X_centered = X - mean
    
    # Singular Value Decomposition
    U, S, Vt = np.linalg.svd(X_centered, full_matrices=False)
    scores = U[:, :2] * S[:2]
    var = (S**2) / (X.shape[0] - 1)
    var_ratio = var[:2] / np.sum(var)
    
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "Arial", "Inter", "Liberation Sans"]
    
    fig, ax = plt.subplots(figsize=(8, 6), dpi=300)
    colors = {0: 'red', 1: 'green', 2: 'blue'}
    
    for c in np.unique(y):
        mask = (y == c)
        ax.scatter(
            scores[mask, 0], scores[mask, 1], 
            label=class_map.get(c, f"Class {c}"), 
            color=colors.get(c, 'black'), 
            alpha=0.7, edgecolors='k', s=40
        )
        
    ax.set_xlabel(f"PC1 ({var_ratio[0]*100:.1f}%)", fontsize=11)
    ax.set_ylabel(f"PC2 ({var_ratio[1]*100:.1f}%)", fontsize=11)
    ax.set_title("Espacio de Puntuaciones PCA (Clasificación Raman)", fontsize=12, fontweight='bold', pad=10)
    ax.legend(loc='best', frameon=True, edgecolor='black', fontsize=9)
    ax.grid(True, linestyle='--', alpha=0.5)
    
    plt.tight_layout()
    plt.savefig(output_image, bbox_inches='tight', dpi=300)
    plt.close()
    print(f"PCA score plot saved to '{output_image}'.")


class PipelineResult:
    """
    Unified container for spectral data and grid search results.
    Designed to hide dimensionality and configuration complexity for friendly scripting.
    """
    def __init__(self, x, y, best_config, results, is_raman=False, groups_db=None):
        self.x = x
        self.y = y
        self.best_config = best_config
        self.results = results
        self.is_raman = is_raman
        self.groups_db = groups_db


FTIR = "FTIR"
SERS = "SERS"


def load_data(filepath, format_type=None):
    """
    Loads spectral data from filepath.
    Can manually select format ('FTIR', 'SERS', or 'JCAMP'), or auto-detect by file extension:
    - If format_type is 'SERS' or .csv extension: Loaded as SERS Raman cell spectrum.
    - If format_type is 'JCAMP', 'JDX' or ends with .jdx/.dx extension: Loaded as JCAMP-DX spectrum.
    - Otherwise: Loaded as FTIR transmittance (default txt).
    
    Args:
        filepath (str): Path to the data file.
        format_type (str, optional): 'FTIR', 'SERS', or 'JCAMP'.
        
    Returns:
        x (np.ndarray): Wavenumbers.
        y (np.ndarray): Spectral intensities.
    """
    if format_type is not None:
        if isinstance(format_type, str):
            format_type = format_type.upper()
        if format_type == "SERS":
            # Raman CSV cells spectrum
            raw_data = np.genfromtxt(filepath, delimiter=',', skip_header=1)
            if len(raw_data.shape) > 1:
                y = raw_data[0]
            else:
                y = raw_data
            x = np.linspace(100, 4278, len(y))
            return x, y
        elif format_type == "FTIR":
            return load_ftir_data(filepath)
        elif format_type in ("JCAMP", "JDX", "JCAMP-DX"):
            return load_jcamp_dx(filepath)
        else:
            raise ValueError(f"Unknown format_type: {format_type}. Must be 'FTIR', 'SERS', or 'JCAMP'.")
    else:
        # Auto-detect by extension
        lower_filepath = filepath.lower()
        if lower_filepath.endswith(('.jdx', '.dx')):
            return load_jcamp_dx(filepath)
        elif lower_filepath.endswith('.csv'):
            raw_data = np.genfromtxt(filepath, delimiter=',', skip_header=1)
            if len(raw_data.shape) > 1:
                y = raw_data[0]
            else:
                y = raw_data
            x = np.linspace(100, 4278, len(y))
            return x, y
        else:
            import warnings
            warnings.warn(
                "WARNING: format_type was not explicitly provided to load_data. "
                "Auto-detecting format based on file extension. It is highly recommended "
                "to explicitly specify format_type ('FTIR', 'SERS', or 'JCAMP') to reduce errors.",
                UserWarning
            )
            return load_ftir_data(filepath)


def generate_report(x, y, output_csv=None, space=None, groups_db=None):
    """
    Executes standard pre-processing and peak/valley detection to generate a CSV report.
    Automatically handles FTIR vs Raman differences (such as cosmic rays, normalizations,
    and automatic transmittance-to-absorbance conversion for FTIR).
    
    Args:
        x (np.ndarray): Wavenumbers.
        y (np.ndarray): Raw intensities (transmittance or raw Raman).
        output_csv (str): Output CSV path. Defaults to 'report.csv'.
        space (str, optional): Explicit input space ('transmittance' or 'absorbance').
                               If provided, avoids auto-detection warning.
        groups_db (dict, optional): Custom functional group database.
    """
    space = _map_spanish_params(space)
    is_raman = x[0] < 200.0
    csv_path = output_csv if output_csv is not None else "report.csv"
    
    if is_raman:
        # Raman clinical default preprocessing
        from .raman import remove_cosmic_rays, normalize_spectra
        clean_y = remove_cosmic_rays(y, window=11, threshold=6.0)
        norm_y = normalize_spectra(clean_y, method="vector")
        
        # Optimal combination: Moving Average (5) + poly baseline (deg=2)
        _, y_corr = preprocess_spectrum(x, norm_y, "Moving_Average(5)", "polynomial_baseline(deg=2)", space='absorbance')
        prom = 0.015
        dist = 30
        samp_name = "Raman"
    else:
        # FTIR: Check if y is transmittance, convert to absorbance if so
        if space is not None:
            if isinstance(space, str):
                space = space.lower()
            if space in ("transmittance", "t"):
                y_abs = transmittance_to_absorbance(y)
            elif space in ("absorbance", "a"):
                y_abs = y
            else:
                raise ValueError(f"Unknown space: {space}. Must be 'transmittance' or 'absorbance'.")
        else:
            if np.max(y) > 2.0:
                import warnings
                warnings.warn(
                    "WARNING: Spectral data auto-detected as Transmittance (max y > 2.0). "
                    "Converting to Absorbance. It is highly recommended to explicitly configure "
                    "and pass parameters manually to reduce errors.",
                    UserWarning
                )
                y_abs = transmittance_to_absorbance(y)
            else:
                y_abs = y
            
        # Optimal combination: Percentile(5, 75) + airPLS(lam=1e4)
        _, y_corr = preprocess_spectrum(x, y_abs, "Percentile_Filter(5, 75)", "airpls(lam=1e4)", space='absorbance')
        prom = 0.02
        dist = 15
        samp_name = "FTIR"
        
    return generate_numerical_report(
        x, y_corr, samp_name, csv_path,
        prominence_peaks=prom, prominence_valleys=prom, distance=dist,
        groups_db=groups_db
    )


def run_analysis(x, y, space=None, groups_db=None):
    """
    Runs the 180-combination grid search, returning a PipelineResult.
    Auto-detects FTIR vs Raman to apply the correct databases, constraints,
    and automatic transmittance-to-absorbance conversion for FTIR.
    
    Args:
        x (np.ndarray): Wavenumbers.
        y (np.ndarray): Raw intensities (transmittance or raw Raman).
        space (str, optional): Explicit input space ('transmittance' or 'absorbance').
                               If provided, avoids auto-detection warning.
        groups_db (dict, optional): Custom functional group database.
        
    Returns:
        analysis (PipelineResult): Analysis container.
    """
    space = _map_spanish_params(space)
    is_raman = x[0] < 200.0
    if is_raman:
        from .raman import remove_cosmic_rays, normalize_spectra
        clean_y = remove_cosmic_rays(y, window=11, threshold=6.0)
        norm_y = normalize_spectra(clean_y, method="vector")
        
        # Cells biomarkers database
        if groups_db is None:
            groups_db = {
                "Fosfatos (ADN/ARN)": (1000, 1150),
                "Proteínas/Lípido": (1200, 1400),
                "Amida I": (1550, 1650),
                "Lípidos (C-H)": (2800, 3000)
            }
        best_cfg, results = run_grid_search(
            x, norm_y, space="absorbance", prominence=0.015, distance=30,
            groups_db=groups_db
        )
        return PipelineResult(x, norm_y, best_cfg, results, is_raman=True, groups_db=groups_db)
    else:
        # FTIR: Check if y is transmittance, convert to absorbance if so
        if space is not None:
            if isinstance(space, str):
                space = space.lower()
            if space in ("transmittance", "t"):
                y_abs = transmittance_to_absorbance(y)
            elif space in ("absorbance", "a"):
                y_abs = y
            else:
                raise ValueError(f"Unknown space: {space}. Must be 'transmittance' or 'absorbance'.")
        else:
            if np.max(y) > 2.0:
                import warnings
                warnings.warn(
                    "WARNING: Spectral data auto-detected as Transmittance (max y > 2.0). "
                    "Converting to Absorbance. It is highly recommended to explicitly configure "
                    "and pass parameters manually to reduce errors.",
                    UserWarning
                )
                y_abs = transmittance_to_absorbance(y)
            else:
                y_abs = y
            
        best_cfg, results = run_grid_search(
            x, y_abs, space="absorbance", prominence=0.02, distance=15,
            groups_db=groups_db
        )
        return PipelineResult(x, y_abs, best_cfg, results, is_raman=False, groups_db=groups_db)


def plot_best(analysis, output_image, mode="box", space="absorbance"):
    """
    Plots the best configuration from the PipelineResult.
    
    Args:
        analysis (PipelineResult): Grid search analysis results.
        output_image (str): Output file path.
        mode (str): Mode of peak marking ('lines' or 'box'/'boxes').
        space (str): 'absorbance' or 'transmittance'.
    """
    mode = _map_spanish_params(mode)
    space = _map_spanish_params(space)
    if mode == "boxes":
        mode = "box"
        
    if space == "transmittance" and not getattr(analysis, 'is_raman', False):
        y_plot = 10 ** (2.0 - analysis.y)
    else:
        y_plot = analysis.y
        
    is_raman = getattr(analysis, 'is_raman', False)
    custom_groups = getattr(analysis, 'groups_db', None)
    
    if custom_groups is not None:
        groups_db = custom_groups
        group_order = list(custom_groups.keys())
    elif is_raman:
        groups_db = {
            "Fosfatos (ADN/ARN)": (1000, 1150),
            "Proteínas/Lípidos": (1200, 1400),
            "Amida I": (1550, 1650),
            "Lípidos (C-H)": (2800, 3000)
        }
        group_order = list(groups_db.keys())
    else:
        groups_db = None
        group_order = None
        
    prom = 0.015 if is_raman else (0.02 if space == "absorbance" else 0.8)
    dist = 30 if is_raman else 15
    inv_x = not is_raman
    
    plot_best_configuration(
        analysis.x, y_plot, analysis.best_config, output_image,
        space=space, prominence=prom, distance=dist, mode=mode,
        groups_db=groups_db, group_order=group_order, invert_x=inv_x
    )


def plot_gallery(analysis, output_prefix, max_plots=9, mode="box", space="absorbance"):
    """
    Plots horizontal 3x1 configuration galleries of top configurations.
    
    Args:
        analysis (PipelineResult): Grid search analysis results.
        output_prefix (str): Image filename prefix.
        max_plots (int): Maximum number of configurations to plot.
        mode (str): Mode of peak marking ('lines' or 'box'/'boxes').
        space (str): 'absorbance' or 'transmittance'.
    """
    mode = _map_spanish_params(mode)
    space = _map_spanish_params(space)
    if mode == "boxes":
        mode = "box"
        
    if space == "transmittance" and not getattr(analysis, 'is_raman', False):
        y_plot = 10 ** (2.0 - analysis.y)
    else:
        y_plot = analysis.y
        
    is_raman = getattr(analysis, 'is_raman', False)
    custom_groups = getattr(analysis, 'groups_db', None)
    
    if custom_groups is not None:
        groups_db = custom_groups
        group_order = list(custom_groups.keys())
    elif is_raman:
        groups_db = {
            "Fosfatos (ADN/ARN)": (1000, 1150),
            "Proteínas/Lípidos": (1200, 1400),
            "Amida I": (1550, 1650),
            "Lípidos (C-H)": (2800, 3000)
        }
        group_order = list(groups_db.keys())
    else:
        groups_db = None
        group_order = None
        
    prom = 0.015 if is_raman else (0.02 if space == "absorbance" else 0.8)
    dist = 30 if is_raman else 15
    inv_x = not is_raman
    
    plot_gallery_3x1(
        analysis.x, y_plot, analysis.results, output_prefix,
        space=space, prominence=prom, distance=dist, max_total_plots=max_plots,
        mode=mode, groups_db=groups_db, group_order=group_order, invert_x=inv_x
    )


def get_approved_count(analysis):
    """
    Returns the number of successful/approved configurations in the grid search.
    """
    if not analysis.results:
        return 0
    max_groups = max(int(r["N_Groups_Detected"]) for r in analysis.results)
    gallery_configs = [c for c in analysis.results if int(c["N_Groups_Detected"]) == max_groups]
    gallery_configs = [c for c in gallery_configs if c["Baseline"] != "RAW"]
    return len(gallery_configs)


get_approvednumber = get_approved_count

