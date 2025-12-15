"""
Page de visualisation de données.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from streamlit_utils import obtenir_colonnes_numeriques, obtenir_colonnes_categorielles


def afficher():
    """Affiche la page de visualisation."""
    
    st.markdown("## 📈 Visualisation de données")
    
    # Vérifier qu'un fichier est chargé
    if not st.session_state.get('fichier_actuel') or st.session_state.get('donnees_actuelles') is None:
        st.warning("⚠️ Veuillez d'abord charger un fichier dans la page 'Charger des données'")
        return
    
    df = st.session_state['donnees_actuelles']
    
    st.success(f"✅ Fichier actuel : **{st.session_state['fichier_actuel']}**")
    
    # Sélection du type de graphique
    st.markdown("### 📊 Type de graphique")
    
    type_graphique = st.selectbox(
        "Sélectionner un type de graphique",
        [
            "Histogramme",
            "Boîte à moustaches (Box plot)",
            "Nuage de points (Scatter)",
            "Graphique en ligne",
            "Graphique en barres",
            "Matrice de corrélation",
            "Diagramme circulaire (Pie chart)",
            "Graphique de distribution"
        ]
    )
    
    st.markdown("---")
    
    # Afficher le graphique correspondant
    if type_graphique == "Histogramme":
        creer_histogramme(df)
    elif type_graphique == "Boîte à moustaches (Box plot)":
        creer_boxplot(df)
    elif type_graphique == "Nuage de points (Scatter)":
        creer_scatter(df)
    elif type_graphique == "Graphique en ligne":
        creer_ligne(df)
    elif type_graphique == "Graphique en barres":
        creer_barres(df)
    elif type_graphique == "Matrice de corrélation":
        creer_matrice_correlation(df)
    elif type_graphique == "Diagramme circulaire (Pie chart)":
        creer_pie_chart(df)
    elif type_graphique == "Graphique de distribution":
        creer_distribution(df)


def creer_histogramme(df):
    """Crée un histogramme."""
    
    st.markdown("### 📊 Histogramme")
    
    colonnes_num = obtenir_colonnes_numeriques(df)
    
    if not colonnes_num:
        st.error("❌ Aucune colonne numérique trouvée")
        return
    
    colonne = st.selectbox("Sélectionner une colonne", colonnes_num)
    
    col1, col2 = st.columns(2)
    with col1:
        nb_bins = st.slider("Nombre de barres", 5, 100, 30)
    with col2:
        couleur = st.color_picker("Couleur", "#1f77b4")
    
    # Créer le graphique
    fig = px.histogram(
        df,
        x=colonne,
        nbins=nb_bins,
        title=f"Distribution de {colonne}",
        labels={colonne: colonne, 'count': 'Fréquence'}
    )
    
    fig.update_traces(marker_color=couleur)
    fig.update_layout(showlegend=False)
    
    st.plotly_chart(fig, use_container_width=True)


def creer_boxplot(df):
    """Crée une boîte à moustaches."""
    
    st.markdown("### 📊 Boîte à moustaches")
    
    colonnes_num = obtenir_colonnes_numeriques(df)
    
    if not colonnes_num:
        st.error("❌ Aucune colonne numérique trouvée")
        return
    
    colonne = st.selectbox("Sélectionner une colonne", colonnes_num)
    
    # Option de groupement
    colonnes_cat = obtenir_colonnes_categorielles(df)
    groupe = None
    
    if colonnes_cat:
        utiliser_groupe = st.checkbox("Grouper par une variable catégorielle")
        if utiliser_groupe:
            groupe = st.selectbox("Variable de groupement", colonnes_cat)
    
    # Créer le graphique
    if groupe:
        fig = px.box(
            df,
            x=groupe,
            y=colonne,
            title=f"Distribution de {colonne} par {groupe}",
            color=groupe
        )
    else:
        fig = px.box(
            df,
            y=colonne,
            title=f"Distribution de {colonne}"
        )
    
    st.plotly_chart(fig, use_container_width=True)


def creer_scatter(df):
    """Crée un nuage de points."""
    
    st.markdown("### 📊 Nuage de points")
    
    colonnes_num = obtenir_colonnes_numeriques(df)
    
    if len(colonnes_num) < 2:
        st.error("❌ Au moins 2 colonnes numériques sont nécessaires")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        x_col = st.selectbox("Axe X", colonnes_num)
    
    with col2:
        y_col = st.selectbox("Axe Y", [c for c in colonnes_num if c != x_col])
    
    # Options supplémentaires
    colonnes_cat = obtenir_colonnes_categorielles(df)
    couleur_col = None
    taille_col = None
    
    if colonnes_cat:
        utiliser_couleur = st.checkbox("Colorer par une variable")
        if utiliser_couleur:
            couleur_col = st.selectbox("Variable de couleur", colonnes_cat + colonnes_num)
    
    if len(colonnes_num) > 2:
        utiliser_taille = st.checkbox("Taille variable")
        if utiliser_taille:
            taille_col = st.selectbox("Variable de taille", [c for c in colonnes_num if c not in [x_col, y_col]])
    
    # Créer le graphique
    fig = px.scatter(
        df,
        x=x_col,
        y=y_col,
        color=couleur_col,
        size=taille_col,
        title=f"{y_col} vs {x_col}",
        trendline="ols" if st.checkbox("Ajouter une ligne de tendance") else None
    )
    
    st.plotly_chart(fig, use_container_width=True)


def creer_ligne(df):
    """Crée un graphique en ligne."""
    
    st.markdown("### 📊 Graphique en ligne")
    
    colonnes_num = obtenir_colonnes_numeriques(df)
    
    if not colonnes_num:
        st.error("❌ Aucune colonne numérique trouvée")
        return
    
    # Sélection des colonnes
    y_cols = st.multiselect("Sélectionner les colonnes à afficher", colonnes_num)
    
    if not y_cols:
        st.warning("⚠️ Sélectionnez au moins une colonne")
        return
    
    # Index ou colonne X
    utiliser_colonne_x = st.checkbox("Utiliser une colonne pour l'axe X")
    x_col = None
    
    if utiliser_colonne_x:
        x_col = st.selectbox("Colonne X", df.columns.tolist())
    
    # Créer le graphique
    if x_col:
        fig = px.line(
            df,
            x=x_col,
            y=y_cols,
            title="Évolution temporelle"
        )
    else:
        fig = go.Figure()
        for col in y_cols:
            fig.add_trace(go.Scatter(
                y=df[col],
                mode='lines',
                name=col
            ))
        fig.update_layout(title="Évolution temporelle", xaxis_title="Index", yaxis_title="Valeur")
    
    st.plotly_chart(fig, use_container_width=True)


def creer_barres(df):
    """Crée un graphique en barres."""
    
    st.markdown("### 📊 Graphique en barres")
    
    colonnes_cat = obtenir_colonnes_categorielles(df)
    colonnes_num = obtenir_colonnes_numeriques(df)
    
    if not colonnes_cat:
        st.error("❌ Aucune colonne catégorielle trouvée")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        x_col = st.selectbox("Catégorie (X)", colonnes_cat)
    
    with col2:
        if colonnes_num:
            y_col = st.selectbox("Valeur (Y)", colonnes_num)
            aggregation = st.selectbox("Agrégation", ["sum", "mean", "count", "median"])
        else:
            y_col = None
            aggregation = "count"
    
    # Créer le graphique
    if y_col:
        if aggregation == "count":
            donnees_agg = df.groupby(x_col)[y_col].count().reset_index()
        elif aggregation == "sum":
            donnees_agg = df.groupby(x_col)[y_col].sum().reset_index()
        elif aggregation == "mean":
            donnees_agg = df.groupby(x_col)[y_col].mean().reset_index()
        else:
            donnees_agg = df.groupby(x_col)[y_col].median().reset_index()
        
        fig = px.bar(
            donnees_agg,
            x=x_col,
            y=y_col,
            title=f"{aggregation.capitalize()} de {y_col} par {x_col}"
        )
    else:
        donnees_agg = df[x_col].value_counts().reset_index()
        donnees_agg.columns = [x_col, 'count']
        fig = px.bar(
            donnees_agg,
            x=x_col,
            y='count',
            title=f"Distribution de {x_col}"
        )
    
    st.plotly_chart(fig, use_container_width=True)


def creer_matrice_correlation(df):
    """Crée une matrice de corrélation."""
    
    st.markdown("### 📊 Matrice de corrélation")
    
    colonnes_num = obtenir_colonnes_numeriques(df)
    
    if len(colonnes_num) < 2:
        st.error("❌ Au moins 2 colonnes numériques sont nécessaires")
        return
    
    # Sélection des colonnes
    colonnes_selectionnees = st.multiselect(
        "Sélectionner les colonnes (vide = toutes)",
        colonnes_num,
        default=colonnes_num[:min(10, len(colonnes_num))]
    )
    
    if not colonnes_selectionnees:
        colonnes_selectionnees = colonnes_num
    
    # Calculer la corrélation
    correlation = df[colonnes_selectionnees].corr()
    
    # Créer la heatmap
    fig = px.imshow(
        correlation,
        text_auto='.2f',
        aspect="auto",
        color_continuous_scale='RdBu_r',
        title="Matrice de corrélation"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Afficher les corrélations les plus fortes
    st.markdown("#### Corrélations les plus fortes")
    
    # Extraire les corrélations
    correlations_liste = []
    for i in range(len(correlation.columns)):
        for j in range(i+1, len(correlation.columns)):
            correlations_liste.append({
                'Variable 1': correlation.columns[i],
                'Variable 2': correlation.columns[j],
                'Corrélation': correlation.iloc[i, j]
            })
    
    if correlations_liste:
        corr_df = pd.DataFrame(correlations_liste)
        corr_df = corr_df.sort_values('Corrélation', key=abs, ascending=False).head(10)
        st.dataframe(corr_df, use_container_width=True)


def creer_pie_chart(df):
    """Crée un diagramme circulaire."""
    
    st.markdown("### 📊 Diagramme circulaire")
    
    colonnes_cat = obtenir_colonnes_categorielles(df)
    
    if not colonnes_cat:
        st.error("❌ Aucune colonne catégorielle trouvée")
        return
    
    colonne = st.selectbox("Sélectionner une colonne", colonnes_cat)
    
    # Limiter le nombre de catégories
    max_categories = st.slider("Nombre maximum de catégories", 3, 20, 10)
    
    # Compter les valeurs
    valeurs = df[colonne].value_counts().head(max_categories)
    
    # Créer le graphique
    fig = px.pie(
        values=valeurs.values,
        names=valeurs.index,
        title=f"Distribution de {colonne}"
    )
    
    st.plotly_chart(fig, use_container_width=True)


def creer_distribution(df):
    """Crée un graphique de distribution."""
    
    st.markdown("### 📊 Graphique de distribution")
    
    colonnes_num = obtenir_colonnes_numeriques(df)
    
    if not colonnes_num:
        st.error("❌ Aucune colonne numérique trouvée")
        return
    
    colonne = st.selectbox("Sélectionner une colonne", colonnes_num)
    
    # Options
    afficher_rug = st.checkbox("Afficher les points individuels (rug plot)")
    afficher_kde = st.checkbox("Afficher la courbe de densité (KDE)", value=True)
    
    # Créer le graphique
    fig = go.Figure()
    
    # Histogramme
    fig.add_trace(go.Histogram(
        x=df[colonne],
        name='Histogramme',
        opacity=0.7
    ))
    
    # KDE
    if afficher_kde:
        from scipy import stats
        donnees = df[colonne].dropna()
        kde = stats.gaussian_kde(donnees)
        x_range = pd.Series(pd.np.linspace(donnees.min(), donnees.max(), 100))
        fig.add_trace(go.Scatter(
            x=x_range,
            y=kde(x_range) * len(donnees) * (donnees.max() - donnees.min()) / 30,
            mode='lines',
            name='Densité (KDE)',
            line=dict(color='red', width=2)
        ))
    
    fig.update_layout(
        title=f"Distribution de {colonne}",
        xaxis_title=colonne,
        yaxis_title='Fréquence',
        showlegend=True
    )
    
    st.plotly_chart(fig, use_container_width=True)