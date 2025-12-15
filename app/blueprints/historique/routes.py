"""
Blueprint pour la gestion de l'historique des tests.
"""
from flask import Blueprint, render_template, session, redirect, url_for, current_app, request
from app.utils import get_history, clear_history
import math

bp = Blueprint('historique', __name__)

# Nombre d'éléments par page
ITEMS_PER_PAGE = 20


@bp.route('/')
def index():
    """Affiche l'historique de tous les tests effectués avec pagination."""
    history = get_history(session=session)
    total_tests = len(history)
    
    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', ITEMS_PER_PAGE, type=int)
    
    # Calculer les indices de pagination
    total_pages = math.ceil(total_tests / per_page) if total_tests > 0 else 1
    page = max(1, min(page, total_pages))  # S'assurer que page est valide
    
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    
    # Paginer l'historique
    paginated_history = history[start_idx:end_idx]
    
    return render_template(
        "historique.html",
        history=paginated_history,
        total_tests=total_tests,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        has_prev=page > 1,
        has_next=page < total_pages,
        prev_page=page - 1 if page > 1 else None,
        next_page=page + 1 if page < total_pages else None
    )


@bp.route("/clear_history", methods=['POST'])
def clear_all_history():
    """Efface l'historique complet des tests."""
    clear_history(session=session)
    session.pop('last_result', None)
    return redirect(url_for('historique.index'))
