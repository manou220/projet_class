"""
Blueprint pour les prévisions utilisant des modèles de Machine Learning.
"""
import os
import json
import numpy as np
import pandas as pd
import joblib
import matplotlib.pyplot as plt
from datetime import datetime
from io import BytesIO
from flask import Blueprint, render_template, request, session, current_app, jsonify, send_file, redirect, url_for
import uuid
from pandas.tseries.offsets import DateOffset
from app import utils as _utils
from app.extensions import executor


def get_available_models():
    """Récupère la liste des modèles ML disponibles."""
    # Utiliser le chemin depuis la configuration de l'app
    from flask import current_app
    try:
        models_dir = current_app.config.get('MODELS_DIR')
        if not models_dir:
            # Fallback si MODELS_DIR n'est pas défini
            models_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'models')
    except RuntimeError:
        # Si on n'est pas dans un contexte d'application, utiliser le chemin relatif
        models_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'models')
    
    available_models = {}
    
    if os.path.exists(models_dir):
        for file in os.listdir(models_dir):
            if file.endswith('.joblib'):
                available_models[file] = f"Modèle: {file.replace('.joblib', '')}"
    
    return available_models


def calculate_forecast_metrics(historical_data, forecast_data, target_column):
    """Calcule les métriques de prévision avec gestion des NaN."""
    # Fonction helper pour nettoyer les NaN
    def clean_nan(value):
        return 0.0 if np.isnan(value) or np.isinf(value) else float(value)
    
    metrics = {
        'historical_mean': clean_nan(historical_data[target_column].mean()),
        'historical_std': clean_nan(historical_data[target_column].std()),
        'forecast_mean': clean_nan(forecast_data[target_column].mean()),
        'forecast_range': [
            clean_nan(forecast_data[target_column].min()), 
            clean_nan(forecast_data[target_column].max())
        ],
        'confidence_range': [
            clean_nan(forecast_data['lower_bound'].min()), 
            clean_nan(forecast_data['upper_bound'].max())
        ]
    }
    return metrics


def generate_forecast_plot(historical_data, forecast_data, target_column, forecast_type):
    """Génère le graphique de prévision."""
    plt.figure(figsize=(14, 7))
    
    # S'assurer que les index sont compatibles
    # Convertir les index en DatetimeIndex si possible
    try:
        if not isinstance(historical_data.index, pd.DatetimeIndex):
            historical_data.index = pd.to_datetime(historical_data.index, errors='coerce')
        if not isinstance(forecast_data.index, pd.DatetimeIndex):
            forecast_data.index = pd.to_datetime(forecast_data.index, errors='coerce')
    except Exception:
        # Si la conversion échoue, utiliser des indices numériques
        historical_data.index = range(len(historical_data))
        forecast_data.index = range(len(historical_data), len(historical_data) + len(forecast_data))
    
    # Données historiques
    plt.plot(historical_data.index, historical_data[target_column], 
         label='Données historiques', color='blue', linewidth=2)
    
    # Prévisions
    plt.plot(forecast_data.index, forecast_data[target_column], 
         label='Prévisions', color='red', linewidth=2, linestyle='--')
    
    # Intervalle de confiance - utiliser les vraies dates
    plt.fill_between(forecast_data.index, 
             forecast_data['lower_bound'].values,
             forecast_data['upper_bound'].values,
             alpha=0.2, color='red', label='Intervalle de confiance')
    
    plt.xlabel('Date')
    plt.ylabel(target_column)
    plt.title(f'Prévisions {target_column}')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    return _utils.generate_plot_image()


