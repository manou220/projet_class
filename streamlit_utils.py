"""
Utilitaires pour l'application Streamlit.
"""

import streamlit as st
import os
import pandas as pd
import numpy as np
from datetime import datetime


def initialiser_session():
    """Initialise les variables de session si elles n'existent pas."""
    
    # Fichier actuel
    if 'fichier_actuel' not in st.session_state:
        st.session_state['fichier_actuel'] = None
    
    if 'donnees_actuelles' not in st.session_state:
        st.session_state['donnees_actuelles'] = None
    
    if 'colonnes_fichier' not in st.session_state:
        st.session_state['colonnes_fichier'] = []
    
    if 'types_colonnes' not in st.session_state:
        st.session_state['types_colonnes'] = {}
    
    # Historique des tests
    if 'historique_tests' not in st.session_state:
        st.session_state['historique_tests'] = []
    
    # Résultats des tests
    if 'resultats_tests' not in st.session_state:
        st.session_state['resultats_tests'] = {}
    
    # Modèles ML
    if 'modeles_disponibles' not in st.session_state:
        st.session_state['modeles_disponibles'] = {}
    
    # Dossiers
    if 'dossier_uploads' not in st.session_state:
        dossier = os.path.join(os.getcwd(), 'uploads')
        os.makedirs(dossier, exist_ok=True)
        st.session_state['dossier_uploads'] = dossier
    
    if 'dossier_modeles' not in st.session_state:
        dossier = os.path.join(os.getcwd(), 'app', 'models')
        os.makedirs(dossier, exist_ok=True)
        st.session_state['dossier_modeles'] = dossier


def appliquer_style_css():
    """Applique un style CSS personnalisé à l'application."""
    st.markdown("""
        <style>
        /* Style général */
        .main {
            padding: 2rem;
        }
        
        /* Titres */
        h1 {
            color: #1f77b4;
            font-weight: 600;
        }
        
        h2 {
            color: #2c3e50;
            font-weight: 500;
            margin-top: 2rem;
        }
        
        h3 {
            color: #34495e;
            font-weight: 500;
        }
        
        /* Boutons */
        .stButton>button {
            border-radius: 5px;
            font-weight: 500;
        }
        
        /* Cartes */
        .element-container {
            margin-bottom: 1rem;
        }
        
        /* Sidebar */
        .css-1d391kg {
            background-color: #f8f9fa;
        }
        
        /* Messages */
        .stAlert {
            border-radius: 5px;
        }
        
        /* Dataframes */
        .dataframe {
            font-size: 0.9rem;
        }
        
        /* Métriques */
        [data-testid="stMetricValue"] {
            font-size: 2rem;
            font-weight: 600;
        }
        </style>
    """, unsafe_allow_html=True)


def charger_fichier(fichier_telecharge):
    """
    Charge un fichier CSV ou Excel dans un DataFrame.
    
    Args:
        fichier_telecharge: Fichier uploadé via st.file_uploader
        
    Returns:
        pd.DataFrame ou None si erreur
    """
    try:
        # Déterminer le type de fichier
        nom_fichier = fichier_telecharge.name
        
        if nom_fichier.endswith('.csv'):
            # Essayer différents encodages
            encodages = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
            df = None
            
            for encodage in encodages:
                try:
                    fichier_telecharge.seek(0)
                    df = pd.read_csv(fichier_telecharge, encoding=encodage)
                    if not df.empty:
                        break
                except UnicodeDecodeError:
                    continue
                except Exception:
                    raise
            
            if df is None or df.empty:
                fichier_telecharge.seek(0)
                df = pd.read_csv(fichier_telecharge, encoding='utf-8', errors='ignore')
                
        elif nom_fichier.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(fichier_telecharge, engine='openpyxl')
        else:
            st.error("Format de fichier non supporté. Utilisez CSV ou Excel.")
            return None
        
        return df
        
    except pd.errors.EmptyDataError:
        st.error("Le fichier est vide.")
        return None
    except Exception as e:
        st.error(f"Erreur lors du chargement du fichier : {str(e)}")
        return None


