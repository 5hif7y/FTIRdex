import os
import numpy as np
import matplotlib.pyplot as plt

# Ensure package is importable when running script directly
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from ftir_library import (
    load_data,
    transmittance_to_absorbance,
    apply_smoothing,
    apply_baseline,
    FTIR
)

def make_3x1_plot(x, y_left, y_right, title_left, title_mid, title_right, output_path, is_baseline=False, y_baseline=None):
    """
    Creates a 3x1 plot comparing:
    - Left: Original/Input signal.
    - Middle: Superposition of input and processed (or estimated baseline).
    - Right: Processed/Corrected signal.
    """
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "Arial", "Inter", "Liberation Sans"]
    
    fig, axes = plt.subplots(1, 3, figsize=(15, 5), dpi=300)
    
    # Left plot
    axes[0].plot(x, y_left, color='black', linewidth=1.0)
    axes[0].set_title(title_left, fontsize=12, fontweight='bold')
    axes[0].set_xlabel("Número de onda (cm$^{-1}$)", fontsize=10)
    axes[0].set_ylabel("Intensidad (u.a.)", fontsize=10)
    axes[0].grid(True, linestyle='--', alpha=0.5)
    axes[0].set_xlim(max(x), min(x)) # Invert x axis
    
    # Middle plot (Superposition)
    axes[1].plot(x, y_left, color='gray', alpha=0.6, linewidth=1.0, label='Entrada')
    if is_baseline and y_baseline is not None:
        axes[1].plot(x, y_baseline, color='red', linewidth=1.2, label='Línea base')
    else:
        axes[1].plot(x, y_right, color='blue', linewidth=1.0, label='Procesado')
    axes[1].set_title(title_mid, fontsize=12, fontweight='bold')
    axes[1].set_xlabel("Número de onda (cm$^{-1}$)", fontsize=10)
    axes[1].grid(True, linestyle='--', alpha=0.5)
    axes[1].legend(loc='best', fontsize=9)
    axes[1].set_xlim(max(x), min(x))
    
    # Right plot
    axes[2].plot(x, y_right, color='black', linewidth=1.0)
    axes[2].set_title(title_right, fontsize=12, fontweight='bold')
    axes[2].set_xlabel("Número de onda (cm$^{-1}$)", fontsize=10)
    axes[2].grid(True, linestyle='--', alpha=0.5)
    axes[2].set_xlim(max(x), min(x))
    
    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight', dpi=300)
    plt.close()
    print(f"Gráfico guardado en '{output_path}'.")

def main():
    print("==================================================")
    print("Generación de Gráficos Comparativos de Preprocesamiento")
    print("==================================================")
    
    # Load sample spectrum (GO)
    base_file = os.path.join(os.path.dirname(__file__), "GO coque s lav ox.txt")
    if not os.path.exists(base_file):
        print(f"Error: Base spectrum file '{base_file}' not found.")
        return
        
    print(f"Cargando espectro desde '{os.path.basename(base_file)}'...")
    x, y_trans = load_data(base_file, FTIR)
    y_abs = transmittance_to_absorbance(y_trans)
    
    # Ensure output directory exists
    img_dir = os.path.join(os.path.dirname(__file__), "images")
    os.makedirs(img_dir, exist_ok=True)
    
    # 1. Comparisons for Smoothing Algorithms (using raw absorbance y_abs)
    print("\nGenerando gráficos comparativos de suavizado...")
    
    # A. Savitzky-Golay
    y_sg = apply_smoothing(y_abs, "Savitzky_Golay(15, 2)")
    make_3x1_plot(
        x, y_abs, y_sg,
        "Absorbancia Cruda", "Superposición (Cruda vs SG)", "Suavizado Savitzky-Golay",
        os.path.join(img_dir, "comparison_smooth_savitzky_golay.png")
    )
    
    # B. Moving Average
    y_ma = apply_smoothing(y_abs, "Moving_Average(15)")
    make_3x1_plot(
        x, y_abs, y_ma,
        "Absorbancia Cruda", "Superposición (Cruda vs MA)", "Suavizado Promedio Móvil",
        os.path.join(img_dir, "comparison_smooth_moving_average.png")
    )
    
    # C. Percentile Filter
    y_pf = apply_smoothing(y_abs, "Percentile_Filter(15, 75)")
    make_3x1_plot(
        x, y_abs, y_pf,
        "Absorbancia Cruda", "Superposición (Cruda vs PF)", "Suavizado Percentil (75%)",
        os.path.join(img_dir, "comparison_smooth_percentile.png")
    )
    
    # 2. Comparisons for Baseline Correction (using smoothed signal y_sg as input)
    print("\nGenerando gráficos comparativos de línea base...")
    
    # A. AsLS
    z_asls, y_corr_asls = apply_baseline(x, y_sg, "asls(lam=1e5, p=0.001)", space='absorbance')
    make_3x1_plot(
        x, y_sg, y_corr_asls,
        "Señal Suavizada", "Ajuste de Línea Base AsLS", "Señal Corregida AsLS",
        os.path.join(img_dir, "comparison_baseline_asls.png"),
        is_baseline=True, y_baseline=z_asls
    )
    
    # B. airPLS
    z_air, y_corr_air = apply_baseline(x, y_sg, "airpls(lam=1e5)", space='absorbance')
    make_3x1_plot(
        x, y_sg, y_corr_air,
        "Señal Suavizada", "Ajuste de Línea Base airPLS", "Señal Corregida airPLS",
        os.path.join(img_dir, "comparison_baseline_airpls.png"),
        is_baseline=True, y_baseline=z_air
    )
    
    # C. arPLS
    z_ar, y_corr_ar = apply_baseline(x, y_sg, "arpls(lam=1e5)", space='absorbance')
    make_3x1_plot(
        x, y_sg, y_corr_ar,
        "Señal Suavizada", "Ajuste de Línea Base arPLS", "Señal Corregida arPLS",
        os.path.join(img_dir, "comparison_baseline_arpls.png"),
        is_baseline=True, y_baseline=z_ar
    )
    
    print("\nGeneración de gráficos finalizada.")

if __name__ == "__main__":
    main()
