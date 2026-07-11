"""
FTIR Absorbance Grid Search & Plotting Pipeline
-----------------------------------------------
Converts transmittance to absorbance and runs grid searches of 180 combinations
for both rGO and GO. Generates:
1. absorbance_pipeline_results_[rGO/GO].csv
2. absorbance_result_best_[rGO/GO].png
3. absorbance_result_gallery_[rGO/GO].png
"""

import os
import csv
import numpy as np
import matplotlib.pyplot as plt

# Import from installed library
from ftir_library import (
    load_ftir_data,
    transmittance_to_absorbance,
    moving_average,
    savitzky_golay,
    median_filter,
    percentile_filter,
    correct_baseline_absorbance,
    detect_peaks_absorbance,
    assign_functional_groups,
    calculate_pipeline_score,
    DEFAULT_FUNCTIONAL_GROUPS
)

# Input files in local examples directory
RGO_FILE = "GO coque s lav red.txt"
GO_FILE = "GO coque s lav ox.txt"

# Prominence in absorbance space (absorbance scale, typical range 0.0 to ~2.0)
PROMINENCE = 0.02
DISTANCE = 15

# Configurations
SMOOTHING_CONFIGS = [
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

BASELINE_CONFIGS = [
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


def parse_config_params(label):
    """Parses configuration names and parameters from labels."""
    label = label.strip()
    if label == "RAW":
        return "raw", {}
        
    if "(" in label and ")" in label:
        name = label.split("(")[0].strip()
        param_str = label.split("(")[1].split(")")[0].strip()
        
        # Parse parameters
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


def parse_num(s):
    try:
        val = float(s)
        if val.is_integer():
            return int(val)
        return val
    except ValueError:
        return s


def run_pipeline(input_file, sample_name):
    print(f"\n==========================================")
    print(f"PROCESSING SAMPLE: {sample_name} ({input_file})")
    print(f"==========================================")
    
    x, y_trans = load_ftir_data(input_file)
    y_abs = transmittance_to_absorbance(y_trans)
    
    results = []
    
    for smooth_cfg in SMOOTHING_CONFIGS:
        y_smoothed = smooth_cfg["func"](y_abs)
        for base_cfg in BASELINE_CONFIGS:
            try:
                z, y_corrected = correct_baseline_absorbance(
                    x, y_smoothed,
                    method=base_cfg["method"],
                    **base_cfg["kwargs"]
                )
                indices, peak_x, peak_y = detect_peaks_absorbance(x, y_corrected, prominence=PROMINENCE, distance=DISTANCE)
                matched_groups, noise_peaks = assign_functional_groups(peak_x)
                
                score_std = calculate_pipeline_score(peak_x, matched_groups, noise_peaks, noise_penalty_weight=1.0)
                score_pen = calculate_pipeline_score(peak_x, matched_groups, noise_peaks, noise_penalty_weight=2.0)
                
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
                
    # Save to CSV
    csv_file = f"absorbance_pipeline_results_{sample_name}.csv"
    print(f"Saving results to '{csv_file}'...")
    with open(csv_file, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            "Smoothing", "Baseline", "N_Groups_Detected", 
            "Detected_Groups", "N_Peaks_Detected", 
            "N_Noise_Peaks", "Score_Std", "Score_Penalized"
        ])
        writer.writeheader()
        writer.writerows(results)
        
    # Find best config by penalized score - EXCLUDING RAW baseline
    filtered_results = [r for r in results if r["Baseline"] != "RAW"]
    if not filtered_results:
        # Fallback to all results if all were somehow raw (which isn't the case)
        filtered_results = results
        
    best_cfg = max(filtered_results, key=lambda r: (r["Score_Penalized"], r["N_Groups_Detected"], -r["N_Noise_Peaks"]))
    print(f"Best configuration (excluding RAW) for {sample_name}: {best_cfg['Smoothing']} + {best_cfg['Baseline']}")
    
    # Save best config text
    cfg_text_file = f"best_config_absorbance_{sample_name}.txt"
    with open(cfg_text_file, "w", encoding='utf-8') as f:
        f.write(f"Smoothing: {best_cfg['Smoothing']}\n")
        f.write(f"Baseline: {best_cfg['Baseline']}\n")
        
    return x, y_abs, best_cfg, results


def plot_best(x, y_abs, best_cfg, sample_name):
    smooth_label = best_cfg["Smoothing"]
    base_label = best_cfg["Baseline"]
    
    # Apply preprocessing
    smooth_name, smooth_params = parse_config_params(smooth_label)
    if smooth_name == "raw":
        y_smoothed = y_abs.copy()
    elif "Moving_Average" in smooth_label:
        y_smoothed = moving_average(y_abs, window=smooth_params.get("window", 5))
    elif "Savitzky_Golay" in smooth_label:
        y_smoothed = savitzky_golay(y_abs, window=smooth_params.get("window", 11), poly=smooth_params.get("poly", 2))
    elif "Median_Filter" in smooth_label:
        y_smoothed = median_filter(y_abs, window=smooth_params.get("window", 5))
    elif "Percentile_Filter" in smooth_label:
        pct = smooth_params.get("percentile", 50)
        if "percentile" not in smooth_params and "poly" in smooth_params:
            pct = smooth_params["poly"]
        y_smoothed = percentile_filter(y_abs, window=smooth_params.get("window", 5), percentile=pct)
    else:
        y_smoothed = y_abs.copy()
        
    base_name, base_params = parse_config_params(base_label)
    z, y_corrected = correct_baseline_absorbance(x, y_smoothed, method=base_name, **base_params)
    
    # Detect peaks
    indices, peak_x, peak_y = detect_peaks_absorbance(x, y_corrected, prominence=PROMINENCE, distance=DISTANCE)
    matched_groups, noise_peaks = assign_functional_groups(peak_x)
    
    # Plotting
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "Arial", "Inter", "Liberation Sans"]
    
    fig, ax = plt.subplots(figsize=(10, 7), dpi=300)
    ax.plot(x, y_corrected, color='black', linewidth=1.0)
    
    ax.set_xlabel("Número de onda (cm$^{-1}$)", fontsize=13)
    ax.set_ylabel("Absorbância (u.a.)", fontsize=13)
    ax.set_xlim(4000, 400)
    
    y_min, y_max = np.min(y_corrected), np.max(y_corrected)
    y_range = y_max - y_min if y_max > y_min else 1.0
    ax.set_ylim(y_min - 0.05 * y_range, y_max + 0.40 * y_range) # Increased overhead space
    
    ax.yaxis.set_major_formatter(plt.NullFormatter())
    ax.tick_params(axis='both', which='major', labelsize=11, direction='in', length=6, width=1.0)
    ax.tick_params(axis='both', which='minor', direction='in', length=3, width=1.0)
    ax.minorticks_on()
    ax.yaxis.set_minor_locator(plt.NullLocator())
    
    # Collision avoidance text labeling logic
    group_order = ["O-H", "C-H", "CO2", "C=O", "C=C", "C-O", "C-O-C"]
    text_offset = 0.10 * y_range
    
    sorted_peaks = []
    for group_name in group_order:
        if group_name not in matched_groups:
            w_min, w_max = DEFAULT_FUNCTIONAL_GROUPS[group_name]
            mask = (x >= w_min) & (x <= w_max)
            if np.any(mask):
                max_idx = np.argmax(y_corrected[mask])
                peak_w = x[mask][max_idx]
                peak_t = y_corrected[mask][max_idx]
                if peak_t > 0.01:
                    matched_groups[group_name] = [peak_w]
                    
        if group_name in matched_groups:
            peak_w = matched_groups[group_name][0]
            idx = np.abs(x - peak_w).argmin()
            sorted_peaks.append((x[idx], y_corrected[idx], group_name))
            
    # Sort from left to right (high wavenumber to low)
    sorted_peaks.sort(key=lambda item: item[0], reverse=True)
    
    alternate = False
    for i, (peak_w_exact, peak_t, group_name) in enumerate(sorted_peaks):
        current_offset = text_offset
        # If too close to the previous peak in X (e.g. less than 160 cm^-1), alternate height
        if i > 0 and abs(peak_w_exact - sorted_peaks[i-1][0]) < 160:
            if not alternate:
                current_offset = text_offset + 0.15 * y_range
                alternate = True
            else:
                current_offset = text_offset
                alternate = False
        else:
            alternate = False
            
        y_text = peak_t + current_offset
        ax.plot([peak_w_exact, peak_w_exact], [peak_t, y_text], color='red', linestyle='--', linewidth=1.0)
        
        ax.text(
            peak_w_exact, 
            y_text + 0.02 * y_range, 
            group_name, 
            rotation=270, 
            color='blue', 
            ha='center', 
            va='bottom', 
            fontsize=12, 
            fontweight='bold'
        )
        
    plt.tight_layout()
    img_name = f"absorbance_result_best_{sample_name}.png"
    plt.savefig(img_name, bbox_inches='tight', dpi=300)
    print(f"Best plot saved to '{img_name}'.")
    plt.close()