def _run_forecast_job(jobid, params):
    """Exécute une prévision en arrière-plan (background job)."""
    try:
        model_path = params['model_path']
        filepath = params['filepath']
        target_column = params.get('target_column', 'Close')
        forecast_steps = int(params.get('forecast_steps', 10))
        confidence_level = float(params.get('confidence_level', 95))
        forecast_interval = params.get('forecast_interval', 'jour')
        forecast_type = params.get('forecast_type', 'close_price')

        # Charger et valider le modèle
        artifact = joblib.load(model_path)
        model, feature_cols, model_metadata = _utils.validate_model_artifact(artifact, model_path)

        df = _utils.load_dataframe(filepath)
        
        # Nettoyer les colonnes du DataFrame
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = ['_'.join(str(c) for c in col).strip() if isinstance(col, tuple) else str(col) 
                         for col in df.columns.values]
        df.columns = [str(col) for col in df.columns]
        
        # S'assurer que le DataFrame a un index datetime
        df = _utils.ensure_datetime_index(df)
        
        # Préparer les données
        X, y, feature_cols_raw = _utils.prepare_data_for_ml(df, target_column)
        feature_cols_generated = _utils.normalize_feature_columns(feature_cols_raw)
        
        # Valider la compatibilité
        is_compatible, missing_cols, extra_cols, warnings = _utils.validate_model_data_compatibility(
            feature_cols, feature_cols_generated, X
        )
        
        df = df.reindex(X.index)

        # S'assurer que current_df a un DatetimeIndex
        current_df = _utils.ensure_datetime_index(df.copy())
        
        # Calculer l'écart-type initial
        initial_std = np.std(current_df[target_column].diff().dropna())
        if np.isnan(initial_std) or initial_std == 0:
            initial_std = current_df[target_column].std() * 0.01 if current_df[target_column].std() > 0 else 1.0

        forecast_dates = []
        forecast_values = []
        lower_bounds = []
        upper_bounds = []

        interval_map = {
            'heure': pd.Timedelta(hours=1),
            'jour': pd.Timedelta(days=1),
            'semaine': pd.Timedelta(weeks=1),
            'mois': DateOffset(months=1)
        }
        time_offset = interval_map.get(forecast_interval, pd.Timedelta(days=1))

        for i in range(1, forecast_steps + 1):
            try:
                # Feature Engineering
                features_df = _utils.make_features(current_df, target_col=target_column)
                features_df = features_df.bfill().ffill().fillna(0)
                
                # Préparer les features pour la prédiction
                X_latest = _utils.prepare_features_for_prediction(
                    features_df, 
                    feature_cols, 
                    current_df=current_df,
                    target_column=target_column
                )
                
                if X_latest.empty or len(X_latest) == 0:
                    X_latest = pd.DataFrame([[0.0] * len(feature_cols)], columns=feature_cols)
                    predicted_diff = 0.0
                else:
                    try:
                        X_latest = X_latest[feature_cols].iloc[[-1]]
                        prediction = model.predict(X_latest)
                        predicted_diff = float(prediction[0])
                        if np.isnan(predicted_diff) or np.isinf(predicted_diff):
                            predicted_diff = 0.0
                    except Exception as e:
                        predicted_diff = 0.0

                # Calcul de l'intervalle de confiance amélioré
                recent_diff = current_df[target_column].diff().dropna()
                if len(recent_diff) > 0:
                    std_dev = np.std(recent_diff.iloc[-min(20, len(recent_diff)):])
                    if np.isnan(std_dev) or std_dev == 0:
                        std_dev = initial_std
                else:
                    std_dev = initial_std
                
                z_scores = {90: 1.645, 95: 1.96, 99: 2.576}
                z_score = z_scores.get(int(confidence_level), 1.96)
                margin_error = z_score * std_dev

                last_known_price = float(current_df[target_column].iloc[-1])
                new_price = last_known_price + predicted_diff
                
                if np.isnan(new_price) or np.isinf(new_price):
                    new_price = last_known_price

                # Génération de la nouvelle date
                if not isinstance(current_df.index, pd.DatetimeIndex):
                    current_df = _utils.ensure_datetime_index(current_df)
                
                last_date = current_df.index[-1]
                if isinstance(last_date, pd.Timestamp):
                    next_date = last_date + time_offset
                else:
                    next_date = pd.Timestamp.now() + pd.Timedelta(days=i)

                new_row_data = {target_column: new_price}
                for col in current_df.columns:
                    if col != target_column:
                        try:
                            last_val = current_df[col].iloc[-1]
                            if pd.api.types.is_numeric_dtype(current_df[col]):
                                new_row_data[col] = float(last_val) if not (np.isnan(last_val) or np.isinf(last_val)) else 0.0
                            else:
                                new_row_data[col] = last_val
                        except (KeyError, TypeError, ValueError, IndexError):
                            new_row_data[col] = 0.0

                new_row = pd.DataFrame([new_row_data], index=[next_date])
                
                try:
                    current_df = pd.concat([current_df, new_row], ignore_index=False)
                    if not isinstance(current_df.index, pd.DatetimeIndex):
                        current_df.index = pd.to_datetime(current_df.index, errors='coerce')
                except Exception:
                    current_df = _utils.ensure_datetime_index(current_df)
                    new_row.index = [next_date]
                    current_df = pd.concat([current_df, new_row], ignore_index=False)

                forecast_dates.append(next_date)
                forecast_values.append(float(new_price))
                lower_bounds.append(float(new_price - margin_error))
                upper_bounds.append(float(new_price + margin_error))
                
            except Exception as e:
                if i == 1:
                    raise ValueError(f"Échec de la première itération: {e}")
                
                if forecast_values:
                    last_value = forecast_values[-1]
                    last_date = forecast_dates[-1] if forecast_dates else current_df.index[-1]
                    if isinstance(last_date, pd.Timestamp):
                        next_date = last_date + time_offset
                    else:
                        next_date = pd.Timestamp.now() + pd.Timedelta(days=i)
                    
                    forecast_dates.append(next_date)
                    forecast_values.append(last_value)
                    lower_bounds.append(last_value * 0.95)
                    upper_bounds.append(last_value * 1.05)
                else:
                    last_price = float(current_df[target_column].iloc[-1])
                    next_date = current_df.index[-1] + time_offset if isinstance(current_df.index, pd.DatetimeIndex) else pd.Timestamp.now() + pd.Timedelta(days=i)
                    
                    forecast_dates.append(next_date)
                    forecast_values.append(last_price)
                    lower_bounds.append(last_price * 0.95)
                    upper_bounds.append(last_price * 1.05)

        if len(forecast_values) == 0:
            raise ValueError("Aucune prévision générée")

        # Validation et synchronisation des longueurs
        if not (len(forecast_dates) == len(forecast_values) == len(lower_bounds) == len(upper_bounds)):
            min_length = min(len(forecast_dates), len(forecast_values), len(lower_bounds), len(upper_bounds))
            forecast_dates = forecast_dates[:min_length]
            forecast_values = forecast_values[:min_length]
            lower_bounds = lower_bounds[:min_length]
            upper_bounds = upper_bounds[:min_length]

        forecast_dates_str = [d.strftime('%Y-%m-%d') if hasattr(d, 'strftime') else str(d) for d in forecast_dates]
        
        try:
            base_value = float(df[target_column].iloc[-1])
            forecast_float = [float(v) for v in forecast_values]
            # np.diff retourne n-1 éléments, calculer manuellement pour avoir n éléments
            diff_values = []
            prev_value = base_value
            for current_value in forecast_float:
                diff_values.append(current_value - prev_value)
                prev_value = current_value
        except Exception:
            diff_values = [0.0] * len(forecast_values)

        forecast_df = pd.DataFrame({
            'Date': forecast_dates_str,
            target_column: forecast_values,
            'lower_bound': lower_bounds,
            'upper_bound': upper_bounds,
            f'{target_column}_diff': diff_values
        }).set_index('Date')
        
        # Nettoyer les NaN et Inf pour éviter les erreurs JSON
        forecast_df = forecast_df.replace([np.inf, -np.inf], 0.0)
        forecast_df = forecast_df.fillna(0.0)

        historical_data = df.iloc[-min(50, len(df)):]
        metrics = calculate_forecast_metrics(historical_data, forecast_df, target_column)
        plot_b64 = generate_forecast_plot(historical_data, forecast_df, target_column, forecast_type)

        display_data = []
        for i, (date, row) in enumerate(forecast_df.iterrows(), 1):
            display_data.append({
                'Période': i,
                'Date': date.strftime('%Y-%m-%d') if hasattr(date, 'strftime') else str(date),
                'Prévision': round(row[target_column], 4),
                'Variation': round(row[f'{target_column}_diff'], 6),
                'Borne inf.': round(row['lower_bound'], 4),
                'Borne sup.': round(row['upper_bound'], 4)
            })

        result_payload = {
            'meta': {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'filename': os.path.basename(filepath),
                'model': os.path.basename(model_path),
            },
            'result': {
                'forecast_data': display_data,
                'metrics': metrics,
                'plot_b64': plot_b64
            }
        }

        _utils.write_job_result(jobid, result_payload)
    except Exception as e:
        _utils.write_job_error(jobid, str(e))


