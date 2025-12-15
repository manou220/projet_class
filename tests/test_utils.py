"""
Tests unitaires pour les fonctions utilitaires.
"""
import pytest
import pandas as pd
import numpy as np
from app.utils import (
    allowed_file,
    load_dataframe,
    validate_test_requirements,
    make_features,
    prepare_data_for_ml
)


class TestAllowedFile:
    """Tests pour la fonction allowed_file."""
    
    def test_allowed_csv(self):
        """Test avec un fichier CSV."""
        assert allowed_file('test.csv') == True
    
    def test_allowed_xlsx(self):
        """Test avec un fichier XLSX."""
        assert allowed_file('test.xlsx') == True
    
    def test_allowed_xls(self):
        """Test avec un fichier XLS."""
        assert allowed_file('test.xls') == True
    
    def test_not_allowed_txt(self):
        """Test avec un fichier non autorisé."""
        assert allowed_file('test.txt') == False
    
    def test_not_allowed_no_extension(self):
        """Test avec un fichier sans extension."""
        assert allowed_file('test') == False


class TestLoadDataframe:
    """Tests pour la fonction load_dataframe."""
    
    def test_load_csv(self, tmp_path):
        """Test chargement d'un CSV."""
        # Créer un fichier CSV de test
        csv_file = tmp_path / "test.csv"
        df_test = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})
        df_test.to_csv(csv_file, index=False)
        
        # Charger le fichier
        df_loaded = load_dataframe(str(csv_file))
        
        assert isinstance(df_loaded, pd.DataFrame)
        assert len(df_loaded) == 3
    
    def test_load_nonexistent_file(self):
        """Test avec un fichier inexistant."""
        with pytest.raises(FileNotFoundError):
            load_dataframe('nonexistent.csv')


class TestValidateTestRequirements:
    """Tests pour la fonction validate_test_requirements."""
    
    def test_wilcoxon_valid(self):
        """Test validation Wilcoxon avec 2 colonnes."""
        is_valid, msg = validate_test_requirements('wilcoxon', ['col1', 'col2'])
        assert is_valid == True
        assert msg == ""
    
    def test_wilcoxon_invalid(self):
        """Test validation Wilcoxon avec mauvais nombre de colonnes."""
        is_valid, msg = validate_test_requirements('wilcoxon', ['col1'])
        assert is_valid == False
        assert '2 colonne' in msg
    
    def test_shapiro_wilk_valid(self):
        """Test validation Shapiro-Wilk avec 1 colonne."""
        is_valid, msg = validate_test_requirements('shapiro_wilk', ['col1'])
        assert is_valid == True
    
    def test_kruskal_valid(self):
        """Test validation Kruskal avec plusieurs colonnes."""
        is_valid, msg = validate_test_requirements('kruskal', ['col1', 'col2', 'col3'])
        assert is_valid == True


class TestMakeFeatures:
    """Tests pour la fonction make_features."""
    
    def test_make_features_basic(self):
        """Test création de features basique."""
        # Créer un DataFrame de test
        dates = pd.date_range('2024-01-01', periods=50, freq='D')
        df = pd.DataFrame({
            'Close': np.random.randn(50).cumsum() + 100,
            'Open': np.random.randn(50).cumsum() + 100,
            'Volume': np.random.randint(1000, 10000, 50)
        }, index=dates)
        
        # Créer les features
        df_features = make_features(df, target_col='Close')
        
        assert isinstance(df_features, pd.DataFrame)
        assert 'Close_diff' in df_features.columns
        assert 'lag_diff_1' in df_features.columns
        assert 'day_of_week' in df_features.columns
    
    def test_make_features_non_datetime_index(self):
        """Test avec un index non-datetime."""
        df = pd.DataFrame({
            'Close': [100, 101, 102, 103, 104]
        })
        
        # Ne devrait pas planter
        df_features = make_features(df, target_col='Close')
        assert isinstance(df_features, pd.DataFrame)


class TestPrepareDataForML:
    """Tests pour la fonction prepare_data_for_ml."""
    
    def test_prepare_data_basic(self):
        """Test préparation de données basique."""
        dates = pd.date_range('2024-01-01', periods=50, freq='D')
        df = pd.DataFrame({
            'Close': np.random.randn(50).cumsum() + 100
        }, index=dates)
        
        X, y, feature_cols = prepare_data_for_ml(df, 'Close')
        
        assert isinstance(X, pd.DataFrame)
        assert isinstance(y, pd.Series)
        assert len(feature_cols) > 0
        assert len(X) == len(y)

