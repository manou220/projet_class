# Service API Boursière

Ce service fournit une interface unifiée pour accéder à différentes APIs boursières avec gestion du cache et respect des quotas.

## APIs supportées

### 1. Yahoo Finance
- **Gratuit** : Oui, pas de clé API requise
- **Quotas** : ~2000 requêtes/min (pas de limite stricte connue)
- **Intervalles** : 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo
- **Cache** : 5 minutes

### 2. Alpha Vantage
- **Gratuit** : Oui, clé API requise (obtenue gratuitement sur https://www.alphavantage.co/support/#api-key)
- **Quotas gratuits** : 5 requêtes/min, 500 requêtes/jour
- **Intervalles** : daily, weekly, monthly
- **Cache** : 1 heure (pour respecter les quotas)
- **Variable d'environnement** : `ALPHAVANTAGE_KEY`

### 3. IEX Cloud
- **Gratuit** : Oui avec plan gratuit, clé API requise (obtenue sur https://iexcloud.io/console/login)
- **Quotas gratuits** : ~100 requêtes/min, ~50 000 requêtes/mois (selon le plan)
- **Intervalles** : 1d, 1w, 1mo
- **Cache** : 5 minutes
- **Variable d'environnement** : `IEX_CLOUD_API_KEY`
- **Format de clé** : sk-xxxxx ou pk-xxxxx

## Configuration

### Variables d'environnement

Ajoutez les clés API dans votre fichier `.env` (copié depuis `ENV_EXAMPLE.txt`) :

```env
# Alpha Vantage
ALPHAVANTAGE_KEY=votre_cle_alpha_vantage

# IEX Cloud
IEX_CLOUD_API_KEY=votre_cle_iex_cloud
```

### Utilisation dans le code

```python
from app.services.stock_api_service import get_stock_api_service
from flask import current_app

# Obtenir le service (utilise le cache de l'application)
api_service = current_app.stock_api_service

# Ou créer une instance manuellement
api_service = get_stock_api_service(cache=current_app.cache)

# Récupérer des données
try:
    df = api_service.fetch_stock_data(
        api_name='yahoo',
        symbol='AAPL',
        interval='1d'
    )
    print(df)
except StockAPIError as e:
    print(f"Erreur API: {e}")
except RateLimitExceeded as e:
    print(f"Quota dépassé: {e}")
```

## Fonctionnalités

### Cache intelligent
- Chaque API a un timeout de cache adapté à ses quotas
- Les données sont mises en cache automatiquement pour éviter les appels redondants
- Le cache utilise Flask-Caching (SimpleCache en dev, Redis en prod)

### Rate limiting
- Gestion automatique des quotas par API
- Limitation par minute selon les quotas de chaque API
- Exception `RateLimitExceeded` levée si la limite est dépassée

### Normalisation des données
- Tous les DataFrames retournés ont le même format :
  - Colonnes : `Date`, `Open`, `High`, `Low`, `Close`, `Volume`
  - Dates triées chronologiquement
  - Types de données cohérents

### Gestion d'erreurs
- Exceptions personnalisées : `StockAPIError`, `RateLimitExceeded`
- Validation stricte des paramètres (symboles, intervalles)
- Messages d'erreur clairs et informatifs

## Endpoints API REST

### POST /upload/api_fetch
Récupère des données depuis une API et les charge comme un fichier.

**Body (JSON)** :
```json
{
    "source": "yahoo",
    "symbol": "AAPL",
    "interval": "1d",
    "api_key": "optional_key"
}
```

**Réponse** :
```json
{
    "success": true,
    "filename": "yahoo_AAPL_1d.csv",
    "columns": ["Date", "Open", "High", "Low", "Close", "Volume"],
    "preview": [[...]],
    "dtypes": {...}
}
```

### GET /upload/api_list
Retourne la liste des APIs disponibles avec leurs configurations.

**Réponse** :
```json
{
    "success": true,
    "apis": {
        "yahoo": {
            "name": "Yahoo Finance",
            "requires_key": false,
            "has_key": true,
            "quotas": {...}
        },
        ...
    }
}
```

## Bonnes pratiques

1. **Utiliser le cache** : Le service met automatiquement en cache les données. Ne pas créer de mécanismes de cache supplémentaires.

2. **Gérer les erreurs** : Toujours capturer `StockAPIError` et `RateLimitExceeded` séparément pour une meilleure gestion utilisateur.

3. **Respecter les quotas** : Le rate limiting est automatique, mais en cas d'erreur 429, attendre avant de réessayer.

4. **Variables d'environnement** : Ne jamais hardcoder les clés API. Toujours utiliser les variables d'environnement.

5. **Validation** : Valider les symboles et intervalles côté client avant l'appel API.

## Dépannage

### Erreur "Clé API manquante"
- Vérifiez que la variable d'environnement est définie dans `.env`
- Redémarrez l'application après avoir modifié `.env`

### Erreur "Rate limit dépassé"
- Attendez quelques minutes avant de réessayer
- Utilisez une autre API si disponible
- Vérifiez vos quotas sur le site de l'API

### Erreur "Symbole invalide"
- Vérifiez le format du symbole (lettres, chiffres, tirets, points uniquement)
- Assurez-vous que le symbole existe sur l'API choisie
- Pour les crypto-monnaies, utilisez le format "BTC-USD" plutôt que "BTCUSD"

## Extension future

Pour ajouter une nouvelle API :

1. Ajouter les quotas dans `API_QUOTAS`
2. Implémenter la méthode `_fetch_<api_name>()`
3. Ajouter la clé API dans `get_available_apis()`
4. Mettre à jour `fetch_stock_data()` pour gérer le nouveau nom d'API
5. Documenter les intervalles et spécificités

