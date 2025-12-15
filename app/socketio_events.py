"""
Handlers Socket.IO pour la collecte et diffusion des positions utilisateurs.
"""
from datetime import datetime
from flask import current_app
from app.extensions import socketio

# Stockage en mémoire des positions: {sid: {username, lat, lon, ts}}
positions = {}

# Si socketio n'est pas disponible, les handlers ne seront pas enregistrés
if socketio is not None:
    from flask_socketio import emit

    @socketio.on('connect')
    def handle_connect():
        sid = getattr(socketio, 'server', None)
        current_app.logger.debug('Client connecté')

    @socketio.on('location_update')
    def handle_location_update(data):
        """Réception d'une mise à jour de position client.
        Data attendu: {"lat": float, "lon": float, "username": str}
        """
        sid = None
        try:
            # flask-socketio fournit request.sid via le contexte
            from flask import request
            sid = request.sid
        except Exception:
            sid = None

        lat = data.get('lat')
        lon = data.get('lon')
        username = data.get('username', 'anonymous')

        if lat is None or lon is None:
            return

        positions[sid] = {
            'username': username,
            'lat': float(lat),
            'lon': float(lon),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }

        # Broadcast des positions actuelles à tous les clients
        try:
            socketio.emit('positions', list(positions.values()))
        except Exception as e:
            current_app.logger.error(f"Erreur lors de l'émission des positions: {e}")

    @socketio.on('disconnect')
    def handle_disconnect():
        try:
            from flask import request
            sid = request.sid
            positions.pop(sid, None)
            socketio.emit('positions', list(positions.values()))
        except Exception:
            current_app.logger.debug('Disconnect: impossible de nettoyer la position')
