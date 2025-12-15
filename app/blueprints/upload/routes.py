"""
Blueprint pour la gestion de l'upload de fichiers.
"""
import mimetypes
import os
import re
import shutil
import tempfile
import time
from collections import defaultdict
from typing import Optional

# ClamAV est optionnel - peut ne pas être installé
try:
    import clamd
    CLAMAV_AVAILABLE = True
except ImportError:
    CLAMAV_AVAILABLE = False
    clamd = None

import pandas as pd
import requests
import yfinance as yf
from flask import Blueprint, request, session, jsonify, current_app
from werkzeug.utils import secure_filename
from app.extensions import cache

from app.utils import allowed_file, load_dataframe
from app.services.stock_api_service import get_stock_api_service, StockAPIError, RateLimitExceeded

bp = Blueprint('upload', __name__)

# Rate limiting pour les API externes (par session/IP)
_api_rate_limit = defaultdict(list)
_RATE_LIMIT_WINDOW = 60  # secondes
_RATE_LIMIT_MAX_REQUESTS = 10  # requêtes par fenêtre


@bp.errorhandler(Exception)
def handle_upload_error(e):
    """Gestionnaire d'erreur global pour le blueprint upload."""
    current_app.logger.exception(f"Erreur non gérée dans upload: {e}")
    return jsonify({
        'success': False,
        'message': f'Erreur serveur: {str(e)}'
    }), 500


def _set_session_from_df(df: pd.DataFrame, filename: str):
    """Stocke les infos fichier dans la session et prépare la réponse JSON."""
    try:
        # Convertir les colonnes et les dtypes en types JSON-serializables (clés string)
        columns = [str(c) for c in df.columns.tolist()]
        preview = df.head(5).fillna('').astype(str).values.tolist()
        raw_dtypes = df.dtypes.apply(lambda x: x.name).to_dict()
        dtypes = {str(k): v for k, v in raw_dtypes.items()}

        # Vérifier que la session est disponible
        if not hasattr(session, 'get'):
            current_app.logger.warning("Session Flask non disponible")
        
        session['current_file'] = str(filename)
        session['file_columns'] = columns
        session['file_dtypes'] = dtypes
        session.modified = True  # S'assurer que la session est marquée comme modifiée

        return {
            'success': True,
            'filename': filename,
            'columns': columns,
            'preview': preview,
            'dtypes': dtypes
        }
    except Exception as e:
        current_app.logger.exception(f"Erreur lors de la sauvegarde en session: {e}")
        # Retourner quand même les données même si la session échoue
        return {
            'success': True,
            'filename': filename,
            'columns': df.columns.tolist(),
            'preview': df.head(5).fillna('').astype(str).values.tolist(),
            'dtypes': df.dtypes.apply(lambda x: x.name).to_dict(),
            'warning': 'Session non sauvegardée'
        }


