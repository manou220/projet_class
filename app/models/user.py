"""
Modèle utilisateur avec authentification et gestion des permissions.
"""

from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app.extensions import db


class Role:
    """Rôles disponibles dans l'application."""
    ADMIN = 'admin'
    USER = 'user'
    VIEWER = 'viewer'
    
    @staticmethod
    def all():
        """Retourne la liste de tous les rôles."""
        return [Role.ADMIN, Role.USER, Role.VIEWER]


class Permission:
    """Permissions disponibles dans l'application."""
    # Permissions générales
    VIEW = 'view'
    UPLOAD = 'upload'
    ANALYZE = 'analyze'
    PREDICT = 'predict'
    EXPORT = 'export'
    
    # Permissions administratives
    MANAGE_USERS = 'manage_users'
    MANAGE_CONFIG = 'manage_config'
    VIEW_LOGS = 'view_logs'
    
    @staticmethod
    def all():
        """Retourne la liste de toutes les permissions."""
        return [
            Permission.VIEW,
            Permission.UPLOAD,
            Permission.ANALYZE,
            Permission.PREDICT,
            Permission.EXPORT,
            Permission.MANAGE_USERS,
            Permission.MANAGE_CONFIG,
            Permission.VIEW_LOGS
        ]


# Mapping des rôles vers les permissions
ROLE_PERMISSIONS = {
    Role.ADMIN: Permission.all(),  # Admin a toutes les permissions
    Role.USER: [
        Permission.VIEW,
        Permission.UPLOAD,
        Permission.ANALYZE,
        Permission.PREDICT,
        Permission.EXPORT
    ],
    Role.VIEWER: [
        Permission.VIEW
    ]
}


class User(UserMixin, db.Model):
    """
    Modèle utilisateur avec authentification et gestion des rôles.
    """
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default=Role.USER, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_login = db.Column(db.DateTime, nullable=True)
    failed_login_attempts = db.Column(db.Integer, default=0, nullable=False)
    locked_until = db.Column(db.DateTime, nullable=True)
    
    def set_password(self, password):
        """Définit le mot de passe hashé."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Vérifie le mot de passe."""
        return check_password_hash(self.password_hash, password)
    
    def has_permission(self, permission):
        """Vérifie si l'utilisateur a une permission donnée."""
        if not self.is_active:
            return False
        return permission in ROLE_PERMISSIONS.get(self.role, [])
    
    def has_role(self, role):
        """Vérifie si l'utilisateur a un rôle donné."""
        return self.role == role
    
    def is_admin(self):
        """Vérifie si l'utilisateur est administrateur."""
        return self.has_role(Role.ADMIN)
    
    def record_login(self):
        """Enregistre une connexion réussie."""
        self.last_login = datetime.utcnow()
        self.failed_login_attempts = 0
        self.locked_until = None
        db.session.commit()
    
    def record_failed_login(self, max_attempts=5, lock_duration_minutes=30):
        """Enregistre une tentative de connexion échouée."""
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= max_attempts:
            from datetime import timedelta
            self.locked_until = datetime.utcnow() + timedelta(minutes=lock_duration_minutes)
        db.session.commit()
    
    def is_locked(self):
        """Vérifie si le compte est verrouillé."""
        if self.locked_until is None:
            return False
        if datetime.utcnow() > self.locked_until:
            self.locked_until = None
            self.failed_login_attempts = 0
            db.session.commit()
            return False
        return True
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def to_dict(self):
        """Convertit l'utilisateur en dictionnaire (pour JSON)."""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }


def init_users_table():
    """Initialise la table des utilisateurs avec un admin par défaut."""
    from sqlalchemy import inspect
    
    # Vérifier si la table existe et a le bon schéma
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    
    if 'users' in tables:
        # Vérifier si toutes les colonnes nécessaires existent
        columns = [col['name'] for col in inspector.get_columns('users')]
        required_columns = ['id', 'username', 'email', 'password_hash', 'role', 'is_active', 
                          'created_at', 'last_login', 'failed_login_attempts', 'locked_until']
        
        missing_columns = [col for col in required_columns if col not in columns]
        
        if missing_columns:
            # La table existe mais avec un schéma différent - la recréer
            print(f"Migration nécessaire: colonnes manquantes {missing_columns}")
            print("Recréation de la table users...")
            db.drop_all()
            db.create_all()
            print("Table users recréée avec le nouveau schéma.")
    else:
        # Créer la table si elle n'existe pas
        db.create_all()
    
    # Vérifier si un admin existe déjà
    try:
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@boursa.local',
                role=Role.ADMIN,
                is_active=True
            )
            admin.set_password('admin123')  # Changer en production!
            db.session.add(admin)
            db.session.commit()
            print("Utilisateur admin créé: admin / admin123 (CHANGER EN PRODUCTION!)")
        else:
            print("Utilisateur admin existe déjà.")
    except Exception as e:
        db.session.rollback()
        print(f"Erreur lors de la vérification/création de l'admin: {e}")
        raise

