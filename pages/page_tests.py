"""
Page des tests statistiques.
"""

import streamlit as st
import pandas as pd
import numpy as np
from scipy import stats
from streamlit_utils import obtenir_colonnes_numeriques, obtenir_colonnes_categorielles, ajouter_a_historique, formater_nombre


def afficher():
    """Affiche la page des tests statistiques."""
    
    st.markdown("## 📊 Tests statistiques")
    
    # Vérifier qu'un fichier est chargé
    if not st.session_state.get('fichier_actuel') or st.session_state.get('donnees_actuelles') is None:
        st.warning("⚠️ Veuillez d'abord charger un fichier dans la page 'Charger des données'")
        return
    
    df = st.session_state['donnees_actuelles']
    
    st.success(f"✅ Fichier actuel : **{st.session_state['fichier_actuel']}**")
    
    # Sélection du type de test
    st.markdown("### 🔬 Sélectionner un test")
    
    type_test = st.selectbox(
        "Type de test statistique",
        [
            "Test de normalité (Shapiro-Wilk)",
            "Test de normalité (Kolmogorov-Smirnov)",
            "Test t de Student",
            "Test de corrélation de Pearson",
            "Test de corrélation de Spearman",
            "Test du Chi-2",
            "ANOVA (analyse de variance)",
            "Test de Mann-Whitney U"
        ]
    )
    
    st.markdown("---")
    
    # Tests de normalité
    if "normalité" in type_test:
        executer_test_normalite(df, type_test)
    
    # Test t
    elif "Test t" in type_test:
        executer_test_t(df)
    
    # Tests de corrélation
    elif "corrélation" in type_test:
        executer_test_correlation(df, type_test)
    
    # Test du Chi-2
    elif "Chi-2" in type_test:
        executer_test_chi2(df)
    
    # ANOVA
    elif "ANOVA" in type_test:
        executer_test_anova(df)
    
    # Test de Mann-Whitney
    elif "Mann-Whitney" in type_test:
        executer_test_mann_whitney(df)


def executer_test_normalite(df, type_test):
    """Exécute un test de normalité."""
    
    st.markdown("### 📈 Test de normalité")
    
    colonnes_num = obtenir_colonnes_numeriques(df)
    
    if not colonnes_num:
        st.error("❌ Aucune colonne numérique trouvée dans le fichier")
        return
    
    colonne = st.selectbox("Sélectionner une colonne", colonnes_num)
    
    if st.button("🚀 Exécuter le test", type="primary"):
        donnees = df[colonne].dropna()
        
        if len(donnees) < 3:
            st.error("❌ Pas assez de données (minimum 3 valeurs)")
            return
        
        # Exécuter le test
        if "Shapiro" in type_test:
            stat, p_value = stats.shapiro(donnees)
            nom_test = "Shapiro-Wilk"
        else:
            stat, p_value = stats.kstest(donnees, 'norm')
            nom_test = "Kolmogorov-Smirnov"
        
        # Interprétation
        alpha = 0.05
        if p_value > alpha:
            interpretation = f"Les données suivent une distribution normale (p={formater_nombre(p_value, 4)} > {alpha})"
            couleur = "success"
        else:
            interpretation = f"Les données ne suivent PAS une distribution normale (p={formater_nombre(p_value, 4)} < {alpha})"
            couleur = "error"
        
        # Afficher les résultats
        st.markdown("### 📊 Résultats")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Statistique", formater_nombre(stat, 4))
        with col2:
            st.metric("Valeur p", formater_nombre(p_value, 4))
        
        if couleur == "success":
            st.success(interpretation)
        else:
            st.error(interpretation)
        
        # Ajouter à l'historique
        ajouter_a_historique(
            nom_test=f"Test de normalité ({nom_test})",
            nom_fichier=st.session_state['fichier_actuel'],
            colonnes_utilisees=[colonne],
            p_value=p_value,
            stat_value=stat,
            interpretation=interpretation,
            resultats_complets={
                "statistique": float(stat),
                "p_value": float(p_value),
                "alpha": alpha,
                "nombre_observations": len(donnees)
            }
        )
        
        st.success("✅ Résultat ajouté à l'historique")


