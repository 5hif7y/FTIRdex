"""
Biomedical and Analytical Statistics and Machine Learning Module
-----------------------------------------------------------------
Provides statistical algorithms (PCA), classifiers (Kernel Ridge, Nearest Centroid),
and mock sample generators for FTIR and Raman spectroscopy.
"""

import numpy as np

class NearestCentroidClassifier:
    """Nearest Centroid classifier for spectral data (distance-based classification)."""
    def __init__(self):
        self.centroids = {}
        self.classes = None
        
    def fit(self, X, y):
        self.classes = np.unique(y)
        for c in self.classes:
            self.centroids[c] = np.mean(X[y == c], axis=0)
        return self
        
    def predict(self, X):
        n_test = X.shape[0]
        preds = np.zeros(n_test, dtype=self.classes.dtype)
        for i, sample in enumerate(X):
            best_class = None
            min_dist = np.inf
            for c in self.classes:
                dist = np.linalg.norm(sample - self.centroids[c])
                if dist < min_dist:
                    min_dist = dist
                    best_class = c
            preds[i] = best_class
        return preds

class KernelRidgeClassifier:
    """
    Regularized Least Squares Classifier (RLSC) supporting linear and RBF kernels.
    Provides diagnostic-grade classification matching SVM performance.
    """
    def __init__(self, kernel='rbf', gamma=1.0, alpha=1.0):
        self.kernel = kernel
        self.gamma = gamma
        self.alpha = alpha
        self.X_train = None
        self.y_train = None
        self.classes = None
        self.alphas = {}
        
    def _compute_kernel(self, X1, X2):
        if self.kernel == 'linear':
            return np.dot(X1, X2.T)
        elif self.kernel == 'rbf':
            # Pairwise squared Euclidean distance: ||x||^2 + ||y||^2 - 2x.y
            sq1 = np.sum(X1**2, axis=1).reshape(-1, 1)
            sq2 = np.sum(X2**2, axis=1).reshape(1, -1)
            dists = sq1 + sq2 - 2 * np.dot(X1, X2.T)
            dists = np.clip(dists, 0, None)  # Prevent numerical precision underflow
            return np.exp(-self.gamma * dists)
        else:
            raise ValueError(f"Unknown kernel type: {self.kernel}")
            
    def fit(self, X, y):
        self.X_train = np.copy(X)
        self.y_train = np.copy(y)
        self.classes = np.unique(y)
        
        n_samples = X.shape[0]
        K = self._compute_kernel(X, X)
        
        # Dual weights system: (K + alpha * I) * alphas = y_binary
        reg_matrix = K + self.alpha * np.eye(n_samples)
        
        if len(self.classes) == 2:
            # Binary class labels are set to +1.0 and -1.0
            y_binary = np.where(y == self.classes[0], 1.0, -1.0)
            theta = np.linalg.solve(reg_matrix, y_binary)
            self.alphas[self.classes[0]] = theta
            self.alphas[self.classes[1]] = -theta
        else:
            # One-vs-Rest (OvR) multiclass scheme
            for c in self.classes:
                y_binary = np.where(y == c, 1.0, -1.0)
                theta = np.linalg.solve(reg_matrix, y_binary)
                self.alphas[c] = theta
                
        return self
        
    def predict(self, X):
        # Compute test-to-train kernel matrix
        K_test = self._compute_kernel(X, self.X_train)
        
        scores = {}
        for c in self.classes:
            theta = self.alphas[c]
            scores[c] = np.dot(K_test, theta)
            
        n_test = X.shape[0]
        preds = np.zeros(n_test, dtype=self.classes.dtype)
        
        for i in range(n_test):
            best_class = None
            best_score = -np.inf
            for c in self.classes:
                score = scores[c][i]
                if score > best_score:
                    best_score = score
                    best_class = c
            preds[i] = best_class
            
        return preds

