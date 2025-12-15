"""
Page de l'historique des tests.
"""

import streamlit as st
import pandas as pd
from datetime import datetime


def afficher():
    """Affiche la page de l'historique."""
    
    st.markdown("## 📜 Historique des tests")
    
    historique = st.session_state.get('historique_tests', [])
    
    if not historique:
        st.info("""
        ℹ️ Aucun test effectué pour le moment.
        
        Effectuez des tests statistiques dans la page "Tests statistiques" 
        pour voir l'historique ici.
        """)
        return
    
    st.success(f"✅ {len(historique)} test(s) dans l'historique")
    
    # Options de filtrage
    st.markdown("### 🔍 Filtres")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Filtre par type de test
        types_tests = list(set([t['nom_test'] for t in historique]))
        filtre_type = st.multiselect(
            "Type de test",
            types_tests,
            default=types_tests
        )
    
    with col2:
        # Filtre par fichier
        fichiers = list(set([t['nom_fichier'] for t in historique]))
        filtre_fichier = st.multiselect(
            "Fichier",
            fichiers,
            default=fichiers
        )
    
    # Appliquer les filtres
    historique_filtre = [
        t for t in historique
        if t['nom_test'] in filtre_type and t['nom_fichier'] in filtre_fichier
    ]
    
    if not historique_filtre:
        st.warning("⚠️ Aucun test ne correspond aux filtres sélectionnés")
        return
    
    st.markdown("---")
    
    # Affichage de l'historique
    st.markdown("### 📊 Liste des tests")
    
    # Inverser pour afficher les plus récents en premier
    for i, test in enumerate(reversed(historique_filtre)):
        with st.expander(
            f"#{len(historique_filtre) - i} - {test['nom_test']} - {test['timestamp']}",
            expanded=(i == 0)
        ):
            # Informations générales
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"**Fichier :** {test['nom_fichier']}")
                st.markdown(f"**Date :** {test['timestamp']}")
            
            with col2:
                colonnes = test['colonnes_utilisees']
                if isinstance(colonnes, list):
                    colonnes_str = ", ".join(colonnes)
                else:
                    colonnes_str = str(colonnes)
                st.markdown(f"**Colonnes :** {colonnes_str}")
            
            # Résultats
            st.markdown("#### Résultats")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if test.get('stat_value') is not None:
                    st.metric("Statistique", f"{test['stat_value']:.4f}")
            
            with col2:
                if test.get('p_value') is not None:
                    st.metric("Valeur p", f"{test['p_value']:.4f}")
            
            # Interprétation
            st.markdown("#### Interprétation")
            st.info(test['interpretation'])
            
            # Résultats complets
            if test.get('resultats_complets'):
                with st.expander("📋 Résultats détaillés"):
                    st.json(test['resultats_complets'])
    
    st.markdown("---")
    
    # Actions
    st.markdown("### ⚙️ Actions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Exporter l'historique
        if st.button("📥 Exporter l'historique (CSV)"):
            exporter_historique(historique_filtre)
    
    with col2:
        # Effacer l'historique
        if st.button("🗑️ Effacer l'historique", type="secondary"):
            if st.session_state.get('confirmer_effacement'):
                st.session_state['historique_tests'] = []
                st.session_state['confirmer_effacement'] = False
                st.success("✅ Historique effacé")
                st.rerun()
            else:
                st.session_state['confirmer_effacement'] = True
                st.warning("⚠️ Cliquez à nouveau pour confirmer")


def exporter_historique(historique):
    """Exporte l'historique au format CSV."""
    
    # Préparer les données
    donnees_export = []
    
    for test in historique:
        donnees_export.append({
            'ID': test['id'],
            'Type de test': test['nom_test'],
            'Fichier': test['nom_fichier'],
            'Colonnes': ', '.join(test['colonnes_utilisees']) if isinstance(test['colonnes_utilisees'], list) else test['colonnes_utilisees'],
            'Statistique': test.get('stat_value'),
            'Valeur p': test.get('p_value'),
            'Interprétation': test['interpretation'],
            'Date': test['timestamp']
        })
    
    df = pd.DataFrame(donnees_export)
    csv = df.to_csv(index=False).encode('utf-8')
    
    st.download_button(
        label="💾 Télécharger CSV",
        data=csv,
        file_name=f"historique_tests_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )