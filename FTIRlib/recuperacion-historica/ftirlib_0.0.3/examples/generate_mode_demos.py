"""
Demo Script to Generate Plotting Mode Comparisons and Galleries
-----------------------------------------------------------------
This script demonstrates the dual plotting and grid search capabilities of ftir_library:
1. FTIR (Graphene Oxide) in both 'lines' and 'box' modes.
2. Raman (Melanoma Cell SERS spectrum) in both 'lines' and 'box' modes.
3. Raman 3x1 preprocessing configuration gallery showing successful cell diagnoses.
"""

import os
import glob
import numpy as np
import matplotlib.pyplot as plt

from ftir_library import (
    load_ftir_data,
    preprocess_spectrum,
    transmittance_to_absorbance,
    plot_best_configuration,
    plot_gallery_3x1,
    run_grid_search,
    remove_cosmic_rays,
    moving_average,
    correct_baseline_absorbance,
    normalize_spectra
)

def main():
    print("Generating demo images and galleries for plotting modes...")
    os.makedirs("images", exist_ok=True)
    
    # ==========================================
    # 1. FTIR DEMONSTRATION (Graphene Oxide)
    # ==========================================
    ftir_file = "GO coque s lav ox.txt"
    ftir_cfg_file = "best_config_absorbance_GO.txt"
    
    if os.path.exists(ftir_file):
        print("\n[FTIR] Processing Graphene Oxide spectrum...")
        x_ftir, y_ftir_trans = load_ftir_data(ftir_file)
        y_ftir_abs = transmittance_to_absorbance(y_ftir_trans)
        
        # Default optimal config or fallback
        best_cfg = {"Smoothing": "Savitzky_Golay(11, 2)", "Baseline": "arpls(lam=1e5)"}
        if os.path.exists(ftir_cfg_file):
            try:
                with open(ftir_cfg_file, "r", encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if ":" in line:
                            k, v = line.split(":", 1)
                            best_cfg[k.strip().capitalize()] = v.strip()
            except Exception as e:
                print(f"Warning: Could not read FTIR config: {e}")
                
        # A. Save in 'lines' mode
        print("[FTIR] Plotting in 'lines' mode...")
        plot_best_configuration(
            x_ftir, y_ftir_abs, best_cfg, 
            output_image="images/ftir_demo_lines.png",
            space="absorbance", prominence=0.02, distance=15, 
            mode="lines", invert_x=True
        )
        
        # B. Save in 'box' mode
        print("[FTIR] Plotting in 'box' mode...")
        plot_best_configuration(
            x_ftir, y_ftir_abs, best_cfg, 
            output_image="images/ftir_demo_box.png",
            space="absorbance", prominence=0.02, distance=15, 
            mode="box", invert_x=True
        )
    else:
        print(f"Warning: FTIR file '{ftir_file}' not found.")

    # ==========================================
    # 2. RAMAN DEMONSTRATION (Melanoma Cancer Cell)
    # ==========================================
    raman_dir = r"c:\Users\Shifty\Antigravity-DEV\Trabajar-0.0.2\Trabajar-0.0.2\Cells Raman Spectra\A"
    
    csv_files = glob.glob(os.path.join(raman_dir, "*.csv"))
    if csv_files:
        raman_file = csv_files[0]
        print(f"\n[Raman] Loading single SERS spectrum from {raman_file}...")
        try:
            raw_data = np.genfromtxt(raman_file, delimiter=',', skip_header=1)
            # Take the first spectrum row
            if len(raw_data.shape) > 1:
                raw_spec = raw_data[0]
            else:
                raw_spec = raw_data
                
            x_raman = np.linspace(100, 4278, 2090)
            
            # Preprocess the spectrum (cosmic ray spike removal)
            clean_spec = remove_cosmic_rays(raw_spec, window=11, threshold=6.0)
            
            # Setup Raman chemical bands (Biomarkers)
            RAMAN_GROUPS = {
                "Fosfatos (ADN/ARN)": (1000, 1150),
                "Proteínas/Lípidos": (1200, 1400),
                "Amida I": (1550, 1650),
                "Lípidos (C-H)": (2800, 3000)
            }
            RAMAN_ORDER = ["Fosfatos (ADN/ARN)", "Proteínas/Lípidos", "Amida I", "Lípidos (C-H)"]
            
            # We want to run a grid search to find the best preprocessors on this cell spectrum
            # evaluating against our custom RAMAN_GROUPS
            print("[Raman] Running grid search over 180 configurations...")
            best_cfg_raman, results_raman = run_grid_search(
                x_raman, clean_spec, 
                output_csv="raman_grid_search_results.csv",
                best_config_txt="best_config_raman_spec.txt",
                space="absorbance", prominence=0.015, distance=30,
                groups_db=RAMAN_GROUPS
            )
            print(f"[Raman] Best config: {best_cfg_raman}")
            
            # Clean results names for plotting function formatting compatibility
            # In plot_best_configuration, z and y_corrected are calculated by preprocessing.
            # We will preprocess clean_spec and apply L2 normalization to be compatible with Raman.
            # Wait, let's normalize the signal first so the plots match the vector-normalized scale.
            norm_spec = normalize_spectra(clean_spec, method="vector")
            
            # Setup config dict for plotting pipeline function compatibility
            best_cfg_raman_norm = {
                "Smoothing": best_cfg_raman["Smoothing"],
                "Baseline": best_cfg_raman["Baseline"]
            }
            
            # A. Save in 'lines' mode
            print("[Raman] Plotting in 'lines' mode...")
            plot_best_configuration(
                x_raman, norm_spec, best_cfg_raman_norm,
                output_image="images/raman_demo_lines.png",
                space="absorbance", prominence=0.015, distance=30,
                mode="lines", groups_db=RAMAN_GROUPS, group_order=RAMAN_ORDER,
                invert_x=False
            )
            
            # B. Save in 'box' mode
            print("[Raman] Plotting in 'box' mode...")
            plot_best_configuration(
                x_raman, norm_spec, best_cfg_raman_norm,
                output_image="images/raman_demo_box.png",
                space="absorbance", prominence=0.015, distance=30,
                mode="box", groups_db=RAMAN_GROUPS, group_order=RAMAN_ORDER,
                invert_x=False
            )
            
            # C. Save 3x1 configuration gallery
            print("[Raman] Plotting 3x1 gallery of top configurations...")
            # We will use plot_gallery_3x1 on the normalized spectrum
            plot_gallery_3x1(
                x_raman, norm_spec, results_raman, 
                output_prefix="images/raman_gallery_box",
                space="absorbance", prominence=0.015, distance=30,
                max_total_plots=17, mode="box", 
                groups_db=RAMAN_GROUPS, group_order=RAMAN_ORDER,
                invert_x=False
            )
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Error processing Raman spectrum: {e}")
    else:
        print(f"Warning: Raman directory '{raman_dir}' or files not found.")
        
    print("\nPlotting demos completed.")

if __name__ == "__main__":
    main()
