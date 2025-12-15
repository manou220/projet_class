"""
Service backend pour l'interrogation d'APIs boursières réelles.

Ce module fournit une interface unifiée pour accéder à différentes APIs boursières :
- Yahoo Finance (gratuit, pas de clé API requise)
- Alpha Vantage (gratuit avec clé API, limité à 5 appels/min, 500/jour)
- IEX Cloud (gratuit avec clé API, limité selon le plan)

Le service implémente :
- Un cache intelligent pour réduire les appels API
- Un rate limiting par API pour respecter les quotas
- Une gestion d'erreurs robuste
- Une normalisation des données retournées
"""

import os
import re
import time
from collections import defaultdict
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timedelta

import pandas as pd
import requests
import yfinance as yf
from flask import current_app
from flask_caching import Cache

# Configuration des quotas par API
API_QUOTAS = {
    'yahoo': {
        'requests_per_minute': 2000,  # Limite approximative (pas de limite officielle stricte)
        'requests_per_day': None,  # Pas de limite quotidienne connue
        'cache_timeout': 300  # 5 minutes par défaut
    },
    'alpha_vantage': {
        'requests_per_minute': 5,
        'requests_per_day': 500,
        'cache_timeout': 3600  # 1 heure (API gratuite limitée)
    },
    'iex_cloud': {
        'requests_per_minute': 100,  # Selon le plan gratuit
        'requests_per_day': 50000,  # Selon le plan gratuit
        'cache_timeout': 300  # 5 minutes
    }
}

# Rate limiting par API (en mémoire)
_rate_limiters: Dict[str, Dict[str, list]] = defaultdict(lambda: defaultdict(list))


class StockAPIError(Exception):
    """Exception personnalisée pour les erreurs d'API boursière."""
    pass


class RateLimitExceeded(StockAPIError):
    """Exception levée lorsque le rate limit est dépassé."""
    pass


