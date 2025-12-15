"""
Utilitaires partagés pour l'application Flask.
"""

import os
import base64
import json
from io import BytesIO
from datetime import datetime
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sqlite3


def allowed_file(filename, allowed_extensions=None):
    """Vérifie si l'extension du fichier est autorisée."""
    if allowed_extensions is None:
        allowed_extensions = {'csv', 'xlsx', 'xls'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


def load_dataframe(filepath):
    """Charge un DataFrame selon le format du fichier."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Le fichier {filepath} n'existe pas")
    
    try:
        if filepath.endswith('.csv'):
            # Essayer différentes encodages pour les CSV
            encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
            for encoding in encodings:
                try:
                    df = pd.read_csv(filepath, encoding=encoding)
                    if not df.empty:
                        return df
                except UnicodeDecodeError:
                    continue
                except Exception as e:
                    # Si ce n'est pas un problème d'encodage, relancer l'erreur
                    raise
            # Si aucun encodage n'a fonctionné, essayer avec utf-8 et errors='ignore'
            return pd.read_csv(filepath, encoding='utf-8', errors='ignore')
        else:
            # Pour Excel, essayer de lire le premier onglet
            try:
                return pd.read_excel(filepath, engine='openpyxl')
            except:
                # Fallback sur xlrd pour les anciens fichiers .xls
                try:
                    return pd.read_excel(filepath, engine='xlrd')
                except:
                    # Dernier recours : essayer sans spécifier l'engine
                    return pd.read_excel(filepath)
    except pd.errors.EmptyDataError:
        raise ValueError("Le fichier est vide")
    except pd.errors.ParserError as e:
        raise ValueError(f"Erreur de parsing du fichier: {str(e)}")
    except Exception as e:
        raise ValueError(f"Erreur lors du chargement du fichier: {str(e)}")


def _ensure_history_table(conn):
    """Crée la table d'historique des tests si absente."""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS test_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            test_name TEXT NOT NULL,
            filename TEXT NOT NULL,
            columns_used TEXT NOT NULL,
            p_value REAL,
            stat_value REAL,
            interpretation TEXT,
            full_results TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()


def add_to_history(test_name, filename, columns_used, p_value, stat_value, interpretation, full_results, session=None):
    """Ajoute un résultat de test à l'historique de la session utilisateur."""
    if session is None:
        from flask import session as flask_session
        session = flask_session
    
    if 'test_history' not in session:
        session['test_history'] = []
    
    from datetime import datetime
    new_entry = {
        "id": str(len(session['test_history']) + 1),
        "test_name": test_name,
        "filename": filename,
        "columns_used": columns_used if isinstance(columns_used, list) else [columns_used],
        "p_value": float(p_value) if p_value is not None else None,
        "stat_value": float(stat_value) if stat_value is not None else None,
        "interpretation": interpretation,
        "full_results": full_results if isinstance(full_results, dict) else {},
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    }
    session['test_history'].insert(0, new_entry)
    session.modified = True


def get_history(session=None):
    """Retourne l'historique des tests de la session utilisateur."""
    if session is None:
        from flask import session as flask_session
        session = flask_session
    
    return session.get('test_history', [])


def clear_history(session=None):
    """Efface l'historique des tests de la session utilisateur."""
    if session is None:
        from flask import session as flask_session
        session = flask_session
    
    session['test_history'] = []
    session.modified = True


def add_to_forecast_history(forecast_data, session=None):
    """Ajoute une prévision à l'historique de la session utilisateur."""
    if session is None:
        from flask import session as flask_session
        session = flask_session
    
    if 'forecast_history' not in session:
        session['forecast_history'] = []
    
    from datetime import datetime
    if 'timestamp' not in forecast_data:
        forecast_data['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    forecast_data['id'] = str(len(session['forecast_history']) + 1)
    session['forecast_history'].insert(0, forecast_data)
    session.modified = True


def get_forecast_history(session=None):
    """Retourne l'historique des prévisions de la session utilisateur."""
    if session is None:
        from flask import session as flask_session
        session = flask_session
    
    return session.get('forecast_history', [])


def clear_forecast_history(session=None):
    """Efface l'historique des prévisions de la session utilisateur."""
    if session is None:
        from flask import session as flask_session
        session = flask_session
    
    session['forecast_history'] = []
    session.modified = True


def generate_plot_image():
    """Génère une image matplotlib encodée en base64."""
    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close()
    return img_base64


def validate_test_requirements(test_type, selected_columns):
    """Valide les exigences du test sélectionné."""
    requirements = {
        'wilcoxon': 2,
        'mannwhitney': 2,
        'spearman': 2,
        'kolmogorov_smirnov': 1,
        'shapiro_wilk': 1
    }
    
    if test_type in requirements:
        if len(selected_columns) != requirements[test_type]:
            return False, f"Le test {test_type} nécessite exactement {requirements[test_type]} colonne(s)."
    elif test_type in ['kruskal', 'friedman']:
        if len(selected_columns) < 2:
            return False, f"Le test {test_type} nécessite au moins 2 colonnes."
    
    return True, ""


def _ensure_user_table(conn):
    """Crée la table des positions utilisateurs si elle n'existe pas."""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS user_locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            active_users INTEGER DEFAULT 1,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )


def _seed_sample_locations(conn):
    """Insère des données d'exemple si la table est vide."""
    sample_data = [
        ('Abidjan', 5.3600, -4.0083, 150),
        ('Yamoussoukro (Capitale)', 6.8270, -5.2893, 85),
        ('Bouaké', 7.6900, -5.0300, 42),
        ('Daloa', 6.8786, -6.4439, 28),
        ('Korhogo', 9.4577, -5.6281, 35),
        ('San-Pédro', 4.7506, -6.6349, 24),
        ('Gagnoa', 6.1333, -5.9500, 22),
        ('Duekoué', 6.7306, -7.3500, 18),
        ('Soubré', 6.1272, -6.1208, 20),
        ('Odienné', 9.5099, -7.5699, 15)
    ]

    conn.executemany(
        "INSERT INTO user_locations (username, latitude, longitude, active_users) VALUES (?, ?, ?, ?)",
        sample_data,
    )
    conn.commit()


def save_user_location(db_path, username, latitude, longitude, active_users=1):
    """Enregistre ou met à jour la position d'un utilisateur."""
    conn = sqlite3.connect(db_path)
    _ensure_user_table(conn)
    cursor = conn.cursor()

    # Un utilisateur (nom) = une entrée, on écrase l'ancienne position
    cursor.execute("DELETE FROM user_locations WHERE username = ?", (username,))
    cursor.execute(
        """
        INSERT INTO user_locations (username, latitude, longitude, active_users, timestamp)
        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        """,
        (username, latitude, longitude, active_users or 1),
    )
    conn.commit()
    conn.close()


def get_real_time_users_from_db(db_path, seed=True):
    """Récupère les données de localisation utilisateur depuis SQLite."""
    try:
        conn = sqlite3.connect(db_path)
        _ensure_user_table(conn)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM user_locations")
        count = cursor.fetchone()[0]
        if seed and count == 0:
            _seed_sample_locations(conn)

        cursor.execute(
            "SELECT username, latitude, longitude, active_users, timestamp FROM user_locations"
        )
        rows = cursor.fetchall()
        conn.close()

        return [
            {
                "username": row[0],
                "lat": row[1],
                "lon": row[2],
                "active_users": row[3],
                "timestamp": row[4],
            }
            for row in rows
        ]

    except sqlite3.Error as e:
        print(f"Erreur de base de données: {e}")
        return []


def make_features(data, target_col='Close'):
    """
    Crée les features nécessaires à la prédiction du modèle ML.
    """
    data = data.copy()
    data[f'{target_col}_diff'] = data[target_col].diff()
    
    # Lags de différence
    lags = [1, 2, 3, 5, 7, 14]
    for lag in lags:
        data[f'lag_diff_{lag}'] = data[f'{target_col}_diff'].shift(lag)
    
    # Moyennes mobiles de différence
    windows = [3, 7, 14]
    for w in windows:
        data[f'ma_diff_{w}'] = data[f'{target_col}_diff'].rolling(window=w).mean()
    
    # Moyennes mobiles de prix
    for w in [7, 14, 30]:
        data[f'ma_price_{w}'] = data[target_col].rolling(window=w).mean()
    
    # Features temporelles
    if not data.empty:
        # Vérifier si l'index est un DatetimeIndex
        if isinstance(data.index, pd.DatetimeIndex):
            data['day_of_week'] = data.index.dayofweek
            data['day_of_month'] = data.index.day
            data['month'] = data.index.month
        else:
            # Si l'index n'est pas datetime, utiliser des valeurs par défaut
            # ou essayer de convertir
            try:
                # Essayer de convertir l'index en datetime
                data.index = pd.to_datetime(data.index, errors='coerce')
                if isinstance(data.index, pd.DatetimeIndex):
                    data['day_of_week'] = data.index.dayofweek
                    data['day_of_month'] = data.index.day
                    data['month'] = data.index.month
                else:
                    # Si la conversion échoue, utiliser des valeurs par défaut
                    data['day_of_week'] = 0
                    data['day_of_month'] = 1
                    data['month'] = 1
            except:
                # En cas d'erreur, utiliser des valeurs par défaut
                data['day_of_week'] = 0
                data['day_of_month'] = 1
                data['month'] = 1
    
    # Volatilité
    data['volatility'] = data[target_col].rolling(window=20).std()
    
    return data


def prepare_data_for_ml(df, target_column):
    """
    Prépare les données pour l'entraînement du modèle ML.
    """
    # Préparer l'index datetime si nécessaire
    df = df.copy()
    
    # Si l'index n'est pas déjà un DatetimeIndex, essayer de le convertir
    if not isinstance(df.index, pd.DatetimeIndex):
        # Chercher une colonne Date dans les colonnes
        date_cols = [col for col in df.columns if 'date' in col.lower() or 'Date' in col or 'time' in col.lower()]
        if date_cols:
            # Utiliser la première colonne de date trouvée comme index
            df = df.set_index(date_cols[0])
        
        # Essayer de convertir l'index en datetime
        try:
            df.index = pd.to_datetime(df.index, errors='coerce')
            # Trier par date après conversion
            df = df.sort_index()
        except Exception:
            # Si la conversion échoue, garder l'index tel quel
            pass
    
    # Vérifier que la colonne cible existe
    if target_column not in df.columns:
        # Essayer de trouver une colonne similaire
        possible_cols = [col for col in df.columns 
                        if 'close' in col.lower() or 'price' in col.lower() or 'value' in col.lower()]
        if possible_cols:
            target_column = possible_cols[0]
        else:
            raise ValueError(f"La colonne cible '{target_column}' est introuvable dans le fichier.")
    
    # Convertir la colonne cible en numérique
    df[target_column] = pd.to_numeric(df[target_column], errors='coerce')
    
    # Créer les features
    data = make_features(df, target_column)
    
    # Drop na
    data.dropna(inplace=True)
    
    # Sélectionner les features
    feature_columns = [
        f'{target_column}_diff',
        'lag_diff_1', 'lag_diff_2', 'lag_diff_3', 'lag_diff_5', 'lag_diff_7', 'lag_diff_14',
        'ma_diff_3', 'ma_diff_7', 'ma_diff_14',
        'ma_price_7', 'ma_price_14', 'ma_price_30',
        'day_of_week', 'day_of_month', 'month',
        'volatility'
    ]
    
    # Vérifier que les colonnes existent
    feature_columns = [col for col in feature_columns if col in data.columns]
    
    X = data[feature_columns]
    y = data[target_column]
    
    return X, y, feature_columns


### Job storage helpers for background tasks
def _ensure_jobs_dir(app_root=None):
    """Return path to jobs storage directory, ensure it exists."""
    if app_root is None:
        app_root = os.path.dirname(os.path.dirname(__file__))
    jobs_dir = os.path.join(app_root, 'logs', 'jobs')
    os.makedirs(jobs_dir, exist_ok=True)
    return jobs_dir


def _job_path(jobid, app_root=None):
    jobs_dir = _ensure_jobs_dir(app_root)
    return os.path.join(jobs_dir, f"{jobid}.json")


def write_job_pending(jobid, meta=None, app_root=None):
    """Write a pending job file with metadata."""
    payload = {
        'status': 'pending',
        'meta': meta or {},
        'result': None,
        'error': None
    }
    path = _job_path(jobid, app_root)
    with open(path, 'w', encoding='utf-8') as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2, default=str)


