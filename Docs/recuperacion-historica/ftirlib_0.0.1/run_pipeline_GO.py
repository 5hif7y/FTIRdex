"""
FTIR Grid Search & Plotting Pipeline (GO)
-----------------------------------------
Runs combinations of smoothing and baseline correction algorithms on unwashed Graphene Oxide data,
calculates scores, outputs results to a CSV, and generates:
1. resultado_bestGO.png (and outcome copy resultado_best_GO.png)
2. resultado_galeriaGO.png (and outcome copy resultado_galeria_GO.png)
"""

import os
import csv
import shutil
import numpy as np
import matplotlib.pyplot as plt
from ftir_library import (
    load_ftir_data,
    moving_average,
    savitzky_golay,
    median_filter,
    percentile_filter,
    correct_baseline_transmittance,
    detect_peaks_transmittance,
    assign_functional_groups,
    calculate_pipeline_score,
    DEFAULT_FUNCTIONAL_GROUPS
)
from plot_best import parse_config_params

# Input & Output files
INPUT_FILE = "GO coque s lav ox.txt"
OUTPUT_CSV = "pipeline_results_GO.csv"
BEST_CONFIG_FILE = "best_config_GO.txt"

# Single best plot names
BEST_IMG = "resultado_bestGO.png"
BEST_IMG_ALT = "resultado_best_GO.png"

# Gallery plot names
GAL_IMG = "resultado_galeriaGO.png"
GAL_IMG_ALT = "resultado_galeria_GO.png"

# Configuration of smoothing algorithms (12 total)
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

# Configuration of baseline correction algorithms (15 total)
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

# Peak detection parameters
PROMINENCE = 0.8
DISTANCE = 15

def run_grid_search_go():
    if not os.path.exists(INPUT_FILE):
        print(f"Error: Input file '{INPUT_FILE}' not found.")
        return
        
    print(f"Loading Graphene Oxide (GO) spectrum from {INPUT_FILE}...")
    x, y = load_ftir_data(INPUT_FILE)
    print(f"Loaded {len(x)} data points. Range: {x[0]:.2f} to {x[-1]:.2f} cm^-1.")
    
    results = []
    
    print("\nRunning grid search of 180 combinations for GO...")
    for smooth_cfg in SMOOTHING_CONFIGS:
        y_smoothed = smooth_cfg["func"](y)
        for base_cfg in BASELINE_CONFIGS:
            try:
                z, y_corrected = correct_baseline_transmittance(
                    x, y_smoothed, 
                    method=base_cfg["method"], 
                    **base_cfg["kwargs"]
                )
                indices, peak_x, peak_y = detect_peaks_transmittance(x, y_corrected, prominence=PROMINENCE, distance=DISTANCE)
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
    print(f"Saving results to '{OUTPUT_CSV}'...")
    with open(OUTPUT_CSV, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            "Smoothing", "Baseline", "N_Groups_Detected", 
            "Detected_Groups", "N_Peaks_Detected", 
            "N_Noise_Peaks", "Score_Std", "Score_Penalized"
        ])
        writer.writeheader()
        writer.writerows(results)
        
    # Find best config
    best_by_pen = max(results, key=lambda r: (r["Score_Penalized"], r["N_Groups_Detected"], -r["N_Noise_Peaks"]))
    print(f"Best configuration by Penalized Score: {best_by_pen['Smoothing']} + {best_by_pen['Baseline']}")
    
    with open(BEST_CONFIG_FILE, "w", encoding='utf-8') as f:
        f.write(f"Smoothing: {best_by_pen['Smoothing']}\n")
        f.write(f"Baseline: {best_by_pen['Baseline']}\n")
        
    return x, y, best_by_pen, results