class StockAPIService:
    """
    Service centralisé pour l'accès aux APIs boursières.
    
    Gère le cache, le rate limiting et la normalisation des données.
    """
    
    def __init__(self, cache: Optional[Cache] = None):
        """
        Initialise le service.
        
        Args:
            cache: Instance Flask-Caching (optionnel)
        """
        self.cache = cache
        self._rate_limiters = _rate_limiters
        
    def get_available_apis(self) -> Dict[str, Dict[str, Any]]:
        """
        Retourne la liste des APIs disponibles avec leurs configurations.
        
        Returns:
            Dict contenant les informations sur chaque API
        """
        apis = {}
        
        # Yahoo Finance - toujours disponible
        apis['yahoo'] = {
            'name': 'Yahoo Finance',
            'requires_key': False,
            'has_key': True,  # Pas de clé requise
            'quotas': API_QUOTAS['yahoo']
        }
        
        # Alpha Vantage
        alphavantage_key = os.getenv('ALPHAVANTAGE_KEY')
        apis['alpha_vantage'] = {
            'name': 'Alpha Vantage',
            'requires_key': True,
            'has_key': bool(alphavantage_key),
            'quotas': API_QUOTAS['alpha_vantage']
        }
        
        # IEX Cloud
        iex_key = os.getenv('IEX_CLOUD_API_KEY')
        apis['iex_cloud'] = {
            'name': 'IEX Cloud',
            'requires_key': True,
            'has_key': bool(iex_key),
            'quotas': API_QUOTAS['iex_cloud']
        }
        
        return apis
    
    def _check_rate_limit(self, api_name: str, identifier: str) -> bool:
        """
        Vérifie le rate limiting pour une API et un identifiant.
        
        Args:
            api_name: Nom de l'API
            identifier: Identifiant unique (session ID, IP, etc.)
            
        Returns:
            True si la requête est autorisée, False sinon
            
        Raises:
            RateLimitExceeded: Si la limite est dépassée
        """
        if api_name not in API_QUOTAS:
            return True
        
        quota = API_QUOTAS[api_name]
        now = time.time()
        
        # Nettoyer les anciennes entrées (fenêtre glissante)
        limiter = self._rate_limiters[api_name][identifier]
        limiter[:] = [ts for ts in limiter if now - ts < 60]  # Fenêtre de 1 minute
        
        # Vérifier la limite par minute
        if len(limiter) >= quota['requests_per_minute']:
            raise RateLimitExceeded(
                f"Rate limit dépassé pour {api_name}: "
                f"{quota['requests_per_minute']} requêtes/min maximum"
            )
        
        # Enregistrer la requête
        limiter.append(now)
        return True
    
    def _validate_symbol(self, symbol: str) -> bool:
        """Valide le format d'un symbole boursier."""
        if not symbol or len(symbol) > 20:
            return False
        return bool(re.match(r'^[A-Z0-9.\-]+$', symbol.upper()))
    
    def _get_cache_key(self, api_name: str, symbol: str, interval: Optional[str], 
                       **kwargs) -> str:
        """Génère une clé de cache pour une requête."""
        params = '_'.join(f"{k}={v}" for k, v in sorted(kwargs.items()) if v)
        interval_str = interval or 'default'
        return f"stock_api:{api_name}:{symbol.upper()}:{interval_str}:{params}"
    
    def fetch_stock_data(self, api_name: str, symbol: str, 
                        interval: Optional[str] = None,
                        api_key: Optional[str] = None,
                        **kwargs) -> pd.DataFrame:
        """
        Récupère des données boursières depuis une API spécifiée.
        
        Args:
            api_name: Nom de l'API ('yahoo', 'alpha_vantage', 'iex_cloud')
            symbol: Symbole boursier (ex: 'AAPL', 'MSFT', 'BTC-USD')
            interval: Intervalle des données (dépend de l'API)
            api_key: Clé API optionnelle (prioritaire sur celle de l'env)
            **kwargs: Paramètres supplémentaires spécifiques à l'API
            
        Returns:
            DataFrame pandas avec les colonnes: Date, Open, High, Low, Close, Volume
            
        Raises:
            StockAPIError: En cas d'erreur API
            RateLimitExceeded: Si le rate limit est dépassé
        """
        # Validation
        if not self._validate_symbol(symbol):
            raise StockAPIError("Symbole invalide (format attendu: lettres/chiffres, tirets, points)")
        
        symbol = symbol.upper()
        api_name = api_name.lower()
        
        # Vérifier le rate limiting (utiliser un identifiant générique pour le cache)
        try:
            self._check_rate_limit(api_name, 'global')
        except RateLimitExceeded as e:
            if current_app:
                current_app.logger.warning(str(e))
            raise
        
        # Vérifier le cache
        if self.cache:
            cache_key = self._get_cache_key(api_name, symbol, interval, **kwargs)
            cached_data = self.cache.get(cache_key)
            if cached_data is not None:
                if current_app:
                    current_app.logger.debug(f"Données récupérées du cache: {cache_key}")
                return cached_data
        
        # Appeler l'API appropriée
        try:
            if api_name == 'yahoo':
                df = self._fetch_yahoo(symbol, interval, **kwargs)
            elif api_name == 'alpha_vantage':
                df = self._fetch_alpha_vantage(symbol, interval, api_key, **kwargs)
            elif api_name == 'iex_cloud':
                df = self._fetch_iex_cloud(symbol, interval, api_key, **kwargs)
            else:
                raise StockAPIError(f"API non supportée: {api_name}")
        except Exception as e:
            if current_app:
                current_app.logger.error(f"Erreur lors de l'appel API {api_name} pour {symbol}: {e}")
            if isinstance(e, (StockAPIError, RateLimitExceeded)):
                raise
            raise StockAPIError(f"Erreur API {api_name}: {str(e)}")
        
        # Normaliser le DataFrame
        df = self._normalize_dataframe(df)
        
        # Mettre en cache
        if self.cache and api_name in API_QUOTAS:
            cache_key = self._get_cache_key(api_name, symbol, interval, **kwargs)
            timeout = API_QUOTAS[api_name]['cache_timeout']
            self.cache.set(cache_key, df, timeout=timeout)
            if current_app:
                current_app.logger.debug(f"Données mises en cache: {cache_key} (timeout: {timeout}s)")
        
        return df
    
    def _fetch_yahoo(self, symbol: str, interval: Optional[str] = None, 
                    **kwargs) -> pd.DataFrame:
        """Récupère des données depuis Yahoo Finance."""
        yf_interval = interval or '1d'
        
        # Validation de l'intervalle
        valid_intervals = {'1m', '2m', '5m', '15m', '30m', '60m', '90m', 
                          '1h', '1d', '5d', '1wk', '1mo', '3mo'}
        if yf_interval not in valid_intervals:
            raise StockAPIError(f"Intervalle Yahoo invalide: {yf_interval}")
        
        # Choix d'une période adaptée à l'intervalle
        period = kwargs.get('period', None)
        if not period:
            if yf_interval in ('1m', '2m', '5m', '15m', '30m', '60m', '90m'):
                period = '7d'
            elif yf_interval == '1h':
                period = '60d'
            else:
                period = '1y'
        
        try:
            # Timeout de 30 secondes
            data = yf.download(
                symbol, 
                interval=yf_interval, 
                period=period, 
                progress=False, 
                timeout=30
            )
            
            if data is None or data.empty:
                raise StockAPIError("Aucune donnée retournée par Yahoo Finance")
            
            if len(data) < 1:
                raise StockAPIError("Données insuffisantes retournées par Yahoo Finance")
            
            data.reset_index(inplace=True)
            return data
            
        except Exception as e:
            raise StockAPIError(f"Erreur Yahoo Finance: {str(e)}")
    
    def _fetch_alpha_vantage(self, symbol: str, interval: Optional[str] = None,
                            api_key: Optional[str] = None, **kwargs) -> pd.DataFrame:
        """Récupère des données depuis Alpha Vantage."""
        # Validation de l'intervalle
        valid_intervals = {'daily', 'weekly', 'monthly'}
        if interval and interval not in valid_intervals:
            raise StockAPIError(f"Intervalle Alpha Vantage invalide: {interval}. Options: daily, weekly, monthly")
        
        # Obtenir la clé API
        key = api_key or os.getenv('ALPHAVANTAGE_KEY')
        if not key:
            raise StockAPIError("Clé API Alpha Vantage manquante (api_key ou ALPHAVANTAGE_KEY)")
        
        # Validation de la clé API
        if not re.match(r'^[A-Z0-9]+$', key.upper()):
            raise StockAPIError("Format de clé API invalide")
        
        # Mapping des intervalles
        interval_map = {
            'daily': 'TIME_SERIES_DAILY',
            'weekly': 'TIME_SERIES_WEEKLY',
            'monthly': 'TIME_SERIES_MONTHLY'
        }
        chosen_interval = interval or 'daily'
        func = interval_map.get(chosen_interval)
        if not func:
            raise StockAPIError("Intervalle Alpha Vantage invalide")
        
        url = "https://www.alphavantage.co/query"
        params = {
            'function': func,
            'symbol': symbol,
            'datatype': 'csv',
            'outputsize': kwargs.get('outputsize', 'compact'),
            'apikey': key.upper()
        }
        
        try:
            resp = requests.get(url, params=params, timeout=30, verify=True)
            
            if resp.status_code != 200:
                raise StockAPIError(f"Erreur HTTP {resp.status_code} depuis Alpha Vantage")
            
            # Vérifier les erreurs API
            if 'Thank you for using Alpha Vantage' in resp.text and 'API call frequency' in resp.text:
                raise RateLimitExceeded("Limite de fréquence Alpha Vantage atteinte")
            
            if 'Error Message' in resp.text or 'Invalid API call' in resp.text:
                raise StockAPIError("Erreur dans la réponse Alpha Vantage")
            
            # Parser le CSV
            if not resp.text or len(resp.text) < 50:
                raise StockAPIError("Réponse API Alpha Vantage vide ou invalide")
            
            df = pd.read_csv(pd.compat.StringIO(resp.text))
            if df.empty or len(df) < 1:
                raise StockAPIError("Aucune donnée retournée par Alpha Vantage")
            
            # Vérifier les colonnes attendues
            required_cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
            if not all(col.lower() in [c.lower() for c in df.columns] for col in required_cols[:4]):
                raise StockAPIError("Format de données Alpha Vantage invalide")
            
            return df
            
        except requests.exceptions.Timeout:
            raise StockAPIError("Timeout lors de l'appel API Alpha Vantage")
        except requests.exceptions.RequestException as e:
            raise StockAPIError(f"Erreur réseau Alpha Vantage: {str(e)}")
        except (StockAPIError, RateLimitExceeded):
            raise
        except Exception as e:
            raise StockAPIError(f"Erreur inattendue Alpha Vantage: {str(e)}")
    
    def _fetch_iex_cloud(self, symbol: str, interval: Optional[str] = None,
                        api_key: Optional[str] = None, **kwargs) -> pd.DataFrame:
        """Récupère des données depuis IEX Cloud."""
        # Obtenir la clé API
        key = api_key or os.getenv('IEX_CLOUD_API_KEY')
        if not key:
            raise StockAPIError("Clé API IEX Cloud manquante (api_key ou IEX_CLOUD_API_KEY)")
        
        # Validation de la clé API (format sk-xxx ou pk-xxx)
        if not re.match(r'^(sk|pk)-[a-zA-Z0-9]+$', key):
            raise StockAPIError("Format de clé API IEX Cloud invalide (format attendu: sk-xxx ou pk-xxx)")
        
        # Déterminer la fonction selon l'intervalle
        # IEX Cloud utilise différents endpoints selon le type de données
        chosen_interval = interval or '1d'
        
        # Mapping des intervalles IEX Cloud
        # Options: 1m, 1d, 1w, 1m (month), 1y, 5y
        if chosen_interval in ('1m', '5m', '15m', '30m', '1h'):
            # Données intraday
            url = f"https://cloud.iexapis.com/stable/stock/{symbol}/chart/1d"
        else:
            # Données historiques
            range_param = '1y'  # Par défaut 1 an
            if chosen_interval == '1d':
                range_param = '1m'  # 1 mois de données quotidiennes
            elif chosen_interval == '1w':
                range_param = '3m'
            elif chosen_interval == '1mo':
                range_param = '1y'
            
            url = f"https://cloud.iexapis.com/stable/stock/{symbol}/chart/{range_param}"
        
        params = {
            'token': key
        }
        
        try:
            resp = requests.get(url, params=params, timeout=30, verify=True)
            
            if resp.status_code == 401:
                raise StockAPIError("Clé API IEX Cloud invalide ou expirée")
            elif resp.status_code == 402:
                raise StockAPIError("Quota IEX Cloud dépassé - veuillez vérifier votre plan")
            elif resp.status_code != 200:
                raise StockAPIError(f"Erreur HTTP {resp.status_code} depuis IEX Cloud")
            
            data = resp.json()
            if not data or len(data) == 0:
                raise StockAPIError("Aucune donnée retournée par IEX Cloud")
            
            # Convertir en DataFrame
            df = pd.DataFrame(data)
            
            # Normaliser les colonnes (IEX Cloud utilise des noms différents)
            column_mapping = {
                'date': 'Date',
                'open': 'Open',
                'high': 'High',
                'low': 'Low',
                'close': 'Close',
                'volume': 'Volume'
            }
            
            # Renommer les colonnes si nécessaire
            for old_col, new_col in column_mapping.items():
                if old_col in df.columns:
                    df.rename(columns={old_col: new_col}, inplace=True)
            
            # Convertir la date si nécessaire
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'])
            
            return df
            
        except requests.exceptions.Timeout:
            raise StockAPIError("Timeout lors de l'appel API IEX Cloud")
        except requests.exceptions.RequestException as e:
            raise StockAPIError(f"Erreur réseau IEX Cloud: {str(e)}")
        except ValueError as e:
            raise StockAPIError(f"Erreur de parsing JSON IEX Cloud: {str(e)}")
        except (StockAPIError, RateLimitExceeded):
            raise
        except Exception as e:
            raise StockAPIError(f"Erreur inattendue IEX Cloud: {str(e)}")
    
    def _normalize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalise un DataFrame pour avoir un format standardisé.
        
        Colonnes attendues: Date, Open, High, Low, Close, Volume
        """
        # Faire une copie pour éviter de modifier l'original
        df = df.copy()
        
        # Normaliser les noms de colonnes (insensible à la casse)
        column_mapping = {}
        for col in df.columns:
            col_lower = col.lower()
            if 'date' in col_lower or col_lower == 'datetime':
                column_mapping[col] = 'Date'
            elif 'open' in col_lower:
                column_mapping[col] = 'Open'
            elif 'high' in col_lower:
                column_mapping[col] = 'High'
            elif 'low' in col_lower:
                column_mapping[col] = 'Low'
            elif 'close' in col_lower:
                column_mapping[col] = 'Close'
            elif 'volume' in col_lower:
                column_mapping[col] = 'Volume'
            elif col_lower == 'timestamp':
                column_mapping[col] = 'Date'
        
        df.rename(columns=column_mapping, inplace=True)
        
        # S'assurer que Date est un datetime
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])
        
        # Trier par date (plus ancien au plus récent)
        if 'Date' in df.columns:
            df.sort_values('Date', inplace=True)
            df.reset_index(drop=True, inplace=True)
        
        return df


# Instance singleton du service
_service_instance: Optional[StockAPIService] = None


def get_stock_api_service(cache: Optional[Cache] = None) -> StockAPIService:
    """
    Obtient l'instance singleton du service API boursière.
    
    Args:
        cache: Instance Flask-Caching (utilisée si fournie)
        
    Returns:
        Instance de StockAPIService
    """
    global _service_instance
    
    if _service_instance is None:
        _service_instance = StockAPIService(cache=cache)
    elif cache and not _service_instance.cache:
        # Mettre à jour le cache si fourni et non encore défini
        _service_instance.cache = cache
    
    return _service_instance

