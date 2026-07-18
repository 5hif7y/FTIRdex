"""
FTIR Numerical Report Generator
-------------------------------
Detects local maxima (peaks) and local minima (valleys) in the optimal
baseline-corrected absorbance spectra for both GO and rGO, mapping them
to functional groups. Outputs data to CSV reports.
"""

import os
import csv
import numpy as np
from scipy.signal import find_peaks

# Import from installed library
from ftir_library import (
    load_ftir_data,
    transmittance_to_absorbance,
    moving_average,
    savitzky_golay,
    median_filter,
    percentile_filter,
    correct_baseline_absorbance,
    assign_functional_groups,
    DEFAULT_FUNCTIONAL_GROUPS
)

# Files
RGO_DATA = "GO coque s lav red.txt"
GO_DATA = "GO coque s lav ox.txt"
RGO_CFG = "best_config_absorbance_rGO.txt"
GO_CFG = "best_config_absorbance_GO.txt"

# Prominences for peak and valley detection
PROMINENCE_PEAKS = 0.02
PROMINENCE_VALLEYS = 0.02
DISTANCE = 15

def load_config(filepath):
    config = {"smoothing": "RAW", "baseline": "arpls(lam=1e6)"}
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if ":" in line:
                        k, v = line.split(":", 1)
                        config[k.strip().lower()] = v.strip()
        except Exception as e:
            print(f"Warning: Error reading {filepath}, using defaults: {e}")
    return config


def parse_config_params(label):
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


def parse_num(s):
    try:
        val = float(s)
        if val.is_integer():
            return int(val)
        return val
    except ValueError:
        return s


def process_spectrum(x, y_trans, config):
    # Convert to absorbance
    y_abs = transmittance_to_absorbance(y_trans)
    
    # Apply Smoothing
    smooth_label = config["smoothing"]
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
        
    # Apply Baseline Correction
    base_label = config["baseline"]
    base_name, base_params = parse_config_params(base_label)
    z, y_corrected = correct_baseline_absorbance(x, y_smoothed, method=base_name, **base_params)
    
    return y_corrected


def generate_numerical_report(x, y_corr, sample_name):
    # 1. Detect Peaks (Local Maxima)
    peak_idx, _ = find_peaks(y_corr, prominence=PROMINENCE_PEAKS, distance=DISTANCE)
    
    # 2. Detect Valleys (Local Minima)
    valley_idx, _ = find_peaks(-y_corr, prominence=PROMINENCE_VALLEYS, distance=DISTANCE)
    
    report_rows = []
    
    # Map peaks to functional groups
    matched_groups, _ = assign_functional_groups(x[peak_idx])
    
    # Add Peaks to report
    for idx in peak_idx:
        wavenumber = x[idx]
        absorbance = y_corr[idx]
        
        # Determine group
        mapped_group = "None"
        for group, pks in matched_groups.items():
            if wavenumber in pks:
                mapped_group = group
                break
                
        report_rows.append({
            "Type": "Peak",
            "Wavenumber": f"{wavenumber:.2f}",
            "Absorbance": f"{absorbance:.6f}",
            "Mapped_Group": mapped_group
        })
        
    # Add Valleys to report
    for idx in valley_idx:
        wavenumber = x[idx]
        absorbance = y_corr[idx]
        report_rows.append({
            "Type": "Valley",
            "Wavenumber": f"{wavenumber:.2f}",
            "Absorbance": f"{absorbance:.6f}",
            "Mapped_Group": "N/A"
        })
        
    # Sort report rows by Wavenumber in descending order
    report_rows.sort(key=lambda r: float(r["Wavenumber"]), reverse=True)
    
    # Save to CSV
    output_csv = f"report_peaks_valleys_{sample_name}.csv"
    print(f"Saving numerical report for {sample_name} to '{output_csv}'...")
    with open(output_csv, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["Type", "Wavenumber", "Absorbance", "Mapped_Group"])
        writer.writeheader()
        writer.writerows(report_rows)
        
    print(f"Saved {len(report_rows)} rows ({len(peak_idx)} peaks, {len(valley_idx)} valleys) for {sample_name}.")


def main():
    if not os.path.exists(RGO_DATA) or not os.path.exists(GO_DATA):
        print("Error: Raw data files not found.")
        return
        
    # Process rGO
    rgo_cfg = load_config(RGO_CFG)
    x_rgo, y_rgo_trans = load_ftir_data(RGO_DATA)
    y_rgo_corr = process_spectrum(x_rgo, y_rgo_trans, rgo_cfg)
    generate_numerical_report(x_rgo, y_rgo_corr, "rGO")
    
    # Process GO
    go_cfg = load_config(GO_CFG)
    x_go, y_go_trans = load_ftir_data(GO_DATA)
    y_go_corr = process_spectrum(x_go, y_go_trans, go_cfg)
    generate_numerical_report(x_go, y_go_corr, "GO")


if __name__ == "__main__":
    main()
