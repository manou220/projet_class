# 🚂 Guide de Déploiement sur Railway

Ce guide vous explique comment déployer votre application Streamlit sur Railway.

## 📋 Prérequis

1. **Compte Railway** : Créez un compte sur [railway.app](https://railway.app)
2. **Compte GitHub** : Votre code doit être sur GitHub
3. **Repository GitHub** : Votre projet doit être poussé sur GitHub

## 🚀 Étapes de déploiement

### 1. Créer un compte Railway

1. Allez sur [railway.app](https://railway.app)
2. Cliquez sur "Start a New Project"
3. Connectez-vous avec GitHub

### 2. Créer un nouveau projet

1. Cliquez sur "New Project"
2. Sélectionnez "Deploy from GitHub repo"
3. Choisissez votre repository : `manou220/projet_class`
4. Railway va détecter automatiquement votre projet

### 3. Configuration automatique

Railway va :
- Détecter que c'est une application Python
- Installer les dépendances depuis `requirements_streamlit.txt`
- Démarrer l'application avec le `Procfile`

### 4. Variables d'environnement (optionnel)

Si vous avez besoin de variables d'environnement :

1. Allez dans votre projet Railway
2. Cliquez sur "Variables"
3. Ajoutez vos variables :
   - `PORT` : Railway définit automatiquement le port
   - Autres variables si nécessaire

### 5. Déployer

1. Railway va automatiquement déployer votre application
2. Vous verrez les logs en temps réel
3. Une fois déployé, vous recevrez une URL : `https://votre-app.railway.app`

## 📁 Fichiers nécessaires

Votre projet doit contenir :

- ✅ `streamlit_app.py` - Fichier principal
- ✅ `Procfile` - Configuration Railway
- ✅ `requirements_streamlit.txt` - Dépendances
- ✅ `.streamlit/config.toml` - Configuration Streamlit

## 🔧 Configuration

### Procfile

Le fichier `Procfile` contient :
```
web: streamlit run streamlit_app.py --server.port=$PORT --server.address=0.0.0.0
```

### Variables d'environnement

Railway définit automatiquement :
- `PORT` : Port sur lequel l'application doit écouter

## 🐛 Résolution de problèmes

### L'application ne démarre pas

1. **Vérifiez les logs** dans Railway Dashboard
2. **Vérifiez que `Procfile` est présent** à la racine
3. **Vérifiez que `requirements_streamlit.txt` contient toutes les dépendances**

### Erreur "Port already in use"

- Railway définit automatiquement le port via `$PORT`
- Assurez-vous que votre `Procfile` utilise `$PORT`

### Erreur de dépendances

- Vérifiez que toutes les dépendances sont dans `requirements_streamlit.txt`
- Railway installera automatiquement les dépendances

### L'application se ferme après quelques minutes

- Railway peut mettre en veille les applications gratuites
- Considérez un plan payant pour une disponibilité 24/7

## 📊 Monitoring

Dans Railway Dashboard, vous pouvez :
- Voir les logs en temps réel
- Surveiller l'utilisation des ressources
- Gérer les variables d'environnement
- Voir les métriques de performance

## 💰 Plans Railway

- **Free Plan** : Gratuit avec limitations
- **Pro Plan** : Payant avec plus de ressources

## 🔄 Mise à jour

Pour mettre à jour votre application :

1. Faites vos modifications
2. Committez et poussez sur GitHub :
   ```bash
   git add .
   git commit -m "Mise à jour"
   git push origin main
   ```
3. Railway redéploiera automatiquement

## 📝 Notes importantes

- Railway redéploie automatiquement à chaque push sur GitHub
- Les fichiers uploadés sont temporaires (stockés en mémoire)
- Les données de session ne persistent pas entre les redémarrages
- Pour un stockage persistant, utilisez une base de données (PostgreSQL, MySQL, etc.)

## ✅ Checklist avant déploiement

- [ ] `Procfile` est présent à la racine
- [ ] `requirements_streamlit.txt` contient toutes les dépendances
- [ ] `streamlit_app.py` est à la racine
- [ ] Le code est poussé sur GitHub
- [ ] Compte Railway créé

## 🎉 C'est prêt !

Votre application sera accessible via une URL Railway une fois déployée !

---

**Besoin d'aide ?** Consultez la [documentation Railway](https://docs.railway.app)

