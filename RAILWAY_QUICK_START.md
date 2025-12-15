# 🚂 Déploiement Railway - Guide Rapide

## 📌 Étapes Simples

### 1️⃣ Créer un compte Railway

1. Allez sur [railway.app](https://railway.app)
2. Cliquez sur "Start a New Project"
3. Connectez-vous avec GitHub

### 2️⃣ Créer un nouveau projet

1. Cliquez sur **"New Project"**
2. Sélectionnez **"Deploy from GitHub repo"**
3. Choisissez votre repository : **`manou220/projet_class`**
4. Railway va détecter automatiquement votre projet

### 3️⃣ Configuration automatique

Railway va automatiquement :
- ✅ Détecter que c'est une application Python
- ✅ Installer les dépendances depuis `requirements_streamlit.txt`
- ✅ Démarrer avec le `Procfile`

### 4️⃣ Déployer

1. Railway va commencer le déploiement automatiquement
2. Vous verrez les logs en temps réel
3. Une fois terminé, vous recevrez une URL : `https://votre-app.railway.app`

## 📁 Fichiers créés pour vous

- ✅ `Procfile` - Configuration Railway pour démarrer Streamlit
- ✅ `railway.json` - Configuration Railway (optionnel)
- ✅ `RAILWAY_DEPLOYMENT.md` - Guide complet

## ⚙️ Configuration

Le `Procfile` contient :
```
web: streamlit run streamlit_app.py --server.port=$PORT --server.address=0.0.0.0
```

Railway définit automatiquement le port via `$PORT`.

## 🔄 Mise à jour

Pour mettre à jour :
1. Faites vos modifications
2. Poussez sur GitHub :
   ```bash
   git add .
   git commit -m "Mise à jour"
   git push origin main
   ```
3. Railway redéploiera automatiquement !

## 🐛 Problèmes ?

- **Vérifiez les logs** dans Railway Dashboard
- **Assurez-vous que `Procfile` est présent** à la racine
- **Vérifiez `requirements_streamlit.txt`** contient toutes les dépendances

## 📖 Guide Complet

Pour plus de détails, consultez : **`RAILWAY_DEPLOYMENT.md`**

---

**C'est prêt !** Allez sur [railway.app](https://railway.app) et créez votre projet ! 🚀

