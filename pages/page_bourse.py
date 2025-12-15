"""
Page des données boursières.
"""

import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta


def afficher():
    """Affiche la page des données boursières."""
    
    st.markdown("## 💹 Données boursières")
    
    st.markdown("""
    Visualisez les données boursières en temps réel et historiques.
    Les données sont fournies par Yahoo Finance.
    """)
    
    # Configuration
    st.markdown("### ⚙️ Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        symbole = st.text_input(
            "Symbole boursier",
            value="AAPL",
            help="Exemples : AAPL, GOOGL, MSFT, TSLA"
        ).upper()
    
    with col2:
        periode = st.selectbox(
            "Période",
            ["1j", "5j", "1mo", "3mo", "6mo", "1y", "2y", "5y", "max"],
            index=4,
            format_func=lambda x: {
                "1j": "1 jour",
                "5j": "5 jours",
                "1mo": "1 mois",
                "3mo": "3 mois",
                "6mo": "6 mois",
                "1y": "1 an",
                "2y": "2 ans",
                "5y": "5 ans",
                "max": "Maximum"
            }[x]
        )
    
    # Bouton de chargement
    if st.button("📊 Charger les données", type="primary"):
        charger_donnees_bourse(symbole, periode)


def charger_donnees_bourse(symbole, periode):
    """Charge et affiche les données boursières."""
    
    try:
        with st.spinner(f"Chargement des données pour {symbole}..."):
            # Télécharger les données
            ticker = yf.Ticker(symbole)
            df = ticker.history(period=periode)
            
            if df.empty:
                st.error(f"❌ Aucune donnée trouvée pour le symbole '{symbole}'")
                return
            
            # Informations sur l'entreprise
            st.markdown("### 🏢 Informations")
            
            try:
                info = ticker.info
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    nom = info.get('longName', symbole)
                    st.metric("Entreprise", nom)
                
                with col2:
                    secteur = info.get('sector', 'N/A')
                    st.metric("Secteur", secteur)
                
                with col3:
                    devise = info.get('currency', 'USD')
                    st.metric("Devise", devise)
                
                with col4:
                    prix_actuel = df['Close'].iloc[-1]
                    st.metric("Prix actuel", f"{prix_actuel:.2f}")
                
            except Exception:
                st.info(f"Symbole : {symbole}")
            
            # Graphique des prix
            st.markdown("### 📈 Évolution du prix")
            
            fig = go.Figure()
            
            # Chandelier (Candlestick)
            fig.add_trace(go.Candlestick(
                x=df.index,
                open=df['Open'],
                high=df['High'],
                low=df['Low'],
                close=df['Close'],
                name=symbole
            ))
            
            fig.update_layout(
                title=f"Prix de {symbole}",
                yaxis_title="Prix",
                xaxis_title="Date",
                xaxis_rangeslider_visible=False,
                hovermode='x unified'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Volume
            st.markdown("### 📊 Volume des transactions")
            
            fig_volume = go.Figure()
            
            fig_volume.add_trace(go.Bar(
                x=df.index,
                y=df['Volume'],
                name='Volume',
                marker_color='lightblue'
            ))
            
            fig_volume.update_layout(
                title=f"Volume de {symbole}",
                yaxis_title="Volume",
                xaxis_title="Date",
                hovermode='x unified'
            )
            
            st.plotly_chart(fig_volume, use_container_width=True)
            
            # Statistiques
            st.markdown("### 📊 Statistiques")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Prix max", f"{df['High'].max():.2f}")
            
            with col2:
                st.metric("Prix min", f"{df['Low'].min():.2f}")
            
            with col3:
                variation = ((df['Close'].iloc[-1] - df['Close'].iloc[0]) / df['Close'].iloc[0]) * 100
                st.metric("Variation", f"{variation:.2f}%")
            
            with col4:
                volume_moyen = df['Volume'].mean()
                st.metric("Volume moyen", f"{volume_moyen:,.0f}")
            
            # Tableau des données
            st.markdown("### 📋 Données brutes")
            
            # Inverser l'ordre pour afficher les plus récentes en premier
            df_affichage = df.sort_index(ascending=False).head(100)
            
            st.dataframe(df_affichage, use_container_width=True)
            
            # Téléchargement
            csv = df.to_csv().encode('utf-8')
            st.download_button(
                label="📥 Télécharger les données (CSV)",
                data=csv,
                file_name=f"{symbole}_{periode}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
            
    except Exception as e:
        st.error(f"❌ Erreur lors du chargement des données : {str(e)}")
        st.info("Vérifiez que le symbole boursier est correct et que vous avez une connexion Internet.")