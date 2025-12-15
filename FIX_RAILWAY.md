# 🔧 Correction du problème Railway

## Problème

Railway utilise `requirements.txt` qui contient des dépendances Windows (`pywin32`) qui ne peuvent pas être installées sur Linux.

## Solution

J'ai créé un fichier `nixpacks.toml` qui force Railway à utiliser `requirements_streamlit.txt`.

## Fichiers créés/modifiés

- ✅ `nixpacks.toml` - Configuration pour utiliser `requirements_streamlit.txt`
- ✅ `railway.json` - Mis à jour
- ✅ `runtime.txt` - Version Python

## Prochaines étapes

1. **Poussez les nouveaux fichiers sur GitHub** :
   - `nixpacks.toml`
   - `runtime.txt`
   - `railway.json` (mis à jour)

2. **Dans Railway** :
   - Allez dans votre projet
   - Cliquez sur "Settings"
   - Vérifiez que le build utilise bien `nixpacks.toml`
   - Redéployez

3. **Alternative** : Renommez temporairement les fichiers
   - Renommez `requirements.txt` en `requirements_flask.txt`
   - Renommez `requirements_streamlit.txt` en `requirements.txt`
   - Poussez sur GitHub
   - Railway utilisera automatiquement `requirements.txt`

## Option recommandée : Renommer

La solution la plus simple est de renommer temporairement :

```bash
# Dans GitHub Desktop ou localement
mv requirements.txt requirements_flask.txt
mv requirements_streamlit.txt requirements.txt
```

Puis poussez sur GitHub. Railway utilisera automatiquement le nouveau `requirements.txt`.

