"""
Point d'entrée principal de l'application Flask.

Cette application utilise une architecture modulaire avec Flask Blueprints
pour séparer les fonctionnalités en modules indépendants:

- home: Pages d'accueil et description
- upload: Gestion de l'upload de fichiers
- tests: Exécution des tests statistiques
- resultats: Affichage et téléchargement des résultats
- historique: Gestion de l'historique des tests
- previsions: Prévisions utilisant des modèles ML
- visualisation: Visualisation de données
- cartographie: Cartographie et visualisation géographique
"""

# Use asyncio (native) for async support. Do NOT monkey-patch; asyncio
# works with Python's event loop and avoids eventlet/gevent deprecation.
# We still set a flag to report the chosen async backend.
_async_lib = 'asyncio'


from app import create_app

# Créer l'application
app = create_app()


if __name__ == '__main__':
    # Afficher explicitement les URLs d'accès avant de lancer le serveur
    import socket

    host = '0.0.0.0'
    port = 5000

    # essayer de déterminer l'IP locale utile (ne pas lever d'erreur)
    local_ip = '127.0.0.1'
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        local_ip = s.getsockname()[0]
        s.close()
    except Exception:
        pass

    print(f"Server starting — accessible on:")
    print(f"  http://localhost:{port}/")
    print(f"  http://{local_ip}:{port}/")

    # Report which async library was used for monkey-patching (if any)
    if '_async_lib' in globals() and globals()['_async_lib']:
        print(f"Using async library: {globals()['_async_lib']}")
    else:
        print('Warning: no async library (gevent/eventlet) available. Websocket performance may be degraded.')

    print(">>> About to call app.run()...")
    # En production, utiliser un serveur WSGI comme Gunicorn ou uWSGI
    # app.run() est uniquement pour le développement
    # Pour la production: gunicorn -w 4 -b 0.0.0.0:5000 wsgi:app
    app.run(debug=False, host=host, port=port, use_reloader=False, threaded=True)
