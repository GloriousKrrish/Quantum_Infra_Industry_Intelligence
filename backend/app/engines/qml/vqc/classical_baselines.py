"""
classical_baselines.py - Classical Machine Learning Baselines Suite.

Provides standard Scikit-learn baselines for rigorous, fair comparison against VQC:
  1. Logistic Regression
  2. Support Vector Machine (Linear Kernel)
  3. Support Vector Machine (RBF Non-linear Kernel)
  4. Decision Tree Classifier
  5. Random Forest Classifier
  6. Multi-Layer Perceptron (MLP Neural Network)
"""

from typing import Dict, Any, Tuple, Optional
import time
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
)


class ClassicalBaselineRunner:
    """
    Trains and evaluates 6 classical ML baselines on identical dataset splits.
    """

    @classmethod
    def run_single_baseline(
        cls,
        model_name: str,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_test: np.ndarray,
        y_test: np.ndarray,
        seed: int = 42,
    ) -> Dict[str, Any]:
        """Trains one classical baseline and extracts evaluation metrics."""
        m_name = model_name.lower().replace("-", "_")

        if m_name in ("logistic_regression", "lr"):
            clf = LogisticRegression(random_state=seed, max_iter=200)
            param_count = X_train.shape[1] + 1
        elif m_name in ("linear_svm", "svm_linear"):
            clf = SVC(kernel="linear", probability=True, random_state=seed)
            param_count = X_train.shape[1] + 1
        elif m_name in ("rbf_svm", "svm_rbf", "svm"):
            clf = SVC(kernel="rbf", probability=True, random_state=seed)
            param_count = len(X_train)  # Upper bound dual coefficients
        elif m_name in ("decision_tree", "dt"):
            clf = DecisionTreeClassifier(max_depth=4, random_state=seed)
            param_count = 15
        elif m_name in ("random_forest", "rf"):
            clf = RandomForestClassifier(n_estimators=30, max_depth=4, random_state=seed)
            param_count = 30 * 15
        elif m_name in ("mlp", "neural_network", "mlp_classifier"):
            clf = MLPClassifier(hidden_layer_sizes=(16, 8), max_iter=250, random_state=seed)
            d = X_train.shape[1]
            param_count = (d * 16 + 16) + (16 * 8 + 8) + (8 * 1 + 1)
        else:
            clf = LogisticRegression(random_state=seed)
            param_count = X_train.shape[1] + 1

        # Train with timing
        t_tr0 = time.perf_counter()
        clf.fit(X_train, y_train)
        train_time_ms = (time.perf_counter() - t_tr0) * 1000.0

        # Predict with timing
        t_te0 = time.perf_counter()
        y_pred = clf.predict(X_test)
        y_prob = clf.predict_proba(X_test)[:, 1] if hasattr(clf, "predict_proba") else y_pred.astype(float)
        test_time_ms = (time.perf_counter() - t_te0) * 1000.0
        inf_latency_ms = test_time_ms / max(1, len(X_test))

        # Metrics
        acc = float(accuracy_score(y_test, y_pred))
        prec = float(precision_score(y_test, y_pred, zero_division=0))
        rec = float(recall_score(y_test, y_pred, zero_division=0))
        f1 = float(f1_score(y_test, y_pred, zero_division=0))

        try:
            auc = float(roc_auc_score(y_test, y_prob))
        except Exception:
            auc = acc

        cm = confusion_matrix(y_test, y_pred)
        tn, fp, fn, tp = int(cm[0, 0]), int(cm[0, 1]), int(cm[1, 0]), int(cm[1, 1])

        return {
            "model_name": model_name,
            "is_quantum": False,
            "accuracy": round(acc, 4),
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1_score": round(f1, 4),
            "roc_auc": round(auc, 4),
            "confusion_matrix": {"tn": tn, "fp": fp, "fn": fn, "tp": tp},
            "training_time_ms": round(train_time_ms, 2),
            "inference_latency_ms": round(inf_latency_ms, 3),
            "num_parameters": param_count,
            "hardware_note": "Classical CPU (Scikit-Learn)",
        }

    @classmethod
    def run_all_baselines(
        cls,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_test: np.ndarray,
        y_test: np.ndarray,
        seed: int = 42,
    ) -> List[Dict[str, Any]]:
        """Runs all 6 classical baselines."""
        baseline_models = [
            "Logistic Regression",
            "Linear SVM",
            "RBF Kernel SVM",
            "Decision Tree",
            "Random Forest",
            "Multi-Layer Perceptron (MLP)",
        ]
        results = []
        for name in baseline_models:
            res = cls.run_single_baseline(name, X_train, y_train, X_test, y_test, seed=seed)
            results.append(res)
        return results