class PCA:
    """
    Principal Component Analysis (PCA) implementation using Singular Value Decomposition (SVD).
    """
    def __init__(self, n_components=2):
        self.n_components = n_components
        self.mean_ = None
        self.components_ = None
        self.explained_variance_ = None
        self.explained_variance_ratio_ = None
        
    def fit(self, X):
        self.mean_ = np.mean(X, axis=0)
        X_centered = X - self.mean_
        
        # SVD: X = U * S * V^T
        U, S, Vt = np.linalg.svd(X_centered, full_matrices=False)
        self.components_ = Vt[:self.n_components]
        
        # Calculate variance
        n_samples = X.shape[0]
        var = (S**2) / (n_samples - 1)
        self.explained_variance_ = var[:self.n_components]
        self.explained_variance_ratio_ = var[:self.n_components] / np.sum(var)
        return self
        
    def transform(self, X):
        X_centered = X - self.mean_
        return np.dot(X_centered, self.components_.T)
        
    def fit_transform(self, X):
        self.fit(X)
        return self.transform(X)

def generate_ftir_quality_samples(x, y_base, n_samples=180, seed=42):
    """
    Generates fictitious FTIR samples simulating different material providers to explain
    statistical quality control mechanism:
    - Provider A (High Quality): Highly reduced GO, very low oxygen functional group peaks, low noise, minimal drift.
    - Provider B (Medium Quality): Partially reduced GO, moderate oxygen peaks, moderate noise, moderate drift.
    - Provider C (Low Quality): Unreduced GO, high oxygen peaks, high noise, severe drift.
    
    Returns:
        X (np.ndarray): Generated spectra matrix (n_samples x len(x))
        y (np.ndarray): Labels (0: Provider A, 1: Provider B, 2: Provider C)
        class_map (dict): Mapping of numeric labels to class names
    """
    np.random.seed(seed)
    L = len(x)
    X_samples = []
    y_labels = []
    
    # Normalize x to [0, 1] for baseline simulation
    x_norm = (x - x.min()) / (x.max() - x.min())
    
    # Define simulated oxygen peaks: O-H (~3400 cm-1), C=O (~1720 cm-1), C-O (~1050 cm-1)
    peak_3400 = np.exp(-((x - 3400)/250)**2)
    peak_1720 = np.exp(-((x - 1720)/50)**2)
    peak_1050 = np.exp(-((x - 1050)/60)**2)
    
    limit1 = n_samples // 3
    limit2 = 2 * (n_samples // 3)
    
    for i in range(n_samples):
        if i < limit1:
            # Provider A: High Quality
            label = 0
            noise_std = 0.005
            drift_amp = 0.02
            scale = np.random.uniform(0.95, 1.05)
            # Highly reduced GO, almost no functional group peaks
            chem_sig = 0.05 * peak_3400 + 0.05 * peak_1720 + 0.05 * peak_1050
        elif i < limit2:
            # Provider B: Medium Quality
            label = 1
            noise_std = 0.03
            drift_amp = 0.15
            scale = np.random.uniform(0.85, 1.15)
            # Partially reduced GO, moderate carbonyl (1720) and C-O (1050), low O-H (3400)
            chem_sig = 0.1 * peak_3400 + 2.0 * peak_1720 + 1.0 * peak_1050
        else:
            # Provider C: Low Quality
            label = 2
            noise_std = 0.09
            drift_amp = 0.40
            scale = np.random.uniform(0.70, 1.30)
            # Unreduced GO, very high O-H (3400), moderate C=O (1720)
            chem_sig = 4.0 * peak_3400 + 0.5 * peak_1720 + 3.0 * peak_1050
            
        # Base spectrum scaled
        y_sim = y_base * scale + chem_sig
        
        # Add random baseline drift (linear + quadratic)
        c1 = np.random.uniform(-drift_amp, drift_amp)
        c2 = np.random.uniform(-drift_amp/2, drift_amp/2)
        baseline_drift = c1 * x_norm + c2 * (x_norm ** 2)
        y_sim += baseline_drift
        
        # Add Gaussian noise
        noise = np.random.normal(0, noise_std, L)
        y_sim += noise
        
        # Add random vertical shift
        y_sim += np.random.uniform(-drift_amp/4, drift_amp/4)
        
        X_samples.append(y_sim)
        y_labels.append(label)
        
    return np.array(X_samples), np.array(y_labels), {0: "Proveedor A", 1: "Proveedor B", 2: "Proveedor C"}
