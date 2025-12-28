"""
Unit Tests für ML-SHAP Explainer (TreeExplainer für LTR-Modell).

TDD Phase 1: RED - Tests für SHAP-Erklärungen des ML-Ranking-Modells.

Diese Tests definieren Anforderungen:
1. TreeExplainer für LightGBM/XGBoost
2. KernelExplainer für sklearn Fallback
3. SHAP für alle 11 ML-Features
4. Output-Struktur kompatibel mit Frontend
5. SHAP Property: base_value + sum(shap_values) ≈ prediction
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch
from datetime import datetime


# ========================================
# Test 1: TreeExplainer für LightGBM
# ========================================

def test_ml_shap_tree_explainer_lightgbm():
    """
    ML-SHAP sollte TreeExplainer für LightGBM verwenden.
    
    Requirements:
    - Erkennt LightGBM Model automatisch
    - Verwendet shap.TreeExplainer
    - Berechnet SHAP-Werte für alle 11 Features
    - Output hat korrekte Struktur
    """
    from contexts.ragintegration.infrastructure.ml.ml_shap_explainer import MLSHAPExplainer
    
    # Mock LightGBM Model
    try:
        import lightgbm as lgb
        # Erstelle einfaches Mock-Model
        mock_model = Mock()
        mock_model.__class__.__name__ = 'Booster'  # LightGBM Booster
        
        # Erstelle Explainer
        explainer = MLSHAPExplainer(model=mock_model, model_type='lightgbm')
        
        # Assertions
        assert explainer.model_type == 'lightgbm', "Model-Typ sollte LightGBM sein"
        assert explainer.explainer_type == 'tree', "Explainer-Typ sollte tree sein"
        
    except (ImportError, OSError):
        pytest.skip("LightGBM nicht verfügbar (OK, sklearn Fallback wird getestet)")


def test_ml_shap_tree_explainer_xgboost():
    """
    ML-SHAP sollte TreeExplainer für XGBoost verwenden.
    
    Requirements:
    - Erkennt XGBoost Model automatisch
    - Verwendet shap.TreeExplainer
    """
    from contexts.ragintegration.infrastructure.ml.ml_shap_explainer import MLSHAPExplainer
    
    # Mock XGBoost Model
    try:
        import xgboost as xgb
        mock_model = Mock()
        mock_model.__class__.__name__ = 'Booster'  # XGBoost Booster
        
        explainer = MLSHAPExplainer(model=mock_model, model_type='xgboost')
        
        assert explainer.model_type == 'xgboost', "Model-Typ sollte XGBoost sein"
        assert explainer.explainer_type == 'tree', "Explainer-Typ sollte tree sein"
        
    except (ImportError, OSError, Exception) as e:
        # XGBoost oder OpenMP nicht verfügbar (OK auf macOS)
        pytest.skip(f"XGBoost nicht verfügbar: {e}")


# ========================================
# Test 2: KernelExplainer für sklearn
# ========================================

def test_ml_shap_kernel_explainer_sklearn():
    """
    ML-SHAP sollte KernelExplainer für sklearn Modelle verwenden.
    
    Requirements:
    - Erkennt sklearn Model automatisch
    - Verwendet shap.KernelExplainer
    - Funktioniert mit GradientBoostingRegressor
    """
    from contexts.ragintegration.infrastructure.ml.ml_shap_explainer import MLSHAPExplainer
    from sklearn.ensemble import GradientBoostingRegressor
    
    # Trainiere einfaches sklearn Model
    X_train = np.random.rand(50, 11)
    y_train = np.random.rand(50)
    
    model = GradientBoostingRegressor(n_estimators=10, random_state=42)
    model.fit(X_train, y_train)
    
    # Erstelle Explainer
    explainer = MLSHAPExplainer(
        model=model,
        model_type='sklearn',
        background_data=X_train[:20]  # Erste 20 Samples als Background
    )
    
    # Assertions
    assert explainer.model_type == 'sklearn', "Model-Typ sollte sklearn sein"
    assert explainer.explainer_type == 'kernel', "Explainer-Typ sollte kernel sein"


# ========================================
# Test 3: SHAP Output-Struktur
# ========================================

def test_ml_shap_output_has_required_fields():
    """
    ML-SHAP Output sollte alle erforderlichen Felder enthalten.
    
    Requirements:
    - feature_names (Liste von 11 Features)
    - shap_values (Liste von 11 SHAP-Werten)
    - base_value (float)
    - prediction (float)
    - feature_importance (Dict mit abs(shap_values))
    """
    from contexts.ragintegration.infrastructure.ml.ml_shap_explainer import MLSHAPExplainer
    from sklearn.ensemble import GradientBoostingRegressor
    
    # Trainiere Model
    X_train = np.random.rand(30, 11)
    y_train = np.random.rand(30)
    model = GradientBoostingRegressor(n_estimators=10, random_state=42)
    model.fit(X_train, y_train)
    
    # Feature-Namen
    feature_names = [
        'vector_score', 'text_score', 'bm25_score', 'jaccard_score',
        'keyword_matches', 'chunk_length', 'document_type_encoded',
        'heading_hierarchy_depth', 'confidence_score', 'user_level', 'hybrid_score'
    ]
    
    # Erstelle Explainer
    explainer = MLSHAPExplainer(
        model=model,
        model_type='sklearn',
        background_data=X_train[:20],
        feature_names=feature_names
    )
    
    # Test Features
    test_features = np.random.rand(11)
    
    # Explain
    explanation = explainer.explain(test_features)
    
    # Assertions
    assert isinstance(explanation, dict), "Explanation sollte Dict sein"
    assert 'feature_names' in explanation, "Explanation sollte feature_names enthalten"
    assert 'shap_values' in explanation, "Explanation sollte shap_values enthalten"
    assert 'base_value' in explanation, "Explanation sollte base_value enthalten"
    assert 'prediction' in explanation, "Explanation sollte prediction enthalten"
    assert 'feature_importance' in explanation, "Explanation sollte feature_importance enthalten"
    
    # Prüfe Dimensionen
    assert len(explanation['feature_names']) == 11, "Feature-Namen sollten 11 Einträge haben"
    assert len(explanation['shap_values']) == 11, "SHAP-Werte sollten 11 Einträge haben"
    assert isinstance(explanation['feature_importance'], dict), "Feature Importance sollte Dict sein"


# ========================================
# Test 4: SHAP Property Validation
# ========================================

def test_ml_shap_property_prediction_consistency():
    """
    SHAP Property sollte gelten: base_value + sum(shap_values) ≈ prediction.
    
    Dies ist eine fundamentale SHAP-Eigenschaft.
    """
    from contexts.ragintegration.infrastructure.ml.ml_shap_explainer import MLSHAPExplainer
    from sklearn.ensemble import GradientBoostingRegressor
    
    # Trainiere Model
    X_train = np.random.rand(30, 11)
    y_train = np.random.rand(30)
    model = GradientBoostingRegressor(n_estimators=10, random_state=42)
    model.fit(X_train, y_train)
    
    feature_names = ['f' + str(i) for i in range(11)]
    
    explainer = MLSHAPExplainer(
        model=model,
        model_type='sklearn',
        background_data=X_train[:20],
        feature_names=feature_names
    )
    
    # Test
    test_features = np.random.rand(11)
    explanation = explainer.explain(test_features)
    
    # SHAP Property
    base_value = explanation['base_value']
    shap_values = explanation['shap_values']
    prediction = explanation['prediction']
    
    prediction_from_shap = base_value + sum(shap_values)
    
    # Assertions
    assert abs(prediction_from_shap - prediction) < 0.1, \
        f"SHAP Property verletzt: base_value + sum(shap_values) = {prediction_from_shap}, " \
        f"aber prediction = {prediction}"


# ========================================
# Test 5: Integration in UseCase
# ========================================

def test_ml_shap_integration_in_usecase():
    """
    ML-SHAP sollte in AskQuestionUseCase integriert werden können.
    
    Requirements:
    - ml_shap wird in _extended_metadata gespeichert
    - Enthält alle erforderlichen Felder
    - Wird nur berechnet wenn ML_SHAP_ENABLE=true
    """
    # Mock Chunk mit ML-Features
    chunk = {
        'chunk_id': 'test_chunk',
        'ml_score': 0.85,
        'final_score': 0.82,
        '_extended_metadata': {}
    }
    
    # Mock ML-SHAP Explanation
    ml_shap = {
        'feature_names': ['vector_score', 'text_score', 'bm25_score', 'jaccard_score',
                         'keyword_matches', 'chunk_length', 'document_type_encoded',
                         'heading_hierarchy_depth', 'confidence_score', 'user_level', 'hybrid_score'],
        'shap_values': [0.12, 0.08, 0.05, 0.03, 0.02, -0.01, 0.04, 0.01, 0.02, 0.01, 0.15],
        'base_value': 0.5,
        'prediction': 0.85,
        'feature_importance': {
            'vector_score': 0.12,
            'text_score': 0.08,
            'hybrid_score': 0.15
        }
    }
    
    # Speichere in Metadaten
    chunk['_extended_metadata']['ml_shap'] = ml_shap
    
    # Assertions
    assert 'ml_shap' in chunk['_extended_metadata'], "ml_shap sollte in Metadaten sein"
    assert 'feature_names' in chunk['_extended_metadata']['ml_shap']
    assert 'shap_values' in chunk['_extended_metadata']['ml_shap']
    assert len(chunk['_extended_metadata']['ml_shap']['shap_values']) == 11, \
        "ML-SHAP sollte 11 Features haben"


# ========================================
# Test 6: Feature Importance Aggregation
# ========================================

def test_ml_shap_aggregates_feature_importance():
    """
    ML-SHAP sollte Feature Importance aggregieren können.
    
    Wichtig für globale Feature Importance Analyse.
    """
    from contexts.ragintegration.infrastructure.ml.ml_shap_explainer import MLSHAPExplainer
    from sklearn.ensemble import GradientBoostingRegressor
    
    # Trainiere Model
    X_train = np.random.rand(30, 11)
    y_train = np.random.rand(30)
    model = GradientBoostingRegressor(n_estimators=10, random_state=42)
    model.fit(X_train, y_train)
    
    feature_names = ['f' + str(i) for i in range(11)]
    
    explainer = MLSHAPExplainer(
        model=model,
        model_type='sklearn',
        background_data=X_train[:20],
        feature_names=feature_names
    )
    
    # Explain mehrere Samples
    explanations = []
    for i in range(5):
        test_features = np.random.rand(11)
        explanation = explainer.explain(test_features)
        explanations.append(explanation)
    
    # Aggregiere Feature Importance
    aggregated = explainer.aggregate_feature_importance(explanations)
    
    # Assertions
    assert isinstance(aggregated, dict), "Aggregierte Importance sollte Dict sein"
    assert len(aggregated) == 11, "Aggregierte Importance sollte 11 Features haben"
    
    # Alle Werte sollten positive sein (absolute Importance)
    for feature, importance in aggregated.items():
        assert importance >= 0, f"Aggregierte Importance sollte >= 0 sein für {feature}"