def executer_test_t(df):
    """Exécute un test t de Student."""
    
    st.markdown("### 📊 Test t de Student")
    
    colonnes_num = obtenir_colonnes_numeriques(df)
    
    if len(colonnes_num) < 2:
        st.error("❌ Au moins 2 colonnes numériques sont nécessaires")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        colonne1 = st.selectbox("Première colonne", colonnes_num, key="t_col1")
    
    with col2:
        colonne2 = st.selectbox("Deuxième colonne", [c for c in colonnes_num if c != colonne1], key="t_col2")
    
    if st.button("🚀 Exécuter le test", type="primary"):
        donnees1 = df[colonne1].dropna()
        donnees2 = df[colonne2].dropna()
        
        if len(donnees1) < 2 or len(donnees2) < 2:
            st.error("❌ Chaque colonne doit avoir au moins 2 valeurs")
            return
        
        # Test t
        stat, p_value = stats.ttest_ind(donnees1, donnees2)
        
        # Interprétation
        alpha = 0.05
        if p_value > alpha:
            interpretation = f"Pas de différence significative entre les moyennes (p={formater_nombre(p_value, 4)} > {alpha})"
            couleur = "info"
        else:
            interpretation = f"Différence significative entre les moyennes (p={formater_nombre(p_value, 4)} < {alpha})"
            couleur = "success"
        
        # Résultats
        st.markdown("### 📊 Résultats")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Statistique t", formater_nombre(stat, 4))
        with col2:
            st.metric("Valeur p", formater_nombre(p_value, 4))
        with col3:
            st.metric("Moyenne 1", formater_nombre(donnees1.mean(), 2))
        
        if couleur == "success":
            st.success(interpretation)
        else:
            st.info(interpretation)
        
        # Ajouter à l'historique
        ajouter_a_historique(
            nom_test="Test t de Student",
            nom_fichier=st.session_state['fichier_actuel'],
            colonnes_utilisees=[colonne1, colonne2],
            p_value=p_value,
            stat_value=stat,
            interpretation=interpretation,
            resultats_complets={
                "statistique_t": float(stat),
                "p_value": float(p_value),
                "moyenne_1": float(donnees1.mean()),
                "moyenne_2": float(donnees2.mean()),
                "ecart_type_1": float(donnees1.std()),
                "ecart_type_2": float(donnees2.std())
            }
        )
        
        st.success("✅ Résultat ajouté à l'historique")


def executer_test_correlation(df, type_test):
    """Exécute un test de corrélation."""
    
    st.markdown("### 📈 Test de corrélation")
    
    colonnes_num = obtenir_colonnes_numeriques(df)
    
    if len(colonnes_num) < 2:
        st.error("❌ Au moins 2 colonnes numériques sont nécessaires")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        colonne1 = st.selectbox("Première colonne", colonnes_num, key="corr_col1")
    
    with col2:
        colonne2 = st.selectbox("Deuxième colonne", [c for c in colonnes_num if c != colonne1], key="corr_col2")
    
    if st.button("🚀 Exécuter le test", type="primary"):
        donnees1 = df[colonne1].dropna()
        donnees2 = df[colonne2].dropna()
        
        # Aligner les données
        donnees_communes = df[[colonne1, colonne2]].dropna()
        
        if len(donnees_communes) < 3:
            st.error("❌ Pas assez de paires de données (minimum 3)")
            return
        
        # Test de corrélation
        if "Pearson" in type_test:
            coef, p_value = stats.pearsonr(donnees_communes[colonne1], donnees_communes[colonne2])
            nom_test = "Pearson"
        else:
            coef, p_value = stats.spearmanr(donnees_communes[colonne1], donnees_communes[colonne2])
            nom_test = "Spearman"
        
        # Interprétation
        alpha = 0.05
        if p_value > alpha:
            interpretation = f"Pas de corrélation significative (p={formater_nombre(p_value, 4)} > {alpha})"
            couleur = "info"
        else:
            force = "forte" if abs(coef) > 0.7 else "modérée" if abs(coef) > 0.4 else "faible"
            direction = "positive" if coef > 0 else "négative"
            interpretation = f"Corrélation {force} {direction} (r={formater_nombre(coef, 4)}, p={formater_nombre(p_value, 4)})"
            couleur = "success"
        
        # Résultats
        st.markdown("### 📊 Résultats")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Coefficient de corrélation", formater_nombre(coef, 4))
        with col2:
            st.metric("Valeur p", formater_nombre(p_value, 4))
        
        if couleur == "success":
            st.success(interpretation)
        else:
            st.info(interpretation)
        
        # Ajouter à l'historique
        ajouter_a_historique(
            nom_test=f"Corrélation de {nom_test}",
            nom_fichier=st.session_state['fichier_actuel'],
            colonnes_utilisees=[colonne1, colonne2],
            p_value=p_value,
            stat_value=coef,
            interpretation=interpretation,
            resultats_complets={
                "coefficient": float(coef),
                "p_value": float(p_value),
                "nombre_paires": len(donnees_communes)
            }
        )
        
        st.success("✅ Résultat ajouté à l'historique")


