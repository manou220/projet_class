"""
Point d'entrée WSGI pour l'application Flask.
Utilisé pour le déploiement en production avec des serveurs WSGI comme Gunicorn ou uWSGI.
"""

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run()
