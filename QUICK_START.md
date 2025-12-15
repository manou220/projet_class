# 🚀 Démarrage Rapide - Déploiement Streamlit

## ✅ Checklist avant déploiement

- [x] Fichier `streamlit_app.py` créé
- [x] Fichier `requirements_streamlit.txt` créé
- [x] Dossier `.streamlit/` avec `config.toml` créé
- [x] Toutes les pages dans le dossier `pages/` fonctionnent
- [x] Guide de déploiement créé (`DEPLOYMENT.md`)

## 📝 Étapes rapides

### 1. Tester localement

```bash
# Installer les dépendances
pip install -r requirements_streamlit.txt

# Lancer l'application
streamlit run streamlit_app.py
```

### 2. Préparer pour GitHub

```bash
# Vérifier que tous les fichiers sont ajoutés
git status

# Ajouter les nouveaux fichiers
git add streamlit_app.py
git add streamlit_utils.py
git add requirements_streamlit.txt
git add .streamlit/
git add pages/
git add DEPLOYMENT.md

# Commiter
git commit -m "Préparation pour déploiement Streamlit Cloud"

# Pousser vers GitHub
git push origin main
```

### 3. Déployer sur Streamlit Cloud

1. Allez sur [share.streamlit.io](https://share.streamlit.io)
2. Connectez-vous avec GitHub
3. Cliquez sur "New app"
4. Sélectionnez votre repository
5. Branch: `main`
6. Main file: `streamlit_app.py`
7. Cliquez sur "Deploy!"

## 🔍 Vérifications

### Fichiers requis

- ✅ `streamlit_app.py` - Point d'entrée principal
- ✅ `streamlit_utils.py` - Utilitaires
- ✅ `requirements_streamlit.txt` - Dépendances
- ✅ `.streamlit/config.toml` - Configuration
- ✅ `pages/` - Toutes les pages

### Structure des dossiers

```
Projet-ML-SEA3/
├── streamlit_app.py
├── streamlit_utils.py
├── requirements_streamlit.txt
├── .streamlit/
│   ├── config.toml
│   └── secrets.toml.example
├── pages/
│   ├── __init__.py
│   ├── page_accueil.py
│   ├── page_chargement.py
│   ├── page_tests.py
│   ├── page_visualisation.py
│   ├── page_previsions.py
│   ├── page_bourse.py
│   └── page_historique.py
└── app/
    └── models/  # Modèles ML (optionnel)
```

## 🐛 Problèmes courants

### Erreur "Module not found"

**Solution** : Ajoutez le module dans `requirements_streamlit.txt` et poussez les changements.

### Erreur de chemin de fichier

**Solution** : Vérifiez que tous les chemins sont relatifs (utilisent `os.path.join()`).

### L'application ne démarre pas

**Solution** : Vérifiez les logs dans Streamlit Cloud (Manage app > Logs).

## 📚 Documentation

- Guide complet : `DEPLOYMENT.md`
- README principal : `README.md`

## 🎉 C'est prêt !

Votre application est maintenant prête à être déployée sur Streamlit Cloud !