def executer_test_chi2(df):
    """Exécute un test du Chi-2."""
    
    st.markdown("### 📊 Test du Chi-2")
    st.info("Test d'indépendance entre deux variables catégorielles")
    
    colonnes_cat = obtenir_colonnes_categorielles(df)
    
    if len(colonnes_cat) < 2:
        st.error("❌ Au moins 2 colonnes catégorielles sont nécessaires")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        colonne1 = st.selectbox("Première variable", colonnes_cat, key="chi2_col1")
    
    with col2:
        colonne2 = st.selectbox("Deuxième variable", [c for c in colonnes_cat if c != colonne1], key="chi2_col2")
    
    if st.button("🚀 Exécuter le test", type="primary"):
        # Créer le tableau de contingence
        tableau_contingence = pd.crosstab(df[colonne1], df[colonne2])
        
        # Test du Chi-2
        chi2, p_value, dof, expected = stats.chi2_contingency(tableau_contingence)
        
        # Interprétation
        alpha = 0.05
        if p_value > alpha:
            interpretation = f"Les variables sont indépendantes (p={formater_nombre(p_value, 4)} > {alpha})"
            couleur = "info"
        else:
            interpretation = f"Les variables sont dépendantes (p={formater_nombre(p_value, 4)} < {alpha})"
            couleur = "success"
        
        # Résultats
        st.markdown("### 📊 Résultats")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Chi-2", formater_nombre(chi2, 4))
        with col2:
            st.metric("Valeur p", formater_nombre(p_value, 4))
        with col3:
            st.metric("Degrés de liberté", dof)
        
        if couleur == "success":
            st.success(interpretation)
        else:
            st.info(interpretation)
        
        # Afficher le tableau de contingence
        st.markdown("#### Tableau de contingence")
        st.dataframe(tableau_contingence, use_container_width=True)
        
        # Ajouter à l'historique
        ajouter_a_historique(
            nom_test="Test du Chi-2",
            nom_fichier=st.session_state['fichier_actuel'],
            colonnes_utilisees=[colonne1, colonne2],
            p_value=p_value,
            stat_value=chi2,
            interpretation=interpretation,
            resultats_complets={
                "chi2": float(chi2),
                "p_value": float(p_value),
                "degres_liberte": int(dof)
            }
        )
        
        st.success("✅ Résultat ajouté à l'historique")


