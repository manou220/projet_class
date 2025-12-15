# 📊 Application d'Analyse de Données et Machine Learning

Application web interactive développée avec **Streamlit** pour l'analyse statistique de données et les prévisions avec Machine Learning.

## 🚀 Fonctionnalités

### 📤 Chargement de données
- Import de fichiers CSV et Excel (max 16 MB)
- Support multi-encodage (UTF-8, Latin-1, ISO-8859-1)
- Prévisualisation et validation automatique
- Détection des valeurs manquantes
- Statistiques descriptives

### 📊 Tests statistiques
- **Tests de normalité** : Shapiro-Wilk, Kolmogorov-Smirnov
- **Tests de comparaison** : Test t de Student, Mann-Whitney U
- **Tests de corrélation** : Pearson, Spearman
- **Tests d'indépendance** : Chi-2
- **Analyse de variance** : ANOVA
- Sauvegarde automatique dans l'historique

### 📈 Visualisation interactive
- Histogrammes et distributions
- Boîtes à moustaches (Box plots)
- Nuages de points avec ligne de tendance
- Graphiques en ligne et en barres
- Matrice de corrélation
- Diagrammes circulaires
- Graphiques personnalisables (couleurs, tailles)

### 🔮 Prévisions ML
- Chargement de modèles pré-entraînés (.joblib)
- Génération de prévisions avec intervalles de confiance
- Visualisation des tendances
- Export des résultats en CSV

### 💹 Données boursières
- Intégration Yahoo Finance
- Graphiques chandelier (Candlestick)
- Volume de transactions
- Statistiques financières en temps réel
- Historique personnalisable (1j à max)

### 📜 Historique
- Sauvegarde de tous les tests effectués
- Filtrage par type de test et fichier
- Export CSV complet
- Résultats détaillés avec interprétation

## 📋 Prérequis

- **Python 3.10+** (testé avec Python 3.13)
- **pip** (gestionnaire de paquets Python)
- **Connexion Internet** (pour données boursières)

## 🔧 Installation

### 1. Cloner le repository

```bash
git clone <votre-repository>
cd Projet-ML-Sea3
```

### 2. Installer les dépendances

```bash
pip install -r requirements_streamlit.txt
```

**Note** : Si vous rencontrez des erreurs d'installation, utilisez :

```bash
python -m pip install -r requirements_streamlit.txt --user
```

### 3. Vérifier l'installation

```bash
python -c "import streamlit, scipy, pandas, numpy, plotly; print('✓ Installation réussie')"
```

## 🎯 Utilisation

### Lancement local

```bash
streamlit run streamlit_app.py
```

L'application sera accessible à : **http://localhost:8501**

### Navigation

1. **Page d'accueil** : Vue d'ensemble et guide de démarrage
2. **Charger des données** : Importer vos fichiers CSV/Excel
3. **Tests statistiques** : Effectuer des analyses statistiques
4. **Visualisation** : Créer des graphiques interactifs
5. **Prévisions ML** : Utiliser des modèles de Machine Learning
6. **Données boursières** : Consulter les cours en temps réel
7. **Historique** : Consulter et exporter vos résultats

## 📁 Structure du projet

```
Projet-ML-Sea3/
├── streamlit_app.py              # Point d'entrée principal
├── streamlit_utils.py             # Fonctions utilitaires
├── pages/                         # Pages de l'application
│   ├── __init__.py
│   ├── page_accueil.py           # Page d'accueil
│   ├── page_chargement.py        # Chargement de fichiers
│   ├── page_tests.py             # Tests statistiques
│   ├── page_visualisation.py     # Visualisations
│   ├── page_previsions.py        # Prévisions ML
│   ├── page_bourse.py            # Données boursières
│   └── page_historique.py        # Historique des tests
├── .streamlit/
│   └── config.toml               # Configuration Streamlit
├── app/
│   └── models/                   # Modèles ML (.joblib)
├── uploads/                      # Fichiers uploadés (temporaire)
├── requirements_streamlit.txt    # Dépendances Python
└── README.md                     # Ce fichier

```

## 🎨 Exemples d'utilisation

### 1. Analyser un fichier CSV

```python
# 1. Aller sur "Charger des données"
# 2. Sélectionner votre fichier CSV
# 3. Visualiser l'aperçu et les statistiques
```

### 2. Effectuer un test de normalité

```python
# 1. Charger vos données
# 2. Aller sur "Tests statistiques"
# 3. Sélectionner "Test de normalité (Shapiro-Wilk)"
# 4. Choisir la colonne à tester
# 5. Cliquer sur "Exécuter le test"
```

### 3. Créer une visualisation

```python
# 1. Charger vos données
# 2. Aller sur "Visualisation"
# 3. Sélectionner le type de graphique
# 4. Configurer les paramètres
# 5. Le graphique s'affiche automatiquement
```

### 4. Consulter des données boursières

