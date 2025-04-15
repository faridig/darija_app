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
└── source/               # Code source
    ├── agregation/      # Scripts d'agrégation et enrichissement
    │   ├── data_synthetique/  # Données synthétiques générées
    │   ├── notebook/          # Notebooks d'analyse
    │   ├── sql/              # Scripts SQL
    │   ├── structured_json/   # Données JSON structurées
    │   ├── enrichir_traductions.py
    │   └── nettoyage_csv.py
    ├── data_Darija-SFT-Mixture/  # Données et modules
    │   └── darija_data/
    └── traductordarija_scrapping/ # Scripts de scraping
```

## Installation

1. Cloner le dépôt :
```bash
git clone https://github.com/votre-username/darija_app.git
cd darija_app
```

2. Créer et activer un environnement virtuel :
```bash
python -m venv venv
source venv/bin/activate  # Sur Unix/MacOS
# ou
venv\Scripts\activate     # Sur Windows
```

3. Installer les dépendances :
```bash
pip install -r requirements.txt
```

4. Configurer la clé API OpenAI :
Créer un fichier `.env` à la racine du projet avec le contenu suivant :
```
OPENAI_API_KEY=votre_clé_api_ici
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
- Sauvegarder les résultats dans `translations_with_tags.json`

## Documentation

- `docs/comprendre_rag.txt` : Documentation sur le système RAG
- `docs/proccess.txt` : Process de développement
- `suivi_projet.md` : Suivi détaillé du projet
- `architecture.md` : Architecture technique du projet

## Contribution

1. Créer une branche pour votre fonctionnalité
2. Commiter vos changements
3. Créer une Pull Request

## Licence

MIT 