def write_job_result(jobid, result, app_root=None):
    """Mark job as done and store result payload."""
    path = _job_path(jobid, app_root)
    payload = {
        'status': 'done',
        'meta': None,
        'result': result,
        'error': None
    }
    with open(path, 'w', encoding='utf-8') as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2, default=str)


def write_job_error(jobid, error_message, app_root=None):
    """Mark job as failed and store error message."""
    path = _job_path(jobid, app_root)
    payload = {
        'status': 'failed',
        'meta': None,
        'result': None,
        'error': str(error_message)
    }
    with open(path, 'w', encoding='utf-8') as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2, default=str)


def read_job(jobid, app_root=None):
    """Read job file and return dict or None if missing/invalid."""
    path = _job_path(jobid, app_root)
    if not os.path.exists(path):
        return None
    try:
        with open(path, 'r', encoding='utf-8') as fh:
            return json.load(fh)
    except Exception:
        return None


### ML Model utilities
def normalize_feature_columns(feature_cols):
    """
    Normalise les feature columns en convertissant les tuples en strings.
    
    Args:
        feature_cols: Liste de colonnes (peut contenir des tuples ou strings)
        
    Returns:
        Liste de strings normalisées
    """
    if not feature_cols:
        return []
    
    normalized = []
    for col in feature_cols:
        if isinstance(col, tuple):
            # Convertir tuple en string avec underscore
            clean_name = '_'.join(str(c).strip() for c in col if c).strip()
            normalized.append(clean_name)
        elif isinstance(col, (list, pd.Index)):
            # Si c'est une liste ou Index, prendre le premier élément
            normalized.append(str(col[0]) if len(col) > 0 else str(col))
        else:
            normalized.append(str(col))
    
    return normalized


