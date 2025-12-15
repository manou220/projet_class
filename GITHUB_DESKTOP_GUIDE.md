# 📦 Guide : Mettre le projet sur GitHub Desktop

Ce guide vous explique étape par étape comment mettre votre projet sur GitHub Desktop et le publier sur GitHub.

## 📋 Prérequis

- ✅ GitHub Desktop installé sur votre ordinateur
- ✅ Compte GitHub créé
- ✅ Projet déjà initialisé en Git (✅ c'est fait !)

## 🚀 Étapes avec GitHub Desktop

### Étape 1 : Ouvrir le projet dans GitHub Desktop

1. **Ouvrez GitHub Desktop**
2. **Cliquez sur "File" > "Add Local Repository"** (ou "Ajouter un dépôt local")
3. **Naviguez vers votre dossier projet** :
   ```
   C:\Users\HP\Downloads\Telegram Desktop\Projet-ML-SEA3 (2)\Projet-ML-SEA3
   ```
4. **Cliquez sur "Add repository"**

### Étape 2 : Vérifier les fichiers à commiter

Dans GitHub Desktop, vous verrez tous les fichiers modifiés/nouveaux dans l'onglet "Changes" :

**Fichiers à inclure** ✅ :
- `streamlit_app.py`
- `streamlit_utils.py`
- `requirements_streamlit.txt`
- `.streamlit/config.toml`
- `.streamlit/secrets.toml.example`
- `pages/` (tous les fichiers)
- `DEPLOYMENT.md`
- `QUICK_START.md`
- `GITHUB_DESKTOP_GUIDE.md`
- `README.md`
- `.gitignore`

**Fichiers à exclure** ❌ (déjà dans .gitignore) :
- `__pycache__/`
- `*.pyc`
- `*.log`
- `*.db`
- `uploads/*.csv`
- `*.joblib` (si trop volumineux)

### Étape 3 : Créer le commit initial

1. **Dans la zone "Summary"**, tapez un message de commit :
   ```
   Préparation pour déploiement Streamlit Cloud
   ```

2. **Dans la zone "Description"** (optionnel), ajoutez :
   ```
   - Ajout de streamlit_app.py et streamlit_utils.py
   - Configuration Streamlit (.streamlit/config.toml)
   - Dépendances pour Streamlit (requirements_streamlit.txt)
   - Pages Streamlit complètes
   - Documentation de déploiement
   ```

3. **Cochez tous les fichiers** que vous voulez inclure dans le commit

4. **Cliquez sur "Commit to main"** (ou "Commit to master")

### Étape 4 : Publier sur GitHub

1. **Cliquez sur "Publish repository"** (en haut à droite)
   - Si vous ne voyez pas ce bouton, allez dans "Repository" > "Publish repository"

2. **Configurez la publication** :
   - ✅ **Name** : `Projet-ML-SEA3` (ou le nom que vous voulez)
   - ✅ **Description** : `Application d'analyse de données et Machine Learning avec Streamlit`
   - ⚠️ **Keep this code private** : 
     - Décochez si vous voulez un repository public (gratuit pour Streamlit Cloud)
     - Cochez si vous voulez un repository privé (nécessite un compte GitHub payant pour Streamlit Cloud)

3. **Cliquez sur "Publish repository"**

### Étape 5 : Vérifier sur GitHub.com

1. **Allez sur [github.com](https://github.com)**
2. **Connectez-vous** avec votre compte
3. **Trouvez votre repository** dans la liste
4. **Vérifiez** que tous les fichiers sont bien présents

## 🔄 Mettre à jour le repository

Après avoir fait des modifications :

1. **Ouvrez GitHub Desktop**
2. **Vous verrez les changements** dans l'onglet "Changes"
3. **Ajoutez un message de commit**
4. **Cliquez sur "Commit to main"**
5. **Cliquez sur "Push origin"** (en haut) pour envoyer les changements sur GitHub

## 📝 Structure recommandée du repository

Votre repository GitHub devrait contenir :

```
Projet-ML-SEA3/
├── .gitignore
├── README.md
├── DEPLOYMENT.md
├── QUICK_START.md
├── GITHUB_DESKTOP_GUIDE.md
├── requirements.txt
├── requirements_streamlit.txt
├── streamlit_app.py
├── streamlit_utils.py
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
├── app/
│   └── models/  # Modèles ML (optionnel)
└── ...
```

## ⚠️ Fichiers à ne PAS commiter

Ces fichiers sont automatiquement ignorés grâce au `.gitignore` :

- ❌ Fichiers de cache Python (`__pycache__/`, `*.pyc`)
- ❌ Fichiers de logs (`*.log`, `logs/`)
- ❌ Bases de données (`*.db`, `*.sqlite`)
- ❌ Fichiers uploadés (`uploads/*.csv`)
- ❌ Secrets (`.streamlit/secrets.toml`)
- ❌ Fichiers de modèles volumineux (`*.joblib` - si trop gros)

## 🐛 Problèmes courants

### "Repository already exists"

**Solution** : Le repository existe déjà sur GitHub. Utilisez "Fetch origin" puis "Push" pour mettre à jour.

### "Nothing to commit"

**Solution** : Tous les fichiers sont déjà committés. Faites des modifications ou vérifiez que vous avez bien sélectionné les fichiers.

### Fichiers trop volumineux

**Solution** : 
- Les fichiers `.joblib` peuvent être volumineux
- Si GitHub refuse, ajoutez-les au `.gitignore` ou utilisez Git LFS

### Erreur de connexion

**Solution** :
- Vérifiez votre connexion Internet
- Vérifiez que vous êtes connecté dans GitHub Desktop (File > Options > Accounts)

## ✅ Checklist finale

Avant de publier, vérifiez :

- [ ] Tous les fichiers importants sont inclus
- [ ] Le `.gitignore` est à jour
- [ ] Le `README.md` est complet
- [ ] Les secrets ne sont pas committés
- [ ] Les fichiers volumineux sont gérés
- [ ] Le message de commit est clair

## 🎉 C'est fait !

Une fois publié sur GitHub, vous pouvez :

1. **Déployer sur Streamlit Cloud** (voir `DEPLOYMENT.md`)
2. **Partager le repository** avec d'autres développeurs
3. **Créer des branches** pour développer de nouvelles fonctionnalités
4. **Créer des issues** pour suivre les bugs et améliorations

## 📚 Ressources

- [Documentation GitHub Desktop](https://docs.github.com/en/desktop)
- [Guide Git pour débutants](https://guides.github.com/activities/hello-world/)
- [Streamlit Cloud Documentation](https://docs.streamlit.io/streamlit-community-cloud)

---

**Besoin d'aide ?** Consultez la documentation GitHub Desktop ou créez une issue sur votre repository.

