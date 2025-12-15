"""
Tests unitaires pour le blueprint upload.
"""
import pytest
import os
import tempfile
from io import BytesIO


class TestUploadRoutes:
    """Tests pour les routes d'upload."""
    
    def test_upload_file_no_file(self, client):
        """Test upload sans fichier."""
        response = client.post('/upload_file')
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] == False
    
    def test_upload_file_invalid_extension(self, client):
        """Test upload avec extension invalide."""
        data = {
            'data_file': (BytesIO(b'test content'), 'test.txt')
        }
        response = client.post('/upload_file', data=data, content_type='multipart/form-data')
        assert response.status_code == 400
    
    def test_clear_session_file(self, client):
        """Test effacement de session."""
        with client.session_transaction() as sess:
            sess['current_file'] = 'test.csv'
            sess['file_columns'] = ['col1', 'col2']
        
        response = client.post('/clear_session_file')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] == True
        
        with client.session_transaction() as sess:
            assert 'current_file' not in sess

