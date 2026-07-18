"""
FTIR Gallery Plotting Script (rGO)
----------------------------------
Loads pipeline results, filters for configurations matching the maximum
number of detected functional groups, and plots them in a 3-column grid (A4 layout).
"""

import os
import csv
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
    DEFAULT_FUNCTIONAL_GROUPS
)
from plot_best import parse_config_params

# Files
INPUT_FILE = "GO coque s lav red.txt"
RESULTS_CSV = "pipeline_results.csv"
OUTPUT_IMAGE = "resultado_galeria_rGO.png"

def main():
    if not os.path.exists(INPUT_FILE) or not os.path.exists(RESULTS_CSV):
        print(f"Error: Required files '{INPUT_FILE}' or '{RESULTS_CSV}' not found.")
        return
        
    # Load raw data
    x, y = load_ftir_data(INPUT_FILE)
    
    # Read CSV and find configurations with the maximum groups detected
    configs = []
    max_groups = 0
    
    with open(RESULTS_CSV, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            n_groups = int(row["N_Groups_Detected"])
            configs.append(row)
            if n_groups > max_groups:
                max_groups = n_groups
                
    # Filter configurations with max groups
    gallery_configs = [c for c in configs if int(c["N_Groups_Detected"]) == max_groups]
    n_plots = len(gallery_configs)
    
    print(f"Found {n_plots} configurations with the maximum of {max_groups} groups detected.")
    if n_plots == 0:
        print("No configurations match. Exiting.")
        return
        
    # Sort them by penalized score and then by fewer noise peaks
    gallery_configs.sort(key=lambda c: (float(c["Score_Penalized"]), -float(c["N_Noise_Peaks"])), reverse=True)
    
    # Setup grid layout: 3 columns, rows depending on count
    n_cols = 3
    n_rows = int(np.ceil(n_plots / n_cols))
    
    # Set up matplotlib font settings
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "Arial", "Inter", "Liberation Sans"]
    
    # Create figure (A4 friendly size: 11.69 x 8.27 in landscape or similar)
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(12.5, 3.2 * n_rows), dpi=300)
    
    # Flatten axes array for easy iteration
    axes_flat = axes.flatten() if n_plots > 1 else [axes]
    
    # Peak detection parameters
    PROMINENCE = 0.8
    DISTANCE = 15
    
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
        
        # 3. Detect peaks
        indices, peak_x, peak_y = detect_peaks_transmittance(x, y_corrected, prominence=PROMINENCE, distance=DISTANCE)
        matched_groups, noise_peaks = assign_functional_groups(peak_x)
        
        # 4. Plot
        ax.plot(x, y_corrected, color='black', linewidth=0.8)
        
        # Axis formatting
        ax.set_xlim(4000, 400)
        y_min, y_max = np.min(y_corrected), np.max(y_corrected)
        y_range = y_max - y_min
        ax.set_ylim(y_min - 0.4 * y_range, y_max + 0.05 * y_range)
        
        # Subplot Title
        ax.set_title(f"{smooth_label}\n+ {base_label}", fontsize=8, fontweight='bold', pad=4)
        
        # Hide Y-axis numerical labels (arbitrary units)
        ax.yaxis.set_major_formatter(plt.NullFormatter())
        ax.tick_params(axis='both', which='major', labelsize=8, direction='in', length=4, width=0.8)
        ax.tick_params(axis='both', which='minor', direction='in', length=2, width=0.8)
        ax.minorticks_on()
        ax.yaxis.set_minor_locator(plt.NullLocator())
        
        # Add labels to X-axis only on the bottom row subplots
        if i >= n_plots - n_cols:
            ax.set_xlabel("Número de onda (cm$^{-1}$)", fontsize=8)
        else:
            ax.set_xticklabels([])
            
        # We also want to label the groups in the subplot
        group_order = ["O-H", "C-H", "CO2", "C=O", "C=C", "C-O", "C-O-C"]
        text_offset = 0.15 * y_range
        
        for group_name in group_order:
            if group_name not in matched_groups:
                # Fallback to local minimum
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
            
            # Dashed red indicator
            y_text = peak_t - text_offset
            ax.plot([peak_w_exact, peak_w_exact], [peak_t, y_text], color='red', linestyle='--', linewidth=0.6)
            
            # Vertical blue label (reads downward)
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
    plt.savefig(OUTPUT_IMAGE, bbox_inches='tight', dpi=300)
    print(f"Gallery plot saved successfully as '{OUTPUT_IMAGE}'.")
    plt.close()


if __name__ == "__main__":
    main()
