"""
Décorateurs pour la gestion des permissions et l'authentification.
"""

from functools import wraps
from flask import abort, current_app, jsonify, request
from flask_login import current_user
from app.models.user import Permission, Role


def permission_required(permission):
    """
    Décorateur qui vérifie qu'un utilisateur a une permission donnée.
    
    Usage:
        @permission_required(Permission.UPLOAD)
        def upload_file():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                if request.is_json:
                    return jsonify({'error': 'Authentication required'}), 401
                abort(401)
            if not current_user.has_permission(permission):
                current_app.logger.warning(
                    f"User {current_user.username} attempted to access {request.endpoint} "
                    f"without permission {permission}"
                )
                if request.is_json:
                    return jsonify({'error': 'Insufficient permissions'}), 403
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def role_required(role):
    """
    Décorateur qui vérifie qu'un utilisateur a un rôle donné.
    
    Usage:
        @role_required(Role.ADMIN)
        def admin_panel():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                if request.is_json:
                    return jsonify({'error': 'Authentication required'}), 401
                abort(401)
            if not current_user.has_role(role):
                current_app.logger.warning(
                    f"User {current_user.username} attempted to access {request.endpoint} "
                    f"without role {role}"
                )
                if request.is_json:
                    return jsonify({'error': 'Insufficient permissions'}), 403
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def admin_required(f):
    """
    Décorateur qui vérifie qu'un utilisateur est administrateur.
    
    Usage:
        @admin_required
        def admin_panel():
            ...
    """
    return role_required(Role.ADMIN)(f)


def login_required_json(f):
    """
    Décorateur qui vérifie qu'un utilisateur est connecté (pour les API JSON).
    
    Usage:
        @login_required_json
        def api_endpoint():
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

