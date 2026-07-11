"""
FTIR Absorbance Overlay Plotting Script
---------------------------------------
Uses ftir_library to:
1. Load best configs for GO and rGO in absorbance space.
2. Load spectra and apply the optimal pre-processing in Absorbance.
3. Superimpose and save the comparison plot.
"""

import os
from ftir_library import (
    load_ftir_data,
    transmittance_to_absorbance,
    preprocess_spectrum,
    plot_superposition
)

# Files
RGO_DATA = "GO coque s lav red.txt"
GO_DATA = "GO coque s lav ox.txt"
RGO_CFG = "best_config_absorbance_rGO.txt"
GO_CFG = "best_config_absorbance_GO.txt"
OUTPUT_IMAGE = "images/absorbance_superposition_GO_rGO.png"


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
        print("Error: Input files not found.")
        return
        
    rgo_cfg = load_config(RGO_CFG)
    go_cfg = load_config(GO_CFG)
    
    print(f"rGO best config: {rgo_cfg['smoothing']} + {rgo_cfg['baseline']}")
    print(f"GO best config:  {go_cfg['smoothing']} + {go_cfg['baseline']}")
    
    # Load raw data and convert to absorbance
    x_rgo, y_rgo_trans = load_ftir_data(RGO_DATA)
    x_go, y_go_trans = load_ftir_data(GO_DATA)
    
    y_rgo_abs = transmittance_to_absorbance(y_rgo_trans)
    y_go_abs = transmittance_to_absorbance(y_go_trans)
    
    # Preprocess both spectra in absorbance space
    print("Preprocessing spectra...")
    _, y_rgo_corr = preprocess_spectrum(x_rgo, y_rgo_abs, rgo_cfg["smoothing"], rgo_cfg["baseline"], space='absorbance')
    _, y_go_corr = preprocess_spectrum(x_go, y_go_abs, go_cfg["smoothing"], go_cfg["baseline"], space='absorbance')
    
    # Superimpose and plot
    plot_superposition(
        x_go, y_go_corr, 'Óxido de Grafeno (GO)',
        x_rgo, y_rgo_corr, 'Óxido de Grafeno Reducido (rGO)',
        OUTPUT_IMAGE, space='absorbance'
    )


if __name__ == "__main__":
    main()