bp = Blueprint('previsions', __name__)


@bp.route('/', methods=['GET', 'POST'])
def index():
    """Page de prévisions utilisant des modèles de Machine Learning."""
    available_models = get_available_models()
    
    if request.method == 'GET':
        return render_template("previsions.html",
                             current_file=session.get('current_file'),
                             file_columns=session.get('file_columns', []),
                             file_dtypes=session.get('file_dtypes', {}),
                             available_models=available_models)

    # POST request - Exécution des prévisions
    is_ajax = request.form.get('ajax') == 'true'
    print(f"[DEBUG] POST request - is_ajax={is_ajax}, form keys={list(request.form.keys())}")
    
    current_file = request.form.get('filename') or session.get('current_file')
    print(f"[DEBUG] current_file={current_file}")

    if not current_file:
        if is_ajax:
            return jsonify({
                'success': False,
                'message': "Veuillez d'abord charger un fichier de données."
            }), 400
        return render_template("previsions.html",
                             current_file=None,
                             file_columns=session.get('file_columns', []),
                             file_dtypes=session.get('file_dtypes', {}),
                             available_models=available_models,
                             error="Veuillez d'abord charger un fichier de données.")

    try:
        # Récupération des paramètres
        forecast_steps = int(request.form.get('forecast_steps', 10))
        target_column = request.form.get('target_column', 'Close')
        selected_model_file = request.form.get('selected_model', next(iter(available_models.keys())) if available_models else '')
        forecast_type = request.form.get('forecast_type', 'close_price')
        forecast_interval = request.form.get('forecast_interval', 'jour')
        confidence_level = float(request.form.get('confidence_level', 95))
        
        if not selected_model_file:
            raise ValueError("Aucun modèle ML disponible. Veuillez placer des fichiers .joblib dans le dossier app/models/")
        
        # Mapping des intervalles de temps
        interval_map = {
            'heure': pd.Timedelta(hours=1),
            'jour': pd.Timedelta(days=1),
            'semaine': pd.Timedelta(weeks=1),
            'mois': DateOffset(months=1)
        }
        
        if forecast_interval not in interval_map:
            raise ValueError(f"Intervalle de prévision non supporté: {forecast_interval}")
            
        time_offset = interval_map[forecast_interval]

        # Chargement du modèle ML avec validation
        models_dir = current_app.config.get('MODELS_DIR')
        if not models_dir:
            models_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'models')
        model_path = os.path.join(models_dir, selected_model_file)
        
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Le modèle {selected_model_file} est introuvable.")
        
        # Charger et valider le modèle
        try:
            artifact = joblib.load(model_path)
            model, feature_cols, model_metadata = _utils.validate_model_artifact(artifact, model_path)
            current_app.logger.info(f"Modèle chargé: {selected_model_file}, {len(feature_cols)} features")
            if model_metadata.get('model_type'):
                current_app.logger.info(f"Type de modèle: {model_metadata['model_type']}")
        except ValueError as e:
            raise ValueError(f"Erreur de validation du modèle {selected_model_file}: {str(e)}")
        except Exception as e:
            raise ValueError(f"Erreur lors du chargement du modèle {selected_model_file}: {str(e)}")
        
        # Chargement des données
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], current_file)
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Le fichier de données {current_file} est introuvable.")

        # EXÉCUTION SYNCHRONE DES PRÉVISIONS
        df = _utils.load_dataframe(filepath)
        
        # CORRECTION 1: Aplatir les MultiIndex columns si présents
        if isinstance(df.columns, pd.MultiIndex):
            current_app.logger.info("MultiIndex columns détecté, aplatissement en cours...")
            df.columns = ['_'.join(str(c) for c in col).strip() if isinstance(col, tuple) else str(col) 
                         for col in df.columns.values]
            current_app.logger.info(f"Nouvelles colonnes après aplatissement: {list(df.columns)}")
        
        # CORRECTION 2: Forcer les noms de colonnes à être des strings simples
        df.columns = [str(col) for col in df.columns]
        current_app.logger.info(f"Colonnes disponibles: {list(df.columns)}")
        
        # CORRECTION 3: Vérifier et nettoyer le target_column
        if isinstance(target_column, tuple):
            target_column = '_'.join(str(c) for c in target_column).strip()
            current_app.logger.info(f"target_column converti en: {target_column}")
        
        # Vérifier que la colonne cible existe
        if target_column not in df.columns:
            possible_cols = [col for col in df.columns if target_column.lower() in col.lower() or col.lower() in target_column.lower()]
            if possible_cols:
                actual_target = possible_cols[0]
                current_app.logger.warning(f"Colonne '{target_column}' non trouvée. Utilisation de '{actual_target}' à la place.")
                target_column = actual_target
            else:
                raise ValueError(f"La colonne '{target_column}' n'existe pas dans le fichier. Colonnes disponibles: {list(df.columns)}")
        
        # S'assurer que le DataFrame a un index datetime
        df = _utils.ensure_datetime_index(df)
        
        # Préparation des données
        try:
            X, y, feature_cols_raw = _utils.prepare_data_for_ml(df, target_column)
        except Exception as e:
            current_app.logger.error(f"Erreur dans prepare_data_for_ml: {str(e)}")
            raise ValueError(f"Erreur lors de la préparation des données: {str(e)}")
        
        # Normaliser les feature columns générées
        feature_cols_generated = _utils.normalize_feature_columns(feature_cols_raw)
        
        # Valider la compatibilité entre le modèle et les données
        is_compatible, missing_cols, extra_cols, warnings = _utils.validate_model_data_compatibility(
            feature_cols, feature_cols_generated, X
        )
        
        if warnings:
            for warning in warnings:
                current_app.logger.warning(warning)
        
        if not is_compatible:
            current_app.logger.warning(f"Colonnes manquantes: {missing_cols[:10]}. Elles seront remplies avec des valeurs par défaut.")
        
        df = df.reindex(X.index)
        
        # Prédictions itératives avec intervalle de confiance
        # S'assurer que current_df a un DatetimeIndex
        current_df = _utils.ensure_datetime_index(df.copy())
        
        # Calculer l'écart-type initial pour l'intervalle de confiance
        initial_std = np.std(current_df[target_column].diff().dropna())
        if np.isnan(initial_std) or initial_std == 0:
            initial_std = current_df[target_column].std() * 0.01 if current_df[target_column].std() > 0 else 1.0
        
        forecast_dates = []
        forecast_values = []
        lower_bounds = []
        upper_bounds = []
        errors_encountered = []
        
        for i in range(1, forecast_steps + 1):
            try:
                # Feature Engineering
                features_df = _utils.make_features(current_df, target_col=target_column)
                
                # Remplir les NaN de manière intelligente
                features_df = features_df.bfill().ffill().fillna(0)
                
                # Préparer les features pour la prédiction avec validation
                X_latest = _utils.prepare_features_for_prediction(
                    features_df, 
                    feature_cols, 
                    current_df=current_df,
                    target_column=target_column
                )
                
                # S'assurer qu'on a au moins une ligne
                if X_latest.empty or len(X_latest) == 0:
                    current_app.logger.warning(f"X_latest vide à l'itération {i}, utilisation valeurs par défaut")
                    X_latest = pd.DataFrame([[0.0] * len(feature_cols)], columns=feature_cols)
                    predicted_diff = 0.0
                else:
                    # Prendre la dernière ligne et s'assurer que les colonnes sont dans le bon ordre
                    X_latest = X_latest[feature_cols].iloc[[-1]]
                    
                    # Prédiction
                    try:
                        prediction = model.predict(X_latest)
                        predicted_diff = float(prediction[0])
                        
                        # Valider que la prédiction est raisonnable
                        if np.isnan(predicted_diff) or np.isinf(predicted_diff):
                            current_app.logger.warning(f"Prédiction NaN/Inf à l'itération {i}, utilisation de 0.0")
                            predicted_diff = 0.0
                    except Exception as e:
                        current_app.logger.warning(f"Prédiction échouée à l'itération {i}: {e}")
                        predicted_diff = 0.0
                
                # Calcul de l'intervalle de confiance amélioré
                # Utiliser l'écart-type des différences récentes
                recent_diff = current_df[target_column].diff().dropna()
                if len(recent_diff) > 0:
                    std_dev = np.std(recent_diff.iloc[-min(20, len(recent_diff)):])
                    if np.isnan(std_dev) or std_dev == 0:
                        std_dev = initial_std
                else:
                    std_dev = initial_std
                
                # Calcul de la marge d'erreur avec z-score selon le niveau de confiance
                z_scores = {90: 1.645, 95: 1.96, 99: 2.576}
                z_score = z_scores.get(int(confidence_level), 1.96)
                margin_error = z_score * std_dev
                
                # Calcul du nouveau prix
                last_known_price = float(current_df[target_column].iloc[-1])
                new_price = last_known_price + predicted_diff
                
                # Valider que le nouveau prix est raisonnable
                if np.isnan(new_price) or np.isinf(new_price):
                    current_app.logger.warning(f"Prix calculé invalide à l'itération {i}, utilisation du dernier prix")
                    new_price = last_known_price
                
                # Génération de la nouvelle date - s'assurer que c'est un DatetimeIndex
                if not isinstance(current_df.index, pd.DatetimeIndex):
                    current_df = _utils.ensure_datetime_index(current_df)
                
                last_date = current_df.index[-1]
                if isinstance(last_date, pd.Timestamp):
                    next_date = last_date + time_offset
                else:
                    # Fallback: créer une date à partir de l'index
                    next_date = pd.Timestamp.now() + pd.Timedelta(days=i)
                
                # Création de la nouvelle ligne
                new_row_data = {target_column: new_price}
                for col in current_df.columns:
                    if col != target_column:
                        try:
                            last_val = current_df[col].iloc[-1]
                            # Utiliser la dernière valeur si numérique, sinon 0
                            if pd.api.types.is_numeric_dtype(current_df[col]):
                                new_row_data[col] = float(last_val) if not (np.isnan(last_val) or np.isinf(last_val)) else 0.0
                            else:
                                new_row_data[col] = last_val
                        except (KeyError, TypeError, ValueError, IndexError):
                            new_row_data[col] = 0.0
                
                # Créer la nouvelle ligne avec un DatetimeIndex
                new_row = pd.DataFrame([new_row_data], index=[next_date])
                
                # Concaténer en s'assurant que les index sont compatibles
                try:
                    current_df = pd.concat([current_df, new_row], ignore_index=False)
                    # S'assurer que l'index reste DatetimeIndex
                    if not isinstance(current_df.index, pd.DatetimeIndex):
                        current_df.index = pd.to_datetime(current_df.index, errors='coerce')
                except Exception as e:
                    current_app.logger.error(f"Erreur lors de la concaténation à l'itération {i}: {e}")
                    # Fallback: réindexer
                    current_df = _utils.ensure_datetime_index(current_df)
                    new_row.index = [next_date]
                    current_df = pd.concat([current_df, new_row], ignore_index=False)
                
                # Stockage des résultats - TOUJOURS exécuté de manière synchrone
                forecast_dates.append(next_date)
                forecast_values.append(float(new_price))
                lower_bounds.append(float(new_price - margin_error))
                upper_bounds.append(float(new_price + margin_error))
                
            except Exception as e:
                error_msg = f"Erreur à l'itération {i}: {str(e)}"
                current_app.logger.error(error_msg)
                errors_encountered.append(error_msg)
                
                # En cas d'erreur critique, arrêter si c'est la première itération
                if i == 1:
                    raise ValueError(f"Échec de la première itération de prévision: {e}")
                
                # Pour les itérations suivantes, utiliser la dernière valeur valide
                if forecast_values:
                    last_value = forecast_values[-1]
                    last_date = forecast_dates[-1] if forecast_dates else current_df.index[-1]
                    
                    # Calculer la prochaine date
                    if isinstance(last_date, pd.Timestamp):
                        next_date = last_date + time_offset
                    else:
                        next_date = pd.Timestamp.now() + pd.Timedelta(days=i)
                    
                    forecast_dates.append(next_date)
                    forecast_values.append(last_value)
                    lower_bounds.append(last_value * 0.95)
                    upper_bounds.append(last_value * 1.05)
                else:
                    # Si aucune valeur valide, utiliser le dernier prix connu
                    last_price = float(current_df[target_column].iloc[-1])
                    next_date = current_df.index[-1] + time_offset if isinstance(current_df.index, pd.DatetimeIndex) else pd.Timestamp.now() + pd.Timedelta(days=i)
                    
                    forecast_dates.append(next_date)
                    forecast_values.append(last_price)
                    lower_bounds.append(last_price * 0.95)
                    upper_bounds.append(last_price * 1.05)
        
        # Avertir si des erreurs ont été rencontrées
        if errors_encountered:
            current_app.logger.warning(f"{len(errors_encountered)} erreurs rencontrées pendant les prévisions")

        # Vérification qu'on a des prévisions
        if len(forecast_values) == 0:
            raise ValueError("Aucune prévision n'a pu être générée. Vérifiez vos données et votre modèle.")

        # Validation et synchronisation des longueurs AVANT conversion
        lengths = {
            'dates': len(forecast_dates),
            'values': len(forecast_values),
            'lower': len(lower_bounds),
            'upper': len(upper_bounds)
        }
        
        if not all(l == lengths['values'] for l in lengths.values()):
            current_app.logger.warning(f"Désynchronisation des arrays détectée: {lengths}")
            min_length = min(lengths.values())
            
            # Tronquer tous les arrays à la même longueur
            forecast_dates = forecast_dates[:min_length]
            forecast_values = forecast_values[:min_length]
            lower_bounds = lower_bounds[:min_length]
            upper_bounds = upper_bounds[:min_length]
            
            current_app.logger.info(f"Arrays synchronisés à la longueur {min_length}")

        # Validation des valeurs (pas de NaN, Inf)
        forecast_values = [float(v) if not (np.isnan(v) or np.isinf(v)) else 0.0 for v in forecast_values]
        lower_bounds = [float(v) if not (np.isnan(v) or np.isinf(v)) else 0.0 for v in lower_bounds]
        upper_bounds = [float(v) if not (np.isnan(v) or np.isinf(v)) else 0.0 for v in upper_bounds]

        # Conversion des dates en strings avec validation
        forecast_dates_str = []
        for d in forecast_dates:
            if isinstance(d, pd.Timestamp):
                forecast_dates_str.append(d.strftime('%Y-%m-%d'))
            elif hasattr(d, 'strftime'):
                forecast_dates_str.append(d.strftime('%Y-%m-%d'))
            else:
                # Fallback: utiliser la date actuelle + index
                forecast_dates_str.append((pd.Timestamp.now() + pd.Timedelta(days=len(forecast_dates_str))).strftime('%Y-%m-%d'))

        # Calcul des différences - calculer manuellement pour garantir n éléments
        try:
            base_value = float(df[target_column].iloc[-1])
            if np.isnan(base_value) or np.isinf(base_value):
                base_value = 0.0
            
            diff_values = []
            prev_value = base_value
            for current_value in forecast_values:
                diff = current_value - prev_value
                diff_values.append(diff if not (np.isnan(diff) or np.isinf(diff)) else 0.0)
                prev_value = current_value
        except Exception as e:
            current_app.logger.warning(f"Erreur lors du calcul des différences: {e}. Utilisation de zéros.")
            diff_values = [0.0] * len(forecast_values)

        # Validation finale des longueurs avant création du DataFrame
        final_lengths = {
            'dates': len(forecast_dates_str),
            'values': len(forecast_values),
            'lower': len(lower_bounds),
            'upper': len(upper_bounds),
            'diff': len(diff_values)
        }
        
        if not all(l == final_lengths['values'] for l in final_lengths.values()):
            current_app.logger.error(f"Erreur de synchronisation finale: {final_lengths}")
            min_length = min(final_lengths.values())
            forecast_dates_str = forecast_dates_str[:min_length]
            forecast_values = forecast_values[:min_length]
            lower_bounds = lower_bounds[:min_length]
            upper_bounds = upper_bounds[:min_length]
            diff_values = diff_values[:min_length]

        # Création du DataFrame de prévision
        forecast_df = pd.DataFrame({
            'Date': forecast_dates_str,
            target_column: forecast_values,
            'lower_bound': lower_bounds,
            'upper_bound': upper_bounds,
            f'{target_column}_diff': diff_values
        }).set_index('Date')
        
        # Nettoyer les NaN et Inf restants
        forecast_df = forecast_df.replace([np.inf, -np.inf], 0.0)
        forecast_df = forecast_df.fillna(0.0)
        
        # Calcul des métriques
        historical_data = df.iloc[-min(50, len(df)):]
        forecast_data = forecast_df
        metrics = calculate_forecast_metrics(historical_data, forecast_data, target_column)
        
        # Génération du graphique
        forecast_plot_b64 = generate_forecast_plot(historical_data, forecast_data, target_column, forecast_type)
        
        # Préparation des données pour l'affichage - avec nettoyage des NaN
        display_data = []
        for i, (date, row) in enumerate(forecast_df.iterrows(), 1):
            # Convertir et valider toutes les valeurs
            prevision_val = float(row[target_column])
            if np.isnan(prevision_val) or np.isinf(prevision_val):
                prevision_val = 0.0
            
            variation_val = float(row.get(f'{target_column}_diff', 0.0))
            if np.isnan(variation_val) or np.isinf(variation_val):
                variation_val = 0.0
            
            lower_val = float(row.get('lower_bound', 0.0))
            if np.isnan(lower_val) or np.isinf(lower_val):
                lower_val = 0.0
            
            upper_val = float(row.get('upper_bound', 0.0))
            if np.isnan(upper_val) or np.isinf(upper_val):
                upper_val = 0.0
            
            # Formater la date
            if isinstance(date, str):
                date_str = date
            elif hasattr(date, 'strftime'):
                date_str = date.strftime('%Y-%m-%d')
            else:
                date_str = str(date)
            
            display_data.append({
                'Période': i,
                'Date': date_str,
                'Prévision': round(prevision_val, 4),
                'Variation': round(variation_val, 6),
                'Borne inf.': round(lower_val, 4),
                'Borne sup.': round(upper_val, 4)
            })
        
        # Stockage en session
        forecast_result = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'filename': current_file,
            'model': selected_model_file,
            'target_column': target_column,
            'forecast_steps': forecast_steps,
            'forecast_interval': forecast_interval,
            'forecast_type': forecast_type,
            'confidence_level': confidence_level,
            'forecast_data': display_data,
            'metrics': metrics
        }
        session['last_forecast'] = forecast_result
        
        # Ajouter à l'historique
        _utils.add_to_forecast_history(forecast_result, session=session)
        
        # Génération du tableau HTML
        forecast_table_html = '<table class="min-w-full divide-y divide-gray-200"><thead class="bg-gray-100">'
        forecast_table_html += '<tr>'
        for col in ['Période', 'Date', 'Prévision', 'Variation', 'Borne inf.', 'Borne sup.']:
            forecast_table_html += f'<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{col}</th>'
        forecast_table_html += '</tr></thead><tbody class="bg-white divide-y divide-gray-200">'
        
        for row_data in display_data:
            forecast_table_html += '<tr>'
            for col in ['Période', 'Date', 'Prévision', 'Variation', 'Borne inf.', 'Borne sup.']:
                forecast_table_html += f'<td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{row_data[col]}</td>'
            forecast_table_html += '</tr>'
        
        forecast_table_html += '</tbody></table>'
        
        # Réponse AJAX ou HTML
        if is_ajax:
            print(f"[DEBUG] Returning JSON response for AJAX request")
            return jsonify({
                'success': True,
                'forecast_plot': forecast_plot_b64,
                'forecast_results': forecast_table_html,
                'forecast_data': display_data,
                'forecast_metrics': metrics
            })
        
        return render_template(
            "previsions.html",
            current_file=current_file,
            file_columns=session.get('file_columns', []),
            file_dtypes=session.get('file_dtypes', {}),
            available_models=available_models,
            forecast_plot=forecast_plot_b64,
            forecast_results=forecast_table_html,
            forecast_data=display_data,
            forecast_metrics=metrics,
            success=True
        )

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Erreur détaillée: {error_details}")
        
        if is_ajax:
            print(f"[DEBUG] Returning error JSON for AJAX request")
            return jsonify({
                'success': False,
                'message': f"Erreur lors de la prévision: {str(e)}"
            }), 500
        
        return render_template(
            "previsions.html",
            current_file=current_file,
            file_columns=session.get('file_columns', []),
            file_dtypes=session.get('file_dtypes', {}),
            available_models=available_models,
            forecast_results=None,
            forecast_plot=None,
            error=f"Erreur lors de la prévision: {str(e)}"
        )