@bp.route('/upload_file', methods=['POST'])
def upload_file():
    """Gère l'upload de fichiers CSV ou Excel."""
    tmp_path = None
    filepath = None
    
    try:
        if 'data_file' not in request.files:
            return jsonify({'success': False, 'message': 'Aucun fichier envoyé'}), 400

        file = request.files['data_file']

        if file.filename == '':
            return jsonify({'success': False, 'message': 'Aucun fichier sélectionné'}), 400

        if not allowed_file(file.filename):
            return jsonify({'success': False, 'message': 'Type de fichier non autorisé'}), 400

        filename = secure_filename(file.filename)
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)

        # Créer le dossier uploads s'il n'existe pas
        try:
            os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
        except Exception as e:
            current_app.logger.error(f"Erreur création dossier uploads: {e}")
            return jsonify({'success': False, 'message': f"Erreur serveur: impossible de créer le dossier d'upload"}), 500

        # Enregistrer dans un fichier temporaire pour inspection
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as tmp:
                file.save(tmp.name)
                tmp_path = tmp.name
        except Exception as e:
            current_app.logger.error(f"Erreur sauvegarde fichier temporaire: {e}")
            return jsonify({'success': False, 'message': f"Erreur lors de la sauvegarde du fichier: {str(e)}"}), 500

        # Contrôle MIME strict : header fourni + deviné + signature simple
        allowed_mimes = {
            'text/csv',
            'text/plain',
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        }
        provided_mime = (file.mimetype or '').split(';')[0].strip()
        guessed_mime, _ = mimetypes.guess_type(filename)

        def looks_like_csv_or_text(head: bytes) -> bool:
            # autorise ASCII/UTF-8 sans NULL
            return b'\x00' not in head

        def looks_like_xlsx(head: bytes) -> bool:
            # XLSX = ZIP donc signature PK
            return head.startswith(b'PK\x03\x04')

        try:
            with open(tmp_path, 'rb') as fh:
                head = fh.read(8)
        except Exception as e:
            current_app.logger.error(f"Erreur lecture fichier temporaire: {e}")
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except:
                    pass
            return jsonify({'success': False, 'message': f"Erreur lors de la lecture du fichier: {str(e)}"}), 500

        signature_ok = looks_like_csv_or_text(head) or looks_like_xlsx(head)
        mime_ok = (
            (provided_mime in allowed_mimes if provided_mime else True)
            and (guessed_mime in allowed_mimes if guessed_mime else True)
        )

        if not (mime_ok and signature_ok):
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except:
                    pass
            return jsonify({'success': False, 'message': 'Type de fichier/MIME non autorisé'}), 400

        # Antivirus ClamAV (si disponible)
        def scan_with_clamav(path: str):
            if not CLAMAV_AVAILABLE or clamd is None:
                current_app.logger.debug("ClamAV non disponible (module non installé)")
                return True, "clamav-unavailable"
            try:
                host = os.getenv('CLAMAV_HOST', 'localhost')
                port = int(os.getenv('CLAMAV_PORT', '3310'))
                client = clamd.ClamdNetworkSocket(host=host, port=port)
                result = client.scan(path)
                if not result:
                    return True, "scan-ok"
                status = list(result.values())[0][0]
                return status == 'OK', status
            except Exception as exc:
                # Si ClamAV indisponible, on log et on laisse passer (défense best-effort)
                current_app.logger.warning("ClamAV indisponible ou non configuré: %s", exc)
                return True, "clamav-unavailable"

        clean, av_status = scan_with_clamav(tmp_path)
        if not clean:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except:
                    pass
            return jsonify({'success': False, 'message': f'Fichier rejeté (AV: {av_status})'}), 400

        # Déplacer le fichier validé vers l'emplacement final
        # Utiliser shutil.move() au lieu de os.replace() pour gérer les déplacements
        # entre différents lecteurs (Windows)
        try:
            # Si le fichier de destination existe déjà, le supprimer d'abord
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except Exception as e:
                    current_app.logger.warning(f"Impossible de supprimer le fichier existant {filepath}: {e}")
            
            shutil.move(tmp_path, filepath)
            tmp_path = None  # Marquer comme déplacé pour éviter la suppression
        except Exception as e:
            current_app.logger.error(f"Erreur déplacement fichier: {e}")
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except:
                    pass
            return jsonify({'success': False, 'message': f"Erreur lors du déplacement du fichier: {str(e)}"}), 500

        # Charger le DataFrame
        try:
            df = load_dataframe(filepath)
            if df is None or df.empty:
                if filepath and os.path.exists(filepath):
                    try:
                        os.remove(filepath)
                    except:
                        pass
                return jsonify({'success': False, 'message': 'Le fichier est vide ou ne contient pas de données valides'}), 400
            
            # Stocker dans la session et retourner la réponse
            return jsonify(_set_session_from_df(df, filename))

        except pd.errors.EmptyDataError:
            if filepath and os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except:
                    pass
            return jsonify({'success': False, 'message': 'Le fichier est vide'}), 400
        except pd.errors.ParserError as e:
            if filepath and os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except:
                    pass
            current_app.logger.error(f"Erreur parsing fichier: {e}")
            return jsonify({'success': False, 'message': f"Erreur de format du fichier: {str(e)}"}), 400
        except Exception as e:
            if filepath and os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except:
                    pass
            current_app.logger.exception(f"Erreur chargement DataFrame: {e}")
            return jsonify({'success': False, 'message': f"Erreur de lecture: {str(e)}"}), 500

    except Exception as e:
        # Nettoyage en cas d'erreur inattendue
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except:
                pass
        if filepath and os.path.exists(filepath):
            try:
                os.remove(filepath)
            except:
                pass
        current_app.logger.exception(f"Erreur inattendue lors de l'upload: {e}")
        return jsonify({'success': False, 'message': f"Erreur serveur interne: {str(e)}"}), 500


