"""
Friendly Demonstration Script for ftir_library (v0.0.3)
------------------------------------------------------
This script demonstrates the simplified, user-friendly high-level API
designed specifically for chemical and medical researchers.
It requires only one or two variable manipulations per step.
"""

import os
import glob
from ftir_library import (
    load_data,
    generate_report,
    run_analysis,
    plot_best,
    plot_gallery,
    get_approvednumber,
    FTIR,
    SERS
)

def main():
    print("==================================================")
    print("DEMO 1: FTIR ANALYSIS (Graphene Oxide)")
    print("==================================================")
    
    # 1. Load data (manually specifying FTIR format using the imported constant)
    ftir_file = "GO coque s lav ox.txt"
    if os.path.exists(ftir_file):
        x_ftir, y_ftir = load_data(ftir_file, FTIR)
        print(f"Loaded FTIR file '{ftir_file}' manually as FTIR.")
        print(f"Data range: {x_ftir[0]:.1f} cm^-1 to {x_ftir[-1]:.1f} cm^-1")
        
        # 2. Generate numerical report (peaks/valleys + group matching)
        print("Generating numerical report...")
        generate_report(x_ftir, y_ftir, output_csv="friendly_report_FTIR.csv", space="transmittance")
        print("Report saved to 'friendly_report_FTIR.csv'.")
        
        # 3. Run search/analysis (combinatorial grid search)
        print("Running grid search analysis...")
        analysis_ftir = run_analysis(x_ftir, y_ftir, space="transmittance")
        print(f"Best Configuration Found: {analysis_ftir.best_config}")
        
        # 4. Get the maximum number of successful/approved configurations
        n_ftir = get_approvednumber(analysis_ftir)
        print(f"Number of successful configurations: {n_ftir}")
        
        # 5. Plot best fit (lines mode)
        print("Plotting best configuration in 'lines' mode...")
        plot_best(analysis_ftir, "images/friendly_best_FTIR.png", "lines")
        print("Plot saved to 'images/friendly_best_FTIR.png'.")
        
        # 6. Plot configuration gallery (horizontal slices of all successful configurations in 'boxes')
        print(f"Plotting all {n_ftir} successful configurations in 'boxes' mode...")
        plot_gallery(analysis_ftir, "images/friendly_gallery_FTIR", n_ftir, "boxes")
        print("Gallery slices saved as 'images/friendly_gallery_FTIR_partN.png'.")
    else:
        print(f"Warning: FTIR file '{ftir_file}' not found.")

    print("\n==================================================")
    print("DEMO 2: RAMAN SERS CELL ANALYSIS (Melanoma Cancer)")
    print("==================================================")
    
    # Locate cells data
    raman_dir = r"c:\Users\Shifty\Antigravity-DEV\Trabajar-0.0.2\Trabajar-0.0.2\Cells Raman Spectra\A"
    csv_files = glob.glob(os.path.join(raman_dir, "*.csv"))
    
    if csv_files:
        raman_file = csv_files[0]
        # 1. Load data (manually specifying SERS format using string)
        x_raman, y_raman = load_data(raman_file, "SERS")
        print(f"Loaded Raman cell file '{os.path.basename(raman_file)}' manually as SERS.")
        print(f"Data range: {x_raman[0]:.1f} cm^-1 to {x_raman[-1]:.1f} cm^-1")
        
        # 2. Generate numerical report (removes cosmic rays + L2 normalization + optimal baseline)
        print("Generating numerical report...")
        generate_report(x_raman, y_raman, output_csv="friendly_report_Raman.csv")
        print("Report saved to 'friendly_report_Raman.csv'.")
        
        # 3. Run search/analysis (evaluates Raman biomarkers automatically)
        print("Running grid search analysis...")
        analysis_raman = run_analysis(x_raman, y_raman)
        print(f"Best Configuration Found: {analysis_raman.best_config}")
        
        # 4. Get approved configurations count
        n_raman = get_approvednumber(analysis_raman)
        print(f"Number of successful configurations: {n_raman}")
        
        # 5. Plot best fit (Raman box/boxes mode)
        print("Plotting best configuration in 'boxes' mode...")
        plot_best(analysis_raman, "images/friendly_best_Raman.png", "boxes")
        print("Plot saved to 'images/friendly_best_Raman.png'.")
        
        # 6. Plot configuration gallery (plots all successful configurations in 'lines')
        print(f"Plotting all {n_raman} successful configurations in 'lines' mode...")
        plot_gallery(analysis_raman, "images/friendly_gallery_Raman", n_raman, "lines")
        print("Gallery slices saved as 'images/friendly_gallery_Raman_partN.png'.")
    else:
        print(f"Warning: Raman directory '{raman_dir}' or files not found.")


if __name__ == "__main__":
    main()