def plot_best_go(x, y, best_cfg):
    smooth_label = best_cfg["Smoothing"]
    base_label = best_cfg["Baseline"]
    
    # 1. Apply Smoothing
    smooth_name, smooth_params = parse_config_params(smooth_label)
    if smooth_name == "raw":
        y_smoothed = y.copy()
    elif "Moving_Average" in smooth_label:
        y_smoothed = moving_average(y, window=smooth_params.get("window", 5))
    elif "Savitzky_Golay" in smooth_label:
        y_smoothed = savitzky_golay(y, window=smooth_params.get("window", 11), poly=smooth_params.get("poly", 2))
    elif "Median_Filter" in smooth_label:
        y_smoothed = median_filter(y, window=smooth_params.get("window", 5))
    elif "Percentile_Filter" in smooth_label:
        pct = smooth_params.get("percentile", 50)
        if "percentile" not in smooth_params and "poly" in smooth_params:
            pct = smooth_params["poly"]
        y_smoothed = percentile_filter(y, window=smooth_params.get("window", 5), percentile=pct)
    else:
        y_smoothed = y.copy()
        
    # 2. Apply Baseline Correction
    base_name, base_params = parse_config_params(base_label)
    z, y_corrected = correct_baseline_transmittance(x, y_smoothed, method=base_name, **base_params)
    
    # 3. Detect Peaks & Assign
    indices, peak_x, peak_y = detect_peaks_transmittance(x, y_corrected, prominence=PROMINENCE, distance=DISTANCE)
    matched_groups, noise_peaks = assign_functional_groups(peak_x)
    
    # Plotting (Styling matching pedido.png)
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "Arial", "Inter", "Liberation Sans"]
    
    fig, ax = plt.subplots(figsize=(10, 7), dpi=300)
    ax.plot(x, y_corrected, color='black', linewidth=1.0)
    
    ax.set_xlabel("Número de onda (cm$^{-1}$)", fontsize=13)
    ax.set_ylabel("Transmitância (u.a.)", fontsize=13)
    ax.set_xlim(4000, 400)
    
    y_min, y_max = np.min(y_corrected), np.max(y_corrected)
    y_range = y_max - y_min
    ax.set_ylim(y_min - 0.35 * y_range, y_max + 0.05 * y_range)
    ax.yaxis.set_major_formatter(plt.NullFormatter())
    
    ax.tick_params(axis='both', which='major', labelsize=11, direction='in', length=6, width=1.0)
    ax.tick_params(axis='both', which='minor', direction='in', length=3, width=1.0)
    ax.minorticks_on()
    ax.yaxis.set_minor_locator(plt.NullLocator())
    
    # Label groups
    group_order = ["O-H", "C-H", "CO2", "C=O", "C=C", "C-O", "C-O-C"]
    text_offset = 0.12 * y_range
    
    for group_name in group_order:
        if group_name not in matched_groups:
            # Fallback
            w_min, w_max = DEFAULT_FUNCTIONAL_GROUPS[group_name]
            mask = (x >= w_min) & (x <= w_max)
            if np.any(mask):
                min_idx = np.argmin(y_corrected[mask])
                peak_w = x[mask][min_idx]
                peak_t = y_corrected[mask][min_idx]
                if peak_t < 99.5:
                    matched_groups[group_name] = [peak_w]
                else:
                    continue
            else:
                continue
                
        peak_w = matched_groups[group_name][0]
        idx = np.abs(x - peak_w).argmin()
        peak_w_exact = x[idx]
        peak_t = y_corrected[idx]
        
        # Red vertical dashed line
        y_text = peak_t - text_offset
        ax.plot([peak_w_exact, peak_w_exact], [peak_t, y_text], color='red', linestyle='--', linewidth=1.0)
        
        # Blue vertical text label
        ax.text(
            peak_w_exact, 
            y_text - 0.02 * y_range, 
            group_name, 
            rotation=270, 
            color='blue', 
            ha='center', 
            va='top', 
            fontsize=12, 
            fontweight='bold'
        )
        
    plt.tight_layout()
    plt.savefig(BEST_IMG, bbox_inches='tight', dpi=300)
    shutil.copy(BEST_IMG, BEST_IMG_ALT)
    print(f"Best GO plot saved as '{BEST_IMG}' (and '{BEST_IMG_ALT}').")
    plt.close()


