"""
Blueprint pour la visualisation de données.
"""
from flask import Blueprint, render_template

bp = Blueprint('visualisation', __name__)


@bp.route('/')
def index():
    """Page de visualisation de données."""
    return render_template('visualisation.html')