@bp.route("/clear_session_file", methods=["POST"])
def clear_session_file():
    """Efface les données du fichier en session."""
    for key in ['current_file', 'file_columns', 'file_dtypes']:
        session.pop(key, None)
    return jsonify({'success': True})


def _validate_symbol(symbol: str) -> bool:
    """Valide le format d'un symbole boursier."""
    # Alphanumérique, tirets, points, max 20 caractères
    if not symbol or len(symbol) > 20:
        return False
    return bool(re.match(r'^[A-Z0-9.\-]+$', symbol.upper()))


def _validate_interval_yahoo(interval: Optional[str]) -> bool:
    """Valide l'intervalle Yahoo Finance."""
    valid_intervals = {'1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h', '1d', '5d', '1wk', '1mo', '3mo'}
    return interval is None or interval in valid_intervals


def _validate_interval_alpha_vantage(interval: Optional[str]) -> bool:
    """Valide l'intervalle Alpha Vantage."""
    valid_intervals = {'daily', 'weekly', 'monthly'}
    return interval is None or interval in valid_intervals


def _check_rate_limit(identifier: str) -> bool:
    """Vérifie le rate limiting pour un identifiant (session/IP)."""
    now = time.time()
    # Nettoyer les anciennes entrées
    _api_rate_limit[identifier] = [
        ts for ts in _api_rate_limit[identifier]
        if now - ts < _RATE_LIMIT_WINDOW
    ]
    # Vérifier la limite
    if len(_api_rate_limit[identifier]) >= _RATE_LIMIT_MAX_REQUESTS:
        return False
    # Ajouter la requête actuelle
    _api_rate_limit[identifier].append(now)
    return True


@cache.memoize(timeout=300)  # Cache 5 minutes avec clé basée sur les paramètres
def _fetch_yahoo(symbol: str, interval: Optional[str]) -> pd.DataFrame:
    """Récupère des données depuis Yahoo Finance avec validation et sécurité."""
    # Validation
    if not _validate_symbol(symbol):
        raise ValueError("Symbole invalide (format attendu: lettres/chiffres, tirets, points)")
    
    yf_interval = interval or '1d'
    if not _validate_interval_yahoo(yf_interval):
        raise ValueError(f"Intervalle Yahoo invalide: {yf_interval}")
    
    # Choix d'une période adaptée à l'intervalle
    period = '1y'
    if yf_interval in ('1m', '2m', '5m', '15m', '30m', '60m', '90m'):
        period = '7d'
    elif yf_interval in ('1h',):
        period = '60d'
    
    try:
        # Timeout de 30 secondes pour éviter les blocages
        data = yf.download(symbol, interval=yf_interval, period=period, progress=False, timeout=30)
        if data is None or data.empty:
            raise ValueError("Aucune donnée retournée par Yahoo Finance")
        
        # Validation des données retournées
        if len(data) < 1:
            raise ValueError("Données insuffisantes retournées par Yahoo Finance")
        
        data.reset_index(inplace=True)
        return data
    except Exception as e:
        current_app.logger.error(f"Erreur Yahoo Finance pour {symbol}: {str(e)}")
        raise ValueError(f"Erreur lors de la récupération des données Yahoo Finance: {str(e)}")


