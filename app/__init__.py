"""
Package principal de l'application Flask.
Initialise l'application avec une structure modulaire utilisant les blueprints.
"""

import os
import logging
from logging.handlers import RotatingFileHandler
import matplotlib
matplotlib.use('Agg')  # Utiliser le backend Agg pour éviter les problèmes avec Tkinter

from flask import Flask, request
from dotenv import load_dotenv
from app.config import config

# Charger les variables d'environnement
load_dotenv()


def create_app(config_name=None):
    """Crée et configure l'application Flask."""
    
    if config_name is None:
        # Par défaut, on part en mode production pour éviter d'exposer le debugger
        # En développement, définir FLASK_ENV=development ou APP_CONFIG=development
        config_name = os.environ.get('FLASK_ENV') or os.environ.get('APP_CONFIG') or 'production'
    
    # Créer l'instance Flask
    # APP_DIR est le répertoire du package 'app'
    APP_DIR = os.path.dirname(os.path.abspath(__file__))
    # PROJECT_DIR est le répertoire parent (racine du projet)
    PROJECT_DIR = os.path.dirname(APP_DIR)
    
    app = Flask(__name__, 
                static_folder=os.path.join(APP_DIR, "static"), 
                template_folder=os.path.join(APP_DIR, "templates"))
    
    # Charger la configuration
    app.config.from_object(config.get(config_name, config['default']))
    
    # Paths - uploads et models au niveau du projet
    app.config['UPLOAD_FOLDER'] = os.path.join(PROJECT_DIR, 'uploads')
    app.config['DB_PATH'] = os.path.join(PROJECT_DIR, 'user_locations.db')
    # Chemin des modèles ML - utiliser app/models/ pour cohérence
    app.config['MODELS_DIR'] = os.path.join(APP_DIR, 'models')

    # SQLAlchemy (utilisé par certains modèles) — défaut sur la base locale
    app.config.setdefault('SQLALCHEMY_DATABASE_URI', f"sqlite:///{app.config['DB_PATH']}")
    app.config.setdefault('SQLALCHEMY_TRACK_MODIFICATIONS', False)
    
    # Créer les dossiers nécessaires
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['MODELS_DIR'], exist_ok=True)
    
    # Configurer le logging
    configure_logging(app)
    
    # Initialiser la base de données
    from app.utils import get_real_time_users_from_db
    # Seed de démonstration seulement si autorisé par la config
    # La valeur par défaut est définie dans la classe Config
    seed_enabled = app.config.get('SEED_SAMPLE_LOCATIONS', True)
    try:
        get_real_time_users_from_db(app.config['DB_PATH'], seed=seed_enabled)
    except Exception as e:
        app.logger.error(f"Erreur lors de l'initialisation de la base de données: {e}")
    
    # Initialiser les extensions
    from app.extensions import db, cache, login_manager
    db.init_app(app)
    
    # Initialiser Flask-Login
    login_manager.init_app(app)
    
    @login_manager.user_loader
    def load_user(user_id):
        """Charge un utilisateur depuis la base de données."""
        from app.models.user import User
        return User.query.get(int(user_id))
    # Initialiser SocketIO (optionnel - peut être désactivé pour développement simple)
    # from app.extensions import socketio
    # try:
    #     socketio.init_app(app)
    # except Exception as e:
    #     app.logger.warning(f"Échec d'initialisation de SocketIO: {e}")
    
    # Initialiser le cache avec gestion d'erreur
    try:
        cache.init_app(app)
    except Exception as e:
        # Si le cache échoue (ex: Redis non disponible), utiliser SimpleCache
        app.logger.warning(f"Échec d'initialisation du cache: {e}. Utilisation de SimpleCache.")
        app.config['CACHE_TYPE'] = 'SimpleCache'
        cache.init_app(app)
    
    # Initialiser le service API boursière avec le cache
    try:
        from app.services.stock_api_service import get_stock_api_service
        stock_api_service = get_stock_api_service(cache=cache)
        app.logger.info("Service API boursière initialisé avec succès")
        # Stocker le service dans l'app pour accès facile
        app.stock_api_service = stock_api_service
    except Exception as e:
        app.logger.warning(f"Échec d'initialisation du service API boursière: {e}")
        app.stock_api_service = None
    
    # Configurer les headers de cache pour les assets statiques
    @app.after_request
    def set_cache_headers(response):
        """Configure les headers de cache pour améliorer les performances."""
        if response.status_code == 200:
            # Cache long pour les assets statiques (CSS, JS, images)
            if request.endpoint == 'static':
                response.cache_control.max_age = 31536000  # 1 an
                response.cache_control.public = True
            # Cache court pour les pages HTML
            elif request.endpoint and not request.endpoint.startswith('api'):
                response.cache_control.max_age = 300  # 5 minutes
                response.cache_control.public = True
                response.cache_control.must_revalidate = True
        return response
    
    # Initialiser la table des utilisateurs
    with app.app_context():
        try:
            from app.models.user import init_users_table
            init_users_table()
        except Exception as e:
            app.logger.warning(f"Erreur lors de l'initialisation de la table utilisateurs: {e}")
    
    # Enregistrer les blueprints
    register_blueprints(app)
    # Importer les handlers SocketIO (enregistre les events) - optionnel si SocketIO est désactivé
    # try:
    #     from app import socketio_events  # noqa: F401
    # except Exception as e:
    #     app.logger.warning(f"Impossible d'importer les events SocketIO: {e}")
    
    # Log des informations
    print(f"Application initialisée en mode {config_name}")
    print(f"Dossier templates: {app.template_folder}")
    print(f"Dossier static: {app.static_folder}")
    print(f"Dossier uploads: {app.config['UPLOAD_FOLDER']}")
    print(f"Base de données: {app.config['DB_PATH']}")
    
    return app


