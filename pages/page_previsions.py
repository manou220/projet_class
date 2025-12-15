"""
Page des prévisions avec modèles ML.
"""

import streamlit as st
import pandas as pd
import numpy as np
import os
import joblib
from datetime import datetime, timedelta
import plotly.graph_objects as go
from streamlit_utils import obtenir_colonnes_numeriques


def afficher():
    """Affiche la page des prévisions ML."""
    
    st.markdown("## 🔮 Prévisions avec Machine Learning")
    
    # Vérifier qu'un fichier est chargé
    if not st.session_state.get('fichier_actuel') or st.session_state.get('donnees_actuelles') is None:
        st.warning("⚠️ Veuillez d'abord charger un fichier dans la page 'Charger des données'")
        return
    
    df = st.session_state['donnees_actuelles']
    
    st.success(f"✅ Fichier actuel : **{st.session_state['fichier_actuel']}**")
    
    # Charger les modèles disponibles
    modeles_disponibles = charger_modeles_disponibles()
    
    if not modeles_disponibles:
        st.info("""
        ℹ️ Aucun modèle ML trouvé dans le dossier `app/models/`.
        
        Pour utiliser cette fonctionnalité :
        1. Entraînez vos modèles
        2. Sauvegardez-les au format `.joblib` dans `app/models/`
        """)
        return
    
    # Sélection du modèle
    st.markdown("### 🤖 Sélection du modèle")
    
    modele_selectionne = st.selectbox(
        "Modèle à utiliser",
        list(modeles_disponibles.keys()),
        format_func=lambda x: modeles_disponibles[x]
    )
    
    # Charger le modèle
    chemin_modele = os.path.join(st.session_state['dossier_modeles'], modele_selectionne)
    
    try:
        modele = joblib.load(chemin_modele)
        st.success(f"✅ Modèle '{modeles_disponibles[modele_selectionne]}' chargé")
    except Exception as e:
        st.error(f"❌ Erreur lors du chargement du modèle : {str(e)}")
        return
    
    st.markdown("---")
    
    # Configuration des prévisions
    st.markdown("### ⚙️ Configuration des prévisions")
    
    colonnes_num = obtenir_colonnes_numeriques(df)
    
    if not colonnes_num:
        st.error("❌ Aucune colonne numérique trouvée")
        return
    
    # Sélection de la colonne cible
    colonne_cible = st.selectbox(
        "Colonne à prédire",
        colonnes_num
    )
    
    # Nombre de prévisions
    nb_previsions = st.slider(
        "Nombre de prévisions à générer",
        min_value=1,
        max_value=100,
        value=10,
        step=1
    )
    
    # Bouton de prévision
    if st.button("🚀 Générer les prévisions", type="primary"):
        generer_previsions(df, modele, colonne_cible, nb_previsions)


def charger_modeles_disponibles():
    """Charge la liste des modèles ML disponibles."""
    
    dossier_modeles = st.session_state.get('dossier_modeles')
    
    if not os.path.exists(dossier_modeles):
        return {}
    
    modeles = {}
    
    for fichier in os.listdir(dossier_modeles):
        if fichier.endswith('.joblib'):
            nom_affichage = fichier.replace('.joblib', '').replace('_', ' ').title()
            modeles[fichier] = nom_affichage
    
    return modeles


def generer_previsions(df, modele, colonne_cible, nb_previsions):
    """Génère les prévisions avec le modèle."""
    
    st.markdown("### 📊 Résultats des prévisions")
    
    try:
        # Préparer les données
        donnees_historiques = df[colonne_cible].dropna()
        
        if len(donnees_historiques) == 0:
            st.error("❌ Aucune donnée disponible pour cette colonne")
            return
        
        # Générer les prévisions (simulation simple)
        # Note: Adapter selon le type de modèle réel
        derniere_valeur = donnees_historiques.iloc[-1]
        tendance = donnees_historiques.diff().mean()
        
        previsions = []
        for i in range(nb_previsions):
            # Prévision simple avec tendance + bruit
            prevision = derniere_valeur + tendance * (i + 1) + np.random.normal(0, donnees_historiques.std() * 0.1)
            previsions.append(prevision)
        
        # Créer un DataFrame de résultats
        index_historique = list(range(len(donnees_historiques)))
        index_previsions = list(range(len(donnees_historiques), len(donnees_historiques) + nb_previsions))
        
        # Graphique
        fig = go.Figure()
        
        # Données historiques
        fig.add_trace(go.Scatter(
            x=index_historique,
            y=donnees_historiques.values,
            mode='lines',
            name='Données historiques',
            line=dict(color='blue', width=2)
        ))
        
        # Prévisions
        fig.add_trace(go.Scatter(
            x=index_previsions,
            y=previsions,
            mode='lines+markers',
            name='Prévisions',
            line=dict(color='red', width=2, dash='dash'),
            marker=dict(size=8)
        ))
        
        # Intervalle de confiance (simulation)
        std_prevision = donnees_historiques.std() * 0.2
        intervalle_sup = [p + 1.96 * std_prevision for p in previsions]
        intervalle_inf = [p - 1.96 * std_prevision for p in previsions]
        
        fig.add_trace(go.Scatter(
            x=index_previsions + index_previsions[::-1],
            y=intervalle_sup + intervalle_inf[::-1],
            fill='toself',
            fillcolor='rgba(255,0,0,0.2)',
            line=dict(color='rgba(255,255,255,0)'),
            name='Intervalle de confiance 95%',
            showlegend=True
        ))
        
        fig.update_layout(
            title=f"Prévisions pour {colonne_cible}",
            xaxis_title="Index",
            yaxis_title=colonne_cible,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Tableau des prévisions
        st.markdown("#### 📋 Tableau des prévisions")
        
        previsions_df = pd.DataFrame({
            'Index': index_previsions,
            'Prévision': previsions,
            'Borne inférieure': intervalle_inf,
            'Borne supérieure': intervalle_sup
        })
        
        st.dataframe(previsions_df, use_container_width=True)
        
        # Métriques
        st.markdown("#### 📈 Métriques")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Moyenne historique", f"{donnees_historiques.mean():.2f}")
        
        with col2:
            st.metric("Moyenne prévisions", f"{np.mean(previsions):.2f}")
        
        with col3:
            variation = ((np.mean(previsions) - donnees_historiques.mean()) / donnees_historiques.mean()) * 100
            st.metric("Variation", f"{variation:.2f}%")
        
        # Téléchargement
        csv = previsions_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Télécharger les prévisions (CSV)",
            data=csv,
            file_name=f"previsions_{colonne_cible}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
        
    except Exception as e:
        st.error(f"❌ Erreur lors de la génération des prévisions : {str(e)}")
        st.exception(e)