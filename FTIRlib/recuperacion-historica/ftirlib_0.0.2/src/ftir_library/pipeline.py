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
    smooth_name, smooth_params = parse_config_params(smooth_label)
    if smooth_name == "raw":
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
    base_name, base_params = parse_config_params(base_label)
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
    return apply_baseline(x, y_smoothed, base_label, space=space)


def run_grid_search(x, y, output_csv=None, best_config_txt=None, space='absorbance', 
                    prominence=0.02, distance=15, noise_penalty_weight=2.0,
                    smoothing_configs=None, baseline_configs=None):
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
        
    Returns:
        best_config (dict): The highest scoring configuration details
        results (list): List of dicts for all configurations executed
    """
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
                    
                matched_groups, noise_peaks = assign_functional_groups(peak_x)
                
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


def plot_best_configuration(x, y, best_cfg, output_image, space='absorbance', prominence=0.02, distance=15):
    """
    Plots the best baseline-corrected spectrum with functional groups annotated.
    Includes collision avoidance for labels.
    """
    smooth_label = best_cfg["Smoothing"]
    base_label = best_cfg["Baseline"]
    
    # Preprocess
    z, y_corrected = preprocess_spectrum(x, y, smooth_label, base_label, space=space)
    
    # Detect peaks
    if space == 'absorbance':
        indices, peak_x, peak_y = detect_peaks_absorbance(x, y_corrected, prominence=prominence, distance=distance)
    else:
        indices, peak_x, peak_y = detect_peaks_transmittance(x, y_corrected, prominence=prominence, distance=distance)
        
    matched_groups, noise_peaks = assign_functional_groups(peak_x)
    
    # Set up plot styling
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "Arial", "Inter", "Liberation Sans"]
    
    fig, ax = plt.subplots(figsize=(10, 7), dpi=300)
    ax.plot(x, y_corrected, color='black', linewidth=1.0)
    
    ax.set_xlabel("Número de onda (cm$^{-1}$)", fontsize=13)
    if space == 'absorbance':
        ax.set_ylabel("Absorbância (u.a.)", fontsize=13)
    else:
        ax.set_ylabel("Transmitância (u.a.)", fontsize=13)
        
    ax.set_xlim(4000, 400)
    
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
    
    # Labeling logic
    group_order = ["O-H", "C-H", "CO2", "C=O", "C=C", "C-O", "C-O-C"]
    
    sorted_peaks = []
    for group_name in group_order:
        if group_name not in matched_groups:
            # Fallback scan for peak in range
            w_min, w_max = DEFAULT_FUNCTIONAL_GROUPS[group_name]
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
            
    # Sort left to right (high wavenumber to low)
    sorted_peaks.sort(key=lambda item: item[0], reverse=True)
    
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


def plot_gallery_3x1(x, y, results, output_prefix, space='absorbance', prominence=0.02, distance=15, max_total_plots=15):
    """
    Plots the best performing configurations as multiple 3x1 images (3 horizontal subplots in one row per file).
    This keeps the resolution high and prevents document truncation or page-overflow.
    """
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
                
            matched_groups, noise_peaks = assign_functional_groups(peak_x)
            
            # Plot
            ax.plot(x, y_corrected, color='black', linewidth=0.8)
            ax.set_xlim(4000, 400)
            
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
            group_order = ["O-H", "C-H", "CO2", "C=O", "C=C", "C-O", "C-O-C"]
            text_offset = 0.12 * y_range if space == 'absorbance' else 0.15 * y_range
            
            sorted_peaks = []
            for group_name in group_order:
                if group_name not in matched_groups:
                    w_min, w_max = DEFAULT_FUNCTIONAL_GROUPS[group_name]
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
                    
            sorted_peaks.sort(key=lambda item: item[0], reverse=True)
            
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
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "Arial", "Inter", "Liberation Sans"]
    
    fig, ax = plt.subplots(figsize=(10, 6), dpi=300)
    
    ax.plot(x1, y1_corr, color='blue', linewidth=1.2, label=label1)
    ax.plot(x2, y2_corr, color='black', linewidth=1.2, label=label2)
    
    ax.set_xlabel("Número de onda (cm$^{-1}$)", fontsize=13)
    if space == 'absorbance':
        ax.set_ylabel("Absorbância (u.a.)", fontsize=13)
    else:
        ax.set_ylabel("Transmitância (u.a.)", fontsize=13)
        
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
                              prominence_peaks=0.02, prominence_valleys=0.02, distance=15):
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
    matched_groups, _ = assign_functional_groups(x[peak_idx])
    
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
