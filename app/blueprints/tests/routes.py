"""
Blueprint pour l'exécution des tests statistiques.
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import statsmodels.api as sm
from scipy import stats
from scipy.stats import kruskal, mannwhitneyu, kstest, shapiro
from flask import Blueprint, render_template, request, session, current_app, jsonify
from app.utils import (
    allowed_file, load_dataframe, validate_test_requirements, 
    generate_plot_image, add_to_history
)
import os

bp = Blueprint('tests', __name__)


@bp.route('/')
def index():
    """Page des tests statistiques."""
    return render_template('tests.html',
                           current_file=session.get('current_file'),
                           file_columns=session.get('file_columns', []),
                           file_dtypes=session.get('file_dtypes', {}))


@bp.route('/run_test', methods=['POST'])
def run_test():
    """Exécute le test statistique sélectionné."""
    test_type = request.form.get('test_type')
    selected_columns = request.form.getlist('selected_columns')
    filename = request.form.get('filename') or session.get('current_file')

    if not all([test_type, selected_columns, filename]):
        return render_template('resultats.html', 
                             error="Paramètres manquants pour l'exécution du test.")

    # Validation des exigences
    is_valid, error_msg = validate_test_requirements(test_type, selected_columns)
    if not is_valid:
        return render_template('resultats.html', error=error_msg)

    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)

    try:
        df = load_dataframe(filepath)
        data = df[selected_columns].apply(pd.to_numeric, errors='coerce').dropna()

        if data.empty:
            return render_template('resultats.html', 
                                 error="Les colonnes sélectionnées ne contiennent pas de données numériques valides.")

        # Exécution du test
        test_functions = {
            'wilcoxon': lambda: stats.wilcoxon(data[selected_columns[0]], data[selected_columns[1]]),
            'mannwhitney': lambda: mannwhitneyu(data[selected_columns[0]], data[selected_columns[1]]),
            'kruskal': lambda: kruskal(*[data[col].values for col in selected_columns]),
            'spearman': lambda: stats.spearmanr(data[selected_columns[0]], data[selected_columns[1]]),
            'friedman': lambda: stats.friedmanchisquare(*[data[col].values for col in selected_columns]),
            'kolmogorov_smirnov': lambda: kstest(data[selected_columns[0]], 'norm', 
                                                 args=(data[selected_columns[0]].mean(), 
                                                       data[selected_columns[0]].std())),
            'shapiro_wilk': lambda: shapiro(data[selected_columns[0]])
        }

        if test_type not in test_functions:
            return render_template('resultats.html', error="Test statistique non reconnu.")

        stat_value, p_value = test_functions[test_type]()
        
        # Interprétation
        if test_type in ['kolmogorov_smirnov', 'shapiro_wilk']:
            interpretation = "Distribution NON normale" if p_value < 0.05 else "Distribution compatible avec la normalité"
        elif test_type == 'spearman':
            interpretation = f"Corrélation {'significative' if p_value < 0.05 else 'non significative'} (rho={stat_value:.4f})"
        else:
            interpretation = "Différence significative détectée" if p_value < 0.05 else "Aucune différence significative"

        # Génération des graphiques pour une colonne
        histogram_base64 = qqplot_base64 = None
        if len(selected_columns) == 1:
            col_data = data[selected_columns[0]]
            
            # Histogramme
            plt.figure(figsize=(8, 6))
            col_data.hist(bins=30, edgecolor='black', alpha=0.7, color='steelblue')
            plt.title(f'Distribution de {selected_columns[0]}')
            plt.xlabel('Valeurs')
            plt.ylabel('Fréquence')
            plt.grid(True, alpha=0.3)
            histogram_base64 = generate_plot_image()

            # QQ Plot
            fig, ax = plt.subplots(figsize=(8, 6))
            sm.qqplot(col_data, line='s', ax=ax)
            ax.set_title(f'QQ Plot de {selected_columns[0]}')
            ax.grid(True, alpha=0.3)
            qqplot_base64 = generate_plot_image()

        # Mise à jour de l'historique
        current_result_data = {
            'test_name': test_type,
            'filename': filename,
            'columns_used': selected_columns,
            'p_value': p_value,
            'stat_value': stat_value,
            'interpretation': interpretation
        }
        
        add_to_history(
            **current_result_data,
            full_results={'statistic': stat_value, 'p_value': p_value},
            session=session
        )
        session['last_result'] = current_result_data

        # Formatage des résultats
        results_text = f"""
Test : {test_type.upper()}
Fichier : {filename}
Colonnes : {', '.join(selected_columns)}
Statistique : {stat_value:.6f}
P-value : {p_value:.6f}

Interprétation : {interpretation}
"""

        return render_template(
            'resultats.html',
            test_name=test_type,
            column=', '.join(selected_columns),
            results_text=results_text,
            interpretation=interpretation,
            histogram=histogram_base64,
            qqplot=qqplot_base64,
            can_download=True
        )

    except Exception as e:
        return render_template('resultats.html', error=f"Erreur lors de l'exécution du test: {str(e)}")
