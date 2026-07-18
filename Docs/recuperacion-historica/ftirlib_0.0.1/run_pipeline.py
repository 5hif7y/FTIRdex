"""
FTIR Grid Search Pipeline
-------------------------
Runs combinations of smoothing and baseline correction algorithms on raw FTIR data,
calculates scores based on detected functional groups and peaks, and saves results to a CSV.
"""

import os
import csv
import numpy as np
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

# Input filepath
INPUT_FILE = "GO coque s lav red.txt"
OUTPUT_CSV = "pipeline_results.csv"

# Configuration of smoothing algorithms
SMOOTHING_CONFIGS = [
    {"name": "RAW", "func": lambda y: y.copy(), "label": "RAW"},
    
    # Moving Average
    {"name": "Moving_Average", "func": lambda y: moving_average(y, 3), "label": "Moving_Average(3)"},
    {"name": "Moving_Average", "func": lambda y: moving_average(y, 5), "label": "Moving_Average(5)"},
    {"name": "Moving_Average", "func": lambda y: moving_average(y, 7), "label": "Moving_Average(7)"},
    
    # Savitzky-Golay
    {"name": "Savitzky_Golay", "func": lambda y: savitzky_golay(y, 7, 2), "label": "Savitzky_Golay(7, 2)"},
    {"name": "Savitzky_Golay", "func": lambda y: savitzky_golay(y, 11, 2), "label": "Savitzky_Golay(11, 2)"},
    {"name": "Savitzky_Golay", "func": lambda y: savitzky_golay(y, 15, 3), "label": "Savitzky_Golay(15, 3)"},
    
    # Median Filter
    {"name": "Median_Filter", "func": lambda y: median_filter(y, 3), "label": "Median_Filter(3)"},
    {"name": "Median_Filter", "func": lambda y: median_filter(y, 5), "label": "Median_Filter(5)"},
    {"name": "Median_Filter", "func": lambda y: median_filter(y, 7), "label": "Median_Filter(7)"},
    
    # Percentile Filter
    {"name": "Percentile_Filter", "func": lambda y: percentile_filter(y, 5, 25), "label": "Percentile_Filter(5, 25)"},
    {"name": "Percentile_Filter", "func": lambda y: percentile_filter(y, 5, 75), "label": "Percentile_Filter(5, 75)"},
]

# Configuration of baseline correction algorithms
BASELINE_CONFIGS = [
    {"name": "RAW", "method": "raw", "kwargs": {}, "label": "RAW"},
    {"name": "detrend", "method": "detrend", "kwargs": {}, "label": "detrend"},
    {"name": "linear_baseline", "method": "linear_baseline", "kwargs": {}, "label": "linear_baseline"},
    
    # Polynomial (IModPoly)
    {"name": "polynomial_baseline", "method": "polynomial_baseline", "kwargs": {"deg": 2}, "label": "polynomial_baseline(deg=2)"},
    {"name": "polynomial_baseline", "method": "polynomial_baseline", "kwargs": {"deg": 3}, "label": "polynomial_baseline(deg=3)"},
    {"name": "polynomial_baseline", "method": "polynomial_baseline", "kwargs": {"deg": 4}, "label": "polynomial_baseline(deg=4)"},
    
    # Asymmetric Least Squares (AsLS)
    {"name": "asls", "method": "asls", "kwargs": {"lam": 1e4, "p": 0.001}, "label": "asls(lam=1e4, p=0.001)"},
    {"name": "asls", "method": "asls", "kwargs": {"lam": 1e5, "p": 0.001}, "label": "asls(lam=1e5, p=0.001)"},
    {"name": "asls", "method": "asls", "kwargs": {"lam": 1e6, "p": 0.001}, "label": "asls(lam=1e6, p=0.001)"},
    
    # Adaptive Iteratively Reweighted Penalized Least Squares (airPLS)
    {"name": "airpls", "method": "airpls", "kwargs": {"lam": 1e4}, "label": "airpls(lam=1e4)"},
    {"name": "airpls", "method": "airpls", "kwargs": {"lam": 1e5}, "label": "airpls(lam=1e5)"},
    {"name": "airpls", "method": "airpls", "kwargs": {"lam": 1e6}, "label": "airpls(lam=1e6)"},
    
    # Asymmetrically Reweighted Penalized Least Squares (arPLS)
    {"name": "arpls", "method": "arpls", "kwargs": {"lam": 1e4}, "label": "arpls(lam=1e4)"},
    {"name": "arpls", "method": "arpls", "kwargs": {"lam": 1e5}, "label": "arpls(lam=1e5)"},
    {"name": "arpls", "method": "arpls", "kwargs": {"lam": 1e6}, "label": "arpls(lam=1e6)"},
]


def run_grid_search():
    if not os.path.exists(INPUT_FILE):
        print(f"Error: Input file '{INPUT_FILE}' not found in current directory.")
        return
        
    print(f"Loading FTIR spectrum from {INPUT_FILE}...")
    x, y = load_ftir_data(INPUT_FILE)
    print(f"Loaded {len(x)} data points. Range: {x[0]:.2f} to {x[-1]:.2f} cm^-1.")
    
    results = []
    
    # Peak detection parameters
    PROMINENCE = 0.8    # Minimum depth of peak in transmittance %
    DISTANCE = 15       # Minimum separation of peaks (points)
    
    print("\nRunning grid search of combinations...")
    print(f"{'Suavizado':<25} | {'Baseline':<30} | {'Grupos':<6} | {'Picos':<6} | {'Score (Std)':<11} | {'Score (Penalized)':<15}")
    print("-" * 110)
    
    # We will compute both:
    # 1. Standard Score (noise weight = 1.0, where noise cancels out, so Score = Valid Peaks + Groups)
    # 2. Penalized Score (noise weight = 2.0, so Score = Valid Peaks + Groups - Noise Peaks)
    
    for smooth_cfg in SMOOTHING_CONFIGS:
        # 1. Apply smoothing
        y_smoothed = smooth_cfg["func"](y)
        
        for base_cfg in BASELINE_CONFIGS:
            # 2. Apply baseline correction
            try:
                z, y_corrected = correct_baseline_transmittance(
                    x, y_smoothed, 
                    method=base_cfg["method"], 
                    **base_cfg["kwargs"]
                )
                
                # 3. Detect peaks
                indices, peak_x, peak_y = detect_peaks_transmittance(
                    x, y_corrected, 
                    prominence=PROMINENCE, 
                    distance=DISTANCE
                )
                
                # 4. Map functional groups
                matched_groups, noise_peaks = assign_functional_groups(peak_x)
                
                # 5. Calculate scores
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
                
                # Display subset of results in CLI to show progress
                # Format output strings
                smooth_lbl = smooth_cfg["label"]
                base_lbl = base_cfg["label"]
                print(f"{smooth_lbl:<25} | {base_lbl:<30} | {len(matched_groups):<6} | {len(peak_x):<6} | {score_std:<11} | {score_pen:<15}")
                
            except Exception as e:
                print(f"Error executing combination: {smooth_cfg['label']} + {base_cfg['label']}: {e}")
                
    # Save to CSV
    print(f"\nSaving results to '{OUTPUT_CSV}'...")
    with open(OUTPUT_CSV, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            "Smoothing", "Baseline", "N_Groups_Detected", 
            "Detected_Groups", "N_Peaks_Detected", 
            "N_Noise_Peaks", "Score_Std", "Score_Penalized"
        ])
        writer.writeheader()
        writer.writerows(results)
        
    print(f"Results successfully saved. Total combinations analyzed: {len(results)}.")
    
    # Determine the best configuration
    # We prioritize Penalized Score first, then number of groups, then fewer noise peaks.
    best_by_pen = max(results, key=lambda r: (r["Score_Penalized"], r["N_Groups_Detected"], -r["N_Noise_Peaks"]))
    best_by_std = max(results, key=lambda r: (r["Score_Std"], r["N_Groups_Detected"]))
    
    print("\n" + "=" * 60)
    print("ANALYSIS SUMMARY")
    print("=" * 60)
    print("Best combination by Standard Score (Valid Peaks + Groups):")
    print(f"  Smoothing:      {best_by_std['Smoothing']}")
    print(f"  Baseline:       {best_by_std['Baseline']}")
    print(f"  Groups (N={best_by_std['N_Groups_Detected']}): {best_by_std['Detected_Groups']}")
    print(f"  Total Peaks:    {best_by_std['N_Peaks_Detected']} (Noise: {best_by_std['N_Noise_Peaks']})")
    print(f"  Score Standard: {best_by_std['Score_Std']}")
    print("-" * 60)
    print("Best combination by Penalized Score (Valid Peaks + Groups - Noise Peaks):")
    print(f"  Smoothing:      {best_by_pen['Smoothing']}")
    print(f"  Baseline:       {best_by_pen['Baseline']}")
    print(f"  Groups (N={best_by_pen['N_Groups_Detected']}): {best_by_pen['Detected_Groups']}")
    print(f"  Total Peaks:    {best_by_pen['N_Peaks_Detected']} (Noise: {best_by_pen['N_Noise_Peaks']})")
    print(f"  Score Penalized:{best_by_pen['Score_Penalized']}")
    print("=" * 60)
    
    # Write details of best configurations to a small configuration file so plot_best.py can read it
    with open("best_config.txt", "w", encoding='utf-8') as f:
        f.write(f"Smoothing: {best_by_pen['Smoothing']}\n")
        f.write(f"Baseline: {best_by_pen['Baseline']}\n")


if __name__ == "__main__":
    run_grid_search()
