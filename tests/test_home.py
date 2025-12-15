"""
Tests unitaires pour le blueprint home.
"""
import pytest


class TestHomeRoutes:
    """Tests pour les routes home."""
    
    def test_accueil_route(self, client):
        """Test route accueil."""
        response = client.get('/')
        assert response.status_code == 200
    
    def test_accueil_alias(self, client):
        """Test alias /accueil."""
        response = client.get('/accueil')
        assert response.status_code == 200
    
    def test_description_route(self, client):
        """Test route description."""
        response = client.get('/description')
        assert response.status_code == 200