@cache.memoize(timeout=300)  # Cache 5 minutes avec clé basée sur les paramètres
def _fetch_alpha_vantage(symbol: str, interval: Optional[str], api_key: Optional[str]) -> pd.DataFrame:
    """Récupère des données depuis Alpha Vantage avec validation et sécurité."""
    # Validation du symbole
    if not _validate_symbol(symbol):
        raise ValueError("Symbole invalide (format attendu: lettres/chiffres, tirets, points)")
    
    # Validation de l'intervalle
    if not _validate_interval_alpha_vantage(interval):
        raise ValueError(f"Intervalle Alpha Vantage invalide: {interval}")
    
    # Validation de la clé API
    key = api_key or os.getenv('ALPHAVANTAGE_KEY')
    if not key:
        raise ValueError("Clé API Alpha Vantage manquante (api_key ou ALPHAVANTAGE_KEY)")
    
    # Sanitization de la clé API (alphanumérique uniquement)
    if not re.match(r'^[A-Z0-9]+$', key.upper()):
        raise ValueError("Format de clé API invalide")
    
    interval_map = {
        'daily': 'TIME_SERIES_DAILY',
        'weekly': 'TIME_SERIES_WEEKLY',
        'monthly': 'TIME_SERIES_MONTHLY'
    }
    chosen_interval = interval or 'daily'
    func = interval_map.get(chosen_interval)
    if not func:
        raise ValueError("Intervalle Alpha Vantage invalide (daily, weekly, monthly)")

    url = "https://www.alphavantage.co/query"
    params = {
        'function': func,
        'symbol': symbol.upper(),  # Normalisation en majuscules
        'datatype': 'csv',
        'outputsize': 'compact',
        'apikey': key.upper()  # Normalisation
    }
    
    try:
        # Timeout de 30 secondes, vérification SSL
        resp = requests.get(url, params=params, timeout=30, verify=True)
        
        if resp.status_code != 200:
            raise ValueError(f"Erreur API Alpha Vantage: HTTP {resp.status_code}")
        
        # Vérification des erreurs API
        if 'Thank you for using Alpha Vantage' in resp.text and 'API call frequency' in resp.text:
            raise ValueError("Limite de fréquence Alpha Vantage atteinte")
        
        if 'Error Message' in resp.text or 'Invalid API call' in resp.text:
            raise ValueError("Erreur dans la réponse Alpha Vantage")
        
        # Validation du contenu CSV
        if not resp.text or len(resp.text) < 50:
            raise ValueError("Réponse API Alpha Vantage vide ou invalide")
        
        df = pd.read_csv(pd.compat.StringIO(resp.text))
        if df.empty or len(df) < 1:
            raise ValueError("Aucune donnée retournée par Alpha Vantage")
        
        # Validation des colonnes attendues
        required_cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        if not all(col.lower() in [c.lower() for c in df.columns] for col in required_cols[:4]):
            raise ValueError("Format de données Alpha Vantage invalide")
        
        return df
    except requests.exceptions.Timeout:
        raise ValueError("Timeout lors de l'appel API Alpha Vantage")
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Erreur réseau Alpha Vantage: {str(e)}")
        raise ValueError(f"Erreur réseau lors de l'appel API Alpha Vantage")
    except Exception as e:
        current_app.logger.error(f"Erreur Alpha Vantage pour {symbol}: {str(e)}")
        raise


