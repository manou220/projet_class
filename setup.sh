#!/bin/bash
# Script de configuration pour Railway

# Créer les dossiers nécessaires
mkdir -p uploads
mkdir -p app/models

# Installer les dépendances
pip install -r requirements_streamlit.txt

echo "Configuration terminée !"

