"""
Blueprint pour la cartographie et la capture de positions en temps réel.
"""

from flask import Blueprint, render_template, current_app, request, jsonify
from app.extensions import cache
from app.utils import get_real_time_users_from_db, save_user_location

bp = Blueprint('cartographie', __name__)


@bp.route('/')
@cache.cached(timeout=60)  # Cache court (1 min) car données en temps réel
def index():
    """Affiche la carte interactive."""
    db_path = current_app.config.get('DB_PATH', 'user_locations.db')
    user_data = get_real_time_users_from_db(db_path)
    return render_template("cartographie.html", initial_locations=user_data)


@bp.route('/api/locations', methods=['GET', 'POST'])
def locations_api():
    """API REST pour récupérer ou enregistrer les positions utilisateurs."""
    db_path = current_app.config.get('DB_PATH', 'user_locations.db')

    if request.method == 'GET':
        # Cache très court pour les données en temps réel (15 secondes)
        cache_key = f'locations_api_{db_path}'
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return jsonify({"users": cached_data})
        
        user_data = get_real_time_users_from_db(db_path)
        cache.set(cache_key, user_data, timeout=15)
        return jsonify({"users": user_data})

    payload = request.get_json(silent=True) or {}
    username = (payload.get('username') or 'Visiteur').strip() or 'Visiteur'
    lat = payload.get('lat') if 'lat' in payload else payload.get('latitude')
    lon = payload.get('lon') if 'lon' in payload else payload.get('longitude')
    active_users = payload.get('active_users', 1)

    if lat is None or lon is None:
        return jsonify({"error": "Latitude et longitude sont requises"}), 400

    try:
        lat = float(lat)
        lon = float(lon)
        active_users = int(active_users) if active_users is not None else 1
    except (TypeError, ValueError):
        return jsonify({"error": "Latitude/longitude invalides"}), 400

    try:
        save_user_location(db_path, username, lat, lon, active_users)
        # Invalider le cache après une mise à jour
        cache_key = f'locations_api_{db_path}'
        cache.delete(cache_key)
    except Exception as exc:  # pragma: no cover - journalisation côté serveur
        current_app.logger.exception("Impossible d'enregistrer la position", exc_info=exc)
        return jsonify({"error": "Erreur lors de l'enregistrement"}), 500

    return jsonify({"status": "ok"})
