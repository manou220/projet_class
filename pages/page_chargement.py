"""
Page de chargement de fichiers.
"""

import streamlit as st
import pandas as pd
from streamlit_utils import charger_fichier, sauvegarder_dans_session, afficher_statistiques_descriptives


def afficher():
    """Affiche la page de chargement de fichiers."""
    
    st.markdown("## 📤 Chargement de données")
    
    st.markdown("""
    Importez vos fichiers CSV ou Excel pour commencer l'analyse.
    Les formats supportés sont : **CSV**, **XLSX**, **XLS**
    """)
    
    # Zone de téléchargement
    st.markdown("### 📁 Sélectionner un fichier")
    
    fichier_telecharge = st.file_uploader(
        "Choisissez un fichier",
        type=['csv', 'xlsx', 'xls'],
        help="Taille maximale : 16 MB"
    )
    
    if fichier_telecharge is not None:
        # Charger le fichier
        with st.spinner("Chargement du fichier en cours..."):
            df = charger_fichier(fichier_telecharge)
        
        if df is not None:
            # Sauvegarder dans la session
            sauvegarder_dans_session(df, fichier_telecharge.name)
            
            st.success(f"✅ Fichier '{fichier_telecharge.name}' chargé avec succès !")
            
            # Afficher les informations du fichier
            st.markdown("### 📊 Informations du fichier")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Nombre de lignes", f"{len(df):,}")
            
            with col2:
                st.metric("Nombre de colonnes", len(df.columns))
            
            with col3:
                taille_mb = fichier_telecharge.size / (1024 * 1024)
                st.metric("Taille", f"{taille_mb:.2f} MB")
            
            # Types de colonnes
            st.markdown("### 📋 Types de colonnes")
            
            types_df = pd.DataFrame({
                'Colonne': df.columns,
                'Type': df.dtypes.astype(str),
                'Valeurs non-nulles': df.count().values,
                'Valeurs nulles': df.isnull().sum().values
            })
            
            st.dataframe(types_df, use_container_width=True)
            
            # Prévisualisation
            st.markdown("### 👀 Prévisualisation des données")
            
            nb_lignes = st.slider(
                "Nombre de lignes à afficher",
                min_value=5,
                max_value=min(100, len(df)),
                value=10,
                step=5
            )
            
            st.dataframe(df.head(nb_lignes), use_container_width=True)
            
            # Statistiques descriptives
            if st.checkbox("Afficher les statistiques descriptives", value=False):
                afficher_statistiques_descriptives(df)
            
            # Valeurs manquantes
            st.markdown("### 🔍 Analyse des valeurs manquantes")
            
            valeurs_manquantes = df.isnull().sum()
            colonnes_avec_manquantes = valeurs_manquantes[valeurs_manquantes > 0]
            
            if len(colonnes_avec_manquantes) > 0:
                st.warning(f"⚠️ {len(colonnes_avec_manquantes)} colonne(s) contiennent des valeurs manquantes")
                
                manquantes_df = pd.DataFrame({
                    'Colonne': colonnes_avec_manquantes.index,
                    'Valeurs manquantes': colonnes_avec_manquantes.values,
                    'Pourcentage': (colonnes_avec_manquantes.values / len(df) * 100).round(2)
                })
                
                st.dataframe(manquantes_df, use_container_width=True)
            else:
                st.success("✅ Aucune valeur manquante détectée")
            
            # Actions supplémentaires
            st.markdown("### ⚙️ Actions")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🗑️ Supprimer le fichier de la session", type="secondary"):
                    st.session_state['fichier_actuel'] = None
                    st.session_state['donnees_actuelles'] = None
                    st.session_state['colonnes_fichier'] = []
                    st.session_state['types_colonnes'] = {}
                    st.rerun()
            
            with col2:
                # Télécharger le fichier nettoyé (sans valeurs manquantes)
                if len(colonnes_avec_manquantes) > 0:
                    if st.button("📥 Télécharger sans valeurs manquantes"):
                        df_nettoye = df.dropna()
                        csv = df_nettoye.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label="💾 Télécharger CSV nettoyé",
                            data=csv,
                            file_name=f"nettoye_{fichier_telecharge.name}",
                            mime="text/csv"
                        )
    
    else:
        # Afficher un message si aucun fichier n'est chargé
        st.info("""
        👆 Utilisez le bouton ci-dessus pour charger un fichier.
        
        **Formats acceptés :**
        - CSV (avec différents encodages)
        - Excel (.xlsx, .xls)
        
        **Taille maximale :** 16 MB
        """)
        
        # Afficher le fichier actuel s'il existe
        if st.session_state.get('fichier_actuel'):
            st.markdown("---")
            st.markdown("### 📂 Fichier actuellement chargé")
            st.info(f"**{st.session_state['fichier_actuel']}** avec {len(st.session_state['colonnes_fichier'])} colonnes")
            
            if st.button("🔄 Recharger les informations"):
                st.rerun()