"""
Blueprint pour les pages principales de l'application.
"""
from flask import render_template, Blueprint
from app.extensions import cache

bp = Blueprint('home', __name__)


@bp.route('/')
@bp.route('/accueil')
@cache.cached(timeout=300)  # Cache 5 minutes
def accueil():
    """Page d'accueil de l'application."""
    return render_template("accueil.html")


@bp.route('/description')
@cache.cached(timeout=600)  # Cache 10 minutes (page moins fréquente)
def description():
    """Page de description de l'application et des tests."""
    return render_template("description.html")
