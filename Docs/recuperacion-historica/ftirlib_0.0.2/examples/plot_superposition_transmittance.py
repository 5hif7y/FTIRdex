"""
FTIR Superposition Plotting Script
----------------------------------
Loads the best configurations for GO and rGO, processes both spectra,
and superimposes them in a single plot for chemical comparison.
"""

import os
import numpy as np
import matplotlib.pyplot as plt
from ftir_library import (
    load_ftir_data,
    moving_average,
    savitzky_golay,
    median_filter,
    percentile_filter,
    correct_baseline_transmittance,
    parse_config_params
)

# Files
RGO_DATA = "GO coque s lav red.txt"
GO_DATA = "GO coque s lav ox.txt"
RGO_CFG = "best_config.txt"
GO_CFG = "best_config_GO.txt"
OUTPUT_IMAGE = "images/resultado_superposicion_GO_rGO.png"

def load_config(filepath):
    """Reads a configuration file, returns smoothing and baseline strings."""
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
            print(f"Warning: Error reading {filepath}, using default config. Error: {e}")
    return config


def preprocess_spectrum(x, y, config_label_smooth, config_label_base):
    # 1. Apply Smoothing
    smooth_name, smooth_params = parse_config_params(config_label_smooth)
    if smooth_name == "raw":
        y_smoothed = y.copy()
    elif "Moving_Average" in config_label_smooth:
        y_smoothed = moving_average(y, window=smooth_params.get("window", 5))
    elif "Savitzky_Golay" in config_label_smooth:
        y_smoothed = savitzky_golay(y, window=smooth_params.get("window", 11), poly=smooth_params.get("poly", 2))
    elif "Median_Filter" in config_label_smooth:
        y_smoothed = median_filter(y, window=smooth_params.get("window", 5))
    elif "Percentile_Filter" in config_label_smooth:
        pct = smooth_params.get("percentile", 50)
        if "percentile" not in smooth_params and "poly" in smooth_params:
            pct = smooth_params["poly"]
        y_smoothed = percentile_filter(y, window=smooth_params.get("window", 5), percentile=pct)
    else:
        y_smoothed = y.copy()
        
    # 2. Apply Baseline Correction
    base_name, base_params = parse_config_params(config_label_base)
    z, y_corrected = correct_baseline_transmittance(x, y_smoothed, method=base_name, **base_params)
    
    return y_corrected


def main():
    if not os.path.exists(RGO_DATA) or not os.path.exists(GO_DATA):
        print(f"Error: Raw data files not found.")
        return
        
    # Load configs
    rgo_cfg = load_config(RGO_CFG)
    go_cfg = load_config(GO_CFG)
    
    print(f"rGO config: {rgo_cfg['smoothing']} + {rgo_cfg['baseline']}")
    print(f"GO config:  {go_cfg['smoothing']} + {go_cfg['baseline']}")
    
    # Load raw data
    x_rgo, y_rgo = load_ftir_data(RGO_DATA)
    x_go, y_go = load_ftir_data(GO_DATA)
    
    # Preprocess
    print("Preprocessing spectra...")
    y_rgo_corr = preprocess_spectrum(x_rgo, y_rgo, rgo_cfg["smoothing"], rgo_cfg["baseline"])
    y_go_corr = preprocess_spectrum(x_go, y_go, go_cfg["smoothing"], go_cfg["baseline"])
    
    # Matplotlib Plotting
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "Arial", "Inter", "Liberation Sans"]
    
    fig, ax = plt.subplots(figsize=(10, 6), dpi=300)
    
    # Plot spectra
    ax.plot(x_go, y_go_corr, color='blue', linewidth=1.2, label='Óxido de Grafeno (GO)')
    ax.plot(x_rgo, y_rgo_corr, color='black', linewidth=1.2, label='Óxido de Grafeno Reducido (rGO)')
    
    # Formatting
    ax.set_xlabel("Número de onda (cm$^{-1}$)", fontsize=13)
    ax.set_ylabel("Transmitância (u.a.)", fontsize=13)
    ax.set_xlim(4000, 400)
    
    # Hide Y-axis numbers (arbitrary units)
    ax.yaxis.set_major_formatter(plt.NullFormatter())
    
    # Tick marks
    ax.tick_params(axis='both', which='major', labelsize=11, direction='in', length=6, width=1.0)
    ax.tick_params(axis='both', which='minor', direction='in', length=3, width=1.0)
    ax.minorticks_on()
    ax.yaxis.set_minor_locator(plt.NullLocator())
    
    # Spines / border
    for spine in ax.spines.values():
        spine.set_linewidth(1.0)
        
    # Legend
    ax.legend(loc='lower left', frameon=True, edgecolor='black', fontsize=11, framealpha=0.9)
    
    plt.tight_layout()
    plt.savefig(OUTPUT_IMAGE, bbox_inches='tight', dpi=300)
    print(f"Superposition plot successfully saved as '{OUTPUT_IMAGE}'.")
    plt.close()


if __name__ == "__main__":
    main()
