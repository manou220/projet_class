"""
Tests unitaires pour les nouvelles fonctions utilitaires ML.
"""
import pytest
import pandas as pd
import numpy as np
import joblib
import tempfile
import os
from sklearn.ensemble import RandomForestRegressor
from app.utils import (
    normalize_feature_columns,
    validate_model_artifact,
    validate_model_data_compatibility,
    ensure_datetime_index,
    prepare_features_for_prediction
)


class TestNormalizeFeatureColumns:
    """Tests pour normalize_feature_columns."""
    
    def test_normalize_strings(self):
        """Test avec des strings simples."""
        feature_cols = ['Close', 'High', 'Low']
        result = normalize_feature_columns(feature_cols)
        assert result == ['Close', 'High', 'Low']
    
    def test_normalize_tuples(self):
        """Test avec des tuples."""
        feature_cols = [('High', 'BTC-USD'), ('Low', 'BTC-USD'), 'Close']
        result = normalize_feature_columns(feature_cols)
        assert result == ['High_BTC-USD', 'Low_BTC-USD', 'Close']
    
    def test_normalize_mixed(self):
        """Test avec un mélange de tuples et strings."""
        feature_cols = ['Close', ('High', 'AAPL'), 'Low', ('Volume', 'MSFT')]
        result = normalize_feature_columns(feature_cols)
        assert result == ['Close', 'High_AAPL', 'Low', 'Volume_MSFT']
    
    def test_normalize_empty(self):
        """Test avec une liste vide."""
        result = normalize_feature_columns([])
        assert result == []
    
    def test_normalize_none(self):
        """Test avec None."""
        result = normalize_feature_columns(None)
        assert result == []


class TestValidateModelArtifact:
    """Tests pour validate_model_artifact."""
    
    def test_validate_valid_artifact(self):
        """Test avec un artifact valide."""
        model = RandomForestRegressor(n_estimators=10)
        model.fit([[1, 2], [3, 4]], [1, 2])
        
        artifact = {
            'model': model,
            'feature_columns': ['feature1', 'feature2']
        }
        
        result_model, result_cols, metadata = validate_model_artifact(artifact)
        assert result_model == model
        assert result_cols == ['feature1', 'feature2']
        assert isinstance(metadata, dict)
    
    def test_validate_artifact_with_tuples(self):
        """Test avec des feature_columns en tuples."""
        model = RandomForestRegressor(n_estimators=10)
        model.fit([[1, 2], [3, 4]], [1, 2])
        
        artifact = {
            'model': model,
            'feature_columns': [('High', 'BTC-USD'), ('Low', 'BTC-USD')]
        }
        
        result_model, result_cols, metadata = validate_model_artifact(artifact)
        assert result_cols == ['High_BTC-USD', 'Low_BTC-USD']
    
    def test_validate_missing_model(self):
        """Test avec un artifact sans 'model'."""
        artifact = {
            'feature_columns': ['feature1', 'feature2']
        }
        
        with pytest.raises(ValueError, match="ne contient pas de clé 'model'"):
            validate_model_artifact(artifact)
    
    def test_validate_missing_feature_columns(self):
        """Test avec un artifact sans 'feature_columns'."""
        model = RandomForestRegressor(n_estimators=10)
        model.fit([[1, 2], [3, 4]], [1, 2])
        
        artifact = {
            'model': model
        }
        
        with pytest.raises(ValueError, match="ne contient pas de clé 'feature_columns'"):
            validate_model_artifact(artifact)
    
    def test_validate_invalid_model(self):
        """Test avec un modèle invalide (sans méthode predict)."""
        artifact = {
            'model': {'not': 'a model'},
            'feature_columns': ['feature1']
        }
        
        with pytest.raises(ValueError, match="n'a pas de méthode 'predict'"):
            validate_model_artifact(artifact)
    
    def test_validate_empty_feature_columns(self):
        """Test avec feature_columns vide."""
        model = RandomForestRegressor(n_estimators=10)
        model.fit([[1, 2], [3, 4]], [1, 2])
        
        artifact = {
            'model': model,
            'feature_columns': []
        }
        
        with pytest.raises(ValueError, match="liste de feature_columns vide"):
            validate_model_artifact(artifact)


class TestValidateModelDataCompatibility:
    """Tests pour validate_model_data_compatibility."""
    
    def test_compatible(self):
        """Test avec des données compatibles."""
        model_cols = ['feature1', 'feature2', 'feature3']
        data_cols = ['feature1', 'feature2', 'feature3', 'extra']
        
        is_compatible, missing, extra, warnings = validate_model_data_compatibility(
            model_cols, data_cols
        )
        
        assert is_compatible == True
        assert len(missing) == 0
        assert len(extra) == 1
        assert 'extra' in extra
    
    def test_incompatible_missing(self):
        """Test avec des colonnes manquantes."""
        model_cols = ['feature1', 'feature2', 'feature3']
        data_cols = ['feature1', 'feature2']
        
        is_compatible, missing, extra, warnings = validate_model_data_compatibility(
            model_cols, data_cols
        )
        
        assert is_compatible == False
        assert 'feature3' in missing
        assert len(extra) == 0
    
    def test_incompatible_extra(self):
        """Test avec des colonnes supplémentaires."""
        model_cols = ['feature1', 'feature2']
        data_cols = ['feature1', 'feature2', 'feature3', 'feature4']
        
        is_compatible, missing, extra, warnings = validate_model_data_compatibility(
            model_cols, data_cols
        )
        
        assert is_compatible == True
        assert len(missing) == 0
        assert len(extra) == 2


