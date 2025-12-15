"""
Page d'accueil de l'application.
"""

import streamlit as st


def afficher():
    """Affiche la page d'accueil."""
    
    # En-tête
    st.markdown("## 🏠 Bienvenue sur la plateforme d'analyse de données")
    
    st.markdown("""
    Cette application vous permet d'effectuer des analyses statistiques avancées 
    et des prévisions avec des modèles de Machine Learning.
    """)
    
    # Fonctionnalités principales
    st.markdown("### ✨ Fonctionnalités principales")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        #### 📤 Chargement de données
        - Import de fichiers CSV et Excel
        - Validation automatique
        - Prévisualisation des données
        """)
    
    with col2:
        st.markdown("""
        #### 📊 Tests statistiques
        - Tests de normalité
        - Tests de corrélation
        - Tests d'hypothèses
        - ANOVA et régression
        """)
    
    with col3:
        st.markdown("""
        #### 🔮 Prévisions ML
        - Modèles pré-entraînés
        - Prévisions temporelles
        - Visualisation des résultats
        """)
    
    st.markdown("---")
    
    # Guide de démarrage
    st.markdown("### 🚀 Guide de démarrage rapide")
    
    with st.expander("📖 Comment utiliser cette application ?", expanded=True):
        st.markdown("""
        1. **Charger vos données** : Utilisez la page "Charger des données" pour importer un fichier CSV ou Excel
        2. **Analyser** : Accédez à la page "Tests statistiques" pour effectuer des analyses
        3. **Visualiser** : Créez des graphiques dans la page "Visualisation"
        4. **Prévoir** : Utilisez les modèles ML dans la page "Prévisions ML"
        5. **Consulter l'historique** : Retrouvez tous vos tests dans la page "Historique"
        """)
    
    # Informations sur les données supportées
    st.markdown("### 📁 Formats de données supportés")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("""
        **Fichiers CSV**
        - Encodage : UTF-8, Latin-1, ISO-8859-1
        - Séparateur : virgule, point-virgule
        - Taille max : 16 MB
        """)
    
    with col2:
        st.info("""
        **Fichiers Excel**
        - Formats : .xlsx, .xls
        - Première feuille utilisée
        - Taille max : 16 MB
        """)
    
    st.markdown("---")
    
    # Statistiques de session
    st.markdown("### 📈 Statistiques de la session")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        fichier_charge = "✅ Oui" if st.session_state.get('fichier_actuel') else "❌ Non"
        st.metric("Fichier chargé", fichier_charge)
    
    with col2:
        nb_tests = len(st.session_state.get('historique_tests', []))
        st.metric("Tests effectués", nb_tests)
    
    with col3:
        nb_colonnes = len(st.session_state.get('colonnes_fichier', []))
        st.metric("Colonnes disponibles", nb_colonnes)
    
    # Conseils
    st.markdown("---")
    st.markdown("### 💡 Conseils")
    
    st.success("""
    **Astuce** : Commencez par charger vos données, puis explorez les différentes 
    fonctionnalités d'analyse. Tous vos résultats sont sauvegardés dans l'historique !
    """)
    
    st.warning("""
    **Note** : Les données sont stockées uniquement pendant votre session. 
    Pensez à télécharger vos résultats importants.
    """)