def plot_gallery(x, y_abs, results, sample_name):
    max_groups = max(int(r["N_Groups_Detected"]) for r in results)
    gallery_configs = [c for c in results if int(c["N_Groups_Detected"]) == max_groups]
    
    # Exclude configurations using RAW baseline from the gallery to keep focus on correctable spectra
    gallery_configs = [c for c in gallery_configs if c["Baseline"] != "RAW"]
    n_plots = len(gallery_configs)
    
    if n_plots == 0:
        print(f"No matching configurations for {sample_name} gallery.")
        return
        
    gallery_configs.sort(key=lambda c: (float(c["Score_Penalized"]), -float(c["N_Noise_Peaks"])), reverse=True)
    
    if n_plots > 15:
        gallery_configs = gallery_configs[:15]
        n_plots = 15
        
    n_cols = 3
    n_rows = int(np.ceil(n_plots / n_cols))
    
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(12.5, 3.2 * n_rows), dpi=300)
    axes_flat = axes.flatten()
    
    for i, cfg in enumerate(gallery_configs):
        ax = axes_flat[i]
        smooth_label = cfg["Smoothing"]
        base_label = cfg["Baseline"]
        
        # Apply preprocessing
        smooth_name, smooth_params = parse_config_params(smooth_label)
        if smooth_name == "raw":
            y_smoothed = y_abs.copy()
        elif "Moving_Average" in smooth_label:
            y_smoothed = moving_average(y_abs, window=smooth_params.get("window", 5))
        elif "Savitzky_Golay" in smooth_label:
            y_smoothed = savitzky_golay(y_abs, window=smooth_params.get("window", 11), poly=smooth_params.get("poly", 2))
        elif "Median_Filter" in smooth_label:
            y_smoothed = median_filter(y_abs, window=smooth_params.get("window", 5))
        elif "Percentile_Filter" in smooth_label:
            pct = smooth_params.get("percentile", 50)
            if "percentile" not in smooth_params and "poly" in smooth_params:
                pct = smooth_params["poly"]
            y_smoothed = percentile_filter(y_abs, window=smooth_params.get("window", 5), percentile=pct)
        else:
            y_smoothed = y_abs.copy()
            
        base_name, base_params = parse_config_params(base_label)
        z, y_corrected = correct_baseline_absorbance(x, y_smoothed, method=base_name, **base_params)
        
        # Detect peaks
        indices, peak_x, peak_y = detect_peaks_absorbance(x, y_corrected, prominence=PROMINENCE, distance=DISTANCE)
        matched_groups, noise_peaks = assign_functional_groups(peak_x)
        
        # Plot
        ax.plot(x, y_corrected, color='black', linewidth=0.8)
        ax.set_xlim(4000, 400)
        
        y_min, y_max = np.min(y_corrected), np.max(y_corrected)
        y_range = y_max - y_min if y_max > y_min else 1.0
        ax.set_ylim(y_min - 0.05 * y_range, y_max + 0.45 * y_range)
        
        ax.set_title(f"{smooth_label}\n+ {base_label}", fontsize=8, fontweight='bold', pad=4)
        ax.yaxis.set_major_formatter(plt.NullFormatter())
        ax.tick_params(axis='both', which='major', labelsize=8, direction='in', length=4, width=0.8)
        ax.tick_params(axis='both', which='minor', direction='in', length=2, width=0.8)
        ax.minorticks_on()
        ax.yaxis.set_minor_locator(plt.NullLocator())
        
        if i >= n_plots - n_cols:
            ax.set_xlabel("Número de onda (cm$^{-1}$)", fontsize=8)
        else:
            ax.set_xticklabels([])
            
        # Label groups with collision avoidance
        group_order = ["O-H", "C-H", "CO2", "C=O", "C=C", "C-O", "C-O-C"]
        text_offset = 0.12 * y_range
        
        sorted_peaks = []
        for group_name in group_order:
            if group_name not in matched_groups:
                w_min, w_max = DEFAULT_FUNCTIONAL_GROUPS[group_name]
                mask = (x >= w_min) & (x <= w_max)
                if np.any(mask):
                    max_idx = np.argmax(y_corrected[mask])
                    peak_w = x[mask][max_idx]
                    peak_t = y_corrected[mask][max_idx]
                    if peak_t > 0.01:
                        matched_groups[group_name] = [peak_w]
                        
            if group_name in matched_groups:
                peak_w = matched_groups[group_name][0]
                idx = np.abs(x - peak_w).argmin()
                sorted_peaks.append((x[idx], y_corrected[idx], group_name))
                
        sorted_peaks.sort(key=lambda item: item[0], reverse=True)
        
        alternate = False
        for j, (peak_w_exact, peak_t, group_name) in enumerate(sorted_peaks):
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
                
            y_text = peak_t + current_offset
            ax.plot([peak_w_exact, peak_w_exact], [peak_t, y_text], color='red', linestyle='--', linewidth=0.6)
            
            ax.text(
                peak_w_exact, 
                y_text + 0.02 * y_range, 
                group_name, 
                rotation=270, 
                color='blue', 
                ha='center', 
                va='bottom', 
                fontsize=7, 
                fontweight='normal'
            )
            
    # Hide unused axes
    for j in range(n_plots, len(axes_flat)):
        axes_flat[j].axis('off')
        
    plt.tight_layout()
    img_name = f"absorbance_result_gallery_{sample_name}.png"
    plt.savefig(img_name, bbox_inches='tight', dpi=300)
    print(f"Gallery plot saved to '{img_name}'.")
    plt.close()


def main():
    # 1. Process rGO
    x_rgo, y_rgo, best_rgo, results_rgo = run_pipeline(RGO_FILE, "rGO")
    plot_best(x_rgo, y_rgo, best_rgo, "rGO")
    plot_gallery(x_rgo, y_rgo, results_rgo, "rGO")
    
    # 2. Process GO
    x_go, y_go, best_go, results_go = run_pipeline(GO_FILE, "GO")
    plot_best(x_go, y_go, best_go, "GO")
    plot_gallery(x_go, y_go, results_go, "GO")


if __name__ == "__main__":
    main()
