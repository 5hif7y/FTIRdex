"""
Case Study V: Automated Reference Database Sampling with JCAMP-DX Files
-----------------------------------------------------------------------
Demonstrates:
1. Native loading of JCAMP-DX (.jdx) files downloaded from NIST Chemistry WebBook.
2. Combinatorial grid search preprocessing on standard compounds (e.g. Ethanol).
3. Peak and valley reporting and functional group mapping.
4. Using the simplified plot_config API with RAW and NONE constants to compare
   raw vs baseline-corrected and smoothed spectra.
"""

import os
import glob
import numpy as np

# Ensure package is importable when running script directly
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from ftir_library import (
    load_data,
    run_analysis,
    generate_report,
    plot_best,
    plot_config,
    RAW,
    NONE,
    FTIR
)

def main():
    print("==================================================")
    print("CASO V: Muestreo Automatizado de Archivos JCAMP-DX")
    print("==================================================")
    
    # 1. Locate samples
    jdx_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'muestras jdx'))
    jdx_files = glob.glob(os.path.join(jdx_dir, "*.jdx"))
    
    if not jdx_files:
        # Fallback check in current or parent directory
        jdx_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'muestras jdx'))
        jdx_files = glob.glob(os.path.join(jdx_dir, "*.jdx"))
        
    if not jdx_files:
        print(f"Error: No .jdx files found in '{jdx_dir}'. Please verify the path.")
        return
        
    print(f"Archivos JCAMP-DX encontrados ({len(jdx_files)}):")
    for f in jdx_files:
        print(f"  - {os.path.basename(f)}")
        
    # Select Ethanol as sample file
    ethanol_file = [f for f in jdx_files if "ethanol" in f.lower()]
    if ethanol_file:
        sample_file = ethanol_file[0]
    else:
        sample_file = jdx_files[0]
        
    print(f"\n[JCAMP-DX] Procesando archivo de muestra: '{os.path.basename(sample_file)}'...")
    
    # 2. Load data (auto-detects .jdx extension)
    x, y_trans = load_data(sample_file)
    print(f"Muestra cargada con éxito. Rango: {x.min():.2f} a {x.max():.2f} cm^-1, Puntos: {len(x)}")
    
    # 3. Generate report (automatically converts fraction transmittance to %T and then to absorbance)
    os.makedirs(os.path.join(os.path.dirname(__file__), "images"), exist_ok=True)
    report_csv = os.path.join(os.path.dirname(__file__), "friendly_report_Ethanol.csv")
    print("\nGenerando reporte numérico de picos y valles...")
    # generate_report expects raw intensities, and handles transmittance-to-absorbance
    generate_report(x, y_trans, output_csv=report_csv, space="transmittance")
    print(f"Reporte numérico guardado en '{report_csv}'.")
    
    # 4. Run Preprocessing Grid Search
    print("\nEjecutando búsqueda en cuadrícula de 180 combinaciones predeterminadas...")
    analysis = run_analysis(x, y_trans, space="transmittance")
    print(f"Mejor configuración encontrada:")
    print(f"  Suavizado: {analysis.best_config['Smoothing']}")
    print(f"  Línea Base: {analysis.best_config['Baseline']}")
    
    # 5. Plot the best configuration
    best_plot_lines = os.path.join(os.path.dirname(__file__), "images", "ethanol_best_lines.png")
    best_plot_box = os.path.join(os.path.dirname(__file__), "images", "ethanol_best_box.png")
    
    print("\nGraficando el mejor preprocesamiento en modo 'lines'...")
    plot_best(analysis, best_plot_lines, mode="lines")
    
    print("Graficando el mejor preprocesamiento en modo 'boxes'...")
    plot_best(analysis, best_plot_box, mode="boxes")
    
    # 6. Simplified plot_config API demonstration
    print("\n[API Simplificada] Demostrando el uso de constantes RAW/NONE...")
    
    # A. Plot raw spectrum (CRUDO - no smoothing, no baseline, no functional group mapping)
    raw_plot = os.path.join(os.path.dirname(__file__), "images", "ethanol_raw.png")
    print("Guardando espectro crudo en 'images/ethanol_raw.png'...")
    plot_config(x, y_trans, RAW, RAW, raw_plot, space="transmittance")
    
    # B. Plot with manual config (Savitzky-Golay + arPLS)
    manual_plot = os.path.join(os.path.dirname(__file__), "images", "ethanol_manual.png")
    print("Guardando espectro manual (Savitzky_Golay + arPLS) en 'images/ethanol_manual.png'...")
    plot_config(
        x, y_trans, 
        smooth_algorithm="Savitzky_Golay(11, 2)", 
        baseline_algorithm="arpls(lam=1e5)", 
        output_image=manual_plot, 
        space="transmittance", 
        mode="box"
    )
    
    print("\nDemostración del Caso V finalizada con éxito.")

if __name__ == "__main__":
    main()
