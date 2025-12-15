"""
Module d'authentification et de gestion des permissions.
"""

from flask import Blueprint

bp = Blueprint('auth', __name__, url_prefix='/auth')

from app.auth import routes, decorators

