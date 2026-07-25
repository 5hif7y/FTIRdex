import numpy as np
import pytest
from ftir_library.stats import (
    KernelRidgeClassifier,
    PCA,
    generate_ftir_quality_samples
)

def test_regression_quality_classification():
    # Setup standard simulation
    x = np.linspace(400, 4000, 1000)
    # Sinusoidal baseline with simulated peak
    y_base = 0.5 * np.sin(x/500) + 1.0 + np.exp(-((x - 1650)/100)**2)
    
    # Generate 90 samples (30 per provider)
    X_raw, y, class_map = generate_ftir_quality_samples(x, y_base, n_samples=90, seed=42)
    
    from ftir_library.raman import normalize_spectra
    X = np.array([normalize_spectra(spec, method='vector') for spec in X_raw])
    
    # 5-Fold Cross Validation check
    folds = 5
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
        
    accuracy = correct / X.shape[0]
    
    # We expect high classification accuracy (>90%) on simulated datasets
    # because noise levels are distinct between high, medium, and low quality.
    assert accuracy >= 0.90, f"Regression check failed: classification accuracy was only {accuracy:.2%}"

def test_regression_pca_variance():
    # Setup data with variance mostly in first coordinate
    np.random.seed(42)
    x1 = np.random.normal(0, 5, 50)
    x2 = np.random.normal(0, 0.5, 50)
    X = np.column_stack((x1, x2))
    
    pca = PCA(n_components=2)
    pca.fit(X)
    
    # PC1 should explain the vast majority of variance (>95%)
    assert pca.explained_variance_ratio_[0] > 0.95, (
        f"Regression check failed: PC1 explained variance was only {pca.explained_variance_ratio_[0]:.2%}"
    )