def plot_gallery_go(x, y, results):
    max_groups = max(int(r["N_Groups_Detected"]) for r in results)
    gallery_configs = [c for c in results if int(c["N_Groups_Detected"]) == max_groups]
    n_plots = len(gallery_configs)
    
    if n_plots == 0:
        print("No configurations found for GO gallery.")
        return
        
    gallery_configs.sort(key=lambda c: (float(c["Score_Penalized"]), -float(c["N_Noise_Peaks"])), reverse=True)
    
    n_cols = 3
    n_rows = int(np.ceil(n_plots / n_cols))
    
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(12.5, 3.2 * n_rows), dpi=300)
    axes_flat = axes.flatten() if n_plots > 1 else [axes]
    
    for i, cfg in enumerate(gallery_configs):
        ax = axes_flat[i]
        smooth_label = cfg["Smoothing"]
        base_label = cfg["Baseline"]
        
        # 1. Apply Smoothing
        smooth_name, smooth_params = parse_config_params(smooth_label)
        if smooth_name == "raw":
            y_smoothed = y.copy()
        elif "Moving_Average" in smooth_label:
            y_smoothed = moving_average(y, window=smooth_params.get("window", 5))
        elif "Savitzky_Golay" in smooth_label:
            y_smoothed = savitzky_golay(y, window=smooth_params.get("window", 11), poly=smooth_params.get("poly", 2))
        elif "Median_Filter" in smooth_label:
            y_smoothed = median_filter(y, window=smooth_params.get("window", 5))
        elif "Percentile_Filter" in smooth_label:
            pct = smooth_params.get("percentile", 50)
            if "percentile" not in smooth_params and "poly" in smooth_params:
                pct = smooth_params["poly"]
            y_smoothed = percentile_filter(y, window=smooth_params.get("window", 5), percentile=pct)
        else:
            y_smoothed = y.copy()
            
        # 2. Apply Baseline Correction
        base_name, base_params = parse_config_params(base_label)
        z, y_corrected = correct_baseline_transmittance(x, y_smoothed, method=base_name, **base_params)
        
        # 3. Detect peaks & assign
        indices, peak_x, peak_y = detect_peaks_transmittance(x, y_corrected, prominence=PROMINENCE, distance=DISTANCE)
        matched_groups, noise_peaks = assign_functional_groups(peak_x)
        
        # 4. Plot
        ax.plot(x, y_corrected, color='black', linewidth=0.8)
        ax.set_xlim(4000, 400)
        y_min, y_max = np.min(y_corrected), np.max(y_corrected)
        y_range = y_max - y_min
        ax.set_ylim(y_min - 0.4 * y_range, y_max + 0.05 * y_range)
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
            
        group_order = ["O-H", "C-H", "CO2", "C=O", "C=C", "C-O", "C-O-C"]
        text_offset = 0.15 * y_range
        
        for group_name in group_order:
            if group_name not in matched_groups:
                w_min, w_max = DEFAULT_FUNCTIONAL_GROUPS[group_name]
                mask = (x >= w_min) & (x <= w_max)
                if np.any(mask):
                    min_idx = np.argmin(y_corrected[mask])
                    peak_w = x[mask][min_idx]
                    peak_t = y_corrected[mask][min_idx]
                    if peak_t < 99.5:
                        matched_groups[group_name] = [peak_w]
                    else:
                        continue
                else:
                    continue
                    
            peak_w = matched_groups[group_name][0]
            idx = np.abs(x - peak_w).argmin()
            peak_w_exact = x[idx]
            peak_t = y_corrected[idx]
            
            y_text = peak_t - text_offset
            ax.plot([peak_w_exact, peak_w_exact], [peak_t, y_text], color='red', linestyle='--', linewidth=0.6)
            
            ax.text(
                peak_w_exact, 
                y_text - 0.02 * y_range, 
                group_name, 
                rotation=270, 
                color='blue', 
                ha='center', 
                va='top', 
                fontsize=7, 
                fontweight='normal'
            )
            
    # Hide unused axes
    for j in range(n_plots, len(axes_flat)):
        axes_flat[j].axis('off')
        
    plt.tight_layout()
    plt.savefig(GAL_IMG, bbox_inches='tight', dpi=300)
    shutil.copy(GAL_IMG, GAL_IMG_ALT)
    print(f"GO gallery plot saved as '{GAL_IMG}' (and '{GAL_IMG_ALT}').")
    plt.close()


def main():
    x, y, best_cfg, results = run_grid_search_go()
    plot_best_go(x, y, best_cfg)
    plot_gallery_go(x, y, results)


if __name__ == "__main__":
    main()
