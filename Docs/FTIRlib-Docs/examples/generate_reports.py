"""
FTIR Numerical Report Generator
-------------------------------
Uses ftir_library to:
1. Load best configs for GO and rGO.
2. Load spectra and apply the optimal pre-processing in Absorbance.
3. Detect local maxima (peaks) and local minima (valleys).
4. Map peaks to functional groups and save a structured CSV report.
"""

import os
from ftir_library import (
    load_ftir_data,
    preprocess_spectrum,
    generate_numerical_report
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
    """Reads a configuration file, returning smoothing and baseline strings."""
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


def main():
    if not os.path.exists(RGO_DATA) or not os.path.exists(GO_DATA):
        print("Error: Raw data files not found.")
        return
        
    # Process rGO
    print("\nGenerating report for rGO...")
    rgo_cfg = load_config(RGO_CFG)
    x_rgo, y_rgo_trans = load_ftir_data(RGO_DATA)
    
    # Preprocess (smoothing + baseline correction) in Absorbance space
    _, y_rgo_corr = preprocess_spectrum(
        x_rgo, y_rgo_trans, rgo_cfg["smoothing"], rgo_cfg["baseline"], space='absorbance'
    )
    
    generate_numerical_report(
        x_rgo, y_rgo_corr, "rGO", "report_peaks_valleys_rGO.csv",
        prominence_peaks=PROMINENCE_PEAKS, prominence_valleys=PROMINENCE_VALLEYS, distance=DISTANCE
    )
    
    # Process GO
    print("\nGenerating report for GO...")
    go_cfg = load_config(GO_CFG)
    x_go, y_go_trans = load_ftir_data(GO_DATA)
    
    _, y_go_corr = preprocess_spectrum(
        x_go, y_go_trans, go_cfg["smoothing"], go_cfg["baseline"], space='absorbance'
    )
    
    generate_numerical_report(
        x_go, y_go_corr, "GO", "report_peaks_valleys_GO.csv",
        prominence_peaks=PROMINENCE_PEAKS, prominence_valleys=PROMINENCE_VALLEYS, distance=DISTANCE
    )


if __name__ == "__main__":
    main()