def validate_model_artifact(artifact, model_path=None):
    """
    Valide le format d'un artifact de modèle ML.
    
    Args:
        artifact: Dictionnaire chargé depuis joblib
        model_path: Chemin du modèle (pour messages d'erreur)
        
    Returns:
        Tuple (model, feature_columns, metadata)
        
    Raises:
        ValueError: Si le format est invalide
    """
    if not isinstance(artifact, dict):
        raise ValueError(f"Le modèle {model_path or 'inconnu'} n'est pas un dictionnaire. Format attendu: {{'model': <estimator>, 'feature_columns': [<list>]}}")
    
    if 'model' not in artifact:
        raise ValueError(f"Le modèle {model_path or 'inconnu'} ne contient pas de clé 'model'")
    
    model = artifact['model']
    
    # Vérifier que c'est un modèle valide (a une méthode predict)
    if not hasattr(model, 'predict'):
        raise ValueError(f"Le modèle {model_path or 'inconnu'} n'a pas de méthode 'predict'. Type: {type(model)}")
    
    if 'feature_columns' not in artifact:
        raise ValueError(f"Le modèle {model_path or 'inconnu'} ne contient pas de clé 'feature_columns'")
    
    feature_cols = artifact['feature_columns']
    
    if not isinstance(feature_cols, (list, tuple, pd.Index)):
        raise ValueError(f"Les feature_columns du modèle {model_path or 'inconnu'} doivent être une liste. Type reçu: {type(feature_cols)}")
    
    if len(feature_cols) == 0:
        raise ValueError(f"Le modèle {model_path or 'inconnu'} a une liste de feature_columns vide")
    
    # Normaliser les feature columns
    feature_cols_normalized = normalize_feature_columns(feature_cols)
    
    # Metadata optionnelle
    metadata = {
        'target_column': artifact.get('target_column'),
        'model_type': artifact.get('model_type'),
        'version': artifact.get('version'),
        'original_feature_columns': feature_cols
    }
    
    return model, feature_cols_normalized, metadata


