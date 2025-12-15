"""
Configuration pytest pour les tests.
"""
import pytest
import os
import sys
import tempfile
import shutil

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app


@pytest.fixture
def app():
    """Crée une instance de l'application Flask pour les tests."""
    # Créer un dossier temporaire pour les tests
    test_upload_folder = tempfile.mkdtemp()
    test_db_path = os.path.join(tempfile.mkdtemp(), 'test.db')
    
    # Créer l'app en mode test
    app = create_app('testing')
    
    # Override les chemins pour les tests
    app.config['UPLOAD_FOLDER'] = test_upload_folder
    app.config['DB_PATH'] = test_db_path
    app.config['TESTING'] = True
    
    yield app
    
    # Nettoyage après les tests
    shutil.rmtree(test_upload_folder, ignore_errors=True)
    if os.path.exists(test_db_path):
        os.remove(test_db_path)


@pytest.fixture
def client(app):
    """Crée un client de test Flask."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Crée un runner CLI pour les tests."""
    return app.test_cli_runner()


@pytest.fixture
def auth_headers():
    """Headers d'authentification pour les tests (si nécessaire)."""
    return {}

