"""
FTIR Absorbance Overlay Plotting Script
---------------------------------------
Loads the best configurations for GO and rGO in absorbance space,
processes both spectra, and overlays them in a single plot.
"""

import os
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
    correct_baseline_absorbance
)

# Files
RGO_DATA = "GO coque s lav red.txt"
GO_DATA = "GO coque s lav ox.txt"
RGO_CFG = "best_config_absorbance_rGO.txt"
GO_CFG = "best_config_absorbance_GO.txt"
OUTPUT_IMAGE = "absorbance_superposition_GO_rGO.png"

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
            print(f"Warning: Error reading {filepath}, using defaults. Error: {e}")
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


def preprocess_spectrum(x, y_abs, config_label_smooth, config_label_base):
    # Apply Smoothing
    smooth_name, smooth_params = parse_config_params(config_label_smooth)
    if smooth_name == "raw":
        y_smoothed = y_abs.copy()
    elif "Moving_Average" in config_label_smooth:
        y_smoothed = moving_average(y_abs, window=smooth_params.get("window", 5))
    elif "Savitzky_Golay" in config_label_smooth:
        y_smoothed = savitzky_golay(y_abs, window=smooth_params.get("window", 11), poly=smooth_params.get("poly", 2))
    elif "Median_Filter" in config_label_smooth:
        y_smoothed = median_filter(y_abs, window=smooth_params.get("window", 5))
    elif "Percentile_Filter" in config_label_smooth:
        pct = smooth_params.get("percentile", 50)
        if "percentile" not in smooth_params and "poly" in smooth_params:
            pct = smooth_params["poly"]
        y_smoothed = percentile_filter(y_abs, window=smooth_params.get("window", 5), percentile=pct)
    else:
        y_smoothed = y_abs.copy()
        
    # Apply Baseline Correction
    base_name, base_params = parse_config_params(config_label_base)
    z, y_corrected = correct_baseline_absorbance(x, y_smoothed, method=base_name, **base_params)
    
    return y_corrected


def main():
    if not os.path.exists(RGO_DATA) or not os.path.exists(GO_DATA):
        print("Error: Input files not found.")
        return
        
    rgo_cfg = load_config(RGO_CFG)
    go_cfg = load_config(GO_CFG)
    
    print(f"rGO best: {rgo_cfg['smoothing']} + {rgo_cfg['baseline']}")
    print(f"GO best:  {go_cfg['smoothing']} + {go_cfg['baseline']}")
    
    # Load raw data and convert to absorbance
    x_rgo, y_rgo_trans = load_ftir_data(RGO_DATA)
    x_go, y_go_trans = load_ftir_data(GO_DATA)
    
    y_rgo_abs = transmittance_to_absorbance(y_rgo_trans)
    y_go_abs = transmittance_to_absorbance(y_go_trans)
    
    # Preprocess
    print("Preprocessing spectra in absorbance space...")
    y_rgo_corr = preprocess_spectrum(x_rgo, y_rgo_abs, rgo_cfg["smoothing"], rgo_cfg["baseline"])
    y_go_corr = preprocess_spectrum(x_go, y_go_abs, go_cfg["smoothing"], go_cfg["baseline"])
    
    # Plotting
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "Arial", "Inter", "Liberation Sans"]
    
    fig, ax = plt.subplots(figsize=(10, 6), dpi=300)
    
    # Plot curves
    ax.plot(x_go, y_go_corr, color='blue', linewidth=1.2, label='Óxido de Grafeno (GO)')
    ax.plot(x_rgo, y_rgo_corr, color='black', linewidth=1.2, label='Óxido de Grafeno Reducido (rGO)')
    
    # Axis styling
    ax.set_xlabel("Número de onda (cm$^{-1}$)", fontsize=13)
    ax.set_ylabel("Absorbância (u.a.)", fontsize=13)
    ax.set_xlim(4000, 400)
    
    # Hide numeric values on Y-axis
    ax.yaxis.set_major_formatter(plt.NullFormatter())
    
    # Ticks
    ax.tick_params(axis='both', which='major', labelsize=11, direction='in', length=6, width=1.0)
    ax.tick_params(axis='both', which='minor', direction='in', length=3, width=1.0)
    ax.minorticks_on()
    ax.yaxis.set_minor_locator(plt.NullLocator())
    
    # Border spines
    for spine in ax.spines.values():
        spine.set_linewidth(1.0)
        
    # Legend
    ax.legend(loc='upper right', frameon=True, edgecolor='black', fontsize=11, framealpha=0.9)
    
    plt.tight_layout()
    plt.savefig(OUTPUT_IMAGE, bbox_inches='tight', dpi=300)
    print(f"Absorbance overlay plot successfully saved as '{OUTPUT_IMAGE}'.")
    plt.close()


if __name__ == "__main__":
    main()
