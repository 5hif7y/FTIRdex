"""
Raman Biomedical Oncology Diagnosis Pipeline (v0.0.3)
------------------------------------------------------
Applies specialized Raman preprocessors and trains a high-precision Kernel Ridge
Classifier to diagnose cancer cells (melanoma) from SERS culture medium spectra.
"""

import os
import glob
import csv
import numpy as np
import matplotlib.pyplot as plt

from ftir_library import (
    correct_baseline_absorbance,
    moving_average,
    remove_cosmic_rays,
    normalize_spectra,
    KernelRidgeClassifier,
    run_raman_grid_search,
    plot_raman_pca
)

# Configuration and output paths
BASE_DATA_DIR = r"c:\Users\Shifty\Antigravity-DEV\Trabajar-0.0.2\Trabajar-0.0.2\Cells Raman Spectra"
BEST_CONFIG_FILE = "best_config_raman.txt"
RESULTS_CSV = "raman_pipeline_results.csv"

# Image paths (inside examples/images)
AVG_SPEC_IMG = "images/average_spectra_raman.png"
PCA_SCORE_IMG = "images/pca_scores_raman.png"

def load_full_dataset(subsample=None):
    """
    Loads spectra from the Cells Raman Spectra directory.
    If subsample is an integer, limits spectra loaded per CSV file (useful for fast tuning).
    """
    folders = ["A", "A-S", "G", "G-S", "HF", "HF-S", "MEL", "MEL-S", "ZAM", "ZAM-S", "DMEM", "DMEM-S"]
    X = []
    y = [] # 0: Cancer (Melanoma), 1: Healthy/Normal Cells, 2: Control DMEM Medium
    
    for folder in folders:
        folder_path = os.path.join(BASE_DATA_DIR, folder)
        if not os.path.isdir(folder_path):
            continue
            
        # Class labels
        if folder in ["A", "A-S", "G", "G-S"]:
            cls = 0  # Cancer
        elif folder in ["DMEM", "DMEM-S"]:
            cls = 2  # Control DMEM
        else:
            cls = 1  # Healthy cells / normal fibroblasts
            
        csv_files = glob.glob(os.path.join(folder_path, "*.csv"))
        for csv_file in csv_files:
            try:
                data = np.genfromtxt(csv_file, delimiter=',', skip_header=1)
                if len(data.shape) == 1:
                    data = data.reshape(1, -1)
                
                # Apply subsampling if requested
                if subsample is not None:
                    n_rows = data.shape[0]
                    step = max(1, n_rows // subsample)
                    indices = np.arange(0, n_rows, step)[:subsample]
                    data = data[indices]
                    
                for row in data:
                    if row.shape[0] == 2090:
                        X.append(row)
                        y.append(cls)
            except Exception as e:
                print(f"Error loading file {csv_file}: {e}")
                
    return np.array(X), np.array(y)

def calculate_diagnostic_metrics(y_true, y_pred):
    """
    Calculates diagnostic performance metrics (Accuracy, Sensitivity, Specificity, Confusion Matrix)
    for binary classification: Cancer (0) vs Healthy/Control (1).
    """
    # Map to binary (0: Cancer, 1: Healthy/Control)
    y_true_bin = np.where(y_true == 0, 0, 1)
    y_pred_bin = np.where(y_pred == 0, 0, 1)
    
    TP = np.sum((y_true_bin == 0) & (y_pred_bin == 0))
    TN = np.sum((y_true_bin == 1) & (y_pred_bin == 1))
    FP = np.sum((y_true_bin == 1) & (y_pred_bin == 0))
    FN = np.sum((y_true_bin == 0) & (y_pred_bin == 1))
    
    accuracy = (TP + TN) / len(y_true_bin)
    sensitivity = TP / (TP + FN) if (TP + FN) > 0 else 0.0
    specificity = TN / (TN + FP) if (TN + FP) > 0 else 0.0
    
    return {
        "Accuracy": accuracy,
        "Sensitivity": sensitivity,
        "Specificity": specificity,
        "TP": TP, "TN": TN, "FP": FP, "FN": FN
    }

def main():
    if not os.path.exists(BASE_DATA_DIR):
        print(f"Error: Data directory not found at {BASE_DATA_DIR}")
        return
        
    print("==========================================================")
    print("BIOMEDICAL RAMAN ONCOLOGY CLASSIFICATION PIPELINE (v0.0.3)")
    print("==========================================================")
    
    # 1. Load subsampled dataset for fast parameter optimization
    print("\n[Step 1/5] Loading subsampled dataset for grid search...")
    X_sub, y_sub = load_full_dataset(subsample=10)
    print(f"Loaded {len(X_sub)} spectra for hyperparameter tuning.")
    
    # 2. Run Grid Search
    print("\n[Step 2/5] Optimizing preprocessing and classifier hyperparameters...")
    best_cfg, best_acc = run_raman_grid_search(X_sub, y_sub, folds=5)
    print(f"Optimal Configuration Found (Validation Accuracy: {best_acc*100:.2f}%):")
    print(f"  Smoothing Window:  {best_cfg['smoothing_window']}")
    print(f"  Baseline Method:   {best_cfg['baseline_method']}")
    print(f"  Kernel Classifier: {best_cfg['kernel']}")
    if best_cfg['kernel'] == 'rbf':
        print(f"  RBF Gamma (g):     {best_cfg['gamma']}")
    print(f"  Regularization (a):{best_cfg['alpha']}")
    
    # Save configuration
    with open(BEST_CONFIG_FILE, "w", encoding='utf-8') as f:
        f.write(f"smoothing_window: {best_cfg['smoothing_window']}\n")
        f.write(f"baseline_method: {best_cfg['baseline_method']}\n")
        f.write(f"kernel: {best_cfg['kernel']}\n")
        f.write(f"gamma: {best_cfg['gamma']}\n")
        f.write(f"alpha: {best_cfg['alpha']}\n")
    print(f"Saved configuration to '{BEST_CONFIG_FILE}'")
    
    # 3. Load COMPLETE dataset for final training and validation (lives are on the line!)
    print("\n[Step 3/5] Loading complete dataset (+1900 spectra) for final evaluation...")
    X_full, y_full = load_full_dataset(subsample=None)
    print(f"Loaded complete dataset with {X_full.shape[0]} spectra.")
    
    # 4. Preprocess full dataset using the best parameters
    print("\n[Step 4/5] Preprocessing complete dataset (Spike removal, Smoothing, Baseline, Normalization)...")
    x = np.linspace(100, 4278, 2090)
    X_prep = []
    
    for i, raw_spec in enumerate(X_full):
        # A. Cosmic ray removal (Spike filtering)
        clean_spec = remove_cosmic_rays(raw_spec, window=11, threshold=6.0)
        # B. Smoothing
        smooth_spec = moving_average(clean_spec, window=best_cfg['smoothing_window'])
        # C. Baseline Correction
        _, corr_spec = correct_baseline_absorbance(x, smooth_spec, method=best_cfg['baseline_method'], deg=2)
        # D. Normalization L2 (Vector)
        norm_spec = normalize_spectra(corr_spec, method='vector')
        X_prep.append(norm_spec)
        
    X_prep = np.array(X_prep)
    print("Preprocessing completed.")
    
    # 5. Evaluate on complete dataset using 5-fold cross-validation
    print("\n[Step 5/5] Performing final cross-validated evaluation on complete dataset...")
    np.random.seed(42)
    indices = np.arange(X_prep.shape[0])
    np.random.shuffle(indices)
    
    folds = 5
    fold_sizes = np.full(folds, X_prep.shape[0] // folds)
    fold_sizes[:X_prep.shape[0] % folds] += 1
    
    current = 0
    predictions = np.zeros(X_prep.shape[0])
    
    for fold in range(folds):
        start, end = current, current + fold_sizes[fold]
        test_idx = indices[start:end]
        train_idx = np.setdiff1d(indices, test_idx)
        current = end
        
        X_train, y_train = X_prep[train_idx], y_full[train_idx]
        X_test, y_test = X_prep[test_idx], y_full[test_idx]
        
        clf = KernelRidgeClassifier(
            kernel=best_cfg['kernel'], 
            gamma=best_cfg['gamma'], 
            alpha=best_cfg['alpha']
        )
        clf.fit(X_train, y_train)
        predictions[test_idx] = clf.predict(X_test)
        
    # Calculate performance metrics
    multiclass_accuracy = np.mean(predictions == y_full)
    metrics = calculate_diagnostic_metrics(y_full, predictions)
    
    print("\n==========================================================")
    print("DIAGNOSTIC REPORT & CLINICAL METRICS")
    print("==========================================================")
    print(f"Multiclass Classification Accuracy:  {multiclass_accuracy*100:.2f}%")
    print(f"Cancer Binary Diagnosis Accuracy:    {metrics['Accuracy']*100:.2f}%")
    print(f"Sensitivity (Oncology True Positive): {metrics['Sensitivity']*100:.2f}%")
    print(f"Specificity (Oncology True Negative): {metrics['Specificity']*100:.2f}%")
    print("----------------------------------------------------------")
    print("CONFUSION MATRIX (Binary Diagnosis):")
    print(f"  True Positives (Cancer diagnosed as Cancer):      {metrics['TP']}")
    print(f"  True Negatives (Healthy diagnosed as Healthy):    {metrics['TN']}")
    print(f"  False Positives (Healthy diagnosed as Cancer):    {metrics['FP']}")
    print(f"  False Negatives (Cancer diagnosed as Healthy):    {metrics['FN']}")
    print("==========================================================")
    
    # Save numeric report
    with open(RESULTS_CSV, "w", newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Metric", "Value"])
        writer.writerow(["Multiclass_Accuracy", multiclass_accuracy])
        writer.writerow(["Binary_Accuracy", metrics['Accuracy']])
        writer.writerow(["Sensitivity", metrics['Sensitivity']])
        writer.writerow(["Specificity", metrics['Specificity']])
        writer.writerow(["TP", metrics['TP']])
        writer.writerow(["TN", metrics['TN']])
        writer.writerow(["FP", metrics['FP']])
        writer.writerow(["FN", metrics['FN']])
        writer.writerow(["Smoothing_Window", best_cfg['smoothing_window']])
        writer.writerow(["Baseline_Method", best_cfg['baseline_method']])
        writer.writerow(["Classifier_Kernel", best_cfg['kernel']])
        writer.writerow(["Classifier_Gamma", best_cfg['gamma']])
        writer.writerow(["Classifier_Alpha", best_cfg['alpha']])
    print(f"Saved numerical metrics report to '{RESULTS_CSV}'")
    
    # Create output directory for images if it doesn't exist
    os.makedirs("images", exist_ok=True)
    
    # 6. Generate PCA scores plot
    class_map = {0: "Cancer (Melanoma)", 1: "Healthy Cells", 2: "Control Medium"}
    plot_raman_pca(X_prep, y_full, class_map, PCA_SCORE_IMG)
    
    # 7. Generate Average Spectra Plot
    plt.figure(figsize=(10, 6))
    for c in [0, 1, 2]:
        mean_spec = np.mean(X_prep[y_full == c], axis=0)
        plt.plot(x, mean_spec, label=class_map[c], linewidth=1.5)
    plt.xlabel("Desplazamiento Raman (cm$^{-1}$)", fontsize=12)
    plt.ylabel("Intensidad Normalizada (u.a.)", fontsize=12)
    plt.title("Espectro Promedio Raman de Medios de Cultivo (v0.0.3)", fontsize=13, fontweight='bold', pad=10)
    plt.legend(frameon=True, edgecolor='black')
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.savefig(AVG_SPEC_IMG, bbox_inches='tight', dpi=300)
    plt.close()
    print(f"Average spectra plot saved to '{AVG_SPEC_IMG}'.")

if __name__ == "__main__":
    main()