def executer_test_anova(df):
    """Exécute une ANOVA."""
    
    st.markdown("### 📊 ANOVA (Analyse de variance)")
    st.info("Compare les moyennes de plusieurs groupes")
    
    colonnes_num = obtenir_colonnes_numeriques(df)
    colonnes_cat = obtenir_colonnes_categorielles(df)
    
    if not colonnes_num or not colonnes_cat:
        st.error("❌ Nécessite au moins une colonne numérique et une colonne catégorielle")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        colonne_valeur = st.selectbox("Variable numérique", colonnes_num)
    
    with col2:
        colonne_groupe = st.selectbox("Variable de groupement", colonnes_cat)
    
    if st.button("🚀 Exécuter le test", type="primary"):
        # Créer les groupes
        groupes = [df[df[colonne_groupe] == cat][colonne_valeur].dropna() 
                   for cat in df[colonne_groupe].unique()]
        
        # Filtrer les groupes vides
        groupes = [g for g in groupes if len(g) > 0]
        
        if len(groupes) < 2:
            st.error("❌ Au moins 2 groupes non-vides sont nécessaires")
            return
        
        # ANOVA
        stat, p_value = stats.f_oneway(*groupes)
        
        # Interprétation
        alpha = 0.05
        if p_value > alpha:
            interpretation = f"Pas de différence significative entre les groupes (p={formater_nombre(p_value, 4)} > {alpha})"
            couleur = "info"
        else:
            interpretation = f"Différence significative entre les groupes (p={formater_nombre(p_value, 4)} < {alpha})"
            couleur = "success"
        
        # Résultats
        st.markdown("### 📊 Résultats")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Statistique F", formater_nombre(stat, 4))
        with col2:
            st.metric("Valeur p", formater_nombre(p_value, 4))
        with col3:
            st.metric("Nombre de groupes", len(groupes))
        
        if couleur == "success":
            st.success(interpretation)
        else:
            st.info(interpretation)
        
        # Moyennes par groupe
        st.markdown("#### Moyennes par groupe")
        moyennes_df = df.groupby(colonne_groupe)[colonne_valeur].agg(['mean', 'std', 'count'])
        st.dataframe(moyennes_df, use_container_width=True)
        
        # Ajouter à l'historique
        ajouter_a_historique(
            nom_test="ANOVA",
            nom_fichier=st.session_state['fichier_actuel'],
            colonnes_utilisees=[colonne_valeur, colonne_groupe],
            p_value=p_value,
            stat_value=stat,
            interpretation=interpretation,
            resultats_complets={
                "statistique_f": float(stat),
                "p_value": float(p_value),
                "nombre_groupes": len(groupes)
            }
        )
        
        st.success("✅ Résultat ajouté à l'historique")


def executer_test_mann_whitney(df):
    """Exécute un test de Mann-Whitney U."""
    
    st.markdown("### 📊 Test de Mann-Whitney U")
    st.info("Alternative non-paramétrique au test t")
    
    colonnes_num = obtenir_colonnes_numeriques(df)
    
    if len(colonnes_num) < 2:
        st.error("❌ Au moins 2 colonnes numériques sont nécessaires")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        colonne1 = st.selectbox("Première colonne", colonnes_num, key="mw_col1")
    
    with col2:
        colonne2 = st.selectbox("Deuxième colonne", [c for c in colonnes_num if c != colonne1], key="mw_col2")
    
    if st.button("🚀 Exécuter le test", type="primary"):
        donnees1 = df[colonne1].dropna()
        donnees2 = df[colonne2].dropna()
        
        if len(donnees1) < 2 or len(donnees2) < 2:
            st.error("❌ Chaque colonne doit avoir au moins 2 valeurs")
            return
        
        # Test de Mann-Whitney
        stat, p_value = stats.mannwhitneyu(donnees1, donnees2, alternative='two-sided')
        
        # Interprétation
        alpha = 0.05
        if p_value > alpha:
            interpretation = f"Pas de différence significative entre les distributions (p={formater_nombre(p_value, 4)} > {alpha})"
            couleur = "info"
        else:
            interpretation = f"Différence significative entre les distributions (p={formater_nombre(p_value, 4)} < {alpha})"
            couleur = "success"
        
        # Résultats
        st.markdown("### 📊 Résultats")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Statistique U", formater_nombre(stat, 4))
        with col2:
            st.metric("Valeur p", formater_nombre(p_value, 4))
        
        if couleur == "success":
            st.success(interpretation)
        else:
            st.info(interpretation)
        
        # Ajouter à l'historique
        ajouter_a_historique(
            nom_test="Test de Mann-Whitney U",
            nom_fichier=st.session_state['fichier_actuel'],
            colonnes_utilisees=[colonne1, colonne2],
            p_value=p_value,
            stat_value=stat,
            interpretation=interpretation,
            resultats_complets={
                "statistique_u": float(stat),
                "p_value": float(p_value),
                "mediane_1": float(donnees1.median()),
                "mediane_2": float(donnees2.median())
            }
        )
        
        st.success("✅ Résultat ajouté à l'historique")