class TestEnsureDatetimeIndex:
    """Tests pour ensure_datetime_index."""
    
    def test_already_datetime_index(self):
        """Test avec un DataFrame qui a déjà un DatetimeIndex."""
        dates = pd.date_range('2024-01-01', periods=10, freq='D')
        df = pd.DataFrame({'value': range(10)}, index=dates)
        
        result = ensure_datetime_index(df)
        assert isinstance(result.index, pd.DatetimeIndex)
        assert len(result) == 10
    
    def test_numeric_index(self):
        """Test avec un index numérique."""
        df = pd.DataFrame({'value': range(10)})
        
        result = ensure_datetime_index(df)
        assert isinstance(result.index, pd.DatetimeIndex)
        assert len(result) == 10
    
    def test_with_date_column(self):
        """Test avec une colonne Date."""
        df = pd.DataFrame({
            'Date': pd.date_range('2024-01-01', periods=10, freq='D'),
            'value': range(10)
        })
        
        result = ensure_datetime_index(df, date_column='Date')
        assert isinstance(result.index, pd.DatetimeIndex)
        assert 'Date' not in result.columns  # Devrait être l'index
    
    def test_string_index(self):
        """Test avec un index de strings."""
        df = pd.DataFrame({
            'value': range(10)
        }, index=[f'2024-01-{i+1:02d}' for i in range(10)])
        
        result = ensure_datetime_index(df)
        assert isinstance(result.index, pd.DatetimeIndex)


class TestPrepareFeaturesForPrediction:
    """Tests pour prepare_features_for_prediction."""
    
    def test_prepare_complete_features(self):
        """Test avec toutes les features présentes."""
        dates = pd.date_range('2024-01-01', periods=20, freq='D')
        features_df = pd.DataFrame({
            'Close_diff': np.random.randn(20),
            'lag_diff_1': np.random.randn(20),
            'ma_diff_3': np.random.randn(20),
            'volatility': np.random.randn(20)
        }, index=dates)
        
        model_cols = ['Close_diff', 'lag_diff_1', 'ma_diff_3', 'volatility']
        current_df = pd.DataFrame({'Close': range(100, 120)}, index=dates)
        
        result = prepare_features_for_prediction(
            features_df, model_cols, current_df=current_df, target_column='Close'
        )
        
        assert isinstance(result, pd.DataFrame)
        assert len(result.columns) == len(model_cols)
        assert all(col in result.columns for col in model_cols)
    
    def test_prepare_missing_features(self):
        """Test avec des features manquantes."""
        dates = pd.date_range('2024-01-01', periods=20, freq='D')
        features_df = pd.DataFrame({
            'Close_diff': np.random.randn(20),
            'lag_diff_1': np.random.randn(20)
        }, index=dates)
        
        model_cols = ['Close_diff', 'lag_diff_1', 'ma_diff_3', 'volatility']
        current_df = pd.DataFrame({'Close': range(100, 120)}, index=dates)
        
        result = prepare_features_for_prediction(
            features_df, model_cols, current_df=current_df, target_column='Close'
        )
        
        assert isinstance(result, pd.DataFrame)
        assert len(result.columns) == len(model_cols)
        # Les colonnes manquantes devraient être remplies
        assert 'ma_diff_3' in result.columns
        assert 'volatility' in result.columns
    
    def test_prepare_empty_features(self):
        """Test avec un DataFrame de features vide."""
        features_df = pd.DataFrame()
        model_cols = ['feature1', 'feature2']
        
        result = prepare_features_for_prediction(
            features_df, model_cols
        )
        
        assert isinstance(result, pd.DataFrame)
        assert len(result.columns) == len(model_cols)
    
    def test_prepare_with_tuples_in_model_cols(self):
        """Test avec des tuples dans model_cols."""
        dates = pd.date_range('2024-01-01', periods=20, freq='D')
        features_df = pd.DataFrame({
            'High_BTC-USD': np.random.randn(20),
            'Low_BTC-USD': np.random.randn(20)
        }, index=dates)
        
        # Simuler des tuples normalisés
        model_cols = [('High', 'BTC-USD'), ('Low', 'BTC-USD')]
        result = prepare_features_for_prediction(
            features_df, model_cols
        )
        
        # Les tuples devraient être normalisés
        assert isinstance(result, pd.DataFrame)

