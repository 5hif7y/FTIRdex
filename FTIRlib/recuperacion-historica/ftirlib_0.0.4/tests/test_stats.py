import numpy as np
import pytest
from ftir_library.stats import (
    NearestCentroidClassifier,
    KernelRidgeClassifier,
    PCA,
    generate_ftir_quality_samples
)

def test_nearest_centroid():
    # Simple 2D classification
    X = np.array([[1.0, 1.0], [1.1, 0.9], [2.0, 2.0], [2.2, 1.8]])
    y = np.array([0, 0, 1, 1])
    
    clf = NearestCentroidClassifier()
    clf.fit(X, y)
    
    # Check predictions
    preds = clf.predict(np.array([[0.9, 1.1], [2.1, 1.9]]))
    assert np.array_equal(preds, [0, 1])

def test_kernel_ridge():
    # Binary classification with linear kernel
    X = np.array([[1.0, 1.0], [1.1, 0.9], [2.0, 2.0], [2.2, 1.8]])
    y = np.array([0, 0, 1, 1])
    
    clf = KernelRidgeClassifier(kernel='rbf', gamma=1.0, alpha=0.1)
    clf.fit(X, y)
    
    preds = clf.predict(np.array([[0.9, 1.1], [2.1, 1.9]]))
    assert np.array_equal(preds, [0, 1])
    
    # Multiclass classification with RBF kernel
    X_multi = np.array([[1.0, 1.0], [2.0, 2.0], [3.0, 3.0]])
    y_multi = np.array([0, 1, 2])
    clf_rbf = KernelRidgeClassifier(kernel='rbf', gamma=1.0, alpha=0.01)
    clf_rbf.fit(X_multi, y_multi)
    
    preds_multi = clf_rbf.predict(np.array([[1.1, 0.9], [2.0, 2.0], [2.9, 3.1]]))
    assert np.array_equal(preds_multi, [0, 1, 2])

def test_pca():
    # 3 samples, 2 dimensions. Centering should put them in a line
    X = np.array([[1.0, 2.0], [2.0, 4.0], [3.0, 6.0]])
    pca = PCA(n_components=1)
    X_trans = pca.fit_transform(X)
    
    assert X_trans.shape == (3, 1)
    assert len(pca.components_) == 1
    assert len(pca.explained_variance_ratio_) == 1
    # Check that explained variance ratio is close to 100% since they are collinear
    assert np.allclose(pca.explained_variance_ratio_[0], 1.0, atol=1e-5)

def test_generate_quality_samples():
    x = np.linspace(400, 4000, 100)
    y_base = np.sin(x/500) + 1.0
    
    X_samples, y, class_map = generate_ftir_quality_samples(x, y_base, n_samples=30, seed=42)
    
    assert X_samples.shape == (30, 100)
    assert len(y) == 30
    assert 0 in y
    assert 1 in y
    assert 2 in y
    assert class_map[0] == "Proveedor A"