@bp.route("/download_forecast")
def download_forecast():
    """Télécharge les résultats de prévision au format JSON."""
    if 'last_forecast' not in session:
        return "Aucune prévision récente à télécharger.", 404

    forecast_data = session['last_forecast']
    forecast_json = json.dumps(forecast_data, indent=4, ensure_ascii=False, default=str)
    
    buffer = BytesIO()
    buffer.write(forecast_json.encode('utf-8'))
    buffer.seek(0)
    
    filename = f"prevision_{forecast_data['timestamp'].replace(':', '-').replace(' ', '_')}.json"
    
    return send_file(buffer, as_attachment=True, download_name=filename, mimetype='application/json')


@bp.route("/history")
def forecast_history():
    """Affiche l'historique des prévisions de la session utilisateur."""
    history = _utils.get_forecast_history(session=session)
    return render_template("previsions_history.html", history=history, total_forecasts=len(history))


@bp.route("/download_forecast_history")
def download_forecast_history():
    """Télécharge l'historique complet des prévisions au format JSON."""
    history = _utils.get_forecast_history(session=session)
    
    if not history:
        return "Aucun historique de prévisions à télécharger.", 404
    
    history_json = json.dumps(history, indent=4, ensure_ascii=False, default=str)
    
    buffer = BytesIO()
    buffer.write(history_json.encode('utf-8'))
    buffer.seek(0)
    
    return send_file(buffer, as_attachment=True,
                    download_name=f'historique_previsions_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json',
                    mimetype='application/json')


@bp.route("/clear_forecast_history", methods=['POST'])
def clear_forecast_history_route():
    """Efface l'historique complet des prévisions de la session."""
    _utils.clear_forecast_history(session=session)
    session.pop('last_forecast', None)
    return redirect(url_for('previsions.forecast_history'))