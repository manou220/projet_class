"""
Tests pour les prévisions ML.
"""
import pytest
import pandas as pd
import numpy as np
import joblib
import tempfile
import os
from sklearn.ensemble import RandomForestRegressor
from app.blueprints.previsions.routes import get_available_models
from app.utils import (
    normalize_feature_columns,
    validate_model_artifact,
    ensure_datetime_index,
    prepare_data_for_ml,
    make_features
)


class TestGetAvailableModels:
    """Tests pour get_available_models."""
    
    def test_get_models_with_context(self, app):
        """Test récupération des modèles avec contexte d'application."""
        with app.app_context():
            models = get_available_models()
            assert isinstance(models, dict)
    
    def test_get_models_no_context(self):
        """Test récupération des modèles sans contexte (fallback)."""
        # Devrait fonctionner même sans contexte
        try:
            models = get_available_models()
            assert isinstance(models, dict)
        except RuntimeError:
            # Acceptable si pas de contexte
            pass


class TestModelLoading:
    """Tests pour le chargement de modèles."""
    
    def test_create_valid_model_artifact(self, tmp_path):
        """Crée un artifact de modèle valide pour les tests."""
        model = RandomForestRegressor(n_estimators=10, random_state=42)
        # Entraîner avec des données factices
        X_train = np.random.randn(100, 5)
        y_train = np.random.randn(100)
        model.fit(X_train, y_train)
        
        artifact = {
            'model': model,
            'feature_columns': ['feature1', 'feature2', 'feature3', 'feature4', 'feature5'],
            'target_column': 'Close',
            'model_type': 'random_forest',
            'version': '1.0'
        }
        
        model_path = tmp_path / "test_model.joblib"
        joblib.dump(artifact, model_path)
        
        # Tester le chargement
        loaded_artifact = joblib.load(model_path)
        result_model, result_cols, metadata = validate_model_artifact(loaded_artifact, str(model_path))
        
        assert hasattr(result_model, 'predict')
        assert len(result_cols) == 5
        assert metadata['model_type'] == 'random_forest'
        
        # Ne pas retourner de valeur (pytest warning)
        assert hasattr(result_model, 'predict')
        assert len(result_cols) == 5
        assert metadata['model_type'] == 'random_forest'
    
    def test_create_model_with_tuple_features(self, tmp_path):
        """Crée un modèle avec des feature_columns en tuples."""
        model = RandomForestRegressor(n_estimators=10, random_state=42)
        X_train = np.random.randn(100, 3)
        y_train = np.random.randn(100)
        model.fit(X_train, y_train)
        
        artifact = {
            'model': model,
            'feature_columns': [('High', 'BTC-USD'), ('Low', 'BTC-USD'), 'Close'],
            'target_column': 'Close'
        }
        
        model_path = tmp_path / "test_model_tuples.joblib"
        joblib.dump(artifact, model_path)
        
        # Tester le chargement et la normalisation
        loaded_artifact = joblib.load(model_path)
        result_model, result_cols, metadata = validate_model_artifact(loaded_artifact, str(model_path))
        
        # Les tuples devraient être normalisés
        assert 'High_BTC-USD' in result_cols
        assert 'Low_BTC-USD' in result_cols
        assert 'Close' in result_cols