def sauvegarder_dans_session(df, nom_fichier):
    """
    Sauvegarde les données du DataFrame dans la session.
    
    Args:
        df: DataFrame pandas
        nom_fichier: Nom du fichier
    """
    st.session_state['fichier_actuel'] = nom_fichier
    st.session_state['donnees_actuelles'] = df
    st.session_state['colonnes_fichier'] = df.columns.tolist()
    st.session_state['types_colonnes'] = df.dtypes.apply(lambda x: x.name).to_dict()


def ajouter_a_historique(nom_test, nom_fichier, colonnes_utilisees, p_value, 
                         stat_value, interpretation, resultats_complets):
    """
    Ajoute un résultat de test à l'historique.
    
    Args:
        nom_test: Nom du test statistique
        nom_fichier: Nom du fichier analysé
        colonnes_utilisees: Liste des colonnes utilisées
        p_value: Valeur p du test
        stat_value: Valeur de la statistique
        interpretation: Interprétation du résultat
        resultats_complets: Dictionnaire avec tous les résultats
    """
    nouvelle_entree = {
        "id": len(st.session_state['historique_tests']) + 1,
        "nom_test": nom_test,
        "nom_fichier": nom_fichier,
        "colonnes_utilisees": colonnes_utilisees if isinstance(colonnes_utilisees, list) else [colonnes_utilisees],
        "p_value": float(p_value) if p_value is not None else None,
        "stat_value": float(stat_value) if stat_value is not None else None,
        "interpretation": interpretation,
        "resultats_complets": resultats_complets,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    st.session_state['historique_tests'].append(nouvelle_entree)


def obtenir_colonnes_numeriques(df):
    """
    Retourne la liste des colonnes numériques d'un DataFrame.
    
    Args:
        df: DataFrame pandas
        
    Returns:
        Liste des noms de colonnes numériques
    """
    return df.select_dtypes(include=[np.number]).columns.tolist()


def obtenir_colonnes_categorielles(df):
    """
    Retourne la liste des colonnes catégorielles d'un DataFrame.
    
    Args:
        df: DataFrame pandas
        
    Returns:
        Liste des noms de colonnes catégorielles
    """
    return df.select_dtypes(include=['object', 'category']).columns.tolist()


def formater_nombre(nombre, decimales=2):
    """
    Formate un nombre avec un nombre de décimales spécifié.
    
    Args:
        nombre: Nombre à formater
        decimales: Nombre de décimales
        
    Returns:
        Chaîne formatée
    """
    if nombre is None or (isinstance(nombre, float) and (np.isnan(nombre) or np.isinf(nombre))):
        return "N/A"
    
    try:
        return f"{float(nombre):.{decimales}f}"
    except (ValueError, TypeError):
        return str(nombre)


def afficher_statistiques_descriptives(df, colonnes=None):
    """
    Affiche les statistiques descriptives d'un DataFrame.
    
    Args:
        df: DataFrame pandas
        colonnes: Liste de colonnes à analyser (None = toutes)
    """
    if colonnes is None:
        colonnes = df.columns.tolist()
    
    st.subheader("📊 Statistiques descriptives")
    
    # Statistiques pour colonnes numériques
    colonnes_num = [col for col in colonnes if col in obtenir_colonnes_numeriques(df)]
    if colonnes_num:
        st.write("**Colonnes numériques :**")
        st.dataframe(df[colonnes_num].describe(), use_container_width=True)
    
    # Informations pour colonnes catégorielles
    colonnes_cat = [col for col in colonnes if col in obtenir_colonnes_categorielles(df)]
    if colonnes_cat:
        st.write("**Colonnes catégorielles :**")
        for col in colonnes_cat:
            with st.expander(f"📋 {col}"):
                valeurs_uniques = df[col].nunique()
                st.metric("Valeurs uniques", valeurs_uniques)
                if valeurs_uniques <= 20:
                    st.write("**Distribution :**")
                    st.dataframe(
                        df[col].value_counts().reset_index()
                        .rename(columns={'index': col, col: 'Nombre'}),
                        use_container_width=True
                    )