```python
# 1. Aller sur "Données boursières"
# 2. Entrer un symbole (ex: AAPL, GOOGL, MSFT)
# 3. Choisir la période
# 4. Cliquer sur "Charger les données"
```

## 🔒 Sécurité et confidentialité

- ✅ Validation des types de fichiers
- ✅ Limite de taille : 16 MB par fichier
- ✅ Protection XSRF activée
- ✅ Données stockées uniquement en session (non persistantes)
- ⚠️ **Important** : Les données sont effacées à la fermeture du navigateur

## 🚀 Déploiement sur Streamlit Cloud

### Étapes

1. **Créer un compte** sur [Streamlit Cloud](https://share.streamlit.io)

2. **Connecter votre repository GitHub**

3. **Configurer le déploiement** :
   - Repository : Sélectionner votre repo
   - Branch : main (ou master)
   - Main file : `streamlit_app.py`

4. **Déployer** : Cliquer sur "Deploy!"

5. **Accéder à votre app** : URL fournie par Streamlit Cloud

### Variables d'environnement (optionnel)

Si vous utilisez des API keys, ajoutez-les dans les secrets :

```toml
# Dans Streamlit Cloud > Settings > Secrets
ALPHAVANTAGE_KEY = "votre_clé"
IEX_CLOUD_API_KEY = "votre_clé"
```

## 🛠️ Développement

### Ajouter une nouvelle page

1. Créer `pages/page_nouvelle.py` :

```python
import streamlit as st

def afficher():
    st.markdown("## Ma nouvelle page")
    # Votre code ici
```

2. Importer dans `pages/__init__.py` :

```python
from . import page_nouvelle
```

3. Ajouter dans `streamlit_app.py` :

```python
pages = {
    # ...
    "🆕 Nouvelle page": "nouvelle",
}

# Dans la section d'affichage
elif page_nom == "nouvelle":
    from pages import page_nouvelle
    page_nouvelle.afficher()
```

### Personnaliser le thème

Modifier `.streamlit/config.toml` :

```toml
[theme]
primaryColor = "#1f77b4"  # Couleur principale
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
```

## 📊 Formats supportés

### Fichiers de données
- **CSV** : UTF-8, Latin-1, ISO-8859-1, CP1252
- **Excel** : .xlsx, .xls

### Modèles ML
- **Format** : .joblib (scikit-learn)
- **Emplacement** : `app/models/`

## 🐛 Résolution de problèmes

### ModuleNotFoundError: No module named 'scipy'

```bash
python -m pip install scipy --user
```

### Erreur d'encodage CSV

L'application teste automatiquement plusieurs encodages. Si le problème persiste, convertissez votre fichier en UTF-8.

### Port déjà utilisé

```bash
streamlit run streamlit_app.py --server.port 8503
```

### Fichier trop volumineux

Modifier `.streamlit/config.toml` :

```toml
[server]
maxUploadSize = 50  # En MB
```

### L'application ne démarre pas

1. Vérifier que toutes les dépendances sont installées :
```bash
pip install -r requirements_streamlit.txt
```

2. Vérifier la version de Python :
```bash
python --version  # Doit être 3.10+
```

3. Nettoyer le cache :
```bash
streamlit cache clear
```

## 📦 Dépendances

```
streamlit==1.40.2      # Framework web
pandas==2.3.3          # Manipulation de données
numpy==2.3.5           # Calculs numériques
scipy==1.16.3          # Tests statistiques
plotly==6.3.1          # Visualisations interactives
yfinance==0.2.66       # Données boursières
openpyxl==3.1.5        # Lecture Excel
joblib==1.5.2          # Chargement de modèles
scikit-learn==1.8.0    # Machine Learning
matplotlib==3.10.8     # Graphiques
```

## 🤝 Contribution

Les contributions sont les bienvenues ! Pour contribuer :

1. Fork le projet
2. Créer une branche (`git checkout -b feature/amelioration`)
3. Commit vos changements (`git commit -m 'Ajout d'une fonctionnalité'`)
4. Push vers la branche (`git push origin feature/amelioration`)
5. Ouvrir une Pull Request

## 📝 Notes importantes

- Les données sont stockées **uniquement en session**
- Pensez à **télécharger vos résultats** importants
- L'historique est **effacé à la fermeture** du navigateur
- Les modèles ML doivent être au format **.joblib**
- Les fichiers uploadés sont **temporaires**

## 📞 Support

Pour toute question ou problème :

1. Consulter ce README
2. Vérifier les [Issues GitHub](https://github.com/votre-repo/issues)
3. Ouvrir une nouvelle issue si nécessaire

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## 🎓 Crédits

Développé avec ❤️ en utilisant :
- [Streamlit](https://streamlit.io) - Framework web
- [Plotly](https://plotly.com) - Visualisations
- [Yahoo Finance](https://finance.yahoo.com) - Données boursières
- [scikit-learn](https://scikit-learn.org) - Machine Learning

---

**Version** : 2.0 - Streamlit  
**Dernière mise à jour** : Décembre 2025