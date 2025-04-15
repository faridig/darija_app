# Darija App

Application de traduction et d'apprentissage du Darija (Arabe Marocain).

## Structure du Projet

```
darija_app/
├── venv/                    # Environnement virtuel Python
├── docs/                    # Documentation du projet
│   ├── comprendre_rag.txt  # Documentation sur le RAG
│   └── proccess.txt        # Process de développement
├── README.md               # Documentation principale
├── suivi_projet.md         # Suivi du projet
├── suivi.txt              # Suivi des tâches
├── .env                   # Variables d'environnement
├── setup.sh               # Script d'installation
└── source/               # Code source
    ├── agregation/      # Scripts d'agrégation et enrichissement
    │   ├── data_synthetique/  # Données synthétiques générées
    │   ├── notebook/          # Notebooks d'analyse
    │   ├── sql/              # Scripts SQL
    │   ├── structured_json/   # Données JSON structurées
    │   └── nettoyage_csv.py
    ├── database/        # Gestion de la base de données
    │   ├── models.py    # Modèles SQLAlchemy
    │   └── migration.py # Scripts de migration
    ├── data_Darija-SFT-Mixture/  # Données et modules
    │   └── darija_data/
    └── traductordarija_scrapping/ # Scripts de scraping
```

## Installation

1. Cloner le dépôt :
```bash
git clone https://github.com/faridig/darija_app.git
cd darija_app
```

2. Exécuter le script d'installation :
```bash
chmod +x setup.sh
./setup.sh
```

3. Mettre à jour la clé API OpenAI dans `.env` :
```bash
nano source/agregation/.env
```

## Migration des Données vers PostgreSQL

1. Installer PostgreSQL :
```bash
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib
```

2. Créer la base de données :
```bash
sudo -u postgres psql
CREATE DATABASE darija_db;
\q
```

3. Mettre à jour les variables d'environnement dans `source/agregation/.env` :
```bash
nano source/agregation/.env
```

4. Exécuter la migration :
```bash
cd source/agregation
python migrate_to_postgres.py
```

## Utilisation

### Enrichissement des traductions

Pour enrichir les traductions avec des tags et du contexte :

```bash
cd source/agregation
python enrichir_traductions.py
```

Le script va :
- Charger les traductions depuis les fichiers JSON
- Générer des tags et du contexte pour chaque paire
- Sauvegarder les résultats dans `data/translations_with_tags.json`

## Documentation

- `docs/comprendre_rag.txt` : Documentation sur le système RAG
- `docs/proccess.txt` : Process de développement
- `suivi_projet.md` : Suivi détaillé du projet
- `architecture.md` : Architecture technique du projet

## Contribution

Les contributions sont les bienvenues ! N'hésitez pas à :
1. Forker le projet
2. Créer une branche pour votre fonctionnalité
3. Commiter vos changements
4. Pousser vers la branche
5. Ouvrir une Pull Request

## Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails. 