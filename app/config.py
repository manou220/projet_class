"""
Configuration de l'application Flask.
"""

import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuration de base de l'application."""
    # SECRET_KEY: Générer avec: python -c "import secrets; print(secrets.token_hex(32))"
    # En production, DOIT être défini dans les variables d'environnement
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max
    ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}
    DB_PATH = 'user_locations.db'
    SEED_SAMPLE_LOCATIONS = True  # Par défaut, seed activé pour démonstration
    
    # Configuration du cache
    CACHE_TYPE = 'SimpleCache'  # SimpleCache pour développement, Redis pour production
    CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes par défaut
    CACHE_THRESHOLD = 1000  # Nombre max d'éléments en cache
    
    # Configuration Redis (pour le cache en production)
    CACHE_REDIS_HOST = os.environ.get('CACHE_REDIS_HOST', 'localhost')
    CACHE_REDIS_PORT = int(os.environ.get('CACHE_REDIS_PORT', '6379'))
    CACHE_REDIS_DB = int(os.environ.get('CACHE_REDIS_DB', '0'))
    CACHE_REDIS_PASSWORD = os.environ.get('CACHE_REDIS_PASSWORD', None)
    CACHE_REDIS_URL = os.environ.get('CACHE_REDIS_URL', None)  # Format: redis://:password@host:port/db
    
    # Configuration de sécurité
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600  # 1 heure
    SESSION_COOKIE_SECURE = False  # True en production avec HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 86400  # 24 heures
    
    # Authentification
    DISABLE_PUBLIC_REGISTRATION = os.environ.get('DISABLE_PUBLIC_REGISTRATION', 'false').lower() == 'true'
    MAX_LOGIN_ATTEMPTS = int(os.environ.get('MAX_LOGIN_ATTEMPTS', '5'))
    ACCOUNT_LOCKOUT_DURATION = int(os.environ.get('ACCOUNT_LOCKOUT_DURATION', '30'))  # minutes
    
    # Configuration des APIs boursières
    # Les clés API sont chargées depuis les variables d'environnement
    # Voir ENV_EXAMPLE.txt pour plus de détails
    ALPHAVANTAGE_KEY = os.environ.get('ALPHAVANTAGE_KEY')
    IEX_CLOUD_API_KEY = os.environ.get('IEX_CLOUD_API_KEY')
    
    # Configuration du cache pour les APIs boursières (en secondes)
    STOCK_API_CACHE_TIMEOUT = {
        'yahoo': 300,  # 5 minutes
        'alpha_vantage': 3600,  # 1 heure (API limitée)
        'iex_cloud': 300  # 5 minutes
    }
    
    # Configuration du logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO').upper()
    LOG_FILE = os.environ.get('LOG_FILE', None)  # None = console seulement

class DevelopmentConfig(Config):
    """Configuration pour le développement."""
    DEBUG = True
    TESTING = False
    SEED_SAMPLE_LOCATIONS = True  # Seed activé en développement pour tests

class ProductionConfig(Config):
    """Configuration pour la production."""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PREFERRED_URL_SCHEME = 'https'
    SEED_SAMPLE_LOCATIONS = False
    
    # SECRET_KEY obligatoire en production
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError(
            "SECRET_KEY doit être défini en production. "
            "Définissez-la dans les variables d'environnement ou dans le fichier .env"
        )
    
    # Cache optimisé pour la production - Redis recommandé
    cache_type = os.environ.get('CACHE_TYPE', 'Redis')
    redis_url = os.environ.get('CACHE_REDIS_URL')
    
    if cache_type == 'Redis':
        if redis_url:
            CACHE_TYPE = 'Redis'
            CACHE_REDIS_URL = redis_url
        elif os.environ.get('CACHE_REDIS_HOST'):
            # Construire l'URL Redis si les composants sont fournis
            host = os.environ.get('CACHE_REDIS_HOST', 'localhost')
            port = os.environ.get('CACHE_REDIS_PORT', '6379')
            db = os.environ.get('CACHE_REDIS_DB', '0')
            password = os.environ.get('CACHE_REDIS_PASSWORD', '')
            if password:
                CACHE_REDIS_URL = f"redis://:{password}@{host}:{port}/{db}"
            else:
                CACHE_REDIS_URL = f"redis://{host}:{port}/{db}"
            CACHE_TYPE = 'Redis'
        else:
            CACHE_TYPE = 'SimpleCache'  # Fallback si Redis non configuré
            import warnings
            warnings.warn("Redis non configuré, utilisation de SimpleCache. Configurez CACHE_REDIS_URL en production.")
    else:
        CACHE_TYPE = 'SimpleCache'
    
    CACHE_DEFAULT_TIMEOUT = 600  # 10 minutes en production
    
    # Sécurité renforcée en production
    SESSION_COOKIE_SECURE = True  # HTTPS requis
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    WTF_CSRF_ENABLED = True
    
    # Logging en production
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'WARNING').upper()
    LOG_FILE = os.environ.get('LOG_FILE', 'logs/app.log')

class TestingConfig(Config):
    """Configuration pour les tests."""
    DEBUG = True
    TESTING = True

# Configuration par défaut
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