def validate_model_data_compatibility(model_feature_cols, data_feature_cols, data_df=None):
    """
    Valide que les features des données sont compatibles avec le modèle.
    
    Args:
        model_feature_cols: Liste des colonnes attendues par le modèle
        data_feature_cols: Liste des colonnes disponibles dans les données
        data_df: DataFrame optionnel pour vérification supplémentaire
        
    Returns:
        Tuple (is_compatible, missing_cols, extra_cols, warnings)
    """
    model_set = set(model_feature_cols)
    data_set = set(data_feature_cols)
    
    missing_cols = model_set - data_set
    extra_cols = data_set - model_set
    
    is_compatible = len(missing_cols) == 0
    
    warnings = []
    
    if missing_cols:
        warnings.append(f"Colonnes manquantes dans les données: {list(missing_cols)[:10]}")
    
    if extra_cols:
        warnings.append(f"Colonnes supplémentaires dans les données (non utilisées): {list(extra_cols)[:10]}")
    
    # Vérifier l'ordre si DataFrame fourni
    if data_df is not None and is_compatible:
        available_cols = [col for col in model_feature_cols if col in data_df.columns]
        if len(available_cols) != len(model_feature_cols):
            warnings.append("Certaines colonnes du modèle ne sont pas disponibles dans le DataFrame")
    
    return is_compatible, list(missing_cols), list(extra_cols), warnings


