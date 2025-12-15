# Guide de Sécurité et Performance

Ce document décrit la configuration de la sécurité et des performances pour l'application BoursA.

## Table des matières

1. [Authentification et Autorisation](#authentification-et-autorisation)
2. [Cache Redis](#cache-redis)
3. [HTTPS/SSL](#httpsssl)
4. [Load Balancing](#load-balancing)
5. [Recommandations de Production](#recommandations-de-production)

---

## Authentification et Autorisation

### Système de Rôles

L'application utilise un système de rôles avec permissions :

- **Admin** : Accès complet à toutes les fonctionnalités
- **User** : Peut uploader, analyser, prédire et exporter des données
- **Viewer** : Accès en lecture seule

### Permissions

Les permissions disponibles sont :
- `VIEW` : Visualiser les données
- `UPLOAD` : Uploader des fichiers
- `ANALYZE` : Analyser les données
- `PREDICT` : Faire des prédictions
- `EXPORT` : Exporter les résultats
- `MANAGE_USERS` : Gérer les utilisateurs (admin uniquement)
- `MANAGE_CONFIG` : Gérer la configuration (admin uniquement)
- `VIEW_LOGS` : Consulter les logs (admin uniquement)

### Protection des Routes

Utilisez les décorateurs pour protéger vos routes :

```python
from app.auth.decorators import permission_required, admin_required, role_required
from app.models.user import Permission, Role

@permission_required(Permission.UPLOAD)
def upload_file():
    # Seuls les utilisateurs avec la permission UPLOAD peuvent accéder
    pass

@admin_required
def admin_panel():
    # Seuls les administrateurs peuvent accéder
    pass

@role_required(Role.USER)
def user_area():
    # Seuls les utilisateurs avec le rôle USER peuvent accéder
    pass
```

### Sécurité des Comptes

- **Verrouillage automatique** : Après 5 tentatives de connexion échouées, le compte est verrouillé pendant 30 minutes
- **Mots de passe hashés** : Utilisation de werkzeug.security pour le hachage sécurisé
- **Protection CSRF** : Flask-WTF active par défaut

### Configuration

```env
# Désactiver l'inscription publique (recommandé en production)
DISABLE_PUBLIC_REGISTRATION=true

# Limites de connexion
MAX_LOGIN_ATTEMPTS=5
ACCOUNT_LOCKOUT_DURATION=30
```

---

## Cache Redis

### Installation Redis

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install redis-server
sudo systemctl start redis
sudo systemctl enable redis
```

**macOS:**
```bash
brew install redis
brew services start redis
```

**Docker:**
```bash
docker run -d -p 6379:6379 --name redis redis:alpine
```

### Configuration

Ajoutez dans votre `.env` :

```env
CACHE_TYPE=Redis
CACHE_REDIS_URL=redis://localhost:6379/0

# OU avec authentification
CACHE_REDIS_URL=redis://:password@localhost:6379/0

# OU configuration détaillée
CACHE_REDIS_HOST=localhost
CACHE_REDIS_PORT=6379
CACHE_REDIS_DB=0
CACHE_REDIS_PASSWORD=your_password
```

### Vérification

Pour vérifier que Redis fonctionne :

```python
from app.extensions import cache
cache.set('test_key', 'test_value', timeout=60)
value = cache.get('test_key')
print(value)  # Devrait afficher 'test_value'
```

### Performance

Redis améliore significativement les performances :
- Réduction des appels API (cache des données boursières)
- Cache des résultats d'analyse
- Partage de session entre plusieurs instances (load balancing)

---

## HTTPS/SSL

### Certificats SSL/TLS

#### Option 1: Let's Encrypt (Recommandé pour production)

1. Installer Certbot :
```bash
sudo apt-get install certbot python3-certbot-nginx
```

2. Obtenir un certificat :
```bash
sudo certbot --nginx -d votre-domaine.com
```

3. Renouvellement automatique :
Certbot configure automatiquement le renouvellement. Vérifiez avec :
```bash
sudo certbot renew --dry-run
```

#### Option 2: Auto-signé (Développement uniquement)

```bash
openssl req -x509 -newkey rsa:4096 -nodes \
  -keyout key.pem -out cert.pem -days 365 \
  -subj "/CN=localhost"
```

### Configuration Flask avec HTTPS

Pour tester en développement avec un certificat auto-signé :

```python
if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=5000,
        ssl_context=('cert.pem', 'key.pem')
    )
```

**⚠️ Ne jamais utiliser de certificats auto-signés en production !**

### Headers de Sécurité

L'application configure automatiquement :
- `SESSION_COOKIE_SECURE=True` : Cookies uniquement en HTTPS
- `SESSION_COOKIE_HTTPONLY=True` : Protection XSS
- `SESSION_COOKIE_SAMESITE='Lax'` : Protection CSRF

### Nginx avec SSL

Voir la configuration Nginx dans `docs/nginx-ssl.conf.example`

---

## Load Balancing

### Architecture Recommandée

```
Internet
   ↓
[Load Balancer (Nginx/HAProxy)]
   ↓
[Flask App Instance 1] [Flask App Instance 2] [Flask App Instance N]
   ↓
[Redis Cache]
   ↓
[Database]
```

### Nginx comme Load Balancer

Configuration de base (`/etc/nginx/sites-available/boursa`):

```nginx
upstream flask_app {
    least_conn;  # Répartition par connexions actives
    server 127.0.0.1:5000;
    server 127.0.0.1:5001;
    server 127.0.0.1:5002;
    # Ajoutez plus d'instances selon vos besoins
}

server {
    listen 80;
    server_name votre-domaine.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name votre-domaine.com;

    ssl_certificate /etc/letsencrypt/live/votre-domaine.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/votre-domaine.com/privkey.pem;

    # Configuration SSL moderne
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    location / {
        proxy_pass http://flask_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support (si nécessaire)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Cache des assets statiques
    location /static {
        alias /chemin/vers/app/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

### HAProxy comme Load Balancer

Configuration de base (`/etc/haproxy/haproxy.cfg`):

```haproxy
global
    log /dev/log local0
    chroot /var/lib/haproxy
    stats socket /run/haproxy/admin.sock mode 660 level admin
    stats timeout 30s
    user haproxy
    group haproxy
    daemon

defaults
    mode http
    log global
    option httplog
    option dontlognull
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms

frontend http_front
    bind *:80
    redirect scheme https code 301 if !{ ssl_fc }

frontend https_front
    bind *:443 ssl crt /etc/ssl/certs/votre-domaine.com.pem
    default_backend flask_backend

backend flask_backend
    balance roundrobin
    option httpchk GET /health
    http-check expect status 200
    server flask1 127.0.0.1:5000 check
    server flask2 127.0.0.1:5001 check
    server flask3 127.0.0.1:5002 check
```

### Démarrer Plusieurs Instances

Avec Gunicorn :

```bash
# Instance 1
gunicorn -w 4 -b 127.0.0.1:5000 --access-logfile - wsgi:app

# Instance 2
gunicorn -w 4 -b 127.0.0.1:5001 --access-logfile - wsgi:app

# Instance 3
gunicorn -w 4 -b 127.0.0.1:5002 --access-logfile - wsgi:app
```

Ou avec systemd (voir `docs/systemd/` pour les fichiers de service)

### Sticky Sessions (si nécessaire)

Si vous utilisez des sessions côté serveur (non recommandé, préférez Redis) :

```nginx
upstream flask_app {
    ip_hash;  # Sticky session par IP
    server 127.0.0.1:5000;
    server 127.0.0.1:5001;
}
```

---

## Recommandations de Production

### Checklist de Sécurité

- [ ] `SECRET_KEY` fort et unique généré
- [ ] `DISABLE_PUBLIC_REGISTRATION=true`
- [ ] HTTPS activé avec certificat valide
- [ ] Redis configuré et sécurisé avec mot de passe
- [ ] Firewall configuré (ports 80, 443 uniquement)
- [ ] Logs activés et surveillés
- [ ] Backups de la base de données configurés
- [ ] Rate limiting configuré (voir nginx)
- [ ] Headers de sécurité configurés

### Variables d'Environnement Critiques

```env
SECRET_KEY=<généré avec secrets.token_hex(32)>
FLASK_ENV=production
DISABLE_PUBLIC_REGISTRATION=true
CACHE_TYPE=Redis
CACHE_REDIS_URL=redis://:strong_password@localhost:6379/0
```

### Monitoring

- Surveiller les logs d'authentification
- Alerter sur les tentatives de connexion échouées multiples
- Monitorer l'utilisation du cache Redis
- Surveiller les performances du load balancer

### Performance

- Utiliser Redis pour le cache
- Activer la compression gzip dans Nginx
- Configurer le cache des assets statiques
- Utiliser CDN pour les assets statiques si possible
- Optimiser les requêtes de base de données

---

## Support

Pour plus d'informations, consultez :
- [Flask-Login Documentation](https://flask-login.readthedocs.io/)
- [Redis Documentation](https://redis.io/documentation)
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [Nginx Documentation](https://nginx.org/en/docs/)

