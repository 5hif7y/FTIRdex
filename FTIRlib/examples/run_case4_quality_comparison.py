"""
Case Study IV: FTIR Quality Comparison between Material Providers
-----------------------------------------------------------------
Generates 180 fictitious spectra from a base FTIR spectrum, representing
different suppliers of varying quality (low, medium, high).
Applies Vector Normalization, executes PCA for dimensionality reduction,
and validates a Kernel Ridge Classifier to distinguish between providers.
"""

import os
import numpy as np
import matplotlib.pyplot as plt

# Ensure package is importable when running script directly
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from ftir_library import (
    load_data,
    preprocess_spectrum,
    transmittance_to_absorbance,
    generate_ftir_quality_samples,
    PCA,
    KernelRidgeClassifier,
    normalize_spectra,
    FTIR
)

def run_cross_validation(X, y, folds=5):
    """Simple 5-fold cross validation helper."""
    np.random.seed(42)
    indices = np.arange(X.shape[0])
    np.random.shuffle(indices)
    
    fold_sizes = np.full(folds, X.shape[0] // folds)
    fold_sizes[:X.shape[0] % folds] += 1
    
    current = 0
    correct = 0
    
    for fold in range(folds):
        start, end = current, current + fold_sizes[fold]
        test_idx = indices[start:end]
        train_idx = np.setdiff1d(indices, test_idx)
        current = end
        
        X_train, y_train = X[train_idx], y[train_idx]
        X_test, y_test = X[test_idx], y[test_idx]
        
        clf = KernelRidgeClassifier(kernel='rbf', gamma=0.1, alpha=0.1)
        clf.fit(X_train, y_train)
        preds = clf.predict(X_test)
        correct += np.sum(preds == y_test)
        
    return correct / X.shape[0]

def main():
    print("==================================================")
    print("CASO IV: Comparación de Calidad de Proveedores FTIR")
    print("==================================================")
    
    # 1. Load base spectrum
    base_file = os.path.join(os.path.dirname(__file__), "GO coque s lav ox.txt")
    if not os.path.exists(base_file):
        print(f"Error: Base spectrum file '{base_file}' not found.")
        return
        
    print(f"Cargando espectro base desde '{os.path.basename(base_file)}'...")
    x, y_trans = load_data(base_file, FTIR)
    y_abs = transmittance_to_absorbance(y_trans)
    
    # Preprocess base spectrum (Savitzky-Golay + ASLS)
    _, y_clean = preprocess_spectrum(x, y_abs, "Savitzky_Golay(11, 2)", "asls(lam=1e5, p=0.001)", space='absorbance')
    
    # 2. Generate 180 quality samples
    print("Generando 180 muestras de calidad para 3 proveedores (60 muestras por proveedor)...")
    X_raw, y, class_map = generate_ftir_quality_samples(x, y_clean, n_samples=180, seed=42)
    
    # 3. Preprocess and Normalize samples
    # We apply vector (L2) normalization to standardize spectral scales
    print("Preprocesando y aplicando normalización vectorial (L2) a los espectros...")
    X_prep = []
    for spec in X_raw:
        # Preprocess each sample to estimate its baseline and smooth
        # For simplicity, we directly normalize the simulated spectrum
        norm_spec = normalize_spectra(spec, method="vector")
        X_prep.append(norm_spec)
    X_prep = np.array(X_prep)
    
    # 4. Perform Principal Component Analysis (PCA)
    print("Ejecutando Análisis de Componentes Principales (PCA) mediante SVD...")
    pca = PCA(n_components=2)
    X_pca = pca.fit_transform(X_prep)
    explained_var = pca.explained_variance_ratio_
    
    print(f"Varianza explicada: PC1 = {explained_var[0]*100:.2f}%, PC2 = {explained_var[1]*100:.2f}%")
    
    # 5. Plot PCA Score Space
    os.makedirs(os.path.join(os.path.dirname(__file__), "images"), exist_ok=True)
    output_image = os.path.join(os.path.dirname(__file__), "images", "pca_scores_ftir_quality.png")
    
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "Arial", "Inter", "Liberation Sans"]
    fig, ax = plt.subplots(figsize=(8, 6), dpi=300)
    
    colors = {0: 'green', 1: 'orange', 2: 'red'}
    markers = {0: 'o', 1: 's', 2: '^'}
    
    for class_val, class_name in class_map.items():
        mask = (y == class_val)
        ax.scatter(
            X_pca[mask, 0], X_pca[mask, 1],
            label=class_name,
            color=colors[class_val],
            marker=markers[class_val],
            alpha=0.8, edgecolors='black', s=50
        )
        
    ax.set_xlabel(f"PC1 ({explained_var[0]*100:.1f}%)", fontsize=11)
    ax.set_ylabel(f"PC2 ({explained_var[1]*100:.1f}%)", fontsize=11)
    ax.set_title("Espacio de Puntuaciones PCA (Comparación de Proveedores FTIR)", fontsize=12, fontweight='bold', pad=10)
    ax.legend(loc='best', frameon=True, edgecolor='black', fontsize=9)
    ax.grid(True, linestyle='--', alpha=0.5)
    
    plt.tight_layout()
    plt.savefig(output_image, bbox_inches='tight', dpi=300)
    plt.close()
    print(f"Gráfico de PCA guardado en '{output_image}'.")
    
    # 6. Classification and Cross-validation
    print("Validando el clasificador Kernel Ridge (Kernel RBF) con validación cruzada de 5 pliegues...")
    accuracy = run_cross_validation(X_prep, y, folds=5)
    print(f"Precisión de clasificación (Clasificación de Proveedores): {accuracy*100:.2f}%")
    
    # 7. Train a final model and predict a mock new sample
    clf = KernelRidgeClassifier(kernel='rbf', gamma=0.1, alpha=0.1)
    clf.fit(X_prep, y)
    
    # Generate a single new sample from Provider C
    samples_new, single_y, _ = generate_ftir_quality_samples(x, y_clean, n_samples=180, seed=99)
    new_raw_sample = samples_new[150] # Index in Provider C class
    new_norm_sample = normalize_spectra(new_raw_sample, method="vector").reshape(1, -1)
    pred_class = clf.predict(new_norm_sample)[0]
    print(f"Predicción para una nueva muestra ciega del Proveedor C: '{class_map[pred_class]}'")

if __name__ == "__main__":
    main()