@bp.route('/upload/api_fetch', methods=['POST'])
def api_fetch():
    """Récupère des données boursières depuis une API gratuite et les charge comme un fichier."""
    # Rate limiting par session (pour limiter les abus côté client)
    session_id = session.get('_id', request.remote_addr)
    if not _check_rate_limit(session_id):
        return jsonify({
            'success': False,
            'message': f'Trop de requêtes. Limite: {_RATE_LIMIT_MAX_REQUESTS} requêtes par {_RATE_LIMIT_WINDOW} secondes'
        }), 429
    
    payload = request.get_json(silent=True) or {}
    source = (payload.get('source') or '').strip().lower()
    symbol = (payload.get('symbol') or '').strip().upper()  # Normalisation
    interval = (payload.get('interval') or '').strip() or None
    api_key = (payload.get('api_key') or '').strip() or None

    # Validation stricte des paramètres - support des nouvelles APIs
    valid_sources = {'yahoo', 'alpha_vantage', 'iex_cloud'}
    if not source or source not in valid_sources:
        return jsonify({
            'success': False, 
            'message': f'Paramètre source requis: {", ".join(valid_sources)}'
        }), 400
    
    if not symbol:
        return jsonify({'success': False, 'message': 'Paramètre symbol requis'}), 400
    
    # Validation de la longueur du symbole
    if len(symbol) > 20:
        return jsonify({'success': False, 'message': 'Symbole trop long (max 20 caractères)'}), 400

    # Utiliser le service API centralisé
    try:
        # Obtenir le service depuis l'application ou créer une instance avec le cache
        if hasattr(current_app, 'stock_api_service') and current_app.stock_api_service:
            api_service = current_app.stock_api_service
        else:
            api_service = get_stock_api_service(cache=cache)
        
        # Récupérer les données via le service
        df = api_service.fetch_stock_data(
            api_name=source,
            symbol=symbol,
            interval=interval,
            api_key=api_key
        )
        
    except RateLimitExceeded as e:
        # Rate limit spécifique à l'API
        current_app.logger.warning(f"Rate limit dépassé pour {source}: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Limite de requêtes dépassée pour {source}: {str(e)}'
        }), 429
    except StockAPIError as exc:
        # Erreurs API spécifiques
        current_app.logger.error(f"Erreur API {source} pour {symbol}: {str(exc)}")
        return jsonify({'success': False, 'message': f'Erreur API ({source}): {str(exc)}'}), 400
    except Exception as exc:
        # Erreurs inattendues
        current_app.logger.exception(f"Erreur inattendue API {source}: {exc}")
        return jsonify({
            'success': False, 
            'message': f'Erreur serveur lors de l\'appel API ({source})'
        }), 500

    # Sécurisation du nom de fichier
    safe_symbol = re.sub(r'[^A-Z0-9.\-]', '', symbol)
    filename = secure_filename(f"{source}_{safe_symbol}_{interval or 'default'}.csv")
    
    # Limitation de la taille du nom de fichier
    if len(filename) > 255:
        filename = secure_filename(f"{source}_{safe_symbol[:20]}.csv")
    
    os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    
    try:
        # Validation de la taille des données avant sauvegarde
        if len(df) > 10000:  # Limite raisonnable
            current_app.logger.warning(f"Dataset volumineux: {len(df)} lignes pour {symbol}")
        
        df.to_csv(filepath, index=False)
        return jsonify(_set_session_from_df(df, filename))
    except Exception as exc:
        current_app.logger.exception(f"Erreur sauvegarde fichier API: {exc}")
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except:
                pass
        return jsonify({'success': False, 'message': f'Impossible d\'enregistrer les données: {exc}'}), 500


@bp.route('/upload/api_list', methods=['GET'])
def api_list():
    """Retourne la liste des APIs boursières disponibles avec leurs configurations."""
    try:
        # Obtenir le service depuis l'application
        if hasattr(current_app, 'stock_api_service') and current_app.stock_api_service:
            api_service = current_app.stock_api_service
        else:
            api_service = get_stock_api_service(cache=cache)
        
        apis = api_service.get_available_apis()
        return jsonify({
            'success': True,
            'apis': apis
        })
    except Exception as e:
        current_app.logger.exception(f"Erreur lors de la récupération de la liste des APIs: {e}")
        return jsonify({
            'success': False,
            'message': 'Erreur lors de la récupération de la liste des APIs'
        }), 500