def ensure_datetime_index(df, date_column=None):
    """
    S'assure que le DataFrame a un index DatetimeIndex.
    
    Args:
        df: DataFrame pandas
        date_column: Nom de la colonne de date (si l'index n'est pas déjà datetime)
        
    Returns:
        DataFrame avec DatetimeIndex
    """
    df = df.copy()
    
    # Si l'index est déjà DatetimeIndex, retourner tel quel
    if isinstance(df.index, pd.DatetimeIndex):
        return df.sort_index()
    
    # Si une colonne de date est spécifiée, l'utiliser comme index
    if date_column and date_column in df.columns:
        df = df.set_index(date_column)
    
    # Essayer de convertir l'index en datetime
    try:
        df.index = pd.to_datetime(df.index, errors='coerce')
        # Supprimer les lignes avec des dates invalides
        df = df.dropna(subset=[df.index.name] if df.index.name else [])
        df = df.sort_index()
        
        # Vérifier qu'on a un DatetimeIndex maintenant
        if isinstance(df.index, pd.DatetimeIndex):
            return df
    except Exception:
        pass
    
    # Si la conversion échoue, créer un DatetimeIndex à partir de RangeIndex
    # Utiliser la date actuelle comme point de départ
    if len(df) > 0:
        start_date = pd.Timestamp.now() - pd.Timedelta(days=len(df))
        df.index = pd.date_range(start=start_date, periods=len(df), freq='D')
    
    return df


def prepare_features_for_prediction(features_df, model_feature_cols, current_df=None, target_column=None):
    """
    Prépare les features pour la prédiction en s'assurant que toutes les colonnes requises sont présentes.
    
    Args:
        features_df: DataFrame avec les features générées
        model_feature_cols: Liste des colonnes attendues par le modèle
        current_df: DataFrame original (pour récupérer des colonnes manquantes)
        target_column: Nom de la colonne cible
        
    Returns:
        DataFrame avec toutes les colonnes requises dans le bon ordre
    """
    features_df = features_df.copy()
    
    # Normaliser les noms de colonnes du DataFrame
    if isinstance(features_df.columns, pd.MultiIndex):
        features_df.columns = ['_'.join(str(c) for c in col).strip() if isinstance(col, tuple) else str(col) 
                               for col in features_df.columns.values]
    features_df.columns = [str(col) for col in features_df.columns]
    
    # Normaliser les feature columns du modèle
    model_feature_cols = normalize_feature_columns(model_feature_cols)
    
    # Identifier les colonnes manquantes
    missing_cols = set(model_feature_cols) - set(features_df.columns)
    
    # Ajouter les colonnes manquantes
    for col in missing_cols:
        # Essayer de trouver la colonne dans current_df
        if current_df is not None and col in current_df.columns:
            features_df[col] = current_df[col].iloc[-1] if len(current_df) > 0 else 0.0
        elif current_df is not None and target_column and col == target_column:
            features_df[col] = current_df[target_column].iloc[-1] if len(current_df) > 0 else 0.0
        else:
            # Valeur par défaut intelligente selon le type de feature
            if 'lag' in col.lower() or 'diff' in col.lower():
                features_df[col] = 0.0
            elif 'ma' in col.lower():
                # Moyenne mobile - utiliser la dernière valeur disponible
                if target_column and target_column in features_df.columns:
                    features_df[col] = features_df[target_column].iloc[-1] if len(features_df) > 0 else 0.0
                else:
                    features_df[col] = 0.0
            elif 'volatility' in col.lower():
                features_df[col] = 0.0
            elif 'day_of' in col.lower() or 'month' in col.lower():
                # Features temporelles - utiliser la date actuelle
                if isinstance(features_df.index, pd.DatetimeIndex) and len(features_df) > 0:
                    last_date = features_df.index[-1]
                    if 'day_of_week' in col.lower():
                        features_df[col] = last_date.dayofweek
                    elif 'day_of_month' in col.lower():
                        features_df[col] = last_date.day
                    elif 'month' in col.lower():
                        features_df[col] = last_date.month
                    else:
                        features_df[col] = 0
                else:
                    features_df[col] = 0
            else:
                features_df[col] = 0.0
    
    # S'assurer que les colonnes sont dans le bon ordre
    # Garder seulement les colonnes du modèle
    available_cols = [col for col in model_feature_cols if col in features_df.columns]
    missing_in_order = [col for col in model_feature_cols if col not in available_cols]
    
    # Réorganiser les colonnes dans l'ordre attendu par le modèle
    ordered_cols = available_cols + missing_in_order
    
    # Créer un DataFrame avec les colonnes dans le bon ordre
    result_df = pd.DataFrame(index=features_df.index)
    for col in model_feature_cols:
        if col in features_df.columns:
            result_df[col] = features_df[col]
        else:
            # Cette colonne devrait avoir été ajoutée ci-dessus
            result_df[col] = 0.0
    
    return result_df
