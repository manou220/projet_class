"""
Application Streamlit pour l'analyse de données et prévisions ML.

Cette application permet de :
- Charger des fichiers CSV/Excel
- Effectuer des tests statistiques
- Visualiser des données
- Faire des prévisions avec des modèles ML
- Visualiser des données boursières
"""

import streamlit as st
import os
import sys

# Configuration de la page
st.set_page_config(
    page_title="Analyse de Données & ML",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Ajouter le répertoire du projet au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import des utilitaires
try:
    from streamlit_utils import initialiser_session, appliquer_style_css
    
    # Initialiser la session
    initialiser_session()
    
    # Appliquer le style CSS
    appliquer_style_css()
except Exception as e:
    st.error(f"Erreur lors de l'initialisation : {str(e)}")
    st.stop()

# Titre principal
st.title("📊 Plateforme d'Analyse de Données et Machine Learning")

# Sidebar avec navigation
st.sidebar.title("Navigation")
st.sidebar.markdown("---")

# Pages disponibles
pages = {
    "🏠 Accueil": "accueil",
    "📤 Charger des données": "chargement",
    "📊 Tests statistiques": "tests",
    "📈 Visualisation": "visualisation",
    "🔮 Prévisions ML": "previsions",
    "💹 Données boursières": "bourse",
    "📜 Historique": "historique"
}

# Sélection de la page
page_selectionnee = st.sidebar.radio(
    "Sélectionnez une page :",
    list(pages.keys()),
    key="navigation"
)

# Afficher les informations de session dans la sidebar
st.sidebar.markdown("---")
st.sidebar.subheader("📁 Fichier actuel")
if st.session_state.get('fichier_actuel'):
    st.sidebar.success(f"✅ {st.session_state['fichier_actuel']}")
    if st.session_state.get('colonnes_fichier'):
        st.sidebar.info(f"📊 {len(st.session_state['colonnes_fichier'])} colonnes")
else:
    st.sidebar.warning("Aucun fichier chargé")

# Afficher la page sélectionnée
page_nom = pages[page_selectionnee]

try:
    if page_nom == "accueil":
        from pages import page_accueil
        page_accueil.afficher()
    elif page_nom == "chargement":
        from pages import page_chargement
        page_chargement.afficher()
    elif page_nom == "tests":
        from pages import page_tests
        page_tests.afficher()
    elif page_nom == "visualisation":
        from pages import page_visualisation
        page_visualisation.afficher()
    elif page_nom == "previsions":
        from pages import page_previsions
        page_previsions.afficher()
    elif page_nom == "bourse":
        from pages import page_bourse
        page_bourse.afficher()
    elif page_nom == "historique":
        from pages import page_historique
        page_historique.afficher()
except Exception as e:
    st.error(f"❌ Erreur lors du chargement de la page : {str(e)}")
    st.info("💡 Vérifiez que toutes les dépendances sont installées : `pip install -r requirements_streamlit.txt`")
    if st.checkbox("Afficher les détails de l'erreur"):
        st.exception(e)

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("### À propos")
st.sidebar.info(
    "Application d'analyse de données avec ML\n\n"
    "Version 2.0 - Streamlit"
)