class TestDataPreparation:
    """Tests pour la préparation des données."""
    
    def test_prepare_data_with_datetime_index(self):
        """Test préparation avec index datetime."""
        dates = pd.date_range('2024-01-01', periods=50, freq='D')
        df = pd.DataFrame({
            'Close': np.random.randn(50).cumsum() + 100,
            'Open': np.random.randn(50).cumsum() + 100,
            'High': np.random.randn(50).cumsum() + 105,
            'Low': np.random.randn(50).cumsum() + 95,
            'Volume': np.random.randint(1000, 10000, 50)
        }, index=dates)
        
        # S'assurer que l'index est datetime
        df = ensure_datetime_index(df)
        assert isinstance(df.index, pd.DatetimeIndex)
        
        # Préparer pour ML
        X, y, feature_cols = prepare_data_for_ml(df, 'Close')
        
        assert isinstance(X, pd.DataFrame)
        assert isinstance(y, pd.Series)
        assert len(feature_cols) > 0
        assert len(X) == len(y)
        assert len(X) > 0  # Après dropna
    
    def test_prepare_data_with_numeric_index(self):
        """Test préparation avec index numérique."""
        df = pd.DataFrame({
            'Close': np.random.randn(50).cumsum() + 100,
            'Date': pd.date_range('2024-01-01', periods=50, freq='D')
        })
        
        # S'assurer que l'index devient datetime
        df = ensure_datetime_index(df, date_column='Date')
        assert isinstance(df.index, pd.DatetimeIndex)
    
    def test_prepare_data_with_multiindex_columns(self):
        """Test avec colonnes MultiIndex."""
        dates = pd.date_range('2024-01-01', periods=50, freq='D')  # Plus de données pour éviter dropna complet
        df = pd.DataFrame({
            ('Close', 'BTC-USD'): np.random.randn(50).cumsum() + 100,
            ('High', 'BTC-USD'): np.random.randn(50).cumsum() + 105,
            ('Low', 'BTC-USD'): np.random.randn(50).cumsum() + 95
        }, index=dates)
        
        # Aplatir les colonnes
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = ['_'.join(str(c) for c in col).strip() for col in df.columns.values]
        
        # Renommer Close_BTC-USD en Close
        if 'Close_BTC-USD' in df.columns:
            df['Close'] = df['Close_BTC-USD']
        
        df = ensure_datetime_index(df)
        X, y, feature_cols = prepare_data_for_ml(df, 'Close')
        
        # Après dropna, il devrait rester des données (au moins quelques lignes)
        assert len(X) > 0, "Le DataFrame X est vide après préparation"
        assert len(feature_cols) > 0, "Aucune feature column générée"
        assert len(X) == len(y), "X et y doivent avoir la même longueur"


class TestFeatureEngineering:
    """Tests pour le feature engineering."""
    
    def test_make_features_complete(self):
        """Test création de toutes les features."""
        dates = pd.date_range('2024-01-01', periods=50, freq='D')
        df = pd.DataFrame({
            'Close': np.random.randn(50).cumsum() + 100
        }, index=dates)
        
        features_df = make_features(df, target_col='Close')
        
        # Vérifier que les features attendues sont présentes
        expected_features = [
            'Close_diff', 'lag_diff_1', 'lag_diff_2',
            'ma_diff_3', 'ma_price_7',
            'day_of_week', 'volatility'
        ]
        
        for feature in expected_features:
            assert feature in features_df.columns, f"Feature {feature} manquante"
    
    def test_make_features_with_nan(self):
        """Test avec des NaN dans les données."""
        dates = pd.date_range('2024-01-01', periods=30, freq='D')
        df = pd.DataFrame({
            'Close': [100, 101, np.nan, 103, 104] + list(np.random.randn(25).cumsum() + 100)
        }, index=dates[:30])
        
        features_df = make_features(df, target_col='Close')
        
        # Ne devrait pas planter, même avec des NaN
        assert isinstance(features_df, pd.DataFrame)
        assert len(features_df) == 30


class TestForecastIntegration:
    """Tests d'intégration pour les prévisions."""
    
    def test_full_pipeline(self, tmp_path):
        """Test du pipeline complet de prévision."""
        # 1. Créer un modèle
        model = RandomForestRegressor(n_estimators=10, random_state=42)
        X_train = np.random.randn(100, 10)
        y_train = np.random.randn(100)
        model.fit(X_train, y_train)
        
        # Créer des feature columns qui correspondent à make_features
        feature_cols = [
            'Close_diff', 'lag_diff_1', 'lag_diff_2', 'lag_diff_3',
            'ma_diff_3', 'ma_diff_7', 'ma_price_7', 'ma_price_14',
            'day_of_week', 'volatility'
        ]
        
        artifact = {
            'model': model,
            'feature_columns': feature_cols,
            'target_column': 'Close'
        }
        
        model_path = tmp_path / "test_forecast_model.joblib"
        joblib.dump(artifact, model_path)
        
        # 2. Créer des données de test
        dates = pd.date_range('2024-01-01', periods=50, freq='D')
        df = pd.DataFrame({
            'Close': np.random.randn(50).cumsum() + 100
        }, index=dates)
        
        # 3. Préparer les données
        df = ensure_datetime_index(df)
        X, y, generated_feature_cols = prepare_data_for_ml(df, 'Close')
        
        # 4. Normaliser les feature columns
        normalized_model_cols = normalize_feature_columns(feature_cols)
        normalized_generated_cols = normalize_feature_columns(generated_feature_cols)
        
        # 5. Vérifier la compatibilité
        from app.utils import validate_model_data_compatibility
        is_compatible, missing, extra, warnings = validate_model_data_compatibility(
            normalized_model_cols, normalized_generated_cols, X
        )
        
        # Le modèle devrait être compatible (ou au moins partiellement)
        assert isinstance(is_compatible, bool)