def configure_logging(app):
    """Configure le logging structuré pour l'application."""
    log_level = getattr(logging, app.config.get('LOG_LEVEL', 'INFO'), logging.INFO)
    log_file = app.config.get('LOG_FILE')
    
    # Formatter structuré
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s: %(message)s [%(pathname)s:%(lineno)d]'
    )
    
    # Handler console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    app.logger.addHandler(console_handler)
    
    # Handler fichier (si configuré)
    if log_file:
        # Créer le dossier logs si nécessaire
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        
        # Rotating file handler (max 10MB, 5 fichiers de backup)
        file_handler = RotatingFileHandler(
            log_file, maxBytes=10*1024*1024, backupCount=5
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        app.logger.addHandler(file_handler)
    
    # Définir le niveau du logger principal
    app.logger.setLevel(log_level)
    
    # Désactiver le logging verbeux de certaines bibliothèques en production
    if not app.config.get('DEBUG'):
        logging.getLogger('werkzeug').setLevel(logging.WARNING)
        logging.getLogger('matplotlib').setLevel(logging.WARNING)


def register_blueprints(app):
    """Enregistre tous les blueprints de l'application."""
    
    # Blueprint Home
    from app.blueprints.home.routes import bp as home_bp
    app.register_blueprint(home_bp)
    
    # Blueprint Upload
    from app.blueprints.upload.routes import bp as upload_bp
    app.register_blueprint(upload_bp)
    
    # Blueprint Tests
    from app.blueprints.tests.routes import bp as tests_bp
    app.register_blueprint(tests_bp, url_prefix='/tests')
    
    # Blueprint Resultats
    from app.blueprints.resultats.routes import bp as resultats_bp
    app.register_blueprint(resultats_bp, url_prefix='/resultats')
    
    # Blueprint Historique
    from app.blueprints.historique.routes import bp as historique_bp
    app.register_blueprint(historique_bp, url_prefix='/historique')
    
    # Blueprint Previsions
    from app.blueprints.previsions.routes import bp as previsions_bp
    app.register_blueprint(previsions_bp, url_prefix='/previsions')
    
    # Blueprint Visualisation
    from app.blueprints.visualisation.routes import bp as visualisation_bp
    app.register_blueprint(visualisation_bp, url_prefix='/visualisation')
    
    # Blueprint Cartographie
    from app.blueprints.cartographie.routes import bp as cartographie_bp
    app.register_blueprint(cartographie_bp, url_prefix='/cartographie')

    # Blueprint Jobs (background tasks status)
    from app.blueprints.jobs.routes import bp as jobs_bp
    app.register_blueprint(jobs_bp, url_prefix='/jobs')
    
    # Blueprint Auth (authentification)
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp)
    
    print("Blueprints enregistrés avec succès")
