# Guide de Déploiement sur Streamlit Cloud

Ce guide vous explique comment déployer votre application Streamlit sur Streamlit Cloud.

## 📋 Prérequis

1. **Compte GitHub** : Vous devez avoir un compte GitHub
2. **Repository GitHub** : Votre code doit être dans un repository GitHub (public ou privé)
3. **Compte Streamlit Cloud** : Créez un compte sur [share.streamlit.io](https://share.streamlit.io)

## 🚀 Étapes de déploiement

### 1. Préparer votre repository GitHub

Assurez-vous que votre code est bien poussé sur GitHub :

```bash
git add .
git commit -m "Préparation pour déploiement Streamlit"
git push origin main
```

### 2. Créer un compte Streamlit Cloud

1. Allez sur [share.streamlit.io](https://share.streamlit.io)
2. Cliquez sur "Sign up" ou "Sign in"
3. Connectez-vous avec votre compte GitHub

### 3. Déployer l'application

1. **Cliquez sur "New app"** dans le tableau de bord Streamlit Cloud
2. **Sélectionnez votre repository** : Choisissez le repository contenant votre projet
3. **Sélectionnez la branche** : Généralement `main` ou `master`
4. **Fichier principal** : Entrez `streamlit_app.py`
5. **Cliquez sur "Deploy!"**

### 4. Configuration (optionnel)

Si vous avez besoin de variables d'environnement ou de secrets :

1. Allez dans **Settings** de votre application
2. Cliquez sur **Secrets**
3. Ajoutez vos secrets au format TOML :

```toml
# Exemple de secrets.toml
API_KEY = "votre_clé_api"
DATABASE_URL = "votre_url_base_de_données"
```

## 📁 Structure requise

Votre projet doit avoir cette structure :

```
Projet-ML-SEA3/
├── streamlit_app.py          # Point d'entrée principal
├── streamlit_utils.py         # Utilitaires
├── requirements_streamlit.txt # Dépendances
├── .streamlit/
│   └── config.toml           # Configuration Streamlit
├── pages/                    # Pages de l'application
│   ├── __init__.py
│   ├── page_accueil.py
│   ├── page_chargement.py
│   ├── page_tests.py
│   ├── page_visualisation.py
│   ├── page_previsions.py
│   ├── page_bourse.py
│   └── page_historique.py
└── app/
    └── models/               # Modèles ML (optionnel)
```

## ✅ Vérifications avant déploiement

### 1. Vérifier les dépendances

Assurez-vous que `requirements_streamlit.txt` contient toutes les dépendances nécessaires :

```bash
pip install -r requirements_streamlit.txt
streamlit run streamlit_app.py
```

### 2. Tester localement

Testez votre application localement avant de déployer :

```bash
streamlit run streamlit_app.py
```

### 3. Vérifier les chemins de fichiers

- Les chemins relatifs doivent fonctionner depuis la racine du projet
- Les modèles ML doivent être dans `app/models/` ou accessibles via des chemins relatifs

## 🔧 Configuration avancée

### Personnaliser le thème

Modifiez `.streamlit/config.toml` :

```toml
[theme]
primaryColor = "#1f77b4"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
```

### Augmenter la taille d'upload

Dans `.streamlit/config.toml` :

```toml
[server]
maxUploadSize = 50  # En MB
```

## 🐛 Résolution de problèmes

### L'application ne démarre pas

1. **Vérifiez les logs** : Dans Streamlit Cloud, cliquez sur "Manage app" > "Logs"
2. **Vérifiez les dépendances** : Assurez-vous que toutes les dépendances sont dans `requirements_streamlit.txt`
3. **Vérifiez les imports** : Tous les imports doivent être corrects

### Erreur "Module not found"

Ajoutez le module manquant dans `requirements_streamlit.txt` et poussez les changements :

```bash
git add requirements_streamlit.txt
git commit -m "Ajout dépendance manquante"
git push
```

Streamlit Cloud redéploiera automatiquement.

### Problèmes de chemins de fichiers

- Utilisez des chemins relatifs : `app/models/` au lieu de chemins absolus
- Vérifiez que les fichiers nécessaires sont dans le repository

### Limites de mémoire

Si votre application utilise beaucoup de mémoire :
- Optimisez le chargement des données
- Utilisez `@st.cache_data` pour mettre en cache les données

## 📝 Bonnes pratiques

1. **Versionner votre code** : Utilisez Git pour versionner votre code
2. **Tester localement** : Testez toujours localement avant de déployer
3. **Gérer les secrets** : Ne commitez jamais de secrets dans le code
4. **Optimiser les performances** : Utilisez le cache Streamlit pour les données lourdes
5. **Documenter** : Maintenez la documentation à jour

## 🔄 Mise à jour de l'application

Pour mettre à jour votre application :

1. Faites vos modifications localement
2. Testez localement
3. Commitez et poussez sur GitHub :
   ```bash
   git add .
   git commit -m "Description des changements"
   git push origin main
   ```
4. Streamlit Cloud redéploiera automatiquement

## 📊 Monitoring

Dans Streamlit Cloud, vous pouvez :
- Voir les logs en temps réel
- Surveiller l'utilisation
- Gérer les versions
- Configurer les domaines personnalisés (pour les comptes payants)

## 🔒 Sécurité

- Ne stockez jamais de secrets dans le code
- Utilisez les secrets Streamlit pour les clés API
- Validez toutes les entrées utilisateur
- Limitez la taille des fichiers uploadés

## 📞 Support

- **Documentation Streamlit** : [docs.streamlit.io](https://docs.streamlit.io)
- **Community Forum** : [discuss.streamlit.io](https://discuss.streamlit.io)
- **GitHub Issues** : Pour les bugs et demandes de fonctionnalités

---

**Note** : Le déploiement sur Streamlit Cloud est gratuit pour les applications publiques. Pour les applications privées, un compte payant est requis.

